#!/bin/bash
# install_xray_bare.sh
set -e

if [ "$(id -u)" -ne 0 ]; then
    echo "Запустите скрипт от root!"
    exit 1
fi

# --- Домен и email ---
read -p "Введите домен для Xray: " DOMAIN_NAME
read -p "Введите email для Let's Encrypt: " EMAIL

if [ -z "$DOMAIN_NAME" ] || [ -z "$EMAIL" ]; then
    echo "Домен и email обязательны!"
    exit 1
fi

# --- Пути ---
XRAY_CONFIG="/usr/local/etc/xray/config.json"

# --- Установка зависимостей ---
apt update && apt install -y curl socat snapd
snap install core; snap refresh core
snap install --classic certbot
ln -sf /snap/bin/certbot /usr/bin/certbot

# --- Получение TLS сертификата ---
systemctl stop nginx || true
certbot certonly --standalone --non-interactive --agree-tos --email "$EMAIL" -d "$DOMAIN_NAME"

# --- Установка Xray ---
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install

# --- Минимальный конфиг Xray ---
mkdir -p $(dirname $XRAY_CONFIG)
cat > $XRAY_CONFIG <<EOL
{
  "log": {"loglevel": "warning"},
  "inbounds": [
    {
      "listen": "127.0.0.1",
      "port": 10001,
      "protocol": "vless",
      "settings": {"clients": [], "decryption": "none"},
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {
          "certificates": [
            {
              "certificateFile": "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem",
              "keyFile": "/etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem"
            }
          ]
        }
      }
    }
  ],
  "outbounds": [{"protocol": "freedom"}]
}
EOL

# --- Запуск Xray ---
systemctl enable --now xray.service

echo "✅ Xray установлен и работает на 127.0.0.1:10001 с TLS"
echo "TLS-сертификат выпущен для $DOMAIN_NAME"
