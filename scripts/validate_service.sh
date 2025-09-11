#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/aurorapass/AuroraPass"
cd "$APP_DIR" || exit 1

# .env 로드(있다면) → 환경변수 노출
set -a
[ -f ".env" ] && . ".env"
set +a

# 네 .env 기준 변수명 사용 (둘 다 대응)
BACKEND_PORT="${BACKEND_PORT:-${BACK_PORT:-8000}}"
FRONT_PORT="${FRONT_PORT:-3000}"

try_url() {
  local url="$1"
  echo "[ValidateService] check $url"
  curl -fsS --max-time 3 "$url" >/dev/null
}

BACK_CANDIDATES=(
  "http://localhost:${BACKEND_PORT}/healthz"
  "http://localhost:${BACKEND_PORT}/health"
  "http://localhost:${BACKEND_PORT}/docs"
  "http://localhost:${BACKEND_PORT}/"
)
FRONT_CANDIDATES=(
  "http://localhost:${FRONT_PORT}/"
)

for i in $(seq 1 40); do # 최대 약 120초 (3초 x 40)
  for u in "${BACK_CANDIDATES[@]}"; do
    if try_url "$u"; then
      echo "[ValidateService] Backend OK: $u"; exit 0
    fi
  done
  for u in "${FRONT_CANDIDATES[@]}"; do
    if try_url "$u"; then
      echo "[ValidateService] Frontend OK: $u"; exit 0
    fi
  done
  echo "[ValidateService] not ready... ($i/40)"; sleep 3
done

echo "[ValidateService] 헬스체크 실패" >&2
exit 1
