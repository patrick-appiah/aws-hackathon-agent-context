---
tags: [workstream, area/team]
owner: Abdul
updated: 2026-10-14
---
# Abdul: evals, Cognito users, cost and docs
> The repo is the source of truth. Read [[Workstreams]] first. Your row: `docs/TEAM_PLAN.md` §2, workstream 4. You pair with Linus ([[Linus - API, identity, blocker-analyst]]). **None of your tasks needs Python.** Everything is JSON, Markdown, configuration or a diagram, and Linus covers the code side.

## Your job in one paragraph
You make our work **provable and presentable**:
- **the eval set:** the 14 test questions as files the eval runner reads, plus what a correct answer must contain;
- **the API request collection**, so anyone can click through every route;
- **the Cognito test users**, so we can sign in as each role (with Michael);
- **the Bedrock prices** behind `COST.md`;
- **the documents judges read:** `EVALS.md` results (honest, failures included), the worked examples per agent, the target architecture diagram v2, and your `HANDOFF.md` and `DEMO.md` lines.

The organisers' guideline calls the eval set "the single highest-leverage ninety minutes" of Day 1, and that's your first job.

## Where you sit in the architecture
```
 ★evals/inputs/Qnn.json★ ─▶ Linus's evals/run.py ─▶ the agent loop (in-process) ─▶ evals/results/<date>.json
                                                                                       └─▶ ★EVALS.md results★
 ★evals/expected/Qnn.json★ (what must appear)        ★evals/expected/agents/<agent>.json★ (worked examples)
 ★evals/api-collection/★ (Bruno) ─▶ API Gateway ─▶ Linus's handlers
 ★Cognito groups + test users★ (Michael deploys in AuthStack) ─▶ sign-in ─▶ the token's role and entity claims
 ★Bedrock prices★ ─▶ Huvison's price table ─▶ cost per run ─▶ ★COST.md★
```

