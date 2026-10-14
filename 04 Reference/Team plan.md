---
date: 2026-10-14
source: repo docs/TEAM_PLAN.md (the repo copy is canonical; regenerate this note from it, never edit it by hand)
synced_from_commit: e8b86c6
tags: [reference, area/team, area/process]
---
# Team plan: 8 engineers, 2 days, a POC plus one target slice

> **Read this first, then `AGENTS.md` and `ARCHITECTURE.md`.** If you're an AI assistant helping a teammate: stay inside that teammate's workstream (§2). Don't change a contract in §3 without the lead's OK. Follow the rules in §6.

## 1. Strategy in four lines
1. **Walking skeleton first.** By **Day 1 18:00** one thin path works end-to-end *in AWS*: dashboard numbers + one question answered with citations. Everything else plugs into it.
2. **POC plus one target slice; the rest is a 90-day roadmap** (D-015). We build the POC (`ARCHITECTURE.md` §3) and one target layer end-to-end: Cognito sign-in with entity scope. Everything else in the target (§3b) is drawn and planned in `docs/ROADMAP.md`, not built. If the slice isn't green by **Day 2 12:00**, switch `AUTH_MODE=none`, demo the rest, and say so in `HANDOFF.md`.
3. **Contracts before code.** The interfaces in §3 are frozen at **Day 1 10:30**. After that, everyone builds against them in parallel, mocking whatever isn't ready.
4. **Half the score is documents.** Pitch deck 20 + business case 20 + spec 10, and the repo's 50 is mostly the markdown files and agent definitions. One owner is fully on the business documents; every workstream writes its own section of the repo docs.

## 2. Workstreams

Four teams: back end (4), front end (2), DevOps (2), and the business documents. Each workstream owns its folders; a change to another workstream's folder goes through its owner.

