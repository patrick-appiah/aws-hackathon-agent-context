---
tags: [build, spec, area/flow, area/cost]
id: H8
owner: Huvison
status: ready
updated: 2026-10-15
---
# H8: the stored answer, budget checks inside the spine, and a claim cap (spec)
> **Three spine changes, in priority order.** (1) `write_answer` stores the `AskResponse` on the run, so `GET /ask/{run_id}` can return it (D-023; Linus's `ask_result` reads it). (2) The budget is checked before every critic, writer and re-plan call, not only at the start: the deployed E4 run cost $0.61 and the local one $0.57 against a $0.50 budget. (3) A cap on the claims one plan sends to the critic. Repo: `Amali-Tech/cloud-9-hackathon`, branch `feature/spine-answer-and-budget` from `develop` (0a566fa or later). The repo is the source of truth for code; the vault is the source of context.

## 0. Context: read the vault first
Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead: `/mnt/c/dev/aws-hackathon/aws-hackathon/`), then `git pull`. **Before writing any code, read, in this order:**
1. [[How to execute a plan]].
2. [[2026-10-15 Ask is asynchronous with start and poll]] (D-023): what `GET /ask/{run_id}` returns and why it reads the ledger.
3. [[2026-10-15]]: Michael's deployed run ($0.61, 206 s), live run 4 ($0.57, 4 orchestrator rounds, 7 critic calls) and the first eval run.
4. [[Whole-code review 2026-10-14]], Huvison's section: "No budget check before the critic and the writer", "Usage is lost when the critic or writer raises".
5. [[H1 - Ledger extensions - spec]] (the ledger's create-once items), [[H2a - Budget and ledger states - spec]] (`tools.budget.require_budget`), [[H2b - Agent states, local spine and Lambda handlers - spec]] (`steps.py`, `spine.py`, `states.py`).
6. [[L3 - Ask, publish and approve entry points - spec]]: Linus's `api.ask_result` reads what this item stores.
7. `01 Decisions/`: [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]] (D-007), the repo's `DECISIONS.md` D-012 (attempts), D-022 (2 attempts), D-023.