## What you own
| Path | State |
|---|---|
| `evals/inputs/`, `evals/expected/` | exist (Michael, PR #16): you review them, write Q10 on Day 2, and run the manual checks |
| `evals/expected/agents/` *(new)* | worked examples per agent |
| `evals/api-collection/` *(new)* | the Bruno collection |
| `EVALS.md` "Results" and "What still fails" sections | exist, empty |
| `COST.md` unit prices and totals | exist as TODOs |
| `HANDOFF.md`, `DEMO.md` lines for evals and cost | exist |
| `docs/architecture-target-v2.png` *(new)* | target diagram v2 |

## Tools you'll use (no Python)
- **Editing files:** VS Code (or the GitHub web editor) for JSON and Markdown. To save work: in VS Code's Source Control panel, stage, commit with a clear message, then push your branch. Linus can show you once.
- **JSON check:** VS Code underlines invalid JSON in red. Fix it before committing.
- **Bruno** (https://www.usebruno.com): a free API client that stores collections as plain files in the repo.
- **AWS console, read-only:** to *look* at Cognito and the deployed API. Never create anything by hand; Michael creates everything in CDK (the clean-deploy gate).
- **Diagram:** draw.io (diagrams.net) or Excalidraw; export PNG.
- **Branch flow:**
  - `git switch develop && git pull`, then `git switch -c feature/eval-inputs`;
  - commit, push, open a PR to `develop`;
  - Patrick merges.

  Linus reviews your PRs.

## What you build

### 1. The eval set: review it and own it (D1 10:30–12:00)
**Already built (Michael, PR #16):**
- `evals/run.py` is the runner: `uv run python -m evals.run`, then `--asker <module>:<function>` once the agent loop exists.
- The 14 inputs are in `evals/inputs/QNN.json`: `id`, `question`, `scope`, `entity_id`, and optionally `inject` (`strip_citations` for Q08, `always_reject` for Q09), `kind` (`manual` for Q10) and `note`.
- The expectations are in `evals/expected/QNN.json`: `must_cite`, `should_cite`, `must_not_contain` (regular expressions), `row_fields`, `min_rejected` and `manual_check`.
- Each run writes `evals/results/run-*.json`.
- 27 of 27 data checks pass today; the answer checks show *not run* until an asker is plugged in (`EVALS.md`).

Your part:
1. **Review all 28 files against `EVALS.md`'s question table.** Check that each question, scope and entity matches, that every ID is exact, and that the `must_cite` lists are right. Report any mismatch to Michael (author) or Linus. Don't edit `evals/run.py`.
2. **Q10, on Day 2:** a teammate picks an unseen question. You record it in `evals/inputs/Q10.json`, and its answer and whether it "degraded honestly" in `EVALS.md`. It's `kind: manual`.
3. **The three manual checks after every run** (from `EVALS.md` "What still fails"):
   - **Q02:** does the answer *flag* the conflict, not just avoid the word "ready"?
   - **Q09:** how many verdicts are on the rejected claim? `EVALS.md` says 3, but `config.py` `max_claim_attempts = 2`. **Ask Huvison** to confirm the number, and record the answer in `EVALS.md`. Don't guess.
   - **Q11:** no E2 rows in the ledger.

   Linus or Huvison shows you where to look.

### 2. The results write-up after every run
Each `uv run python -m evals.run` writes `evals/results/run-*.json` (Linus or Michael runs it). From that file, add one row to `EVALS.md` "Results" (date, commit, prompt versions, pass, fail, notes), and update "What still fails" honestly.

### 3. Worked examples per agent: `evals/expected/agents/<agent>.json`
Once the agents run (D2), capture **one real input and its real output** per agent (orchestrator, retriever, blocker-analyst, critic, writer) from a run. Linus shows you where they're printed. This is scored ("worked examples"). Real outputs only, never hand-written.

### 4. The API request collection: `evals/api-collection/` (Bruno)
- One request per route: `GET /summary`, `GET /entity/E4`, `GET /rows?cite=defect_log:DEF-0412`, `POST /ask {"entity_id":"E4","question":"What is blocking cutover for E4?"}`, `POST /publish {"run_id": ...}`, `POST /approve {"run_id": ..., "decision": "approve", "note": ""}`.
- **Three environments:** `cfo`, `e4-lead` and `no-token`. Each holds the base URL and a token variable; tokens are pasted locally and **never saved in the files**.
- For each route, save the example response from Patrick's schema (`tools/api_schema.py` *(new)*), so the front end can compare. Expected: the E4 lead gets **403 on E2**, and `no-token` gets **401**.

### 5. Cognito groups and test users (with Michael)
- **Groups:** `cfo`, `sponsor`, `delivery_lead`, `entity_lead`. **Each user is in exactly one group.**
- **Custom attributes:** `custom:tenant_id` (`t-01`) and `custom:entity_ids`, a **comma-separated string**: `*` for the CFO, sponsor and delivery lead; `E4` for the E4 lead; `E2` for the E2 lead.
- **Test users:** one per role, plus a second entity lead (E2) for the scope demo.
- **Write the list** (usernames, groups, attributes, **no passwords**) into `HANDOFF.md`. Michael creates them in AuthStack (CDK), not by hand.
- **Passwords:** Patrick shares them privately. Never in the repo, the vault or Slack.

### 6. Bedrock prices for `COST.md`
- For each model ID in `config.py` (`eu.anthropic.claude-sonnet-4-6`, `eu.amazon.nova-lite-v1:0`, and Haiku 4.5 if it activates), find the on-demand price per 1,000 input and output tokens in **eu-west-1** on the AWS Bedrock pricing page.
- Put them in `COST.md`'s unit-price column with the source link and the date you checked. Send the table to Huvison for the price table in code.
- After the D2 eval run, fill the per-question and scale rows from the measured `cost_usd` in `evals/results/<date>.json`: pilot ~200 questions/month, and 100/day.

### 7. Documents
- **`EVALS.md` "Results" and "What still fails":** one row per eval run (date, commit, prompt versions, pass, fail, notes) from Linus's results file. **Write failures honestly:** a perfect `EVALS.md` is treated as a missing one.
- **Target diagram v2** (`docs/architecture-target-v2.png`): based on `ARCHITECTURE.md` §3b. Show Cognito federation, Verified Permissions, Athena + Glue, Lake Formation row filters, connectors + EventBridge and CloudTrail, with the roadmap phase on each box (`ARCHITECTURE.md` §6 table). Review it with Patrick.
- **`HANDOFF.md`:** the test users, what the evals cover, what fails. **`DEMO.md`:** the eval and cost lines.
- **Prompt wording review:** read `agents/prompts/*.txt` and send wording suggestions to each owner. The files are locked; only the owner edits and re-locks them.

## Dependencies
- **You wait on:**
  - **The agent loop** (an asker) for answer checks. Until then, only the data checks run.
  - **Patrick's schema** for example responses. Until then, use `web/src/app/core/api/fixtures/*.json` as a guide.
  - **Michael** for the Cognito deploy.
  - **The first eval run** (D2) for results and worked examples.
- **Waiting on you:** Huvison (prices), the front end (the request collection), the business case (cost figures).

## Your milestones
| When | Milestone |
|---|---|
| D1 12:00 | All 28 eval files reviewed against `EVALS.md`; mismatches reported |
| D1 18:00 | Bruno collection with example responses; Cognito groups and users agreed with Michael; prices in `COST.md` |
| D2 12:00 | Test users signed in end to end |
| D2 14:00 | Worked examples captured; Q10 written |
| D2 15:00 | `EVALS.md` results + what still fails; `COST.md` measured; target diagram v2; `HANDOFF.md`/`DEMO.md` lines |

## Definition of done
- [ ] Eval files reviewed; Q10 recorded on Day 2; the manual checks (Q02, Q09, Q11) written into `EVALS.md` after each run.
- [ ] Bruno collection covers all six routes and three users, with no tokens in the files.
- [ ] Cognito test users per role exist (deployed by Michael); the list is in `HANDOFF.md`, no passwords.
- [ ] `COST.md` has sourced unit prices and measured totals.
- [ ] `EVALS.md` results and failures written; worked examples for all five agents.
- [ ] Target diagram v2 reviewed by Patrick.

## Rules and pitfalls specific to you
- **No passwords or tokens in any file,** ever (including Bruno environments).
- **Never create AWS resources by hand.** Ask Michael to add them in CDK.
- **Copy IDs exactly** (`RC-C3-E4-customers`, `E4#RB-010`). The runner matches them character for character.
- **Results are reported as they are.** Never round a failure into a pass.

## Getting started
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
git switch -c docs/eval-review
# open the folder in VS Code; read evals/inputs/Q01.json and evals/expected/Q01.json next to EVALS.md
```
Then give your assistant `06 Workstreams/prompts/abdul.txt`.

## Who to ask
| Topic | Person |
|---|---|
| Runner, worked examples, Git | Linus, Michael (runner author) |
| Verdict count, prices | Huvison |
| Cognito | Michael |
| Diagram, schema, priorities | Patrick |

Related: [[Workstreams]], [[Team plan]]
