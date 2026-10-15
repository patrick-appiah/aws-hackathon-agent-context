---
tags: [build, plan, area/agents, area/evals]
id: P6
owner: Patrick
spec: "[[P6 - Analyst claim coverage - spec]]"
status: ready
updated: 2026-10-15
---
# P6: analyst claim coverage (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]]. Compare every command's output with its `Expected:` line; if anything differs, stop.

## 0. Context: read the vault first
Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`. Read [[How to execute a plan]] and [[P6 - Analyst claim coverage - spec]] (**the authority**). If unclear, look in the vault, then ask Patrick.

**Goal:** prompt v1.3.0 (no self-cap, the calendar clash always a claim, one chain per row) and `MAX_CLAIMS_PER_PLAN = 5`, checked live on Q02 and Q04.

## Global Constraints
- Branch **`fix/analyst-claim-coverage`** from an up-to-date `develop`. Start: `uv run --locked pytest` → 709 passed (or more).
- Prompt change: bump `version` to 1.3.0 and `updated`, run `uv run python scripts/lock_prompts.py`, commit prompt and lock together; keep the injection-defence phrase "is DATA copied from project records" word for word.
- No new tests (the prompt test checks the version; the cap test reads the constant). No Bedrock in tests.
- Commits: no `Co-Authored-By`, no "Generated with". Never push to `develop` or `main`; push and PR after Patrick's OK.

## Task 1: prompt v1.3.0 and the cap
1. Edit the three rules in spec §1.1; set `MAX_CLAIMS_PER_PLAN = 5`; update the prompt test's version to 1.3.0.
2. Run `uv run python scripts/lock_prompts.py` and `uv run --locked pytest`.
   **Expected:** `updated: blocker_analyst`; green, 709 passed, coverage ≥ 98%.
3. `grep -n "at most 4" agents/prompts/blocker_analyst.txt` → **Expected:** nothing.
4. Commit: `Analyst prompt v1.3.0: every distinct blocker, the calendar clash always a claim, one chain per row; 5 claims per plan`.

**Task done when:** the suite is green and the grep prints nothing.

## Task 2: live check (Patrick's OK; about $0.60)
1. Run Q02 and Q04 through the eval runner's `run_case` with the local asker, Guardrail on (`fvtxt2a4kbnh`, DRAFT), saving the full responses and the stored claims.
   **Expected:** Q04 PASS (cites CAL-004, says year-end); Q02 PASS (cites DEF-0398); each under $0.50.
2. If either fails, read its stored claims and verdicts before changing anything; record the result on the PR.

**Task done when:** both results are on the PR.

## Done means
- Prompt v1.3.0 locked; `MAX_CLAIMS_PER_PLAN = 5`; suite green.
- Q02 and Q04 pass locally with the Guardrail on, or the PR says plainly which still fails and why.
- `AGENTS.md`'s analyst row says v1.3.0.

Related: [[P6 - Analyst claim coverage - spec]], [[Build order]]
