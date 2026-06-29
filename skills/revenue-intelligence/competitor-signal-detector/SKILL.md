---
name: competitor-signal-detector
description: "Use when competitor mentions spike across deals to alert sales leadership with cited context and responses that are working."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, competitor-intelligence, battlecards, hydradb]
---

# Competitor Signal Detector

Use this skill when competitor mentions increase across active deals or when a rep faces a competitor objection.

## Trigger

- Competitor mentions spike across deals in a configured time window.
- A call analysis records a new or repeated competitor objection.

## Inputs

- `tenant_id`, time window, optional `competitor_name`
- structured competitor mentions from HydraDB
- prospect framing, rep response, stage, outcome, and follow-up mentions
- relevant competitor knowledge records

## Procedure

1. Query competitor mentions by time window, stage, segment, and deal outcome.
2. Detect spikes or repeated objection patterns across active deals.
3. Extract what prospects are claiming, what reps are saying back, and which responses correlate with progress.
4. For reps, surface the three most relevant proven responses and known failed responses.
5. For leaders, send a concise alert with affected deals, stage pattern, working responses, and recommended enablement action.

## Outputs

- Competitor objection guidance for reps.
- Spike alert for sales leaders.
- Updated competitor intelligence knowledge when new evidence is confirmed.

## Verification

- Spike alert cites affected deals and mention counts in the time window.
- Response guidance distinguishes worked, failed, and unknown.
- New competitor knowledge links back to source call evidence.

## Fail-Closed Boundary

If mentions cannot be tied to deals, stages, or outcomes, do not claim a spike or winning response. Return insufficient-evidence with the missing dimensions.
