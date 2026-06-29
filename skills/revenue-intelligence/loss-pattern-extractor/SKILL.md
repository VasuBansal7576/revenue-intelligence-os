---
name: loss-pattern-extractor
description: "Use when CRM marks a deal Lost to extract the losing sequence from HydraDB and produce a cited risk-detection skill."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, loss-pattern, risk-detection, hydradb]
---

# Loss Pattern Extractor

Use this skill when a deal is marked Lost and the product should turn the loss into future risk detection.

## Trigger

- CRM deal status changes to Lost.
- Loss reason or close-lost event is available.

## Inputs

- `tenant_id`, `deal_id`, closed-lost timestamp
- full deal history from HydraDB
- CRM loss reason and stage history
- comparable won deals, when available

## Procedure

1. Load the complete temporal history for the lost deal.
2. Identify warning signs that emerged before loss: stale follow-up, broken commitment, vague next step, competitor escalation, pricing stall, sentiment drop, or single-threaded relationship.
3. Compare against similar won deals to avoid blaming common but non-causal activity.
4. Draft a risk-detection SKILL.md with trigger, symptoms, intervention, citations, and stop conditions.
5. Store the pattern as versioned knowledge and link it to the lost deal.

## Outputs

- Cited loss pattern summary.
- Candidate risk-detection SKILL.md content.
- HydraDB link from Lost Deal to produced Risk Pattern.

## Verification

- Each risk symptom appears before the loss event in the temporal graph.
- The intervention names an action that could have been taken earlier.
- The pattern excludes unsupported or post-hoc explanations.

## Fail-Closed Boundary

If the loss event, timeline, or source evidence is incomplete, do not publish a risk skill. Return draft-blocked with the missing records.
