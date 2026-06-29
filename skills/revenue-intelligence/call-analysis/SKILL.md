---
name: call-analysis
description: "Use after revenue call ingestion to extract deal entities, commitments, objections, sentiment, risk signals, competitors, and next steps into HydraDB."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, hydradb, call-analysis, deal-memory]
---

# Call Analysis

Use this skill after a Zoom, Google Meet, Teams, or uploaded sales call has been transcribed and linked to a tenant, deal, prospect company, and rep.

## Trigger

- Call transcript ingestion completes.
- A call memory exists or is ready to write in HydraDB.

## Inputs

- `tenant_id`, `deal_id`, `call_id`, `rep_id`
- transcript with speaker labels
- call timestamp and source system
- existing HydraDB deal, prospect, and rep context

## Procedure

1. Load the transcript and the current HydraDB context for the deal, prospect, and rep.
2. Extract typed facts: attendees, objections, commitments, owner and due date, competitor mentions, sentiment trend, next step, and risk signals.
3. Link every extracted fact to transcript evidence and the call timestamp.
4. Update the call memory, deal memory, prospect knowledge, and rep activity memory in HydraDB.
5. Emit only deal changes supported by transcript evidence.

## Outputs

- Structured call analysis record.
- Updated HydraDB memory nodes for call, deal, prospect, and rep.
- Risk signals eligible for `rep-coaching-nudge`, `post-call-chain`, and manager alerts.

## Verification

- Every commitment has owner, due date or explicit missing-date marker, and transcript evidence.
- Every competitor mention includes what the prospect said and what the rep said in response.
- The deal node shows the latest next step, sentiment direction, objections, and risk signals.

## Fail-Closed Boundary

If transcript, tenant boundary, deal link, or HydraDB write is missing or fails, stop and return a setup or data error. Do not invent call facts, commitments, sentiment, or next steps.
