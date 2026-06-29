# Local Demo Proof

Run:

```bash
bash scripts/t5-docs-proof.sh
```

Output:

```text
.omo/evidence/t5-docs-proof.txt
```

What this proves locally:

- README and runbook expose the same one-command proof harness.
- npm scripts are discoverable without starting services.
- `CDI_DEMO_MODE=1` and the seeded demo tests exist for context, temporal replay, cited intelligence, pipeline risk, and tenant enforcement.
- The source mentions the local wedge claims: deal context, temporal replay, stale-followup risk, and cited actions.

What this does not prove:

- Live HydraDB memory/knowledge ingest or query success.
- OpenAI transcription/responses.
- Salesforce, HubSpot, or any CRM sync.
- Browser/API runtime success against provider data.

Use `npm run check` only when dependencies and the full local runtime gate are in scope.
