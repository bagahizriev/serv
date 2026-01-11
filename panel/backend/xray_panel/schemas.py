from pydantic import BaseModel
from typing import Optional


class NodeCreate(BaseModel):
    name: str
    url: str
    node_key: str


class NodeUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    node_key: Optional[str] = None


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


class InboundUpdate(BaseModel):
    name: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    network: Optional[str] = None
    security: Optional[str] = None
    sni: Optional[str] = None
    reality_dest: Optional[str] = None
    reality_fingerprint: Optional[str] = None


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


class ClientUpdate(BaseModel):
    username: Optional[str] = None
    level: Optional[int] = None


class ClientOut(BaseModel):
    id: int
    inbound_id: int
    username: str
    uuid: str
    level: int

    class Config:
        from_attributes = True
