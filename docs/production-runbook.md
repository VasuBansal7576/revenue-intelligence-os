# Revenue Intelligence OS Runbook

## 0. Local Demo Proof

Run the no-service proof harness before credential handoff:

```bash
bash scripts/t5-docs-proof.sh
```

It writes `.omo/evidence/t5-docs-proof.txt` and checks the README/runbook wiring, npm scripts, demo-mode test contract, and source references for temporal replay, stale-followup risk, and cited actions. It does not call HydraDB, OpenAI, CRM, or the web/API servers.

## 1. Run The Local API And Web Demo

This is the reviewer path for the local DealTrace proof. It uses seeded Northstar data and does not call live HydraDB, OpenAI, or CRM providers.

Start the API:

```bash
npm install
CDI_DEMO_MODE=1 \
CDI_TENANT_ID=tenant_test \
CDI_AUTH_TOKEN=test-token \
PYTHONPATH=apps/api \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Check readiness:

```bash
curl -i 'http://127.0.0.1:8010/health'
curl -i \
  -H "Authorization: Bearer test-token" \
  -H "X-Tenant-Id: tenant_test" \
  'http://127.0.0.1:8010/ops/readiness?tenant_id=tenant_test'
```

Expected local demo runtime is `local-demo`. The ops response includes provider states and missing config names, but no secret values.

Start the web workbench in a second terminal:

```bash
rm -rf apps/web/.next
CDI_API_BASE_URL=http://127.0.0.1:8010 \
CDI_TENANT_ID=tenant_test \
CDI_AUTH_TOKEN=test-token \
npm --workspace @causal-deal/web exec next -- dev --port 3001
```

Open the current deal view:

```text
http://127.0.0.1:3001/deals/deal_northstar_expansion
```

Open the point-in-time replay:

```text
http://127.0.0.1:3001/deals/deal_northstar_expansion?as_of=2026-02-04T15:00:00Z
```

Useful API smoke calls:

```bash
AUTH=(-H "Authorization: Bearer test-token" -H "X-Tenant-Id: tenant_test")
curl 'http://127.0.0.1:8010/deals/deal_northstar_expansion/context?tenant_id=tenant_test' "${AUTH[@]}"
curl 'http://127.0.0.1:8010/deals/deal_northstar_expansion/timeline?tenant_id=tenant_test&as_of=2026-02-04T15:00:00Z' "${AUTH[@]}"
curl 'http://127.0.0.1:8010/intelligence/deal/deal_northstar_expansion?tenant_id=tenant_test' "${AUTH[@]}"
curl 'http://127.0.0.1:8010/pipeline/summary?tenant_id=tenant_test' "${AUTH[@]}"
```

To verify the setup-required branch, stop the `3001` web server first. Then clear the generated Next cache and run one no-env server:

```bash
rm -rf apps/web/.next
env -u CDI_API_BASE_URL -u CDI_TENANT_ID -u CDI_AUTH_TOKEN \
npm --workspace @causal-deal/web exec next -- dev --port 3002
```

Open:

```text
http://127.0.0.1:3002/deals/deal_northstar_expansion
```

The page should render `Configuration required`. Only run one Next dev server against `apps/web/.next` at a time; this generated directory is safe to remove between local proof passes.

## 2. Configure Live Providers

Required for protected API access:

```bash
export CDI_TENANT_ID="tenant_123"
export CDI_AUTH_TOKEN="server-token"
```

Required for the web app to call the API:

```bash
export CDI_API_BASE_URL="http://127.0.0.1:8010"
```

Required for HydraDB and OpenAI provider calls:

```bash
export HYDRA_DB_API_KEY="..."
export HYDRA_DB_BASE_URL="https://api.hydradb.com"
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-5.5"
export OPENAI_TRANSCRIPTION_MODEL="gpt-4o-transcribe"
export PROVIDER_HTTP_TIMEOUT_SECONDS="30"
```

Required for durable ingestion jobs when the default `.cdi/ingestion-jobs.jsonl` path is not suitable:

```bash
export CDI_JOB_STORE_PATH="/var/lib/cdi/ingestion-jobs.jsonl"
```

Free hackathon CRM path:

```bash
export CDI_CRM_PROVIDER="manual"
```

This keeps `POST /crm/sync` useful without any external CRM account. Send JSON source or integration facts with `provider: "manual"` and the route writes them to HydraDB as cited knowledge.

Required only for external CRM sync:

```bash
export CRM_CLIENT_ID="..."
export CRM_CLIENT_SECRET="..."
export CRM_WEBHOOK_SECRET="..."
```

Optional replacement for static bearer auth:

```bash
export CDI_SERVICE_TOKEN_HMAC_SECRET="..."
export CDI_SERVICE_TOKEN_ISSUER="cdi"
export CDI_SERVICE_TOKEN_AUDIENCE="providers"
```

Service-token mode is enabled only when the HMAC secret is present. If it is present, issuer and audience are mandatory. Static bearer auth remains available when service-token mode is not configured.

## 3. Start Live Runtime

```bash
npm install
npm run build
scripts/production-start-api.sh
```

Readiness:

```bash
curl -i 'http://127.0.0.1:8010/health'
curl -i \
  -H "Authorization: Bearer $CDI_AUTH_TOKEN" \
  -H "X-Tenant-Id: $CDI_TENANT_ID" \
  "http://127.0.0.1:8010/ops/readiness?tenant_id=$CDI_TENANT_ID"
