---
name: win-pattern-extractor
description: "Use when CRM marks a deal Won to extract the winning sequence from HydraDB and write a reusable cited SKILL.md pattern."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, win-pattern, skill-compounding, hydradb]
---

# Win Pattern Extractor

Use this skill when a deal is marked Won and the product should preserve what worked as an executable pattern.

## Trigger

- CRM deal status changes to Won.
- The winning deal can be mapped to a tenant and full HydraDB deal history.

## Inputs

- `tenant_id`, `deal_id`, closed-won timestamp
- full deal history: calls, emails, CRM changes, rep actions, prospect responses, competitors, objections, and outcome
- comparable won and lost deals, when available

## Procedure

1. Load the complete temporal deal history from HydraDB.
2. Identify the sequence that plausibly drove the win: discovery move, objection handling, follow-up cadence, stakeholder expansion, final push, and timing.
3. Compare against similar lost deals to remove generic activity that did not distinguish the win.
4. Draft a compact SKILL.md pattern with trigger, fit criteria, steps, citations, and fail-closed limits.
5. Store the pattern as versioned knowledge and link it to the won deal.

## Outputs

- Cited win pattern summary.
- Candidate SKILL.md content for future matching deals.
- HydraDB link from Won Deal to produced Skill.

## Verification

- Every recommended step cites source deal evidence.
- Fit criteria include industry, company size, deal size, competitor landscape, and objection pattern when present.
- The pattern states when not to use it.

## Fail-Closed Boundary

If deal history is incomplete, outcome is not confirmed Won, or citations are missing, do not publish a reusable pattern. Return draft-blocked with missing evidence.
