---
tags: [build, spec, area/cost]
id: A3b
owner: Abdul
status: awaiting review
updated: 2026-10-14
---
# A3b: COST.md measured per-question and scale figures (spec)
> **Split of A3.** [[A3a - Bedrock unit prices - spec]] puts the unit prices in `COST.md` (D1). A3b (this note, D2 14:00–15:00) fills the **measured** rows from a real eval run's results file, after Huvison's cost per run (H5) is merged. No Python: you read JSON, use a calculator and edit Markdown.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before you start, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[A3a - Bedrock unit prices - spec]] and its merged result in `COST.md`.
3. [[Abdul - evals, Cognito, docs]] §6 (pilot ~200 questions/month; 100/day).
4. [[Huvison - trust and flow]] §6 (`tools/cost.py` *(new)*, created by H5, `cost_usd(usage)`; every agent state calls `add_cost`; the total lands in `AskResponse.cost_usd`) and §7 (the local asker H6).
5. [[Build order]]: A3b depends on H5 (cost per run) and on one eval run with an asker (H6 or L6). B1 (business case `[TBC]`s) and B3 (the cost slide) wait on it.
6. `04 Reference/`: [[Pitch track grading rubric]] ("COST.md: **measured** cost per run and at 100 runs/day"), [[Judging rubric]] 3.2 (monthly run cost at pilot and full scale; cost levers).
7. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/`, `03 Sessions/`, `Open follow-ups.md`. If it's still unclear, stop and ask Huvison (cost) or Linus (the run). Never estimate a figure that should be measured; write "not measured" instead.

## 1. Intent
**What:** from one recorded eval run (`evals/results/run-*.json`, with an asker and H5 merged; the folder `evals/results/` *(new)* is created by the eval runner's first committed run, A5a's first PR):
1. **Per question:** Q01's ("what is blocking cutover for E4?", the row `COST.md` is titled after) tokens and cost; the "Units / question" and "Cost / question" cells; the **Total** row, labelled **Total (Q01 worked example)** so nobody quotes it as the average.
2. **Scale:** the average measured cost per answered question × 200 (pilot) and × 3,000 (full: 100/day × 30).
3. **A "Measured on" line** naming the results file, the commit, the asker, the number of questions answered, the average, the cheapest and the dearest question. **Its average is the team's one "cost per question"**: the business case (B1 line 34), the deck (B2 slide 9), the pitch (B3c) and `HANDOFF.md`/`DEMO.md` (A4b) all quote it.
4. **The "Value side" TODO line** is replaced by a pointer to the business case (§3), so `COST.md` has no `TODO` left.

**Why:** the rubric scores **measured** cost, and the business case (B1) and the cost slide (B3) reuse these numbers. A wrong multiplication there is visible to every judge.

**Success means:**
- `COST.md` on `develop` has no `TODO` anywhere (cells that can't be measured say "not measured" with the reason; the "Value side" TODO is replaced by the pointer).
- Every number can be traced to the named results file (cost) or the named ledger item (tokens), and the scale rows equal the average × volume.
- The results file named is committed in `evals/results/` (A5a commits it; this item only cites it).

**Assumptions (to reconcile with the owners):**
- **A3b-1:** every answered case in the results file has a numeric `cost_usd` (the runner copies `response["cost_usd"]`, `evals/run.py` `run_case`), produced by H5's price table. Refused cases (Q11) may show `0` or `null`.
- **A3b-2:** token counts per question are **not** in the results file (`AskResponse` has `cost_usd` but no token fields). They're on the ledger's run item (`sk` = `RUN`: `tokens_in`, `tokens_out`, `cost_usd`; `adapters/dynamo_ledger.py` `add_cost`). For a **deployed** run you read them in the DynamoDB console (`erp-portal-run-ledger`, `pk` = the case's `answer.run_id`); for a **local** run (H6, in-memory ledger) Huvison sends them. A split by model (Sonnet vs Nova Lite) exists only if H5 records it; otherwise you write the totals and "split by model not measured".
- **A3b-3:** AgentCore Runtime seconds per question are only measurable on the deployed run (Michael's observability dashboard). Local runs don't use AgentCore.
- **A3b-4:** for a **local** run, token counts exist only if H6 exposes them (Huvison reads them from the in-memory ledger's run item or H6's output and sends them). If H6 doesn't expose them, the token cells say `not measured: local run, H6 does not expose tokens`.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Which run | The latest run Linus marks as **recorded** (the one A5a writes into `EVALS.md`), with an asker and H5 merged; prefer the deployed-API run (L6) if it has costs, else the local one (H6), and say which | Mixing questions from different runs |
| Per-question row | **Q01** (the row title is that question) | An average in the per-question table (the average goes in the scale and the "Measured on" line) |
| Average for scale | Mean `cost_usd` over every case with status `pass` or `fail` **and** a `cost_usd` above 0 | Including refused, manual or not-applicable cases (no model calls) |
| Volumes | Pilot **200**/month (`COST.md` row); full **3,000**/month (100/day × 30) | Other volumes |
| Rounding | Per question: 4 decimals (`$0.0123`); monthly: 2 decimals (`$2.46`); compute with the unrounded average | Rounding the average first |
| Tokens unavailable | Write "not measured: <reason>" in the cell | Calculating tokens back from cost |
| Lambda / API Gateway / DynamoDB / S3 | Keep "~negligible" | Pricing them now |

## 3. The `COST.md` changes (exact)
**Per question** (the cells you fill; the unit-price column is A3a's):
| Component | Units / question | Cost / question |
|---|---|---|
| `Bedrock: Sonnet (orchestrator, analyst, critic, writer)` | `<tokens_in> input / <tokens_out> output tokens (Q01)` — or, without a split: `<run tokens_in> input / <run tokens_out> output tokens, all agents (Q01; split by model not measured)` | `$<tokens_in/1000 × in-price + tokens_out/1000 × out-price>` — or, without a split: `see Total` |
| `Bedrock: Haiku / Nova (retriever)` | `<tokens> (Q01)` — or `included in the Sonnet row (split not measured)` | `$<…>` — or `see Total` |
| `AgentCore Runtime` | `<seconds> s (deployed run)` — or `not measured (local run, no AgentCore)` | `$<…>` — or `not measured` |
| `**Total (Q01 worked example)**` | | `**$<Q01 cost_usd>**` (from the results file) |

**Scale:**
| Scenario | Volume | Monthly cost |
|---|---|---|
| Pilot: 1 programme, ~10 users, ~200 questions/month | 200 | `$<average × 200>` |
| Full: 100 questions/day across programmes | 3,000 | `$<average × 3,000>` |

**The "Measured on" line**, added right under the Scale table:
```markdown
Measured on `evals/results/<file name>` (commit `<commit>`, asker `<asker>`, <date>): <n> questions answered, average **$<average, 4 decimals>** per question; cheapest <Qxx> $<…>, dearest <Qyy> $<…>. Bedrock tokens are priced with the unit prices above (`tools/cost.py`); Lambda, API Gateway, DynamoDB and S3 are negligible at these volumes; AgentCore Runtime <is included from the deployed run / is not measured (local run)>. Every run stayed under the per-run budget of $0.50 (`RUN_BUDGET_USD`) <or: <Qzz> hit the budget and returned a partial answer>.
```
**The "Value side" TODO line** (`- TODO: confirm with Vanessa Addo how often these questions are asked per month → payback estimate.`) becomes, with B1's label on the day (`validated <YYYY-MM-DD>` if the business case's sizing rows say *validated*, else `proposed`):
```markdown
- See business/business-case.md §2 (validated <YYYY-MM-DD>/proposed).
```
(Dry-run: this line and the filled tables with sample numbers on the C1 branch → `204 passed`, 96%.)

## 4. Tests
No code. The checks:
- **Arithmetic:** a second person (Linus or Huvison) recomputes the average and both monthly figures from the same results file and gets the same numbers.
- **Trace:** Q01's `cost_usd` in the file equals the Total cell; the token cells equal the ledger item (or Huvison's message).
- **Budget sanity:** every answered case's `cost_usd` ≤ 0.50 (`config.py` `DEFAULT_RUN_BUDGET_USD`); a case above it is a finding to send to Huvison.
- **Doc guards:** Linus runs `uv run --locked pytest` on the branch → the baseline count, 0 failed.

## 5. Out of scope
- Unit prices ([[A3a - Bedrock unit prices - spec]]), the price table and `tools/cost.py` (H5).
- The "Value side" content and the business case (B1; A3b only swaps its TODO line for the pointer), the cost slide (B3).
- Committing the results file (A5a, [[A5a - EVALS results write-up - spec]]).

Related: [[Build order]], [[Abdul - evals, Cognito, docs]], [[A3b - COST measured figures - plan]]
