---
tags: [build, plan, area/evals]
id: A5a
owner: Abdul
spec: "[[A5a - EVALS results write-up - spec]]"
status: ready
updated: 2026-10-14
---
# A5a: EVALS.md results rows and "What still fails" (implementation plan)

> **For the executing agent (and Abdul):** follow [[How to execute a plan]] exactly, with one change: **Abdul does not run Python, uv or pytest.** Linus runs the evals and the suite and sends you the output; you compare it with `Expected:`. Repeat Tasks 1–3 for every recorded run. If anything differs from `Expected:`, stop and follow "When output doesn't match".

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[A5a - EVALS results write-up - spec]]: **the authority** (§3 row template, §4 "What still fails"). Where this plan and the spec disagree, the spec wins; record the conflict in your ledger.
3. [[A1 - Eval set review and manual checks - plan]] Task 6 (the manual-check lines).
4. [[Linus - API, identity, blocker-analyst]] §6.

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If it's still unclear, stop and ask Linus.

**Goal:** every recorded eval run is committed with an honest `EVALS.md` row, and "What still fails" describes the latest run.

**Architecture:** `uv run python -m evals.run --asker flow.local:ask` (Linus) → `evals/results/run-*.json` (the folder `evals/results/` *(new)* is created by the eval runner's first committed run, your first PR) → you → `EVALS.md` + the file committed.

**Tech stack:** VS Code (JSON search, Markdown preview), Git, GitHub.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch per recorded run: `docs/eval-results-<yyyymmdd>-<hhmm>` (the run's time, for example `docs/eval-results-20261015-1130`), from an up-to-date `develop`.
- **Start state:** H6 merged; `EVALS.md` "## Results" has one row (`2026-10-14 | feature/eval-runner | critic 1.0.0 | 0 | 0 | …`); "## What still fails" has three bullets, the first "**No question can be answered yet.**"; the heading reads `(160 tests, 95% coverage, passing)`. `evals/results/` doesn't exist on `develop` (or holds earlier recorded files). Linus's `uv run --locked pytest` on `develop`: your baseline count (≥ `204 passed`, ≥ 96%).
- **Your ledger:** `.superpowers/ledger-A5a.md` (gitignored), one block per run.
- **Rules:** results as they are, never rounded into a pass; never edit the results file; no token or password in any file (check `eyJ`); Markdown guard tests (no bare `` `pytest` ``, no `uv run pytest`, no `python scripts/…` without `uv run `, test files only by `tests/…` path); commits with the given messages; **no `Co-Authored-By` and no "Generated with" lines**; never push to `develop` or `main`; PR to `develop`; Linus reviews; Patrick merges.

## Review Focus (what nothing tests; check by hand at the end)
1. Pass and Fail in each row equal the file's `summary` (not your own count).
2. Every failing question has a bullet with a cause from its owner.
3. The committed file is byte-for-byte what Linus sent (you didn't open-and-reformat it: VS Code's "Format Document" must not be used on it).
4. Warnings are listed, not hidden and not counted as failures.
5. The stale "No question can be answered yet" bullet is gone after the first asker run.

---

### Task 1: Receive and check the file (each run)

**Files:** none yet.

- [ ] **Step 1: Ask Linus for the run.** *"Please run `uv run python -m evals.run --asker flow.local:ask` on develop (and the deployed-API asker if it's ready), plus `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"`, and send me the console output and the results file(s). Is this a recorded run?"*
Expected: console output ending with a summary line such as `8 pass · 3 fail · 1 manual · 2 not applicable` and `Results written to evals/results/run-<yyyymmdd>-<hhmmss>.json`; the file; "recorded: yes"; the pytest lines.

- [ ] **Step 2: Check the top of the file.**
Expected: `"asker"` is not `null`; `"commit"` is a short hash; `"prompt_versions"` lists every locked agent; `"summary"` counts add up to **14**. Ledger: run_at, commit, asker, prompt_versions, summary.

- [ ] **Step 3: No secret.** Ctrl+F `eyJ`, then `password`.
Expected: **No results** for both. If either is found, don't commit: tell Linus.

- [ ] **Step 4: Failures and warnings.** Ctrl+F `"status": "fail"`; for each, note the case `id` and `detail` up to the first `; `. Then Ctrl+F `"warning": true` and, for each with `"passed": false`, note the case and check name.
Expected: the number of `"status": "fail"` cases equals `summary.fail` (0 if absent). Ledger lines `Fail: Qxx: <check>` and `Warning: Qxx: <check>`.

- [ ] **Step 5: Manual checks.** Do [[A1 - Eval set review and manual checks - plan]] Task 6 on this file.
Expected: four lines `Q02 manual: …`, `Q03 manual: …`, `Q09 manual: …`, `Q11 manual: …` in the ledger.

- [ ] **Step 6: Causes.** For each failing question, ask its owner via Linus: *"Qxx fails on '<check>' in run <file>. One sentence: why, and is a fix coming before the freeze?"*
Expected: one sentence per failure, with "fix in PR #nn" or "not before the freeze".

**Task done when:**
- the ledger has the summary, every failure with its check and cause, the warnings and the four manual lines for this run;
- the file contains no `eyJ` or `password`.

### Task 2: Write `EVALS.md` and commit the file (each run)

**Files:** Create `evals/results/run-<…>.json` *(new)*; Modify `EVALS.md`.

- [ ] **Step 1: Branch, add the file.**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
git switch -c docs/eval-results-<yyyymmdd>-<hhmm>
mkdir -p evals/results
cp <path to the file Linus sent> evals/results/
git status --short
```
Expected: `?? evals/results/run-<yyyymmdd>-<hhmmss>.json` (and nothing else).

- [ ] **Step 2: The Results row.** In `EVALS.md` "## Results", add a new last row from spec §3, filled from the ledger.
Expected: the preview shows the new row under the earlier ones; its Pass and Fail equal `summary`; the Notes end with `File: \`evals/results/<file name>\`.`

- [ ] **Step 3: "What still fails".** Replace the whole section (from `## What still fails` to the end of its last bullet) with the spec §4 structure, filled for this run. Drop the "No question can be answered yet" bullet. Keep the by-hand bullet (now "Four checks are still by hand") and "Phrase checks are blunt", updated as in §4.
Expected: the preview shows the latest-run line, one bullet per failing question (count = `summary.fail`), then the manual and blunt-check bullets. If `summary.fail` is 0, the first bullet is the "No automatic check failed…" wording.

- [ ] **Step 4: The heading count.** In `## Deterministic layer: \`uv run --locked pytest\` (160 tests, 95% coverage, passing)`, replace `160` and `95%` with Linus's latest numbers.
Expected: the heading shows his count and coverage (for example `(204 tests, 96% coverage, passing)`).

- [ ] **Step 5: Commit, push.**
```bash
git add evals/results EVALS.md
git commit -m "Evals: record run <yyyymmdd-hhmmss> (<pass> pass, <fail> fail) and update what still fails"
git push -u origin docs/eval-results-<yyyymmdd>-<hhmm>
```
Expected: `2 files changed` (one created), then the tracking line.

- [ ] **Step 6: Ask Linus** to run `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"` on the branch.
Expected: the baseline count, no `failed` (dry-run of a sample row, this section and a committed results file on the C1 branch: `204 passed`, 96%).

- [ ] **Step 7: PR.** Base `develop`, title `Evals: run <yyyymmdd-hhmmss>, <pass> pass / <fail> fail (A5a)`, body: the summary line, the failing questions with causes, Linus's output. Reviewer: Linus.
Expected: the PR diff shows the new results file and `EVALS.md` only.

**Task done when:**
- the PR to `develop` is open with the results file and `EVALS.md`, and Linus's output shows 0 failed;
- the row's counts equal the file's `summary`.

### Task 3: Hand on the numbers (each run)

- [ ] **Step 1:** tell Huvison and Patrick the run file name (A3b uses it for cost; A4b quotes the counts).
Expected: a message in the team channel with the file name and `<pass> pass, <fail> fail`.

**Task done when:**
- the message is posted.

## Never
- Edit, reformat or "fix" a results file.
- Count manual, not-applicable or warning checks as pass or fail.
- Leave out a failing question, or write a cause you weren't given.
- Commit a file that contains `eyJ` or a password.
- Push to `develop` or `main`, or add attribution lines.

## Done means
- [ ] **Every recorded run is on `develop`.** *Verify:* `evals/results/` on GitHub lists one file per recorded run, and `EVALS.md` "Results" has one row per file, each naming its file.
- [ ] **The counts are true.** *Verify:* for any row, open its file: `summary.pass` and `summary.fail` equal the row's Pass and Fail.
- [ ] **"What still fails" matches the latest run.** *Verify:* its first line names the latest file; it has one bullet per case with `"status": "fail"` in that file, each with a cause and an owner.
- [ ] **The manual checks are recorded.** *Verify:* each row after the first has `Q02 manual:`, `Q03 manual:`, `Q09 manual:`, `Q11 manual:` notes.
- [ ] **The heading count is current.** *Verify:* `EVALS.md`'s deterministic-layer heading equals the `passed` count and `TOTAL` coverage of Linus's last pytest output in the latest PR.
- [ ] **The PRs are merged** with Linus's 0-failed output. *Verify:* each `docs/eval-results-…` PR shows "Merged".

Related: [[A5a - EVALS results write-up - spec]], [[A5b - Worked examples per agent - plan]], [[Build order]], [[How to execute a plan]]
