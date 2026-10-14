---
tags: [moc, area/team]
updated: 2026-10-14
---
# Workstreams: who builds what, and how it fits together

**Read this note first, then your own note below, then the repo docs it points to.** Every person has a personal brief with what to build, the exact interfaces, who you depend on, how to start and what "done" means. Each brief also has a starter prompt for your AI assistant: a `.txt` file in `06 Workstreams/prompts/`. Paste it as your assistant's first message.

| Person | Workstream | Brief | Assistant prompt |
|---|---|---|---|
| Patrick (lead) | Contracts, orchestrator, retriever, integration | [[Patrick - contracts, orchestrator, retriever]] | `prompts/patrick.txt` |
| Huvison | Trust and flow (writer, ask spine, publish, ledger, cost, guardrail) | [[Huvison - trust and flow]] | `prompts/huvison.txt` |
| Linus | API, identity, blocker-analyst, eval runner | [[Linus - API, identity, blocker-analyst]] | `prompts/linus.txt` |
| Abdul | Evals, Cognito users, cost and docs (pairs with Linus) | [[Abdul - evals, Cognito, docs]] | `prompts/abdul.txt` |
| Michael | DevOps: CI, data, ledger, guardrail, Cognito, web hosting, observability | [[Michael - DevOps]] | `prompts/michael.txt` |
| Yaw | DevOps: API, Lambdas, Step Functions, AgentCore, IAM | [[Yaw - DevOps]] | `prompts/yaw.txt` |
| Mildred | Front end: data and the one screen | [[Mildred - front end]] | `prompts/mildred.txt` |
| Clement | Front end: sign-in, ask, publish and approve | [[Clement - front end]] | `prompts/clement.txt` |
| Patrick + Michael | Business case, product spec and pitch deck (`business/`): **half the score** | [[Business case and pitch]] | `prompts/business.txt` |

The DevOps split between Michael and Yaw, and the front-end split between Mildred and Clement, are **proposals**: agree them in your pair at the first stand-up and tell Patrick. The canonical list is `docs/TEAM_PLAN.md` §2 in the repo. If this note and the repo disagree, the repo wins.

## 1. The project in five lines
- **Problem (the brief):** "Show the client where the migration actually is." A mid-market industrial group is consolidating four legacy ERPs onto one platform. The sponsor, the CFO and the delivery lead get a weeks-old deck, and every "what is blocking cutover?" costs a consultant two days.
- **What we build:** an **ERP Migration Progress Portal**:
  1. **One screen**: source systems, target, timeline, capacity and % complete, with every number computed from the migration's own artefacts (`tools/metrics.py`), never typed in.
  2. **One agent loop that genuinely runs**: "What is blocking cutover for entity 4?", answered in seconds, with every claim citing the rows it came from and a **critic** that rejects what the evidence doesn't support.
- **Owners:** problem owner Vanessa Addo, oversight Joseph Akayesi (AmaliTech Ventures).
- **Scope (D-015):** the POC plus **one** target slice, Cognito sign-in with entity scope. Everything else in the target architecture is a 90-day roadmap (`docs/ROADMAP.md`).
- **Brief rule:** "the back end may be stubbed; the agent layer may not."

