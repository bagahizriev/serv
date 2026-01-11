#!/bin/sh
set -eu

: "${XRAY_NODE_KEY:?XRAY_NODE_KEY is required}"

mkdir -p /etc/xray

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

exec "$@"
