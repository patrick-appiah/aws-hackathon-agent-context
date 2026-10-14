---
date: 2026-10-13
source: repo docs/ROADMAP.md (the repo copy is canonical; regenerate this note from it, never edit it by hand)
synced_from_commit: 1f25771
tags: [reference, area/scope]
---
# Roadmap: from the hackathon POC to production in 90 days

> What a portfolio company gets if it funds the next 90 days. The POC we demo is Phase 0; the target architecture in `ARCHITECTURE.md` §3b is where Phase 3 ends. Targets marked *proposed* are ours until confirmed with the problem owner.

## Phase 0: hackathon POC (2 days, done at the demo)
- The one screen (source → target, timeline, capacity, % complete) from synthetic artefacts.
- The full agent loop: orchestrator, retriever, blocker-analyst, blind critic with a bounded retry guard, and writer. Every claim is cited.
- Run ledger, versioned prompt files, Guardrails, a budget ceiling per run, and human-approved status-pack publishing.
- **One target slice:** Cognito sign-in with role and entity scope. An entity lead can't see another entity.
- What's faked is listed in `HANDOFF.md`.

## Phase 1: pilot (weeks 1–6), one portfolio company, one programme
| Work | Detail |
|---|---|
| Real data in | Connectors for the project tool (workplan), the defect tracker and the migration tool's reconciliation exports; scheduled refresh (EventBridge); Glue + Athena replace CSV |
| Real users | Cognito federated with the client's identity provider; the four roles; Verified Permissions policies |
| Quality bar | An eval set grown to ~40 questions written **with** the delivery lead; failures triaged weekly from the rejected-records queue |
| Status pack | The monthly steering pack generated, approved in the portal and sent, for two cycles |

**Go / no-go at week 6 (proposed):**
- ≥ 85% of the eval set answered correctly, with citations.
- Zero answers using rows outside the asker's scope.
- The delivery lead approves two generated status packs with only minor edits.
- Cost per question within the `COST.md` pilot estimate.

## Phase 2: production hardening (weeks 7–10)
- Lake Formation row filters under Athena: scope enforced a second time, in the data layer.
- CloudTrail data events for "who saw what"; AgentCore Observability dashboards; cost and error alarms.
- The eval set runs in CI on every prompt or agent change, and a score drop blocks the release.
- Runbook and on-call handover to the client's IT team.

**Go / no-go at week 10 (proposed):**
- The client security review passes.
- Evals stay at or above the Phase 1 bar in CI for two weeks.
- No Sev-1 incidents in the last two weeks of pilot use.

## Phase 3: scale and reuse (weeks 11–13)
- **Second portfolio company onboarded as a new tenant:** a new data prefix, a connector configuration and new users, with **no code changes**. This proves the template (the business case's reuse argument).
- External data: vendor support-lifecycle dates; holiday and financial-close calendars from the client; an automation estimate from published AWS Transform capability.
- Onboarding guide, so the next tenant takes days, not weeks.

**Go / no-go at week 13 (proposed):**
- The second tenant is live within 5 working days of data access.
- Its users see none of the first tenant's data (verified by the cross-tenant eval questions).

## Team (proposed)
- **Weeks 1–6:** 3 engineers + 1 delivery lead (part-time) + the client's delivery lead as product owner.
- **Weeks 7–13:** 2 engineers + 1 platform/security engineer (part-time).

## What we need from the client
1. A named **sponsor** (CFO or programme sponsor) and a **delivery lead** as product owner.
2. Read access (API or export) to the project tool, the defect tracker and the migration tool's reconciliation outputs.
3. Identity-provider federation for Cognito, and the list of users per role and entity.
4. A security reviewer available in weeks 6–9.
5. Their financial-close and holiday calendars.

## Top 3 risks
| Risk | Effect | Mitigation | Stop if |
|---|---|---|---|
| **Source data quality.** IDs don't line up across tools (workplan vs defects vs reconciliation) | Wrong joins mean wrong blockers | Week-2 data-quality report from the connectors; ID mapping table owned by the client's delivery lead | Mapping isn't agreed by week 4 |
| **Answer accuracy.** The agent misses or invents blockers on real data | Loss of trust; the sponsor stops using it | The critic and citations already reject unsupported claims; the eval set is co-written with the client; rejected records are triaged weekly | Below the 85% bar after week 6 |
| **Access and security approvals are slow** | Pilot starts late | Request access and IdP federation in week 1; run on synthetic or sanitised data meanwhile | No data access by week 3 |

Related: `ARCHITECTURE.md` §3b (target), `COST.md` (pilot and full-scale cost), `HANDOFF.md` (what's real today), `DECISIONS.md` D-015.

Related: [[Reference]], [[2026-10-13 POC plus one target slice, target as 90-day roadmap|D-015]], [[Team plan]]
