---
name: forecast-review
description: "Use for manager forecast review to fetch forecast summaries and submissions from the app API without fabricating pipeline health."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, forecast, manager-review, api]
---

# Forecast Review

Use this skill when a manager asks for the current forecast position or wants to review submitted forecast changes.

## Trigger

- Manager opens forecast review.
- Weekly forecast review job runs.
- Operator asks why forecast moved.

## Inputs

- `tenant_id`, optional `rep_id`, `team_id`, or time window
- app API access for `GET /forecast/summary` and `GET /forecast/submissions`
- deal, amount, close-date, category, and risk records returned by the app API

## Procedure

1. Confirm tenant auth before any forecast request.
2. Fetch `GET /forecast/summary?tenant_id=<tenant_id>` for totals and category rollups.
3. Fetch `GET /forecast/submissions?tenant_id=<tenant_id>` when submission details or rep changes are needed.
4. Explain movement only from returned forecast, deal, and risk fields.
5. Surface provider-not-ready or context-missing exactly when the API cannot supply forecast records.

## Outputs

- Forecast summary with cited category and weighted amount fields.
- Submission review with rep, deal, amount, and reason fields when available.
- Setup or provider-readiness error when records are unavailable.

## Verification

- Weighted forecast amount matches the app API response.
- Every at-risk deal cited in the review appears in the returned forecast payload.
- Unknown or missing records are labeled unknown, not healthy.

## Fail-Closed Boundary

If the app API cannot return tenant-scoped forecast records, do not generate a forecast or pipeline confidence statement. Return the API failure state.
