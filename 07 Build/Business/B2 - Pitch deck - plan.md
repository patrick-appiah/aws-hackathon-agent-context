---
tags: [build, plan, area/business]
id: B2
owner: Patrick + Michael
spec: "[[B2 - Pitch deck - spec]]"
status: ready
updated: 2026-10-14
---
# B2: The pitch deck (implementation plan)

> **For the executing person or agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Every step has an `Expected:` line: compare what you see with it, every time. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never fill a slide with a figure, verdict or screenshot that didn't come from the named source.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]]: the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[B2 - Pitch deck - spec]]: **the authority**, with the exact text of every slide (§3). Where this plan and the spec disagree, the spec wins; record the conflict in the ledger.
3. [[Business case and pitch]] (the brief), [[Pitch track grading rubric]] (the four deck items), [[Hackathon guideline]] (the critic catching something on stage).
4. [[B1 - Business case figures and validation - spec]] (the figures the deck reuses), [[Workstreams]] §7, D-015 ([[2026-10-13 POC plus one target slice, target as 90-day roadmap]]).

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Patrick.

**Goal:** `business/pitch-deck.pptx` and `business/pitch-deck.pdf` hold the brief's 10 slides, every number sourced, slide 5 showing the critic's real rejection of the `DEF-0398` decoy (or, on the path recorded on D1, the flagged conflict with a labelled real rejection).

**Architecture:** one PowerPoint file, edited in place, exported to PDF. Two phases: the structure and every slide that needs no measurement (D1 evening to D2 morning, Tasks 1–3), then the measured figures and real screenshots after the D2 14:00 freeze (Task 4), then export and PR (Task 5). One branch, `docs/pitch-deck`.

