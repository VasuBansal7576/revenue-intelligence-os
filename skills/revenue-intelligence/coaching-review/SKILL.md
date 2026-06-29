---
name: coaching-review
description: "Use for manager coaching review to inspect rep scorecards and coaching risks from the app API with transcript-backed evidence."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, coaching, scorecards, api]
---

# Coaching Review

Use this skill when a manager reviews rep coaching needs across scorecards, calls, and repeated behavior patterns.

## Trigger

- Manager opens coaching review.
- `call-analysis` or `rep-coaching-nudge` reports repeated coaching gaps.
- Weekly coaching digest job runs.

## Inputs

- `tenant_id`, optional `rep_id`
- app API access for `GET /coaching/scorecards` and `GET /coaching/reps/{id}`
- scorecard, call evidence, coaching gap, and recommended action fields returned by the app API

## Procedure

1. Confirm tenant auth before loading scorecards.
2. Fetch `GET /coaching/scorecards?tenant_id=<tenant_id>` for team-level coaching rows.
3. Fetch `GET /coaching/reps/<rep_id>?tenant_id=<tenant_id>` for one-rep review when requested.
4. Summarize only the gaps, examples, and recommended actions returned by the app API.
5. Preserve links to transcript, call, or scorecard evidence in the manager output.

## Outputs

- Manager coaching review by rep or team.
- Evidence-backed coaching gaps and next actions.
- Setup or provider-readiness error when coaching records are unavailable.

## Verification

- Each coaching gap names one rep, one behavior, and one evidence record.
- Repeated-gap claims are backed by more than one returned event or an explicit repeat count.
- The review does not create coaching scores outside the app payload.

## Fail-Closed Boundary

If scorecards, rep mapping, evidence links, or tenant auth are missing, do not coach from generic best practices. Return the app/API failure state.
