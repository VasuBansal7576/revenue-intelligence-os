#!/usr/bin/env bash
set -u

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8010}"
PROVIDER_API_BASE_URL="${PROVIDER_API_BASE_URL:-}"
TENANT_ID="${CDI_TENANT_ID:?CDI_TENANT_ID is required}"
AUTH_TOKEN="${CDI_AUTH_TOKEN:?CDI_AUTH_TOKEN is required}"

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

failures=0

run_case() {
  local id="$1"
  local expected="$2"
  local method="$3"
  local path="$4"
  local body="${5:-}"
  local url="${API_BASE_URL}${path}"
  local status

  echo
  echo "surfaceEvidence scenario=${id} surface=http invocation=\"curl -i -X ${method} ${url}\" expected=${expected}"
  if [[ -n "$body" ]]; then
    status="$(curl -sS -i -o "$tmp" -w "%{http_code}" \
      -X "$method" \
      -H "Authorization: Bearer ${AUTH_TOKEN}" \
      -H "X-Tenant-Id: ${TENANT_ID}" \
      -H "Content-Type: application/json" \
      --data "$body" \
      "$url")"
  else
    status="$(curl -sS -i -o "$tmp" -w "%{http_code}" \
      -X "$method" \
      -H "Authorization: Bearer ${AUTH_TOKEN}" \
      -H "X-Tenant-Id: ${TENANT_ID}" \
      "$url")"
  fi
  cat "$tmp"
  echo
  echo "result scenario=${id} status=${status}"
  if [[ "$status" != "$expected" ]]; then
    echo "FAIL scenario=${id} expected=${expected} actual=${status}"
    failures=$((failures + 1))
  else
    echo "PASS scenario=${id}"
  fi
}

run_public_case() {
  local id="$1"
  local expected="$2"
  local path="$3"
  local url="${API_BASE_URL}${path}"
  local status

  echo
  echo "surfaceEvidence scenario=${id} surface=http invocation=\"curl -i ${url}\" expected=${expected}"
  status="$(curl -sS -i -o "$tmp" -w "%{http_code}" "$url")"
  cat "$tmp"
  echo
  echo "result scenario=${id} status=${status}"
  if [[ "$status" != "$expected" ]]; then
    echo "FAIL scenario=${id} expected=${expected} actual=${status}"
    failures=$((failures + 1))
  else
    echo "PASS scenario=${id}"
  fi
}

run_case_no_auth() {
  local id="$1"
  local expected="$2"
  local method="$3"
  local path="$4"
  local url="${API_BASE_URL}${path}"
  local status

  echo
  echo "surfaceEvidence scenario=${id} surface=http invocation=\"curl -i -X ${method} ${url} -H 'Authorization: Bearer wrong-token' -H 'X-Tenant-Id: ${TENANT_ID}'\" expected=${expected}"
  status="$(curl -sS -i -o "$tmp" -w "%{http_code}" \
    -X "$method" \
    -H "Authorization: Bearer wrong-token" \
    -H "X-Tenant-Id: ${TENANT_ID}" \
    "$url")"
  cat "$tmp"
  echo
  echo "result scenario=${id} status=${status}"
  if [[ "$status" != "$expected" ]]; then
    echo "FAIL scenario=${id} expected=${expected} actual=${status}"
    failures=$((failures + 1))
  else
    echo "PASS scenario=${id}"
  fi
}

run_provider_case() {
  if [[ -z "$PROVIDER_API_BASE_URL" ]]; then
    return
  fi
  local id="$1"
  local expected="$2"
  local method="$3"
  local path="$4"
  local body="${5:-}"
  local url="${PROVIDER_API_BASE_URL}${path}"
  local status

  echo
  echo "surfaceEvidence scenario=${id} surface=http invocation=\"curl -i -X ${method} ${url}\" expected=${expected}"
  if [[ -n "$body" ]]; then
    status="$(curl -sS -i -o "$tmp" -w "%{http_code}" \
      -X "$method" \
      -H "Authorization: Bearer ${AUTH_TOKEN}" \
      -H "X-Tenant-Id: ${TENANT_ID}" \
      -H "Content-Type: application/json" \
      --data "$body" \
      "$url")"
  else
    status="$(curl -sS -i -o "$tmp" -w "%{http_code}" \
      -X "$method" \
      -H "Authorization: Bearer ${AUTH_TOKEN}" \
      -H "X-Tenant-Id: ${TENANT_ID}" \
      "$url")"
  fi
  cat "$tmp"
  echo
  echo "result scenario=${id} status=${status}"
  if [[ "$status" != "$expected" ]]; then
    echo "FAIL scenario=${id} expected=${expected} actual=${status}"
    failures=$((failures + 1))
  else
    echo "PASS scenario=${id}"
  fi
}

