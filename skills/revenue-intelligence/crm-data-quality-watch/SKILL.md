---
name: crm-data-quality-watch
description: "Use daily to detect divergence between CRM stage/data and actual call reality, then flag specific mismatches to the manager."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, crm, data-quality, hydradb]
---

# CRM Data Quality Watch

Use this skill to keep CRM honest by comparing declared CRM state with HydraDB call and deal reality.

## Trigger

- Daily tenant sweep.
- CRM sync completes for an active deal.
- Manager requests CRM quality review.

## Inputs

- `tenant_id`, optional `deal_id`
- CRM stage, amount, close date, next step, contact activity, and owner
- latest call analysis, commitments, objections, next steps, and sentiment from HydraDB

## Procedure

1. Query CRM facts and matching HydraDB deal reality for active deals.
2. Detect mismatches: stage too advanced for objections, missing next step, stale close date, unlogged contact activity, amount mismatch, owner mismatch, or unresolved action items.
3. Cite the CRM field, the conflicting call or deal evidence, and the recommended correction.
4. Flag only material mismatches to the manager or RevOps channel.
5. Record acknowledged, corrected, and still-open mismatches.

## Outputs

- CRM data quality mismatch list.
- Manager or RevOps alert.
- Audit trail for acknowledged and corrected mismatches.

## Verification

- Each mismatch cites one CRM field and one conflicting HydraDB fact.
- False positives are suppressed when the latest call evidence supports the CRM state.
- Corrected mismatches disappear on the next sweep.

## Fail-Closed Boundary

If CRM data, HydraDB context, or tenant mapping is unavailable, do not infer data quality. Return setup-required or context-missing with the failed source.
