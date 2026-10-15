---
tags: [build, spec, area/tests]
id: P5
owner: Patrick
status: awaiting review
updated: 2026-10-15
---
# P5: remove the tests that police layout and docs (spec)
> **The root guard tests that check where files live and how docs word commands go; the ones that catch real code mistakes stay.** The rules they enforced are documented in `docs/TEAM_PLAN.md` §6 instead (Patrick's rule: no layout guard tests; document rules). Repo: `Amali-Tech/cloud-9-hackathon`, branch `test/remove-layout-guards` from `develop`. The repo is the source of truth for code; the vault is the source of context.

## 0. Context: read the vault first
Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`. Read: [[How to execute a plan]]; [[Whole-code review 2026-10-14]] ("Open decisions (Patrick)"); [[C2 - Repo layout - spec]]; `01 Decisions/` [[2026-10-13 Clean-code rules enforced by tests]] (which of its rules stay tested). If something is unclear, look in the vault, then ask Patrick.

## 1. Intent
| File | Delete | Keep |
|---|---|---|
| `tests/test_code_style.py` | `find_tests_outside_tests_folder` and its 3 tests; `test_docs_and_code_refer_to_tests_by_their_tests_path` | no single-character names; no inline prompts in agents (and their finder tests) |
| `tests/test_dependencies.py` | `test_requirements_files_are_retired_and_the_lock_exists`, `test_included_dependency_groups_are_followed`, `test_every_declared_dependency_is_locked` (and the group helpers), `test_documented_commands_run_through_uv_with_a_locked_environment` | `test_lock_is_in_sync_with_pyproject` (`uv lock --check`) |
| `tests/test_architecture.py` | `test_tests_never_shadow_the_real_packages`, `test_coverage_runs_are_refused_outside_the_repo_root`, `test_runs_without_coverage_work_from_any_folder` | `test_core_has_no_infrastructure_imports` (the hexagon, D-024) |

`tests/conftest.py`'s refusal of coverage runs outside the repo root stays (it protects the coverage figure); only its test goes.

**Why:** these tests check repo shape and doc wording, not behaviour. They fail on harmless moves and wording, cost review time, and the rules fit in one doc. The kept ones catch mistakes that change behaviour or break the core's isolation.

**Success means:** 11 tests fewer, about 130 lines fewer; the suite green; `docs/TEAM_PLAN.md` §6 states the removed rules as rules ("tests live in `tests/`, mirroring the code"; "no requirements files"; "documented commands use `uv run --locked`"; "run pytest from the repo root") without "a test fails if…"; `DECISIONS.md` and the vault's "Clean-code rules enforced by tests" note say which rules are tested and which are documented.

## 2. Out of scope
Every other test; the conftest guard; the prompt lock check (`lock_prompts.py --check`).

Related: [[Build order]], [[P5 - Remove layout guard tests - plan]]
