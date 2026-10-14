---
date: 2026-10-13
status: superseded
tags: [decision, status/done, area/architecture]
---
# Build the target, with fallbacks *(superseded the same day by [[2026-10-13 POC plus one target slice, target as 90-day roadmap|POC + one target slice]])*
## Decision
Build the full target architecture with 8 engineers, on top of a walking skeleton. Every target layer (Cognito, Verified Permissions, Athena + Glue, Lake Formation, connectors + EventBridge, CloudTrail) sits behind a config flag with a working fallback. Go/no-go per layer at Day 2 12:00. Plan: `docs/TEAM_PLAN.md` in the repo → [[Team plan]].
## Why
Team capacity is there (8 seniors with AI help); a running multi-tenant, role-scoped system makes the reuse case real. The flags protect the demo and the clean-deploy gate.
## Rejected
POC-only (first version of this decision, same day; reversed by the lead). Target with no fallbacks.

Related: [[Decisions]], [[Teammate target diagram v1 review]]
