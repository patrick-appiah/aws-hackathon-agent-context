---
tags: [build, plan, area/business]
id: B1
owner: Patrick + Michael
spec: "[[B1 - Business case figures and validation - spec]]"
status: ready
updated: 2026-10-14
---
# B1: Business case figures and the validation session (implementation plan)

> **For the executing person or agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Every step that changes or checks something has an `Expected:` line: compare what you see with it, every time. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise a figure, a quote or a source.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]]: the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[B1 - Business case figures and validation - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger.
3. [[Business case and pitch]] (the brief), [[Pitch track grading rubric]], [[Judging rubric]] (1.1, 1.2), [[Problem statement]].
4. [[Workstreams]] §7 (rules), [[2026-10-13 POC plus one target slice, target as 90-day roadmap]] (D-015), [[Graders are AI and read only what is written]].

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Patrick.

**Goal:** `business/business-case.md` has no `[TBC]`; every figure on the closed lines says where it came from; the validation session is recorded in `business/validation-session.md` *(new)*; `business/product-spec.md` has a feasibility note per must-do; both PDFs match their Markdown.

**Architecture:** documents only, all in `business/` (workstream 7's folder, `docs/TEAM_PLAN.md` §2). Two pull requests, because the inputs arrive on different days:
- PR 1, D1 evening, branch `docs/validation-session`: the session record and the lines that need only the problem owner (3, 23, 79, and the sizing rows if corrected).
- PR 2, D2 14:00–15:00, branch `docs/business-case-measured`: the measured lines (31, 34, 46, the net value, 51), the two consistency fixes, the product-spec pass and both PDFs. The measured inputs are read from A5a's and A3b's **open** PR branches as soon as they are pushed (about 14:40), and re-checked once those PRs merge (Task 3 Step 10).

**Tools:** a text editor (VS Code); `git`; a shell for `grep`; the Markdown-to-PDF tool Michael used for commit `68866af` (if someone else renders: VS Code extension **Markdown PDF** by yzane, command "Markdown PDF: Export (pdf)"); `uv run --locked pytest` only to run the documentation guards (no Python is written).

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your own clone). Branches `docs/validation-session` and `docs/business-case-measured`, each from an up-to-date `develop`.
- **Start state** (check before Task 2 and again before Task 3):
  - `grep -c 'TBC' business/business-case.md` → `7` (lines 3, 23, 31, 34, 46, 51, 79). Before Task 3 it is `4` (31, 34, 46, 51) if PR 1 is merged.
  - `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"` → `204 passed`, `TOTAL` 96%, when only C1 is merged after today's `develop`. Later items add tests, so **write the number you see in the ledger** (`.superpowers/ledger-B1.md`); after every commit the count must be the same, because B1 changes no code.
- **Every figure carries a label:** *(brief)*, *(validated: name, date)*, *measured* (with the file), or *proposed* (with the assumption and who confirms). Never present an estimate as measured.
- **The executive is the CFO** (with the programme sponsor), never the CIO.
- **Names:** only the problem owner and oversight as the brief names them (Vanessa Addo, Joseph Akayesi), and our own team. No real portfolio-company, system or client-person names. Synthetic data only. No secrets.
- **Never claim the target as built (D-015):** only the POC plus the Cognito slice is built.
- **The documentation guards read every tracked `.md` file:** no bare `pytest` in backticks, no `uv run pytest`, no `python scripts/…` without `uv run`, no `test_*.py` path outside `tests/`.
- **Commits:** small, the messages given. No `Co-Authored-By` and no "Generated with" lines. Never push to `develop` or `main`; ask Patrick before pushing; Patrick merges.
- **Stay in `business/`.** Don't edit `COST.md`, `EVALS.md`, `docs/ROADMAP.md` or anyone else's file; tell the owner instead.

## Review Focus (what no check catches; do it by hand at the end)
1. **Every *measured* figure is traceable:** open the file each one names and find the same number there.
2. **The quote is word for word and agreed:** compare it with the session notes; consent is recorded as `yes`.
3. **The arithmetic adds up:** recompute net value, payback and total value from the figures in the document with a calculator.
4. **No target capability reads as built:** search the business case for Verified Permissions, Athena, Lake Formation, connectors, CloudTrail, second tenant; each appears only as roadmap or target.
5. **The product-spec feasibility notes match the [[Build order]] on the day:** each `Built:` note's item is `merged`.

---

### Task 1: Book the validation session (D1, before 09:30)

**Files:** none.
**Produces:** a calendar booking for D1 09:30, 15 minutes. **Consumes:** the brief's names (Vanessa Addo, Joseph Akayesi).

- [ ] **Step 1: Send the invite.** In the team's calendar tool, create an event: D1, 09:30–09:45. Title: `ERP Migration Progress Portal: 15-minute validation (Team Cloud 9)`. Guests: Vanessa Addo, Joseph Akayesi, Patrick, Michael. Body, exactly:
  ```text
  We're building the ERP Migration Progress Portal from your problem statement. We'd like 15 minutes to check three things before we write them into the business case the judges read:
  1. The executive and the pain: is it the CFO funding the consolidation, with the programme sponsor? What happened the last time one of them asked "what is blocking cutover?"
  2. The cost today: we assume 6 status questions a month at 2 consultant-days each, 3 days a month to rebuild the status pack, and a $1,000 blended day rate. Which is wrong?
  3. How many portfolio companies have an ERP consolidation planned or under way in the next 12 to 24 months?
  We'd also like to quote one sentence from you by name and role, only with your OK.
  ```
  Expected: the event shows in the calendar with four guests.
- [ ] **Step 2: Wait for replies until D1 09:15.** Expected: Vanessa Addo has accepted (Joseph Akayesi optional). If she declines or doesn't reply by 09:15, message her for any 15-minute slot before D1 12:00 and tell Patrick. Expected: a confirmed time before 12:00, or a written "no" you can quote in the record.
- [ ] **Step 3: Ledger.** `mkdir -p .superpowers && printf '# Ledger: B1 Business case figures and validation\nTask 1: session booked for <date> <time>, accepted by <names>\n' > .superpowers/ledger-B1.md`. Expected: `cat .superpowers/ledger-B1.md` shows the line.

**Task done when:**
- The calendar event exists with Vanessa Addo as a guest, and her acceptance (or her written decline) is visible.
- `.superpowers/ledger-B1.md` names the booked time.

### Task 2: Run the session, record it, and close lines 3, 23 and 79 (D1)

**Files:**
- Create: `business/validation-session.md` *(new)*
- Modify: `business/business-case.md` (lines 3, 23, 79; rows 41–44 and lines 48–50 only if question 2 corrects an assumption)

**Produces:** the session record; three closed `[TBC]` lines. **Consumes:** the answers.

- [ ] **Step 1: Branch and baseline**
  ```bash
  cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
  grep -c 'TBC' business/business-case.md
  uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
  git switch -c docs/validation-session
  ```
  Expected: `7`; then the pass count and coverage, which you write in the ledger as `Start: <n> passed, <pct>%`.
- [ ] **Step 2: Run the session.** Patrick asks the three questions word for word from the spec §3; Michael types the answers as spoken into a scratch note. At the end, read back the sentence you want to quote and ask for consent. Expected: three answers written down, one agreed sentence, consent recorded as yes or no.
- [ ] **Step 3: Create `business/validation-session.md`** with exactly the structure in the spec §3, filled from the scratch note. Keep their words; fix only obvious typing errors. If the session didn't happen by D1 12:00, the file holds only the title and the "not held" sentence from the spec §3. Expected: `grep -c 'Answer (as spoken)' business/validation-session.md` prints `3` (or the "not held" sentence is present: `grep -c 'not held' business/validation-session.md` prints `1`).
- [ ] **Step 4: Line 3 (the legend).** Find the line that starts `> Facts marked *(brief)*` and replace the whole line with the "Line 3, always" text in the spec §4. Expected: `grep -n 'TBC' business/business-case.md | head -1` no longer shows line 3.
- [ ] **Step 5: Line 23.** Find the line that starts `**Validated with:**` and replace it with variant A, A-without-consent, or B from the spec §4, filled from `business/validation-session.md`. Expected: `grep -n 'Validat' business/business-case.md` shows the new line with a date in `YYYY-MM-DD` form and no `TBC`.
- [ ] **Step 6: Line 79.** Find the line that starts `- **[TBC: how many portfolio companies` and replace it with variant A (count given) or B. For A, total = count × $261,000, written with a thousands comma (for example 4 → `$1,044,000`). Expected: `grep -n 'portfolio companies' business/business-case.md` shows the new line, labelled *validated* or *proposed*.
- [ ] **Step 7: Corrections from question 2 (only if any).** For each corrected assumption, change its row in the sizing table (rows 41–44) to `**<value>** | Validated: <name>, <YYYY-MM-DD> (`business/validation-session.md`)`. Then recompute and rewrite lines 48–50 with the same formulas:
  - days saved = questions × days per question + pack days − 0.5;
  - value per month = days saved × day rate;
  - value per programme = value per month × 18.

  If any of these change, also change `$14,500` and `$261,000` everywhere in the file (`grep -n '14,500\|261,000' business/business-case.md` lists them) and tell B2/B3 (the deck uses them). Expected: the grep shows only the new values, and the arithmetic checks with a calculator.
- [ ] **Step 8: Check and commit**
  ```bash
  grep -c 'TBC' business/business-case.md
  uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
  git add business/validation-session.md business/business-case.md
  git commit -m "Record the validation session and close the problem-owner figures in the business case"
  ```
  Expected: `4`; the same pass count as the start; one commit.
- [ ] **Step 9: Vault and PR (with Patrick's OK only).** Add one line to the vault session note for that day (`03 Sessions/<YYYY-MM-DD>.md`, "Shipped"): `Validation session with Vanessa Addo and Joseph Akayesi held <time> (or not held: reason); recorded in business/validation-session.md`. Then `git push -u origin docs/validation-session` and open a PR to `develop` titled `Validation session and problem-owner figures in the business case`. The body lists the closed lines and any corrected assumption. Expected: the PR shows 2 files changed, both in `business/`.

**Task done when:**
- `grep -c 'TBC' business/business-case.md` prints `4` on the branch, and the only remaining ones are lines 31, 34, 46 and 51 (`grep -n TBC` shows them).
- `business/validation-session.md` exists and either has three "Answer (as spoken)" sections or the "not held" sentence.
- A PR from `docs/validation-session` to `develop` is open (or merged), touching only `business/`.

### Task 3: Close the measured lines 31, 34, 46 and 51 (D2, after the 14:00 freeze)

**Files:** Modify `business/business-case.md`.
**Produces:** four closed lines, a new "Net value per month" line, two consistency fixes. **Consumes:** `COST.md` (the "Measured on" line's **average** cost per question, and the Scale table's **Pilot** monthly cost; A3b/H5), read first from A3b's open PR branch `docs/cost-measured`; the recorded `evals/results/run-<stamp>.json` (case `Q01`: `seconds`, `status`; H6/L6), read first from A5a's open PR branch `docs/eval-results-<yyyymmdd>-<hhmm>`; `docs/ROADMAP.md` "Team (proposed)" (L7).

- [ ] **Step 0: Book the run (D2 09:00 stand-up).** Ask Linus, in the team channel so it's written: *"B1, B2 and A3b need one recorded eval run with an asker. Please start it at 14:00 sharp, right after the freeze, mark it recorded, and hand the file to Abdul (A5a, A3b) straight away."* Expected: Linus's written yes with the asker he'll use (deployed API or local); ledger line `Run booked: 14:00, <asker>, confirmed by Linus <time>`.
- [ ] **Step 1: Branch and baseline**
  ```bash
  cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
  grep -n 'TBC' business/business-case.md
  uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
  git switch -c docs/business-case-measured
  ```
  Expected: four lines (31, 34, 46, 51; numbers may shift by the lines Task 2 changed); the pass count, written in the ledger.
- [ ] **Step 2: Collect the inputs from the open PR branches and write them in the ledger.** Don't wait for the merges: A5a and A3b push their branches at about 14:40.
  ```bash
  git fetch origin
  git branch -r --list 'origin/docs/eval-results-*' 'origin/docs/cost-measured'
  git ls-tree --name-only origin/docs/eval-results-<yyyymmdd>-<hhmm> evals/results/
  git show origin/docs/eval-results-<yyyymmdd>-<hhmm>:evals/results/<file> > .superpowers/<file>
  git show origin/docs/cost-measured:COST.md > .superpowers/COST-measured.md
  git rev-parse --short origin/docs/eval-results-<yyyymmdd>-<hhmm> origin/docs/cost-measured
  ```
  Use the `docs/eval-results-…` branch whose time is the 14:00 run (Step 0). Expected: both branches listed; the `ls-tree` prints `evals/results/run-<yyyymmdd>-<hhmmss>.json`; two short hashes, written in the ledger as `Read from: <A5a branch> @ <hash>, docs/cost-measured @ <hash>`. If a branch is gone because its PR already merged, read the same file from `develop` instead (`ls evals/results/`, `COST.md`) and write `Read from: develop @ <hash>`.
  - Time: open `.superpowers/<file>` and find the case whose `"id"` is `"Q01"`. Copy `seconds` and `status`, and note whether the run used the deployed-API asker (L6) or the local asker (H6): the file's top-level `"asker"` field, or ask Linus. Expected: ledger line `Inputs: Q01 <seconds> s (<status>, <file>, <asker>)`.
  - Cost per question: `grep -n 'Measured on' .superpowers/COST-measured.md` and copy the **average** (`average **$<…>** per question`). This is the team's one cost per question (the deck, the pitch script and `HANDOFF.md`/`DEMO.md` quote the same figure). Never use the "Per question" table's Total row: it is labelled "Q01 worked example" and is one question. Expected: ledger line `Inputs: cost per question $<average> (COST.md "Measured on" average, <file>)`.
  - Pilot monthly cost: in `.superpowers/COST-measured.md`, the "Scale" table's **Pilot** row, last column. Expected: ledger line `Inputs: pilot monthly $<value> (COST.md Pilot)`.
  - If any input still says `TODO` or doesn't exist, on the open branches or on `develop`, at **15:30**, use variant B for that line and tell Patrick. Expected: a ledger line `Ruling: <line> uses variant B because <input> missing at <time>`.
- [ ] **Step 3: Line 31.** Find the row that starts `| Time to answer a status question` and replace it with variant A or B from the spec §4. If `Q01`'s `status` is not `pass`, still write the real seconds, and add `; the answer did not pass all checks in that run, see `EVALS.md`` before the closing bracket. Expected: `grep -n 'Time to answer' business/business-case.md` shows `measured` and the file name, or `proposed`.
- [ ] **Step 4: Line 34.** Find the row that starts `| Cost per answered question` and replace it with variant A (the "Measured on" average from the ledger) or B. Expected: `grep -n 'Cost per answered question' business/business-case.md` shows `$2,000` and either `measured` (with the same average as the `Inputs: cost per question` ledger line) or `proposed`.
- [ ] **Step 5: Line 46.** Find the row that starts `| Portal run cost per month` and replace it with variant A or B. Expected: `grep -n 'Portal run cost per month' business/business-case.md` shows a dollar figure and no `TBC`.
- [ ] **Step 6: Net value.** Directly after the line that starts `- **Value per month**`, insert the "Net value per month" line from the spec §4, with net = $14,500 (or the Task 2 value) − the line-46 figure, rounded to whole dollars. Expected: `grep -n 'Net value per month' business/business-case.md` shows one line, and $14,500 − line 46 = the figure shown.
- [ ] **Step 7: Line 51.** Find the line that starts `- **Payback**` and replace it with the spec §4 text. Months = 105,000 ÷ net, rounded to one decimal (for example 105,000 ÷ 14,400 = 7.3). If Task 2 changed the day rate, recompute $105,000 = 105 × day rate, $87,500 = 87.5 × day rate and $192,500 = their sum. Expected: `grep -n 'Payback' business/business-case.md` shows `*Proposed*`, `$105,000` (or the recomputed figure) and the months.
- [ ] **Step 8: The two consistency fixes** from the spec §4 (line 72: `(EVALS.md Q13, a roadmap question, not run in the POC)`; line 74: ` (*proposed*)` after `**within 5 working days**`). Expected: `grep -c 'not run in the POC' business/business-case.md` prints `1`; `grep -c 'within 5 working days\*\* (\*proposed\*)' business/business-case.md` prints `1`.
- [ ] **Step 9: Check and commit**
  ```bash
  grep -c 'TBC' business/business-case.md
  uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
  git add business/business-case.md
  git commit -m "Close the measured figures in the business case: time, cost, run cost and payback"
  ```
  Expected: `0`; the same pass count as Step 1; one commit.
- [ ] **Step 10: Re-check after the A5a and A3b merges** (do it as soon as both PRs show "Merged", even if you are already in Task 4 or 5).
  ```bash
  git fetch origin
  git diff <A5a hash from the ledger> origin/develop -- evals/results/<file>
  git diff <A3b hash from the ledger> origin/develop -- COST.md
  ```
  Expected: no output for the results file; for `COST.md`, no change to the "Measured on" average or the Pilot row. If either changed, update lines 31, 34, 46, the net value and 51 from `develop` with the same steps, commit `Business case: re-check the measured figures after the COST and EVALS merges`, re-render the PDF (Task 5 Step 1) and add a `Ruling:` line. Ledger: `Re-check after merge: same | changed: <what>`.

**Task done when:**
- `grep -c 'TBC' business/business-case.md` prints `0`.
- Each of lines 31, 34, 46 and 51 says `measured` with a file name, or `proposed` with who confirms (`grep -n -E 'Time to answer|Cost per answered|Portal run cost|Payback' business/business-case.md` shows all four with their labels).
- The ledger lists each input with its source file and branch hash, any variant B with a `Ruling:` line, and a `Re-check after merge:` line once A5a and A3b are merged.

### Task 4: The product-spec rubric pass (D2, same branch)

**Files:** Modify `business/product-spec.md`.
**Produces:** a **Feasibility** column on the four requirement tables, F9 aligned with the decided retry limit, a corrected test count, the D-015 note on P1. **Consumes:** [[Build order]] statuses on the day; D-022 (`DECISIONS.md`: at most 2 attempts in total, one retry) (A1 Task 4 Step 2).

- [ ] **Step 1: Read the Build order.** In the vault, `git pull`, open [[Build order]] and write in the ledger the status of: L1, L2, L3, L5, P1, P2, H1, H2, H3, H4, Y2, M3*, F1, F2, F3, F5. Expected: 16 ledger lines `Build order <ID>: <status>`.
- [ ] **Step 1b: The retry limit.** Read D-022 (`DECISIONS.md`: at most 2 attempts in total, one retry) (A1's ledger line `Q09: <n> verdicts; retry limit: <his words>; …`, from [[A1 - Eval set review and manual checks - plan]] Task 4 Step 2; ask Abdul for it). Write it in the B1 ledger as `Fact: retry limit = <his words> (Huvison, <date>)`. In `business/product-spec.md`, find the F9 row (today: `A rejected claim is re-planned at most **2** times (a counter in the run ledger); …`) and make its requirement text state that limit in his words (for example, replace `re-planned at most **2** times` with `retried at most **once**`, if that is what he wrote; the code today, `max_claim_attempts = 2` with a retry only while attempts are below 2, allows at most one retry, but the decision is Huvison's); change nothing else in the row. Expected: one `Fact: retry limit` ledger line, and `grep -n '^| F9 ' business/product-spec.md` shows the same wording as that line.
- [ ] **Step 2: Add the column.** In each of the four tables in §2.1–§2.4, change the header `| # | Requirement |` to `| # | Requirement | Feasibility |` and the separator `|---|---|` to `|---|---|---|`. Add each row's note from this table. A note in the "To build" column becomes the "Built" note only if **every** item it names is `merged` in Step 1; otherwise use the "To build" text.

  | Row | Built (everything named is merged) | To build (otherwise) |
  |---|---|---|
  | F1 | Built: `tools/metrics.py`, pinned in `tests/tools/test_metrics.py`; on screen via `/summary` (L1, F1) | Built: `tools/metrics.py`, pinned in `tests/tools/test_metrics.py`. To build: `/summary` (L1, Linus) and the screen on the new keys (F1, Mildred) |
  | F2 | Built: entity rows and statuses in `tools/metrics.py` (`EntityStatus` in `tools/constants.py`); on screen (F1) | Built: entity rows and statuses in `tools/metrics.py`. To build: the screen on the new keys (F1, Mildred) |
  | F3 | Built: the timeline on screen (F1) | To build: a timeline figure is not in `metrics.portfolio_summary` yet; Patrick and Linus decide whether metrics adds one (open follow-up). The screen shows the workplan dates meanwhile |
  | F4 | Built: open blockers and capacity by role in `tools/metrics.py`; on screen (F1) | Built: open blockers and capacity by role in `tools/metrics.py`. To build: the screen (F1, Mildred) |
  | F5 | Built: every figure carries `evidence` citations; click-through via `/rows` (L2, F2) | Built: every figure carries `evidence` citations (`tools/metrics.py`). To build: `/rows` (L2, Linus) and click-through (F2, Mildred); P3 priority |
  | F6 | Built: orchestrator, retriever, blocker-analyst and the ask spine (P1, P2, L5, H2) | To build: orchestrator and retriever (P1, P2, Patrick), blocker-analyst (L5, Linus), the ask spine (H2, Huvison) |
  | F7 | Built: `tools/claims.py` and the critic's citation pre-check (`agents/critic.py`); the writer drops uncited bullets (H3) | Built: `tools/claims.py` and the critic's citation pre-check (`agents/critic.py`). To build: the writer's drop rule (H3, Huvison) |
  | F8 | Built: `agents/critic.py` with `agents/prompts/critic.txt`, judging blind inside the ask spine (H2) | Built: the critic's code-side guards and locked prompt (`agents/critic.py`, `agents/prompts/critic.txt`). To build: wiring it into the ask spine (H2, Huvison) |
  | F9 | Built: the attempt counter in both ledgers (`adapters/memory_ledger.py`, `adapters/dynamo_ledger.py`), the retry guard and rejected records (H1, H2, Y2) | Built: the attempt counter in both ledgers. To build: rejected records (H1), the retry guard (H2, Y2) |
  | F10 | Built: the $0.50 ceiling (`DEFAULT_RUN_BUDGET_USD` in `config.py`) checked before every step (H2) | Built: the ceiling setting (`DEFAULT_RUN_BUDGET_USD` in `config.py`). To build: the budget check (H2, Huvison) |
  | F11 | Built: scope-bound tools (`tools/agent_tools.py`), `PartialAnswer` for an unknown entity (P2), the pre-run refusal (L3) | Built: scope-bound tools (`tools/agent_tools.py`). To build: `PartialAnswer` (P2, Patrick), the pre-run refusal (L3, Linus) |
  | F12 | Built: the writer and the status-pack write (H3, H4) | To build: the writer (H3) and the status-pack write (H4), Huvison |
  | F13 | Built: Step Functions Standard with `waitForTaskToken` (H4, Y2) and the approve screen (F5) | To build: the approval flow (H4, Huvison; Y2, Yaw) and the approve screen (F5, Clement) |
  | F14 | Built: Cognito sign-in, scope from the token (L1, M3*, F3) | To build: scope from the token (L1, Linus), Cognito (M3*, Michael), sign-in screen (F3, Clement); fallback `AUTH_MODE=none` (a demo user with CFO scope) |
  | F15 | Built: `tools/queries.in_entity_view` and scope-bound tools; refused at the API (L1, L3) | Built: `tools/queries.in_entity_view` and scope-bound tools. To build: the API refusal (L1, L3, Linus) |
  | F16 | Built: `tenant_id` in every `Scope` (`tools/models.py`). Onboarding a second tenant is roadmap Phase 3 | Built: `tenant_id` in every `Scope` (`tools/models.py`). Onboarding a second tenant is roadmap Phase 3 |

  Expected: `grep -c '| Feasibility |' business/product-spec.md` prints `4`, and every F row has three cells (`grep -c -E '^\| F[0-9]+ \|[^|]+\|[^|]+\|$' business/product-spec.md` prints `16`).
- [ ] **Step 3: The test count.** In §3, replace the row `| The test suite | 140 tests passing |` with `| The test suite | <n> tests passing (`uv run --locked pytest`, <YYYY-MM-DD>) |`, where `<n>` is the count from Task 3 Step 1. Expected: `grep -c '140 tests' business/product-spec.md` prints `0`.
- [ ] **Step 4: Priorities.** In §4's P1 row, after `**Cognito sign-in with entity scope**` add ` (D-015: the one target layer built in the POC)`. If the Cognito go/no-go at D2 12:00 was **no-go** (ask Patrick), instead add ` (D-015; no-go at D2 12:00, so the demo runs with `AUTH_MODE=none` and `HANDOFF.md` says so)`. Expected: `grep -c 'D-015' business/product-spec.md` prints `1`.
- [ ] **Step 5: Check and commit**
  ```bash
  uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
  git add business/product-spec.md
  git commit -m "Add a feasibility note per must-do to the product spec and update its test count"
  ```
  Expected: the same pass count as Task 3 Step 1; one commit.

**Task done when:**
- `grep -c '| Feasibility |' business/product-spec.md` prints `4` and the 16-row check prints `16`.
- `grep -c '140 tests' business/product-spec.md` prints `0` and `grep -c 'D-015' business/product-spec.md` prints `1`.
- The F9 row states the retry limit in the words of the `Fact: retry limit` ledger line.
- Every `Built:` note names only items that are `merged` in the ledger's Build order lines.

### Task 5: Re-render both PDFs and open PR 2 (D2, before the 15:00 lead review)

**Files:** Modify `business/business-case.pdf`, `business/product-spec.pdf`.

- [ ] **Step 1: Render.** Render `business/business-case.md` to `business/business-case.pdf` and `business/product-spec.md` to `business/product-spec.pdf`, with the tool Michael used for commit `68866af` (same look). If that tool isn't available: VS Code → open the `.md` → Command Palette → "Markdown PDF: Export (pdf)" (extension yzane.markdown-pdf); the PDF lands beside the file. Expected: both files have today's modification time (`ls -l business/*.pdf`).
- [ ] **Step 2: Read them.** Open each PDF and search (Ctrl+F) for `TBC` and `TODO`. Check that the tables show every column. Expected: 0 results for both words in both PDFs; the product-spec tables show the Feasibility column.
- [ ] **Step 3: Commit**
  ```bash
  git add business/business-case.pdf business/product-spec.pdf
  git commit -m "Re-render the business case and product spec PDFs"
  git log -1 --format=%ct -- business/business-case.pdf; git log -1 --format=%ct -- business/business-case.md
  ```
  Expected: the first timestamp is greater than or equal to the second.
- [ ] **Step 4: Review Focus.** Work through the five Review Focus lines by hand and write each result in the ledger. Expected: five ledger lines `Review <n>: ok` or a fix commit for each problem.
- [ ] **Step 5: PR (with Patrick's OK only).** `git diff develop --stat` → only `business/business-case.md`, `business/business-case.pdf`, `business/product-spec.md`, `business/product-spec.pdf`. Then `git push -u origin docs/business-case-measured` and open a PR to `develop` titled `Measured figures in the business case and the product-spec rubric pass`. The body lists each closed line with its source and every `Ruling:` from the ledger. Expected: the PR shows 4 files changed; Patrick reviews at D2 15:00.
- [ ] **Step 6: Build order.** Set B1's row in [[Build order]] to `in review (PR #<n>)`, and to `merged` when Patrick merges. Expected: the vault row shows the PR number.

**Task done when:**
- Both PDFs are committed after their Markdown (the timestamp check holds) and contain no `TBC` or `TODO`.
- A PR from `docs/business-case-measured` to `develop` exists, touching only the four files.
- The B1 row in [[Build order]] shows `in review (PR #<n>)` or `merged`.

## Done means
- [ ] **No `[TBC]` left.** Verify: on `develop` after both merges, `grep -c 'TBC' business/business-case.md` prints `0`.
- [ ] **Every closed line is labelled.** Verify: `grep -n -E 'Validat|Time to answer|Cost per answered|Portal run cost|Net value per month|Payback|ERP consolidation planned' business/business-case.md` shows at least seven lines, each containing `(brief)`, `validated`, `measured` or `proposed` (case-insensitive).
- [ ] **The session is on record.** Verify: `business/validation-session.md` exists on `develop`; `grep -c 'Answer (as spoken)' business/validation-session.md` prints `3`, or `grep -c 'not held' business/validation-session.md` prints `1`.
- [ ] **The quote is real.** Verify: the line-23 quote appears word for word in `business/validation-session.md` (`grep -F '<first five words of the quote>' business/validation-session.md` prints the line), and the record's consent field says `yes`.
- [ ] **One cost per question.** Verify: the figure on the `Cost per answered question` line equals the "Measured on" average in `COST.md` on `develop` (not its Total row, the Q01 worked example), or the line says `proposed`.
- [ ] **F9 states the decided retry limit.** Verify: `grep -n '^| F9 ' business/product-spec.md` shows the same wording as the `Fact: retry limit` ledger line.
- [ ] **The arithmetic holds.** Verify with a calculator: net = value per month − run cost per month; payback months = pilot cost ÷ net (one decimal); total = count × value per programme.
- [ ] **The product spec has a feasibility note per must-do.** Verify: `grep -c '| Feasibility |' business/product-spec.md` → `4`; `grep -c -E '^\| F[0-9]+ \|[^|]+\|[^|]+\|$' business/product-spec.md` → `16`; `grep -c '140 tests' business/product-spec.md` → `0`.
- [ ] **The PDFs match.** Verify: `git log -1 --format=%ct` of each PDF ≥ that of its `.md`; Ctrl+F `TBC` in `business/business-case.pdf` finds nothing.
- [ ] **The guards still pass.** Verify: `uv run --locked pytest` on `develop` after the merges passes with the same count as before them.
- [ ] **The PRs are merged and the Build order is updated.** Verify: on GitHub, both PRs (`docs/validation-session`, `docs/business-case-measured`) show "Merged"; B1's row in [[Build order]] says `merged`.

## Never
- Invent or paraphrase a quote, or quote anyone without their recorded consent.
- Write an estimate as *measured*, or a measured figure without the file it came from.
- Name a real portfolio company, system or client person beyond Vanessa Addo and Joseph Akayesi.
- Describe Verified Permissions, Athena + Glue, Lake Formation, connectors, CloudTrail or a second tenant as built.
- Edit `COST.md`, `EVALS.md`, `docs/ROADMAP.md` or any file outside `business/`.
- Push to `develop` or `main`, or add attribution lines.

Related: [[B1 - Business case figures and validation - spec]], [[Build order]], [[How to execute a plan]]
