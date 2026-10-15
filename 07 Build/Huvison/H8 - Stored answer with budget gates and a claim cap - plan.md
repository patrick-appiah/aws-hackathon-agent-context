---
tags: [build, plan, area/flow, area/cost]
id: H8
owner: Huvison
spec: "[[H8 - Stored answer with budget gates and a claim cap - spec]]"
status: ready
updated: 2026-10-15
---
# H8: stored answer, budget checks, claim cap (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line; if anything differs, stop.

## 0. Context: read the vault first
Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`. Read before Task 1: [[How to execute a plan]]; [[H8 - Stored answer with budget gates and a claim cap - spec]] (**the authority**; where this plan and the spec disagree, the spec wins); [[2026-10-15 Ask is asynchronous with start and poll]]; [[H1 - Ledger extensions - spec]]; [[H2b - Agent states, local spine and Lambda handlers - spec]]; [[2026-10-15]]. If unclear, look in the vault, then ask Patrick.

**Goal:** `write_answer` stores the `AskResponse` on the run; the budget is checked before every critic, writer and re-plan call; a plan sends at most 4 claims to the critic.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch **`feature/spine-answer-and-budget`** from an up-to-date `develop`.
- **Start state:** `uv run --locked pytest` → **563 passed** at 0a566fa (it may be higher); coverage 98%. Write the number in the ledger.
- **Clean code:** constants in `tools/constants.py` or the module; no single-character names; no magic numbers.
- **No Bedrock or AWS calls in tests** (moto for DynamoDB, as H1 does).
- **Never weaken a security rule:** create-once ledger items, the run's scope check (`require_run_scope`), fail-closed critic.
- **Fewer tests:** only those in the spec §4. No layout guard tests.
- **Stay in your files:** `tools/ports.py` (the two methods only), both ledger adapters, `infra/functions/steps.py`, `infra/functions/spine.py` if needed, `tools/constants.py` (one constant), their tests, `docs/DEVOPS_HANDOVER.md`. Don't touch `infra/functions/api.py` (Linus) or `infra/stacks/` (Michael).
- **Commits:** one per task, the messages given. No `Co-Authored-By`, no "Generated with" lines. Never push to `develop` or `main`; the PR is after Patrick's OK.

## Task 1: the stored answer
1. Write the adapter test (both adapters) and the `run_spine` test (spec §4). Run `uv run --locked pytest tests/adapters tests/infra/functions/test_spine.py --no-cov`.
   **Expected:** `AttributeError: ... has no attribute 'put_answer'` (or `'answer'`).
2. Add `put_answer` / `answer` to the `Ledger` port and both adapters (`ANSWER_SORT_KEY = "ANSWER"`, `ITEM_IS_NEW`, `GetItem` with `ConsistentRead=True`); `steps.write_answer` calls `ledger.put_answer(run_id, response.model_dump(mode="json", by_alias=True))` before returning.
3. Re-run. **Expected:** pass. Then `uv run --locked pytest`. **Expected:** green.
4. Commit: `Ledger: store the AskResponse on the run for GET /ask/{run_id} (D-023)`.

**Task done when:** `grep -n "Query" adapters/dynamo_ledger.py` shows no use in `answer` (GetItem only), and the suite is green.

## Task 2: budget checks before the critic, the re-plan and the writer
1. Write the `test_steps.py` tests (spec §4) with a ledger whose run's cost already equals its budget (`ledger.add_cost(run_id, 0, 0, budget)`), a critic and a writer that record whether they were called.
   **Expected:** failures: the critic and writer stand-ins were called; `retry_decision` returned `retry`.
2. Implement in `steps.judge_claim`, `steps.retry_decision`, `steps.write_answer` (spec §1.2), with `require_budget`.
3. Run `uv run --locked pytest`. **Expected:** green. Spine tests that expect a re-plan still pass (their budget isn't spent).
4. Commit: `Spine: check the budget before every critic, writer and re-plan call`.

**Task done when:** `grep -n "require_budget" infra/functions/steps.py` shows it in `check_budget`, `judge_claim`, `retry_decision` and `write_answer`.

## Task 3: claim cap and the handover
1. Write the `store_claims` test (6 claims → the first 4). **Expected:** fails, `assert 6 == 4`.
2. Add `MAX_CLAIMS_PER_PLAN = 4` to `tools/constants.py`; cap in `steps.store_claims`, logging the dropped IDs. Update `docs/DEVOPS_HANDOVER.md` (the `ANSWER` item; `ask_result` reads `RUN` and `ANSWER` with `GetItem`).
3. Run `uv run --locked pytest`. **Expected:** green, coverage ≥ 98%.
4. Commit: `Spine: at most 4 claims per plan go to the critic`.

**Task done when:** the suite is green and the handover names the `ANSWER` item.

## Done means
- `uv run --locked pytest` green, about **start + 7** passed, coverage ≥ 98%.
- After `run_spine`, `ledger.answer(run_id)` is the response; create-once holds.
- With a spent budget no critic, writer or orchestrator call is made, and the answer is partial with the passed claims verbatim.
- **Verify in AWS** (after Michael redeploys, Patrick's OK): an E4 run's cost stays at most one model call above $0.50, and `GET /ask/{run_id}` (once L3 lands) returns the stored answer.
- Tell Linus the method names (`ledger.answer(run_id)`), and Michael the `ANSWER` item.

Related: [[H8 - Stored answer with budget gates and a claim cap - spec]], [[Build order]]
