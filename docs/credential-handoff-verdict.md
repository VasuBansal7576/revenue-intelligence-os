# Credential Handoff Verdict

This repo is production-shaped for a local Gong-style Revenue Intelligence OS, but live provider behavior is not proven until credentials and seeded records are supplied.

## What Is Proven Now

- Local demo mode: `CDI_DEMO_MODE=1` with tenant auth.
- Revenue surfaces: deals, accounts, calls, forecast, coaching, engagement tasks, assistant, admin, audit, exports, ingestion, and the existing DealTrace workbench.
- Tenant boundary: protected routes require `Authorization: Bearer <token>` and `X-Tenant-Id`.
- Fail-closed provider behavior: missing provider config reports `provider-not-ready` or explicit missing config names.
- Readiness labels: `local-demo`, `provider-not-ready`, and `live-provider-ready`.
- Automated proof: `npm run check`, API curl matrix, browser smoke, setup-required smoke, and cleanup receipts under `.omo/evidence/production-gong/`.

## Credential Inputs Required

```bash
export CDI_TENANT_ID="tenant_123"
export CDI_AUTH_TOKEN="server-token"
export CDI_API_BASE_URL="http://127.0.0.1:8010"

export HYDRA_DB_API_KEY="..."
export HYDRA_DB_BASE_URL="https://api.hydradb.com"

# Option A: OpenAI API key, required for audio transcription.
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-5.5"
export OPENAI_TRANSCRIPTION_MODEL="gpt-4o-transcribe"

# Option B: Codex subscription auth for text LLM responses.
export CDI_LLM_PROVIDER="codex"
export CDI_LLM_MODEL="gpt-5.3-codex"
export CODEX_AUTH_FILE="$HOME/.codex/auth.json"

# Optional local/free audio transcription command.
# The command must print transcript text to stdout.
export CDI_TRANSCRIPTION_COMMAND="uv run '$PWD/scripts/transcribe_faster_whisper.py' {audio_path}"

export CRM_CLIENT_ID="..."
export CRM_CLIENT_SECRET="..."
export CRM_WEBHOOK_SECRET="..."

export CDI_JOB_STORE_PATH="/var/lib/cdi/ingestion-jobs.jsonl"
```

Optional service-token auth:

```bash
export CDI_SERVICE_TOKEN_HMAC_SECRET="..."
export CDI_SERVICE_TOKEN_ISSUER="cdi"
export CDI_SERVICE_TOKEN_AUDIENCE="providers"
```

## Seed Requirements

These seed requirements must be satisfied before live provider validation can pass.

HydraDB must contain provider records for the target tenant before live validation can pass:

- `tenant`
- `deal`
- `contact`
- `deal_memory`
- `contact_memory`
- `call_event`
- `causal_link`
- `playbook`
- `battlecard`
- `icp_definition`
- `source_fact`
- `integration_fact`
- `account`
- `role`
- `user`
- `admin_setting`
- `call_library_entry`
- `coaching_scorecard`
- `forecast_submission`
- `engagement_task`
- `assistant_answer`
- `audit_event`
- `export_job`

Deal-scoped records need `tenant_id` and `deal_id`. Tenant-wide records need `tenant_id`. The detailed provider contract is in `docs/hydradb-integration.md`.

## Live Validation Commands

Start API and web after exporting credentials:

```bash
PYTHONPATH=apps/api python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
CDI_API_BASE_URL=http://127.0.0.1:8010 npm run dev
```

Check readiness:

```bash
curl -i http://127.0.0.1:8010/health
curl -i \
  -H "Authorization: Bearer $CDI_AUTH_TOKEN" \
  -H "X-Tenant-Id: $CDI_TENANT_ID" \
  "http://127.0.0.1:8010/ops/readiness?tenant_id=$CDI_TENANT_ID"
```

Validate provider-backed surfaces:

```bash
AUTH=(-H "Authorization: Bearer $CDI_AUTH_TOKEN" -H "X-Tenant-Id: $CDI_TENANT_ID")

curl -i "http://127.0.0.1:8010/accounts?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
curl -i "http://127.0.0.1:8010/deals?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
curl -i "http://127.0.0.1:8010/calls?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
curl -i "http://127.0.0.1:8010/forecast/summary?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
curl -i "http://127.0.0.1:8010/coaching/scorecards?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
curl -i "http://127.0.0.1:8010/engage/tasks?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
curl -i "http://127.0.0.1:8010/admin/users?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
curl -i "http://127.0.0.1:8010/audit/events?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
curl -i "http://127.0.0.1:8010/exports?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
curl -i "http://127.0.0.1:8010/pipeline/summary?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
curl -i "http://127.0.0.1:8010/deals/<deal_id>/context?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
curl -i "http://127.0.0.1:8010/deals/<deal_id>/timeline?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
curl -i "http://127.0.0.1:8010/intelligence/deal/<deal_id>?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
```

Validate write paths:

```bash
curl -i -X POST "http://127.0.0.1:8010/calls/ingest" \
  "${AUTH[@]}" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"'"$CDI_TENANT_ID"'","deal_id":"<deal_id>","call_id":"<call_id>","timestamp":"2026-03-04T15:00:00.000Z","duration_seconds":1800,"transcript":"Paste production transcript here."}'

curl -i -X POST "http://127.0.0.1:8010/crm/sync" \
  "${AUTH[@]}" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"'"$CDI_TENANT_ID"'","provider":"salesforce","record_type":"integration_fact","deal_id":"<deal_id>","source_record_id":"<crm_id>","stage":"Proposal","amount":250000,"content":"CRM opportunity state"}'
```

## Rollback And Cleanup

Local cleanup:

```bash
pkill -f "uvicorn app.main:app" || true
pkill -f "next.*dev" || true
rm -rf apps/web/.next
rm -rf apps/api/app/**/__pycache__
rm -f .cdi/ingestion-jobs.jsonl
```

Deployment rollback should restore the previous process-manager unit or release artifact, rotate any exposed secrets, and re-run `/ops/readiness` plus `npm run check` before traffic is reopened.

## Final Boundary

The current verdict is non-credential productionization complete. Live HydraDB, LLM responses, audio transcription, CRM, deployment restart policy, HTTPS ingress, managed secret storage, log retention, and provider observability remain not proven until credentials or local command configuration are supplied and the live validation commands pass against seeded provider records. Codex subscription auth can satisfy text LLM responses, but it does not replace audio transcription; use OpenAI audio or `CDI_TRANSCRIPTION_COMMAND`.
