---
tags: [workflow, area/process]
---
# Deploy and demo checks
The checks that protect the hard gates and the demo. Full detail lives in the repo `docs/TEAM_PLAN.md`; this note is the working checklist.

## Clean-account deploy (hard gate)
- Everything is in CDK; nothing is created by hand in the console.
- The lead deploys from clean with a fresh stack prefix **twice**: Day 1 18:00 and Day 2 13:00 ([[Team plan]] §4).
- The README's 5 commands must work exactly as written.

## Go / no-go on the fallback switches (Day 2 12:00)
For each target layer (`AUTH_MODE`, `AUTHZ_MODE`, `ARTEFACT_BACKEND`, `LF_FILTERS`, `SOURCES`): green → stays on; not green → flip to fallback in SSM and write it in `HANDOFF.md`.

## Before the freeze (Day 2 14:00)
- Eval set run and recorded **with failures** (`EVALS.md`).
- One worked example per agent committed in `evals/expected/`.
- `COST.md` filled from measured ledger costs.

## Demo (Day 2 16:00–17:00)
- Rehearse twice, on the clock, from a cold start.
- Show the critic rejecting the decoy (DEF-0419) live.
- Backup video on the laptop (relying on it caps criterion 2.2 at 3).
- Pre-flight: region eu-west-1, Bedrock smoke test re-run ([[Bedrock smoke test 2026-10-13]]).

Related: [[Workflow]], [[Team plan]]
