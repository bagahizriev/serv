import json
import subprocess
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Base, Inbound, Client

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

            # TLS или Reality
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
                inbound_dict["streamSettings"]["realitySettings"] = {
                    "show": "auto",
                    "dest": inbound.sni or "example.com",
                    "xver": 0
                }

            # Sniffing по умолчанию
            inbound_dict["sniffing"] = {"enabled": True, "destOverride": ["http", "tls"]}

            config["inbounds"].append(inbound_dict)

        # Запись в файл
        with open(XRAY_CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        print(f"[+] config.json сгенерирован по данным базы в {XRAY_CONFIG_PATH}")

    finally:
        db.close()

# --- Функция перезапуска Xray ---
def restart_xray():
    subprocess.run(["supervisorctl", "restart", "xray"], check=True)
    print("[+] Xray перезапущен")

def apply_config():
    build_config()
    restart_xray()

# --- Основная функция ---
if __name__ == "__main__":
    apply_config()
