---
tags: [workflow, area/process]
---
# Dev loop
How a change goes from idea to `develop` (and from `develop` to `main` for releases). Full detail lives in the repo `docs/TEAM_PLAN.md`; this note is the working checklist.

## Steps
1. **Branch** from `develop`: `<type>/<short-topic>`, where type is `feature/`, `fix/`, `chore/`, `docs/`, `refactor/` or `test/` (e.g. `feature/blocker-analyst`). Not seat numbers. Stay inside your seat's folders ([[Team plan]] §2).
2. **Test first.** Write the failing test before the code (superpowers TDD flow). Deterministic code lives in `tools/` and gets a unit test in `tests/tools/` (all tests live in `tests/`, mirroring the code); an adapter joins the existing suite for its port (see [[Test each adapter with the same suite]]).
3. **Write the code** to the [[2026-10-13 Clean-code rules enforced by tests|clean-code rules]]: DRY, constants in `tools/constants.py`, settings in `config.py`, descriptive names, core (`tools/`) free of AWS.
4. **Run the suite:** `uv run --locked pytest` from the repo root (after `uv sync`) (coverage is on). It must be green and coverage must not drop.
5. **Commit small and often.** History is graded ([[Repo change history is graded]]).
6. **Open a PR to `develop`.** Run the code-simplifier / code-review pass on the PR diff. Fix what it finds, or say why not in the PR.
7. **The lead merges into `develop`.** Nobody pushes to `develop` or `main` directly. `main` only gets releases (demo and submission builds) through a `develop` → `main` PR the lead opens.

Front end (`web/`): `cd web && yarn install --frozen-lockfile`, then `yarn start` / `yarn test` / `yarn build`. Node 22; the npm token lives only in your home `~/.npmrc` ([[2026-10-14 Two apps in one repo]]).

## Commit messages
- Subject: imperative, says what changed (`Make the run ledger create-once…`), under ~72 characters.
- Body: **why**, what a reviewer should check, and the test count / coverage after the change.
- Reference the decision (`D-0xx`) or eval (`Qxx`) it relates to.

## Before you call it done
- `uv run --locked pytest` green, coverage not lower.
- Your `AGENTS.md` row, `DECISIONS.md` entry and `HANDOFF.md` lines updated if the change affects them.
- The vault updated if you made a decision or learned something ([[Vault upkeep]]).

Related: [[Workflow]], [[Team plan]]