| # | Workstream | Owner | Owns (folders) | Builds | Done when |
|---|---|---|---|---|---|
| 1 | **Lead: contracts, orchestrator and retriever** | Patrick | `config.py`, the shared core contracts (`tools/models.py`, `tools/ports.py`, `tools/constants.py`, `tools/evidence.py`), the API schema, `agents/orchestrator.py`, `agents/retriever.py`, `agents/prompts/{orchestrator,retriever}.txt`, `scripts/ask.py`, `ARCHITECTURE.md`, `DECISIONS.md`, `README.md`, `docs/` | Freezes the contracts first: API response shapes (`/summary`, `/entity`, `/rows`, `/ask`, `/publish`, `/approve`, error body), the ask-spine step inputs and outputs, new `config.py` settings (`AUTH_MODE`, tables, bucket, state machines, user pool), and the DevOps handover (handlers, environment, IAM, bundling including prompts). Then the orchestrator and retriever on Strands; reviews contract files; merges PRs; runs the clean-deploy check with DevOps; drives the demo | Contracts merged before any handler code; Q07 returns a `PartialAnswer`; the retriever cites rows for Q01; `cdk deploy --all` from clean works twice (D1 18:00, D2 13:00) |
| 2 | **Trust and flow** | Huvison | `agents/critic.py`, `agents/writer.py`, `agents/prompts/{critic,writer}.txt`, `agents/prompt_loader.py`, `adapters/*_ledger.py`, the ask-spine and publish handlers | Writer agent; the `/ask` step handlers (budget check, claims to the ledger, critic per claim, retry guard reading the ledger, writer); `/publish` + `/approve` with the task token and the status-pack write to S3; ledger extensions (rejected records, read methods, `STEP#n`, token totals, task tokens); cost per run from token counts × a price table in code; the Q08/Q09 fault hook; the Guardrail configuration (DevOps deploys it); times a full `/ask` against API Gateway's 29 s limit and picks the fallback | Q08 and Q09 pass; a rejected claim lands in rejected records with all its verdicts; a status pack publishes only after approval; cost per run recorded |
| 3 | **API, identity and the blocker-analyst** | Linus (with Abdul) | `api/`, `auth/` (Python side), `tools/metrics.py`, `tools/queries.py`, `tools/agent_tools.py`, `tools/claims.py`, `agents/blocker_analyst.py`, `agents/prompts/blocker_analyst.txt`, `scripts/export_summary.py`, the eval runner | `/summary`, `/entity/{id}`, `/rows` handlers on `metrics`; scope built from the token (`AUTH_MODE=none` fallback); the `/ask` scope refusal before a run starts (Q11) and the error body; `export_summary.py` so the front end's fixtures come from the real summary; the blocker-analyst (figures from `make_analyst_tools`, validated by `tools/claims.py`); the eval runner on Day 2 (records prompt versions, writes failures). Main back-end contact for DevOps | `/summary` serves the one screen; an entity lead is refused another entity; Q01, Q02 and Q06 claims pass `tools/claims.py`; evals run with one command |
| 4 | **Evals, Cognito and documentation** | Abdul (with Linus) | `evals/inputs/`, `evals/expected/`, `EVALS.md` results, `COST.md`, `HANDOFF.md`, `docs/architecture-target-*.png`, the API request collection | The 14 eval questions as JSON inputs with expected outputs; API request collection and example responses; Cognito groups (cfo, sponsor, delivery_lead, entity_lead), `tenant_id`/`entity_ids` claims and test users per role (with DevOps); Bedrock eu-west-1 price research for `COST.md`; worked examples per agent captured from real runs; the EVALS results and "what still fails"; target diagram v2; DEMO and HANDOFF lines; wording review of the agent prompts | Q01–Q14 inputs committed; every route has an example response; test users exist per role; `COST.md` and EVALS results filled honestly |
| 5 | **DevOps** | Michael, Yaw | `infra/` (all CDK stacks and `infra/app.py`), `Jenkinsfile` | Data (S3 artefacts + upload of `demo/data/erp/output/migration`), API Gateway + JWT authorizer, Lambdas, Step Functions definitions (from the step I/O contract), AgentCore Runtime (or the Lambda fallback), DynamoDB ledger, Guardrail, Cognito, web hosting (S3 + CloudFront), least-privilege roles, logs and traces; CI | Every stack deploys from a clean account; CI green on every PR |
| 6 | **Portal front end** | Mildred, Clement | `web/` | Angular 22 (D-020): the one screen, ask panel with clickable citations, "could not verify" list, publish + approve screens, role-based views; types from the API schema | All five KPIs on one screen from `/summary`; clicking a number shows its source rows |
| 7 | **Business case & pitch** | to be confirmed | `business/` (deck, business case, product spec) | Validates with the problem owner and oversight; named executive (CFO); baseline vs target numbers with stated assumptions; reuse across portfolio companies; spec (must-dos, priorities, user stories, success measures); 10-min pitch | All three documents reviewed by the lead by D2 15:00 |

**Pairing:** Patrick + Huvison (the agent contract and the ledger); Linus + Abdul (API, identity, evals); Linus + Mildred/Clement (the API schema and fixtures); Huvison + Michael/Yaw (Step Functions, Guardrail, AgentCore); Abdul + DevOps (Cognito users). The business-case owner interviews the others for the "why it's agentic" and cost numbers.

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
| **D1 09:00–09:30** | Kick-off: read this, `AGENTS.md`, `ARCHITECTURE.md`; confirm workstreams | |
| **D1 09:30–10:30** | Each workstream drafts its part of the contracts (the lead freezes them); the business-case owner books 15 min with the problem owner | **10:30 contracts frozen** (lead) |
| **D1 10:30–12:00** | Abdul (with Huvison): the 14 eval questions as runnable inputs with expected outputs. DevOps: CDK stack skeletons, deployable empty | Every stack deploys empty |
| **D1 12:00–16:00** | Tools before agents: everyone builds and unit-tests their deterministic parts against mocks of the others | `uv run --locked pytest` green; each stack deploys |
| **D1 16:00–18:00** | Integrate the **walking skeleton**: portal → `/summary` (CSV) and `/ask` → orchestrator → retriever → ledger → writer (critic stubbed to pass) | **18:00 skeleton live in AWS**; first clean deploy check |
| D1 evening | Optional: the business-case owner drafts the business case; Linus + Abdul draft `docs/ROADMAP.md` and the target diagram v2; lead updates docs | |
| **D2 09:00–12:00** | Cognito slice end-to-end (Linus + Abdul with the front end and DevOps); real critic + retry guard; publish flow. Evals after each merge | **12:00 go/no-go for the Cognito slice**: green stays on, otherwise `AUTH_MODE=none` and `HANDOFF.md` says so |
| **D2 12:00–14:00** | Guardrails on, budget ceiling, human approval end-to-end; worked example per agent committed | |
| **D2 14:00** | **CODE FREEZE** | |
| **D2 14:00–16:00** | Each workstream writes its docs (§6); evals recorded with failures; COST.md measured; ROADMAP final; clean deploy check #2 | Lead + the business-case owner review the documents at 15:00 |
| **D2 16:00–17:00** | Rehearse twice from cold, on the clock; record backup video | |

