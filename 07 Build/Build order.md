---
tags: [build, moc]
updated: 2026-10-14
---
# Build order
> **Every build item, its owner, what it depends on, its milestone and its status.** The stand-ups and the [[Progress auditor - handoff|progress auditor]] read this note. Owners update their own row (see [[How to execute a plan]] §5).
>
> **Status values:** `not specced` · `spec + plan ready` · `in progress` · `in review (PR #nn)` · `merged` · `blocked (why)`.
>
> **Start an item only when every item in its "Depends on" column is `merged`,** unless its plan says it builds against today's types and fakes.

Milestones (`docs/TEAM_PLAN.md` §4):
- **M0** D1 10:30: contracts frozen.
- **M1** D1 12:00: stacks deploy empty.
- **M2** D1 18:00: walking skeleton live in AWS.
- **M3** D2 12:00: Cognito go/no-go, real critic and retry, publish.
- **M4** D2 14:00: code freeze.
- **M5** D2 16:00: docs, evals, cost, rehearsal.

## Back end
| ID | Item | Owner | Depends on | Milestone | Status | Spec / plan |
|---|---|---|---|---|---|---|
| **C1** | API and ask-spine contracts (`tools/api_schema.py` *(new)*, step models with `usage`, settings, JSON Schema, DevOps handover) | Patrick | (none) | M0 | spec + plan ready | [[C1 - API and spine contracts - spec]] · [[C1 - API and spine contracts - plan]] |
| P1 | Retriever agent + prompt | Patrick | C1 | M2 | spec + plan ready | [[P1 - Retriever agent - spec]] · [[P1 - Retriever agent - plan]] |
| P2 | Orchestrator agent + prompt (budget via H2a, `PartialAnswer`, re-plan) | Patrick | C1, H2a, L5 (or a stub) | M2 | spec + plan ready | [[P2 - Orchestrator agent - spec]] · [[P2 - Orchestrator agent - plan]] |
| P3 | `scripts/ask.py` *(new)* local runner on `run_spine` | Patrick | H2b | M2 | spec + plan ready | [[P3 - Local ask runner - spec]] · [[P3 - Local ask runner - plan]] |
| H1 | Ledger extensions (rejected records, read methods, steps, task tokens) on both adapters | Huvison | C1 | M2 | spec + plan ready | [[H1 - Ledger extensions - spec]] · [[H1 - Ledger extensions - plan]] |
| H2a | Budget and ledger states (`flow/budget.py` *(new)*, the ledger steps of the ask spine) | Huvison | C1, H1, H5 | M2 | spec + plan ready | [[H2a - Budget and ledger states - spec]] · [[H2a - Budget and ledger states - plan]] |
| H2b | Agent states, local spine (`run_spine`) and Lambda handlers | Huvison | H2a, H3, H5 | M2 | spec + plan ready | [[H2b - Agent states, local spine and Lambda handlers - spec]] · [[H2b - Agent states, local spine and Lambda handlers - plan]] |
| H3 | Writer agent + prompt (drops uncited bullets) | Huvison | C1, P1 | M2 | spec + plan ready | [[H3 - Writer agent - spec]] · [[H3 - Writer agent - plan]] |
| H4 | Publish + approve (`flow/publish.py` *(new)*, task token, status-pack write) | Huvison | C1, H1, H2b | M3 | spec + plan ready | [[H4 - Publish and approve - spec]] · [[H4 - Publish and approve - plan]] |
| H5 | Cost per run (price table, `flow/cost.py` *(new)*) | Huvison | C1 | M4 | spec + plan ready | [[H5 - Cost per run - spec]] · [[H5 - Cost per run - plan]] |
| H6 | Local eval asker `flow/local.py` *(new)* (applies `inject`; decides the Q09 verdict count) | Huvison | H2b, P2 | M3 | spec + plan ready | [[H6 - Local eval asker - spec]] · [[H6 - Local eval asker - plan]] |
| H7 | Guardrail settings (PII and prompt-attack filters) and the `/ask` latency check (sync or async decision) | Huvison | P1; M3a for the deploy part; Y2a deployed and H6 merged for the timing | M3 | spec + plan ready | [[H7 - Guardrail settings and ask latency - spec]] · [[H7 - Guardrail settings and ask latency - plan]] |
| L1 | `auth/scope.py` *(new)* + `/summary` handler (+ `DEMO_ROLE` for `AUTH_MODE=none`) | Linus | C1 | M2 | spec + plan ready | [[L1 - Scope from the token and the summary handler - spec]] · [[L1 - Scope from the token and the summary handler - plan]] |
| L2 | `/entity`, `/rows`, the error body | Linus | C1, L1 | M2 | spec + plan ready | [[L2 - Entity and rows handlers - spec]] · [[L2 - Entity and rows handlers - plan]] |
| L3 | `/ask`, `/publish`, `/approve` entry points (Q11 pre-run refusal) | Linus | L1, H2b, H4 | M3 | spec + plan ready | [[L3 - Ask, publish and approve entry points - spec]] · [[L3 - Ask, publish and approve entry points - plan]] |
| L4 | `scripts/export_summary.py` *(new)* (front-end fixtures) | Linus | C1 | M2 | spec + plan ready | [[L4 - Front-end fixtures from the real summary - spec]] · [[L4 - Front-end fixtures from the real summary - plan]] |
| L5 | Blocker-analyst agent + prompt | Linus | C1, P1 | M2 | spec + plan ready | [[L5 - Blocker-analyst agent - spec]] · [[L5 - Blocker-analyst agent - plan]] |
| L6 | Deployed-API eval asker `evals/api_asker.py` *(new)* | Linus | L3, Y1, M3b | M4 | spec + plan ready | [[L6 - Deployed-API eval asker - spec]] · [[L6 - Deployed-API eval asker - plan]] |
| L7 | `docs/ROADMAP.md` review and update (exists on develop) | Linus | (none) | M5 | spec + plan ready | [[L7 - Roadmap draft - spec]] · [[L7 - Roadmap draft - plan]] |

