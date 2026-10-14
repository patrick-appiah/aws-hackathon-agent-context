---
tags: [build, plan, area/cost]
id: A3b
owner: Abdul
spec: "[[A3b - COST measured figures - spec]]"
status: ready
updated: 2026-10-14
---
# A3b: COST.md measured per-question and scale figures (implementation plan)

> **For the executing agent (and Abdul):** follow [[How to execute a plan]] exactly, with one change: **Abdul does not run Python, uv or pytest.** Where a command is needed, ask Linus to run it and send you the output, and compare it with `Expected:`. Work the tasks in order. If anything differs from `Expected:`, stop and follow "When output doesn't match".

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[A3b - COST measured figures - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in your ledger.
3. [[A3a - Bedrock unit prices - spec]] (the unit prices it uses) and [[A5a - EVALS results write-up - spec]] (the same run's write-up).
4. [[Huvison - trust and flow]] §6–7.

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If it's still unclear, stop and ask Huvison or Linus.

**Goal:** `COST.md`'s per-question and scale rows hold measured figures from one named run, with every number traceable.

**Architecture:** `evals/results/run-*.json` (`cases[].cost_usd`, `cases[].answer.run_id`) + the ledger run item (`tokens_in`, `tokens_out`) → your calculator → `COST.md`.

**Tech stack:** VS Code (JSON search), a calculator, the AWS console read-only (DynamoDB, deployed runs), Git.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: `docs/cost-measured` from an up-to-date `develop`.
- **Start state:** H5 (cost per run) and A3a are merged: `COST.md` has "## Unit prices (on-demand, eu-west-1)" with four filled rows; the per-question table's "Units / question" and "Cost / question" cells and the Scale "Monthly cost" cells say `TODO`. Linus's `uv run --locked pytest` on `develop` gives the baseline count (≥ `204 passed`, ≥ 96%): write it down. Linus has sent you the recorded run's results file.
- **Your ledger:** `.superpowers/ledger-A3b.md` (gitignored).
- **Rules:** synthetic data only; never estimate a measured number; AWS console read-only; Markdown guard tests (no bare `` `pytest` ``, no `uv run pytest`, no `python scripts/…` without `uv run `, test files only by `tests/…` path); commits with the given messages; **no `Co-Authored-By` and no "Generated with" lines**; never push to `develop` or `main`; PR to `develop`; Linus reviews; Patrick merges.

## Review Focus (what nothing tests; check by hand at the end)
1. The average excludes refused, manual and not-applicable cases, and cases with `cost_usd` 0 or `null`.
2. The monthly figures use the **unrounded** average.
3. The Total cell equals Q01's `cost_usd` from **the same** file the "Measured on" line names.
4. Token cells come from the ledger or Huvison, never back-calculated from cost.
5. Every "not measured" cell says why.

---

### Task 1: Collect the numbers (D2 14:00–14:30)

**Files:** none (numbers in the ledger).
**Produces:** a list of `(question, status, cost_usd)` and Q01's tokens.

- [ ] **Step 1: Start the ledger, open the file.**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
mkdir -p .superpowers && printf '# Ledger: A3b measured cost\n' > .superpowers/ledger-A3b.md
```
  Open the results file Linus sent in VS Code. At the top, note `"run_at"`, `"commit"`, `"asker"`.
Expected: `"asker"` is not `null` (for example `"flow.local:ask"`). If it's `null`, the run has no costs: stop and ask Linus for the recorded run with an asker.

- [ ] **Step 2: List every case's cost.** Ctrl+F `"cost_usd"`. For each of the 14 cases, note `id`, `status` and `cost_usd` (press Enter in the find box to jump to the next match; the case `id` is a few lines above).
Expected: 14 matches (one per case) plus any inside `answer` objects (the `/ask` response also carries `cost_usd`; use the case-level one, which is next to `"seconds"`). Q10 `manual`, Q13 and Q14 `not applicable` show `null`. Q11 may show `0` or `null`. The rest show a number. Ledger: one line per case, `Q01 pass 0.0xxx`.

- [ ] **Step 3: Budget sanity.** Check every number is at most `0.5`.
Expected: all ≤ 0.5. Any above: send Huvison the question ID and value (the budget should have stopped it) and note it for the "Measured on" line.

- [ ] **Step 4: Q01's tokens.**
  - **Deployed run:** copy Q01's `"run_id"` (under its `"answer"`). AWS console (eu-west-1) → DynamoDB → Tables → `erp-portal-run-ledger` (or the prefixed name Michael gives you) → Explore table items → Query: `pk` = the run ID, `sk` = `RUN` → Run → open the item.
  - **Local run:** ask Huvison: *"For run <file name>, Q01: tokens_in and tokens_out for the run, and per model ID if H5 records it?"*
Expected: `tokens_in` and `tokens_out` (integers, `tokens_in` larger) and `cost_usd` equal to the file's Q01 cost (to 4 decimals); or Huvison's message with the same. Ledger line, with "split by model: yes/no". If Huvison says H6 doesn't expose the tokens of a local run (spec A3b-4), the ledger line is `Q01 tokens: not measured: local run, H6 does not expose tokens`.

- [ ] **Step 5 (deployed run only): AgentCore seconds.** Ask Michael: *"On the observability dashboard, how many AgentCore Runtime seconds (and vCPU / memory size) did Q01's run use?"*
Expected: a number of seconds and the runtime size, or "not available". Ledger line.

**Task done when:**
- the ledger lists all 14 cases with status and `cost_usd`;
- Q01's tokens (or "not measured: <reason>") and AgentCore seconds (or "not measured") are in the ledger.

### Task 2: Calculate (D2 14:30–14:40)

**Files:** none.

- [ ] **Step 1: The average.** Take the cases with status `pass` or `fail` and `cost_usd` above 0. Add them up, divide by how many there are.
Expected: `n` between 1 and 11 (Q01–Q09, Q11, Q12 are the automatic cases; Q11 usually has no cost), and an average. Ledger: `average = <sum> / <n> = <unrounded>`.

- [ ] **Step 2: Cheapest and dearest.** From the same cases.
Expected: two question IDs with their costs.

- [ ] **Step 3: Monthly.** `pilot = average × 200`; `full = average × 3000`, with the unrounded average. Round each to 2 decimals.
Expected: two dollar figures; `full` is exactly 15 × `pilot` (before rounding).

- [ ] **Step 4 (only if the split by model exists): per-row cost for Q01.** `Sonnet = tokens_in/1000 × Sonnet input price + tokens_out/1000 × Sonnet output price` (prices from `COST.md` "Unit prices"); the same for Nova Lite.
Expected: the two row costs add up to Q01's `cost_usd` within $0.0001. If not, send Huvison both numbers; don't adjust.

**Task done when:**
- the ledger has the average (unrounded and 4-decimal), cheapest, dearest, pilot and full monthly figures.

### Task 3: Write `COST.md` (D2 14:40–15:00)

**Files:** Modify `COST.md`.

- [ ] **Step 1: Branch.**
```bash
git switch -c docs/cost-measured
```
Expected: `Switched to a new branch 'docs/cost-measured'`.

- [ ] **Step 2: Fill "Per question".** Replace each `TODO` in the "Units / question" and "Cost / question" columns with the matching text from spec §3 (choose the "split" or the "without a split" wording from your ledger). Replace `**TODO**` in the Total row with `**$<Q01 cost_usd, 4 decimals>**`, and the row's first cell `**Total**` with `**Total (Q01 worked example)**` (it is one question; the cost per question everyone quotes is the "Measured on" average, Step 4).
Expected: Ctrl+F `TODO` in the "Per question" table finds nothing; the Total row reads `Total (Q01 worked example)` and shows Q01's cost with 4 decimals.

- [ ] **Step 3: Fill "Scale".** Replace the two `TODO` cells with `$<pilot>` and `$<full>`.
Expected: the Scale table shows two dollar figures; no `TODO`.

- [ ] **Step 4: Add the "Measured on" line** from spec §3 directly under the Scale table, every `<…>` filled from your ledger. Choose one wording in each `<a / b>` pair.
Expected: Ctrl+F `<` in `COST.md` finds nothing.

- [ ] **Step 4b: The "Value side" TODO.** In "## Value side (for the one-page value case)", replace the whole line `- TODO: confirm with Vanessa Addo how often these questions are asked per month → payback estimate.` with `- See business/business-case.md §2 (validated <date>/proposed).`, keeping one of the two words: `validated <YYYY-MM-DD>` if `business/business-case.md` on `develop` marks the sizing rows *validated* (B1's validation session), else `proposed`. Leave the rest of the section as it is.
Expected: Ctrl+F `TODO` in `COST.md` → **No results**; the Value side shows `- See business/business-case.md §2 (validated 2026-10-15).` or `- See business/business-case.md §2 (proposed).`

- [ ] **Step 5: Commit, push, ask Linus.**
```bash
git add COST.md
git commit -m "COST: measured cost per question and at pilot and full scale from run <file name>"
git push -u origin docs/cost-measured
```
  Ask Linus to run `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"` on the branch, **and** to recompute your average and the two monthly figures from the same results file.
Expected: the baseline count, no `failed` (dry-run with sample numbers on the C1 branch: `204 passed`, 96%); Linus's three numbers equal yours.

- [ ] **Step 6: PR.** Base `develop`, title `COST: measured per question and scale (A3b)`, body: the results file name, the average, n, pilot, full, Linus's output and his "recomputed: same". Reviewers: Linus, Huvison. Tell Patrick and Michael (B1, B3) the figures.
Expected: the PR page shows `COST.md` only, base `develop`.

**Task done when:**
- the PR to `develop` is open with `COST.md` only and no `TODO` left anywhere in it (Ctrl+F `TODO` → No results);
- Linus confirmed both the suite (0 failed) and the arithmetic.

## Never
- Estimate a figure that should be measured, or back-calculate tokens from cost.
- Mix numbers from two runs.
- Change the unit prices (that's A3a; if one is wrong, fix it there).
- Push to `develop` or `main`, or add attribution lines.

## Done means
- [ ] **No `TODO` left** in `COST.md` on `develop`. *Verify:* open the file on GitHub, Ctrl+F `TODO` → none; the "Value side" shows `- See business/business-case.md §2 (validated <date>)` or `(proposed)`.
- [ ] **The figures trace to one run.** *Verify:* the "Measured on" line names `evals/results/<file>`; that file is on `develop` (A5a); its Q01 `cost_usd` equals the Total cell; the average of its answered cases' `cost_usd` equals the stated average.
- [ ] **Scale = average × volume.** *Verify:* pilot ÷ 200 and full ÷ 3,000 both give the stated average (to rounding).
- [ ] **Tokens are sourced or marked "not measured".** *Verify:* the DynamoDB run item (deployed) or Huvison's message (local) shows the same `tokens_in` / `tokens_out` as the Sonnet row, or the cell says 'not measured: <reason>'.
- [ ] **The Total row is labelled as one question.** *Verify:* `COST.md` on `develop` shows `**Total (Q01 worked example)**`.
- [ ] **The PR is merged** with Linus's 0-failed output and his "recomputed: same". *Verify:* the PR from `docs/cost-measured` shows "Merged".

Related: [[A3b - COST measured figures - spec]], [[A3a - Bedrock unit prices - plan]], [[Build order]], [[How to execute a plan]]
