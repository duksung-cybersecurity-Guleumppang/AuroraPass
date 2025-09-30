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

echo "[ApplicationStart] reset infra (DEV ONLY) - down with volumes"
dc --env-file .env down -v --remove-orphans || true

echo "[ApplicationStart] bring up infra (db/redis)"
dc --env-file .env up -d postgres redis

echo "[ApplicationStart] run migrator once"
dc --env-file .env run --rm migrator

echo "[ApplicationStart] bring up app"
dc --env-file .env up -d backend frontend

# 호스트에 Nginx를 쓰는 경우만 재로드 (없으면 skip)
if command -v nginx &>/dev/null; then
  if sudo nginx -t; then
    echo "[ApplicationStart] nginx reload"
    sudo systemctl reload nginx || true
  fi
fi
