#!/usr/bin/env bash
set -euo pipefail

# Обновляет репозиторий на сервере и перезапускает node через актуальный start.sh.
# Запускать на VPS от root: sudo bash update.sh

REPO_DIR="/opt/xray-project"
BRANCH="main"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Запусти скрипт от root (sudo)."
  exit 1
fi

if [[ ! -d "$REPO_DIR/.git" ]]; then
  echo "Не найден git-репозиторий в $REPO_DIR. Сначала выполни первичный деплой через start.sh."
  exit 1
fi

echo "[1/2] Обновление репозитория в $REPO_DIR (ветка: $BRANCH)..."
git -C "$REPO_DIR" fetch --all
git -C "$REPO_DIR" checkout "$BRANCH"
git -C "$REPO_DIR" pull --ff-only

echo "[2/2] Перезапуск ноды через актуальный node/start.sh..."
if [[ ! -f "$REPO_DIR/node/start.sh" ]]; then
  echo "Не найден $REPO_DIR/node/start.sh."
  exit 1
fi

bash "$REPO_DIR/node/start.sh"
