---
tags: [workflow, area/process]
---
# Deploy and demo checks
The checks that protect the hard gates and the demo. Full detail lives in the repo `docs/TEAM_PLAN.md`; this note is the working checklist.

## Clean-account deploy (hard gate)
- Everything is in CDK; nothing is created by hand in the console.
- The lead deploys from clean with a fresh stack prefix **twice**: Day 1 18:00 and Day 2 13:00 ([[Team plan]] §4).
- The README's 5 commands must work exactly as written, and the front end builds: `cd web && yarn install --frozen-lockfile && yarn build` (npm token in the home `~/.npmrc`).

## Go / no-go on the Cognito slice (Day 2 12:00)
`AUTH_MODE=cognito` green → stays on; not green → `AUTH_MODE=none` (demo CFO user) and say so in `HANDOFF.md`. The other target layers are roadmap-only since D-015.

## Before the freeze (Day 2 14:00)
- Eval set run and recorded **with failures** (`EVALS.md`).
- One worked example per agent committed in `evals/expected/<agent>.json`.
- `COST.md` filled from measured ledger costs.

## Demo (Day 2 16:00–17:00)
- Rehearse twice, on the clock, from a cold start.
- Show the critic rejecting the decoy (DEF-0398 closed, RC-C3-E4-customers still failing) live.
- Backup video on the laptop (relying on it caps criterion 2.2 at 3).
- Pre-flight: region eu-west-1, Bedrock smoke test re-run ([[Bedrock smoke test 2026-10-13]]).

Related: [[Workflow]], [[Team plan]]
