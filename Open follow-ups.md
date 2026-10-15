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
- [x] (done by Michael, PR #71) **Yaw (Y2a §6):** route `GET /ask/{run_id}`; ask Lambda gets `states:StartExecution` (not `StartSyncExecution`) and `dynamodb:GetItem` on the ledger; ask machine timeout above the measured run time, within Express's 5 minutes (D-023) #area/flow
- [x] (PR #81) (spec: H8) **Huvison:** `write_answer` stores the `AskResponse` on the run, plus a ledger method to read it back for `ask_result` (D-023) #area/flow
- [ ] **Clement (F4b):** the ask panel polls `GET /ask/{run_id}` after `POST /ask` returns `AskPending`; wait a few seconds before the first poll (a 404 at first means the run isn't created yet) (D-023) #area/web
- [ ] **Michael:** raise the ask machine's own timeout (2 min today) as well as the step timeouts; time again after PR #65 (merged) is deployed #area/flow

### From the first eval run (2026-10-15)
- [x] (done by Patrick, PR #80: prompt v1.1.0, checked live) **Linus (analyst prompt):** one blocker per claim; the statement names only rows in its chain; every date and number is copied from a cited row or is a `figure` with its tool (D-030); keep the DEF-0412 → RC-C3-E4-customers → RB-010 chain together (Q01, Q02, Q04) #area/agents
- [x] (PR #85) **Huvison (critic, D-030):** mark the claim's figures as recomputed by code in the critic's input; drop "every figure must appear in the cited rows" from the prompt; keep rejecting numbers and dates no row shows; also `callback_handler=None` (H7) #area/agents
- [x] (PR #81) (spec: H8, parallel judging not in it) **Huvison (spine):** budget check before each critic, writer and re-plan call; a claim cap per plan; judge claims in parallel (4 orchestrator rounds, 7 critic calls in run 4) #area/cost
- [x] (PR #85) **Huvison (writer), Patrick's OK given:** when the analyst returns no claims and `metrics.open_blockers(entity)` is empty, the headline is "Nothing is blocking cutover for <entity> in the migration records", decided in code; "could not verify" stays for rejected claims (Q03) #area/agents
- [x] (built by Patrick, PR #82) **Linus with Abdul (`evals/run.py`, D-031):** check Q05 against `summary_response`'s capacity card (Tester, 133.3 %, roster rows), not `/ask` #area/evals
- [ ] **Patrick:** check whether `replan` lets a re-planned claim drift off the rejected claim's subject (run 4: claim-1 lost DEF-0412 on its retry) #area/agents

- [ ] **Patrick, after tonight's builds:** rename the 21 vault notes with commas in their names (`find . -name "*,*"`) and fix their links; tell the team first, since their agents read the old paths #area/vault

- [ ] **Clement (F4b, PR #75):** polling gives up after 60 s (`ASK_POLL_MAX_ATTEMPTS = 30` × 2 s); live runs take 129–206 s. Raise to about 5 minutes (Express's limit), e.g. 100 polls × 3 s #area/web
- [ ] **Michael (Y2b):** when the publish machine lands, switch `publish` and `approve` to real handlers in `ROUTES_WITH_REAL_HANDLERS` with `PUBLISH_STATE_MACHINE_ARN`, the ledger settings and H4's IAM (handover) #area/flow

- [ ] **Huvison with Michael (D-023 gap):** a run that fails inside the ask spine (a Lambda error, a timeout) never stores an answer, so `GET /ask/{run_id}` says "running" until the panel gives up. Add a Catch on the ask machine to a state that stores a failed `AskResponse` (partial, with the reason) through `put_answer` (L3 final review) #area/flow
- [ ] **Michael (least privilege, minor):** `POST /ask` gets ledger `GetItem` and the ledger settings but never reads the ledger; only `GET /ask/{run_id}` needs them (`api_stack.py` `_statements_for`) #area/iam

### Business documents (2026-10-15)
- [ ] **Patrick: book the validation session** with Vanessa Addo and Joseph Akayesi (15 minutes; the three questions in [[B1 - Business case figures and validation - spec]] §3). "The problem" is 8 of the business case's 20 points and needs the owner's words, validated during the event. Then lines 23 and 79 of the business case and `business/validation-session.md` #area/business
- [ ] **Michael (B2 deck), from the measured runs and D-028:**
  - "in seconds" on slides 1, 6, 8, 9 and 11 → "in minutes" (measured 2–3.5 minutes; product spec says "within 5 minutes");
  - slide 7 "Under $0.50 a question, or it stops" → capped at $0.50 plus the one model call already running (measured $0.57 and $0.61 before the H8 budget checks);
  - slide 5 "It picks from 14 different lookups" → it decides which leads to follow and which figures to compute (the retriever is a fixed lookup now, D-028);
  - slide 6 "AI assistants … gather the evidence and work out the numbers" → code fetches the records and computes every number; the AI decides where to look and connects the evidence;
  - slides 5 and 8 "open 18 days" → "open since 25 September" (the answer states the date, not a computed duration; the dashboard's "oldest 18 days" on slide 4 is fine, code computes it)
  #area/business
- [ ] **Abdul (A5a, A3b):** commit the eval results file (`evals/results/run-*.json`, with `git add -f`) and the measured average cost per question in `COST.md` ("Measured on" and the Pilot row), so the business case cites a file instead of a vault note #area/business

Related: [[00 Home]]