**Tools:** Microsoft PowerPoint (desktop, or Microsoft 365 on the web); Google Slides as the fallback (File → Open → Upload the pptx; edit; File → Download → Microsoft PowerPoint (.pptx), then again → PDF). A screenshot tool (Windows: Win+Shift+S). `git`, `unzip`, `sed` and `grep` in a shell for the checks. `uv run --locked pytest` only to confirm the repo guards.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your own clone). Branch: `docs/pitch-deck` from an up-to-date `develop`.
- **Start state:**
  - `unzip -l business/pitch-deck.pptx | grep -c -E 'ppt/slides/slide[0-9]+\.xml$'` → `11` (today's deck, commit `68866af`).
  - `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"` → `204 passed`, 96%, when only C1 is merged after today's `develop`; later items add tests, so write the number you see in `.superpowers/ledger-B2.md` and expect the same after every commit.
- **The executive is the CFO** (with the programme sponsor), never the CIO.
- **Every number has a source** in its slide's evidence line: *(brief)*, *measured* (file), *proposed* (assumption), or synthetic demo data (`tools/metrics.py`). Never a guessed number, not even "for now".
- **Never claim the target as built (D-015).** Cognito is "built" only after a **go** at D2 12:00.
- **Synthetic data only; no secrets:** no AWS account ID, URL with a token, console window or real name (beyond Vanessa Addo and Joseph Akayesi) in any screenshot.
- **Commits:** small, the messages given; binary files are fine. No `Co-Authored-By` and no "Generated with" lines. Ask Patrick before pushing; Patrick merges. Never push to `develop` or `main`.
- **Stay in `business/`.** Don't edit `DEMO.md`, `EVALS.md`, `COST.md`, `docs/` or `web/`.

## Review Focus (what the checks don't catch; do it by hand at the end)
1. **Slide 5 is real:** the verdict text on the slide equals, character for character, `rejected[].statement` and `reason` in the named results file.
2. **Every screenshot is from the run the slide names** (deployed portal after the freeze, or labelled "mock data"), and shows no secret or account detail.
3. **Each number matches its source today:** `COST.md`, `EVALS.md` Results, `business/business-case.md` and `/summary` on the deployed portal agree with the slides.
4. **Nothing in the 90-day column reads as built,** and the Cognito line matches the D2 12:00 decision.
5. **The deck reads in 10 minutes:** one idea per slide, the evidence line small but legible in the PDF at 100% zoom.

---

### Task 1: Branch, baseline and the slide map

**Files:** none changed yet.
**Produces:** the ledger with the start state and the old-to-new slide map. **Consumes:** today's `business/pitch-deck.pptx`.

- [ ] **Step 1: Branch and baseline**
  ```bash
  cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
  unzip -l business/pitch-deck.pptx | grep -c -E 'ppt/slides/slide[0-9]+\.xml$'
  uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
  git switch -c docs/pitch-deck
  mkdir -p .superpowers && printf '# Ledger: B2 Pitch deck\n' > .superpowers/ledger-B2.md
  ```
  Expected: `11`; the pass count and coverage (write them in the ledger as `Start: <n> passed, <pct>%`).
- [ ] **Step 2: Print today's slide text** (the checks in Tasks 3–5 use the same loop):
  ```bash
  for number in $(seq 1 11); do printf 'slide %s: ' "$number"; unzip -p business/pitch-deck.pptx "ppt/slides/slide${number}.xml" | sed 's/<[^>]*>/ /g' | tr -s ' ' | cut -c1-160; echo; done
  ```
  Expected: slide 1 starts `ERP MIGRATION PROGRESS PORTAL`, slide 8 contains `SEE IT LIVE`, slide 11 contains `NEXT STEP`.
- [ ] **Step 3: Write the slide map in the ledger**, exactly:
  ```text
  Map: new 1 = old 1 + old 2 (merge) | new 2 = old 3 | new 3 = old 4 | new 4 = old 8 (top) | new 5 = new slide (from old 8's "Then it catches...") | new 6 = old 5 + old 6 (merge) | new 7 = old 9 (rework) | new 8 = old 7 | new 9 = old 10 | new 10 = old 11
  ```
  Expected: `grep -c '^Map:' .superpowers/ledger-B2.md` prints `1`.

**Task done when:**
- Branch `docs/pitch-deck` exists and the ledger holds the start state and the map.

### Task 2: The "why it's agentic" interview (D1 evening)

**Files:** the vault session note of that day (`03 Sessions/<YYYY-MM-DD>.md`).
**Produces:** the interview answers. **Consumes:** Patrick and Huvison, 15 minutes.

- [ ] **Step 1: Hold it.** Ask the four questions in the spec §4 word for word; write the answers as spoken. Expected: four answers written down.
- [ ] **Step 2: Record it.** In the vault session note, add a section `## Why it's agentic interview` with the four questions and answers, then `git pull --rebase`, commit `Why it's agentic interview notes` and push the vault. Expected: the section is visible in the vault on GitHub (`patrick-appiah/aws-hackathon-agent-context`).
- [ ] **Step 3: Pick the sentence.** Choose the one sentence for slide 6 that states a real decision of the orchestrator (what it fetched next, and why). Write it in the B2 ledger as `Slide 6 quote: "<sentence>" (<Patrick | Huvison>)`. If the agents aren't built yet, write `Slide 6 quote: none (agents not built at interview time)` and use no quote. Expected: one `Slide 6 quote:` line in the ledger.

- [ ] **Step 4: The slide 5 path (on D1).** Ask Patrick and Huvison which run shows a rejection naming `DEF-0398` (Q01 live, Q02 eval, or neither). Record `Slide 5 path: main | (a) | (b)` now, with one value: `main` if either run shows the critic rejecting a claim that names `DEF-0398` (or calls the customer master ready or resolved); otherwise `(a)` (the default: the answer flagging the conflict, plus a labelled real rejection from Q08) unless Patrick picks `(b)` (another real rejection from the run). Expected: one ledger line `Slide 5 path: <main | (a) | (b)> (<Q01 live | Q02 eval | neither>, Patrick + Huvison, <date>)`. Task 3 builds slide 5 on that path from the start.

**Task done when:**
- The vault session note has the four answers under `## Why it's agentic interview`.
- The ledger has exactly one `Slide 6 quote:` line and exactly one `Slide 5 path:` line.

### Task 3: Restructure to 10 slides and fill every slide that needs no measurement

**Files:** Modify `business/pitch-deck.pptx`.
**Produces:** 10 slides; slides 1, 2, 3, 7, 8 and 10 complete; slides 4, 5, 6 and 9 with their structure, their non-measured text, and the words `measured at the D2 run` where a measured figure goes. **Consumes:** spec §3; B1's figures as they stand.

- [ ] **Step 1: Restructure.** Open `business/pitch-deck.pptx` in PowerPoint. Following the ledger map:
  - copy old slide 2's three role cards onto slide 1, then delete old slide 2;
  - duplicate old slide 8 (right-click → Duplicate Slide); the copy becomes new slide 5;
  - copy old slide 6's four steps under old slide 5's content as a small strip, then delete old slide 6;
  - reorder in the left panel to the map's order.

  Save. Expected: the left panel shows 10 slides; `unzip -l business/pitch-deck.pptx | grep -c -E 'ppt/slides/slide[0-9]+\.xml$'` prints `10`.
- [ ] **Step 2: Slides 1, 2, 3.** Replace each slide's kicker, title, body, strip and evidence line with the spec §3 text exactly. Add a small grey text box at the bottom left of each slide for the evidence line (11 pt, the footer's colour), above the footer. Slide 1: add the quote box only if B1 line 23 on `develop` (or B1's open branch) is variant A with consent. Slide 2: use B1's corrected figures if Task 2 of B1 changed any. Slide 3: insert a screenshot of the portal's one screen (from the deployed portal if it is up, else `cd web && yarn start` on mock data, and then add ` Screenshot: mock data.` to the evidence line). Save. Expected: each slide's text matches the spec when read side by side.
- [ ] **Step 3: Slides 7, 8 and 10.** Replace their text with the spec §3 text. On slide 7, choose the Cognito line from the D2 12:00 decision (ask Patrick; before the decision, use `Sign-in with role and entity scope: go / no-go at D2 12:00` and revisit in Task 4). Add each target box's phase tag as a small rounded label. Save. Expected: slide 7 has exactly two columns, and every right-column line ends with a `Phase` tag.
- [ ] **Step 4: Slides 4, 5, 6 and 9: the structure.** Lay out each slide as the spec describes; build slide 5 on the ledger's `Slide 5 path:` (spec §3 slide 5: `main` = the three panels with the critic's verdict; `(a)`, the default = the conflict title and panels plus a fourth, labelled panel `Another check, same run: the critic rejects an uncited claim (eval Q08)`; `(b)` = the three panels with the verdict panel titled `A real rejection from the same run`). Put in all the text that isn't measured. Where a measured figure, verdict or trace goes, type `measured at the D2 run` (never a number). Save. Expected: each of these slides contains the phrase `measured at the D2 run` at least once.
- [ ] **Step 5: Check and commit**
  ```bash
  unzip -l business/pitch-deck.pptx | grep -c -E 'ppt/slides/slide[0-9]+\.xml$'
  for number in 1 7 10; do unzip -p business/pitch-deck.pptx "ppt/slides/slide${number}.xml" | sed 's/<[^>]*>/ /g' | grep -c -E 'CFO|90-day|ROADMAP'; done
  git add business/pitch-deck.pptx
  git commit -m "Restructure the pitch deck into the brief's ten slides, with sources on every slide"
  ```
  Expected: `10`; then three numbers, each `1` or more; one commit.