## 2. Architecture you all build into (POC)
```
 user (CFO · sponsor · delivery lead · entity lead)
   │
   ▼
 Portal (Angular, web/)  ── S3 + CloudFront ................................ Mildred, Clement / Michael
   │ sign in (Cognito: groups = roles, claims tenant_id + entity_ids) ........ Abdul, Linus / Michael
   │ JWT
   ▼
 API Gateway + JWT authorizer ............................................. Yaw
   ├─ GET /summary, /entity/{id}, /rows ─▶ KPI Lambda (`infra/functions/api.py` *(new)*) ─▶ tools/metrics.py ─▶ S3 artefacts .. Linus / Michael
   ├─ POST /ask ─▶ Step Functions Express "ask spine" ........................ Huvison (handlers) / Yaw (definition)
   │      budget check ─▶ orchestrator ─▶ retriever / blocker-analyst ─▶ run ledger (DynamoDB)
   │      ─▶ citation pre-check (code) ─▶ critic (blind) ─▶ retry guard (Choice, reads ledger; < 2)
   │      ─▶ writer ─▶ answer with citations + prompt versions; failures ─▶ rejected records
   │      (orchestrator, retriever: Patrick · blocker-analyst: Linus · critic, writer, ledger: Huvison)
   └─ POST /publish, /approve ─▶ Step Functions Standard + waitForTaskToken ─▶ S3 status-packs/ .. Huvison / Yaw
 Bedrock (eu.* only) through a Guardrail (PII + prompt attack) on every model call ........ Huvison / Michael
 Agents hosted on AgentCore Runtime (Strands); same code runnable as a Lambda (fallback) .. Patrick / Yaw
```
- **Diagram and service choices:** `ARCHITECTURE.md` §3 (POC) and §3b (target).
- **Fixed flow vs agent:** `ARCHITECTURE.md` §2. Only the planning, the retrieval and the judging are agents; everything else is code or Step Functions.
- **The agent table:** `AGENTS.md`, one row per agent with schemas, tools, guardrail and failure mode. It's the contract for agent work.

## 3. The code you build on (already done and tested)
**160 tests, 95% coverage** (including the eval runner). Run `uv run --locked pytest` from the repo root.

| Module | What it gives you |
|---|---|
| `tools/constants.py` | The 14 artefact names (`ArtefactName`), row-ID rules, status values, thresholds. No magic values anywhere else |
| `tools/models.py` | `Scope` (`allows`, `require`), `Citation`, `Row`, `Figure`, `BlockerClaim`, `Verdict` (`Verdict.rejection(...)`), `validate_entity_id`, `validate_identifier` |
| `tools/ports.py` | `ArtefactRepository` (`load(artefact)`, `programme()`) and `Ledger` (`start_run`, `put_claim`, `revise_claim`, `record_verdict`, `attempts`, `claim`, `add_cost`, `budget_remaining`). Create-once rule |
| `tools/metrics.py` | **Every number on screen:** `portfolio_summary(repository, scope)`, `records_reconciled`, `recon_pass_rate`, `open_blockers`, `days_to_cutover`, `final_cutover`, `capacity_used`, `effort_cost`, `entity_status`, `failing_reconciliations`, `cutover_calendar_conflicts` |
| `tools/queries.py` | Lookups and citations: `cite`, `row_id`, `rows_by_citation`, `latest_reconciliations`, `defects_for_object`, `load_errors_for_object`, `mapping_for_field`, `runbook_for_entity`, `in_entity_view` |
| `tools/agent_tools.py` | **The agents' only door to data:** `make_retriever_tools(scope, repository)` (9 tools) and `make_analyst_tools(scope, repository)` (5 tools); `as_strands_tools(...)`. Scope is bound per request and is **never** a tool argument |
| `tools/claims.py` | `validate_claim(raw_claim, repository, scope, analyst_tools)`: shape, citations, scope, and every figure recomputed |
| `tools/evidence.py` | The one citation and scope gate (`check_citations`) |
| `agents/critic.py` | `judge(claim, repository, scope, agent=None)`, `precheck`, `build_input`; fails closed |
| `agents/prompt_loader.py` | `load_prompt(agent)` returns a `Prompt` with `.text`, `.version`, `.content_hash`, `.provenance()`; refuses unlocked prompts |
| `adapters/` | `CsvRepository` (local or S3), `InMemoryLedger`, `DynamoLedger` (moto-tested), `AthenaRepository` (roadmap stub) |
| `config.py` | **The only place settings live:** region `eu-west-1`, model IDs (`eu.*`), table names, backends, guardrail, `MAX_CLAIM_ATTEMPTS=2`, `RUN_BUDGET_USD=0.50`; environment overrides |

**Data (D-019):** `demo/data/erp/output/migration/`, 14 artefacts. Row IDs are listed in `docs/TEAM_PLAN.md` §3 (e.g. `E4#RB-014`).

