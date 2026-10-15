---
tags: [build, plan, area/agents, area/cost]
id: P7
owner: Patrick
spec: "[[P7 - Fewer load-error rows for the analyst - spec]]"
status: ready
updated: 2026-10-15
---
# P7: fewer load-error rows for the analyst (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]]. Write the test, watch it fail, implement, watch it pass. Compare every command's output with its `Expected:` line; if anything differs, stop.

## 0. Context: read the vault first
Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`. Read [[How to execute a plan]] and [[P7 - Fewer load-error rows for the analyst - spec]] (**the authority**). If unclear, look in the vault, then ask Patrick.

**Goal:** the object lookup keeps at most 5 sample load-error rows; the mapping rules still come from every failing field.

## Global Constraints
- Branch **`perf/retriever-load-error-samples`** from an up-to-date `develop`. Start: `uv run --locked pytest` → 729 passed (or more).
- The constant lives in `tools/constants.py`; no magic numbers; no single-character names.
- One new test only (the parametrised lead-kind test already covers the chain). No Bedrock in tests.
- Commits: no `Co-Authored-By`, no "Generated with". Never push to `develop` or `main`; push and PR after Patrick's OK.

## Task 1: sample the load errors
1. Test in `tests/agents/test_retriever.py`: E4 `object:customers` → at most `LOAD_ERROR_SAMPLE_ROWS` `load_errors` rows, and the `E4#CUSMST#TAXNO` mapping row still present.
   Run `uv run --locked pytest tests/agents/test_retriever.py --no-cov`. **Expected:** the new test fails (50 load-error rows).
2. `LOAD_ERROR_SAMPLE_ROWS = 5` in `tools/constants.py`; in `_object_lead`, read the failed fields from the full tool result, then pass a copy of the result with only the first `LOAD_ERROR_SAMPLE_ROWS` rows to the recorder.
3. Run `uv run --locked pytest`. **Expected:** green, 730 passed, coverage ≥ 98%.
4. `DECISIONS.md`: **D-033 · The orchestrator's first step stays its own decision** (What: P8 rejected; Why: about 5–8 s against the scored "decision about what to do next"; Rejected: fetching the entity's rows in code before planning). Update `AGENTS.md`'s retriever row: "object → … `load_errors_for_object` (at most 5 sample rows kept) …".
5. Commit: `Retriever: at most 5 sample load-error rows for the analyst (P7); D-033 keeps the orchestrator's first decision`.

**Task done when:** the suite is green and D-033 is in `DECISIONS.md`.

## Task 2: live check (Patrick's OK; about $0.30)
1. Q01 through `run_case` with the local asker, Guardrail on. **Expected:** PASS; record the time and cost on the PR next to the eval run's Q01 (63 s, $0.27).

## Done means
- At most 5 load-error rows reach the analyst; every failing field still has its mapping rule.
- D-033 records why P8 was not built.
- Q01 passes live, with its time and cost on the PR.

Related: [[P7 - Fewer load-error rows for the analyst - spec]], [[Build order]]
