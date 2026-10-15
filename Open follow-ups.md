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
- [x] (PR #22 merged, 5d6ff5f, 2026-10-14) Write the contracts spec (Patrick, first): API shapes incl. /rows, /entity, rejected[], partial_reason, trace, /approve statuses, error body; ask-spine step I/O; new config.py settings; DevOps handover
- [ ] Draft one GitHub issue per workstream's first milestone and a project board
- [ ] Tell each teammate: read `06 Workstreams/<you>.md` (after [[Workstreams]]), and paste `prompts/<you>.txt` into your AI assistant
- [x] (Patrick, 2026-10-14: D-022, branch `fix/q09-attempt-limit`) Q09 verdict count: at most 2 attempts in total (one retry), 2 verdicts on a rejected claim; EVALS.md and Q09 files corrected
- [ ] Timeline bars: `portfolio_summary` has no timeline figure. Patrick + Linus decide whether metrics adds one (Mildred waits)
- [ ] Delete `team-credentials.txt` (IAM user credentials file) once everyone has signed in

## From [[2026-10-14]] (evening)
- [x] (done by Abdul, COST.md: 0.0055 / 0.0275 per 1K) **Abdul (A3a follow-up):** add the Claude Opus 4.6 price (`eu.anthropic.claude-opus-4-6-v1`) to `COST.md`'s unit-price table and its per-question row. Take it from the "Geo and In-region Cross-region Inference" row on https://aws.amazon.com/bedrock/pricing/ (Europe (Ireland)), per 1K tokens like the others, with the date checked. Opus 4.6 is now the analyst and critic model (D-025, PR #29) #area/cost
- [ ] **Linus (L5):** the blocker-analyst's `make_agent` must bound its model loop with `agents.agent_support.ModelCallBudget` and set `MODEL_CALL_BUDGET_ATTRIBUTE`, as the `AgentFactory` contract in `agents/retriever.py` requires (P2 re-review, 2026-10-14). P2 passes the analyst the scope narrowed to the question's entity #area/agents
- [ ] **Linus (L5), Huvison (critic, writer):** Strands 1.60 does not raise when the Bedrock Guardrail intervenes; the turn ends with `stop_reason == "guardrail_intervened"`. Treat that stop reason as a failure (the critic fails closed; the analyst and writer return nothing usable), as P2 does (final review I-1, 2026-10-14). Note: Bedrock reports the same stop reason when it only *masks* PII (ANONYMIZED); to tell blocked from masked, read the guardrail trace (Strands `_should_redact_guardrail_content`). Huvison (H7): check in the live runs whether masking ever fires on agent output #area/agents
- [ ] **Huvison (H2b `run_orchestrator`):** call `replan` with a `BlockerClaim` (`BlockerClaim.model_validate(stored["claim"])`) and the latest verdict dict; budget the Lambda timeout against the Express 5-minute ceiling; don't put `plan.steps[].reason` (model text) into large state payloads uncapped #area/flow
- [x] (done, PR #58) **Patrick (P2 follow-up), after the live measurement:** the orchestrator's `retrieve` tool returns every row in full (~5.4k tokens per entity fetch, resent on each later model call, ~30k+ input tokens per run). Measure it in the live run; if confirmed, return a lead digest instead (`{artefact, row_id}` plus the lead-bearing fields and status; full rows still go to the analyst in code), prompt v1.1.0 #area/cost
- [ ] **Linus:** review PR #57 (Patrick patched `agents/blocker_analyst.py` reply parsing after the live run: claims are read from the first JSON object with a "claims" key, prose around it allowed) #area/agents
- [x] (done, PR #63) **Patrick (P2):** one `analyse` call per plan (the live run analysed twice over the full evidence, most of the $0.46); "6 steps" is hard-coded in prompt v1.1.0 #area/cost
- [ ] **Huvison (H7):** when `critic.make_agent` moves onto `bedrock_model`, set `callback_handler=None` (the third live run streamed the critic's raw reasoning to stdout and the Lambda logs) #area/agents
- [ ] **Huvison (spine):** budget check before each critic, writer and re-plan call, and a cap on claims per plan: the third live run's re-plans after unreadable verdicts took it to $0.62 of $0.50 (see [[Whole-code review 2026-10-14]]) #area/cost
- [x] (decided: D-023, async) **Huvison (H7):** `/ask` took 87 s end to end (third run: 2 min 42 s) — the sync API cannot fit 29 s; D-023 (async /ask) is triggered #area/flow
- [ ] Ask the organisers to enable Claude Opus 5.5, Sonnet 5.5 and Haiku 5.5 (eu-west-1, `eu.anthropic.claude-*-5-5`) in account 796973512193; then re-test; per D-026 a 5.5 model replaces a default only when evals or cost show the needs (D-025 target) #area/bedrock
- [x] (2026-10-14) Anthropic use-case form submitted; Opus 4.6, Sonnet 4.6 and Haiku 4.5 answer in the new account #area/bedrock
- [x] (2026-10-14, account moved to AmaliTech-email sign-in) Delete `team-credentials.txt` once everyone has signed in: obsolete; delete the file #area/iam

## From [[2026-10-15]]
- [ ] **Linus (L3):** `api.ask` returns `AskPending` `{run_id, status: "running"}` after `states:StartExecution`; new `api.ask_result` for `GET /ask/{run_id}`: the stored `AskResponse`, else `AskPending`; scope check against the run's stored scope; 404 for a run the ledger doesn't hold (D-023) #area/api
- [ ] **Yaw (Y2a §6):** route `GET /ask/{run_id}`; ask Lambda gets `states:StartExecution` (not `StartSyncExecution`) and `dynamodb:GetItem` on the ledger; ask machine timeout above the measured run time, within Express's 5 minutes (D-023) #area/flow
- [ ] **Huvison:** `write_answer` stores the `AskResponse` on the run, plus a ledger method to read it back for `ask_result` (D-023) #area/flow
- [ ] **Clement (F4b):** the ask panel polls `GET /ask/{run_id}` after `POST /ask` returns `AskPending`; wait a few seconds before the first poll (a 404 at first means the run isn't created yet) (D-023) #area/web
- [ ] **Michael:** raise the ask machine's own timeout (2 min today) as well as the step timeouts; time again after PR #65 (merged) is deployed #area/flow

Related: [[00 Home]]
