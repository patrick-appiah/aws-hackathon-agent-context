---
tags: [build, plan, area/business]
id: B3b
owner: Patrick + Michael
spec: "[[B3b - Architecture and cost slides - spec]]"
status: ready
updated: 2026-10-14
---
# B3b: The architecture slides and the cost + 90-day-plan slide (implementation plan)

> **For the executing person or agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Compare what you see with every `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never draw a component the documents don't have, or a figure `COST.md` doesn't hold.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[B3b - Architecture and cost slides - spec]]: **the authority**, with each slide's exact content (§3).
3. [[Judging rubric]] (3.1–3.3 and the required submissions), [[Business case and pitch]].
4. [[B2 - Pitch deck - spec]] (look and conventions), [[Teammate target diagram v1 review]], D-015 ([[2026-10-13 POC plus one target slice, target as 90-day roadmap]]).

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If it's still unclear, stop and ask Patrick.

**Goal:** `business/submission-slides.pptx` *(new)* and `business/submission-slides.pdf` *(new)* with slides A1 (POC), A2 (target) and A3 (cost and the 90-day plan).

**Architecture:** one new PowerPoint file in `business/`, built from a copy of the deck; diagrams rendered from `ARCHITECTURE.md` or taken from `docs/`. Branch `docs/submission-slides`.

**Tools:** PowerPoint (or Google Slides, as in B2); a browser for https://mermaid.live (paste Mermaid code, Actions → PNG); `git`, `unzip`, `sed`, `grep`.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: `docs/submission-slides` from an up-to-date `develop`, **after B2 is merged**.
- **Start state:**
  - `test -f business/submission-slides.pptx; echo $?` → `1`.
  - `unzip -l business/pitch-deck.pptx | grep -c -E 'ppt/slides/slide[0-9]+\.xml$'` → `10` (B2 merged). If `11`, stop: B2 isn't merged.
  - `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"` → write the count in `.superpowers/ledger-B3b.md`; the same after every commit.
- **Never claim the target as built (D-015);** Cognito is built only after a **go** at D2 12:00.
- **Every figure from `COST.md`** with its date; every plan line from `docs/ROADMAP.md`.
- **No secrets, synthetic data only:** no account IDs or ARNs on the slides (the Mermaid diagrams hold none).
- **Commits:** the messages given; no attribution lines; ask Patrick before pushing; Patrick merges. Stay in `business/`.

## Review Focus
1. **A1 shows only what is built:** no Verified Permissions, Athena, Glue, Lake Formation, EventBridge connectors or CloudTrail on it.
2. **A2's phase tags match `ARCHITECTURE.md` §6** box by box.
3. **A3's figures match `COST.md` today**, and its thresholds match `docs/ROADMAP.md` word for word where quoted.
4. **The diagrams are legible in the PDF** at 100% zoom (node labels readable).
5. **The Cognito line on A1 matches the D2 12:00 decision** and the deck's slide 7.

---

### Task 1: Create the file from the deck's template

**Files:** Create `business/submission-slides.pptx` *(new)*.

- [ ] **Step 1: Branch and baseline**
  ```bash
  cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
  test -f business/submission-slides.pptx; echo $?
  unzip -l business/pitch-deck.pptx | grep -c -E 'ppt/slides/slide[0-9]+\.xml$'
  uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
  git switch -c docs/submission-slides
  cp business/pitch-deck.pptx business/submission-slides.pptx
  mkdir -p .superpowers && printf '# Ledger: B3b Architecture and cost slides\n' > .superpowers/ledger-B3b.md
  ```
  Expected: `1`; `10`; the pass count (write `Start: <n> passed` in the ledger).
- [ ] **Step 2: Keep three slides.** Open `business/submission-slides.pptx`. Delete every slide except slide 7 (two columns) and slide 8 (tiles); duplicate slide 7 once. Order: slide-7 copy, slide-7 copy, slide 8. Clear their text. Change the slide numbers to `A1`, `A2`, `A3` (Insert → Header & Footer, or edit the number box). Save. Expected: `unzip -l business/submission-slides.pptx | grep -c -E 'ppt/slides/slide[0-9]+\.xml$'` prints `3`.

**Task done when:**
- `business/submission-slides.pptx` exists with 3 blank slides in the deck's look, numbered A1–A3.

### Task 2: A1 and A2, the architecture slides

