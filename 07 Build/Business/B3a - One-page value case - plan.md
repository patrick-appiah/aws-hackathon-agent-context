---
tags: [build, plan, area/business]
id: B3a
owner: Patrick + Michael
spec: "[[B3a - One-page value case - spec]]"
status: ready
updated: 2026-10-14
---
# B3a: The one-page value case (implementation plan)

> **For the executing person or agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Compare what you see with every `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never put a figure on the page that isn't in `business/business-case.md` with the same label.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[B3a - One-page value case - spec]]: **the authority**, with the page's exact content (§3).
3. [[Business case and pitch]], [[Judging rubric]] (required submissions; 1.1–1.3), [[B1 - Business case figures and validation - spec]].
4. [[Workstreams]] §7, D-015 ([[2026-10-13 POC plus one target slice, target as 90-day roadmap]]).

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If it's still unclear, stop and ask Patrick.

**Goal:** `business/value-case.md` *(new)* and `business/value-case.pdf` *(new)*, one page, every figure copied from the finished business case.

**Architecture:** one Markdown file and its PDF in `business/`; branch `docs/value-case-page` (not `docs/value-case`, which already exists on the remote from an old draft).

**Tools:** VS Code; the Markdown-to-PDF tool used for `business/business-case.pdf` (commit `68866af`), or the VS Code extension **Markdown PDF** (yzane) → "Markdown PDF: Export (pdf)"; `git` and `grep`.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: `docs/value-case-page` from an up-to-date `develop`, **after B1's PR 2 is merged** (or from `docs/business-case-measured` if it isn't by D2 14:45; then rebase on `develop` once it merges).
- **Start state:**
  - `test -f business/value-case.md; echo $?` → `1` (the file doesn't exist).
  - `grep -c 'TBC' business/business-case.md` → `0` (B1 done). If not `0`, stop: B1 isn't finished.
  - `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"` → write the count in `.superpowers/ledger-B3a.md`; the same count after every commit.
- **No new figures:** copy, with the label. **The executive is the CFO.** **Never claim the target as built (D-015).** Synthetic data, no secrets, no names beyond the brief's.
- **Documentation guards** read every tracked `.md`: no bare `pytest` in backticks, no `uv run pytest`, no `python scripts/…` without `uv run`, no `test_*.py` path outside `tests/`.
- **Commits:** the messages given; no attribution lines; ask Patrick before pushing; Patrick merges.

## Review Focus
1. **Every figure matches the business case** today (not a figure from an earlier draft).
2. **The labels came with the figures:** a *proposed* figure in the business case is *proposed* here.
3. **One page:** the PDF is one page with the footer of the table visible, not clipped.
4. **The pilot facts match `docs/ROADMAP.md`** (6 weeks, the team, the four go/no-go lines).
5. **The tone is the CFO's:** money, days and risk, not architecture.

---

### Task 1: Branch and copy the figures into the ledger

**Files:** none changed. **Produces:** a ledger with every figure the page needs. **Consumes:** `business/business-case.md`, `docs/ROADMAP.md`.

- [ ] **Step 1: Branch and baseline**
  ```bash
  cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
  test -f business/value-case.md; echo $?
  grep -c 'TBC' business/business-case.md
  uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
  git switch -c docs/value-case-page
  mkdir -p .superpowers && printf '# Ledger: B3a One-page value case\n' > .superpowers/ledger-B3a.md
  ```
  Expected: `1`; `0`; the pass count (write it as `Start: <n> passed`).
- [ ] **Step 2: Copy the figures.** Run:
  ```bash
  grep -n -E 'Validated with|Validation:|Time to answer|Cost per answered|Days to rebuild|Consultant days saved|Value per month|Portal run cost|Net value per month|Payback|Value over one programme|ERP consolidation planned' business/business-case.md
  ```
  Write each line's figure and label in the ledger as `Figure: <name> = <value> (<label>, line <n>)`. Expected: 11 lines found (lines 23, 31, 34, 42, 46, 48–52 and the portfolio line, give or take moved line numbers), and one `Figure:` ledger line per slot in spec §3.

**Task done when:**
- The ledger has a `Figure:` line for every `<…>` slot in spec §3, each with its business-case line number.

