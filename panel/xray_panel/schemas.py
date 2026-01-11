from pydantic import BaseModel
from typing import Optional


class NodeCreate(BaseModel):
    name: str
    url: str
    node_key: str


class NodeOut(BaseModel):
    id: int
    name: str
    url: str

    class Config:
        from_attributes = True


class InboundCreate(BaseModel):
    node_id: int
    name: str
    port: int = 443
    protocol: str = "vless"
    network: str = "tcp"
    security: str = "reality"
    sni: str
    reality_dest: Optional[str] = None
    reality_fingerprint: str = "chrome"


class InboundOut(BaseModel):
    id: int
    node_id: int
    name: str
    port: int
    protocol: str
    network: str
    security: str
    sni: str
    reality_public_key: str
    reality_short_id: str
    reality_dest: str
    reality_fingerprint: str

    class Config:
        from_attributes = True


class ClientCreate(BaseModel):
    inbound_id: int
    username: str


class ClientOut(BaseModel):
    id: int
    inbound_id: int
    username: str
    uuid: str
    level: int

    class Config:
        from_attributes = True
