#!/usr/bin/env bash
set -euo pipefail

# --- Настройки (отредактируй под себя) ---
REPO_URL="https://github.com/REPLACE_ME/REPLACE_ME.git"
REPO_DIR="/opt/xray-project"
BRANCH="main"

NODE_ADDRESS="REPLACE_WITH_YOUR_VPS_IP_OR_DOMAIN"   # то, что будет в VLESS URI (host)
API_KEY="REPLACE_WITH_STRONG_KEY"

VPN_PORT="443"                 # внешний порт ноды для клиентов
API_PORT="8585"                 # порт API ноды
EXPOSE_API_PUBLIC="false"       # true -> откроет API наружу; false -> только localhost

ENABLE_UFW="true"              # настроить firewall через ufw
PANEL_IP_ALLOW=""              # если EXPOSE_API_PUBLIC=true: можно указать IP панели (тогда API будет доступно только с него)

IMAGE_NAME="xray-node"
CONTAINER_NAME="xray-node"

# --- Проверки ---
if [[ "$(id -u)" -ne 0 ]]; then
  echo "Запусти скрипт от root (sudo)."
  exit 1
fi

if [[ "$REPO_URL" == *"REPLACE_ME"* ]]; then
  echo "Сначала укажи REPO_URL в начале файла."
  exit 1
fi

if [[ "$NODE_ADDRESS" == *"REPLACE_WITH"* ]]; then
  echo "Сначала укажи NODE_ADDRESS (IP/домен VPS) в начале файла."
  exit 1
fi

if [[ "$API_KEY" == *"REPLACE_WITH"* ]]; then
  echo "Сначала укажи API_KEY в начале файла."
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

echo "[1/6] Обновление системы и пакетов..."
apt-get update -y
apt-get upgrade -y
apt-get install -y --no-install-recommends git ca-certificates curl

if [[ "$ENABLE_UFW" == "true" ]]; then
  apt-get install -y --no-install-recommends ufw
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[2/6] Установка Docker..."
  curl -fsSL https://get.docker.com | sh
fi

# Не критично, но удобно
systemctl enable --now docker >/dev/null 2>&1 || true

echo "[3/6] Клонирование/обновление репозитория..."
mkdir -p "$(dirname "$REPO_DIR")"
if [[ -d "$REPO_DIR/.git" ]]; then
  git -C "$REPO_DIR" fetch --all
  git -C "$REPO_DIR" checkout "$BRANCH"
  git -C "$REPO_DIR" pull --ff-only
else
  git clone --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
fi

if [[ "$ENABLE_UFW" == "true" ]]; then
  echo "[4/6] Настройка firewall (ufw)..."
  ufw --force reset
  ufw default deny incoming
  ufw default allow outgoing

  # SSH (чтобы не отрезать себе доступ)
  ufw allow 22/tcp

  # VPN порт
  ufw allow "${VPN_PORT}/tcp"

  if [[ "$EXPOSE_API_PUBLIC" == "true" ]]; then
    if [[ -n "$PANEL_IP_ALLOW" ]]; then
      ufw allow from "$PANEL_IP_ALLOW" to any port "$API_PORT" proto tcp
    else
      ufw allow "${API_PORT}/tcp"
    fi
  else
    # API наружу не открываем
    ufw deny "${API_PORT}/tcp" || true
  fi

  ufw --force enable
fi

echo "[5/6] Сборка Docker-образа ноды..."
docker build -t "$IMAGE_NAME" "$REPO_DIR/node"

echo "[6/6] Запуск контейнера..."
docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true

docker_volume_db="${CONTAINER_NAME}_db"
docker_volume_cfg="${CONTAINER_NAME}_cfg"

docker run -d --name "$CONTAINER_NAME" \
  -e XRAY_API_KEY="$API_KEY" \
  -e XRAY_APPLY_DEBOUNCE_SECONDS="1.5" \
  -e XRAY_NODE_ADDRESS="$NODE_ADDRESS" \
  -v "$docker_volume_db":/var/lib/xray-api \
  -v "$docker_volume_cfg":/etc/xray \
  -p "${VPN_PORT}:${VPN_PORT}" \
  $( [[ "$EXPOSE_API_PUBLIC" == "true" ]] && echo "-p ${API_PORT}:${API_PORT}" || echo "-p 127.0.0.1:${API_PORT}:${API_PORT}" ) \
  "$IMAGE_NAME"

echo "Готово. Проверка API (локально на сервере):"
echo "  curl -H 'X-API-Key: *****' http://127.0.0.1:${API_PORT}/inbounds"
