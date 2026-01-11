#!/usr/bin/env bash
set -euo pipefail

# ================== БАЗОВЫЕ НАСТРОЙКИ ==================
REPO_URL="https://github.com/bagahizriev/serv.git"
REPO_DIR="/opt/xray-project"
BRANCH="main"

VPN_PORT="443"                  # внешний порт ноды для клиентов
API_PORT="8585"                 # порт API ноды
EXPOSE_API_PUBLIC="true"        # true -> API доступен извне
ENABLE_UFW="true"               # включить firewall (ufw)

# IP, которым разрешён доступ к API (если API открыт публично)
API_ALLOW_IPS=("46.32.186.181" "146.158.124.131")

IMAGE_NAME="xray-node"
CONTAINER_NAME="xray-node"

# ================== АВТОНАСТРОЙКИ ==================
echo "[*] Определение публичного IP..."
NODE_ADDRESS="$(curl -fsSL https://api.ipify.org || curl -fsSL https://ifconfig.me)"

if [[ -z "$NODE_ADDRESS" ]]; then
  echo "Не удалось определить публичный IP"
  exit 1
fi

echo "[*] Генерация API ключа..."
API_KEY="$(openssl rand -base64 32 | tr -d '\n')"

export DEBIAN_FRONTEND=noninteractive

# ================== ПРОВЕРКИ ==================
if [[ "$(id -u)" -ne 0 ]]; then
  echo "Запусти скрипт от root (sudo)."
  exit 1
fi

# ================== УСТАНОВКА ==================
echo "[1/6] Обновление системы..."
apt-get update -y
apt-get upgrade -y
apt-get install -y --no-install-recommends git ca-certificates curl openssl

if [[ "$ENABLE_UFW" == "true" ]]; then
  apt-get install -y --no-install-recommends ufw
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[2/6] Установка Docker..."
  curl -fsSL https://get.docker.com | sh
fi

systemctl enable --now docker >/dev/null 2>&1 || true

# ================== РЕПОЗИТОРИЙ ==================
echo "[3/6] Клонирование / обновление репозитория..."
mkdir -p "$(dirname "$REPO_DIR")"

if [[ -d "$REPO_DIR/.git" ]]; then
  git -C "$REPO_DIR" fetch --all
  git -C "$REPO_DIR" checkout "$BRANCH"
  git -C "$REPO_DIR" pull --ff-only
else
  git clone --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
fi

# ================== FIREWALL ==================
if [[ "$ENABLE_UFW" == "true" ]]; then
  echo "[4/6] Настройка UFW..."
  ufw --force reset
  ufw default deny incoming
  ufw default allow outgoing

  ufw allow 22/tcp
  ufw allow "${VPN_PORT}/tcp"

  if [[ "$EXPOSE_API_PUBLIC" == "true" ]]; then
    if [[ ${#API_ALLOW_IPS[@]} -gt 0 ]]; then
      for ip in "${API_ALLOW_IPS[@]}"; do
        ufw allow from "$ip" to any port "$API_PORT" proto tcp
      done
    else
      ufw allow "${API_PORT}/tcp"
    fi
  else
    ufw deny "${API_PORT}/tcp" || true
  fi

  ufw --force enable
fi

# ================== DOCKER ==================
echo "[5/6] Сборка Docker образа..."
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

# ================== ВЫВОД ДАННЫХ ==================
echo
echo "======================================"
echo "   XRAY NODE УСПЕШНО УСТАНОВЛЕНА"
echo "======================================"
echo "IP / HOST:        ${NODE_ADDRESS}"
echo "VPN PORT:         ${VPN_PORT}"
echo "API PORT:         ${API_PORT}"
echo "API KEY:          ${API_KEY}"
echo
echo "Проверка API:"
echo "curl -H \"X-API-Key: ${API_KEY}\" http://127.0.0.1:${API_PORT}/inbounds"
echo "======================================"