**Whenever this spec is silent or unclear, look in the vault before guessing** (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`). If it doesn't answer, stop and ask Patrick. Never invent a name, a shape or a rule.

## 1. Intent
### 1.1 The stored answer (do first)
- **Ledger port** (`tools/ports.py`, `Ledger`): `put_answer(run_id: str, response: dict) -> None`, create-once (a second call raises `LedgerConflict`); `answer(run_id: str) -> dict | None`, `None` until stored.
- **Adapters:** `adapters/memory_ledger.py`; `adapters/dynamo_ledger.py` stores it as its own item, `pk = run_id`, `sk = "ANSWER"` (`ANSWER_SORT_KEY`), written with `ITEM_IS_NEW`, read with `GetItem` (strongly consistent). That is the only action Michael's ApiStack grants `ask_result` (`LEDGER_READ_ACTIONS = ("dynamodb:GetItem",)`, PR #71): **no `Query`**.
- **`steps.write_answer`** stores `response.model_dump(mode="json", by_alias=True)` with `put_answer` as its last act, then returns the response (the execution's output is unchanged).

### 1.2 Budget checks inside the spine
- **Before the critic** (`steps.judge_claim`): `require_budget(ledger, run_id)`. Spent → no model call; record a code-made `Verdict.rejection(claim_id, BUDGET_SPENT_VERDICT_REASON)` (no prompt, like the pre-check's) and return it.
- **Before a re-plan** (`steps.retry_decision`): spent → `REJECT`, whatever the attempt count. The claim goes to the rejected records; no orchestrator call. (The orchestrator also checks inside its plan, P2; this stops the call being made at all.)
- **Before the writer** (`steps.write_answer`): spent → no writer call; the answer is `agents.writer.verbatim_answer(verified)` (code, no model), so passed claims still reach the user.
- **Partial:** `write_answer` marks the response partial when the budget is spent, even if no earlier state passed a `partial` in (the reason from `require_budget`).
- Each check costs one ledger read. The overshoot is at most the one call in flight per state (several if claims are judged in parallel).

### 1.3 Claim cap
- `MAX_CLAIMS_PER_PLAN = 4` in `tools/constants.py` (the lead's value; equal to the planned `MAX_PARALLEL_JUDGEMENTS`).
- `steps.store_claims` keeps the first `MAX_CLAIMS_PER_PLAN` claims of a plan, in the order the orchestrator gave them, and logs the dropped claim IDs. A re-plan already keeps at most one claim.

**Why:**
- **1.1:** async `/ask` (D-023, PR #68, infra PR #71) is built except this and Linus's handler: without a stored answer, `GET /ask/{run_id}` can never return one.
- **1.2:** guideline §02 rule 7 (a run never exceeds its budget). Both measured runs went over. Each rejection buys a critic call and a re-plan, and nothing checked the budget between them.
- **1.3:** live run 4 judged 7 times for one question; each claim can cost two critic calls and a re-plan. Four claims is enough for one entity's blockers and bounds the worst case.

**Success means:**
- `GET /ask/{run_id}`'s data exists: after `run_spine` (and the `write_answer` Lambda), `ledger.answer(run_id)` equals the returned `AskResponse` as JSON. A second `put_answer` raises `LedgerConflict`.
- With the budget spent before a claim is judged: no critic call, a code-made rejection, `retry_decision` → `reject`, no orchestrator call, the writer not called, the response `partial` with the budget reason, and the passed claims in a verbatim answer.
- A plan with 6 claims stores and judges 4.
- `uv run --locked pytest` green, coverage ≥ 98%; no test calls Bedrock.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Where the answer lives | Its own ledger item, `sk = "ANSWER"`, create-once | An attribute on the RUN item (rewrites the run item; a second write can't be refused cleanly); S3 (one more permission for `ask_result`) |
| What a spent budget does to a claim | A code-made rejection, no retry | Leaving it unjudged (it would vanish from the answer and the rejected records) |
| A spent budget at the writer | `verbatim_answer` of the passed claims | No answer (throws away verified work) |
| Cap value | 4 per plan | No cap (run 4: 7 critic calls); 2 (too few for E4's real blockers) |
| Parallel judging | Not here: Michael's FlowStack Map and `run_spine`'s loop are separate work | — |

## 3. Shapes
| Name | Where | Value / signature |
|---|---|---|
| `put_answer`, `answer` | `tools/ports.py` `Ledger`; both adapters | as §1.1 |
| `ANSWER_SORT_KEY` | `adapters/dynamo_ledger.py` | `"ANSWER"` |
| `MAX_CLAIMS_PER_PLAN` | `tools/constants.py` | `4` |
| `BUDGET_SPENT_VERDICT_REASON` | `infra/functions/steps.py` | `"the run's budget was spent before this claim was judged"` |

`docs/DEVOPS_HANDOVER.md`: the ledger's item list gains `ANSWER`; the `ask_result` row says it reads `RUN` and `ANSWER` with `GetItem`.

## 4. Tests (about 7, in the existing files)
- `tests/adapters/test_ledgers.py` (its `ledger` fixture runs every test on both adapters): `put_answer` then `answer` returns it; a second `put_answer` raises `LedgerConflict`; `answer` is `None` before.
- `tests/infra/functions/test_spine.py`: after `run_spine`, `ledger.answer(run_id)` equals the response's JSON.
- `tests/infra/functions/test_steps.py`: spent budget → `judge_claim` makes no critic call and returns a rejection without a prompt; `retry_decision` → `reject`; `write_answer` calls no writer, answers verbatim and is partial with the budget reason.
- `store_claims` with 6 claims keeps the first 4.

## 5. Out of scope
- Linus's `api.ask_result` and `api.ask` (L3).
- The critic's figures (D-029) and the "nothing is blocking" headline (Q03): [[H9 - Critic figures and the nothing-blocking answer - spec]].
- Parallel judging; the FlowStack (Michael).

Related: [[Build order]], [[H8 - Stored answer with budget gates and a claim cap - plan]]
