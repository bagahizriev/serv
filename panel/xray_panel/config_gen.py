from typing import Dict, Any

from .models import Node


def build_node_config(node: Node) -> Dict[str, Any]:
    config: Dict[str, Any] = {
        "log": {"loglevel": "warning"},
        "inbounds": [],
        "outbounds": [{"protocol": "freedom"}],
    }

    for inbound in node.inbounds:
        clients = [
            {"id": c.uuid, "email": c.username, "level": c.level}
            for c in inbound.clients
        ]

        inbound_dict: Dict[str, Any] = {
            "listen": inbound.listen,
            "port": inbound.port,
            "protocol": inbound.protocol,
            "settings": {"clients": clients, "decryption": "none"},
            "streamSettings": {"network": inbound.network},
            "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
        }

        sec = (inbound.security or "").lower()
        if sec == "reality":
            if not inbound.sni:
                raise ValueError("Reality inbound requires sni")
            if not inbound.reality_private_key:
                raise ValueError("Reality inbound requires reality_private_key")
            if not inbound.reality_short_id:
                raise ValueError("Reality inbound requires reality_short_id")
            dest = inbound.reality_dest or f"{inbound.sni}:443"

            inbound_dict["streamSettings"]["security"] = "reality"
            inbound_dict["streamSettings"]["realitySettings"] = {
                "show": False,
                "dest": dest,
                "xver": 0,
                "serverNames": [inbound.sni],
                "privateKey": inbound.reality_private_key,
                "shortIds": [inbound.reality_short_id],
                "spiderX": "/",
            }

        config["inbounds"].append(inbound_dict)

    return config
