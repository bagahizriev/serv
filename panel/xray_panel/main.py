import secrets
import uuid as py_uuid
from typing import List

import httpx
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session, joinedload

from .db import engine, get_db
from .models import Base, Node, Inbound, Client
from .schemas import NodeCreate, NodeOut, InboundCreate, InboundOut, ClientCreate, ClientOut
from .config_gen import build_node_config

app = FastAPI(title="Xray Panel API")


@app.on_event("startup")
def _startup():
    Base.metadata.create_all(bind=engine)


def _x25519_keypair():
    priv = x25519.X25519PrivateKey.generate()
    pub = priv.public_key()
    priv_raw = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return priv_raw, pub_raw


def _b64url_nopad(raw: bytes) -> str:
    import base64

    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


@app.post("/nodes", response_model=NodeOut)
def create_node(data: NodeCreate, db: Session = Depends(get_db)):
    node = Node(name=data.name, url=data.url.rstrip("/"), node_key=data.node_key)
    db.add(node)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.refresh(node)
    return node


@app.get("/nodes", response_model=List[NodeOut])
def list_nodes(db: Session = Depends(get_db)):
    return db.query(Node).order_by(Node.id.asc()).all()


@app.post("/inbounds", response_model=InboundOut)
def create_inbound(data: InboundCreate, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.id == data.node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    inbound = Inbound(
        node_id=data.node_id,
        name=data.name,
        port=data.port,
        protocol=data.protocol,
        network=data.network,
        security=data.security,
        sni=data.sni,
        reality_dest=data.reality_dest or f"{data.sni}:443",
        reality_fingerprint=data.reality_fingerprint or "chrome",
    )

    if (data.security or "").lower() == "reality":
        priv_raw, pub_raw = _x25519_keypair()
        inbound.reality_private_key = _b64url_nopad(priv_raw)
        inbound.reality_public_key = _b64url_nopad(pub_raw)
        inbound.reality_short_id = secrets.token_hex(8)

    db.add(inbound)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.refresh(inbound)
    return inbound


@app.post("/clients", response_model=ClientOut)
def create_client(data: ClientCreate, db: Session = Depends(get_db)):
    inbound = db.query(Inbound).filter(Inbound.id == data.inbound_id).first()
    if not inbound:
        raise HTTPException(status_code=404, detail="Inbound not found")

    client = Client(inbound_id=data.inbound_id, username=data.username, uuid=str(py_uuid.uuid4()))
    db.add(client)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.refresh(client)
    return client


@app.get("/nodes/{node_id}/config")
def get_node_config(node_id: int, db: Session = Depends(get_db)):
    node = (
        db.query(Node)
        .options(joinedload(Node.inbounds).joinedload(Inbound.clients))
        .filter(Node.id == node_id)
        .first()
    )
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    try:
        return build_node_config(node)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/nodes/{node_id}/push")
def push_node_config(node_id: int, db: Session = Depends(get_db)):
    node = (
        db.query(Node)
        .options(joinedload(Node.inbounds).joinedload(Inbound.clients))
        .filter(Node.id == node_id)
        .first()
    )
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    config = build_node_config(node)

    url = f"{node.url}/apply-config"
    headers = {"X-Node-Key": node.node_key}

    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(url, json={"config": config}, headers=headers)
        if r.status_code >= 400:
            raise HTTPException(status_code=400, detail=f"Node error: {r.status_code} {r.text}")
        return {"status": "pushed", "node_response": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