## Evals, Cognito, docs (Abdul, no Python)
| ID | Item | Owner | Depends on | Milestone | Status | Spec / plan |
|---|---|---|---|---|---|---|
| A1 | Review the 28 eval files against `EVALS.md`; Q10 on Day 2; manual checks (Q02, Q03, Q09, Q11) after each run | Abdul | (none); Task 6: H6/L6 | M0, then every run | spec + plan ready | [[A1 - Eval set review and manual checks - spec]] · [[A1 - Eval set review and manual checks - plan]] |
| A2 | Cognito groups, claims and test users (with Michael) | Abdul | (none); Tasks 3–4: M3*, Y1, L1–L2, F3, F4 | M3 | spec + plan ready | [[A2 - Cognito groups, claims and test users - spec]] · [[A2 - Cognito groups, claims and test users - plan]] |
| A3a | Bedrock unit prices | Abdul | (none) | M2 | spec + plan ready | [[A3a - Bedrock unit prices - spec]] · [[A3a - Bedrock unit prices - plan]] |
| A3b | COST measured figures | Abdul | A3a, H5, H6, A5a | M5 | spec + plan ready | [[A3b - COST measured figures - spec]] · [[A3b - COST measured figures - plan]] |
| A4a | Target architecture diagram v2 | Abdul | (none) | M5 | spec + plan ready | [[A4a - Target architecture diagram v2 - spec]] · [[A4a - Target architecture diagram v2 - plan]] |
| A4b | HANDOFF and DEMO lines | Abdul | A5a, A3b, A2 | M5 | spec + plan ready | [[A4b - HANDOFF and DEMO lines - spec]] · [[A4b - HANDOFF and DEMO lines - plan]] |
| A4c | Prompt wording review | Abdul | P1, P2, L5, H3 PRs | M4 | spec + plan ready | [[A4c - Prompt wording review - spec]] · [[A4c - Prompt wording review - plan]] |
| A5a | EVALS results write-up | Abdul (with Linus) | H6 | M5 | spec + plan ready | [[A5a - EVALS results write-up - spec]] · [[A5a - EVALS results write-up - plan]] |
| A5b | Worked examples per agent | Abdul (with Linus) | P1, P2, L5, H3, H6 | M4 | spec + plan ready | [[A5b - Worked examples per agent - spec]] · [[A5b - Worked examples per agent - plan]] |

## DevOps
| ID | Item | Owner | Depends on | Milestone | Status |
|---|---|---|---|---|---|
| M1 | Jenkins CI: PR #8 reviewed and merged; bandit list extended | Michael | (none) | M0 | in review (PR #8) |
| M2 | `infra/app.py` *(new)* + DataStack + LedgerStack | Michael | C1 (handover) | M1 → M2 | not specced |
| M3* | GuardrailStack + AuthStack (Cognito) | Michael | C1, A2 | M1 → M3 | not specced |
| M4 | WebStack (S3 + CloudFront, `/api/*`) + observability | Michael | M2 | M1 → M2 | not specced |
| M5 | Clean-deploy runbook (with Patrick) | Michael | all stacks | M2, M4 | not specced |
| Y1 | ApiStack (HTTP API v2, JWT authorizer, routes) | Yaw | C1, M3* | M1 → M2 | not specced |
| Y2 | FlowStack (Express ask spine, Standard publish) | Yaw | C1, H2, H4 | M1 → M3 | not specced |
| Y3 | AgentStack (AgentCore + Lambda fallback + shim) | Yaw | C1, P2 | M1 → M2 | not specced |
| Y4 | IAM review (least privilege, no `*`) | Yaw (with Patrick) | all stacks | M2 | not specced |

