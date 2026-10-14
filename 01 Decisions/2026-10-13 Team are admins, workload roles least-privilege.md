---
date: 2026-10-13
status: done
tags: [decision, status/done, area/iam, area/security]
---
# Team admin vs workload IAM
## Decision
All 8 humans are in `hackathon-admins`. Every Lambda/runtime role is least-privilege in CDK.
## Why
Speed for 8 builders in a throwaway sandbox; the gate judges the deployed system's permissions.
## Rejected
Per-person scoped IAM (too slow for 2 days). PowerUserAccess (can't create roles).

Related: [[Decisions]], [[AWS sandbox]]
