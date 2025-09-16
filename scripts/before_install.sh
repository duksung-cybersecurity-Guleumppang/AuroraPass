#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/opt/aurorapass"
APP_DIR="$APP_ROOT/AuroraPass"

echo "[BeforeInstall] prepare: $APP_DIR"
sudo mkdir -p "$APP_ROOT"

# docker compose 호환 핸들러
dc() {
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

# 이미 떠있을 수 있는 컨테이너 정리 (실패해도 계속 진행)
echo "[BeforeInstall] docker compose down (if any)"
cd "$APP_DIR" 2>/dev/null && dc down || true

# 네트워크/찌꺼기 정리 (선택)
sudo docker network prune -f || true

# === 핵심: 이전 배포물 깨끗하게 제거 ===
# 주의: .env는 APP_ROOT(/opt/aurorapass/.env)에 있어서 영향 없음
if [ -d "$APP_DIR" ]; then
  echo "[BeforeInstall] clean old deploy dir: $APP_DIR"
  sudo rm -rf "$APP_DIR"
fi

# 새 디렉터리 준비 및 권한
sudo mkdir -p "$APP_DIR"
sudo chown -R ubuntu:ubuntu "$APP_ROOT"

echo "[BeforeInstall] ready."