### Task 2: Write `business/value-case.md`

**Files:** Create `business/value-case.md` *(new)*.

- [ ] **Step 1: Create the file** with the spec §3 content exactly, replacing each `<…>` slot with its `Figure:` ledger value and label. For the "Validated" row, use line 23's date and quote (variant A) or `Not yet: requested for <date>` (variant B). For the Reuse paragraph's last sentence, rewrite line 79 as one sentence keeping its figure and label. Expected: the file opens in VS Code's Markdown preview (Ctrl+Shift+V) with six `##` sections and three tables.
- [ ] **Step 2: Check it**
  ```bash
  grep -c '^## ' business/value-case.md
  grep -c 'TBC\|<' business/value-case.md
  for figure in $(grep -o '\$[0-9]\+\(,[0-9]\{3\}\)*\(\.[0-9]\+\)\?' business/value-case.md | sort -u); do printf '%s ' "$figure"; grep -c -F "$figure" business/business-case.md; done
  ```
  Expected: `6`; `0`; every figure prints `1` or more.
- [ ] **Step 3: Commit**
  ```bash
  uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
  git add business/value-case.md
  git commit -m "Add the one-page value case, derived from the business case"
  ```
  Expected: the start count; one commit.

**Task done when:**
- `business/value-case.md` has 6 sections, no `TBC` or `<`, and every dollar figure is found in `business/business-case.md`.

### Task 3: Export the one-page PDF and open the PR

**Files:** Create `business/value-case.pdf` *(new)*.

- [ ] **Step 1: Export** `business/value-case.md` to `business/value-case.pdf` with the same tool and look as `business/business-case.pdf`, A4 portrait. Expected: the PDF exists beside the Markdown.
- [ ] **Step 2: One page.** Open the PDF. Expected: exactly one page; all three tables complete. If it runs over: shorten "The problem" to two sentences, then the Reuse paragraph to two sentences, then reduce the font one step; re-export until it fits. Never cut the ROI table or its Basis column.
- [ ] **Step 3: Review Focus.** Work through the five lines; write each result in the ledger. Expected: five `Review <n>: ok` lines.
- [ ] **Step 4: Commit and PR (PR with Patrick's OK only)**
  ```bash
  git add business/value-case.md business/value-case.pdf
  git commit -m "Export the one-page value case PDF"
  git diff develop --stat
  ```
  Expected: the diff lists only `business/value-case.md` and `business/value-case.pdf`. Then `git push -u origin docs/value-case-page` and open a PR to `develop` titled `One-page value case`; the body says every figure is copied from the business case and lists the lines. Set B3a's row in [[Build order]] to `in review (PR #<n>)` (the lead adds the row when splitting B3). Expected: the PR shows 2 files.

**Task done when:**
- `business/value-case.pdf` is one page and committed.
- A PR from `docs/value-case-page` to `develop` touches only the two files.

## Done means
- [ ] **The page exists.** Verify: on `develop`, `test -f business/value-case.md && test -f business/value-case.pdf && echo ok` prints `ok`.
- [ ] **It has the judges' sections.** Verify: `grep '^## ' business/value-case.md` prints Who, The problem, KPIs: baseline and target, ROI, with every assumption, Reuse across portfolio companies, The next engagement: a 6-week pilot.
- [ ] **No figure of its own.** Verify: the Task 2 Step 2 loop prints `1` or more for every dollar figure; the two headline KPI rows carry the same labels as business-case lines 31 and the sizing table.
- [ ] **No unfilled slot.** Verify: `grep -c 'TBC\|<' business/value-case.md` → `0`.
- [ ] **One page.** Verify: `business/value-case.pdf` opens with 1 page.
- [ ] **The guards pass.** Verify: `uv run --locked pytest` passes with the start count.
- [ ] **Merged.** Verify: the PR from `docs/value-case-page` shows "Merged"; B3a's row in [[Build order]] says `merged`.

## Never
- Add, round or recompute a figure that isn't in the business case.
- Drop an assumption to make the page fit.
- Describe a roadmap capability as built.
- Push to `develop` or `main`, or add attribution lines.

Related: [[B3a - One-page value case - spec]], [[Build order]], [[How to execute a plan]]
