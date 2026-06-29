---
name: admin-audit-review
description: "Use for admin and audit review to inspect users, settings, audit events, and export previews from tenant-scoped app APIs."
platforms: [linux, macos, windows]
version: 1.0.0
author: Revenue Intelligence OS
license: MIT
category: revenue-intelligence
metadata:
  hermes:
    tags: [revenue-intelligence, admin, audit, exports, api]
---

# Admin Audit Review

Use this skill when an admin or RevOps operator reviews users, tenant settings, audit events, or export previews.

## Trigger

- Admin opens tenant administration.
- RevOps requests audit history or export status.
- A workflow needs to prove what was configured or exported.

## Inputs

- `tenant_id` and authenticated admin/operator context
- optional user, audit event, or export id
- app API access for `GET /admin/users`, `GET /admin/settings`, `GET /audit/events`, `GET /exports`, and `GET /exports/{id}`

## Procedure

1. Confirm tenant auth and admin/operator permission before loading admin data.
2. Fetch users from `GET /admin/users?tenant_id=<tenant_id>` when reviewing access.
3. Fetch settings from `GET /admin/settings?tenant_id=<tenant_id>` when reviewing configuration.
4. Fetch audit events from `GET /audit/events?tenant_id=<tenant_id>` for trace review.
5. Fetch exports from `GET /exports?tenant_id=<tenant_id>` or `GET /exports/<export_id>?tenant_id=<tenant_id>` for export preview.
6. Report only returned fields and preserve timestamps, actor ids, and runtime readiness labels.

## Outputs

- Tenant user or settings review.
- Audit event summary with actor, action, target, and timestamp.
- Export preview or export status.
- Setup or provider-readiness error when records are unavailable.

## Verification

- Every admin, audit, or export item belongs to the requested tenant.
- Audit summaries preserve actor, action, target, and timestamp.
- Export status is copied from the API response and never upgraded.

## Fail-Closed Boundary

If tenant auth, admin/operator permission, or app API records are unavailable, do not reveal admin data, infer settings, or claim an export exists. Return the app/API failure state.
