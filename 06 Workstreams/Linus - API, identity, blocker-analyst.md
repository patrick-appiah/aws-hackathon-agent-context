---
tags: [workstream, area/team]
owner: Linus
updated: 2026-10-14
---
# Linus: API, identity, blocker-analyst, eval runner
> The repo is the source of truth. Read [[Workstreams]] first. Your row: `docs/TEAM_PLAN.md` §2, workstream 3. You pair with Abdul ([[Abdul - evals, Cognito, docs]]), who doesn't write Python. Mentor him and own the code side of his tasks.

## Your job in one paragraph
You build:
- **the API**, the door everyone uses: the dashboard handlers (`/summary`, `/entity/{id}`, `/rows`), the HTTP entry points for `/ask`, `/publish` and `/approve`, and **scope built from the sign-in token**, so an entity lead can never see another entity's data;
- **the blocker-analyst**, the agent that turns evidence into cited, figure-checked claims;
- **the eval runner** on Day 2, which scores the 14 questions honestly.

You're also the back end's main contact for DevOps, and the person who gets the front end off mock data: `scripts/export_summary.py`, then the live API.

## Where you sit in the architecture
```
 Portal ─JWT─▶ API Gateway HTTP API (Yaw) ─▶ ★api/handlers.py★
     ├─ summary / entity / rows ─▶ ★auth/scope.py★ (claims → Scope) ─▶ tools/metrics.py · tools/queries.py ─▶ CSV/S3
     ├─ ask ─▶ scope check (Q11: 403 BEFORE any run starts) ─▶ Step Functions Express (Huvison's flow/)
     └─ publish / approve ─▶ Huvison's flow/publish.py (start_publish, decide)
 orchestrator (Patrick) ─▶ ★BLOCKER-ANALYST★ ─▶ make_analyst_tools(scope, repo) ─▶ metrics
                                           └─▶ every claim checked by tools/claims.py validate_claim
 Day 2: ★evals/run.py★ ─▶ evals/inputs/Qnn.json (Abdul) ─▶ the flow in-process ─▶ scores ─▶ evals/results/
```
- **Handlers are thin.** No business logic in `api/`. Numbers come only from `tools/metrics.py` (D-001); lookups only from `tools/queries.py`.
- **Scope flows from the token** (`ARCHITECTURE.md` §4). The client never sends scope; a model never supplies it.

## What you own
| Path | State |
|---|---|
| `tools/metrics.py`, `tools/queries.py`, `tools/agent_tools.py`, `tools/claims.py` | exist, 140 tests; you maintain them |
| `api/handlers.py` *(new)*, `auth/scope.py` *(new)* | API and identity |
| `agents/blocker_analyst.py` *(new)*, `agents/prompts/blocker_analyst.txt` *(new)* | the analyst |
| `scripts/export_summary.py` *(new)* | front-end fixtures from the real summary |
| `evals/run.py` *(new)*, `evals/results/` *(new)* | the eval runner |
| `AGENTS.md` blocker-analyst row; `HANDOFF.md` lines for your parts | your docs |

## What you build
Each task has a spec and plan first (superpowers), test-first code, and a PR to `develop`.