**Files:** Modify `business/submission-slides.pptx`.
**Consumes:** `ARCHITECTURE.md` §3, §3b, §6; `docs/architecture-target-v2.png` *(new)* (created by A4a).

- [ ] **Step 1: Render the POC diagram.** Open `ARCHITECTURE.md` on `develop`; copy everything between the ` ```mermaid ` and ` ``` ` lines of §3. At https://mermaid.live, replace the editor's code with it; Actions → PNG → save as `poc.png` outside the repo (for example your Downloads folder). Expected: the PNG shows the nodes `Cognito`, `Step Functions Express · ask spine`, `critic · judges blind`, `Run ledger · DynamoDB`, and no `Verified Permissions` or `Lake Formation`.
- [ ] **Step 2: Fill A1** with the spec §3 text and `poc.png` on the left. Pick the Cognito line from the D2 12:00 decision (ask Patrick; `HANDOFF.md` records it). Save. Expected: A1's right panel has seven bullets, the last being one of the two Cognito lines.
- [ ] **Step 3: Get the target diagram.** `ls docs/architecture-target-v2.png`. If it exists, use it. If not, render §3b at mermaid.live as in Step 1 (save as `target.png`) and write `Ruling: A2 uses the §3b render; v2 not on develop at <time>` in the ledger. Expected: either the `ls` prints the path, or the ledger has the `Ruling:` line.
- [ ] **Step 4: Fill A2** with the spec §3 text, the diagram on the left, and the phase tags as small rounded labels next to: Verified Permissions (`Phase 1`), connectors / EventBridge / Glue / Athena (`Phase 1`), Lake Formation (`Phase 2`), CloudTrail (`Phase 2`), the tenant note (`Phase 3`), Cognito (`Built (POC)`, or `Phase 1` after a no-go). If the v2 PNG already carries phase labels, don't add duplicates. If A2 uses the §3b render, the evidence line ends `Rendered from ARCHITECTURE.md §3b; v2 visual pending.` Save. Expected: A2 shows `Phase 1`, `Phase 2` and `Phase 3` at least once each.
- [ ] **Step 5: Check and commit**
  ```bash
  for number in 1 2; do unzip -p business/submission-slides.pptx "ppt/slides/slide${number}.xml" | sed 's/<[^>]*>/ /g' | grep -c -E 'ARCHITECTURE.md §3|Phase 1'; done
  git add business/submission-slides.pptx
  git commit -m "Add the POC and target architecture slides for the submission"
  ```
  Expected: two numbers, each `1` or more; one commit.

**Task done when:**
- A1 shows the §3 render and seven control bullets; A2 shows the target diagram with Phase 1–3 tags and the POC → target table.

### Task 3: A3, cost and the 90-day plan (after `COST.md` is measured)

**Files:** Modify `business/submission-slides.pptx`.
**Consumes:** `COST.md` (the "Measured on" **average** per question, Scale **Pilot** and **Full**, "Cost levers"; the Per question **Total** row is the Q01 worked example and is not quoted); `docs/ROADMAP.md`.

- [ ] **Step 1: Copy the inputs to the ledger.** `git merge develop` first (to pick up the latest `COST.md` and `docs/ROADMAP.md`). Then `grep -n -E 'Measured on|Pilot|Full' COST.md` and write `Cost: average $<x> per question ("Measured on"), pilot $<y>, full $<z> (COST.md, <date of its last commit: git log -1 --format=%cs -- COST.md>)`. The per-question figure is the "Measured on" average, the same as business case line 34 and deck slide 9, never the Total row (the Q01 worked example). If any still says `TODO`, write `not measured` for it and tell Patrick and Abdul. Expected: one `Cost:` ledger line.
- [ ] **Step 2: Fill A3** with the spec §3 text: the cost table from the `Cost:` line; the four levers from `COST.md` "Cost levers"; the three phase bars, the team and dependencies, and the three risks from `docs/ROADMAP.md`. If `docs/ROADMAP.md` changed since the spec was written, use its wording and write a `Ruling:` line. Save. Expected: A3 has three columns: cost, 90 days, top 3 risks.
- [ ] **Step 3: Check and commit**
  ```bash
  unzip -p business/submission-slides.pptx ppt/slides/slide3.xml | sed 's/<[^>]*>/ /g' | grep -c -E 'COST.md|ROADMAP|Stop if'
  for figure in $(unzip -p business/submission-slides.pptx ppt/slides/slide3.xml | sed 's/<[^>]*>/ /g' | grep -o '\$[0-9][0-9,.]*' | sort -u); do printf '%s ' "$figure"; grep -c -F "$figure" COST.md; done
  git add business/submission-slides.pptx
  git commit -m "Add the cost and 90-day plan slide for the submission"
  ```
  Expected: `1` or more; every dollar figure prints `1` or more (a figure of `$0.50`, the ceiling, may come from `config.py` instead: then it prints `0` here and is allowed only in the levers line); one commit.

