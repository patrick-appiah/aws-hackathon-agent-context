---
tags: [build, plan, area/business]
id: B3c
owner: Patrick + Michael
spec: "[[B3c - Pitch script and Q and A - spec]]"
status: ready
updated: 2026-10-14
---
# B3c: The 10-minute pitch and the 8-minute Q&A (implementation plan)

> **For the executing person or agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Compare what you see with every `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never put a figure or a claim in an answer that its `Source:` file doesn't hold.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[B3c - Pitch script and Q and A - spec]]: **the authority**, with both files' exact content (§3, §4) and the rehearsal procedure (§5).
3. [[Business case and pitch]], [[Judging rubric]] ("Questions judges should ask"; the process), [[Hackathon guideline]] §05.
4. [[B2 - Pitch deck - spec]], [[B3b - Architecture and cost slides - spec]], [[Clement - front end]] (F6), D-002 ([[2026-10-13 EU-only Bedrock inference profiles]]), D-015.

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If it's still unclear, stop and ask Patrick.

**Goal:** `business/pitch-script.md` *(new)* and `business/qa-prep.md` *(new)* on `develop`, every slot filled from its source, and two logged rehearsals that finish within 10 minutes.

**Architecture:** two Markdown files in `business/`, one branch `docs/pitch-script`; the rehearsal log in the vault's D2 session note.

**Tools:** VS Code; `git`, `grep`; a stopwatch (phone); the deployed portal and the backup video (Clement).

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: `docs/pitch-script` from an up-to-date `develop`, after B2 is merged (B3b merged or final).
- **Start state:**
  - `test -f business/pitch-script.md; echo $?` → `1`; `test -f business/qa-prep.md; echo $?` → `1`.
  - `unzip -l business/pitch-deck.pptx | grep -c -E 'ppt/slides/slide[0-9]+\.xml$'` → `10` (B2 merged).
  - `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"` → write the count in `.superpowers/ledger-B3c.md`; the same after every commit.
- **The executive is the CFO**, never the CIO. **Never claim the target as built (D-015).** Every figure spoken equals the slide's and its source's.
- **Documentation guards** read every tracked `.md`: no bare `pytest` in backticks, no `uv run pytest`, no `python scripts/…` without `uv run`, no `test_*.py` path outside `tests/`.
- **No secrets, synthetic data, no names beyond the brief's** (and our team).
- **Commits:** the messages given; no attribution lines; ask Patrick before pushing; Patrick merges. Stay in `business/`.

## Review Focus
1. **Each Q&A answer's facts are in its `Source:` file** today (open each one).
2. **Spoken figures equal the slides** (script row by row against the PDF).
3. **The Cognito wording** in the script and Q1 matches the D2 12:00 decision and slide 7.
4. **The tenants answer (Q10)** matches Patrick's fix of the `ARCHITECTURE.md` §4 vs §6 inconsistency.
5. **Rehearsal 2 finished between 9:00 and 10:00** and the fixes from rehearsal 1 are in the files.

---

### Task 1: Settle the open facts before writing

**Files:** none changed. **Produces:** ledger lines with each fact the files need.

- [ ] **Step 1: Branch and baseline**
  ```bash
  cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
  test -f business/pitch-script.md; echo $?; test -f business/qa-prep.md; echo $?
  unzip -l business/pitch-deck.pptx | grep -c -E 'ppt/slides/slide[0-9]+\.xml$'
  uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
  git switch -c docs/pitch-script
  mkdir -p .superpowers && printf '# Ledger: B3c Pitch script and Q and A\n' > .superpowers/ledger-B3c.md
  ```
  Expected: `1`, `1`, `10`; the pass count (write `Start: <n> passed`).
- [ ] **Step 2: Ask Patrick three things** and write each answer in the ledger:
  - the Cognito go/no-go result at D2 12:00 → `Fact: Cognito <go | no-go>`;
  - the tenants wording after his fix of `ARCHITECTURE.md` §4 vs §6 → `Fact: tenants <one synthetic tenant | two synthetic tenants>` (check `grep -n 'synthetic tenant' ARCHITECTURE.md` shows one consistent wording);
  - Huvison's `/ask` timing decision (synchronous within 29 s, or async start plus polling) → `Fact: ask timing <decision>` (`DECISIONS.md` if recorded).

  Then copy two facts that are already written down:
  - the retry limit: Huvison's written Q09 answer ([[A1 - Eval set review and manual checks - plan]] Task 4 Step 2; the `Fact: retry limit` line in B2's PR body) → `Fact: retry limit <his words, for example "at most one retry">`. Never "two retries" from memory: the code today allows at most one retry (`max_claim_attempts = 2`, retried only while attempts are below 2), and the decision is his;
  - the slide 5 path: B2's ledger `Slide 5 path:` line and any slide-5 `Ruling:` (both in B2's PR body) → `Fact: slide 5 path <main | (a) | (b)>; slide 5 shows <the rejected claim, verbatim, and its question ID>`.

  Expected: five `Fact:` lines.
