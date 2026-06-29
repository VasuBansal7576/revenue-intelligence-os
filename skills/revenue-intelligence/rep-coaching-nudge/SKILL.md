---
name: rep-coaching-nudge
description: "Use post-call when a coaching gap is detected to send one specific evidence-backed rep nudge through Slack or the configured channel."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, coaching, slack, post-call]
---

# Rep Coaching Nudge

Use this skill after call analysis detects a specific rep coaching gap. The output is a nudge, not a dashboard score.

## Trigger

- `call-analysis` emits a coaching gap.
- Deal risk or rep behavior crosses a configured threshold.

## Inputs

- `tenant_id`, `deal_id`, `call_id`, `rep_id`
- detected gap with transcript evidence
- similar successful patterns from HydraDB
- rep delivery channel

## Procedure

1. Confirm the gap is specific and supported by evidence: talk ratio, early pricing, vague next step, unhandled competitor, missed commitment, or sentiment drop.
2. Query HydraDB for one relevant winning behavior or playbook.
3. Write a short note: observation, why it matters now, suggested next move, and source evidence.
4. Send within 5 minutes of call completion through Slack or the configured channel.
5. Record delivery and whether this rep has repeated the same gap.

## Outputs

- Rep coaching note.
- Delivery status.
- Optional manager digest input for repeated patterns.

## Verification

- The note names one behavior and one next action.
- The note cites transcript evidence and a winning pattern when one is used.
- Delivery timestamp is within the post-call window.

## Fail-Closed Boundary

If the gap is vague, unsupported, or lacks a delivery channel, do not coach. Return no-nudge with the missing evidence or setup requirement.
