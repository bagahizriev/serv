#!/bin/sh
set -eu

: "${XRAY_API_KEY:?XRAY_API_KEY is required}"

mkdir -p /etc/xray /var/lib/xray-api

chown -R xrayapi:xrayapi /var/lib/xray-api
chown -R xrayapi:xrayapi /etc/xray

if [ ! -f /etc/xray/config.json ]; then
  cat > /etc/xray/config.json <<'EOF'
{
  "log": {"loglevel": "warning"},
  "inbounds": [],
  "outbounds": [{"protocol": "freedom"}]
}
EOF
fi

if [ ! -f /var/lib/xray-api/xray.db ]; then
  cd /app
  /app/venv/bin/python -c 'from sqlalchemy import create_engine; from xray_api.models import ensure_schema; import os; db=os.environ.get("XRAY_API_DB_PATH","/var/lib/xray-api/xray.db"); os.makedirs(os.path.dirname(db), exist_ok=True); engine=create_engine(f"sqlite:///{db}", connect_args={"check_same_thread": False}); ensure_schema(engine)'
fi

exec "$@"
