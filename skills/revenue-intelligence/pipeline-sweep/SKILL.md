---
name: pipeline-sweep
description: "Use every Monday at 8am to query open deals, produce a cited forecast, and push a prioritized action list to the sales manager."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, pipeline, forecast, manager-alert]
---

# Pipeline Sweep

Use this skill for weekly manager-facing pipeline intelligence that tells managers what to do, not just what to inspect.

## Trigger

- Monday 8am tenant-local scheduled sweep.
- Manual manager request for current open-pipeline risk.

## Inputs

- `tenant_id`
- open deals, amounts, stages, owners, close dates, and CRM facts
- latest deal memories, risk signals, commitments, sentiment, competitor exposure, and relationship depth from HydraDB

## Procedure

1. Query all open deals for the tenant.
2. Score each deal using evidence-backed momentum, sentiment trajectory, commitment symmetry, competitive exposure, and relationship depth.
3. Build a forecast with explicit conditions and cited risks.
4. Rank interventions by close date, amount, risk severity, and freshness of available next action.
5. Push the manager a concise Slack message with forecast, at-risk deals, and exact actions.

## Outputs

- Weekly forecast with reasoning.
- Prioritized action list.
- Manager delivery status.

## Verification

- Each at-risk deal has a cited reason and recommended action.
- Forecast amount is traceable to CRM or HydraDB deal records.
- Deals with no evidence are marked unknown, not healthy.

## Fail-Closed Boundary

If open-pipeline data or HydraDB risk context is unavailable, do not generate a forecast. Return setup-required or context-missing with the failed data source.
