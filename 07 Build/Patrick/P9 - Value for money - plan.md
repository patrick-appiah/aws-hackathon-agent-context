---
tags: [build, plan, area/agents, area/metrics, area/business]
id: P9
owner: Patrick
spec: "[[P9 - Value for money - spec]]"
status: ready
updated: 2026-10-15
---
# P9: value for money (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]]. Write the test, watch it fail, implement, watch it pass. Compare every command's output with its `Expected:` line; if anything differs, stop.

## 0. Context: read the vault first
Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`. Read [[How to execute a plan]] and [[P9 - Value for money - spec]] (**the authority**). If unclear, look in the vault, then ask Patrick.

**Goal:** three money figures in code, usable by the analyst as figure tools, asked in a new eval Q15.

## Global Constraints
- Branch **`feature/value-for-money`** from an up-to-date `develop`. Start: `uv run --locked pytest` → N passed (write N in the ledger).
- Figures in `tools/metrics.py` only (D-010); constants in `tools/constants.py`; no single-character names; no magic numbers.
- Prompt changes: bump `version` and `updated`, `uv run python scripts/lock_prompts.py`, commit prompt and lock together; keep the injection-defence phrases word for word.
- Fewer tests: one per metric (the E4 values), one for the tools' scope, the prompt version tests. No Bedrock in tests.
- Commits: no `Co-Authored-By`, no "Generated with". Never push to `develop` or `main`; push and PR after Patrick's OK.

## Task 1: the three metrics
1. Tests in `tests/tools/test_metrics.py`: E4 `spend_vs_plan` (276400, 292500, 16100, three months), `cost_of_delay` (6, 5, 7150, 35750), `unused_capacity` (9, 4500); each cites roster and rate-card rows. **Expected:** `AttributeError: module 'tools.metrics' has no attribute 'spend_vs_plan'`.
2. Implement per spec §1.1 (reuse `effort_cost`'s rate-card and roster filtering; working days with `date.weekday() < 5`).
3. `uv run --locked pytest tests/tools --no-cov`. **Expected:** pass.
4. Commit: `Metrics: spend vs plan, cost of delay and unused capacity per entity (P9)`.

**Task done when:** the three tests pass with the E4 values.

## Task 2: figure tools
1. Test in `tests/tools/test_agent_tools.py`: the three tools exist in `make_analyst_tools`, return the spec's fields without `evidence`, and refuse another entity (`out_of_scope`). **Expected:** fails (`KeyError`).
2. Add them with `_requires_entity_in`; field tuples as constants.
3. `uv run --locked pytest`. **Expected:** green.
4. Commit: `Analyst tools: the three money figures (P9)`.

**Task done when:** the suite is green.

## Task 3: prompts, eval, docs
1. Analyst prompt v1.4.0 and orchestrator prompt v1.3.0 per spec §1.3; lock; update the two version tests.
2. `evals/inputs/Q15.json` and `evals/expected/Q15.json` per spec §1.4; `EVALS.md` Q15 row; `uv run python -m evals.run` (no asker). **Expected:** Q15's data checks pass (NOT RUN, no failed checks).
3. `DECISIONS.md` D-034; `AGENTS.md` analyst tools and versions; the business case's line.
4. `uv run --locked pytest`. **Expected:** green, coverage ≥ 98%.
5. Commit: `Prompts and eval for value for money: analyst v1.4.0, orchestrator v1.3.0, EVALS Q15, D-034`.

**Task done when:** the runner's Q15 data checks hold and the suite is green.

## Task 4: live check (Patrick's OK; about $0.60)
1. Q15 and Q01 through `run_case` with the local asker, Guardrail on, saving the stored claims. **Expected:** Q15 PASS (a money figure stated, no "budget"); Q01 still PASS.

## Done means
- The three figures exist in code with the E4 values, cited; the analyst can state them as figures.
- Q15 passes live; Q01 doesn't regress.
- D-034, AGENTS.md, EVALS.md and the business case say what was added and that there is no budget figure.

Related: [[P9 - Value for money - spec]], [[Build order]]
