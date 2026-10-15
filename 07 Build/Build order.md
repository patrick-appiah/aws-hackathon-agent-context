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

## Waves: who can work in parallel
Work in parallel: an item starts as soon as its dependencies are merged into `develop`, not when the row above it is done. The waves below are the dependency columns read as a timeline. A wave starts item by item, not all at once.

| Wave | Can start when | Items |
|---|---|---|
| **1: now** | C1 is merged | P1, H1, H5, L1, L4, L7, F1a, M1, A1, A3a, A4a |
| **2** | wave 1 items merge | H3 and L5 (after P1) · H2a (after H1, H5) · L2 (after L1) · M2 (after M1) · F1b (after F1a, L4) · F3b (after F1b, L1) · M3a, M3b (after M2) |
| **3** | the spine pieces exist | H2b (after H2a, H3) · P2 (after H2a; a stub until L5 lands) · Y1 (after M3a, M3b) · M4a · F2 |
| **4** | the spine runs | H4, H6, P3, L3, Y2a, Y3a, F4a, F5 |
| **5** | deployed end to end | Y2b, Y3b, L6, M4b, H7 timing, A5a/b, M5, Y4, F6, B1–B3 |

- **Critical path:** P1 → H3 → H2b → L3 → Y2a. Patrick merges these PRs within the hour they're ready.
- **Waiting on a dependency?** Write against its declared interface with a fake, as P2 does for L5, but don't merge before it.
- **Idle early:** Yaw pairs with Michael on M2 and M3a/M3b; Clement pairs with Mildred on F1a and F1b.
- The rows below stay the source of truth. If a "Depends on" cell and this table disagree, the cell wins.

