from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Inbound(Base):
    __tablename__ = "inbounds"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)      # имя inbound
    listen = Column(String, default="0.0.0.0")
    port = Column(Integer, default=443)
    protocol = Column(String, default="vless")
    network = Column(String, default="tcp")
    security = Column(String, default="tls")           # tls/reality/none
    sni = Column(String, default="")                   # SNI-приманка
    clients = relationship("Client", back_populates="inbound", cascade="all, delete")

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    uuid = Column(String, unique=True)
    level = Column(Integer, default=0)
    inbound_id = Column(Integer, ForeignKey("inbounds.id"))
    inbound = relationship("Inbound", back_populates="clients")
