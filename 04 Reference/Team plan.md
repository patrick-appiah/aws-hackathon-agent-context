---
date: 2026-10-14
source: repo docs/TEAM_PLAN.md (the repo copy is canonical; regenerate this note from it, never edit it by hand)
synced_from_commit: 113cc18
tags: [reference, area/team, area/process]
---
# Team plan: 8 engineers, 2 days, a POC plus one target slice

> **Read this first, then `AGENTS.md` and `ARCHITECTURE.md`.** If you're an AI assistant helping a teammate: stay inside that teammate's seat (§2). Don't change a contract in §3 without the lead's OK. Follow the rules in §6.

## 1. Strategy in four lines
1. **Walking skeleton first.** By **Day 1 18:00** one thin path works end-to-end *in AWS*: dashboard numbers + one question answered with citations. Everything else plugs into it.
2. **POC plus one target slice; the rest is a 90-day roadmap** (D-015). We build the POC (`ARCHITECTURE.md` §3) and one target layer end-to-end: Cognito sign-in with entity scope. Everything else in the target (§3b) is drawn and planned in `docs/ROADMAP.md`, not built. If the slice isn't green by **Day 2 12:00**, switch `AUTH_MODE=none`, demo the rest, and say so in `HANDOFF.md`.
3. **Contracts before code.** The interfaces in §3 are frozen at **Day 1 10:30**. After that, everyone builds against them in parallel, mocking whatever isn't ready.
4. **Half the score is documents.** Pitch deck 20 + business case 20 + spec 10, and the repo's 50 is mostly the markdown files and agent definitions. One seat is fully on the business documents; every seat writes its own section of the repo docs.

## 2. Seats

| # | Seat | Owns (folders) | Builds | Done when |
|---|---|---|---|---|
| 1 | **Lead / integrator** | `infra/app.py`, `config.py`, the shared core contracts (`tools/models.py`, `tools/ports.py`, `tools/constants.py`, `tools/evidence.py`), `ARCHITECTURE.md`, `DECISIONS.md`, `README.md`, `docs/` | Freezes contracts; reviews and merges PRs; runs the clean-account deploy check; stand-ups; drives the demo | `cdk deploy --all` from clean works twice (D1 18:00, D2 13:00); README runs in 5 commands |
| 2 | **ERP-layer dataset (generator, planted scenarios), CSV adapter, evals and worked examples** | `scripts/`, `demo/data/erp/`, `adapters/csv_repo.py`, `evals/`, `EVALS.md`, `infra/data_stack.py` | S3 artefacts bucket + upload of the synthetic data; the 14 eval questions as runnable inputs with expected outputs; the eval runner (records prompt versions); one worked example per agent in `evals/expected/` | `evals` run with one command and write results, failures included; every agent has a committed worked example |
| 3 | **KPI service, API, cost & roadmap** | `tools/metrics.py`, `tools/queries.py`, `api/`, `COST.md`, `docs/ROADMAP.md` | KPI Lambda + API Gateway routes; scope filtering; cost per question measured from the ledger, at pilot and full scale; the 90-day roadmap with phases, client dependencies, top-3 risks and go/no-go criteria | `/summary` serves the one screen; `COST.md` has measured numbers; `ROADMAP.md` reviewed by the lead and seat 8 |
| 4 | **Identity slice & target design** | `auth/`, `infra/auth_stack.py`, `docs/architecture-target-*.png` | Cognito user pool + groups (cfo, sponsor, delivery_lead, entity_lead) with `tenant_id`/`entity_ids` claims; API Gateway JWT authorizer; scope built from the token for every request; the target architecture diagram v2 (Verified Permissions, Lake Formation, connectors, CloudTrail) matching `ARCHITECTURE.md` §3b | Entity lead for E4 is refused E2 (EVALS Q11); CFO sees all; target diagram v2 committed |
| 5 | **Agents: plan & evidence** | `agents/orchestrator.py`, `agents/retriever.py`, `agents/blocker_analyst.py`, `tools/agent_tools.py`, `tools/claims.py`, `infra/agent_stack.py`, `agents/prompts/{orchestrator,retriever,blocker_analyst}.txt` | Strands agents on AgentCore Runtime; retriever and analyst tools wired to `tools/`; scope-aware tool calls | Q01 (what blocks E4?) returns claims with correct citations in the ledger |
| 6 | **Trust & flow** | `agents/critic.py`, `agents/writer.py`, `adapters/*_ledger.py`, `infra/flow_stack.py`, `infra/guardrail_stack.py`, `agents/prompts/{critic,writer}.txt`, `agents/prompt_loader.py` | DynamoDB run ledger + rejected records; Step Functions Express ask spine (budget check → orchestrator → critic per claim → retry `Choice` reading the ledger → writer); Standard publish + `waitForTaskToken`; Bedrock Guardrail; budget ceiling | Critic rejects the DEF-0398 decoy live; Q09 hits the retry limit and lands in rejected records; publish waits for approval |
| 7 | **Portal front end** | `web/`, `infra/web_stack.py` | React/Vite on S3 + CloudFront; Cognito sign-in; the one screen (source → target, timeline, capacity, % complete); ask panel with clickable citations; "could not verify" list; publish + approve screens; role-based views | All five KPIs on one screen; clicking a number shows its source rows |
| 8 | **Business case & pitch** | `business/` (deck, business case, product spec) | Validates with the problem owner and oversight; named executive (CFO); baseline vs target numbers with stated assumptions; reuse across portfolio companies; spec (must-dos, priorities, user stories, success measures); 10-min pitch | All three documents reviewed by the lead by D2 15:00 |

