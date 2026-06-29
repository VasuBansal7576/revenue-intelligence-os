#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8010}"
WEB_BASE_URL="${WEB_BASE_URL:-}"
TENANT_ID="${CDI_TENANT_ID:?CDI_TENANT_ID is required}"
AUTH_TOKEN="${CDI_AUTH_TOKEN:-}"
EXPECTED_RUNTIME="${EXPECTED_RUNTIME:-}"

if [[ -z "$AUTH_TOKEN" ]]; then
  echo "CDI_AUTH_TOKEN is required for the smoke gate" >&2
  exit 2
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

check_secret_echo() {
  local body="$1"
  local name value
  for name in HYDRA_DB_API_KEY OPENAI_API_KEY CODEX_ACCESS_TOKEN CDI_AUTH_TOKEN CRM_CLIENT_SECRET CRM_WEBHOOK_SECRET CDI_SERVICE_TOKEN_HMAC_SECRET; do
    value="${!name:-}"
    if [[ -n "$value" ]] && grep -Fq "$value" "$body"; then
      echo "secret leaked in smoke response: $name" >&2
      exit 1
    fi
  done
}

request() {
  local label="$1"
  local expected="$2"
  shift 2
  local status
  status="$(curl -sS -o "$tmp" -w "%{http_code}" "$@")"
  check_secret_echo "$tmp"
  if [[ "$status" != "$expected" ]]; then
    echo "$label failed: expected $expected got $status" >&2
    cat "$tmp" >&2
    exit 1
  fi
  echo "$label ok ($status)"
}

request health 200 "$API_BASE_URL/health"

request readiness 200 \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "X-Tenant-Id: $TENANT_ID" \
  "$API_BASE_URL/ops/readiness?tenant_id=$TENANT_ID"

if [[ -n "$EXPECTED_RUNTIME" ]] && ! grep -Fq "\"runtime\":\"$EXPECTED_RUNTIME\"" "$tmp"; then
  echo "readiness runtime mismatch, expected $EXPECTED_RUNTIME" >&2
  cat "$tmp" >&2
  exit 1
fi

if [[ -n "$WEB_BASE_URL" ]]; then
  request web 200 -L "$WEB_BASE_URL/"
fi

echo "production-smoke-ok"
