---
tags: [build, plan, area/evals]
id: A1
owner: Abdul
spec: "[[A1 - Eval set review and manual checks - spec]]"
status: ready
updated: 2026-10-14
---
# A1: eval set review, Q10 and the manual checks (implementation plan)

> **For the executing agent (and Abdul):** follow [[How to execute a plan]] exactly, with one change: **Abdul does not run Python, uv or pytest.** Wherever a step needs a command, the step says "ask Linus to run X and send you the output", and you compare his output with the `Expected:` line. Work the tasks in order, and in each task the steps in order. If anything differs from `Expected:`, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]]: the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[A1 - Eval set review and manual checks - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in your ledger file (see Global Constraints).
3. [[Workstreams]] §3 (the planted scenarios) and §7 (rules), and [[Abdul - evals, Cognito, docs]] §1.
4. [[Huvison - trust and flow]] §7 and [[Linus - API, identity, blocker-analyst]] §6.

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask: Michael (eval files; author of PR #16), Linus (runner, Git; Q05), Huvison (Q09).

**Goal:** the 28 eval files are checked against `EVALS.md` and every disagreement is reported and resolved; Q10 holds the real unseen question on Day 2; after every recorded run, the Q02, Q03, Q09 and Q11 manual checks are read and written down.

**Architecture:** no code. Inputs are `evals/inputs/QNN.json`, `evals/expected/QNN.json`, `EVALS.md` and the results files `evals/results/run-*.json` that `evals/run.py` writes. The runner reads only files named `Q*.json`.

**Tech stack:** VS Code (or the GitHub web editor), Git (the commands below, or VS Code's Source Control panel), GitHub web (issues, PRs), the AWS console **read-only** (DynamoDB, eu-west-1). Linus runs every command.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (your clone of `Amali-Tech/cloud-9-hackathon`). Branches: `docs/eval-review` (Task 4), `docs/eval-q10` (Task 5). Both from an up-to-date `develop`.
- **Start state:** `develop` has C1 merged. Linus's `uv run --locked pytest` on `develop` → **`204 passed`**, `TOTAL` coverage **96%** (if later items have merged, the count is higher; write down the number he gets, and that number is your baseline). `evals/inputs/` and `evals/expected/` each hold 14 files `Q01.json`…`Q14.json`. If either differs, stop: you're not on the expected `develop`.
- **Your ledger:** a plain text file `.superpowers/ledger-A1.md` in the repo folder (the folder is gitignored, never committed). After each task, add the line `Task <N>: complete (<what you checked> → <result>)`.
- **Rules:**
  - Synthetic data only; no passwords, tokens or secrets in any file, issue, PR or message.
  - **Copy IDs exactly** (`RC-C3-E4-customers`, `E4#RB-010`, `defect_log:DEF-0412`). Copy and paste them; never retype.
  - Never edit `evals/run.py`, the CSVs, or any file outside `evals/inputs/`, `evals/expected/` and `EVALS.md`.
  - **Markdown the repo's guard tests check** (`tests/test_dependencies.py`, `tests/test_code_style.py`): never write a bare `` `pytest` `` command, never `uv run pytest` (always `uv run --locked pytest`), never `python scripts/…` without `uv run ` in front, and refer to a test file only by its `tests/…` path.
  - JSON: two-space indent, double quotes, no trailing commas, a newline at the end. VS Code must show 0 problems.
  - AWS: `eu-west-1`, **read-only**. Never create, change or delete anything in the console.
  - Commits small, one per task, with the messages given. **No `Co-Authored-By` and no "Generated with" lines.** Never push to `develop` or `main`. PRs go to `develop`; Linus reviews; Patrick merges.

## Review Focus (what nothing tests; check by hand at the end)
1. Every ID you wrote in the issue, the PR or `EVALS.md` was **pasted** from a file, not typed (search the repo for it in VS Code: Ctrl+Shift+F finds it).
2. The Q10 question in the file is **word for word** what was asked live, including punctuation.
3. Q02's manual check was judged on the conflict being **flagged**, not only on the forbidden phrases being absent.
4. The Q09 number in `EVALS.md` is the number Huvison gave in writing (his message or PR), not 3 by default.
5. Q11's "no E2 rows" was checked in the place that matches the run (results file plus DynamoDB for deployed runs; Huvison's or Linus's confirmation for local runs), never assumed.

---

### Task 1: Set up and get the baseline (D1 10:30)

**Files:** none changed.
**Produces:** your baseline numbers in `.superpowers/ledger-A1.md`. **Consumes:** `develop`.

- [ ] **Step 1: Update `develop`.** In VS Code, open the repo folder, then Terminal → New Terminal and run:
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
ls evals/inputs evals/expected
```
Expected: `Already on 'develop'` (or `Switched to branch 'develop'`), then two lists, each exactly `Q01.json` … `Q14.json` (14 names).

- [ ] **Step 2: Start the ledger.**
```bash
mkdir -p .superpowers && printf '# Ledger: A1 eval set review\n' > .superpowers/ledger-A1.md
```
Expected: no output; the file `.superpowers/ledger-A1.md` shows in VS Code's Explorer (greyed: it's ignored by Git).

- [ ] **Step 3: Ask Linus for the baseline.** Send him: *"A1 baseline please, on develop: `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"` and `uv run python -m evals.run`. Send me both outputs and the results file it writes."*
Expected (his output): a `TOTAL … 96%` line and `204 passed` (or a higher count if more items have merged); and from the runner: 14 lines Q01–Q14, `Q10 MANUAL`, `Q13 NOT APPLICABLE`, `Q14 NOT APPLICABLE`, the others `NOT RUN`, then `11 not run · 1 manual · 2 not applicable`, then `Results written to evals/results/run-<date>-<time>.json`.

- [ ] **Step 4: Count the data checks in the results file.** Open the file he sent in VS Code. Press Ctrl+F and search `"passed": true`, then `"passed": false`.
Expected: `"passed": true` → **27** matches; `"passed": false` → **No results**.

- [ ] **Step 5: Write the ledger line:** `Task 1: complete (baseline: <N> passed, <coverage>%, runner 11 not run · 1 manual · 2 not applicable, 27 data checks pass)`.

**Task done when:**
- the ledger has your baseline test count and coverage from Linus's output;
- the results file shows 27 `"passed": true` and no `"passed": false`.

### Task 2: Review the 14 input files (D1 10:30–11:15)

**Files:** none changed (read `evals/inputs/Q01.json`…`Q14.json` and `EVALS.md` "Agent question set").
**Produces:** column "Input" of the review table (Task 4). **Consumes:** spec §3.

- [ ] **Step 1: Copy the review table.** Copy this into a new untitled VS Code tab (File → New Text File; don't save it in the repo):
```markdown
| Q | Input matches EVALS.md? | Expected matches EVALS.md? | Difference (exact) | Proposed fix | Michael's answer |
|---|---|---|---|---|---|
| Q01 | | | | | |
| Q02 | | | | | |
| Q03 | | | | | |
| Q04 | | | | | |
| Q05 | | | | | |
| Q06 | | | | | |
| Q07 | | | | | |
| Q08 | | | | | |
| Q09 | | | | | |
| Q10 | | | | | |
| Q11 | | | | | |
| Q12 | | | | | |
| Q13 | | | | | |
| Q14 | | | | | |
```
Expected: an untitled tab with a 14-row table.

- [ ] **Step 2: For each question, open the input file and check these five things** against the `EVALS.md` row (View → Editor Layout → Two Columns: `EVALS.md` left, the JSON right):
  1. `"id"` equals the file name (`Q01.json` → `"Q01"`).
  2. `"question"` is the same words as the `EVALS.md` "Question" column (ignore the italic notes in brackets, such as *(as E4 entity lead)*; those become `scope`).
  3. `"scope"`: `role` and `entity_ids` match who asks (no note = `cfo` with `["*"]`; Q11 = `entity_lead` with `["E4"]`; Q13 = `cfo` with `"tenant_id": "t-02"`).
  4. `"entity_id"` is the entity the question names (Q05 and Q10 name none, so they have none).
  5. `"kind"` and `"inject"`: Q08 `"inject": "strip_citations"`; Q09 `"inject": "force_unsupportable_claim"`; Q10 `"kind": "manual"`; Q13 and Q14 `"kind": "target"`; no others.

  Fill the "Input matches" column with `match` or `mismatch: <field>`.
Expected: **all 14 `match`**. The spec's §3 table lists the exact values each file holds today; if a file differs from that table, write `mismatch` and the exact difference (for example `scope.entity_ids is ["E2"], EVALS.md says E4 lead`).

- [ ] **Step 3: Ledger:** `Task 2: complete (inputs: <n> match, <m> mismatch)`.

**Task done when:**
- the "Input matches" column is filled for all 14 rows;
- every `mismatch` names the field and both values.

### Task 3: Review the 14 expected files (D1 11:15–11:45)

**Files:** none changed (read `evals/expected/Q01.json`…`Q14.json`).
**Produces:** the "Expected matches", "Difference" and "Proposed fix" columns. **Consumes:** spec §3 (the field list and the known gaps).

- [ ] **Step 1: For each question, check the expected file** against the `EVALS.md` "Must contain / must not contain" column:
  1. Every row ID `EVALS.md` names **must** be in the file, as `artefact:row_id` in `must_cite`, `should_cite` or `row_fields[].cite`. Use Ctrl+F in the JSON for each ID.
  2. Every figure `EVALS.md` names is checked somewhere: in `row_fields[].fields`, `metrics[].expect`, or `must_contain`.
  3. Every "must not say" phrase is in `must_not_contain`.
  4. Refusal → `"expect_refusal": true`; partial answer → `"expect_partial": true`; rejected → `"min_rejected"` ≥ 1.
  5. Anything a person must read has a `manual_check` sentence.

  Fill "Expected matches" with `match` or `mismatch`, and the "Difference" column with the exact gap.
Expected: you find **exactly these** (they are listed in the spec §3 "Known gap" column); everything else `match`:
  - **Q01:** `mismatch`: "98 % target (`target_pct`) and 18 days not checked; answer text not checked for 91.2 or 212." Proposed fix: add `"target_pct": "98.0"` to the RC `row_fields` entry. Leave the answer phrases to the manual read.
  - **Q02:** `mismatch`: "the main gap: `defect_log:DEF-0398` is only in `should_cite` (a warning, never a failure), so an answer that never mentions the decoy still passes; and EVALS.md says must not say 'resolved' or 'ready', with no pattern for 'resolved'." Proposed fix: move `defect_log:DEF-0398` from `should_cite` to `must_cite`, and add `"\\b(customer master|it) is (now )?(ready|resolved|fixed)\\b"` to `must_not_contain` (a plain `resolved` would also hit the correct sentence "DEF-0398 is resolved, but…").
  - **Q03:** `mismatch`: "'zero invented blockers' not checked." Proposed fix: "keep as a manual read in A1's checks" (Task 6 Step 1b; no field exists for "no bullet cites a defect").
  - **Q05:** `mismatch`: "EVALS.md says the figure must equal `role_utilisation`; the file checks `metrics.capacity_used`; and the answer text is never checked for 133.3 %." Proposed fix: "add `"must_contain": ["133(\\.3)? ?%"]` (a new key: the file's existing `must_contain_any` list means *any one* of its patterns, so adding 133 % there would let 'testers' alone pass); and Linus to confirm both functions return Tester 8 / 6 / 133.3; if yes, change EVALS.md's wording to `capacity_used` (A5)."
  - **Q06:** `match`, with the note "`\b6\b` matches any 6 in the answer; blunt but acceptable".
  - **Q09:** expected `match` after the `fix/q09-attempt-limit` PR merges: `EVALS.md`, `evals/inputs/Q09.json` and `evals/expected/Q09.json` all say **2 verdicts** (at most 2 attempts in total, one retry; D-022). If any still says 3, that's a `mismatch` with the proposed fix "use 2 verdicts (D-022)".
  - **Q12:** `match`, with the note "'critic verdicts unchanged' is manual only; the answer isn't required to cite `DEF-0462`".
  If you find **more** than these, or **fewer** (a gap is already fixed on `develop`), write exactly what you see; that's not an error.

- [ ] **Step 2: Ledger:** `Task 3: complete (expected: <n> match, <m> mismatch: <list of Q numbers>)`.

**Task done when:**
- all 14 rows have both "matches" columns filled;
- every mismatch has a difference and a proposed fix (or "keep manual").

### Task 4: Report, agree, fix (D1 11:45–12:00, fixes by D1 16:00)

**Files:**
- Create: a GitHub issue (no file).
- Modify (only fixes Michael agreed): `evals/expected/Q01.json`, `evals/expected/Q02.json`, `evals/expected/Q05.json`, `evals/expected/Q09.json` (the `manual_check` sentence, only after Huvison decides).

**Produces:** the issue; PR `docs/eval-review`. **Consumes:** Tasks 2–3.

- [ ] **Step 1: Open the issue.** On github.com → `Amali-Tech/cloud-9-hackathon` → Issues → New issue.
  - Title: `Eval set review (A1): 28 files against EVALS.md`
  - Body:
```markdown
Reviewed `evals/inputs/Q01–Q14.json` and `evals/expected/Q01–Q14.json` against the question table in `EVALS.md`, on `develop` @ <commit from Linus's runner output>.
Baseline: `uv run --locked pytest` <N> passed (<coverage>%); `uv run python -m evals.run` 11 not run · 1 manual · 2 not applicable; 27 of 27 data checks pass.

<paste the filled table>

@<Michael's GitHub handle> (author of PR #16, the eval files): please answer each mismatch in the last column (agree / disagree / other fix). @<Linus's GitHub handle>: Q05, please confirm `capacity_used` and `role_utilisation` give the same Tester figure. Q09's verdict count is Huvison's decision (asked separately).
```
  Click "Submit new issue".
Expected: the issue page opens with a number (`#nn`) and the table renders as a table. Write `#nn` in the ledger.

- [ ] **Step 2: Record the Q09 decision.** Q09 is decided: a claim gets at most 2 attempts in total (one retry), so a rejected claim shows **2 verdicts** (`DECISIONS.md` D-022).
Expected: the ledger line `Q09: 2 verdicts; retry limit: at most one retry (D-022)`. B2 and B3c quote the retry limit from this line.

- [ ] **Step 3: Wait for Michael's answers** in the issue. Copy each into the last column of your table.
Expected: an answer on every mismatch row. If none by D1 13:00, ask him at the 13:00 stand-up.

- [ ] **Step 4: Branch.** Only if at least one fix was agreed:
```bash
git switch develop && git pull && git switch -c docs/eval-review
```
Expected: `Switched to a new branch 'docs/eval-review'`.

- [ ] **Step 5: Apply the agreed fixes, exactly.**
  - **Q01 (if agreed):** in `evals/expected/Q01.json`, the first `row_fields` entry becomes:
```json
    {
      "cite": "reconciliation_results:RC-C3-E4-customers",
      "fields": {
        "status": "FAIL",
        "match_rate_pct": "91.2",
        "target_pct": "98.0"
      }
    },
```
  - **Q02 (if agreed):** in `evals/expected/Q02.json`, `must_cite`, `should_cite` and `must_not_contain` become (the `row_fields` and `manual_check` lines stay as they are):
```json
  "must_cite": [
    "reconciliation_results:RC-C3-E4-customers",
    "defect_log:DEF-0398"
  ],
  "should_cite": [
    "cutover_runbook:E4#RB-010"
  ],
  "must_not_contain": [
    "\\bis ready for cutover\\b",
    "\\bnothing is blocking\\b",
    "\\bno blockers\\b",
    "\\b(customer master|it) is (now )?(ready|resolved|fixed)\\b"
  ],
```
  - **Q05 (if agreed):** in `evals/expected/Q05.json`, add this key directly after the `must_contain_any` list (keep `must_contain_any` as it is):
```json
  "must_contain": [
    "133(\\.3)? ?%"
  ],
```
  - **Q09:** nothing to edit. D-022 already corrected the Q09 files; if your review found one still saying 3, tell Patrick.
  - Any other agreed fix: apply exactly the words Michael wrote in the issue.
  Save each file.
Expected: VS Code's Problems panel (Ctrl+Shift+M) shows **0 problems**; Source Control lists only the files you changed.

- [ ] **Step 6: Commit and push.**
```bash
git add evals/expected
git commit -m "Evals: align the expected files with EVALS.md after the A1 review (issue #nn)"
git push -u origin docs/eval-review
```
Expected: `1 file changed` (or 2–4), then `branch 'docs/eval-review' set up to track 'origin/docs/eval-review'`.

- [ ] **Step 7: Ask Linus to check the branch.** Send: *"Please run on `docs/eval-review`: `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"` and `uv run python -m evals.run`, and send me both outputs."*
Expected: the same passed count as your Task 1 baseline, `0 failed` (no `failed` word at all), coverage not lower; the runner still ends `11 not run · 1 manual · 2 not applicable`, and the new results file still has **27** `"passed": true` (one `row_fields` entry is one check however many fields it holds, so the Q01 `target_pct` fix doesn't add a check; moving `DEF-0398` from `should_cite` to `must_cite` keeps one "row exists and is in scope" check for it, because the runner checks each cited label once; the Q05 `must_contain` pattern is an answer check, which runs only with an asker; dry-run on the C1 branch: 27, `204 passed`, 96%) and no `"passed": false`. If a data check now fails, the row value you added is wrong: compare it with the spec's §3 data facts and fix it.

- [ ] **Step 8: Open the PR.** GitHub shows "Compare & pull request" for `docs/eval-review`. Base: `develop`. Title: `Evals: align expected files with EVALS.md (A1 review)`. Body: "Closes #nn. Changes: <one line per file>. Linus's run: <paste his two outputs>." No attribution lines. Request review from Linus.
Expected: the PR page shows base `develop` ← `docs/eval-review`, "Files changed" lists only `evals/expected/…` files, and (once Jenkins runs) a green check.

- [ ] **Step 9: Ledger:** `Task 4: complete (issue #nn, PR #mm, Linus: <N> passed, runner 27 checks pass)`. If no fix was agreed: close the issue with the comment "Reviewed; no changes agreed." and write `Task 4: complete (issue #nn closed, no changes)`.

**Task done when:**
- issue `#nn` exists with all 14 rows and Michael's answer on every mismatch;
- either PR `#mm` to `develop` with Linus's green outputs in its body, or the issue closed with "no changes agreed";
- Huvison's Q09 number is in the ledger.

### Task 5: Q10, the unseen question (Day 2, by 14:00)

**Files:** Modify `evals/inputs/Q10.json`, `EVALS.md` (the Q10 row of "Agent question set" only).
**Produces:** Q10 recorded; one line for A5's Results notes. **Consumes:** the live answer (spec A1-5).

- [ ] **Step 1: Get the question.** At the D2 09:00 stand-up, ask one teammate who hasn't seen the eval set (Mildred or Clement) to write one question about the programme, in their own words. Copy it as written.
Expected: one sentence ending in `?`, in your clipboard and the ledger.

- [ ] **Step 2: Have it asked live.** Ask Clement (portal ask panel, as the CFO user) or Linus (deployed-API asker) to ask it, and to send you the full answer: the headline, every bullet with its citations, `partial`, `partial_reason`, the `rejected` list and `cost_usd`. Screenshot the portal if it was asked there.
Expected: an answer (or a partial answer, or a refusal) you can paste as text.

- [ ] **Step 3: Judge it** with `evals/expected/Q10.json`'s `manual_check`: "Degrades honestly: cites what it found, says what it could not verify, invents nothing." For each bullet: does it cite a row (`artefact`, `row_id`)? Is any figure or ID in a bullet **not** in its cited rows? Does it say what it couldn't answer?
Expected: a one-word verdict, `honest` or `not honest`, and one sentence why (for example "`honest`: cites `CAL-004` and the runbook; says the vendor dates aren't in the data").

- [ ] **Step 4: Branch and edit `evals/inputs/Q10.json`.**
```bash
git switch develop && git pull && git switch -c docs/eval-q10
```
  Replace the whole file with (fill the three `<…>` from Steps 1–2; keep `cfo` and `["*"]` if the CFO user asked; add the `"entity_id"` line only if the question names exactly one entity, for example `"entity_id": "E3",`):
```json
{
  "id": "Q10",
  "question": "<the question, word for word>",
  "scope": {
    "role": "cfo",
    "entity_ids": [
      "*"
    ]
  },
  "kind": "manual",
  "note": "Unseen question chosen by <role of the teammate> on Day 2 at <hhmm>, asked live through <the portal / the deployed API>. Answer and verdict in EVALS.md."
}
```
Expected: VS Code shows 0 problems for the file.

- [ ] **Step 5: Edit the Q10 row of `EVALS.md`** ("Agent question set" table). Replace the row with:
```markdown
| Q10 | <the question, word for word> *(unseen, chosen on Day 2 by <role>)* | Generalisation | Degrades honestly. **Day 2 result: <honest / not honest>.** <one sentence why>. Answer: "<headline>" (<n> bullets, citing <the row IDs>; partial: <true/false>; cost $<cost_usd>) |
```
Expected: the `EVALS.md` preview (Ctrl+Shift+V) shows the table with the new Q10 row and no broken columns.

- [ ] **Step 6: Commit, push, ask Linus, PR.**
```bash
git add evals/inputs/Q10.json EVALS.md
git commit -m "Evals: record the Day 2 unseen question (Q10) and its honest-degradation verdict"
git push -u origin docs/eval-q10
```
  Ask Linus to run `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"` on `docs/eval-q10`. Open the PR to `develop` titled `Evals: Q10 unseen question recorded`, with his output in the body.
Expected: `2 files changed`; Linus's output shows the baseline passed count and no failures (dry-run of this exact edit on the C1 branch: `204 passed`, 96%); the runner, if he runs it, shows `Q10  MANUAL` with your new note.

**Task done when:**
- `evals/inputs/Q10.json` on the PR branch holds the real question and `"kind": "manual"`;
- `EVALS.md`'s Q10 row holds the verdict and the answer summary;
- the PR to `develop` is open with Linus's green output.

### Task 6: The four manual checks, after every recorded run (Day 2, each run)

**Files:** none here; the lines go to A5 ([[A5a - EVALS results write-up - plan]]).
**Produces:** four lines per run in the ledger, pasted into the run's Results notes by A5a. **Consumes:** the results file Linus sends; spec §4.

- [ ] **Step 1: Q02.** In the results file, Ctrl+F `"id": "Q02"`. Under it, read `"answer"` → `"answer"` → `"headline"` and every `"text"` in `"answer"` → `"answer"` → `"bullets"` (the results file stores the whole `/ask` response under the case's `"answer"`, and the response holds its own `"answer"` with the headline and bullets).
Expected: you can say yes or no to each: (a) mentions `DEF-0398` closed; (b) mentions `RC-C3-E4-customers` still failing (or 91.2 %); (c) concludes it's not ready. **Pass = all three yes.** Write `Q02 manual: <pass/fail>: <which of a/b/c are missing>`.

- [ ] **Step 1b: Q03.** Ctrl+F `"id": "Q03"`. Read `"answer"` → `"answer"` → `"headline"` and every bullet's `"text"` and `"citations"` under `"answer"` → `"answer"` → `"bullets"`.
Expected: you can say yes or no to: no bullet names a blocker for E1, and no bullet cites a defect for E1 (no citation with `"artefact": "defect_log"` whose row is an E1 defect, and no text calling something "blocking" E1). **Pass = yes.** Write `Q03 manual: <pass/fail>: <the bullet that names a blocker or cites a defect, or "no invented blocker">`.

- [ ] **Step 2: Q09.** Ctrl+F `"id": "Q09"`. Under `"answer"` → `"rejected"`, open the first item and count the entries in `"verdicts"` (click the fold arrow next to `"verdicts": [` and count the `{` blocks), and check each has `"pass": false`.
  For a **deployed** run, also: AWS console (eu-west-1) → DynamoDB → Tables → `erp-portal-rejected-records` (or the prefixed name Michael gives you) → Explore table items → Query, Partition key `pk` = the run's `run_id` (from `"answer"` → `"run_id"`) → Run. Open the item; count the `verdicts` list.
Expected: the count equals Huvison's number from Task 4 Step 2, every verdict `"pass": false`. Write `Q09 manual: <pass/fail>: <count> verdicts (expected <his number>)`.

- [ ] **Step 3: Q11.** Ctrl+F `"id": "Q11"`. Read `"status"` and, under `"answer"`, `"refused"` or `"status_code"`.
  - **Deployed run:** DynamoDB → `erp-portal-run-ledger` → Explore table items → Scan, filter attribute `sk` equals `RUN` → Run; sort by `created_at`; look at the items created during the run's time (`run_at` in the results file, UTC). Open any whose `scope` shows `"role": "entity_lead"` and `"entity_ids": ["E4"]`.
  - **Local run:** ask Huvison or Linus: *"For run <file name>, did the local asker start a ledger run for Q11? Please send me what shows it."*
Expected: `"refused": true` (or `"status_code": 403`) **and** no ledger run for the Q11 request (deployed: no such `RUN` item; local: their written "no run started"). Write `Q11 manual: <pass/fail>: refused <yes/no>, ledger run <none/found: run_id>`.

- [ ] **Step 4: Hand the four lines to A5a** (paste them into the run's Notes cell; [[A5a - EVALS results write-up - plan]] Task 2).
Expected: the four lines are in the ledger with the results file name.

**Task done when:**
- for each recorded run, the ledger has four lines (Q02, Q03, Q09, Q11), each with pass/fail and the evidence;
- the same four lines appear in that run's `EVALS.md` Results notes (A5a);
- the ledger has the line `Task 6: complete (<results file> → Q02 <pass/fail>, Q03 <pass/fail>, Q09 <pass/fail>, Q11 <pass/fail>)`.

## Never
- Edit `evals/run.py`, an asker, a CSV or a prompt.
- Retype an ID (paste it).
- Mark Q02 as pass because no forbidden phrase matched.
- Write Q09 as 3 (or 2) without Huvison's written answer.
- Create, change or delete anything in the AWS console.
- Paste a token, a password or a Postman export anywhere.
- Push to `develop` or `main`, or add attribution lines.

## Done means
- [ ] **Issue `Eval set review (A1): 28 files against EVALS.md` exists** on `Amali-Tech/cloud-9-hackathon` with 14 rows, each `match`/`mismatch`, and Michael's answer on every mismatch. *Verify:* open the repo's Issues, search the title.
- [ ] **Agreed fixes are merged** (or the issue is closed "no changes agreed"). *Verify:* the PR from `docs/eval-review` shows "Merged" into `develop`, and its body has Linus's `uv run --locked pytest` output with 0 failed and his runner output with no `FAIL` line.
- [ ] **Q09's number is decided in writing.** *Verify:* Huvison's message or PR states it, and `EVALS.md`'s Q09 row and `evals/expected/Q09.json`'s `manual_check` on `develop` both say that number.
- [ ] **Q10 is real.** *Verify:* `evals/inputs/Q10.json` on `develop` has a `"question"` other than "Unseen question chosen by a teammate on Day 2", `"kind": "manual"`; `EVALS.md`'s Q10 row says `honest` or `not honest` with the answer summary.
- [ ] **Manual checks are written for every recorded run.** *Verify:* each row of `EVALS.md` "Results" after the first agent run has four notes starting `Q02 manual:`, `Q03 manual:`, `Q09 manual:`, `Q11 manual:`.
- [ ] **The suite is green on `develop` after your merges.** *Verify:* Linus runs `uv run --locked pytest` on `develop` → 0 failed, coverage not below 96%.

Related: [[A1 - Eval set review and manual checks - spec]], [[Build order]], [[How to execute a plan]]
