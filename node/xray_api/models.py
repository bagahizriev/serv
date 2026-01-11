from sqlalchemy import Column, Integer, String, ForeignKey, text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Inbound(Base):
    __tablename__ = "inbounds"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)      # имя inbound
    address = Column(String, default="")               # адрес сервера для клиента (ip/домен)
    listen = Column(String, default="0.0.0.0")
    port = Column(Integer, default=443)
    protocol = Column(String, default="vless")
    network = Column(String, default="tcp")
    security = Column(String, default="tls")           # tls/reality/none
    sni = Column(String, default="")                   # SNI-приманка
    reality_private_key = Column(String, default="")
    reality_public_key = Column(String, default="")
    reality_short_id = Column(String, default="")
    reality_dest = Column(String, default="")
    reality_fingerprint = Column(String, default="chrome")
    clients = relationship("Client", back_populates="inbound", cascade="all, delete")

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    uuid = Column(String, unique=True)
    level = Column(Integer, default=0)
    inbound_id = Column(Integer, ForeignKey("inbounds.id"))
    inbound = relationship("Inbound", back_populates="clients")

def ensure_schema(engine):
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(inbounds)"))}
        to_add = []
        if "address" not in cols:
            to_add.append("ALTER TABLE inbounds ADD COLUMN address VARCHAR DEFAULT ''")
        if "reality_private_key" not in cols:
            to_add.append("ALTER TABLE inbounds ADD COLUMN reality_private_key VARCHAR DEFAULT ''")
        if "reality_public_key" not in cols:
            to_add.append("ALTER TABLE inbounds ADD COLUMN reality_public_key VARCHAR DEFAULT ''")
        if "reality_short_id" not in cols:
            to_add.append("ALTER TABLE inbounds ADD COLUMN reality_short_id VARCHAR DEFAULT ''")
        if "reality_dest" not in cols:
            to_add.append("ALTER TABLE inbounds ADD COLUMN reality_dest VARCHAR DEFAULT ''")
        if "reality_fingerprint" not in cols:
            to_add.append("ALTER TABLE inbounds ADD COLUMN reality_fingerprint VARCHAR DEFAULT 'chrome'")
        for ddl in to_add:
            conn.execute(text(ddl))
        conn.commit()