### 1. The scope builder: `auth/scope.py` (first)
- `scope_from_claims(claims: dict, settings) -> Scope`. The claims are the JWT claims API Gateway HTTP API (v2) passes in `event["requestContext"]["authorizer"]["jwt"]["claims"]`.
- **Exactly one group** in `cognito:groups` → `Scope.role` (`cfo`, `sponsor`, `delivery_lead`, `entity_lead`). None or several → 403 `forbidden`.
- `custom:tenant_id` → `tenant_id`.
- `custom:entity_ids` is a **comma-separated string**: `"E2,E4"` or `"*"` (Cognito custom attributes are strings), split into the tuple.
- `user_id` comes from `sub`.
- **`AUTH_MODE=none`** (Patrick's new `auth_mode` setting) → a demo CFO scope `(entity_ids=("*",))`, used only if the Cognito slice slips at the D2 12:00 go/no-go.
- **Tests:** a CFO, an E4 entity lead, missing claims, two groups, a malformed entity ID. `Scope.require` already raises `OutOfScope` and `validate_entity_id` raises `ValueError`.

### 2. The dashboard handlers: `api/handlers.py`
- **`summary(event, context)`:** scope → `metrics.portfolio_summary(repository_from_settings(), scope)`, validated as Patrick's `SummaryResponse` (`tools/api_schema.py` *(new)*).
- **`entity(event, context)`:** `/entity/{id}`; `scope.require(entity_id)`, then the entity row plus `open_blockers`, `failing_reconciliations` and `cutover_calendar_conflicts`.
- **`rows(event, context)`:** `/rows?cite=artefact:row_id,...`; `queries.rows_by_citation`; out-of-scope or unknown citations go to `missing`, using `queries.in_entity_view`. Never return them.
- **Errors:** `ErrorResponse {error, detail}`: 400 `invalid_input`, 403 `out_of_scope` / `forbidden`, 404 `not_found`.
- **Tests** call the handlers with fake HTTP API v2 events; no AWS.

### 3. The `/ask`, `/publish` and `/approve` entry points (same file)
- **`ask`:** validate the body `{entity_id, question}`; build the scope; **refuse an out-of-scope entity with 403 before anything starts** (EVALS Q11: no E2 rows may reach the ledger). Then start the Express execution (`ask_state_machine_arn`) and return its output as `AskResponse`.
- **`publish` / `approve`:** call Huvison's `flow.publish.start_publish(run_id, user)` and `flow.publish.decide(run_id, decision, note, scope)`. `approve` takes `run_id` (spec decision).

### 4. Fixtures for the front end: `scripts/export_summary.py`
- `uv run python scripts/export_summary.py` writes, from the real code:
  - `summary.json` (CFO scope);
  - `entity-E1.json` … `entity-E4.json`;
  - a `rows.json` sample;
  - an `ask-E4.json` example (from a local run once the flow exists);

  to `web/src/app/core/api/fixtures/`, in the schema shapes.
- **Agree the file names with Mildred.** This replaces `web/scripts/build-fixtures.mjs`'s read of `kpis.json`, which PR #11 deleted.

### 5. The blocker-analyst: `agents/blocker_analyst.py`, `agents/prompts/blocker_analyst.txt`
- **Input/output:** `{scope, entity_id, evidence}` → `BlockerClaim[]` + `Usage`.
  - Each claim is `{claim_id, statement, chain[{artefact, row_id, role_in_chain}], severity, owner_role, figures{name: {value, tool, args, field}}}`, as in `tools/models.py`.
- **Figures only from tools:** `as_strands_tools(make_analyst_tools(scope, repository))`: `days_to_cutover`, `records_reconciled`, `blocker_ages`, `role_utilisation`, `effort_cost`. `tools/claims.validate_claim` re-runs every figure's tool and rejects any mismatch.
- **Conflicting rows → a conflict claim,** never a silent pick (`AGENTS.md`, analyst row). Q02's decoy: `DEF-0398` is Closed, but `RC-C3-E4-customers` still fails and `E4#RB-010` needs it to pass.
- **The E4 chain to support (Q01):** `E4#RB-010` → `RC-C3-E4-customers` (91.2% vs 98%) → 212 load errors → `DEF-0412` (open, 18 days) → `E4#CUSMST#TAXNO`. `tests/tools/test_evidence_chain.py` walks it through the tools today.
- **Model:** `get_settings().analyst_model_id` with the Guardrail (the `agents/critic.py` `make_agent` pattern). Stub-model tests: valid claims pass `validate_claim`, and a wrong figure is rejected.

### 6. The eval runner, Day 2: `evals/run.py`
- `uv run python evals/run.py` reads every `evals/inputs/Qnn.json` (Abdul's format, below) and builds the flow **in-process**:
  - `CsvRepository`, `InMemoryLedger` and the real agents;
  - for Q08/Q09, Huvison's fault doubles (`evals/doubles.py`), chosen by the input's `fault` field. That field is read **only** by the runner.
- **Scoring:**
  - `must_cite` (every `artefact:row_id` appears in the answer's citations);
  - `must_not_say` (case-insensitive);
  - `expect` (`answer` / `partial` / `refused`);
  - `target_only: true` → reported as "not run (target)".
- **Output:** `evals/results/<YYYY-MM-DD>.json`, with the prompt versions (`load_prompt(name).provenance()` for each agent), the cost, pass/fail and the reasons, failures included. Abdul writes the `EVALS.md` results from it.
- **The input format (agree it with Abdul at D1 10:30):**
  ```json
  {"id": "Q01", "question": "What is blocking cutover for E4?", "entity_id": "E4",
   "scope": {"role": "cfo", "tenant_id": "t-01", "entity_ids": ["*"]},
   "must_cite": ["reconciliation_results:RC-C3-E4-customers", "defect_log:DEF-0412", "cutover_runbook:E4#RB-010"],
   "must_not_say": ["resolved"], "expect": "answer", "fault": null, "target_only": false, "source": "EVALS.md Q01"}
  ```

### 7. DevOps contact and mentoring
- **For Yaw:** keep your rows of `docs/DEVOPS_HANDOVER.md` (Patrick's) true: entry points `api.handlers:summary` etc., the environment variables, and IAM (read `artefacts/`, read the ledger, `states:StartSyncExecution` on the ask machine).
- **For Abdul:** explain the eval format, review his JSON, and help him capture the worked examples in `evals/expected/agents/<agent>.json` from real runs.

## Interfaces
| You consume | From | Exact name |
|---|---|---|
| API schema, settings | Patrick | `tools/api_schema.py` *(new)*, `config.get_settings()` (`auth_mode`, `ask_state_machine_arn`) |
| Repository | done | `adapters.repository_from_settings()` |
| KPIs, lookups | done (yours) | `metrics.portfolio_summary`, `open_blockers`, `failing_reconciliations`, `cutover_calendar_conflicts`; `queries.rows_by_citation`, `in_entity_view` |
| Analyst tools, claim validation | done (yours) | `make_analyst_tools(scope, repository)`, `validate_claim(raw_claim, repository, scope, analyst_tools)` |
| Publish functions, fault doubles | Huvison | `flow/publish.py`, `evals/doubles.py` *(new)* |
| Eval inputs | Abdul | `evals/inputs/Qnn.json` *(new)* |

| You produce | For | Exact name |
|---|---|---|
| Handlers | Yaw (ApiStack), Mildred, Clement | `api/handlers.py`: `summary`, `entity`, `rows`, `ask`, `publish`, `approve` |
| Scope builder | every handler | `auth/scope.py` `scope_from_claims` |
| Fixtures | Mildred | `scripts/export_summary.py` → `web/src/app/core/api/fixtures/` |
| Blocker-analyst | Patrick (orchestrator) | `agents/blocker_analyst.py` |
| Eval results | Abdul (EVALS.md), everyone | `evals/results/<date>.json` |

## Dependencies
- **You wait on:**
  - **Patrick's contracts PR** for the schema and settings. Until then, return `portfolio_summary` as-is and add schema validation when it lands.
  - **Huvison's `flow/`** for `/ask` and publish. Until then, stub the entry points and test the Q11 refusal on its own.
  - **Michael's Cognito claims.** Until then, use fake claims in tests.
- **Waiting on you:** Mildred and Clement (real data), Yaw (handler entry points), Patrick (the analyst), Abdul (the runner).

## Your milestones
| When | Milestone |
|---|---|
| D1 12:00 | `auth/scope.py` + the `/summary` handler tested locally |
| D1 16:00 | `/entity`, `/rows` and the `/ask` Q11 refusal; `export_summary.py` committed; the analyst produces a valid E4 claim against a stub |
| D1 18:00 | `/summary` live behind API Gateway (with Yaw); the front end on real data |
| D2 12:00 | Cognito go/no-go: an entity lead is refused another entity, end to end |
| D2 14:00 | Eval runner records all 14 (failures included) |

## Eval questions you own or affect
| Question | What it checks |
|---|---|
| **Q01** | The chain claims |
| **Q02** | Decoy conflict claim |
| **Q03** | E1 clean, zero invented blockers |
| **Q05** | `role_utilisation`: Tester 8 working vs 6 planned, 133.3% |
| **Q06** | Figures equal `metrics.days_to_cutover`: 102 days, 6 behind |
| **Q11** | E4 lead asks about E2 → refused, no ledger rows |
| **Q13** *(target only)* | |
| The runner | Runs them all |

## Definition of done
- [ ] `auth/scope.py` and `api/handlers.py` tested with fake HTTP API v2 events; errors use the contract body.
- [ ] Q11 refusal happens before `start_run` (tested: the ledger stays empty).
- [ ] `/summary` serves the one screen in AWS; the front end uses it.
- [ ] `export_summary.py` fixtures replace the `kpis.json` dependency.
- [ ] The blocker-analyst's claims pass `validate_claim`; prompt locked; `AGENTS.md` row true.
- [ ] `evals/run.py` runs all 14 with one command and writes results with prompt versions and failures.
- [ ] Your `HANDOFF.md` lines.

## Rules and pitfalls specific to you
- **Scope only from token claims** (or the `AUTH_MODE=none` demo user). Never from a request body or query string.
- **No numbers outside `tools/metrics.py`.** A handler that does arithmetic is a bug.
- **No business logic in handlers.** If you need a new figure, add it to `metrics` with a pinned test.
- **The front end sends the ID token** (custom claims are only in the ID token). The authorizer's audience is the app client ID (Yaw).
- **The eval runner reports failures honestly.** A perfect `EVALS.md` is treated as a missing one.

## Getting started
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest           # 140 passed
git switch -c feature/api-summary-and-scope
```
Then give your assistant `06 Workstreams/prompts/linus.txt`.

## Who to ask
| Topic | Person |
|---|---|
| Schema, settings, orchestrator | Patrick |
| Flow, publish, ledger, doubles | Huvison |
| ApiStack, authorizer | Yaw |
| Cognito | Michael |
| Fixtures, front-end types | Mildred |
| Sign-in | Clement |
| Eval inputs | Abdul |

Related: [[Workstreams]], [[Team plan]]