**Pairing:** seats 5 + 6 sit together (they share the ledger and the agent contract); 2 + 6 (evals ↔ critic); 3 + 8 (cost and roadmap ↔ business case); 4 + 7 (sign-in ↔ portal). Seat 8 interviews the others for the "why it's agentic" and cost numbers.

## 3. Contracts (frozen D1 10:30, changes only via the lead)

**Scope** (from JWT claims; passed in every request and tool call):
```json
{"user_id": "u-123", "role": "cfo|sponsor|delivery_lead|entity_lead", "tenant_id": "t-01", "entity_ids": ["E4"]}
```
`entity_ids: ["*"]` means all entities of the tenant.

**Data:** POC: `s3://<bucket>/artefacts/<artefact>.csv` plus `programme.json`, exactly as produced in `demo/data/erp/output/migration/` by `demo/data/erp/generate.py` (D-019). Target (roadmap): `artefacts/tenant=<id>/<artefact>/entity=<id>/`, Glue table names = artefact names.

| Artefact | Row ID (what a citation's `row_id` is) | Used for |
|---|---|---|
| `entities` | `entity_id` | Entity names, source tier, target company code |
| `object_inventory` | `{entity_id}#{object_id}` | Records in scope |
| `load_cycles` | `cycle_id` | Which cycles are TEST, their order |
| `load_runs` | `run_id` | Records sent per load |
| `load_errors` | `error_id` | Record-level failures (agent evidence) |
| `reconciliation_results` | `recon_id` | Records matched, PASS/FAIL |
| `defect_log` | `defect_id` | Blockers, causes, linked rules |
| `workplan` | `task_id` | Cutover dates, blocked tasks |
| `cutover_runbook` | `{entity_id}#{step_id}` | Prerequisites, unowned steps |
| `team_roster` | `{month}#{person_id}` | Capacity, effort |
| `rate_card` | `role` | Effort cost |
| `field_mappings` | `{entity_id}#{source_table}#{source_field}` | The rule behind a load error |
| `value_mappings` | `{entity_id}#{mapping}#{legacy_value}` | Code translations |
| `calendar` | `window_id` | Close and holiday windows |

`programme.json`: `programme_name`, `description`, `as_of_date`, `recon_target_pct`, `target_platform`, `currency`, `data_notice`. Column lists: the CSV headers in `demo/data/erp/output/migration/`.

**Citation:** `{"artefact": "defect_log", "row_id": "DEF-0412"}`. Every claim, bullet and number on screen carries one or more.

**API (API Gateway, JWT required when `AUTH_MODE=cognito`):**

| Route | Request | Response |
|---|---|---|
| `GET /summary` | scope from token | `metrics.portfolio_summary()` JSON, scope-filtered |
| `GET /entity/{id}` | scope | entity KPIs + evidence |
| `GET /rows?cite=artefact:row_id,...` | scope | the cited rows (powers "click a number") |
| `POST /ask` | `{"entity_id": "E4", "question": "..."}` | `{"run_id", "answer": {"headline", "bullets": [{"text", "citations": []}]}, "rejected": [{"claim", "reason"}], "cost_usd", "partial": bool}` |
| `POST /publish` | `{"run_id"}` | `{"execution_arn", "status": "awaiting_approval"}` |
| `POST /approve` | `{"execution_arn", "decision": "approve\|send_back", "note"}` | `{"status"}` |

**Agents:** schemas exactly as in `AGENTS.md` and `tools/models.py`. Model IDs only `eu.*`.

**Ports (`tools/ports.py`):** `ArtefactRepository` and `Ledger`. Every adapter must pass the same tests as the reference adapter (`CsvRepository`, `InMemoryLedger`). Agents reach data **only** through `tools/agent_tools.py` factories, built per request with the user's scope bound in.

**Run ledger (DynamoDB):** `pk=run_id`, `sk=RUN | CLAIM#<id> | STEP#<n>`; claim items hold `claim`, `evidence[]`, `verdicts[]`, `attempts`, `status`; the RUN item holds `scope`, `budget_usd`, `cost_usd`, `tokens_in`, `tokens_out`.

**Switches in the POC:**

| Flag | Values | Fallback |
|---|---|---|
| `AUTH_MODE` | `cognito` / `none` | `none` = demo user with CFO scope (only if the Cognito slice slips) |
| `LEDGER_BACKEND` | `dynamo` / `memory` | `memory` = in-process ledger (local runs and tests only; lost on restart) |

The target's switches (`AUTHZ_MODE`, `ARTEFACT_BACKEND`, `LF_FILTERS`, `SOURCES`) belong to the roadmap, not the two days.
Switches and every other deployment setting are read in one place, `config.py` (`get_settings()`); nothing else reads environment variables.

## 4. Schedule

| When | Everyone | Milestone |
|---|---|---|
| **D1 09:00–09:30** | Kick-off: read this, `AGENTS.md`, `ARCHITECTURE.md`; confirm seats | |
| **D1 09:30–10:30** | Each seat drafts its part of the contracts; seat 8 books 15 min with the problem owner | **10:30 contracts frozen** (lead) |
| **D1 10:30–12:00** | Seats 2 + 6: the 14 eval questions as runnable inputs with expected outputs. Others: CDK stack skeletons, deployable empty | Every stack deploys empty |
| **D1 12:00–16:00** | Tools before agents: everyone builds and unit-tests their deterministic parts against mocks of the others | `uv run --locked pytest` green; each stack deploys |
| **D1 16:00–18:00** | Integrate the **walking skeleton**: portal → `/summary` (CSV) and `/ask` → orchestrator → retriever → ledger → writer (critic stubbed to pass) | **18:00 skeleton live in AWS**; first clean deploy check |
| D1 evening | Optional: seat 8 drafts the business case; seats 3 + 4 draft `docs/ROADMAP.md` and the target diagram v2; lead updates docs | |
| **D2 09:00–12:00** | Cognito slice end-to-end (seats 4 + 7); real critic + retry guard; publish flow. Evals after each merge | **12:00 go/no-go for the Cognito slice**: green stays on, otherwise `AUTH_MODE=none` and `HANDOFF.md` says so |
| **D2 12:00–14:00** | Guardrails on, budget ceiling, human approval end-to-end; worked example per agent committed | |
| **D2 14:00** | **CODE FREEZE** | |
| **D2 14:00–16:00** | Each seat writes its docs (§6); evals recorded with failures; COST.md measured; ROADMAP final; clean deploy check #2 | Lead + seat 8 review the documents at 15:00 |
| **D2 16:00–17:00** | Rehearse twice from cold, on the clock; record backup video | |

**Stand-ups:** 09:00, 13:00, 17:00 each day, 10 minutes. Each seat says: done, next, blocked, contract changes needed.

## 5. Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Cognito slice slips (JWT authorizer, claims) | Medium | Start D1 morning; `AUTH_MODE=none` fallback; the scope filter in code works either way |
| The roadmap reads as vague promises | Medium | Phases with client dependencies, top-3 risks and go/no-go criteria (`docs/ROADMAP.md`); numbers marked *proposed* until confirmed with the problem owner |
| AgentCore Runtime deployment issues | Medium | Agents also runnable as a Lambda (same Strands code) as a fallback |
| Clean-account deploy fails (hard gate) | Medium | Lead deploys with a fresh stack prefix twice; no console-clicked resources |
| Integration chaos with 8 people | High | Folder ownership, frozen contracts, small PRs, lead merges |
| Docs left late (half the score) | High | 14:00 freeze; seat 8 full-time on business docs; each seat owns its rows |
| Haiku access still pending | Low | Nova Lite for the retriever |

## 6. Working rules (for humans and their AI assistants)
- **Getting started:** install uv once (`curl -LsSf https://astral.sh/uv/install.sh | sh`), then `uv sync` (creates `.venv` with the exact locked versions) and `uv run --locked pytest` from the repo root (`--locked` refuses a `uv.lock` that's out of date instead of silently rewriting it; run `uv lock` deliberately when you change dependencies) (coverage on by default; the suite must stay green and coverage must not drop). `AWS_PROFILE=hackathon`, `eu-west-1`.
- **Dependencies:** add with `uv add <package>` (or `uv add --dev <package>` for test-only tools) and commit `pyproject.toml` **and** `uv.lock` together. Never edit `uv.lock` by hand; there are no requirements files (a test fails if they come back).
- **Front end (`web/`):** a separate app with its own tooling (D-020). Node 22 (`web/.nvmrc`), yarn 1.22.22 via `corepack enable`, and the read-only npm token in your **home** `~/.npmrc` (lines in `web/README.md`; never in the repo). Then `cd web && yarn install --frozen-lockfile && yarn start`; `yarn test` runs its unit tests. One lock file: `web/yarn.lock`. No front-end files at the repo root and no Python under `web/`.
- **How we build a feature (superpowers):** brainstorm → written spec → written plan → test-first implementation (red, then green) → review of the whole branch → PR. Specs and plans live in `docs/superpowers/` (local, gitignored); the decisions they lead to go in `DECISIONS.md`. Small fixes skip the spec but still go test-first.
- **Security findings:** confirm the finding against the code, reproduce it with a failing test, fix it, check sibling modules for the same gap, and record a `DECISIONS.md` entry. Never weaken a security rule (scope gate, create-once ledger, fail-closed critic, data escaping) to make a test pass.
- **Hexagonal rule:** `tools/` is the core: no boto3, no Strands, no `adapters` imports (`tests/test_architecture.py` fails the build). AWS code goes in `adapters/` behind a port; agents call data only through `tools/agent_tools.py`.
- **Stay in your folders.** Need something from another seat? Mock it against the contract and tell them.
- **Commit small and often** with clear messages; history is graded. Branch `<type>/<short-topic>` **from `develop`**, where type is `feature/`, `fix/`, `chore/`, `docs/`, `refactor/` or `test/` (e.g. `feature/blocker-analyst`, `fix/ledger-budget`), PR **to `develop`**, the lead merges. `develop` is the integration branch; `main` only receives reviewed releases from `develop` (e.g. the demo and submission builds), via a PR the lead opens.
- **Clean code, enforced by tests where possible:**
  - **DRY:** a rule or check lives in one place (e.g. `tools/evidence.py` is the only citation and scope gate).
  - **No magic numbers:** domain thresholds in `tools/constants.py`; deployment settings (region, model IDs, table names, budgets) in `config.py`, read via `get_settings()`. Nothing else reads environment variables.
  - **Nothing hardcoded** that differs between laptop, sandbox and production.
  - **Descriptive names, never single characters** (`row`, not `r`). `tests/test_code_style.py` fails the build otherwise.
- **Review per PR, not per edit:** before the lead merges, run the code-simplifier / code-review pass on the PR's diff and `uv run --locked pytest` with coverage.
- **Changing a prompt:** edit `agents/prompts/<agent>.txt` → bump `version` (PATCH wording, MINOR new rule, MAJOR output format) and `updated` → run `uv run python scripts/lock_prompts.py` → `uv run --locked pytest` (which runs `lock_prompts.py --check`, never writing) → PR showing the prompt and lock diff. Never put prompt text in Python (`tests/test_code_style.py` fails the build).
- **Every deterministic function gets a unit test in `tests/`, mirroring the code** (`tests/tools/…` for `tools/…`; never next to the code, a guard test fails the build). Every agent gets one worked example in `evals/expected/<agent>.json`.
- **No real names or data**, `eu-west-1` only, `eu.*` models only, no secrets in code (SSM/Secrets Manager).
- **No console-only resources.** If it isn't in CDK, it doesn't exist (clean-deploy gate).
- **Your docs:** seats 5 and 6 own their `AGENTS.md` rows; every seat adds its `DECISIONS.md` entries and its real/faked/breaks-first lines to `HANDOFF.md`; seat 3 owns `EVALS.md` and `COST.md`; seat 7 and the lead own `DEMO.md`.
- **AI assistants:** read this file, `AGENTS.md` and `ARCHITECTURE.md` before writing code, and use the superpowers skills (brainstorming, writing-plans, test-driven-development); don't edit another seat's folder or a §3 contract; run `uv run --locked pytest` before every commit.