tenant_qs="?tenant_id=${TENANT_ID}"

run_public_case "health" "200" "/health"
run_case "readiness" "200" "GET" "/ops/readiness${tenant_qs}"

run_case "accounts-list" "200" "GET" "/accounts${tenant_qs}"
run_case "accounts-detail" "200" "GET" "/accounts/account_northstar${tenant_qs}"
run_case "deals-list" "200" "GET" "/deals${tenant_qs}"
run_case "deal-context" "200" "GET" "/deals/deal_northstar_expansion/context${tenant_qs}"
run_case "deal-timeline" "200" "GET" "/deals/deal_northstar_expansion/timeline${tenant_qs}"
run_case "deal-timeline-as-of" "200" "GET" "/deals/deal_northstar_expansion/timeline${tenant_qs}&as_of=2026-02-04T15:00:00Z"
run_case "calls-list" "200" "GET" "/calls${tenant_qs}"
run_case "calls-detail" "200" "GET" "/calls/call_ns_005${tenant_qs}"
run_case "search" "200" "GET" "/search${tenant_qs}&q=Northstar"
run_case "pipeline-summary" "200" "GET" "/pipeline/summary${tenant_qs}"
run_case "intelligence" "200" "GET" "/intelligence/deal/deal_northstar_expansion${tenant_qs}"
run_case "forecast-summary" "200" "GET" "/forecast/summary${tenant_qs}"
run_case "forecast-submissions" "200" "GET" "/forecast/submissions${tenant_qs}"
run_case "coaching-scorecards" "200" "GET" "/coaching/scorecards${tenant_qs}"
run_case "coaching-rep" "200" "GET" "/coaching/reps/user_maya${tenant_qs}"
run_case "engage-tasks" "200" "GET" "/engage/tasks${tenant_qs}"
run_case "engage-task-detail" "200" "GET" "/engage/tasks/task_followup_cfo${tenant_qs}"
run_case "assistant-query" "200" "POST" "/assistant/query${tenant_qs}" '{"question":"why is Northstar risky?"}'
run_case "admin-users" "200" "GET" "/admin/users${tenant_qs}"
run_case "admin-settings" "200" "GET" "/admin/settings${tenant_qs}"
run_case "audit-events" "200" "GET" "/audit/events${tenant_qs}"
run_case "exports-list" "200" "GET" "/exports${tenant_qs}"
run_case "exports-detail" "200" "GET" "/exports/export_pipeline_snapshot${tenant_qs}"

run_case_no_auth "failure-403-invalid-token" "403" "GET" "/forecast/summary${tenant_qs}"
run_case "failure-403-tenant-mismatch" "403" "GET" "/forecast/summary?tenant_id=tenant_other"
run_case "failure-405-engage-mutation" "405" "PATCH" "/engage/tasks/task_followup_cfo${tenant_qs}"
run_case "failure-503-knowledge-provider" "503" "POST" "/knowledge/ingest" "{\"tenant_id\":\"${TENANT_ID}\",\"record_type\":\"playbook\",\"id\":\"matrix_playbook\"}"
run_case "failure-503-crm-provider" "503" "POST" "/crm/sync" "{\"tenant_id\":\"${TENANT_ID}\",\"provider\":\"salesforce\",\"record_type\":\"integration_fact\",\"id\":\"matrix_crm\"}"
run_provider_case "failure-503-accounts-provider-mode" "503" "GET" "/accounts${tenant_qs}"
run_provider_case "failure-503-engage-provider-mode" "503" "GET" "/engage/tasks${tenant_qs}"
run_provider_case "failure-503-assistant-provider-mode" "503" "POST" "/assistant/query${tenant_qs}" '{"question":"why is Northstar risky?"}'

echo
echo "matrix_failures=${failures}"
if [[ "$failures" -ne 0 ]]; then
  exit 1
fi
