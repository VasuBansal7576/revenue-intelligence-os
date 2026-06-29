# HydraDB Integration

The API calls the HydraDB v2 HTTP API directly through `apps/api/app/external.py`.

Local demo proof does not call HydraDB. HydraDB success belongs to the credential-gated live lane and requires `HYDRA_DB_API_KEY` plus seeded tenant/deal records.

Runtime readiness labels are exact: `local-demo`, `provider-not-ready`, or `live-provider-ready`. `/health` is public; `/ops/readiness?tenant_id=...` is tenant-authenticated and reports provider names, states, and missing config names without raw secret values.

## Provider Calls Used

- `POST /context/ingest` with `type=memory`: writes call-derived memory records.
- `POST /context/ingest` with `type=knowledge`: writes playbooks, battlecards, ICP definitions, source facts, and integration facts.
- `GET /context/ingest/status/{job_id}`: reads provider ingest status when a HydraDB ingest job id is available.
- `POST /query`: retrieves tenant/deal-scoped records for context, timeline replay, intelligence, and pipeline summary.

Every HydraDB request includes:

```text
Authorization: Bearer $HYDRA_DB_API_KEY
API-Version: 2
```

`HYDRA_DB_BASE_URL` defaults to `https://api.hydradb.com`.

## Record Types

The app consumes JSON records with `record_type` plus tenant scoping fields. Deal-scoped records also carry `deal_id`.

Memory and deal records:

- `tenant`
- `deal`
- `contact`
- `deal_memory`
- `contact_memory`
- `call_event`
- `causal_link`

Knowledge and integration records:

- `playbook`
- `battlecard`
- `icp_definition`
- `source_fact`
- `integration_fact`
- `knowledge_node`

Revenue AI OS provider records added in Wave 1:

| Record type | Required fields | Query filters | Current wave behavior |
| --- | --- | --- | --- |
| `account` | `id`, `tenant_id`, `name`, `domain`, `owner_user_id`, `segment`, `health`, `renewal_date` | `tenant_id`; optional `id`, `owner_user_id`, `health` | Local demo seed only; provider routes intentionally fail closed until account APIs query seeded records. |
| `role` | `id`, `tenant_id`, `name`, `permissions` | `tenant_id`; optional `id`, `name` | Local demo seed only; provider admin routes intentionally fail closed until seeded. |
| `user` | `id`, `tenant_id`, `name`, `email`, `role_id`, `role_name`, `manager_id`, `status` | `tenant_id`; optional `id`, `role_id`, `status` | Local demo seed only; provider admin routes intentionally fail closed until seeded. |
| `admin_setting` | `id`, `tenant_id`, `key`, `value`, `updated_at` | `tenant_id`; optional `key` | Local demo seed only; provider admin settings intentionally fail closed until seeded. |
| `call_library_entry` | `id`, `tenant_id`, `call_id`, `deal_id`, `account_id`, `title`, `started_at`, `duration_seconds`, `primary_rep_id`, `outcome`, `recording_url`, `transcript_id` | `tenant_id`; optional `call_id`, `deal_id`, `account_id`, `primary_rep_id`, date range on `started_at` | Local demo seed only; provider call-library routes intentionally fail closed until seeded. |
| `coaching_scorecard` | `id`, `tenant_id`, `rep_id`, `call_id`, `deal_id`, `reviewer_user_id`, `overall_score`, `strengths`, `improvement_areas`, `reviewed_at` | `tenant_id`; optional `rep_id`, `call_id`, `deal_id`, date range on `reviewed_at` | Local demo seed only; provider coaching routes intentionally fail closed until seeded. |
| `forecast_submission` | `id`, `tenant_id`, `period`, `submitted_by_user_id`, `forecast_category`, `commit_amount_usd`, `best_case_amount_usd`, `pipeline_amount_usd`, `submitted_at` | `tenant_id`; optional `period`, `submitted_by_user_id`, `forecast_category` | Local demo seed only; provider forecast routes intentionally fail closed until seeded. |
| `engagement_task` | `id`, `tenant_id`, `deal_id`, `account_id`, `owner_user_id`, `title`, `due_date`, `priority`, `status`, `source_call_id` | `tenant_id`; optional `id`, `deal_id`, `account_id`, `owner_user_id`, `status`, due-date range | Local demo seed only and read-only; provider task routes intentionally fail closed until seeded. |
| `assistant_answer` | `id`, `tenant_id`, `question`, `answer`, `citation_ids`, `created_at`, `created_by_user_id` | `tenant_id`; optional `created_by_user_id`, date range on `created_at`, citation id lookup | Local demo seed only; live assistant still requires OpenAI plus HydraDB context and fails closed without both. |
| `audit_event` | `id`, `tenant_id`, `actor_user_id`, `action`, `target_type`, `target_id`, `occurred_at` | `tenant_id`; optional `actor_user_id`, `action`, `target_type`, `target_id`, date range on `occurred_at` | Local demo seed only; provider audit routes intentionally fail closed until seeded. |
| `export_job` | `id`, `tenant_id`, `requested_by_user_id`, `export_type`, `status`, `created_at`, `completed_at`, `download_url` | `tenant_id`; optional `id`, `requested_by_user_id`, `export_type`, `status`, date range on `created_at` | Local demo seed only and read-only; provider export routes intentionally fail closed until seeded. |

`playbook`, `battlecard`, `icp_definition`, `source_fact`, and `integration_fact` records are normalized into `knowledge_nodes` for intelligence citation checks and web evidence rendering.

## Route Usage

- `POST /calls/ingest` and `POST /calls/ingest/audio` write `call_event`, `causal_link`, `deal_memory`, and `contact_memory` records to memory after LLM extraction. Text extraction can use OpenAI or Codex subscription auth; audio transcription can use OpenAI or `CDI_TRANSCRIPTION_COMMAND`.
- `POST /knowledge/ingest` writes playbooks, battlecards, ICP definitions, source facts, and integration facts to knowledge.
- `POST /crm/sync` writes normalized CRM source/integration facts to knowledge after CRM env validation.
- `GET /deals/{deal_id}/context` queries HydraDB and builds the current deal context from the latest valid memory snapshot.
- `GET /deals/{deal_id}/timeline` queries HydraDB and builds ordered snapshots plus optional `as_of` replay state.
- `GET /intelligence/deal/{deal_id}` queries HydraDB, sends the context to the configured LLM provider, and rejects returned actions whose citations are not present in the current memory or knowledge ids.
- `GET /pipeline/summary` queries tenant deal, memory, source fact, and integration fact records, then computes pipeline totals and risk rows.

## Failure Boundary

Missing `HYDRA_DB_API_KEY`, tenant mismatch, missing required records, malformed provider JSON, HTTP errors, and request failures surface as explicit API errors. Routes do not synthesize context, timeline, intelligence, CRM, or pipeline data when HydraDB cannot provide records.

`live-provider-ready` only means local tenant auth, HydraDB, a configured LLM provider, and CRM credential basics are configured. It is not live provider proof until the route-specific validation calls return seeded provider records. Codex subscription auth can satisfy text LLM responses; use OpenAI or `CDI_TRANSCRIPTION_COMMAND` for audio transcription.
