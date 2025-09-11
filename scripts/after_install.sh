#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/aurorapass/AuroraPass"
cd "$APP_DIR" || exit 1

# 서버에 별도 .env가 있으면 우선 사용 (민감값 보호)
if [ -f "/opt/aurorapass/.env" ]; then
  cp -f /opt/aurorapass/.env "$APP_DIR/.env"
elif [ ! -f "$APP_DIR/.env" ] && [ -f "$APP_DIR/example.env" ]; then
  echo "[AfterInstall] .env가 없어 example.env를 복사합니다. 실제 값으로 수정하세요."
  cp "$APP_DIR/example.env" "$APP_DIR/.env"
fi

dc() {
  if docker compose version &>/dev/null; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

echo "[AfterInstall] docker compose pull"
dc pull || true

echo "[AfterInstall] docker compose build --pull"
dc build --pull
