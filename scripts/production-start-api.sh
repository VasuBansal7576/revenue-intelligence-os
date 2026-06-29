#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -n "${CDI_JOB_STORE_PATH:-}" ]]; then
  mkdir -p "$(dirname "$CDI_JOB_STORE_PATH")"
fi

export PYTHONPATH="${PYTHONPATH:-apps/api}"

exec python -m uvicorn app.main:app \
  --host "${CDI_API_HOST:-127.0.0.1}" \
  --port "${CDI_API_PORT:-8010}" \
  --proxy-headers \
  --forwarded-allow-ips "${CDI_FORWARDED_ALLOW_IPS:-127.0.0.1}"
