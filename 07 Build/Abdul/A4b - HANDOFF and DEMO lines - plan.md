---
tags: [build, plan, area/docs]
id: A4b
owner: Abdul
spec: "[[A4b - HANDOFF and DEMO lines - spec]]"
status: ready
updated: 2026-10-14
---
# A4b: the HANDOFF.md and DEMO.md lines for evals and cost (implementation plan)

> **For the executing agent (and Abdul):** follow [[How to execute a plan]] exactly, with one change: **Abdul does not run Python, uv or pytest.** Where a command is needed, ask Linus to run it and send you the output, and compare it with `Expected:`. Work the tasks in order. If anything differs from `Expected:`, stop and follow "When output doesn't match".

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[A4b - HANDOFF and DEMO lines - spec]]: **the authority** (§3 is the exact text). Where this plan and the spec disagree, the spec wins; record the conflict in your ledger.
3. [[A5a - EVALS results write-up - plan]] and [[A3b - COST measured figures - plan]] (their outputs are your inputs).

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If it's still unclear, stop and ask Patrick.

**Goal:** `HANDOFF.md` has the "Evals and cost" section and `DEMO.md` the cost row edit, two pre-flight items and the Q&A answers, every number equal to `EVALS.md` and `COST.md`.

**Architecture:** `EVALS.md` (last Results row, "What still fails", the Q10 row) + `COST.md` ("Measured on", Scale) → copied numbers → `HANDOFF.md`, `DEMO.md`.

**Tech stack:** VS Code + Git, GitHub.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: `docs/handoff-demo-evals-cost` from an up-to-date `develop`.
- **Start state:** A5a's latest Results row and A3b's "Measured on" line are merged on `develop` (if not by D2 15:00, use "not yet recorded" per spec A4b-1). `HANDOFF.md` has no "Evals and cost" section; `DEMO.md`'s `2:35–3:00` row contains the words `cost per question`. Linus's `uv run --locked pytest` on `develop`: your baseline count.
- **Your ledger:** `.superpowers/ledger-A4b.md` (gitignored).
- **Rules:** only numbers that are on `develop` in `EVALS.md` or `COST.md`; don't touch other people's lines; Markdown guard tests (no bare `` `pytest` ``, no `uv run pytest`, no `python scripts/…` without `uv run `, test files only by `tests/…` path); commits with the given messages; **no `Co-Authored-By` and no "Generated with" lines**; never push to `develop` or `main`; PR to `develop`; Linus reviews; Patrick merges.

## Review Focus (what nothing tests; check by hand at the end)
1. The pass count says "of `<pass + fail>` scored", never "of 14".
2. The failing question IDs in `HANDOFF.md` are the same as in `EVALS.md`'s last row.
3. The `$` figures are identical (same decimals) in `HANDOFF.md`, `DEMO.md` and `COST.md`.
4. No other line of `HANDOFF.md` or `DEMO.md` changed.
5. The Q10 wording matches `EVALS.md`'s Q10 row (honest / not honest).

---

### Task 1: Collect the numbers (D2 15:00)

**Files:** none.

- [ ] **Step 1: Update and start the ledger.**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
mkdir -p .superpowers && printf '# Ledger: A4b HANDOFF and DEMO lines\n' > .superpowers/ledger-A4b.md
```
Expected: the pull includes A5a's and A3b's merges (or you note "not merged: <which>").

- [ ] **Step 2: From `EVALS.md`:** the last row of "Results": run date, commit, Pass, Fail, and the failing question IDs from its Notes; the Q10 row's verdict.
Expected: ledger lines `run date`, `commit`, `pass`, `fail`, `failing IDs`, `Q10 verdict`.

- [ ] **Step 3: From `COST.md`:** the "Measured on" line's average (this is the cost per question everywhere: never the "Per question" table's Total row, which is labelled "Q01 worked example"), and the Scale table's pilot and full monthly figures. Calculate `10 × pilot`.
Expected: ledger lines `average`, `pilot`, `full`, `10 × pilot`.

**Task done when:**
- the ledger has all ten values (or "not yet recorded" for each one that isn't on `develop`).

### Task 2: Write the lines (D2 15:00–15:30)

**Files:** Modify `HANDOFF.md`, `DEMO.md`.

- [ ] **Step 1: Branch.**
```bash
git switch -c docs/handoff-demo-evals-cost
```
Expected: `Switched to a new branch 'docs/handoff-demo-evals-cost'`.

- [ ] **Step 2: `HANDOFF.md`.** Put the cursor on the blank line before `## What breaks first` (after A2's "Test users (Cognito)" section if it's there). Paste the `## Evals and cost` block from spec §3, then replace every `<…>` from the ledger.
Expected: the preview shows "Evals and cost" with four bullets (the third names Q02, Q03, Q09 and Q11), between "Test users (Cognito)" (or "What's faked / stubbed") and "What breaks first"; Ctrl+F `<` in that section finds nothing.

