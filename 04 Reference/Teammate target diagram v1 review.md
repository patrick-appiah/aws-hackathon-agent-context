---
date: 2026-10-13
tags: [reference, area/architecture]
---
# Teammate target diagram v1: review
![[architecture-target-v1.png]]

**Keep:** same 5 agents, blind critic, retry guard (max 2), rejected records, human approval with sent-back, one KPI service for dashboard + analyst, swappable connectors (reuse story), role/tenant/entity scope, Guardrails, observability, CloudTrail.

**v2 must match the target Mermaid diagram in ARCHITECTURE.md §3b (v0.6)** (§3 is now the POC), which is now the reference.

**Fix for v2:**
1. Split **ask** (read-only, answer straight to the portal) from **publish status pack** (human approval). Today every answer waits for the delivery lead.
2. **It is now purely the target (90-day roadmap)**, with a separate POC diagram in ARCHITECTURE.md §3. Label each target-only layer with its roadmap phase: Verified Permissions (1), connectors + EventBridge + Athena/Glue (1), Lake Formation + CloudTrail (2), multi-tenant onboarding (3). Cognito is built in the POC.
3. Add a **budget check** before the orchestrator (reads cost from the run ledger).
4. Draw **retry guard ← run ledger** (attempt count lives in the ledger).
5. Label the **Step Functions** parts: Express ask spine, Choice retry guard, Standard publish + waitForTaskToken. Mark the orchestrator as "the one planning agent".
6. Add **external data** to Sources: close/holiday calendars, vendor support dates.
7. Optional: show the critic receiving only claim + cited rows; show rejected records reaching the portal as "could not verify".

Related: [[Reference]], [[2026-10-13 Ask spine is Step Functions Express, publish is Standard|Ask spine decision]], [[2026-10-13 Two architecture views, POC and target|POC and target views]]
