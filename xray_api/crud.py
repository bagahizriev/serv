from sqlalchemy.orm import Session
from .models import Inbound, Client
import uuid as py_uuid

# --- Inbounds ---
def get_inbounds(db: Session):
    return db.query(Inbound).all()

def get_inbound(db: Session, inbound_id: int):
    return db.query(Inbound).filter(Inbound.id == inbound_id).first()

def create_inbound(db: Session, name: str, port: int=443, protocol="vless", network="tcp", security="tls", sni=""):
    inbound = Inbound(name=name, port=port, protocol=protocol, network=network, security=security, sni=sni)
    db.add(inbound)
    db.commit()
    db.refresh(inbound)
    return inbound

def update_inbound(db: Session, inbound_id: int, **kwargs):
    inbound = get_inbound(db, inbound_id)
    for k, v in kwargs.items():
        setattr(inbound, k, v)
    db.commit()
    db.refresh(inbound)
    return inbound

def delete_inbound(db: Session, inbound_id: int):
    inbound = get_inbound(db, inbound_id)
    db.delete(inbound)
    db.commit()

# --- Clients ---
def get_clients(db: Session, inbound_id: int = None):
    query = db.query(Client)
    if inbound_id:
        query = query.filter(Client.inbound_id == inbound_id)
    return query.all()

def get_client(db: Session, client_id: int):
    return db.query(Client).filter(Client.id == client_id).first()

def create_client(db: Session, username: str, inbound_id: int):
    client = Client(username=username, uuid=str(py_uuid.uuid4()), inbound_id=inbound_id)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

def update_client(db: Session, client_id: int, **kwargs):
    client = get_client(db, client_id)
    for k, v in kwargs.items():
        setattr(client, k, v)
    db.commit()
    db.refresh(client)
    return client

def delete_client(db: Session, client_id: int):
    client = get_client(db, client_id)
    db.delete(client)
    db.commit()
