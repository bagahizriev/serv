from fastapi import FastAPI, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import crud
import os
import threading
from typing import Optional

import config_builder

# --- Настройка базы ---
DB_PATH = os.environ.get("XRAY_API_DB_PATH", "/var/lib/xray-api/xray.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

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

def _apply_config_now():
    config_builder.apply_config()

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
    return crud.get_inbounds(db)

@app.post("/inbounds")
def create_inbound(name: str, port: int=443, protocol="vless", network="tcp", security="tls", sni="", db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    inbound = crud.create_inbound(db, name, port, protocol, network, security, sni)
    schedule_apply()
    return inbound

@app.patch("/inbounds/{inbound_id}")
def edit_inbound(inbound_id: int, name: str = None, port: int = None, protocol: str = None, network: str = None, security: str = None, sni: str = None, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    update_data = {k:v for k,v in locals().items() if k not in ["inbound_id","db"] and v is not None}
    inbound = crud.update_inbound(db, inbound_id, **update_data)
    schedule_apply()
    return inbound

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
    # WebSocket настройки
    if inbound.network == "ws":
        cfg["path"] = "/vless-ws"
        cfg["host"] = inbound.sni
    # Reality настройки
    if inbound.security.lower() == "reality":
        cfg["fp"] = "chrome"
        cfg["serverNames"] = [inbound.sni or "example.com"]
    return cfg

@app.get("/clients/{client_id}/vless")
def client_vless_uri(client_id: int, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    inbound = client.inbound

    # Для WebSocket + TLS
    if inbound.network == "ws":
        uri = f"vless://{client.uuid}@{inbound.sni}:{inbound.port}?type=ws&security={inbound.security.lower()}&path=/vless-ws&host={inbound.sni}#{client.username}"
    # Для TCP/Reality
    elif inbound.security.lower() == "reality":
        uri = f"vless://{client.uuid}@{inbound.sni}:{inbound.port}?security=reality&fp=chrome#{client.username}"
    else:  # обычный TCP
        uri = f"vless://{client.uuid}@{inbound.sni}:{inbound.port}?security={inbound.security.lower()}#{client.username}"

    return {"vless_uri": uri}

@app.delete("/inbounds/{inbound_id}")
def delete_inbound(inbound_id: int, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    crud.delete_inbound(db, inbound_id)
    schedule_apply()
    return {"status":"deleted"}

# --- Client endpoints ---
@app.get("/clients")
def list_clients(inbound_id: int = None, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    return crud.get_clients(db, inbound_id)

@app.post("/clients")
def create_client(username: str, inbound_id: int, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    client = crud.create_client(db, username, inbound_id)
    schedule_apply()
    return client

@app.patch("/clients/{client_id}")
def edit_client(client_id: int, username: str = None, level: int = None, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    update_data = {k:v for k,v in locals().items() if k not in ["client_id","db"] and v is not None}
    client = crud.update_client(db, client_id, **update_data)
    schedule_apply()
    return client

@app.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    crud.delete_client(db, client_id)
    schedule_apply()
    return {"status":"deleted"}
