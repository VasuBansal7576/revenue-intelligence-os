# Revenue Intelligence OS

Local proof and production runbook for a Gong-style revenue-intelligence OS built around causal deal memory.

The demo and production paths are intentionally separate:

- Local demo proof is source-backed and runs without provider credentials.
- Live HydraDB, LLM, and CRM work is credential-gated and must fail closed when secrets or seeded records are missing.

## Local Demo Proof

```bash
bash scripts/t5-docs-proof.sh
```

The proof artifact is written to:

```text
.omo/evidence/t5-docs-proof.txt
```

This proof checks the runnable docs surface, npm script listing, the seeded `CDI_DEMO_MODE=1` test contract, and the local wedge claims: DealTrace-style deal context, temporal replay, stale-followup risk, and cited actions. It does not call HydraDB, OpenAI, CRM, or live services.

## Local API And Web Demo

Run the actual local DealTrace workbench with seeded Northstar data:

```bash
npm install
CDI_DEMO_MODE=1 \
CDI_TENANT_ID=tenant_test \
CDI_AUTH_TOKEN=test-token \
PYTHONPATH=apps/api \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

In a second terminal:

```bash
rm -rf apps/web/.next
CDI_API_BASE_URL=http://127.0.0.1:8010 \
CDI_TENANT_ID=tenant_test \
CDI_AUTH_TOKEN=test-token \
npm --workspace @causal-deal/web exec next -- dev --port 3001
```

Open:

```text
http://127.0.0.1:3001/deals/deal_northstar_expansion
http://127.0.0.1:3001/deals/deal_northstar_expansion?as_of=2026-02-04T15:00:00Z
```

API readiness labels are exact: `local-demo`, `provider-not-ready`, or `live-provider-ready`.

```bash
curl -i http://127.0.0.1:8010/health
curl -i \
  -H "Authorization: Bearer test-token" \
  -H "X-Tenant-Id: tenant_test" \
  "http://127.0.0.1:8010/ops/readiness?tenant_id=tenant_test"
```

To verify the setup-required branch, stop the `3001` web server first, clear the generated Next cache, and run one no-env web server:

```bash
rm -rf apps/web/.next
env -u CDI_API_BASE_URL -u CDI_TENANT_ID -u CDI_AUTH_TOKEN \
npm --workspace @causal-deal/web exec next -- dev --port 3002
```

Then open:

```text
http://127.0.0.1:3002/deals/deal_northstar_expansion
```

Only run one Next dev server against `apps/web/.next` at a time; the directory is generated and safe to remove between local proof passes.

## Live Runtime Env

```bash
export CDI_TENANT_ID="tenant_123"
export CDI_AUTH_TOKEN="server-token"
export CDI_API_BASE_URL="http://127.0.0.1:8010"
export HYDRA_DB_API_KEY="..."
export HYDRA_DB_BASE_URL="https://api.hydradb.com"

# LLM option A: OpenAI API key, required for audio transcription.
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-5.5"
export OPENAI_TRANSCRIPTION_MODEL="gpt-4o-transcribe"

# LLM option B: Codex subscription auth for text responses only.
export CDI_LLM_PROVIDER="codex"
export CDI_LLM_MODEL="gpt-5.3-codex"
# Optional; defaults to ~/.codex/auth.json when unset:
export CODEX_AUTH_FILE="$HOME/.codex/auth.json"

# Audio transcription option B: local/free faster-whisper command.
# The command must print transcript text to stdout. Use {audio_path} where the uploaded file path should go.
export CDI_TRANSCRIPTION_COMMAND="uv run '$PWD/scripts/transcribe_faster_whisper.py' {audio_path}"

export CDI_JOB_STORE_PATH=".cdi/ingestion-jobs.jsonl"
export PROVIDER_HTTP_TIMEOUT_SECONDS="30"

# CRM option A: hackathon/free manual CRM facts, no external CRM account.
export CDI_CRM_PROVIDER="manual"

# CRM option B: external CRM connector credentials.
export CRM_CLIENT_ID="..."
export CRM_CLIENT_SECRET="..."
export CRM_WEBHOOK_SECRET="..."

export CDI_SERVICE_TOKEN_HMAC_SECRET="..."
export CDI_SERVICE_TOKEN_ISSUER="cdi"
export CDI_SERVICE_TOKEN_AUDIENCE="providers"
```

`HYDRA_DB_BASE_URL`, `CDI_LLM_PROVIDER`, `CDI_LLM_MODEL`, `OPENAI_MODEL`, `OPENAI_TRANSCRIPTION_MODEL`, `CODEX_AUTH_FILE`, `CDI_JOB_STORE_PATH`, and `PROVIDER_HTTP_TIMEOUT_SECONDS` have defaults. Static bearer auth uses `CDI_AUTH_TOKEN`. HMAC service-token auth is enabled only when `CDI_SERVICE_TOKEN_HMAC_SECRET`, `CDI_SERVICE_TOKEN_ISSUER`, and `CDI_SERVICE_TOKEN_AUDIENCE` are all configured.

`/health` returns `provider-not-ready` until tenant auth basics plus HydraDB, an LLM provider, and CRM are configured. Set `CDI_CRM_PROVIDER=manual` for the free hackathon CRM path, or supply `CRM_CLIENT_ID`, `CRM_CLIENT_SECRET`, and `CRM_WEBHOOK_SECRET` for an external CRM connector. OpenAI uses `OPENAI_API_KEY`; Codex uses `CDI_LLM_PROVIDER=codex` plus `CODEX_ACCESS_TOKEN` or `~/.codex/auth.json`. `/ops/readiness?tenant_id=...` is tenant-authenticated and reports missing provider/config names only, never raw secret values.

## Live Run

```bash
npm install
npm run build
scripts/production-start-api.sh
scripts/production-start-web.sh
```

Open `http://localhost:3000/deals/<deal_id>`.

