import os
import json
import tempfile
import subprocess
from typing import Optional, Set

from fastapi import FastAPI, Header, HTTPException, Request


XRAY_BIN = os.environ.get("XRAY_BIN", "/usr/local/bin/xray")
XRAY_CONFIG_PATH = os.environ.get("XRAY_CONFIG_PATH", "/etc/xray/config.json")
SUPERVISOR_SERVER_URL = os.environ.get("SUPERVISOR_SERVER_URL", "unix:///tmp/supervisor.sock")

NODE_KEY = os.environ.get("XRAY_NODE_KEY", "")
ALLOW_IPS_RAW = os.environ.get("XRAY_PANEL_ALLOW_IPS", "")


def _parse_allow_ips(raw: str) -> Set[str]:
    ips: Set[str] = set()
    for part in (raw or "").split(","):
        part = part.strip()
        if part:
            ips.add(part)
    return ips


ALLOW_IPS = _parse_allow_ips(ALLOW_IPS_RAW)

app = FastAPI(title="Xray Node Agent")


def _require_node_key(x_node_key: Optional[str]):
    if not NODE_KEY:
        raise HTTPException(status_code=500, detail="Server node key is not configured")
    if x_node_key != NODE_KEY:
        raise HTTPException(status_code=401, detail="Invalid node key")


def _require_allow_ip(request: Request):
    if not ALLOW_IPS:
        return
    client_host = request.client.host if request.client else ""
    if client_host not in ALLOW_IPS:
        raise HTTPException(status_code=403, detail="IP is not allowed")


def _restart_xray():
    subprocess.run(["supervisorctl", "-s", SUPERVISOR_SERVER_URL, "restart", "xray"], check=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/apply-config")
async def apply_config(
    request: Request,
    x_node_key: Optional[str] = Header(default=None, alias="X-Node-Key"),
):
    _require_allow_ip(request)
    _require_node_key(x_node_key)

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Принимаем либо {"config": {...}}, либо сразу объект конфига Xray
    config_obj = payload.get("config") if isinstance(payload, dict) and "config" in payload else payload
    if not isinstance(config_obj, dict):
        raise HTTPException(status_code=400, detail="Config must be a JSON object")

    os.makedirs(os.path.dirname(XRAY_CONFIG_PATH) or ".", exist_ok=True)
    target_dir = os.path.dirname(XRAY_CONFIG_PATH) or "."

    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, dir=target_dir, prefix="config.", suffix=".json") as tmp:
            tmp_path = tmp.name
            json.dump(config_obj, tmp, indent=2)

        subprocess.run([XRAY_BIN, "-test", "-config", tmp_path], check=True)
        os.replace(tmp_path, XRAY_CONFIG_PATH)
        tmp_path = ""

        _restart_xray()
        return {"status": "applied"}

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=400, detail=f"Config test/restart failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
