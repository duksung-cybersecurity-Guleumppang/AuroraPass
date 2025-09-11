#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/aurorapass/AuroraPass"

echo "[BeforeInstall] prepare dir: $APP_DIR"
mkdir -p "$APP_DIR"

dc() { # docker compose 호환 핸들러
  if command -v docker &>/dev/null; then
    if docker compose version &>/dev/null; then
      docker compose "$@"
    elif command -v docker-compose &>/dev/null; then
      docker-compose "$@"
    else
      echo "docker compose/docker-compose 없음" >&2; exit 1
    fi
  else
    echo "docker 미설치" >&2; exit 1
  fi
}

cd "$APP_DIR" || exit 1

echo "[BeforeInstall] docker compose down (if any)"
dc down || true

docker network prune -f || true
