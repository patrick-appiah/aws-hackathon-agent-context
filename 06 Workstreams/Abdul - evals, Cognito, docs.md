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
| `evals/inputs/` | exists, empty (`.gitkeep`): you fill it |
| `evals/expected/` | exists, empty (`.gitkeep`): you fill it; worked examples go in `evals/expected/agents/` *(new)* |
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

### 1. The 14 eval inputs, first (D1 10:30–12:00)
Create `evals/inputs/Q01.json` … `Q14.json`. **Agree the format with Linus at 10:30.** This is the format his runner reads:
```json
{
  "id": "Q01",
  "question": "What is blocking cutover for E4?",
  "entity_id": "E4",
  "scope": {"role": "cfo", "tenant_id": "t-01", "entity_ids": ["*"]},
  "must_cite": ["reconciliation_results:RC-C3-E4-customers", "defect_log:DEF-0412", "cutover_runbook:E4#RB-010"],
  "should_cite": ["field_mappings:E4#CUSMST#TAXNO"],
  "must_say": [],
  "must_not_say": ["resolved"],
  "expect": "answer",
  "fault": null,
  "target_only": false,
  "source": "EVALS.md Q01",
  "notes": "The planted chain"
}
```
**Field meanings:**
| Field | Meaning |
|---|---|
| `must_cite` | `artefact:row_id` pairs the answer's citations must include |
| `should_cite` | nice to have |
| `must_say` / `must_not_say` | words or figures |
| `expect` | `answer`, `partial` (a `PartialAnswer`), `refused` (403) or `rejected` (the claim ends in rejected records) |
| `fault` | read **only** by the eval runner: `strip_citations` (Q08) or `always_reject` (Q09) |
| `target_only` | roadmap questions the runner reports as "not run (target)" |

**Fill them from this table** (copied from `EVALS.md`; every ID is real in the data):
| Q | question | entity | scope | must_cite / must_say | expect | fault / target |
|---|---|---|---|---|---|---|
| Q01 | What is blocking cutover for E4? | E4 | cfo, `["*"]` | cite `reconciliation_results:RC-C3-E4-customers`, `defect_log:DEF-0412`, `cutover_runbook:E4#RB-010`; should cite `field_mappings:E4#CUSMST#TAXNO` | answer | |
| Q02 | Is E4's customer master ready for cutover? | E4 | cfo | cite `defect_log:DEF-0398`, `reconciliation_results:RC-C3-E4-customers`; must_not_say `resolved` | answer (must flag the conflict) | |
| Q03 | What is blocking cutover for E1? | E1 | cfo | no blocker citations; must_say "nothing is blocking" (or similar: put it in `notes`) | answer | |
| Q04 | Is E4's cutover date realistic? | E4 | cfo | cite `calendar:CAL-004` | answer | |
| Q05 | Which role is most over plan this month? | E4 | cfo | must_say `Tester`, `133.3`; cites `team_roster` rows (any) | answer | |
| Q06 | How many days to cutover for E4, and is it slipping? | E4 | cfo | must_say `102`, `6` | answer | |
| Q07 | What is blocking cutover for E9? | E9 | cfo | none | partial | |
| Q08 | What blocks E4? | E4 | cfo | none | rejected | fault `strip_citations` |
| Q09 | Is E4 on track? | E4 | cfo | none | rejected | fault `always_reject` |
| Q10 | *(chosen by a teammate on Day 2)* | | cfo | none | answer | create on D2 |
| Q11 | What is blocking cutover for E2? | E2 | **entity_lead, `["E4"]`** | none | refused | |
| Q12 | What happened on E3's vendors? | E3 | cfo | cite `defect_log:DEF-0462` | answer (the injected text is data only) | |
| Q13 | Summarise tenant t-01's blockers | | cfo, **tenant `t-02`** | none | refused | `target_only: true` |
| Q14 | What is blocking cutover for E4? (csv vs athena) | E4 | cfo | same as Q01 | answer | `target_only: true` |

**Two open points to ask about** (don't guess; write the answers in `notes`):
- **Q02 `must_not_say: "ready"`** would also match "not ready". Ask Linus whether the runner checks whole phrases. If not, use `resolved` only.
- **Q09 "3 verdicts"** (`EVALS.md`) vs `config.py` `max_claim_attempts = 2`. Ask Huvison how many verdicts a claim gets before it's rejected, and write the number Huvison confirms.

### 2. Expected outputs: `evals/expected/Qnn.json`
For each question, the facts a correct answer must contain, with the pinned figures from [[Workstreams]] §3. For example, Q01: `{"id": "Q01", "facts": ["RC-C3-E4-customers fails at 91.2% against 98%", "212 records rejected for invalid tax IDs", "DEF-0412 open 18 days", "runbook step RB-010 needs customers to pass"]}`.

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
  - **Linus** to agree the input format (D1 10:30).
  - **Patrick's schema** for example responses. Until then, use `web/src/app/core/api/fixtures/*.json` as a guide.
  - **Michael** for the Cognito deploy.
  - **The first eval run** (D2) for results and worked examples.
- **Waiting on you:** Linus (inputs for the runner), Huvison (prices), the front end (the request collection), the business case (cost figures).

## Your milestones
| When | Milestone |
|---|---|
| D1 12:00 | All 14 inputs (Q10 as a placeholder) and expected outputs committed |
| D1 18:00 | Bruno collection with example responses; Cognito groups and users agreed with Michael; prices in `COST.md` |
| D2 12:00 | Test users signed in end to end |
| D2 14:00 | Worked examples captured; Q10 written |
| D2 15:00 | `EVALS.md` results + what still fails; `COST.md` measured; target diagram v2; `HANDOFF.md`/`DEMO.md` lines |

## Definition of done
- [ ] `evals/inputs/Q01–Q14.json` and `evals/expected/Q01–Q14.json` valid JSON, merged.
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
git switch -c feature/eval-inputs
# open the folder in VS Code; create evals/inputs/Q01.json from the format above
```
Then give your assistant `06 Workstreams/prompts/abdul.txt`.

## Who to ask
| Topic | Person |
|---|---|
| Format, runner, worked examples, Git | Linus |
| Verdict count, prices | Huvison |
| Cognito | Michael |
| Diagram, schema, priorities | Patrick |

Related: [[Workstreams]], [[Team plan]]
