---
tags: [workstream, area/team]
owner: Huvison
updated: 2026-10-14
---
# Huvison: trust and flow
> The repo is the source of truth. Read [[Workstreams]] first. Your row: `docs/TEAM_PLAN.md` §2, workstream 2.

## Your job in one paragraph
You build the part of the system that makes the answers **trustworthy**:
- the **writer** that assembles passed claims into a cited answer;
- the **ask-spine step functions** that run budget check → orchestrator → claims to the ledger → **critic per claim** → **retry guard** → writer;
- the **run ledger** extensions that hold every claim, verdict, attempt, rejection, cost and approval token;
- the **publish flow**, where nothing is written until a human approves it.

You also own **cost per run**, the **Guardrail settings**, and timing `/ask` against API Gateway's 29-second limit. The rubric scores trust heavily: citations, a blind critic that actually rejects, a ledger-bounded retry, human approval and a budget ceiling.

## Where you sit in the architecture
```
 POST /ask ─▶ Step Functions Express (Yaw writes the ASL; each state is one of YOUR flow/ functions)
   ★check_budget★ ─▶ ★run_orchestrator★ (Patrick's agent) ─▶ ★store_claims★ ─▶ ledger (put_claim / revise_claim + add_cost)
   ─▶ ★judge_claim★ (agents/critic.py judge: pre-check in code, then the blind critic) ─▶ ★retry_decision★ (attempts < 2?)
        ├─ pass ─▶ ★write_answer★ (★WRITER★) ─▶ AskResponse (Patrick's schema)
        ├─ reject, attempts < 2 ─▶ back to run_orchestrator (re-plan, same claim ID)
        └─ reject, limit reached ─▶ ★record_rejection★ ─▶ rejected records ("could not verify" in the portal)
 POST /publish ─▶ (Linus's api entry) ─▶ ★start_publish★ ─▶ Step Functions Standard ─▶ waitForTaskToken
 POST /approve ─▶ (Linus's api entry) ─▶ ★decide★ ─▶ SendTaskSuccess ─▶ status pack to S3 status-packs/ | SendTaskFailure (sent back)
```
- **The critic is blind.** It gets only the claim and the rows its citations point to, fetched in code. Never the plan, the question history or the attempt count (D-007, D-012). It **fails closed** on any model error, guardrail block or malformed output (D-009). That's already built and tested in `agents/critic.py`.
- **The retry guard is a Step Functions `Choice` reading the counter from the ledger,** never a model decision. `config.py` `max_claim_attempts` = 2.

## What you own
| Path | State |
|---|---|
| `agents/critic.py`, `agents/prompts/critic.txt`, `agents/prompt_loader.py` | exist (critic v1.0.0, fails closed, prompt provenance) |
| `agents/writer.py` *(new)*, `agents/prompts/writer.txt` *(new)* | the writer |
| `flow/` *(new)*: `flow/steps.py` *(new)*, `flow/budget.py` *(new)*, `flow/publish.py` *(new)*, `flow/cost.py` *(new)* | the step functions |
| `tools/ports.py` (the `Ledger` port only, coordinate with Patrick), `adapters/memory_ledger.py`, `adapters/dynamo_ledger.py` | exist; you extend them |
| `tests/adapters/test_ledgers.py` | exists; one suite run against **both** ledgers |
| `AGENTS.md` rows: critic, writer; `HANDOFF.md` lines for your parts | your docs |

## What you build
Each task has a spec and plan first (superpowers), test-first code, and a PR to `develop`.

### 1. Ledger extensions (first: everyone's flow depends on them)
Extend the `Ledger` port in `tools/ports.py` and **both** adapters. Every method gets a test in `tests/adapters/test_ledgers.py`, which already runs the same suite against `InMemoryLedger` and `DynamoLedger` (moto).
| Method | Behaviour | DynamoDB item |
|---|---|---|
| `put_rejected(run_id, claim_id, verdicts)` | create-once; the claim's full verdict list | separate rejected-records table (`rejected_table` setting from Patrick's PR; Michael's LedgerStack): `pk=run_id, sk=claim_id` |
| `rejected(run_id) -> list[dict]` | for `AskResponse.rejected[]` | query the rejected-records table by `pk=run_id` |
| `run(run_id) -> dict` | scope, budget, cost, tokens, status | `sk=RUN` (exists) |
| `claims(run_id) -> list[dict]` | every claim with attempts and verdicts | `sk` begins_with `CLAIM#` (exists: `CLAIM_SORT_KEY_PREFIX`) |
| `add_step(run_id, step)` | trace entries `{step, agent, prompt}` for `AskResponse.trace` | `sk=STEP#<n>` (TEAM_PLAN §3) |
| token totals | **already stored:** both adapters persist `tokens_in`/`tokens_out`/cost on the RUN item via `add_cost`; expose them through `run(run_id)`, don't rewrite them | `sk=RUN` |
| `put_task_token(run_id, token)` / `task_token(run_id)` | the publish approval token, **keyed by `run_id`** (spec decision; `/approve` takes `run_id`) | `pk=run_id, sk=TASK` |

