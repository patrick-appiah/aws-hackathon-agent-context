---
tags: [build, plan, area/frontend, area/demo]
id: F6
owner: Clement (with Patrick)
spec: "[[F6 - Demo rehearsal and backup video - spec]]"
status: ready
updated: 2026-10-14
---
# F6: demo rehearsal and backup video (plan, no code)

> **For the executing person or agent:** follow [[How to execute a plan]] for the order, the ledger and the PR. There is no code and no test suite: every step says exactly what to do and what you must see. Do the tasks in order. If what you see differs from `Expected:`, stop, write it in the rehearsal log's "What went wrong" column, fix it with the owner of that part, and run the step again.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[F6 - Demo rehearsal and backup video - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger as a `Ruling:` line.
3. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Clement - front end]].
4. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
5. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
6. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

**Goal:** `DEMO.md` is the real script and checklist, two cold rehearsals are logged, and a 2-minute backup video is on the laptop and a USB stick.

**Tools:** a laptop with Chrome or Edge (two profiles), OBS Studio (https://obsproject.com, free), a USB stick, a stopwatch (phone), git and a text editor for `DEMO.md`.

**Dry-run:** not possible (needs the deployed portal and the live agent loop on Day 2). Every step below is to **verify in AWS**.

## Global Constraints
- **Repo:** branch **`docs/demo-rehearsal`** from an up-to-date `develop` (Day 2, after M4 code freeze at 14:00). PR to `develop`; Patrick merges. No `Co-Authored-By` and no "Generated with" lines.
- **Start state:** every front-end item (F1a–F5) and the back-end items they need are `merged` and deployed; `DEMO.md` on `develop` may already hold Abdul's eval and cost lines (A4b): keep them.
- **Synthetic data only.** No real company, system or person names in the video, the script or the narration; people by role. Close every other app and tab before recording (no e-mail, chat or file names on screen).
- **No secrets on screen or in files:** type passwords off camera (sign in before recording starts); never show a token, the AWS console's credentials page or `~/.npmrc`.
- `eu-west-1` only.

## Review Focus (check by hand at the end)
1. Every figure the script names appears on screen exactly (58 %, 96 %, 98 % target, 7, 18 days, 102, 6 behind, 103 %; DEF-0412, RC-C3-E4-customers, DEF-0398).
2. Both rehearsals started from cold (new private windows, no question asked before the timer started except the pre-flight warm-up).
3. The video shows nothing private (pause it every 10 seconds and look at the edges of the screen).
4. The video is under 2:05 and the figures are readable at full screen.
5. `DEMO.md` kept Abdul's lines and has no placeholders left except the blanks the rehearsal fills.

---

### Task 1: Write `DEMO.md`
**Files:** Modify `DEMO.md` (repo root).
- [ ] **Step 1:** `git switch develop && git pull && git switch -c docs/demo-rehearsal`; `mkdir -p .superpowers && printf '# Ledger: F6 demo\n' > .superpowers/ledger-F6.md`.
- [ ] **Step 2:** Open `DEMO.md`. Copy aside any lines Abdul added (A4b: the cost words in the 2:35–3:00 row, two pre-flight items, the "Eval and cost answers (for Q&A)" section).
- [ ] **Step 3:** Replace the file's content with the text below, then put Abdul's lines back: his two pre-flight items at the end of "Pre-flight checklist", his section at the end of the file, and his cost words in the 2:35–3:00 row.
```markdown
# DEMO.md

> Rehearse twice, on the clock, **from a cold start** (Day 2, 16:00–17:00). Also record a 2-minute backup video. Relying on it caps criterion 2.2 at 3, so the live run must work. Drivers: Clement (portal), Patrick (presenter). Region **eu-west-1**. Data: synthetic only.

## Before you start (two browser windows)
- **Window A (driver, the CFO):** a private window on `https://<CloudFront domain>/`, signed in as `demo-cfo`.
- **Window B (approver):** a second private window (another browser profile), signed in as `demo-delivery-lead`, left on the dashboard.
- If the Cognito go/no-go was **no-go**: `portal-config.json` has `"authMode": "none"`; use the role switcher (CFO in A, Delivery lead in B) and say "sign-in is switched off for this demo; the scope rules are enforced by the API" (HANDOFF says so).

## 3-minute script
| Time | Who | On screen | What we say |
|---|---|---|---|
| 0:00–0:30 | Presenter | Problem slide | "Eighteen-month migration, four legacy ERPs onto one platform. The sponsor's picture is a deck that's weeks old, and every 'what's blocking cutover?' costs a consultant two days." |
| 0:30–1:00 | Driver | **Window A, the one screen:** 58 % records reconciled, pass rate 96 % against 98 %, 7 open blockers (oldest 18 days), 102 days to final cutover (6 behind plan), capacity 103 %; E1 Live, E2 On track, E3 At risk, E4 Blocked | "Every number here is computed from the migration's own artefacts. Nobody typed it." **Click 58 %**: the drawer shows its 49 source rows. "Every figure opens the rows it came from." |
| 1:00–1:45 | Driver | Click **"What is blocking cutover for entity 4?"**; open **"How this answer was checked"** | Read the headline and the three bullets; click the `RC-C3-E4-customers` chip: "customer master reconciles at 91.2 % against 98 %, 212 records rejected for invalid tax IDs, open defect DEF-0412, 18 days old." Point at the trace: "planner, retriever, analyst, then a blind critic, each with its prompt version." Point at the cost line. |
| 1:45–2:15 | Driver | The **"Could not verify"** list: DEF-0398 | "The defect log says DEF-0398 is closed. The reconciliation says customers still fail. The critic rejected the claim that it still blocks cutover, and tells you why. A deck would have said green." |
| 2:15–2:35 | Driver | **Publish as status pack** → Send for approval → "Awaiting approval"; switch to **Window B** → `/approve/<run>` → note "Approved for the steering committee" → **Approve** → "Approved" | "Nothing goes to the client until the delivery lead signs it. The only write in the system happens here, after a human approves." |
| 2:35–3:00 | Presenter | Value slide | Two days → seconds per question; status-pack hours saved per month; cost per question (from COST.md); the pilot proposal. |

**If asked about access (Q&A):** in Window B sign out, sign in as `demo-entity-lead-e4`: only Entity 4; click "What is blocking cutover for entity 2?" → "You can see E4 only. E2 is outside your access."

## Pre-flight checklist (15 minutes before)
- [ ] `aws sts get-caller-identity --profile hackathon` shows account `796973512193`; the console region is **eu-west-1**
- [ ] `curl -s https://<CloudFront domain>/portal-config.json` shows `"dataSource": "http"` and the expected `authMode`
- [ ] The portal's one screen shows 58 %, 96 %, 7 blockers (oldest 18 days), 102 days (6 behind plan) and 103 % capacity
- [ ] **One warm-up question** asked in Window A ("What is blocking cutover for entity 4?"); its time to answer noted here: ____ s (cold-start latency known)
- [ ] Window B signed in as the delivery lead
- [ ] Browser zoom 125 %, notifications off, other tabs closed, laptop on mains power
- [ ] Backup video on the laptop **and** on the USB stick, opened once to check it plays
- [ ] Fresh data generated, `uv run --locked pytest` green

## Rehearsal log
| # | When | Cold start? | Total time | What went wrong | Fix |
|---|---|---|---|---|---|
| 1 | | yes | | | |
| 2 | | yes | | | |

## Backup video
- File: `demo-backup-2026-10-15.mp4` (1920×1080, about 2:00), on the presenter's laptop in `Videos/` and on the USB stick. Not committed to the repo.
- Recorded from the live portal on <date time>, following the script from 0:30 to 2:35 with a short spoken intro and close.
```
- [ ] **Step 4:** Replace `<CloudFront domain>` with the real domain from Michael's stack outputs (it is not a secret). Expected: `grep -c "<CloudFront domain>" DEMO.md` prints `0`.
- [ ] **Step 5:** `git add DEMO.md && git commit -m "DEMO: the real script, two windows, pre-flight, rehearsal log and video"`. Expected: `1 file changed`.

**Task done when:** `DEMO.md` has the sections "Before you start", "3-minute script", "Pre-flight checklist", "Rehearsal log", "Backup video" (`grep -c "^## " DEMO.md` ≥ 5) and Abdul's lines are still there.

### Task 2: Install and set up OBS Studio (once)
- [ ] **Step 1:** Download OBS Studio from https://obsproject.com and install it. Open it; skip the auto-configuration wizard ("Cancel").
- [ ] **Step 2:** Settings → Output → Recording: Recording Path = your `Videos` folder; Recording Format = **MP4**; Encoder = the hardware encoder if listed (NVENC/QuickSync/Apple VT), else x264. Settings → Video: Base and Output resolution **1920×1080**, 30 FPS. OK.
- [ ] **Step 3:** In "Sources" press **+** → **Display Capture** (macOS: "macOS Screen Capture") → the laptop's screen → OK. Press **+** → **Audio Input Capture** → your microphone → OK.
- [ ] **Step 4:** Test: Start Recording, say "test" while clicking in the browser for 10 seconds, Stop Recording. Open the file from `Videos`. Expected: the browser is sharp at full screen and your voice is audible. Delete the test file.

**Task done when:** a 10-second test recording played back sharp and audible.

### Task 3: Rehearsal 1 (cold start)
- [ ] **Step 1:** Close every browser window. Run the **pre-flight checklist** in `DEMO.md` top to bottom; tick each line in your copy. Expected: every line true; the warm-up question's time is written in.
- [ ] **Step 2:** Patrick starts the stopwatch and the slides; you follow the script row by row. At each row's end, glance at the stopwatch.
- [ ] **Step 3:** Expected, in order: the one-screen figures; 58 % → "49 source rows"; the entity 4 answer with three bullets and the trace; "Could not verify" with DEF-0398; publish → "Awaiting approval"; window B → Approve → "Approved". Total ≤ 3:00.
- [ ] **Step 4:** Fill row 1 of the rehearsal log (time, total, what went wrong, the fix and who owns it). Commit: `git commit -am "DEMO: rehearsal 1 logged"`.

**Task done when:** row 1 is filled and committed; every "what went wrong" has an owner.

### Task 4: Rehearsal 2 (cold start, after the fixes)
- [ ] **Step 1:** Confirm each fix from rehearsal 1 is in (ask its owner). Close every browser window.
- [ ] **Step 2:** Repeat Task 3 Steps 1–3 exactly.
- [ ] **Step 3:** Fill row 2; commit `git commit -am "DEMO: rehearsal 2 logged"`. Expected: total ≤ 3:00 and nothing in "What went wrong" that would stop the demo.

**Task done when:** row 2 shows ≤ 3:00 and is committed.

### Task 5: Record the 2-minute backup video
- [ ] **Step 1:** Run the pre-flight checklist again (sign in to both windows **before** recording; type no password on camera). Close every other app; turn notifications off (Windows: Focus assist / Do not disturb; macOS: Focus).
- [ ] **Step 2:** OBS: Start Recording. Follow the script from 0:30 to 2:35, saying a one-sentence intro ("This is the ERP Migration Progress Portal on AWS, with synthetic data") and a one-sentence close ("Every number and every claim traces to its source rows, and nothing is published without the delivery lead's approval"). Stop Recording.
- [ ] **Step 3:** Rename the file to `demo-backup-2026-10-15.mp4`. Check its length: right-click → Properties → Details (Windows) or Get Info (macOS). Expected: between 1:45 and 2:05. Longer: record again, faster on the 1:00–1:45 row.
- [ ] **Step 4:** Watch it once at full screen. Expected: every figure readable, voice audible, no private information (Review Focus 3).
- [ ] **Step 5:** Copy it to the USB stick; play it from the stick once. Submit it as the organisers ask (Patrick knows where). Fill the "Backup video" lines in `DEMO.md` (date and time recorded) and commit: `git commit -am "DEMO: backup video recorded"`. **Never** `git add` the video.

**Task done when:** the MP4 plays from the laptop and from the stick, lasts 1:45–2:05, and `DEMO.md` says when it was recorded.

### Task 6: PR (after Clement's and Patrick's OK)
- [ ] **Step 1:** Work through the Review Focus; write each result in the ledger.
- [ ] **Step 2:** `git diff develop --stat` lists only `DEMO.md`.
- [ ] **Step 3:** With the OK: `git push -u origin docs/demo-rehearsal`; open the PR to `develop` titled "DEMO: script, pre-flight, two rehearsals, backup video (F6)". Body: the two rehearsal times, the video length, what was fixed. No attribution lines.
- [ ] **Step 4:** [[Build order]] row F6: `in review (PR #nn)`, then `merged`.

**Task done when:** the PR is open to `develop` and [[Build order]] shows it.

## Never
- Commit the video, a password, a token or a screenshot with a real name.
- Record while signing in (passwords) or with other apps visible.
- Skip a cold start ("it worked earlier" is not a rehearsal).

## Done means
- [ ] **`DEMO.md`:** on the branch, `grep -c "^## " DEMO.md` ≥ 5; the script table names 58 %, DEF-0398 and "Approve"; `grep -c "<CloudFront domain>" DEMO.md` → `0`; Abdul's "Eval and cost answers" section present (if A4b merged). *Verify:* run the greps.
- [ ] **Two cold rehearsals:** the rehearsal log has rows 1 and 2 filled, each "Cold start? yes", total time ≤ 3:00 in row 2. *Verify:* read `DEMO.md`.
- [ ] **Video:** `demo-backup-2026-10-15.mp4` on the presenter's laptop and the USB stick, 1:45–2:05 long (file properties), plays at full screen with readable figures. *Verify:* open it from both places.
- [ ] **Submitted:** the organisers' submission has the video (Patrick confirms in the ledger).
- [ ] **PR:** open to `develop` titled "DEMO: script, pre-flight, two rehearsals, backup video (F6)"; [[Build order]] row F6 updated. *Verify:* `gh pr list --head docs/demo-rehearsal`.

Related: [[F6 - Demo rehearsal and backup video - spec]], [[Build order]], [[Deploy and demo checks]], [[How to execute a plan]]
