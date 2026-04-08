#!/bin/sh
set -e
mkdir -p "${TDL_HOME:-/data/.tdl}" "${DOWNLOAD_DIR:-/data/downloads}" "${DOWNLOAD_DIR:-/data/downloads}/.logs" "${DOWNLOAD_DIR:-/data/downloads}/.jobs"

if [ "$1" = "api" ]; then
  alembic upgrade head
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000
elif [ "$1" = "worker" ]; then
  alembic upgrade head
  shift
  exec celery -A app.workers.celery_app worker --loglevel=INFO "$@"
else
  exec "$@"
fi
