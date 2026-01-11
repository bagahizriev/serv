from fastapi import FastAPI, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, ensure_schema
from . import crud
import os
import threading
import subprocess
import secrets
from typing import Optional

from . import config_builder

# --- Настройка базы ---
DB_PATH = os.environ.get("XRAY_API_DB_PATH", "/var/lib/xray-api/xray.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ensure_schema(engine)

# --- FastAPI ---
app = FastAPI(title="Xray Config API")

API_KEY = os.environ.get("XRAY_API_KEY", "")
APPLY_DEBOUNCE_SECONDS = float(os.environ.get("XRAY_APPLY_DEBOUNCE_SECONDS", "1.5"))

_apply_lock = threading.Lock()
_apply_timer: Optional[threading.Timer] = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Server API key is not configured")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

def _validate_tls_certificates(sni: str):
    if not sni:
        raise HTTPException(status_code=400, detail="For TLS inbound, 'sni' must be set")
    cert = f"/etc/letsencrypt/live/{sni}/fullchain.pem"
    key = f"/etc/letsencrypt/live/{sni}/privkey.pem"
    if not (os.path.exists(cert) and os.path.exists(key)):
        raise HTTPException(
            status_code=400,
            detail=(
                "TLS сертификаты не найдены внутри контейнера. "
                f"Ожидаются файлы: {cert} и {key}. "
                "Смонтируй /etc/letsencrypt (или используй security=none/reality)."
            ),
        )

def _apply_config_now():
    try:
        config_builder.apply_config()
    except Exception as e:
        print(f"[!] apply_config failed: {e}")

def _serialize_inbound(inbound):
    if inbound is None:
        return None
    return {
        "id": inbound.id,
        "name": inbound.name,
        "address": inbound.address,
        "listen": inbound.listen,
        "port": inbound.port,
        "protocol": inbound.protocol,
        "network": inbound.network,
        "security": inbound.security,
        "sni": inbound.sni,
        "reality_public_key": inbound.reality_public_key,
        "reality_short_id": inbound.reality_short_id,
        "reality_dest": inbound.reality_dest,
        "reality_fingerprint": inbound.reality_fingerprint,
    }

def _serialize_client(client):
    if client is None:
        return None
    return {
        "id": client.id,
        "username": client.username,
        "uuid": client.uuid,
        "level": client.level,
        "inbound_id": client.inbound_id,
    }

def _xray_x25519_keys():
    out = subprocess.check_output([config_builder.XRAY_BIN, "x25519"], text=True)
    priv = ""
    pub = ""
    for line in out.splitlines():
        line = line.strip()
        if line.lower().startswith("private key"):
            priv = line.split(":", 1)[1].strip()
        elif line.lower().startswith("public key"):
            pub = line.split(":", 1)[1].strip()
    if not priv or not pub:
        raise RuntimeError(f"Failed to parse xray x25519 output: {out}")
    return priv, pub

def _gen_short_id():
    return secrets.token_hex(8)

def schedule_apply():
    global _apply_timer
    with _apply_lock:
        if _apply_timer is not None:
            _apply_timer.cancel()
        _apply_timer = threading.Timer(APPLY_DEBOUNCE_SECONDS, _apply_config_now)
        _apply_timer.daemon = True
        _apply_timer.start()

# --- Inbound endpoints ---
@app.get("/inbounds")
def list_inbounds(db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    return [_serialize_inbound(x) for x in crud.get_inbounds(db)]

@app.post("/inbounds")
def create_inbound(name: str, port: int=443, protocol="vless", network="tcp", security="tls", sni="", address: str = "", reality_dest: str = "", reality_fingerprint: str = "chrome", db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    if str(security).lower() == "tls":
        _validate_tls_certificates(sni)

    create_kwargs = {}
    if address:
        create_kwargs["address"] = address
    else:
        env_addr = os.environ.get("XRAY_NODE_ADDRESS", "")
        if env_addr:
            create_kwargs["address"] = env_addr
        else:
            create_kwargs["address"] = sni

    if str(security).lower() == "reality":
        priv, pub = _xray_x25519_keys()
        create_kwargs["reality_private_key"] = priv
        create_kwargs["reality_public_key"] = pub
        create_kwargs["reality_short_id"] = _gen_short_id()
        create_kwargs["reality_dest"] = reality_dest or (f"{sni}:443" if sni else "example.com:443")
        create_kwargs["reality_fingerprint"] = reality_fingerprint or "chrome"

    inbound = crud.create_inbound(db, name, port, protocol, network, security, sni, **create_kwargs)
    schedule_apply()
    return _serialize_inbound(inbound)

@app.patch("/inbounds/{inbound_id}")
def edit_inbound(inbound_id: int, name: str = None, port: int = None, protocol: str = None, network: str = None, security: str = None, sni: str = None, address: str = None, reality_dest: str = None, reality_fingerprint: str = None, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    effective_security = security
    effective_sni = sni
    if effective_security is None or effective_sni is None:
        existing = crud.get_inbound(db, inbound_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Inbound not found")
        if effective_security is None:
            effective_security = existing.security
        if effective_sni is None:
            effective_sni = existing.sni

    if str(effective_security).lower() == "tls":
        _validate_tls_certificates(effective_sni)

    update_data = {k:v for k,v in locals().items() if k not in ["inbound_id","db"] and v is not None}

    if str(effective_security).lower() == "reality":
        existing = crud.get_inbound(db, inbound_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Inbound not found")
        if (not existing.reality_private_key) or (not existing.reality_public_key) or (not existing.reality_short_id):
            priv, pub = _xray_x25519_keys()
            update_data.setdefault("reality_private_key", priv)
            update_data.setdefault("reality_public_key", pub)
            update_data.setdefault("reality_short_id", _gen_short_id())
        if "reality_dest" not in update_data or not update_data.get("reality_dest"):
            update_data["reality_dest"] = f"{effective_sni}:443" if effective_sni else "example.com:443"
        if "reality_fingerprint" not in update_data or not update_data.get("reality_fingerprint"):
            update_data["reality_fingerprint"] = "chrome"

    inbound = crud.update_inbound(db, inbound_id, **update_data)
    if inbound is None:
        raise HTTPException(status_code=404, detail="Inbound not found")
    schedule_apply()
    return _serialize_inbound(inbound)

@app.get("/clients/{client_id}/config")
def client_config(client_id: int, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    inbound = client.inbound
    cfg = {
        "v": "2",
        "ps": client.username,
        "add": inbound.sni or "example.com",
        "port": str(inbound.port),
        "id": client.uuid,
        "aid": "0",
        "net": inbound.network,
        "type": "none",
        "tls": inbound.security.lower(),
    }
    if inbound.network == "ws":
        cfg["path"] = "/vless-ws"
        cfg["host"] = inbound.sni
    if inbound.security.lower() == "reality":
        cfg["fp"] = inbound.reality_fingerprint or "chrome"
        cfg["serverNames"] = [inbound.sni or "example.com"]
        cfg["pbk"] = inbound.reality_public_key
        cfg["sid"] = inbound.reality_short_id
    return cfg

@app.get("/clients/{client_id}/vless")
def client_vless_uri(client_id: int, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    inbound = client.inbound
    host = inbound.address or inbound.sni

    if inbound.network == "ws":
        uri = f"vless://{client.uuid}@{host}:{inbound.port}?type=ws&security={inbound.security.lower()}&path=/vless-ws&host={inbound.sni}#{client.username}"
    elif inbound.security.lower() == "reality":
        uri = f"vless://{client.uuid}@{host}:{inbound.port}?type=tcp&encryption=none&security=reality&sni={inbound.sni}&fp={inbound.reality_fingerprint or 'chrome'}&pbk={inbound.reality_public_key}&sid={inbound.reality_short_id}#{client.username}"
    else:
        uri = f"vless://{client.uuid}@{host}:{inbound.port}?security={inbound.security.lower()}#{client.username}"

    return {"vless_uri": uri}

@app.delete("/inbounds/{inbound_id}")
def delete_inbound(inbound_id: int, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    crud.delete_inbound(db, inbound_id)
    schedule_apply()
    return {"status":"deleted"}

# --- Client endpoints ---
@app.get("/clients")
def list_clients(inbound_id: int = None, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    return [_serialize_client(x) for x in crud.get_clients(db, inbound_id)]

@app.post("/clients")
def create_client(username: str, inbound_id: int, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    client = crud.create_client(db, username, inbound_id)
    schedule_apply()
    return _serialize_client(client)

@app.patch("/clients/{client_id}")
def edit_client(client_id: int, username: str = None, level: int = None, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    update_data = {k:v for k,v in locals().items() if k not in ["client_id","db"] and v is not None}
    client = crud.update_client(db, client_id, **update_data)
    schedule_apply()
    return _serialize_client(client)

@app.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    crud.delete_client(db, client_id)
    schedule_apply()
    return {"status":"deleted"}
