#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

artifact=".omo/evidence/t5-docs-proof.txt"
mkdir -p "$(dirname "$artifact")"

{
  echo "Scenario: T5 docs/proof harness separates local demo proof from credential-gated live HydraDB/OpenAI/CRM work."
  echo "Invocation: bash scripts/t5-docs-proof.sh"
  echo "Binary observable: required docs, npm scripts, demo-mode test contract, and wedge source references are present; no live services are called."
  echo "Artifact: $(pwd)/$artifact"
  echo

  echo "== npm scripts =="
  npm pkg get scripts
  echo

  echo "== docs wiring =="
  test -f README.md
  test -f docs/local-demo-proof.md
  test -f docs/production-runbook.md
  test -f .env.production.example
  test -f deploy/README.md
  test -f deploy/systemd/cdi-api.service
  test -f deploy/systemd/cdi-web.service
  test -f deploy/nginx/revenue-intelligence-os.conf
  rg -n "bash scripts/t5-docs-proof.sh|\\.omo/evidence/t5-docs-proof\\.txt|HydraDB, OpenAI, CRM" README.md docs/local-demo-proof.md docs/production-runbook.md
  rg -n "CDI_DEMO_MODE=1|deal_northstar_expansion|--port 3001|--port 3002|Configuration required" README.md docs/production-runbook.md
  rg -n "production-start-api|production-start-web|production-smoke|cdi-api.service|revenue-intelligence-os.env" README.md docs/production-runbook.md deploy/README.md
  echo

  echo "== demo-mode contract =="
  rg -n "CDI_DEMO_MODE|test_demo_context_returns_seeded_deal_without_provider_keys|test_demo_timeline_replays_seeded_point_in_time|test_demo_intelligence_returns_cited_briefing_without_openai|test_demo_pipeline_summary_returns_seeded_metrics|test_demo_mode_still_requires_verified_tenant" apps/api/tests/test_demo_mode.py apps/api/app/config.py
  echo

  echo "== local wedge source references =="
  rg -n "deal_northstar_expansion|budget_freeze|champion silence|Replay|cited|citation" fixtures apps/api/tests apps/web/src/app/deals
  echo

  echo "PASS: T5 docs/proof harness checks completed without live HydraDB/OpenAI/CRM calls."
} > "$artifact"

cat "$artifact"
