#!/bin/sh
set -eux

PORT="${PORT:-8000}"

term_handler() {
  echo "[entrypoint] SIGTERM received, forwarding to uvicorn (if running)"
  if [ -n "${UVICORN_PID:-}" ] && kill -0 "$UVICORN_PID" 2>/dev/null; then
    kill -TERM "$UVICORN_PID" 2>/dev/null || true
    wait "$UVICORN_PID" 2>/dev/null || true
  fi
  echo "[entrypoint] graceful shutdown completed; exiting 0"
  exit 0
}

trap term_handler TERM INT

if [ "${RUN_BOOTSTRAP:-0}" = "1" ]; then
  echo "[entrypoint] running bootstrap"
  python scripts/bootstrap.py || true
else
  echo "[entrypoint] skipping bootstrap (RUN_BOOTSTRAP!=1)"
fi

echo "[entrypoint] starting uvicorn on port ${PORT}"
exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT}" --lifespan on --access-log