## Back end
| ID | Item | Owner | Depends on | Milestone | Status | Spec / plan |
|---|---|---|---|---|---|---|
| **C2** | Repo layout (C2) | Patrick | (none) | M0 | **merged** (PR #27) | [[C2 - Repo layout - spec]] |
| **C1** | API and ask-spine contracts (`tools/api_schema.py` *(new)*, step models with `usage`, settings, JSON Schema, DevOps handover) | Patrick | (none) | M0 | **merged** (PR #22, 5d6ff5f; 213 tests, 96%) | [[C1 - API and spine contracts - spec]] · [[C1 - API and spine contracts - plan]] |
| P1 | Retriever agent + prompt | Patrick | C1 | M2 | **merged** (PR #24, 1b815aa) | [[P1 - Retriever agent - spec]] · [[P1 - Retriever agent - plan]] |
| P2 | Orchestrator agent + prompt (budget via H2a, `PartialAnswer`, re-plan) | Patrick | C1, H2a, L5 (or a stub) | M2 | **merged** (PR #47, 9f16bd6) | [[P2 - Orchestrator agent - spec]] · [[P2 - Orchestrator agent - plan]] |
| P3 | `scripts/ask.py` *(new)* local runner on `run_spine` | Patrick | H2b | M2 | **merged** (PR #50, 2f372c7) | [[P3 - Local ask runner - spec]] · [[P3 - Local ask runner - plan]] |
| P4 | Retriever as a fixed lookup, no model (D-028) | Patrick | P1, P2 | M3 | **merged** (PR #72, 252aea2) | [[P4 - Fixed-lookup retriever - spec]] · [[P4 - Fixed-lookup retriever - plan]] |
| P5 | Remove the layout guard tests; rules documented | Patrick | (none) | M3 | **merged** (PR #84, 2c2a809; 596 tests, D-032) | [[P5 - Remove layout guard tests - spec]] · [[P5 - Remove layout guard tests - plan]] |
| H1 | Ledger extensions (rejected records, read methods, steps, task tokens) on both adapters | Huvison | C1 | M2 | **merged** (PR #26, d2d0e35) | [[H1 - Ledger extensions - spec]] · [[H1 - Ledger extensions - plan]] |
| H2a | Budget and ledger states (`tools/budget.py` *(new)*, the ledger steps of the ask spine) | Huvison | C1, H1, H5 | M2 | **merged** (PR #34, ebd66e0) | [[H2a - Budget and ledger states - spec]] · [[H2a - Budget and ledger states - plan]] |
| H2b | Agent states, local spine (`run_spine`) and Lambda handlers | Huvison | H2a, H3, H5 | M2 | **merged** (PR #49, eaeca3c) | [[H2b - Agent states, local spine and Lambda handlers - spec]] · [[H2b - Agent states, local spine and Lambda handlers - plan]] |
| H3 | Writer agent + prompt (drops uncited bullets) | Huvison | C1, P1 | M2 | **merged** (PR #39, 3e08c96) | [[H3 - Writer agent - spec]] · [[H3 - Writer agent - plan]] |
| H4 | Publish + approve (`infra/functions/publish.py` *(new)*, task token, status-pack write) | Huvison | C1, H1, H2b | M3 | **merged** (PR #59, ca0f645) | [[H4 - Publish and approve - spec]] · [[H4 - Publish and approve - plan]] |
| H5 | Cost per run (price table, `tools/cost.py` *(new)*) | Huvison | C1 | M4 | **merged** (PR #32, 056384e) | [[H5 - Cost per run - spec]] · [[H5 - Cost per run - plan]] |
| H6 | Local eval asker `infra/functions/local.py` *(new)* (applies `inject`; decides the Q09 verdict count) | Huvison | H2b, P2 | M3 | **merged** (PR #66, 651abb2) | [[H6 - Local eval asker - spec]] · [[H6 - Local eval asker - plan]] |
| H7 | Guardrail settings (PII and prompt-attack filters) and the `/ask` latency check (sync or async decision) | Huvison | P1; M3a for the deploy part; Y2a deployed and H6 merged for the timing | M3 | **merged** (PR #74, 0a566fa: Guardrail on every agent, critic through `bedrock_model`); **latency decided: D-023 async** (timing part not needed) | [[H7 - Guardrail settings and ask latency - spec]] · [[H7 - Guardrail settings and ask latency - plan]] |
| H8 | Stored answer for `GET /ask/{run_id}`, budget checks before critic/writer/re-plan, 4 claims per plan | Huvison | H2b, D-023 | M4 | **merged** (PR #81, 66f88a1) | [[H8 - Stored answer with budget gates and a claim cap - spec]] · [[H8 - Stored answer with budget gates and a claim cap - plan]] |
| H9 | Critic: figures recomputed by code (D-030), shared model with no streaming, `Verdict`-validated; nothing-blocking answer for a clean entity (Q03) | Huvison | H8 | M4 | **merged** (PR #85, 229d472) | [[H9 - Critic figures and the nothing-blocking answer - spec]] · [[H9 - Critic figures and the nothing-blocking answer - plan]] |
| L1 | `infra/functions/scope.py` *(new)* + `/summary` handler (+ `DEMO_ROLE` for `AUTH_MODE=none`) | Linus | C1 | M2 | merged (PR #36, ced667f) | [[L1 - Scope from the token and the summary handler - spec]] · [[L1 - Scope from the token and the summary handler - plan]] |
| L2 | `/entity`, `/rows`, the error body | Linus | C1, L1 | M2 | merged (PR #46, 392da2d) | [[L2 - Entity and rows handlers - spec]] · [[L2 - Entity and rows handlers - plan]] |
| L3 | `/ask`, `/publish`, `/approve` entry points (Q11 pre-run refusal) | Linus → **Patrick** (Linus away, 2026-10-15) | L1, H2b, H4 | M3 | **merged** (PR #78; works in AWS now that H8 is merged) | [[L3 - Ask, publish and approve entry points - spec]] · [[L3 - Ask, publish and approve entry points - plan]] |
| L4 | `scripts/export_summary.py` *(new)* (front-end fixtures) | Linus | C1 | M2 | merged (PR #42, 5c33292) | [[L4 - Front-end fixtures from the real summary - spec]] · [[L4 - Front-end fixtures from the real summary - plan]] |
| L5 | Blocker-analyst agent + prompt | Linus | C1, P1 | M2 | merged (PR #52, cb7dd4b) | [[L5 - Blocker-analyst agent - spec]] · [[L5 - Blocker-analyst agent - plan]] |
| L6 | Deployed-API eval asker `evals/api_asker.py` *(new)* | Linus | L3, Y1, M3b | M4 | **merged** (PR #97, cf43b68: deployed-API eval asker) | [[L6 - Deployed-API eval asker - spec]] · [[L6 - Deployed-API eval asker - plan]] |
| L7 | `docs/ROADMAP.md` review and update (exists on develop) | Linus | (none) | M5 | spec + plan ready | [[L7 - Roadmap draft - spec]] · [[L7 - Roadmap draft - plan]] |

## Evals, Cognito, docs (Abdul, no Python)
| ID | Item | Owner | Depends on | Milestone | Status | Spec / plan |
|---|---|---|---|---|---|---|
| A1 | Review the 28 eval files against `EVALS.md`; Q10 on Day 2; manual checks (Q02, Q03, Q09, Q11) after each run | Abdul | (none); Task 6: H6/L6 | M0, then every run | in progress (review done: PR #30, Q05 wording PR #83; Q10 + manual checks wait on the first recorded run) | [[A1 - Eval set review and manual checks - spec]] · [[A1 - Eval set review and manual checks - plan]] |
| A2 | Cognito groups, claims and test users (with Michael) | Abdul | (none); Tasks 3–4: M3b, Y1, L1–L2, F3, F4 | M3 | in progress (HANDOFF section merged, PR #43; AuthStack PR #44 matches the list; Task 3 done: console matches; Task 4 sign-in test pending) | [[A2 - Cognito groups, claims and test users - spec]] · [[A2 - Cognito groups, claims and test users - plan]] |
| A3a | Bedrock unit prices | Abdul | (none) | M2 | **merged** (PR #25, 2372f97; Opus follow-up PR #31) | [[A3a - Bedrock unit prices - spec]] · [[A3a - Bedrock unit prices - plan]] |
| A3b | COST measured figures | Abdul | A3a, H5, H6, A5a | M5 | **merged** (PR #98, on Patrick's run #93) | [[A3b - COST measured figures - spec]] · [[A3b - COST measured figures - plan]] |
| A4a | Target architecture diagram v2 | Abdul | (none) | M5 | **merged** (PR #40) | [[A4a - Target architecture diagram v2 - spec]] · [[A4a - Target architecture diagram v2 - plan]] |
| A4b | HANDOFF and DEMO lines | Abdul | A5a, A3b, A2 | M5 | **merged** (PR #99; Q10 line pending the live question) | [[A4b - HANDOFF and DEMO lines - spec]] · [[A4b - HANDOFF and DEMO lines - plan]] |
| A4c | Prompt wording review | Abdul | P1, P2, L5, H3 PRs | M4 | in progress (issue #45: critic, retriever, writer reviewed; orchestrator, analyst when their PRs open) | [[A4c - Prompt wording review - spec]] · [[A4c - Prompt wording review - plan]] |
| A5a | EVALS results write-up | Abdul (with Linus) | H6 | M5 | **merged** (PR #98, on Patrick's run #93) | [[A5a - EVALS results write-up - spec]] · [[A5a - EVALS results write-up - plan]] |
| A5b | Worked examples per agent | Abdul (with Linus) | P1, P2, L5, H3, H6 | M4 | spec + plan ready | [[A5b - Worked examples per agent - spec]] · [[A5b - Worked examples per agent - plan]] |

## DevOps
| ID | Item | Owner | Depends on | Milestone | Status | Spec / plan |
|---|---|---|---|---|---|---|
| M1 | Jenkins CI: PR #8 reviewed and merged; bandit list extended | Michael | (none) | M0 | **closed** (PR #8 closed 2026-10-15: CI moved from AmaliTech Jenkins to AWS CodeBuild, owned by Mintah) | [[M1 - Jenkins CI - spec]] · [[M1 - Jenkins CI - plan]] |
| M2 | `infra/app.py` *(new)* + DataStack + LedgerStack; CDK in its own `infra` dependency group; Node 22 in CI | Michael | C1, M1 (edits the Jenkinsfile) | M1 → M2 | **merged** (PR #37, 307da7c) | [[M2 - App, DataStack and LedgerStack - spec]] · [[M2 - App, DataStack and LedgerStack - plan]] |
| M3a | GuardrailStack | Michael | M2 | M1 → M3 | **merged** (PR #38, 18f98ae) | [[M3a - GuardrailStack - spec]] · [[M3a - GuardrailStack - plan]] |
| M3b | AuthStack (Cognito) | Michael | M2, A2 | M1 → M3 | **merged** (PR #44, 8ccf8d7) | [[M3b - AuthStack - spec]] · [[M3b - AuthStack - plan]] |
| M4a | WebStack (S3 + CloudFront, `/api/*`) and the Cognito callback fix | Michael | M2; app wiring needs M3b and Y1 | M1 → M2 | **merged** (PR #54, 9b5d3b7) | [[M4a - WebStack - spec]] · [[M4a - WebStack - plan]] |
| M4b | Observability (dashboards, alarms) | Michael | M2; app wiring needs Y1, Y2a and M4a | M2 | **merged** (PR #79, 6e02cbd: demo dashboard with cost per run, Transaction Search behind a switch) | [[M4b - Observability - spec]] · [[M4b - Observability - plan]] |
| M5 | Clean-deploy runbook (with Patrick) | Michael | all stacks | M2, M4 | **merged** (PR #77, 3e6867a: the five README commands, the check table in infra/README) | [[M5 - Clean-deploy runbook - spec]] · [[M5 - Clean-deploy runbook - plan]] |
| Y1 | ApiStack (HTTP API v2, JWT authorizer, routes) | Yaw | M3a, M3b | M1 → M2 | **merged** (PR #51, f17622a) | [[Y1 - ApiStack - spec]] · [[Y1 - ApiStack - plan]] |
| Y2a | Express ask spine + `/ask` | Yaw | Y1; Task 6 needs H2b and L3 | M1 → M3 | **merged** (PR #69, built by Michael; async `/ask` per D-023 merged as PR #71: `StartExecution`, `GET /ask/{run_id}` reads the ledger) | [[Y2a - Express ask spine - spec]] · [[Y2a - Express ask spine - plan]] |
| Y2b | Standard publish flow + `/publish`, `/approve` | Yaw | Y2a; Task 5 needs H4 and L3 | M3 | in review (PR #91, Yaw; changes requested: task-token IAM on `*`, API round trip) | [[Y2b - Standard publish flow - spec]] · [[Y2b - Standard publish flow - plan]] |
| Y3a | AgentCore runtime (code zip, no Docker) | Yaw | Y2a, H2b | M2 | spec + plan ready | [[Y3a - AgentCore runtime - spec]] · [[Y3a - AgentCore runtime - plan]] |
| Y3b | Agent shim and `agent_host=agentcore\|lambda` switch | Yaw | Y3a, Y2b | M2 | spec + plan ready | [[Y3b - Agent shim and host switch - spec]] · [[Y3b - Agent shim and host switch - plan]] |
| Y4 | IAM least-privilege review (no `*` except task-token actions) | Yaw (with Patrick) | all stacks | M2 | spec + plan ready | [[Y4 - IAM least-privilege review - spec]] · [[Y4 - IAM least-privilege review - plan]] |

## Front end
| ID | Item | Owner | Depends on | Milestone | Status | Spec / plan |
|---|---|---|---|---|---|---|
| F1a | Types from the JSON Schema; all 14 artefacts | Mildred | C1 | M2 | **merged** (PR #35, ec0aa53) | [[F1a - Contract types and the 14 artefacts - spec]] · [[F1a - Contract types and the 14 artefacts - plan]] |
| F1b | Fixtures from L4; dashboard on the contract keys | Mildred | F1a, L4 | M2 | **merged** (PR #48, d10d43e) | [[F1b - Real fixtures and the dashboard on the contract keys - spec]] · [[F1b - Real fixtures and the dashboard on the contract keys - plan]] |
| F2 | Click a number → `/rows`; `http` against the deployed API | Mildred | F1b, L2, Y1, M4a | M2 | **merged** (PR #53, 09084a6; deploy-config fix PR #56, 6a77814); live check (Task 4) passed 2026-10-15: signed in, figures match mock, 58% loads 49 rows from `/api/rows` | [[F2 - Click a number and the live API - spec]] · [[F2 - Click a number and the live API - plan]] |
| F3a | Cognito sign-in (managed login + PKCE) | Clement | M3b, Y1, F2 | M3 | merged (PR #67, 278d7aa); #60 merged; sign-in works on the deployed portal (Clement, 2026-10-15) | [[F3a - Cognito sign-in - spec]] · [[F3a - Cognito sign-in - plan]] |
| F3b | Role views and the 403 refusal | Clement | F1b, L1 | M3 | merged (PR #70, b108be5); live check waits on L3 | [[F3b - Role views and the 403 refusal - spec]] · [[F3b - Role views and the 403 refusal - plan]] |
| F4a | Ask panel on `/ask` (trace, cost, partial, could-not-verify) | Clement | C1, F1b, L3 | M3 | in review (PR #73; L3 merged (#78); live check waits on H8 (stored answer) + F4b) | [[F4a - Ask panel on the real ask contract - spec]] · [[F4a - Ask panel on the real ask contract - plan]] |
| F4b | Async ask polling (only if H7 decides async) | Clement | F4a, H7 (only if async) | M4 | in review (PR #75, stacked on #73) | [[F4b - Async ask polling - spec]] · [[F4b - Async ask polling - plan]] |
| F5 | Publish + approve on the real API | Clement | F1b, L3, H4 | M4 | spec + plan ready | [[F5 - Publish and approve on the real API - spec]] · [[F5 - Publish and approve on the real API - plan]] |
| F6 | Demo rehearsal + 2-minute backup video | Clement (with Patrick) | everything | M5 | spec + plan ready | [[F6 - Demo rehearsal and backup video - spec]] · [[F6 - Demo rehearsal and backup video - plan]] |

## Business case and pitch
| ID | Item | Owner | Depends on | Milestone | Status | Spec / plan |
|---|---|---|---|---|---|---|
| B1 | Close the `[TBC]`s in `business/business-case.md`; validation session (D1 09:30) | Patrick, Michael | A3a, A3b, H5, A5a, H6/L6 | M5 | business case merged (PR #88, 39f350e; measured time and cost, payback); validation session still to hold → lines 23 and 79 | [[B1 - Business case figures and validation - spec]] · [[B1 - Business case figures and validation - plan]] |
| B2 | Pitch deck (source + PDF in `business/`) | Patrick, Michael | B1, A3b, A5a, H6/L6 | M5 | in review (PR #90, Michael: deck fixes; reviewed by Patrick: 4 points + PDF) | [[B2 - Pitch deck - spec]] · [[B2 - Pitch deck - plan]] |
| B3a | One-page value case | Patrick, Michael | B1 | M5 | spec + plan ready | [[B3a - One-page value case - spec]] · [[B3a - One-page value case - plan]] |
| B3b | Architecture and cost slides | Patrick, Michael | B2, A4a, A3b | M5 | in review (PR #94, Michael: slides A1–A3; reviewed by Patrick: A3 to $0.27, A1 publish wording, PDF) | [[B3b - Architecture and cost slides - spec]] · [[B3b - Architecture and cost slides - plan]] |
| B3c | Pitch script and Q and A | Patrick, Michael | B2, B3b, F6 | M5 | spec + plan ready | [[B3c - Pitch script and Q and A - spec]] · [[B3c - Pitch script and Q and A - plan]] |

*M3\* is the GuardrailStack + AuthStack item. It isn't the D2 12:00 milestone M3.*

*M3a (GuardrailStack), M3b (AuthStack) and M4a (WebStack) are the split DevOps items: [[M3a - GuardrailStack - spec]], [[M3b - AuthStack - spec]], [[M4a - WebStack - spec]]. The DevOps rows above are updated separately.*

Related: [[Workstreams]], [[How to execute a plan]]