```

Before credentials and seeded provider records are supplied, readiness must stay `provider-not-ready`. After credentials are supplied, `live-provider-ready` only means local config basics are present; live provider behavior is not proven until the validation curls below return provider-backed records.

Start web:

```bash
scripts/production-start-web.sh
```

Open:

```text
http://localhost:3000/deals/<deal_id>
```

## 4. Auth Headers

Use these headers for every protected route:

```bash
AUTH=(-H "Authorization: Bearer $CDI_AUTH_TOKEN" -H "X-Tenant-Id: $CDI_TENANT_ID")
```

## 5. Routes And Calls

Transcript ingestion:

```bash
curl -X POST 'http://127.0.0.1:8010/calls/ingest' \
  "${AUTH[@]}" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "'"$CDI_TENANT_ID"'",
    "deal_id": "deal_123",
    "call_id": "call_123",
    "timestamp": "2026-03-04T15:00:00.000Z",
    "duration_seconds": 1800,
    "transcript": "Paste the production transcript here."
  }'
```

Audio ingestion:

```bash
curl -X POST 'http://127.0.0.1:8010/calls/ingest/audio' \
  "${AUTH[@]}" \
  -F "tenant_id=$CDI_TENANT_ID" \
  -F "deal_id=deal_123" \
  -F "call_id=call_audio_123" \
  -F "timestamp=2026-03-04T15:00:00.000Z" \
  -F "duration_seconds=1800" \
  -F "file=@/path/to/call-audio.mp3;type=audio/mpeg"
```

Job status:

```bash
curl 'http://127.0.0.1:8010/calls/jobs/call.ingest:call_123' "${AUTH[@]}"
curl 'http://127.0.0.1:8010/calls/jobs/call.audio:call_audio_123' "${AUTH[@]}"
```

Knowledge ingest:

```bash
curl -X POST 'http://127.0.0.1:8010/knowledge/ingest' \
  "${AUTH[@]}" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "'"$CDI_TENANT_ID"'",
    "record_type": "playbook",
    "id": "playbook_proposal",
    "stage": "Proposal",
    "title": "Proposal Review",
    "content": "Use cited evidence from deal memory.",
    "objection_handlers": [],
    "version": 1,
    "active": true
  }'
```

CRM sync:

```bash
curl -X POST 'http://127.0.0.1:8010/crm/sync' \
  "${AUTH[@]}" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "'"$CDI_TENANT_ID"'",
    "provider": "salesforce",
    "record_type": "integration_fact",
    "deal_id": "deal_123",
    "source_record_id": "opportunity_123",
    "stage": "Proposal",
    "amount": 250000,
    "content": "CRM opportunity state"
  }'
```

Manual CRM sync, no external CRM account:

```bash
curl -X POST 'http://127.0.0.1:8010/crm/sync' \
  "${AUTH[@]}" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "'"$CDI_TENANT_ID"'",
    "provider": "manual",
    "record_type": "integration_fact",
    "deal_id": "deal_123",
    "stage": "Proposal",
    "amount": 250000,
    "content": "Manual CRM stage and amount from the hackathon proof."
  }'
