---
tags: [build, plan, area/agents, area/cost]
id: P4
owner: Patrick
spec: "[[P4 - Fixed-lookup retriever - spec]]"
status: ready
updated: 2026-10-15
---
# P4: the retriever as a fixed lookup (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line; if anything differs, stop and follow "When output doesn't match".

## 0. Context: read the vault first
Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`. Read before Task 1:
1. [[How to execute a plan]].
2. [[P4 - Fixed-lookup retriever - spec]]: **the authority**. Where this plan and the spec disagree, the spec wins; record the conflict in the ledger.
3. [[P1 - Retriever agent - spec]], [[P2 - Orchestrator agent - spec]], [[Whole-code review 2026-10-14]].
4. `01 Decisions/`: [[2026-10-13 Metrics are code, only the blocker Q&A is agentic]], [[2026-10-13 Scope from the token, enforced twice]]. [[C2 - Repo layout - spec]].

When something is unclear, look in the vault before guessing; if it doesn't answer, stop and ask Patrick.

**Goal:** `agents.retriever.retrieve` fetches each lead's rows with a fixed table of tool calls; no model, no prompt, no retriever model setting.

**Architecture:** `retrieve` checks the scope, builds `make_retriever_tools` on the scope narrowed to the entity, runs `LOOKUP_BY_LEAD_KIND[lead.kind]`, and records the rows of each tool result once. The defect's object is read from the entity's defect log through `tools.queries`.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch **`refactor/retriever-fixed-lookup`** from an up-to-date `develop`.
- **Start state:** `uv run --locked pytest` → **548 passed** (ad58454; it may be higher), coverage 98%. Write the number in the ledger.
- **Clean code:** names in `tools/constants.py` or the module's constants; no single-character names; no magic numbers.
- **No Bedrock or AWS calls in tests.**
- **Never weaken a security rule** (scope gate, narrowed scope, rows only from tool results).
- **Fewer tests:** only the ones in the spec §4. No layout guard tests.
- **Commits:** one per task, the messages given. No `Co-Authored-By`, no "Generated with" lines. Never push to `develop` or `main`; the PR is after Patrick's OK.

## Task 1: the lookup table (`agents/retriever.py`, `tests/agents/test_retriever.py`)
1. Rewrite `tests/agents/test_retriever.py` with the spec §4 tests (no `scripted_agent`, no `agent_factory`). One parametrised test over the five lead kinds asserts the cited `(artefact, row_id)` pairs include, for E4:
   - `entity`: a `reconciliation_results` row `RC-C3-E4-customers` and `defect_log` `DEF-0412`;
   - `object` `customers`: `RC-C3-E4-customers`, a `load_errors` row, `field_mappings:E4#CUSMST#TAXNO`, `DEF-0412`;
   - `defect` `DEF-0412`: `DEF-0412`; `runbook_step`: a `cutover_runbook` row; `task`: a `workplan` row and a `team_roster` row.

   Run `uv run --locked pytest tests/agents/test_retriever.py --no-cov`.
   **Expected:** failures with `TypeError: retrieve() ...` or `AssertionError` (the model-driven retriever needs an agent).
2. In `agents/retriever.py`: delete `make_agent`, `build_input`, `AgentFactory`, the cap and lock in `RowRecorder`, and the Strands/usage imports; add `LOOKUP_BY_LEAD_KIND` and the five lookups; `retrieve(request, repository)` returns `Evidence(rows=recorder.rows)`. Move `AgentFactory` to `agents/agent_support.py` and update `agents/orchestrator.py`'s import. Update the module docstring (no model; the table; rows only from tool results).
3. Run `uv run --locked pytest tests/agents --no-cov`.
   **Expected:** the retriever tests pass; `test_orchestrator.py`'s real-retriever test fails with `TypeError: retrieve() got an unexpected keyword argument 'agent_factory'`. Fix that test to call `retriever.retrieve(request, repository)` (no scripted agent). Re-run: **Expected:** all pass.
4. Commit: `Retriever: a fixed lookup per lead kind, no model call (D-028)`.

**Task done when:** `grep -n "strands\|budgeted_agent\|load_prompt" agents/retriever.py` prints nothing, and `tests/agents` passes.

## Task 2: remove the retriever's model, prompt and caps
1. Delete `agents/prompts/retriever.txt`; run `uv run python scripts/lock_prompts.py`. **Expected:** the `retriever:` entry leaves `agents/prompts/prompts.lock`.
2. Remove the retriever prompt test from `tests/agents/test_prompts.py`; remove `MAX_RETRIEVER_TOOL_CALLS` and `MAX_RETRIEVER_MODEL_CALLS` from `tools/constants.py`; remove `DEFAULT_RETRIEVAL_MODEL`, `retriever_model_id` and `RETRIEVER_MODEL_ID` from `config.py`, `tests/test_config.py` and `tests/tools/test_cost.py`.
3. Run `grep -rn "RETRIEVER_MODEL\|retriever_model\|MAX_RETRIEVER\|prompts/retriever" --include=*.py . | grep -v .venv`. **Expected:** nothing.
4. Run `uv run --locked pytest`. **Expected:** green; `N - (deleted) + (new)` passed; coverage ≥ 98%.
5. Commit: `Retriever: remove its prompt, model setting and loop caps`.

**Task done when:** the suite is green and the grep in step 3 prints nothing.

## Task 3: docs and decision
1. `DECISIONS.md`: add **D-028 · The retriever is a fixed lookup, not a model** (What: the table; Why: time, cost, reliability, the live figures; Rejected: keeping Haiku, a smaller model, a "defect by ID" tool).
2. `AGENTS.md` retriever row: "code, no model (D-028)"; `ARCHITECTURE.md` lines on the retriever and the model list (Haiku 4.5 only for the retriever → gone); `COST.md` Haiku row "not used since D-028"; `docs/DEVOPS_HANDOVER.md`: remove `RETRIEVER_MODEL_ID` and the Haiku profile from the agent Lambdas' settings; `HANDOFF.md`'s retriever line (it still says Nova Lite).
3. Run `uv run --locked pytest` and `git grep -n "Haiku\|RETRIEVER_MODEL_ID" -- '*.md'`. **Expected:** green; Haiku appears only in `COST.md`'s price table and the history in `DECISIONS.md`.
4. Commit: `Docs: the retriever is a fixed lookup (D-028)`.

**Task done when:** every doc that named the retriever's model says D-028.

## Done means
- `uv run --locked pytest` green, coverage ≥ 98%; the retriever tests show each lead kind's rows for E4.
- `agents/retriever.py` imports no Strands and loads no prompt; `agents/prompts/retriever.txt` is gone and the lock has no retriever entry.
- `DECISIONS.md` has D-028; `AGENTS.md`, `ARCHITECTURE.md`, `COST.md`, `HANDOFF.md` and `docs/DEVOPS_HANDOVER.md` agree with it.
- **Verify in AWS** (Patrick's OK, about $0.30–0.60): `uv run python scripts/ask.py --entity E4 "What is blocking cutover for E4?"` shows no retriever model usage and a shorter time than 2 min 42 s; the answer still cites `DEF-0412` and `RC-C3-E4-customers`.

Related: [[P4 - Fixed-lookup retriever - spec]], [[Build order]]
