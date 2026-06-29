# Revenue Intelligence OS Context

Revenue Intelligence OS is a production Gong-style workbench with HydraDB as the causal memory layer.

## Product Thesis

This is not a broad call-recording clone. The wedge is deal causality:

- store deal and contact state as time-versioned memory;
- write explicit causal links between events, objections, champion behavior, buyer absence, and competitive pressure;
- replay what the team knew at a prior date;
- force intelligence output to cite memory or knowledge records.

The product question is: can the system explain why a deal changed from evidence inside the deal?

## Proof Lanes

- Local demo proof: run `bash scripts/t5-docs-proof.sh`; it records static, no-service evidence in `.omo/evidence/t5-docs-proof.txt`.
- Live provider proof: requires tenant auth plus HydraDB, a configured LLM provider, audio transcription configuration, CRM credentials, and seeded provider records. Codex subscription auth can satisfy text LLM responses; audio uses OpenAI or `CDI_TRANSCRIPTION_COMMAND`.

## Runtime Shape

- `apps/api`: FastAPI routes for tenant auth, transcript/audio ingestion, durable job status, knowledge ingest, CRM sync, pipeline summary, deal context, temporal replay, and citation-enforced intelligence.
- `apps/web`: Next.js 15 operator workbench. It fetches API context, timeline, intelligence, replay state, graph anchors, and evidence anchors, then renders setup-required state when browser/server env is incomplete.
- `packages/types`: shared TypeScript contracts for deals, calls, memory, knowledge, causal links, intelligence, and timeline replay.
- `packages/hydradb-client`: HydraDB client contract tests and adapter boundary for memory and knowledge query behavior.

## Built And Gate-Approved

- Provider/config production contracts for HydraDB, text LLM responses, OpenAI or local-command audio transcription, CRM, job storage, and auth config.
- Transcript and audio ingestion through durable job records, with `POST /calls/ingest`, `POST /calls/ingest/audio`, and `GET /calls/jobs/{job_id}`.
- Call ingestion writes `call_event`, `causal_link`, latest `deal_memory`, and affected `contact_memory` records.
- Deal/contact memory supports point-in-time replay from append-only memory snapshots.
- Knowledge/admin ingest supports playbooks, battlecards, ICP definitions, `source_fact`, and `integration_fact` records.
- `GET /intelligence/deal/{deal_id}` validates action citations against current memory and knowledge ids.
- CRM sync accepts credential-gated source/integration records; pipeline summary computes totals, forecast, and risk rows from real deal/memory records.
- Web operator fetches real API context/timeline/intelligence, validates response shapes, renders API-cited actions, replay links, graph/evidence anchors, and setup-required state without credentials.
- Auth supports static bearer tokens and stdlib HMAC service tokens. Service-token mode requires secret, issuer, and audience together; partial HMAC config fails closed. Non-canonical, expired, tampered, and malformed service tokens reject.

## Trust Boundary

Protected routes require tenant auth before provider work:

```text
Authorization: Bearer <token>
X-Tenant-Id: <tenant id>
```

The static token path remains available when service-token mode is not configured. If `CDI_SERVICE_TOKEN_HMAC_SECRET` is set, `CDI_SERVICE_TOKEN_ISSUER` and `CDI_SERVICE_TOKEN_AUDIENCE` are required too.

Missing or partial provider config returns explicit operational errors. API routes do not create placeholder deal context, recommendations, timeline state, transcriptions, CRM records, or provider responses.

## External Services

- HydraDB: `/context/ingest` for memory and knowledge writes, `/context/ingest/status/{job_id}` for ingest status, and `/query` for deal context, timeline replay, intelligence context, and pipeline data.
- LLM provider: `/responses` for structured call-signal extraction and cited deal briefings via OpenAI or Codex subscription auth.
- Audio transcription: OpenAI `/audio/transcriptions` or local `CDI_TRANSCRIPTION_COMMAND` for audio ingestion.
- CRM providers: `/crm/sync` is credential-gated by local CRM env and writes normalized source/integration facts to HydraDB knowledge.

## Hermes Skill Handoff

Revenue Intelligence Hermes skills are product-owned under `skills/revenue-intelligence/`. They should call this app's tenant-authenticated API surfaces, not modify `../hermes-agent`.

Every Hermes-to-app request uses:

```text
Authorization: Bearer <token>
X-Tenant-Id: <tenant id>
```

Workflow endpoint mapping:

- Assistant query: `POST /assistant/query?tenant_id=...`
- Forecast review: `GET /forecast/summary?tenant_id=...`, `GET /forecast/submissions?tenant_id=...`
- Coaching review: `GET /coaching/scorecards?tenant_id=...`, `GET /coaching/reps/{rep_id}?tenant_id=...`
- Engage task sweep: `GET /engage/tasks?tenant_id=...`, `GET /engage/tasks/{task_id}?tenant_id=...`
- Admin/audit review: `GET /admin/users?tenant_id=...`, `GET /admin/settings?tenant_id=...`, `GET /audit/events?tenant_id=...`, `GET /exports?tenant_id=...`, `GET /exports/{export_id}?tenant_id=...`

Hermes skills must preserve API readiness labels exactly: `local-demo`, `provider-not-ready`, or `live-provider-ready`. Missing credentials, missing tenant auth, or missing citations are returned as setup or provider errors; skills do not fabricate live provider output.

## API Routes

- `GET /health`
- `GET /ops/readiness?tenant_id=...`
- `POST /calls/ingest`
- `POST /calls/ingest/audio`
- `GET /calls/jobs/{job_id}`
- `POST /knowledge/ingest`
- `POST /crm/sync`
- `GET /pipeline/summary?tenant_id=...`
- `GET /deals/{deal_id}/context?tenant_id=...`
- `GET /deals/{deal_id}/timeline?tenant_id=...`
- `GET /deals/{deal_id}/timeline?tenant_id=...&as_of=...`
- `GET /intelligence/deal/{deal_id}?tenant_id=...`

## Remaining Credential-Only Work

- Live HydraDB, OpenAI, audio transcription, and CRM provider validation after secrets are supplied.
- Production data seeding for tenant, deal, contact, memory, knowledge, source fact, and integration fact records.
- Deployment choices: process manager, HTTPS ingress, secret store, persistent job-store location, log retention, and provider observability.
- `/ops/readiness` can report readiness state and credential handoff gaps, but it does not prove deployment or live provider validation.
