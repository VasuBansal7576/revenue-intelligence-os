---
name: onboarding-skill-pack
description: "Use when a new rep is added to generate a 30-day progressive revenue skill pack from cited HydraDB win history."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, onboarding, skill-pack, coaching]
---

# Onboarding Skill Pack

Use this skill when a new rep joins and needs daily field training based on the team's actual deal history.

## Trigger

- New rep is added to the system.
- Manager requests a first-30-days skill sequence for a rep.

## Inputs

- `tenant_id`, `rep_id`, role, segment, territory, start date
- won and lost deal history from HydraDB
- current playbooks and competitor knowledge
- rep delivery channel

## Procedure

1. Identify the situations this rep is most likely to face in the first month.
2. Query HydraDB for cited examples of winning and losing behavior in those situations.
3. Build a 30-day sequence with one skill per day: scenario, why it matters, what to do, and cited example.
4. Deliver the first skill immediately and schedule the rest progressively through the configured channel.
5. Track completion and adapt later prompts only from observed rep gaps.

## Outputs

- 30-day onboarding skill pack.
- Day-one delivered skill.
- Delivery and completion schedule.

## Verification

- Every daily skill is tied to a real deal pattern or approved product knowledge.
- The sequence covers discovery, objection handling, follow-up, competitor response, and CRM hygiene.
- Delivery schedule matches the rep start date and channel configuration.

## Fail-Closed Boundary

If the rep, channel, or cited deal history is missing, do not generate generic training. Return setup-required or insufficient-history.
