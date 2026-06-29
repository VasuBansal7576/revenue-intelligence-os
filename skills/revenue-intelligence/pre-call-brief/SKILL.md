---
name: pre-call-brief
description: "Use 10 minutes before a prospect calendar event to synthesize cited deal context from HydraDB and deliver a concise rep brief."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, pre-call, hydradb, briefing]
---

# Pre-Call Brief

Use this skill when a calendar event with a prospect is 10 minutes away and the rep needs the latest deal context without searching dashboards.

## Trigger

- Calendar integration fires for an upcoming prospect meeting.
- The meeting can be mapped to `tenant_id`, `deal_id`, `rep_id`, and prospect company.

## Inputs

- meeting metadata and attendee list
- `tenant_id`, `deal_id`, `rep_id`
- past call summaries, open commitments, objections, competitor mentions, and CRM state from HydraDB
- last 30 days of approved company news, when available

## Procedure

1. Resolve the meeting to one tenant and one active deal.
2. Query HydraDB for past call summaries, open commitments, prior objections, competitor mentions, CRM facts, and recent deal changes.
3. Build one cited brief: current deal state, what changed, open promises, likely objections, competitor context, and recommended next move.
4. Send the brief to the rep through the configured push channel, usually Slack DM or WhatsApp.
5. Record delivery status against the meeting event.

## Outputs

- Cited pre-call brief.
- Delivery status with channel and timestamp.
- Missing-data warning when the deal exists but relevant context is thin.

## Verification

- Brief cites HydraDB records for deal state, commitments, objections, and competitor history.
- Delivery occurs within 60 seconds of trigger handling.
- The brief names the next meeting objective and any open promise from the previous call.

## Fail-Closed Boundary

If the meeting cannot be mapped to one tenant and deal, or cited HydraDB context is unavailable, send no synthesized deal claims. Return a setup-required or context-missing message instead.