```

Pipeline summary:

```bash
curl 'http://127.0.0.1:8010/pipeline/summary?tenant_id='"$CDI_TENANT_ID" "${AUTH[@]}"
```

Deal context:

```bash
curl 'http://127.0.0.1:8010/deals/deal_123/context?tenant_id='"$CDI_TENANT_ID" "${AUTH[@]}"
```

Timeline:

```bash
curl 'http://127.0.0.1:8010/deals/deal_123/timeline?tenant_id='"$CDI_TENANT_ID" "${AUTH[@]}"
```

Point-in-time replay:

```bash
curl 'http://127.0.0.1:8010/deals/deal_123/timeline?tenant_id='"$CDI_TENANT_ID"'&as_of=2026-03-04T15:00:00.000Z' "${AUTH[@]}"
```

Cited intelligence:

```bash
curl 'http://127.0.0.1:8010/intelligence/deal/deal_123?tenant_id='"$CDI_TENANT_ID" "${AUTH[@]}"
```

## 6. Credential Handoff Checklist

Live provider behavior is not proven until credentials are supplied and the validation commands pass against seeded provider records. Use `docs/credential-handoff-verdict.md` as the reviewer-facing handoff packet.

Only these items require supplied secrets and seeded provider records:

- HydraDB memory ingest with production tenant, deal, contact, call, causal link, deal memory, and contact memory records.
- HydraDB knowledge ingest with playbook, battlecard, ICP definition, source fact, and integration fact records.
- HydraDB query coverage for context, timeline, intelligence, and pipeline summary.
- OpenAI Responses extraction for transcript ingestion and cited intelligence.
- OpenAI audio transcription or local `CDI_TRANSCRIPTION_COMMAND` proof for `POST /calls/ingest/audio`.
- CRM provider credentials for `POST /crm/sync`.
- HMAC service-token verification with the production secret, issuer, and audience.
- Production host installation of the checked-in process-manager and HTTPS ingress templates.
- Managed secret storage, log retention policy, and provider observability wiring in the target platform.

Local proof before credential handoff covers fail-closed config behavior, request/response shape validation, citation enforcement, tenant auth, job status persistence, and web setup-required rendering.

## 7. Process Manager And Deployment Handoff

This repo ships systemd and nginx templates for a VM deployment:

```bash
deploy/systemd/cdi-api.service
deploy/systemd/cdi-web.service
deploy/nginx/revenue-intelligence-os.conf
```

Use `.env.production.example` as the source for the managed env file. The default systemd units expect `/etc/cdi/revenue-intelligence-os.env`, `/opt/revenue-intelligence-os`, and `/var/lib/cdi`.

Deployment gate before opening traffic:

```bash
curl -i 'http://127.0.0.1:8010/health'
curl -i -H "Authorization: Bearer $CDI_AUTH_TOKEN" -H "X-Tenant-Id: $CDI_TENANT_ID" "http://127.0.0.1:8010/ops/readiness?tenant_id=$CDI_TENANT_ID"
npm run check
bash scripts/production-smoke.sh
npm audit --json
```

Do not treat deployment as complete until the process manager restarts both processes cleanly, the readiness label is expected for the credential state, logs redact secrets, and rollback/cleanup commands are documented in the deployment platform.

## 8. Audit And Export Operations

Audit and export routes are read-only in this handoff:

```bash
curl "http://127.0.0.1:8010/audit/events?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
curl "http://127.0.0.1:8010/exports?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
curl "http://127.0.0.1:8010/exports/export_pipeline_snapshot?tenant_id=$CDI_TENANT_ID" "${AUTH[@]}"
```

## 9. npm Audit Risk Note

Latest local `npm audit --json` exits `1` with two moderate findings: `postcss` XSS exposure pulled through `next`. The suggested automated fix downgrades the app to `next@9.3.3`, and current stable `next@16.2.9` still pins `postcss@8.4.31`; do not apply the forced downgrade as a production fix.

## 10. Verification

Docs/proof harness:

```bash
bash scripts/t5-docs-proof.sh
```

Full product gate after dependencies and local runtimes are ready:

```bash
npm run check
```