The planted scenarios every demo and eval uses:
- **E4 chain:** runbook step `E4#RB-010` → `RC-C3-E4-customers` FAIL 91.2% → 212 load errors → `DEF-0412` (open, 18 days) → mapping rule `E4#CUSMST#TAXNO`.
- **Decoy:** `DEF-0398` is Closed, but customers still fail.
- **Prompt-injection probe:** `DEF-0462` (E3).
- **Calendar clash:** E4's cutover on 2027-01-23 falls inside the year-end close `CAL-004`.
- **Clean entity:** E1 (live).

Dashboard figures: 18,420 of 31,700 records reconciled (58.1%); C3 pass rate 96.4% (C2 94.8%); 7 blockers, oldest 18 days; E4 final cutover 2027-01-23, 102 days away, 6 behind plan; capacity 38 of 37 people.

## 4. Integration points: the contracts between you
**Patrick freezes these first, in one PR, before anyone writes handler code.** Until it merges, build against the current types in `tools/models.py` and the fakes. Change a contract only through Patrick.

| Contract | Produced by | Consumed by | Lives in |
|---|---|---|---|
| API response schema (`/summary`, `/entity/{id}`, `/rows`, `/ask`, `/publish`, `/approve`, error body), exported as JSON Schema | Patrick (shapes), Linus (handlers) | Mildred, Clement (TypeScript types) | `tools/api_schema.py` *(new)* + `scripts/export_api_schema.py` *(new)* (both new) |
| Ask-spine step inputs and outputs (`Question`, `Plan`, `RetrieveRequest`, `Evidence`, claims, `Verdict`, writer input, `Answer`, `PartialAnswer`), each agent output carrying `usage{model_id, tokens_in, tokens_out}` for cost | Patrick | Huvison (handlers), Yaw (state machine), Patrick and Linus (agents) | `tools/models.py` |
| Agent tools | done | Patrick, Linus | `tools/agent_tools.py` |
| Ledger port and its extensions (rejected records, read methods, steps, tokens, task tokens) | Huvison | Huvison, Linus (eval runner), Yaw (IAM) | `tools/ports.py`, `adapters/*_ledger.py` |
| Lambda handover: entry points, environment variables, IAM needs, bundling (`uv export`, prompts included) | Patrick, Linus, Huvison | Yaw, Michael | `docs/DEVOPS_HANDOVER.md` *(new)* (new) |
| Token claims → `Scope` | Linus (code), Abdul + Michael (Cognito) | every handler | `infra/functions/scope.py` *(new)* |
| Eval runner, inputs and expectations (**built, PR #16**) | Michael (runner), Abdul (review, Q10, write-up) | the local asker (Huvison, `infra/functions/local.py` *(new)*), the deployed-API asker (Linus) | `evals/run.py`, `evals/inputs/`, `evals/expected/` (worked examples per agent in `evals/expected/<agent>.json` *(new)*) |
| Budget check (one function, two callers: the `check_budget` state and the orchestrator before each re-plan) | Huvison | Patrick, Yaw | `tools/budget.py` *(new)* (new) |

## 5. Timeline (`docs/TEAM_PLAN.md` §4)
- **D1 09:00:** kick-off. Everyone reads this note, their own note, `AGENTS.md` and `ARCHITECTURE.md`.
- **D1 10:30:** contracts frozen (Patrick).
- **D1 10:30–12:00: the eval set first.** The guideline calls it the single highest-leverage ninety minutes. It's already built (PR #16): Abdul reviews it against `EVALS.md`. DevOps gets **every stack deploying empty**.
- **D1 12:00–16:00:** tools before agents. Each workstream builds and unit-tests against mocks.
- **D1 16:00–18:00:** integrate the walking skeleton: portal → `/summary`, and `/ask` → orchestrator → retriever → ledger → writer, with the critic stubbed to pass. **It must be live in AWS by 18:00**, and that's the first clean-deploy check.
- **D2 09:00–12:00:** the Cognito slice end to end, the real critic and retry guard, the publish flow. **12:00 go/no-go for Cognito.**
- **D2 12:00–14:00:** guardrails, the budget ceiling, approval end to end, and a worked example per agent. **D2 14:00 code freeze.**
- **D2 14:00–16:00:** docs, evals recorded with their failures, COST.md measured, ROADMAP final, the second clean-deploy check. **16:00–17:00:** rehearse twice and record the backup video.
- **Stand-ups:** 09:00, 13:00 and 17:00, 10 minutes each. Say what's done, what's next, what's blocked, and any contract change you need.

## 6. What's graded (so you know what matters)
**Hard gates:**
1. Deploys from a clean account.
2. Evals recorded honestly.
3. Human approval before the only write.
4. **No real client data anywhere** in the repo, the logs or the prompts.
5. Every agent defined in `AGENTS.md`.

Separately, the organisers' sandbox and security rules require `eu-west-1` and EU-only models (§7).

**Pitch-track rubric:** pitch deck 20, business case 20, product spec 10, GitHub repo 50. The 9 Oct proposal also asks for: a one-page value case, a live demo plus a 2-minute backup video, the POC and target diagram as 1–2 slides, a cost and 90-day-plan slide, and a 10-minute pitch with 8 minutes of Q&A. **The commit history is checked**, so commit small and often with clear messages. Half the score is documents, so each workstream writes its own repo doc lines (`AGENTS.md` rows, `DECISIONS.md` entries, `HANDOFF.md` real/faked/breaks-first, `EVALS.md`, `COST.md`).

## 7. Rules for every person and every AI assistant (non-negotiable)
- **Region and models:** `eu-west-1` only; Bedrock **`eu.*` inference profiles only**, never `global.*` (D-002).
- **Data:** synthetic only. No real company, system or person names; systems by tier and role, people by role.
- **Secrets:** none in code, the repo, Slack or this vault. The npm token goes only in your home `~/.npmrc` (`web/README.md`).
- **Agents are read-only.** The only write, the status pack, happens after a human approves it.
- **Scope comes from the token,** server-side, never from the client or a model. Agent tools never take scope as an argument.
- **Artefact text is untrusted data.** Agents get rows inside `<evidence>` tags. Never weaken the critic, the scope gate or the create-once ledger to make a test pass.
- **Metrics are code (D-001).** Every number comes from `tools/metrics.py`; agents get figures from tools; a model never computes a number.
- **Prompts are locked files (D-014):** `agents/prompts/<agent>.txt` with a header. Bump the version, run `uv run python scripts/lock_prompts.py`, and never put prompt text in Python.
- **Clean code:** settings only in `config.py`, domain constants in `tools/constants.py`, descriptive names, **no single-character names** (a test enforces it), no magic numbers.
- **Python tests:**
  - All tests live in `tests/`, mirroring the code.
  - Run `uv run --locked pytest` from the repo root before every commit.
  - Coverage must not drop.
  - Write the test first: watch it fail, then make it pass.
- **Git:**
  - Branch `<type>/<short-topic>` from `develop` (`feature/`, `fix/`, `chore/`, `docs/`, `refactor/`, `test/`); never seat names.
  - Open a PR **to `develop`**; Patrick merges. Never push to `develop` or `main`.
  - Small PRs, clear commit messages; history is graded.
- **Stay in your folders.** Need something from another workstream? Mock it against the contract and tell its owner.
- **How we build a feature (superpowers):** brainstorm → written spec → written plan → test-first implementation → review of the whole branch → PR. Small fixes skip the spec but still go test-first.
- **No console-clicked AWS resources.** If it isn't in CDK, it doesn't exist (clean-deploy gate).

## 8. Setup (everyone)
```bash
git clone git@github.com:Amali-Tech/cloud-9-hackathon.git && cd cloud-9-hackathon
curl -LsSf https://astral.sh/uv/install.sh | sh        # once per machine
uv sync && uv run --locked pytest                      # back end: 160 passed
cd web && corepack enable && yarn install --frozen-lockfile && yarn start   # front end (needs the npm token, see web/README.md)
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1       # sandbox account 796973512193, you sign in with your own AmaliTech email through the sign-in URL
```
This vault: `git clone git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then open the folder as an Obsidian vault. Run `git pull` before you start.

**Progress auditor:** to see what's done and what isn't against the briefs and the rubric, run `/audit-progress` in Claude Code at the vault root. See [[How to run the progress auditor]].

Related: [[00 Home]], [[Team plan]], [[Repo]], [[Dev loop]], [[Working with AI assistants]]