## Front end
| ID | Item | Owner | Depends on | Milestone | Status | Spec / plan |
|---|---|---|---|---|---|---|
| F1a | Types from the JSON Schema; all 14 artefacts | Mildred | C1 | M2 | spec + plan ready | [[F1a - Contract types and the 14 artefacts - spec]] · [[F1a - Contract types and the 14 artefacts - plan]] |
| F1b | Fixtures from L4; dashboard on the contract keys | Mildred | F1a, L4 | M2 | spec + plan ready | [[F1b - Real fixtures and the dashboard on the contract keys - spec]] · [[F1b - Real fixtures and the dashboard on the contract keys - plan]] |
| F2 | Click a number → `/rows`; `http` against the deployed API | Mildred | F1b, L2, Y1, M4a | M2 | spec + plan ready | [[F2 - Click a number and the live API - spec]] · [[F2 - Click a number and the live API - plan]] |
| F3a | Cognito sign-in (managed login + PKCE) | Clement | M3b, Y1, F2 | M3 | spec + plan ready | [[F3a - Cognito sign-in - spec]] · [[F3a - Cognito sign-in - plan]] |
| F3b | Role views and the 403 refusal | Clement | F1b, L1 | M3 | spec + plan ready | [[F3b - Role views and the 403 refusal - spec]] · [[F3b - Role views and the 403 refusal - plan]] |
| F4a | Ask panel on `/ask` (trace, cost, partial, could-not-verify) | Clement | C1, F1b, L3 | M3 | spec + plan ready | [[F4a - Ask panel on the real ask contract - spec]] · [[F4a - Ask panel on the real ask contract - plan]] |
| F4b | Async ask polling (only if H7 decides async) | Clement | F4a, H7 (only if async) | M4 | spec + plan ready | [[F4b - Async ask polling - spec]] · [[F4b - Async ask polling - plan]] |
| F5 | Publish + approve on the real API | Clement | F1b, L3, H4 | M4 | spec + plan ready | [[F5 - Publish and approve on the real API - spec]] · [[F5 - Publish and approve on the real API - plan]] |
| F6 | Demo rehearsal + 2-minute backup video | Clement (with Patrick) | everything | M5 | spec + plan ready | [[F6 - Demo rehearsal and backup video - spec]] · [[F6 - Demo rehearsal and backup video - plan]] |

## Business case and pitch
| ID | Item | Owner | Depends on | Milestone | Status | Spec / plan |
|---|---|---|---|---|---|---|
| B1 | Close the `[TBC]`s in `business/business-case.md`; validation session (D1 09:30) | Patrick, Michael | A3a, A3b, H5, A5a, H6/L6 | M5 | spec + plan ready | [[B1 - Business case figures and validation - spec]] · [[B1 - Business case figures and validation - plan]] |
| B2 | Pitch deck (source + PDF in `business/`) | Patrick, Michael | B1, A3b, A5a, H6/L6 | M5 | spec + plan ready | [[B2 - Pitch deck - spec]] · [[B2 - Pitch deck - plan]] |
| B3a | One-page value case | Patrick, Michael | B1 | M5 | spec + plan ready | [[B3a - One-page value case - spec]] · [[B3a - One-page value case - plan]] |
| B3b | Architecture and cost slides | Patrick, Michael | B2, A4a, A3b | M5 | spec + plan ready | [[B3b - Architecture and cost slides - spec]] · [[B3b - Architecture and cost slides - plan]] |
| B3c | Pitch script and Q and A | Patrick, Michael | B2, B3b, F6 | M5 | spec + plan ready | [[B3c - Pitch script and Q and A - spec]] · [[B3c - Pitch script and Q and A - plan]] |

*M3\* is the GuardrailStack + AuthStack item. It isn't the D2 12:00 milestone M3.*

*M3a (GuardrailStack), M3b (AuthStack) and M4a (WebStack) are the split DevOps items: [[M3a - GuardrailStack - spec]], [[M3b - AuthStack - spec]], [[M4a - WebStack - spec]]. The DevOps rows above are updated separately.*

Related: [[Workstreams]], [[How to execute a plan]]
