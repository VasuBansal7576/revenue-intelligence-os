---
name: assistant-query
description: "Use when a revenue operator asks the assistant a deal, account, call, or forecast question that must answer from cited app records."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, assistant, citations, api]
---

# Assistant Query

Use this skill when a rep, manager, or RevOps operator asks a natural-language question through the assistant surface.

## Trigger

- Operator submits a question to the Revenue Intelligence OS assistant.
- A scheduled workflow needs a cited answer before sending a rep or manager message.

## Inputs

- `tenant_id` and authenticated operator context
- assistant question text
- optional `deal_id`, `account_id`, `rep_id`, or time window
- app API access for `POST /assistant/query`

## Procedure

1. Confirm the operator tenant and auth headers before calling the app API.
2. Send the question to `POST /assistant/query?tenant_id=<tenant_id>` with the configured bearer token and tenant header.
3. Require the response to include an answer, citations, and runtime readiness.
4. Return the answer with citations intact and no extra unsupported claims.
5. Record provider-not-ready, setup-required, or context-missing exactly when the API returns those states.

## Outputs

- Cited assistant answer.
- Citation list from app memory, knowledge, or source records.
- Runtime readiness or setup error when no answer can be produced.

## Verification

- The answer has at least one citation for every deal or forecast claim.
- The tenant in the request and response match.
- Provider-mode failures are reported as not-ready, not replaced with demo text.

## Fail-Closed Boundary

If auth, tenant mapping, app API access, or citations are missing, do not answer from memory or general knowledge. Return the app/API failure state.
