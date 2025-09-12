#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/aurorapass/AuroraPass"
cd "$APP_DIR" || exit 1

dc() {
  if docker compose version &>/dev/null; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

echo "[ApplicationStart] docker compose up -d"
dc --env-file .env up -d --remove-orphans

# 호스트에 Nginx를 쓰는 경우만 재로드 (없으면 skip)
if command -v nginx &>/dev/null; then
  if sudo nginx -t; then
    echo "[ApplicationStart] nginx reload"
    sudo systemctl reload nginx || true
  fi
fi
