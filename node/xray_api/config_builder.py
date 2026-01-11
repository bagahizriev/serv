import json
import subprocess
import os
import tempfile
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from .models import Base, Inbound, Client

SUPERVISOR_SERVER_URL = os.environ.get("SUPERVISOR_SERVER_URL", "unix:///tmp/supervisor.sock")
XRAY_BIN = os.environ.get("XRAY_BIN", "/usr/local/bin/xray")

# --- Настройка базы ---
DB_PATH = os.environ.get("XRAY_API_DB_PATH", "/var/lib/xray-api/xray.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Путь для Xray config ---
XRAY_CONFIG_PATH = os.environ.get("XRAY_CONFIG_PATH", "/etc/xray/config.json")
os.makedirs(os.path.dirname(XRAY_CONFIG_PATH), exist_ok=True)

# --- Функция сборки config ---
def build_config():
    db = SessionLocal()
    try:
        Base.metadata.create_all(bind=engine)
        config = {
            "log": {"loglevel": "warning"},
            "inbounds": [],
            "outbounds": [{"protocol": "freedom"}]
        }

        inbounds = db.query(Inbound).all()
        for inbound in inbounds:
            clients = db.query(Client).filter(Client.inbound_id == inbound.id).all()
            client_list = [{"id": c.uuid, "email": c.username, "level": c.level} for c in clients]

            inbound_dict = {
                "listen": inbound.listen,
                "port": inbound.port,
                "protocol": inbound.protocol,
                "settings": {
                    "clients": client_list,
                    "decryption": "none"
                },
                "streamSettings": {
                    "network": inbound.network,
                }
            }

            if inbound.security.lower() == "tls":
                inbound_dict["streamSettings"]["security"] = "tls"
                inbound_dict["streamSettings"]["tlsSettings"] = {
                    "certificates": [
                        {
                            "certificateFile": f"/etc/letsencrypt/live/{inbound.sni}/fullchain.pem",
                            "keyFile": f"/etc/letsencrypt/live/{inbound.sni}/privkey.pem"
                        }
                    ]
                }
            elif inbound.security.lower() == "reality":
                inbound_dict["streamSettings"]["security"] = "reality"
                if not inbound.sni:
                    raise RuntimeError("Reality inbound requires sni")
                if not inbound.reality_private_key:
                    raise RuntimeError("Reality inbound requires reality_private_key")
                if not inbound.reality_short_id:
                    raise RuntimeError("Reality inbound requires reality_short_id")
                dest = inbound.reality_dest or f"{inbound.sni}:443"
                inbound_dict["streamSettings"]["realitySettings"] = {
                    "show": "auto",
                    "dest": dest,
                    "xver": 0,
                    "serverNames": [inbound.sni],
                    "privateKey": inbound.reality_private_key,
                    "shortIds": [inbound.reality_short_id],
                    "spiderX": "/"
                }

            inbound_dict["sniffing"] = {"enabled": True, "destOverride": ["http", "tls"]}

            config["inbounds"].append(inbound_dict)

        target_dir = os.path.dirname(XRAY_CONFIG_PATH) or "."
        with tempfile.NamedTemporaryFile("w", delete=False, dir=target_dir, prefix="config.", suffix=".json") as tmp:
            tmp_path = tmp.name
            json.dump(config, tmp, indent=2)

        try:
            subprocess.run([XRAY_BIN, "-test", "-config", tmp_path], check=True)
            os.replace(tmp_path, XRAY_CONFIG_PATH)
            print(f"[+] config.json сгенерирован по данным базы в {XRAY_CONFIG_PATH}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    finally:
        db.close()

# --- Функция перезапуска Xray ---
def restart_xray():
    subprocess.run(["supervisorctl", "-s", SUPERVISOR_SERVER_URL, "restart", "xray"], check=True)
    print("[+] Xray перезапущен")

def apply_config():
    build_config()
    try:
        restart_xray()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Xray restart failed: {e}")

if __name__ == "__main__":
    apply_config()