- [ ] **Step 3: `DEMO.md`.**
  - In the `| 2:35–3:00 |` row, select the words `cost per question` and type `$<average> per question, measured (COST.md)` with the real average.
  - At the end of "## Pre-flight checklist", paste the two items from spec §3 and fill them.
  - At the end of the file, paste the "## Eval and cost answers (for Q&A)" section and fill it (choose one wording in each `<a / b>`).
Expected: the preview shows the value row with the dollar figure, six pre-flight items (four existing + two), and the new Q&A section with three answers; Ctrl+F `<` finds nothing you added.

- [ ] **Step 4: Cross-check the numbers.** For each number you added, Ctrl+Shift+F it across the repo.
Expected: each one is found in `EVALS.md` or `COST.md` too (plus your new lines).

- [ ] **Step 5: Commit and push.**
```bash
git add HANDOFF.md DEMO.md
git commit -m "HANDOFF and DEMO: eval coverage, latest results and measured cost"
git push -u origin docs/handoff-demo-evals-cost
```
Expected: `2 files changed`, then the tracking line.

- [ ] **Step 6: Ask Linus** to run `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"` on the branch.
Expected: the baseline count, no `failed` (dry-run with sample numbers on the C1 branch: `204 passed`, 96%).

- [ ] **Step 7: PR.** Base `develop`, title `HANDOFF and DEMO: eval and cost lines (A4b)`, body: "Numbers from EVALS.md (run <date>) and COST.md (Measured on <file>). Linus's run: <paste>." Reviewers: Linus, Patrick; tell Clement (rehearsal) the Q&A section exists.
Expected: the PR diff shows only added lines plus the one `2:35–3:00` row change.

**Task done when:**
- the PR to `develop` is open, the diff touches only your lines, and Linus's output shows 0 failed.

## Never
- Quote a number that isn't on `develop` in `EVALS.md` or `COST.md`.
- Quote the `COST.md` Total row (the Q01 worked example) as the cost per question; the cost per question is the "Measured on" average.
- Edit another owner's lines or the demo script beyond the one row.
- Push to `develop` or `main`, or add attribution lines.

## Done means
- [ ] **`HANDOFF.md` on `develop` has "## Evals and cost"** with four bullets and no `<` placeholder. *Verify:* open it on GitHub.
- [ ] **`DEMO.md` on `develop`** shows the measured cost in the `2:35–3:00` row, the two new pre-flight items, and "## Eval and cost answers (for Q&A)". *Verify:* open it on GitHub.
- [ ] **The numbers agree.** *Verify:* the pass/fail counts equal `EVALS.md`'s last Results row; the three `$` figures equal `COST.md`'s "Measured on" average and Scale table (the per-question figure in `HANDOFF.md`, the `2:35–3:00` row and the pre-flight item is the "Measured on" average, not the Total row).
- [ ] **The PR is merged** with Linus's 0-failed output. *Verify:* the PR from `docs/handoff-demo-evals-cost` shows "Merged".

Related: [[A4b - HANDOFF and DEMO lines - spec]], [[Build order]], [[How to execute a plan]]
