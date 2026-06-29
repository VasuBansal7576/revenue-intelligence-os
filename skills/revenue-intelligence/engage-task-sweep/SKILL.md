---
name: engage-task-sweep
description: "Use to review engagement tasks, stale follow-ups, and read-only task details from the app API without sending emails or mutating state."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, engage, tasks, stale-followup]
---

# Engage Task Sweep

Use this skill when a rep or manager wants a current queue of engagement tasks and stale follow-up risks.

## Trigger

- Daily engagement task sweep.
- Rep opens the engage task queue.
- Manager requests overdue or high-risk follow-up tasks.

## Inputs

- `tenant_id`, optional `rep_id`, `deal_id`, or task status filter
- app API access for `GET /engage/tasks` and `GET /engage/tasks/{id}`
- task, owner, due date, deal, account, and evidence fields returned by the app API

## Procedure

1. Confirm tenant auth before loading tasks.
2. Fetch `GET /engage/tasks?tenant_id=<tenant_id>` with any supported owner or status filters.
3. Fetch `GET /engage/tasks/<task_id>?tenant_id=<tenant_id>` before presenting task detail.
4. Rank tasks by due date, risk, amount, and evidence returned by the API.
5. Report task actions as read-only recommendations unless a future write endpoint is explicitly available.

## Outputs

- Engagement task sweep.
- Task detail with deal, owner, due date, and supporting evidence.
- Read-only status or setup/provider failure state.

## Verification

- Every task has an id, owner, due date or explicit missing-date marker, and tenant match.
- Stale follow-up claims cite the returned task or deal evidence.
- No email, CRM, or task-status mutation is attempted in this workflow.

## Fail-Closed Boundary

If task records, tenant auth, or supporting evidence are missing, do not infer outreach actions or send messages. Return the app/API failure state.