For systemd and nginx templates, see [deploy/README.md](deploy/README.md). Copy `.env.production.example` to your managed secret store or `/etc/cdi/revenue-intelligence-os.env`, replace placeholders, then run:

```bash
EXPECTED_RUNTIME=live-provider-ready bash scripts/production-smoke.sh
```

## Verify

Docs/proof harness:

```bash
bash scripts/t5-docs-proof.sh
```

Full product gate:

```bash
npm run check
```

Production runtime smoke gate:

```bash
bash scripts/production-smoke.sh
```

## Runtime Contract

- Protected API routes require `Authorization: Bearer <token>` and `X-Tenant-Id: $CDI_TENANT_ID`.
- Transcript and audio ingestion create durable job status records and write `call_event`, `causal_link`, `deal_memory`, and `contact_memory` records.
- Knowledge ingest accepts playbooks, battlecards, ICP definitions, source facts, and integration facts.
- Deal context, timeline replay, intelligence, CRM sync, and pipeline summary read provider data and fail closed until required credentials are present.
- `/intelligence/deal/{deal_id}` validates action citations against current memory and knowledge ids before returning.
- The web workbench fetches API context, timeline, replay, intelligence, graph anchors, evidence anchors, and cited actions; missing browser/server env renders setup-required state.

## API Routes

- `GET /health`
- `GET /ops/readiness?tenant_id=...`
- `POST /calls/ingest`
- `POST /calls/ingest/audio`
- `GET /calls/jobs/{job_id}`
- `GET /accounts?tenant_id=...`
- `GET /accounts/{account_id}?tenant_id=...`
- `GET /deals?tenant_id=...`
- `POST /knowledge/ingest`
- `POST /crm/sync`
- `GET /pipeline/summary?tenant_id=...`
- `GET /deals/{deal_id}/context?tenant_id=...`
- `GET /deals/{deal_id}/timeline?tenant_id=...`
- `GET /deals/{deal_id}/timeline?tenant_id=...&as_of=...`
- `GET /calls?tenant_id=...`
- `GET /calls/{call_id}?tenant_id=...`
- `GET /search?tenant_id=...&q=...`
- `GET /intelligence/deal/{deal_id}?tenant_id=...`
- `GET /forecast/summary?tenant_id=...`
- `GET /forecast/submissions?tenant_id=...`
- `GET /coaching/scorecards?tenant_id=...`
- `GET /coaching/reps/{rep_id}?tenant_id=...`
- `GET /engage/tasks?tenant_id=...`
- `GET /engage/tasks/{task_id}?tenant_id=...`
- `POST /assistant/query?tenant_id=...`
- `GET /admin/users?tenant_id=...`
- `GET /admin/settings?tenant_id=...`
- `GET /audit/events?tenant_id=...`
- `GET /exports?tenant_id=...`
- `GET /exports/{export_id}?tenant_id=...`

## Web Routes

- `/deals`
- `/accounts`
- `/calls`
- `/forecast`
- `/coaching`
- `/engage`
- `/assistant`
- `/admin`
- `/ingestion`
- `/deals/deal_northstar_expansion`

## Credential Boundary

Local proof covers docs wiring, config contracts, fail-closed behavior, citation enforcement, route shape, job status, and web setup-required rendering. Live HydraDB, LLM responses, audio transcription, and CRM provider success require supplied credentials or local command configuration plus seeded production records. Codex subscription auth can satisfy text LLM responses, but not audio transcription; set `CDI_TRANSCRIPTION_COMMAND` for local/free audio transcription.

The credential handoff verdict is explicit: live provider behavior is not proven until credentials are supplied and the live validation commands pass against seeded provider records. See [Credential Handoff Verdict](docs/credential-handoff-verdict.md).

Deployment handoff artifacts are in `.env.production.example`, `scripts/production-start-api.sh`, `scripts/production-start-web.sh`, `scripts/production-smoke.sh`, `deploy/systemd/`, and `deploy/nginx/`.

## npm Audit Risk Note

Latest local `npm audit --json` exits `1` with two moderate findings: `postcss` XSS exposure pulled through `next`. The suggested automated fix downgrades the app to `next@9.3.3`, and current stable `next@16.2.9` still pins `postcss@8.4.31`; do not apply the forced downgrade as a production fix.

## Docs

- [Local Demo Proof](docs/local-demo-proof.md)
- [Context](docs/context.md)
- [Production Runbook](docs/production-runbook.md)
- [HydraDB Integration](docs/hydradb-integration.md)
- [Credential Handoff Verdict](docs/credential-handoff-verdict.md)
- [Deployment Handoff](deploy/README.md)
