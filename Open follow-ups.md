---
tags: [moc]
---
# Open follow-ups
Tick with the commit/run id that closed it; never delete.

## From [[2026-10-13]]
- [ ] Talk to the problem owner + oversight (rubric 1.1 needs validation *during* the event): which 5 numbers, cost of the last "what's blocking?", who signs off the status pack #area/business
- [ ] Re-test Claude Haiku 4.5 (use-case form submitted; agreement pending) #area/bedrock
- [ ] Delete `team-credentials.txt` once all 7 teammates have their logins #area/iam
- [ ] Decide front end (D-006) by Day 1 12:00 #area/frontend
- [ ] Confirm default models (D-004) #area/bedrock
- [ ] Assign the 8 seats in [[Team plan]] to named teammates #area/team
- [x] Create the GitHub repo and push: Amali-Tech/cloud-9-hackathon, `main` @ 3cf6a14 + `feature/prompt-files` @ 1f25771 (2026-10-14) #area/repo
- [x] Merge `feature/prompt-files`: PR #1 into `develop` (2026-10-14) #area/repo
- [ ] Merge PR `seat1/develop-branch-flow` → `develop` (team plan: branch from and PR to `develop`), then regenerate [[Team plan]] and republish the team page #area/repo
- [ ] Release `develop` → `main` when the team needs a stable snapshot (`main` is 13+ commits behind) #area/repo
- [x] Commit the repo now (5 commits, 24641b6..a7a6558, on `main`; no remote yet) and keep committing; history is graded → [[Repo change history is graded]] #area/repo
- [ ] Assign owners for **pitch deck (20)**, **business case (20)** and **product spec (10)** → [[Five deliverables, not just a repo]] #area/business
- [ ] Commit one real input + output per agent in `evals/expected/` (worked examples, 4 pts) #area/agents
- [ ] Prepare for an **unseen input** from judges (guideline §05); degrade honestly #area/evals
- [ ] Confirm with organisers which rubric is final: pitch-track (13 Oct) vs proposal (9 Oct) #area/judging
- [ ] Teammate revises target diagram to v2 (7 fixes) → [[Teammate target diagram v1 review]] #area/architecture
- [ ] Bundle `agents/prompts/*.txt` + `prompts.lock` with the agent code in Lambda/AgentCore packaging, or `load_prompt` fails at runtime (final review, prompt-files branch) #area/infra
- [ ] When wiring the orchestrator/Step Functions, pass the loaded `Prompt` together with the agent into `judge()` so provenance matches the prompt actually used #area/agents
- [ ] Decide on the 9 deferred minors from the prompt-files review (see the branch's final message) #area/agents
- [ ] Write the CDK skeleton (S3, ledger, guardrail, Step Functions approval) #area/infra

- [ ] Tell Michael Part A (DEF-0462 + calendar.csv) is done on `feature/erp-planted-scenarios`; his brief is now informational
- [x] (PRs #10, #11 merged) Merge order: `feature/erp-planted-scenarios` then `refactor/erp-dataset-contract` (B is built on A); CI branch owns D-018, ours is D-019
- [ ] UI shows whole-number percentages from counts (58 %, 89 %, 103 %); handles final_cutover = None and records_sent 0
- [ ] Athena adapter must use `tools.queries.row_id` for identical citations
- [ ] Republish the team page with the new TEAM_PLAN §3 table
- [x] npm token set on the lead's WSL; clean-clone front-end install, build and tests verified (2026-10-14)
- [ ] Share the read-only npm token privately with teammates who build `web/` (never in Slack or the repo)
- [ ] Mildred: `web/scripts/build-fixtures.mjs` reads `kpis.json`, deleted in PR #11; regenerate fixtures from `metrics.portfolio_summary` instead (small spec)
- [ ] Front-end API types still follow the old summary shape (pass_rate_by_cycle, open_defects_by_age, capacity in hours); align with the new `portfolio_summary`
- [x] (Patrick + Michael, 2026-10-14) Name the business-case and pitch owner (TEAM_PLAN §2 workstream 7 says "to be confirmed")
- [ ] Write the contracts spec (Patrick, first): API shapes incl. /rows, /entity, rejected[], partial_reason, trace, /approve statuses, error body; ask-spine step I/O; new config.py settings; DevOps handover
- [ ] Draft one GitHub issue per workstream's first milestone and a project board
- [ ] Tell each teammate: read `06 Workstreams/<you>.md` (after [[Workstreams]]), and paste `prompts/<you>.txt` into your AI assistant
- [x] (Patrick, 2026-10-14: D-022, branch `fix/q09-attempt-limit`) Q09 verdict count: at most 2 attempts in total (one retry), 2 verdicts on a rejected claim; EVALS.md and Q09 files corrected
- [ ] Timeline bars: `portfolio_summary` has no timeline figure. Patrick + Linus decide whether metrics adds one (Mildred waits)
- [ ] Delete `team-credentials.txt` (IAM user credentials file) once everyone has signed in

Related: [[00 Home]]