- [ ] **Step 3: Copy the figures from the deck and files.** From `business/pitch-deck.pdf` slides 1, 8, 9: the quote (if any), `<pass>`, `<total>`, `<cost>`, `<pilot monthly>`, `<months>`, the count sentence. From `COST.md`: `<average>` (the "Measured on" average per question, the same figure as slide 9; never the "Per question" Total row, which is the Q01 worked example), `<Full>`. From `business/business-case.md`: `<seconds>`. From `HANDOFF.md`: "What breaks first", first bullet (or `TODO`). From `EVALS.md`: the first failing question in "What still fails" and Q12's result in the recorded run. Write each as `Figure: <slot> = <value> (<file>)`. Expected: one `Figure:` line per `<…>` slot in the spec §3 and §4 (count them: `grep -o '<[^>]*>' ` on the spec's two blocks).

**Task done when:**
- The ledger has the five `Fact:` lines (Cognito, tenants, ask timing, retry limit, slide 5 path) and a `Figure:` line for every slot.
- `grep -n 'synthetic tenant' ARCHITECTURE.md` shows only one wording (or Patrick has said he'll fix it, recorded as a `Ruling:`).

### Task 2: Write the two files

**Files:** Create `business/pitch-script.md` *(new)*, `business/qa-prep.md` *(new)*.

- [ ] **Step 1: `business/pitch-script.md`.** Create it with the spec §3 content exactly, filling each slot from the ledger. Slide 7's line: the spoken version of slide 7's Cognito line. If there is no quote on slide 1, delete the `<If the quote box …>` sentence entirely. Row 1:30–4:30: keep only the wording for `Fact: slide 5 path` (path `main`: "the critic rejecting the DEF-0398 claim while RC-C3-E4-customers still fails"; path (a) or (b): "the answer flagging the DEF-0398 conflict, and the critic rejecting <claim> (labelled)", with the claim and its label from the `Fact: slide 5 path` line) and the matching line for Patrick. Row 6:30–7:30: the retry clause is the `Fact: retry limit` wording. Expected: the Markdown preview shows one table with 8 rows from 0:00 to 10:00 and the "If the demo fails" list.
- [ ] **Step 2: `business/qa-prep.md`.** Create it with the spec §4 content exactly, filling each slot from the ledger:
  - Q1: the Cognito clause from `Fact: Cognito`.
  - Q3: if "What breaks first" is still `TODO`, delete the slot sentence and keep the ROADMAP sentence; tell Patrick (ledger `Ruling:`).
  - Q10: if `Fact: tenants` says two synthetic tenants run in the demo, add "The demo runs two synthetic tenants to show it." before the last sentence.
  - Q15: the timing clause from `Fact: ask timing`.

  Expected: the preview shows 15 numbered `##` sections, each ending with `Source:` and `Answers:`.
- [ ] **Step 3: Check and commit**
  ```bash
  grep -c -E '^\| [0-9]+:[0-9]{2}–[0-9]+:[0-9]{2} \|' business/pitch-script.md
  grep -c '^## [0-9]' business/qa-prep.md; grep -c '^Source: ' business/qa-prep.md; grep -c 'Answers: ' business/qa-prep.md
  grep -c 'TBC\|TODO\|<' business/pitch-script.md business/qa-prep.md
  grep -c 'CIO' business/pitch-script.md
  uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
  git add business/pitch-script.md business/qa-prep.md
  git commit -m "Add the 10-minute pitch script and the Q&A preparation"
  ```
  Expected: `8`; `15`, `15`, `15`; `business/pitch-script.md:0` and `business/qa-prep.md:0`; `1`; the start count; one commit.
- [ ] **Step 4: Open the PR now, before the 15:00 lead review:** do Task 4 Step 1. The rehearsal fixes (Task 3) are pushed to the same branch. Expected: the PR exists before 15:00.

**Task done when:**
- Both files exist with 8 script rows and 15 answers, no unfilled slot, and "CIO" only in "Not the CIO".
- The PR from `docs/pitch-script` is open (Task 4 Step 1) before 15:00.

### Task 3: Rehearse twice and fix (D2 16:00–17:00)

**Files:** Modify `business/pitch-script.md`, `business/qa-prep.md` (fixes only); the vault D2 session note.

- [ ] **Step 1: Cold start.** Close the browser; open a fresh profile; complete the `DEMO.md` pre-flight checklist. Expected: every pre-flight box ticked, including "one warm-up question asked".
- [ ] **Step 2: Rehearsal 1.** Patrick presents from the script, Clement drives, Michael times each row with the stopwatch. Expected: a time per row written down.
- [ ] **Step 3: Log and fix.** In the vault D2 session note, add `## Pitch rehearsals` and `Run 1: total <m:ss>; demo <m:ss>; over/under by section: <list>; fixes: <list>`. Shorten the "What we say" text of any row that ran over its slot; fix any figure said differently from the slide. Expected: the log line exists; the script rows that ran over are shorter.
- [ ] **Step 4: Rehearsal 2**, the same way, then log `Run 2: …`. Expected: total between `9:00` and `10:00`. If not, cut row text again (slide 8 first) and run once more before 17:00, logging `Run 3`.
- [ ] **Step 5: Q&A drill.** Michael asks five questions from `business/qa-prep.md` chosen at random (roll a die or pick numbers). Patrick answers without reading. Log `Q&A drill: <numbers>; over 45 s: <numbers>; wrong figure: <numbers>`. Shorten or correct those answers in the file. Expected: the drill line in the vault log.
- [ ] **Step 6: Commit and push the fixes to the open PR, and push the vault**
  ```bash
  git add business/pitch-script.md business/qa-prep.md
  git commit -m "Tighten the pitch script and Q&A answers after the rehearsals"
  git push
  ```
  Then in the vault: `git pull --rebase`, commit `Pitch rehearsal log`, push. Expected: one repo commit, shown on the open PR (or none, if nothing changed: write `Task 3: no fixes needed` in the ledger); the vault log visible on GitHub.

**Task done when:**
- The vault D2 note has `Run 1` and `Run 2` lines, and the last run's total is between 9:00 and 10:00.
- The Q&A drill line is logged and its findings are fixed in `business/qa-prep.md`.

### Task 4: PR (opened after Task 2 Step 3) and review

- [ ] **Step 1: PR (with Patrick's OK only), right after Task 2 Step 3, before the 15:00 lead review**
  ```bash
  git diff develop --stat
  uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
  ```
  Expected: only `business/pitch-script.md` and `business/qa-prep.md`; the start count. Then `git push -u origin docs/pitch-script`, PR to `develop` titled `Pitch script and Q&A preparation`; the body has the five `Fact:` lines, every `Ruling:` and the line "Rehearsal totals follow after 16:00". Set B3c's row in [[Build order]] to `in review (PR #<n>)`. Expected: the PR shows 2 files.
- [ ] **Step 2: Review Focus (after Task 3).** Five lines, each result in the ledger. Fix any problem in the files, commit and `git push` to the same PR. Expected: five `Review <n>: ok` lines.
- [ ] **Step 3: Rehearsal totals in the PR.** Edit the PR body: replace "Rehearsal totals follow after 16:00" with the `Run 1`, `Run 2` (and `Run 3`) totals and the `Q&A drill:` line. Expected: the PR body shows the totals; "Files changed" still lists only the two files.

**Task done when:**
- A PR from `docs/pitch-script` to `develop`, opened before 15:00, touches only the two files, with the rehearsal fixes pushed to it and the rehearsal totals in its body.

## Done means
- [ ] **The script exists and fits.** Verify: on `develop`, `grep -c -E '^\| [0-9]+:[0-9]{2}–[0-9]+:[0-9]{2} \|' business/pitch-script.md` → `8`, and the last row starts `| 8:45–10:00 |`.
- [ ] **The demo moment is scripted.** Verify: `grep -c 'DEF-0398' business/pitch-script.md` → ≥ 1 and `grep -c 'If the demo fails' business/pitch-script.md` → `1`.
- [ ] **Fifteen grounded answers.** Verify: `grep -c '^## [0-9]' business/qa-prep.md`, `grep -c '^Source: ' business/qa-prep.md` and `grep -c 'Answers: ' business/qa-prep.md` each → `15`; the four brief topics are present: `grep -c -E "^## .*(real and what's faked|100 questions a day|breaks first|data residency)" business/qa-prep.md` → `4`.
- [ ] **No unfilled slot.** Verify: `grep -c 'TBC\|TODO\|<' business/pitch-script.md business/qa-prep.md` → `0` for both.
- [ ] **Rehearsed twice.** Verify: the vault D2 session note has `Run 1:` and `Run 2:` lines under `## Pitch rehearsals`, the last with a total between 9:00 and 10:00, and a `Q&A drill:` line.
- [ ] **The guards pass.** Verify: `uv run --locked pytest` passes with the start count.
- [ ] **Merged.** Verify: the PR from `docs/pitch-script` shows "Merged"; B3c's row in [[Build order]] says `merged`.

## Never
- Answer with a figure not in the named source, or call an estimate measured.
- Describe a roadmap layer as built, or Cognito as built after a no-go.
- Debug on stage; follow the fallback order.
- Edit `DEMO.md`, the slides or another workstream's file.
- Push to `develop` or `main`, or add attribution lines.

Related: [[B3c - Pitch script and Q and A - spec]], [[Build order]], [[How to execute a plan]]