**Task done when:**
- A3's cost figures are all found in `COST.md` (or say `not measured`), and its plan, team, dependencies and risks match `docs/ROADMAP.md`.

### Task 4: Export the PDF and open the PR

**Files:** Create `business/submission-slides.pdf` *(new)*.

- [ ] **Step 1: Export** as in B2 (File → Export → PDF, all slides). Expected: `business/submission-slides.pdf` opens with 3 pages.
- [ ] **Step 2: Read it.** At 100% zoom, the diagram labels are readable; Ctrl+F `TBC`, `TODO` find nothing. If a diagram is unreadable, re-render it at mermaid.live with a larger size (Actions → PNG, then scale the image up on the slide and crop the margins). Expected: readable labels; no matches.
- [ ] **Step 3: Review Focus.** Five lines, each result in the ledger. Expected: five `Review <n>: ok` lines.
- [ ] **Step 4: Commit and PR (PR with Patrick's OK only)**
  ```bash
  git add business/submission-slides.pdf
  git commit -m "Export the submission slides PDF"
  git log -1 --format=%ct -- business/submission-slides.pdf; git log -1 --format=%ct -- business/submission-slides.pptx
  uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
  git diff develop --stat
  ```
  Expected: the first timestamp ≥ the second; the start count; the diff lists only the two `business/submission-slides.*` files. Then `git push -u origin docs/submission-slides`, PR to `develop` titled `Architecture, cost and 90-day plan slides for the submission`; the body lists the sources and any `Ruling:`. Set B3b's row in [[Build order]] to `in review (PR #<n>)`. Expected: the PR shows 2 files.

**Task done when:**
- `business/submission-slides.pdf` has 3 pages and is committed after the pptx.
- A PR from `docs/submission-slides` to `develop` touches only the two files.

## Done means
- [ ] **Three slides.** Verify: `unzip -l business/submission-slides.pptx | grep -c -E 'ppt/slides/slide[0-9]+\.xml$'` → `3`; the PDF opens with 3 pages.
- [ ] **POC and target, separately (3.1).** Verify: PDF page 1 shows the §3 diagram and no Verified Permissions, Athena, Lake Formation or CloudTrail; page 2 shows the target diagram with `Phase 1`, `Phase 2`, `Phase 3` tags and the five-row POC → target table.
- [ ] **Cost at pilot and full scale (3.2).** Verify: page 3 shows the per-question, pilot and 100-a-day figures, each found in `COST.md` (Task 3 Step 3 loop), or the words `not measured`.
- [ ] **The plan with risks (3.3).** Verify: page 3 shows three phases with their go/no-go lines, the team, the client dependencies and three risks with "Stop if", matching `docs/ROADMAP.md`.
- [ ] **Sources on every slide.** Verify: each page has a grey evidence line naming `ARCHITECTURE.md`, `COST.md` or `docs/ROADMAP.md`.
- [ ] **No unfilled slot.** Verify: `for number in 1 2 3; do unzip -p business/submission-slides.pptx "ppt/slides/slide${number}.xml" | sed 's/<[^>]*>/ /g' | grep -c 'TBC\|TODO\|&lt;'; done` prints three `0`s.
- [ ] **Merged.** Verify: the PR from `docs/submission-slides` shows "Merged"; B3b's row in [[Build order]] says `merged`.

## Never
- Put a target-only layer on A1, or show Cognito as built after a no-go.
- Use the v1 target PNG.
- Type a cost figure that isn't in `COST.md`.
- Edit `ARCHITECTURE.md`, `COST.md`, `docs/ROADMAP.md` or anything in `docs/`.
- Push to `develop` or `main`, or add attribution lines.

Related: [[B3b - Architecture and cost slides - spec]], [[Build order]], [[How to execute a plan]]