Keep the integrity rules (D-012): create-once runs, claims and rejections; updates to unknown items raise `LedgerConflict`; the attempt counter and spent cost can never be reset.

### 2. The budget check: `flow/budget.py`
One function, `require_budget(ledger, run_id) -> float | PartialAnswer`, with two callers:
- your `check_budget` state;
- Patrick's orchestrator, before each re-plan (guideline: "budget ceiling enforced in the orchestrator").

The default ceiling is `config.py` `run_budget_usd` (0.50).

### 3. The step functions: `flow/steps.py`
One function per state. Each takes and returns the step models from Patrick's contracts PR (`Question`, claims, `Verdict`, `WriterInput`, `Answer`, `PartialAnswer`, `Usage`); Step Functions passes JSON, so validate on the way in.
1. `check_budget(question)`: start the run (`Ledger.start_run(run_id, scope, budget_usd)`), then `require_budget`.
2. `run_orchestrator(question)`: calls `agents/orchestrator.py` (Patrick), and records the trace step and `add_cost` from its `Usage`.
3. `store_claims(run_id, claims)`: a new claim → `put_claim`; a re-planned one → `revise_claim` (same ID; attempts kept).
4. `judge_claim(run_id, claim, scope)`: `agents.critic.judge(claim, repository, scope)` → `record_verdict` (returns the new attempt count). The critic's prompt provenance is already on the verdict.
5. `retry_decision(run_id, claim_id)`: `Ledger.attempts(...) < get_settings().max_claim_attempts` → `retry`, else `reject`. It reads only the ledger, never the claim content.
6. `record_rejection(run_id, claim_id)`: `put_rejected` with all of the claim's verdicts.
7. `write_answer(run_id, question, passed_claims)`: the writer → `Answer`; `add_cost` from its `Usage`; build the `AskResponse` (with `rejected` from the ledger and `trace` from the steps).

Test the whole sequence locally with `InMemoryLedger` and stub agents (Q01 passes, a forced rejection retries once and then lands in rejected records).

### 4. The writer: `agents/writer.py`, `agents/prompts/writer.txt`
- **Input/output:** `WriterInput {scope, question, passed_claims[], metrics_snapshot}` → `Answer {headline, bullets[{text, citations[]}], rejected_count}` + `Usage`.
- **Code check after the model:** drop any bullet with no citation, or whose citations don't all belong to a passed claim, and log the drop. The writer never adds a claim (`AGENTS.md`, writer row). Figures appear only as the claims state them.
- **Model:** `get_settings().writer_model_id` with the Guardrail, using the `make_agent` pattern from `agents/critic.py`. Stub-model tests.

