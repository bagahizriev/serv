from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    url = Column(String, nullable=False)
    node_key = Column(String, nullable=False)

    inbounds = relationship("Inbound", back_populates="node", cascade="all, delete")


class Inbound(Base):
    __tablename__ = "inbounds"
    __table_args__ = (
        UniqueConstraint("node_id", "name", name="uq_inbounds_node_name"),
    )

    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)

    name = Column(String, nullable=False)
    listen = Column(String, default="0.0.0.0")
    port = Column(Integer, default=443)
    protocol = Column(String, default="vless")
    network = Column(String, default="tcp")
    security = Column(String, default="reality")
    sni = Column(String, default="")

    reality_private_key = Column(String, default="")
    reality_public_key = Column(String, default="")
    reality_short_id = Column(String, default="")
    reality_dest = Column(String, default="")
    reality_fingerprint = Column(String, default="chrome")

    node = relationship("Node", back_populates="inbounds")
    clients = relationship("Client", back_populates="inbound", cascade="all, delete")


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (
        UniqueConstraint("inbound_id", "username", name="uq_clients_inbound_username"),
    )

    id = Column(Integer, primary_key=True)
    inbound_id = Column(Integer, ForeignKey("inbounds.id"), nullable=False)

    username = Column(String, nullable=False)
    uuid = Column(String, nullable=False, unique=True)
    level = Column(Integer, default=0)

    inbound = relationship("Inbound", back_populates="clients")
