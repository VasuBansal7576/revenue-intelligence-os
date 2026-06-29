---
name: post-call-chain
description: "Use on call completion to run transcript ingestion, CRM update, follow-up draft, risk detection, and manager alert as one fail-closed chain."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, post-call, crm, follow-up]
---

# Post-Call Chain

Use this skill within 5 minutes after a revenue call ends, detected by calendar completion, recording completion, or audio silence.

## Trigger

- A call completion event arrives for a mapped revenue meeting.
- Transcript or recording ingestion is available.

## Inputs

- `tenant_id`, `deal_id`, `call_id`, `rep_id`
- transcript or recording job reference
- CRM provider configuration
- configured rep and manager delivery channels

## Procedure

1. Run or confirm `call-analysis` for the completed call.
2. Write supported deal stage, next step date, notes, contact activity, and action items to CRM.
3. Draft the rep follow-up from call commitments, discussion points, and successful follow-up patterns in HydraDB.
4. Detect risk signals: unresolved pricing objection, first-time competitor, cooling sentiment, vague next step, or broken commitment.
5. Push the follow-up draft to the rep and alert the manager only for material risks.
6. Record each chain step status for audit.

## Outputs

- CRM update result.
- Rep follow-up draft.
- Risk alert or explicit no-alert status.
- Chain audit record with per-step success or failure.

## Verification

- CRM writes are backed by extracted commitments or call notes.
- Follow-up draft references only facts from the call and cited patterns.
- Manager alert includes deal, risk, evidence, and recommended intervention.

## Fail-Closed Boundary

If call analysis, CRM credentials, tenant boundary, or HydraDB context fails, stop the dependent step. Do not update CRM, draft follow-up, or alert managers from inferred facts.