**Task done when:**
- The pptx has 10 slides in the spec's order (slide titles read in the left panel match §3).
- Slides 1, 2, 3, 7, 8 and 10 match the spec text, each with an evidence line.
- Slides 4, 5, 6 and 9 hold the phrase `measured at the D2 run` where their measured content goes.

### Task 4: Fill the measured slides from the real run (D2 14:00–15:00)

**Files:** Modify `business/pitch-deck.pptx`.
**Produces:** slides 4, 5, 6, 8 (eval line and retry tile) and 9 complete; slide 7's Cognito line final. **Consumes:** `evals/results/run-<stamp>.json` (cases `Q01` and `Q02`) and `EVALS.md` Results, read first from A5a's open PR branch `docs/eval-results-<yyyymmdd>-<hhmm>`; `COST.md` (the "Measured on" average, Pilot, Full), read first from A3b's open PR branch `docs/cost-measured`; D-022 (`DECISIONS.md`: at most 2 attempts in total, one retry) (A1 Task 4 Step 2); `business/business-case.md` (B1); the deployed portal.

- [ ] **Step 1: Pick the run, from the open PR branches.** Linus records the run at 14:00 sharp (B1 Task 3 Step 0); A5a and A3b push their branches at about 14:40. Don't wait for the merges:
  ```bash
  git switch develop && git pull && git switch docs/pitch-deck && git merge develop
  git fetch origin
  git branch -r --list 'origin/docs/eval-results-*' 'origin/docs/cost-measured'
  git ls-tree --name-only origin/docs/eval-results-<yyyymmdd>-<hhmm> evals/results/
  git show origin/docs/eval-results-<yyyymmdd>-<hhmm>:evals/results/<file> > .superpowers/<file>
  git show origin/docs/eval-results-<yyyymmdd>-<hhmm>:EVALS.md > .superpowers/EVALS-recorded.md
  git show origin/docs/cost-measured:COST.md > .superpowers/COST-measured.md
  git rev-parse --short origin/docs/eval-results-<yyyymmdd>-<hhmm> origin/docs/cost-measured
  ```
  Use the `docs/eval-results-…` branch of the 14:00 recorded run (ask Linus which, and whether it's the deployed-API run). If a branch is gone because its PR already merged, read the same files from `develop` (`ls evals/results/`, `EVALS.md`, `COST.md`). Write in the ledger `Run: <file> (<asker>)` and `Read from: <A5a branch> @ <hash>, docs/cost-measured @ <hash>` (or `develop @ <hash>`). Expected: one `Run:` line naming the file the `ls-tree` printed, and one `Read from:` line. Steps 2–7 read `.superpowers/<file>`, `.superpowers/EVALS-recorded.md` and `.superpowers/COST-measured.md`.
- [ ] **Step 2: Read Q01 and Q02 out of it.** Open the file in VS Code and use "Find" for `"id": "Q01"` and `"id": "Q02"`. For Q01 copy `seconds`, `status`, the cited row IDs in `answer.answer.bullets[].citations[].row_id`, and the `answer.trace[]` entries (`step`, `agent`). For Q02 copy every entry of `answer.rejected[]`: `claim_id`, `statement`, `reason` and the number of `verdicts`. Write them all in the ledger. Expected: ledger lines `Q01: <seconds> s, <status>, cites <ids>`, `Q01 trace: <step (agent)> → …`, and one `Q02 rejected: <claim_id> | <statement> | <reason> | <n> verdicts` per rejected claim (or `Q02 rejected: none`).
- [ ] **Step 3: Slide 5, the demo moment, on the recorded path.** Read the ledger's `Slide 5 path:` line.
  - **Path `main`, and a Q02 rejected statement mentions `DEF-0398`** (or the customer master being ready or resolved): put its `statement` and `reason` verbatim into the verdict panel, and fill the evidence line (`<file>`, `<claim_id>`, `<n>`, and the critic prompt version from `agents/prompts/critic.txt`'s `version:` line). Take a screenshot of the same rejection in the portal's "could not verify" list after asking Q02 live, if the portal is up, and put it beneath the panels. Expected: the slide shows `DEF-0398`, `RC-C3-E4-customers`, `Rejected:` and a reason in quotation marks.
  - **Path `(a)` or `(b)`:** fill the slide as spec §3 describes for that path, only from the run (`(a)`: the Q02 answer's sentence that flags the conflict, quoted, plus a Q08 `rejected[]` `statement` and `reason`, labelled `eval Q08`; `(b)`: another `rejected[]` entry of the run, verbatim, with its question ID). Write `Ruling: slide 5 uses <a | b> (path recorded on D1)` in the ledger. Expected: a `Ruling:` line, and every quoted sentence found in `.superpowers/<file>`.
  - **If the run doesn't fit the recorded path** (path `main` but `Q02 rejected: none` or no statement about `DEF-0398`; or path `(a)` but no flagged sentence or no Q08 rejection): stop. Tell Patrick, with the ledger lines. Apply his choice from spec §3 (a) or (b), and write `Ruling: slide 5 uses <a | b> because <what the run lacked> in <file>` in the ledger. Expected: a `Ruling:` line, and the slide filled only from the run.
- [ ] **Step 4: Slide 4.** Keep only the chain rows whose ID is in the `Q01: … cites` ledger line (delete the others). Fill `<seconds>`, `<file>`, the asker and `<status>`. Add the screenshot of the Q01 answer card from the portal. Expected: every citation chip on the slide appears in the ledger's Q01 line, and the slide holds no `measured at the D2 run`.
- [ ] **Step 5: Slide 6.** Replace the trace placeholder with the `Q01 trace:` steps as a strip of boxes. Add the `Slide 6 quote:` sentence from Task 2 if there is one. Fill `<file>`. Expected: the strip shows the same steps, in the same order, as the ledger line.
- [ ] **Step 6: Slide 8's eval line and retry tile.** From `.superpowers/EVALS-recorded.md` Results, the row for the same run: fill `<pass>` and `<total>` (`<total>` = Pass + Fail of that row). Then get D-022 (`DECISIONS.md`: at most 2 attempts in total, one retry) (A1's ledger line `Q09: <n> verdicts; retry limit: <his words>; …`, [[A1 - Eval set review and manual checks - plan]] Task 4 Step 2; ask Abdul) and write `Fact: retry limit = <his words> (Huvison, <date>)` in the ledger. Fill the "Bounded retries" tile with that fact (spec §3 slide 8), never with a number of your own. Expected: the numbers match the `EVALS.md` row; one `Fact: retry limit` ledger line, and the tile's wording equals it.
- [ ] **Step 7: Slide 9.** Fill from `.superpowers/COST-measured.md`: `<cost>` = the **"Measured on" average** per question (the team's one cost per question, the same figure as business case line 34; never the "Per question" Total row, which is labelled "Q01 worked example"), `<pilot monthly>` (Pilot), `<full monthly>` (Full); from `business/business-case.md`: `<months>` (Payback), `<count>` (line 79, or the variant-B text). Pick the title by the spec's $1.00 rule. Expected: every figure on slide 9 appears in `COST.md` or `business/business-case.md` (`grep -n '<figure>' COST.md business/business-case.md` finds each).
- [ ] **Step 8: Slide 7's Cognito line.** Set it from the D2 12:00 decision (ask Patrick; `HANDOFF.md` records it). Expected: the line is either the "built" or the "no-go" text from spec §3, nothing else.
- [ ] **Step 9: Check and commit**
  ```bash
  for number in $(seq 1 10); do printf 'slide %s: ' "$number"; unzip -p business/pitch-deck.pptx "ppt/slides/slide${number}.xml" | sed 's/<[^>]*>/ /g' | grep -c -E 'measured at the D2 run|TBC|TODO|&lt;'; done
  unzip -p business/pitch-deck.pptx ppt/slides/slide5.xml | sed 's/<[^>]*>//g' | grep -c -E 'DEF-0398'
  git add business/pitch-deck.pptx
  git commit -m "Fill the pitch deck's measured slides from the recorded eval run and COST.md"
  ```
  Expected: every slide prints `0`; the slide-5 check prints `1` or more (unless the path or a `Ruling:` is option b); one commit.
- [ ] **Step 10: Re-check after the A5a and A3b merges** (as soon as both PRs show "Merged", even if you are in Task 5).
  ```bash
  git fetch origin
  git diff <A5a hash from the ledger> origin/develop -- evals/results/<file> EVALS.md
  git diff <A3b hash from the ledger> origin/develop -- COST.md
  ```
  Expected: no output for the results file; no change to the run's Results row in `EVALS.md`, or to the "Measured on" average, Pilot or Full in `COST.md`. If anything the slides quote changed, update those slides from `develop`, commit `Pitch deck: re-check the measured figures after the merges`, re-export the PDF (Task 5) and add a `Ruling:` line. Ledger: `Re-check after merge: same | changed: <what>`.

**Task done when:**
- No slide contains `measured at the D2 run`, `TBC`, `TODO` or an unfilled `<…>` slot (the loop prints ten `0`s).
- Slide 5 follows the ledger's `Slide 5 path:`; its verdict text matches a `Q02 rejected:` ledger line word for word, or a `Ruling:` line records the (a)/(b) content.
- The "Bounded retries" tile on slide 8 equals the `Fact: retry limit` ledger line.
- Every number on slides 4, 8 and 9 is in the ledger with its source file.

### Task 5: Export the PDF, review, and open the PR

**Files:** Modify `business/pitch-deck.pdf`.

- [ ] **Step 1: Export.** PowerPoint: File → Export → Create PDF/XPS → `business/pitch-deck.pdf`, Options → "All slides", publish "Slides" (not notes). Google Slides: File → Download → PDF. Expected: the PDF opens with 10 pages, in the slide order.
- [ ] **Step 2: Read the PDF.** Page through at 100% zoom. Ctrl+F for `TBC`, `TODO`, `measured at the D2 run`, `CIO`. Expected: the first three find nothing; `CIO` finds only `Not the CIO` on page 1; the evidence lines are legible.
- [ ] **Step 3: Review Focus.** Work through the five Review Focus lines and write each result in the ledger. Fix problems in the pptx, re-export, re-check. Expected: five ledger lines `Review <n>: ok`.
- [ ] **Step 4: Commit and verify the order**
  ```bash
  git add business/pitch-deck.pdf
  git commit -m "Export the pitch deck PDF"
  git log -1 --format=%ct -- business/pitch-deck.pdf; git log -1 --format=%ct -- business/pitch-deck.pptx
  uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
  ```
  Expected: the first timestamp ≥ the second; the same pass count as the start.
- [ ] **Step 5: PR (with Patrick's OK only).** `git diff develop --stat` → only `business/pitch-deck.pptx` and `business/pitch-deck.pdf`. `git push -u origin docs/pitch-deck`; open a PR to `develop` titled `Pitch deck: the brief's ten slides, with the critic rejecting the decoy`. The body lists the run file used, the `Slide 5 path:` line, the `Fact: retry limit` line, every `Ruling:` line, and where each slide's figures come from (B3c reads the slide 5 path and the retry limit from here). Expected: the PR shows 2 files changed.
- [ ] **Step 6: Build order.** Set B2's row in [[Build order]] to `in review (PR #<n>)`, then `merged`. Tell B3b and B3c's owner the deck is merged (they add the appendix and the script). Expected: the vault row shows the PR number.

**Task done when:**
- `business/pitch-deck.pdf` has 10 pages and is committed after the pptx (timestamp check holds).
- A PR from `docs/pitch-deck` to `develop` exists, touching only the two deck files.
- The B2 row in [[Build order]] shows the PR.

## Done means
- [ ] **Ten slides.** Verify: `unzip -l business/pitch-deck.pptx | grep -c -E 'ppt/slides/slide[0-9]+\.xml$'` → `10`; `business/pitch-deck.pdf` opens with 10 pages.
- [ ] **Named executive (6 pts).** Verify: the extracted text of slide 1 contains `CFO` (`unzip -p business/pitch-deck.pptx ppt/slides/slide1.xml | sed 's/<[^>]*>//g' | grep -c CFO` → ≥ 1), and `CIO` appears only as `Not the CIO`.
- [ ] **What it replaces (5 pts).** Verify: slide 2 (PDF page 2) shows "2 days", "3 days a month", "4 weeks old" and "$14,500", with an evidence line naming the brief and the business case.
- [ ] **Why it is agentic (5 pts).** Verify: slide 6 shows "The numbers are code. The question isn't.", "14 scoped tools", and a trace strip whose steps match `answer.trace` of Q01 in the named results file.
- [ ] **Scope and demo moment (4 pts).** Verify: slide 7 shows "Built in 2 days" and "The 90-day target" with phase tags; slide 5 shows `DEF-0398` Closed, `RC-C3-E4-customers` failing, and a "Rejected:" verdict that equals, word for word, a `rejected[].statement` of Q02 in the named results file (or, on path (a)/(b), the PR body's `Slide 5 path:` and `Ruling:` lines name the alternative and every quoted sentence is in that file).
- [ ] **One cost per question and one retry limit.** Verify: slide 9's per-question cost equals `COST.md`'s "Measured on" average on `develop` (not the Total row, the Q01 worked example) and business case line 34; slide 8's "Bounded retries" tile states Huvison's written retry limit (the PR body quotes the `Fact: retry limit` line).
- [ ] **Every number sourced.** Verify: each slide (PDF pages 1–10) has a grey evidence line, and every number on the page appears in that line's named source.
- [ ] **No unfilled slots.** Verify: the Task 4 Step 9 loop prints `0` for all ten slides.
- [ ] **The PDF matches the source.** Verify: `git log -1 --format=%ct -- business/pitch-deck.pdf` ≥ the same for `business/pitch-deck.pptx`.
- [ ] **Merged.** Verify: the PR from `docs/pitch-deck` shows "Merged" on GitHub; B2's row in [[Build order]] says `merged`.

## Never
- Write a verdict, a timing or a cost that isn't in the recorded run, `COST.md` or the business case.
- Show a mock-data screenshot without labelling it "mock data".
- Show a target capability (Verified Permissions, Athena, Lake Formation, connectors, CloudTrail, a second tenant) as built, or Cognito as built after a no-go.
- Put an account ID, token, console screen or real name (beyond the brief's) in a screenshot.
- Push to `develop` or `main`, or add attribution lines.

Related: [[B2 - Pitch deck - spec]], [[Build order]], [[How to execute a plan]]