**Stand-ups:** 09:00, 13:00, 17:00 each day, 10 minutes. Each workstream says: done, next, blocked, contract changes needed.

## 5. Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Cognito slice slips (JWT authorizer, claims) | Medium | Start D1 morning; `AUTH_MODE=none` fallback; the scope filter in code works either way |
| The roadmap reads as vague promises | Medium | Phases with client dependencies, top-3 risks and go/no-go criteria (`docs/ROADMAP.md`); numbers marked *proposed* until confirmed with the problem owner |
| AgentCore Runtime deployment issues | Medium | Agents also runnable as a Lambda (same Strands code) as a fallback |
| Clean-account deploy fails (hard gate) | Medium | Lead deploys with a fresh stack prefix twice; no console-clicked resources |
| Integration chaos with 8 people | High | Folder ownership, frozen contracts, small PRs, lead merges |
| Docs left late (half the score) | High | 14:00 freeze; the business-case owner full-time on business docs; each workstream owns its rows |
| Haiku access still pending | Low | Nova Lite for the retriever |

## 6. Working rules (for humans and their AI assistants)
- **Getting started:** install uv once (`curl -LsSf https://astral.sh/uv/install.sh | sh`), then `uv sync` (creates `.venv` with the exact locked versions) and `uv run --locked pytest` from the repo root (`--locked` refuses a `uv.lock` that's out of date instead of silently rewriting it; run `uv lock` deliberately when you change dependencies) (coverage on by default; the suite must stay green and coverage must not drop). `AWS_PROFILE=hackathon`, `eu-west-1`.
- **Dependencies:** add with `uv add <package>` (or `uv add --dev <package>` for test-only tools) and commit `pyproject.toml` **and** `uv.lock` together. Never edit `uv.lock` by hand; there are no requirements files (a test fails if they come back).
- **Front end (`web/`):** a separate app with its own tooling (D-020). Node 22 (`web/.nvmrc`), yarn 1.22.22 via `corepack enable`, and the read-only npm token in your **home** `~/.npmrc` (lines in `web/README.md`; never in the repo). Then `cd web && yarn install --frozen-lockfile && yarn start`; `yarn test` runs its unit tests. One lock file: `web/yarn.lock`. No front-end files at the repo root and no Python under `web/`.
- **How we build a feature (superpowers):** brainstorm → written spec → written plan → test-first implementation (red, then green) → review of the whole branch → PR. Specs and plans live in `docs/superpowers/` (local, gitignored); the decisions they lead to go in `DECISIONS.md`. Small fixes skip the spec but still go test-first.
- **Security findings:** confirm the finding against the code, reproduce it with a failing test, fix it, check sibling modules for the same gap, and record a `DECISIONS.md` entry. Never weaken a security rule (scope gate, create-once ledger, fail-closed critic, data escaping) to make a test pass.
- **Hexagonal rule:** `tools/` is the core: no boto3, no Strands, no `adapters` imports (`tests/test_architecture.py` fails the build). AWS code goes in `adapters/` behind a port; agents call data only through `tools/agent_tools.py`.
- **Stay in your folders.** Need something from another workstream? Mock it against the contract and tell them.
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
- **Your docs:** Patrick, Huvison and Linus own their agents' `AGENTS.md` rows; every workstream adds its `DECISIONS.md` entries and its real/faked/breaks-first lines to `HANDOFF.md`; Abdul owns the `EVALS.md` results and `COST.md`; the front end and the lead own `DEMO.md`.
- **AI assistants:** read this file, `AGENTS.md` and `ARCHITECTURE.md` before writing code, and use the superpowers skills (brainstorming, writing-plans, test-driven-development); don't edit another workstream's folder or a §3 contract; run `uv run --locked pytest` before every commit.
