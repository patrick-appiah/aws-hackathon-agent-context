---
tags: [build, plan, area/tests]
id: P5
owner: Patrick
spec: "[[P5 - Remove layout guard tests - spec]]"
status: ready
updated: 2026-10-15
---
# P5: remove the layout guard tests (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]]. Compare every command's output with its `Expected:` line; if anything differs, stop.

## 0. Context: read the vault first
Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`. Read [[How to execute a plan]] and [[P5 - Remove layout guard tests - spec]] (**the authority**). If unclear, look in the vault, then ask Patrick.

**Goal:** the 11 tests in the spec's table are gone, the rules they enforced are written in `docs/TEAM_PLAN.md` §6, and the suite is green.

## Global Constraints
- Repo `~/amalitech/aws-hackathon/erp-migration-portal`; branch **`test/remove-layout-guards`** from an up-to-date `develop` (after P4 merges, or rebased on it).
- **Start state:** `uv run --locked pytest` → `N passed` (write `N` in the ledger).
- Delete only the tests named in the spec. No new tests.
- Commits: the messages given; no `Co-Authored-By`, no "Generated with". Never push to `develop` or `main`.

## Task 1: delete the tests
1. Delete the spec's tests and the helpers only they use (`find_tests_outside_tests_folder`, `TEST_FILE_PATTERNS`, `CONFTEST_FILE_NAME`, `TEST_FILE_REFERENCE`, `HISTORICAL_RECORDS`, `RETIRED_FILES`, `_group_requirements`, `_declared_dependency_names`, `COMMAND_RULES` and the regexes, `REAL_PACKAGES`, `_run_pytest_from_the_tests_folder`). Remove imports that become unused.
2. Run `uv run ruff check tests` and `uv run --locked pytest`.
   **Expected:** `All checks passed!`; `N - 11 passed`; coverage unchanged.
3. Commit: `Tests: remove the guard tests that police layout and doc wording`.

**Task done when:** `grep -c "^def test" tests/test_code_style.py tests/test_dependencies.py tests/test_architecture.py` prints `5`, `1`, `1` (the kept tests: names, the inline-prompt finder and its checks; the lock; the core imports).

## Task 2: document the rules
1. `docs/TEAM_PLAN.md` §6: drop "a test fails if they come back" and "a guard test fails the build"; state the rules plainly; say which stay tested (single-character names, inline prompts, core imports, the lock).
2. `DECISIONS.md`: one line under the clean-code rules entry (or a short D-029) saying layout and doc-wording rules are documented, not tested.
3. Run `uv run --locked pytest`. **Expected:** green.
4. Commit: `Docs: layout and command rules are documented, not tested`.

**Task done when:** `grep -n "test fails\|guard test" docs/TEAM_PLAN.md` prints nothing.

## Done means
- `uv run --locked pytest` green with `N - 11` passed; coverage unchanged.
- The kept tests are exactly those in the spec's "Keep" column.
- `docs/TEAM_PLAN.md` §6 lists the removed rules as rules, and `DECISIONS.md` records the change.

Related: [[P5 - Remove layout guard tests - spec]], [[Build order]]
