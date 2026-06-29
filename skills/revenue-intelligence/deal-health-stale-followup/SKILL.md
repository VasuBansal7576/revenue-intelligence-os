---
name: deal-health-stale-followup
description: "Use daily or on deal-change events to find stale follow-up risk from HydraDB temporal deal state and push the smallest supported intervention."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, deal-health, stale-followup, hydradb]
---

# Deal Health Stale Follow-Up

Use this skill to block stale follow-up before a deal decays silently.

## Trigger

- Daily active-deal sweep.
- Deal has no scheduled next step, overdue rep commitment, unanswered prospect thread, or declining engagement.

## Inputs

- `tenant_id`, optional `deal_id`
- active deal memories
- open commitments and due dates
- last activity, next step, CRM stage, sentiment trajectory, and relationship depth from HydraDB

## Procedure

1. Query active deals and their latest temporal state.
2. Flag stale follow-up when a rep-owned commitment is overdue, no next step is scheduled, CRM stage expects action but activity is absent, or prospect response has gone cold.
3. Rank flagged deals by revenue impact, age of stale action, and risk evidence.
4. Generate one concrete intervention per deal: who to contact, what to say, and why now.
5. Push rep nudge for single-deal issues; push manager summary when stale follow-up repeats or affects material pipeline.

## Outputs

- Stale follow-up risk list.
- Rep nudge or manager summary.
- HydraDB audit record for flagged or cleared deals.

## Verification

- Each flag cites the stale commitment, missing next step, or activity gap.
- Each recommendation names the next recipient and action.
- Cleared deals have current activity or a scheduled next step.

## Fail-Closed Boundary

If HydraDB cannot prove the latest deal state, do not mark a deal stale or healthy. Return context-missing with the records required to evaluate it.
