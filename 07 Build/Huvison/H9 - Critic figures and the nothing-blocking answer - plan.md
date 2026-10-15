---
tags: [build, plan, area/agents, area/evals]
id: H9
owner: Huvison
spec: "[[H9 - Critic figures and the nothing-blocking answer - spec]]"
status: ready
updated: 2026-10-15
---
# H9: critic figures and the nothing-blocking answer (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line; if anything differs, stop.

## 0. Context: read the vault first
Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`. Read before Task 1: [[How to execute a plan]]; [[H9 - Critic figures and the nothing-blocking answer - spec]] (**the authority**); [[2026-10-15 Figures are verified by code and the critic judges rows]]; [[H3 - Writer agent - spec]]; [[2026-10-15]]. If unclear, look in the vault, then ask Patrick.

**Goal:** the critic is told which figures code already checked; a clean entity's answer says nothing is blocking, decided in code; the critic streams nothing and validates its verdict.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch **`feature/critic-figures-and-all-clear`** from `develop` **after H8 merges**.
- **Start state:** `uv run --locked pytest` → `N passed` (write `N` in the ledger), coverage 98%.
- **Prompt changes:** bump `version` and `updated`, run `uv run python scripts/lock_prompts.py`, commit the prompt and the lock together.
- **No Bedrock or AWS calls in tests.** Never weaken the critic's fail-closed rule or the D-009 escaping.
- **Fewer tests:** only those in the spec §4.
- **Stay in your files:** `agents/critic.py`, `agents/prompts/critic.txt`, `agents/prompts/prompts.lock`, `agents/writer.py` (one constant), `infra/functions/steps.py`, their tests. Not `agents/blocker_analyst.py` (Linus).
- **Commits:** one per task, the messages given. No `Co-Authored-By`, no "Generated with" lines. Never push to `develop` or `main`; the PR is after Patrick's OK.

## Task 1: the critic's model and verdict
1. Tests: `make_agent` has no callback handler; a verdict with `"missing_evidence": "x"` is a rejection. Run `uv run --locked pytest tests/agents/test_critic.py --no-cov`.
   **Expected:** two failures (a callback handler is set; the string verdict passes or crashes).
2. `make_agent` → `Agent(model=bedrock_model(get_settings().critic_model_id), system_prompt=..., tools=[], callback_handler=None)`; delete the copied escaping helpers and use `agent_support.tagged`; validate with `Verdict.model_validate` inside the `try`.
3. Run `uv run --locked pytest`. **Expected:** green.
4. Commit: `Critic: shared Bedrock model with nothing streamed; verdicts validated with Verdict`.

**Task done when:** `grep -n "ESCAPED_CHARACTERS\|BedrockModel\|_is_valid_verdict" agents/critic.py` prints nothing.

## Task 2: figures recomputed by code (D-030)
1. Tests (spec §4, critic input and prompt). **Expected:** fail: no `<figures_recomputed_by_code>` tag; the prompt is v1.0.0.
2. `build_input`: the claim without `figures`, then `tagged(FIGURES_TAG, {name: figure["value"] ...})` after the evidence. Prompt v1.1.0 with the rule in spec §1.1; `uv run python scripts/lock_prompts.py`.
3. Run `uv run --locked pytest`. **Expected:** green (`lock_prompts.py --check` passes).
4. Commit: `Critic: figures recomputed by code are marked as such (D-030), prompt v1.1.0`.

**Task done when:** `grep -n "version: 1.1.0" agents/prompts/critic.txt` prints one line and the suite is green.

## Task 3: nothing is blocking (Q03)
1. Tests (spec §4, E1 and E4 through `run_spine` with a stub orchestrator that returns no claims and a writer that records calls). **Expected:** E1's headline is "No finding could be verified…".
2. `NOTHING_BLOCKING_HEADLINE` in `agents/writer.py`; in `steps.write_answer`, the rule in spec §1.2 (no claims in the ledger, not partial, `metrics.open_blockers(repository, entity_id) == []`).
3. Run `uv run --locked pytest`. **Expected:** green, coverage ≥ 98%.
4. Commit: `Answer: a clean entity says nothing is blocking, decided in code (EVALS Q03)`.

**Task done when:** the E1 test passes and the E4 test shows the old headline.

## Done means
- `uv run --locked pytest` green, about **N + 5**, coverage ≥ 98%.
- The critic: `bedrock_model`, no streaming, `Verdict`-validated, prompt v1.1.0 locked, figures in their own tag.
- E1 with no claims says nothing is blocking; nothing else does.
- **Verify live** (Patrick's OK): the eval runner's Q03 and Q06 pass; `scripts/ask.py --json` output is valid JSON from the first character (no critic text before it).

Related: [[H9 - Critic figures and the nothing-blocking answer - spec]], [[Build order]]
