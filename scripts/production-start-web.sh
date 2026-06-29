#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${CDI_API_BASE_URL:?CDI_API_BASE_URL is required}"
: "${CDI_TENANT_ID:?CDI_TENANT_ID is required}"

if [[ -z "${CDI_AUTH_TOKEN:-}" && -z "${CDI_SERVICE_TOKEN_HMAC_SECRET:-}" ]]; then
  echo "CDI_AUTH_TOKEN or CDI_SERVICE_TOKEN_HMAC_SECRET is required" >&2
  exit 2
fi

export NODE_ENV=production

exec npm --workspace @causal-deal/web exec next -- start \
  --hostname "${CDI_WEB_HOST:-127.0.0.1}" \
  --port "${CDI_WEB_PORT:-3000}"
