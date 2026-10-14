---
date: 2026-10-13
status: done
tags: [decision, status/done, area/security]
---
# Scope from the token, enforced twice
## Decision
`{user_id, role, tenant_id, entity_ids}` built server-side from Cognito claims → Verified Permissions → every tool call → Lake Formation row filters.
## Why
Multi-tenant reuse across portfolio companies needs hard isolation, even through an agent tool bug.
## Rejected
Client-sent scope; a single enforcement layer

Related: [[Decisions]]