### 5. Publish and approve: `flow/publish.py`
- `start_publish(run_id, user)`: starts the Standard execution (`publish_state_machine_arn` from Patrick's settings). The first state stores its task token with `put_task_token(run_id, token)`. Returns `{run_id, execution_arn, status: "awaiting_approval"}`.
- `decide(run_id, decision, note, approver_scope)`:
  - only a `delivery_lead` may approve;
  - `approve` → `SendTaskSuccess`, and the last state writes `s3://<artefacts_bucket>/<status_pack_prefix><run_id>.json`;
  - `send_back` → `SendTaskFailure`, logged on the run in the ledger.
- Linus's `api/handlers.py` *(new)* entry points call these two functions.
- Test with moto (Step Functions + S3) or fakes; no real AWS in unit tests.

### 6. Cost: `flow/cost.py` + a price table in `tools/constants.py`
- **Price table:** `MODEL_PRICES_USD_PER_1K_TOKENS = {model_id: (input, output)}` for every model ID in `config.py`. The prices and their sources come from Abdul's research (Bedrock eu-west-1 on-demand).
- `cost_usd(usage) -> float`. Every state that runs an agent calls `add_cost` with it. The total per run lands in `AskResponse.cost_usd`, and `COST.md` is filled from real runs (Abdul).

### 7. The local asker for the eval runner: `flow/local.py` *(new)*
Michael's runner (`evals/run.py`, PR #16) calls an asker: `(case_input, scope, repository) -> dict`, returning the `/ask` response plus `"refused": true` when refused.
- Write `flow/local.py: ask`. It runs your step sequence in-process (`CsvRepository`, `InMemoryLedger`, the real agents) and **applies the input's `inject` itself**:
  - `strip_citations` (Q08): strip the citations from one analyst claim, so the critic pre-check must reject it without a model call;
  - `force_unsupportable_claim` (Q09): the asker forces a claim no evidence supports, the **real** critic rejects it until the retry guard stops it, and the claim lands in rejected records (as `evals/inputs/Q09.json` says).
- Run it with `uv run python -m evals.run --asker flow.local:ask`. Patrick's `scripts/ask.py` can call the same function.
- **No fault switch exists in the API or production config.** Only the eval asker applies `inject`.
- **Q09 is decided (D-022):** at most 2 attempts per claim in total, one retry. Keep `max_claim_attempts = 2` and `attempts < 2`; a claim rejected twice lands in rejected records with **2 verdicts**.

### 8. Guardrail settings
Write down the settings Michael deploys in GuardrailStack: a PII filter, and the prompt-attack filter on input. Check that every agent's `make_agent` passes `guardrail_id` and `guardrail_version` when set (the critic already does). EVALS Q12: the `DEF-0462` text must stay data.

### 9. Latency
By D1 18:00, time a full `/ask` with one retry. API Gateway cuts synchronous calls at **29 seconds**. If you're over, propose to Patrick an async start (`POST /ask` returns `run_id`) plus polling (`GET /ask/{run_id}`), and record the decision.

## Interfaces
| You consume | From | Exact name |
|---|---|---|
| Step models, settings | Patrick | `tools/models.py` (`Question`, `WriterInput`, `Answer`, `PartialAnswer`, `Usage`), `config.get_settings()` |
| Orchestrator | Patrick | `agents/orchestrator.py` *(new)* |
| Critic | done | `agents.critic.judge(claim, repository, scope, agent=None)`, `precheck` |
| Prompts | done | `agents.prompt_loader.load_prompt(name)` |
| Model prices | Abdul | the research table in `COST.md` |

| You produce | For | Exact name |
|---|---|---|
| Ledger methods | Linus (runner), Patrick, Yaw (IAM) | `tools/ports.py` `Ledger` + both adapters |
| Step functions | Yaw (FlowStack Lambdas), Patrick (`scripts/ask.py` *(new)*) | `flow/steps.py` |
| Budget check | Patrick | `flow/budget.py` `require_budget` |
| Publish functions | Linus (`api/handlers.py`) | `flow/publish.py` `start_publish`, `decide` |
| Local asker (applies `inject`) | the eval runner, Patrick (`scripts/ask.py`) | `flow/local.py` *(new)* |
| Guardrail settings | Michael | in `docs/DEVOPS_HANDOVER.md` *(new)* |

## Dependencies
- **You wait on:**
  - **Patrick's contracts PR** for the step models and settings. Until then, use `BlockerClaim` and `Verdict` (they exist) and plain dicts.
  - **Patrick's orchestrator.** Use a stub that returns the E4 claim from `tests/tools/test_claims.py` (`VALID_CLAIM`).
  - **Yaw's FlowStack and Michael's LedgerStack** for AWS. Everything runs locally first.
- **Waiting on you:** Patrick (budget, ledger), Linus (publish functions), the eval runner (local asker), Yaw (state functions).

## Your milestones
| When | Milestone |
|---|---|
| D1 12:00 | Ledger extensions merged, tested on both adapters |
| D1 16:00 | The full `/ask` sequence runs locally with stubs, including one retry and one rejection |
| D1 18:00 | Skeleton live (critic stubbed to pass); `/ask` timed against 29 s |
| D2 12:00 | Real critic + retry guard + publish/approve end to end |
| D2 14:00 | Cost per run recorded; the local asker runs all 14 |

## Eval questions you own or affect
| Question | What it checks |
|---|---|
| **Q08** | Uncited claim → rejected |
| **Q09** | Retry limit → rejected records with all verdicts |
| **Q12** | Prompt injection: `DEF-0462` stays data, critic verdicts unchanged |
| Every question | Cost per run and the trace |

## Definition of done
- [ ] Ledger extensions on both adapters, create-once kept, all of `tests/adapters/test_ledgers.py` green.
- [ ] `flow/` step functions tested; the local sequence passes Q01 and handles a rejection.
- [ ] Writer drops uncited bullets (tested); prompt locked; `AGENTS.md` critic and writer rows true.
- [ ] Publish needs a `delivery_lead` approval; the status pack is written only after approval; send-back is logged.
- [ ] Cost per run comes from real `Usage`; the price table is sourced.
- [ ] `uv run python -m evals.run --asker flow.local:ask` runs; Q08, Q09 (2 verdicts, D-022), Q12 pass; the 29-second check done.
- [ ] Your `HANDOFF.md` lines (what's real, what's faked, what breaks first).

## Rules and pitfalls specific to you
- **Never let a model decide the retry,** see attempts or reset a counter.
- **Never catch a critic failure as a pass.** Fail closed, always.
- **Never write the status pack before approval.** The only write in the system is behind human approval.
- **The ledger is create-once.** Re-putting a claim must raise, never reset (D-012).
- **Both adapters must behave the same.** Add every test to the shared suite, never to one adapter only.

## Getting started
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest           # 160 passed; ledger suite: tests/adapters/test_ledgers.py
git switch -c feature/ledger-extensions
```
Then give your assistant `06 Workstreams/prompts/huvison.txt`.

## Who to ask
| Topic | Person |
|---|---|
| Step models, orchestrator, contracts | Patrick |
| API entry points, eval runner | Linus |
| FlowStack, Lambdas | Yaw |
| LedgerStack, GuardrailStack | Michael |
| Prices | Abdul |

Related: [[Workstreams]], [[Team plan]]
