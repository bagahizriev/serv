import secrets
import uuid as py_uuid
from typing import List
from urllib.parse import urlparse

import httpx
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from .db import engine, get_db
from .models import Base, Node, Inbound, Client
from .schemas import (
    NodeCreate,
    NodeOut,
    NodeUpdate,
    InboundCreate,
    InboundOut,
    InboundUpdate,
    ClientCreate,
    ClientOut,
    ClientUpdate,
)
from .config_gen import build_node_config

app = FastAPI(title="Xray Panel API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


def _normalize_node_url(url: str) -> str:
    u = (url or "").strip().rstrip("/")
    if not u:
        return u
    if u.startswith("http://") or u.startswith("https://"):
        return u
    return f"http://{u}"


def _node_host_from_url(node_url: str) -> str:
    normalized = _normalize_node_url(node_url)
    try:
        p = urlparse(normalized)
        if p.hostname:
            return p.hostname
    except Exception:
        pass
    return (normalized or "").replace("http://", "").replace("https://", "").split(":")[0]


def _build_vless_uri(*, node_host: str, inbound: Inbound, client: Client) -> str:
    base = f"vless://{client.uuid}@{node_host}:{inbound.port}"
    params: list[str] = [f"type={inbound.network or 'tcp'}"]

    sec = (inbound.security or "").lower()
    if sec == "reality":
        params.append("security=reality")
        if inbound.sni:
            params.append(f"sni={inbound.sni}")
        if inbound.reality_fingerprint:
            params.append(f"fp={inbound.reality_fingerprint}")
        if inbound.reality_public_key:
            params.append(f"pbk={inbound.reality_public_key}")
        if inbound.reality_short_id:
            params.append(f"sid={inbound.reality_short_id}")
    else:
        params.append("security=none")

    tag = f"{client.username}"
    return f"{base}?{'&'.join(params)}#{tag}"


def _push_node(node_id: int, db: Session):
    node = (
        db.query(Node)
        .options(joinedload(Node.inbounds).joinedload(Inbound.clients))
        .filter(Node.id == node_id)
        .first()
    )
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    config = build_node_config(node)
    base = _normalize_node_url(node.url)
    url = f"{base}/apply-config"
    headers = {"X-Node-Key": node.node_key}

    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(url, json={"config": config}, headers=headers)
        if r.status_code >= 400:
            raise HTTPException(status_code=400, detail=f"Node error: {r.status_code} {r.text}")
        return {
            "status": "pushed",
            "node_response": r.json()
            if r.headers.get("content-type", "").startswith("application/json")
            else r.text,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/nodes", response_model=NodeOut)
def create_node(data: NodeCreate, db: Session = Depends(get_db)):
    node = Node(name=data.name, url=_normalize_node_url(data.url), node_key=data.node_key)
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


@app.get("/nodes/{node_id}", response_model=NodeOut)
def get_node(node_id: int, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@app.put("/nodes/{node_id}", response_model=NodeOut)
def update_node(node_id: int, data: NodeUpdate, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if data.name is not None:
        node.name = data.name
    if data.url is not None:
        node.url = _normalize_node_url(data.url)
    if data.node_key is not None:
        node.node_key = data.node_key

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.refresh(node)
    return node


@app.delete("/nodes/{node_id}")
def delete_node(node_id: int, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    db.delete(node)
    db.commit()
    return {"status": "deleted"}


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

    _push_node(node_id=data.node_id, db=db)
    return inbound


@app.get("/inbounds", response_model=List[InboundOut])
def list_inbounds(node_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Inbound)
    if node_id is not None:
        q = q.filter(Inbound.node_id == node_id)
    return q.order_by(Inbound.id.asc()).all()


@app.get("/inbounds/{inbound_id}", response_model=InboundOut)
def get_inbound(inbound_id: int, db: Session = Depends(get_db)):
    inbound = db.query(Inbound).filter(Inbound.id == inbound_id).first()
    if not inbound:
        raise HTTPException(status_code=404, detail="Inbound not found")
    return inbound


@app.put("/inbounds/{inbound_id}", response_model=InboundOut)
def update_inbound(inbound_id: int, data: InboundUpdate, db: Session = Depends(get_db)):
    inbound = db.query(Inbound).filter(Inbound.id == inbound_id).first()
    if not inbound:
        raise HTTPException(status_code=404, detail="Inbound not found")

    if data.name is not None:
        inbound.name = data.name
    if data.port is not None:
        inbound.port = data.port
    if data.protocol is not None:
        inbound.protocol = data.protocol
    if data.network is not None:
        inbound.network = data.network
    if data.security is not None:
        inbound.security = data.security
    if data.sni is not None:
        inbound.sni = data.sni
    if data.reality_dest is not None:
        inbound.reality_dest = data.reality_dest
    if data.reality_fingerprint is not None:
        inbound.reality_fingerprint = data.reality_fingerprint

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.refresh(inbound)

    _push_node(node_id=inbound.node_id, db=db)
    return inbound


@app.delete("/inbounds/{inbound_id}")
def delete_inbound(inbound_id: int, db: Session = Depends(get_db)):
    inbound = db.query(Inbound).filter(Inbound.id == inbound_id).first()
    if not inbound:
        raise HTTPException(status_code=404, detail="Inbound not found")
    node_id = inbound.node_id
    db.delete(inbound)
    db.commit()
    _push_node(node_id=node_id, db=db)
    return {"status": "deleted"}


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

    _push_node(node_id=inbound.node_id, db=db)
    return client


@app.get("/clients", response_model=List[ClientOut])
def list_clients(inbound_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Client)
    if inbound_id is not None:
        q = q.filter(Client.inbound_id == inbound_id)
    return q.order_by(Client.id.asc()).all()


@app.get("/clients/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@app.put("/clients/{client_id}", response_model=ClientOut)
def update_client(client_id: int, data: ClientUpdate, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    inbound = db.query(Inbound).filter(Inbound.id == client.inbound_id).first()
    if not inbound:
        raise HTTPException(status_code=404, detail="Inbound not found")

    if data.username is not None:
        client.username = data.username
    if data.level is not None:
        client.level = data.level

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.refresh(client)

    _push_node(node_id=inbound.node_id, db=db)
    return client


@app.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    inbound = db.query(Inbound).filter(Inbound.id == client.inbound_id).first()
    if not inbound:
        raise HTTPException(status_code=404, detail="Inbound not found")
    db.delete(client)
    db.commit()

    _push_node(node_id=inbound.node_id, db=db)
    return {"status": "deleted"}


@app.get("/clients/{client_id}/vless-uri")
def get_client_vless_uri(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    inbound = db.query(Inbound).filter(Inbound.id == client.inbound_id).first()
    if not inbound:
        raise HTTPException(status_code=404, detail="Inbound not found")

    node = db.query(Node).filter(Node.id == inbound.node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    node_host = _node_host_from_url(node.url)
    uri = _build_vless_uri(node_host=node_host, inbound=inbound, client=client)
    return {"uri": uri}


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
    return _push_node(node_id=node_id, db=db)
