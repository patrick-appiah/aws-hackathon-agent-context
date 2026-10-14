---
tags: [build, spec, area/business]
id: B1
owner: Patrick + Michael
status: awaiting review
updated: 2026-10-14
---
# B1: Business case figures and the validation session (spec)
> **The business case is 20 of the 100 points, and four AI reviewers read only what is written.** B1 closes every `[TBC]` in `business/business-case.md` with a validated, measured or clearly *proposed* figure, runs the D1 09:30 validation session that supplies the problem-owner figures, and gives `business/product-spec.md` its rubric pass. Repo: `Amali-Tech/cloud-9-hackathon`, branches from `develop`. The repo is the source of truth for the documents; the vault is the source of context.

## 0. Context: read the vault first
The team vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before editing any document, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every person and agent follows.
2. [[Workstreams]] (`06 Workstreams/`): the architecture, the timeline, what is graded and the rules (§7).
3. [[Business case and pitch]]: the owners' brief. **It is the requirement.**
4. [[Pitch track grading rubric]] (what is scored: business case 20, product spec 10), [[Judging rubric]] (level descriptors 1.1 and 1.2, the required submissions), [[Problem statement]] (the *(brief)* facts).
5. [[Build order]]: B1 depends on A3 and H5 for the measured cost, and on the eval runs for the measured time.
6. `01 Decisions/`: [[2026-10-13 POC plus one target slice, target as 90-day roadmap]] (D-015), [[2026-10-13 EU-only Bedrock inference profiles]] (D-002); `02 Learnings/`: [[Graders are AI and read only what is written]], [[Rule of evidence caps claims at 2]], [[Five deliverables, not just a repo]].
7. The briefs whose outputs B1 consumes: [[Abdul - evals, Cognito, docs]] (`COST.md`), [[Huvison - trust and flow]] (cost per run, `/ask` timing), [[Linus - API, identity, blocker-analyst]] (the eval runs and `docs/ROADMAP.md`).

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask the owner (Patrick). Never invent a figure, a quote or a source.

## 1. Intent
**What:**
1. **The validation session** (D1 09:30, 15 minutes) with the problem owner **Vanessa Addo** and oversight **Joseph Akayesi**: three questions, answers recorded word for word in `business/validation-session.md` *(new)*, written into the business case the same day.
2. **Close the seven `[TBC]` lines** in `business/business-case.md` (the six in the brief plus the legend on line 3, which also contains the token), each with a source label.
3. **Re-render `business/business-case.pdf`** from the updated Markdown, so the PDF the organisers take matches the repo.
4. **The product-spec rubric pass** (brief "What you build" item 3): a feasibility note on every must-do, priorities that say what is built first, measurable success measures, and the stale "140 tests" figure corrected.

**Why:**
- Business case: "The problem" is 8 points and "Value if solved" 7. A 4 needs the pain in the owner's words, validated *during the event* (Judging rubric 1.1), and the value sized in real numbers with stated assumptions and a payback (1.2).
- A `[TBC]` in a graded document reads as "not done" to an AI reviewer. A figure labelled *proposed* with a named confirmer reads as honest and still earns credit.
- Every number must say where it came from. An estimate presented as measured is the one mistake the reviewers and the human panel both punish (rule of evidence).

**Success means:**
- `grep -c 'TBC' business/business-case.md` prints `0`.
- Every figure on the seven closed lines carries one of four labels: *(brief)*, *(validated: name, date)*, *measured* (with the file it came from), or *proposed* (with the assumption and who confirms it).
- `business/validation-session.md` exists with the date, the attendees, the three questions and the answers as spoken, or it says plainly that the session didn't happen and why.
- `business/business-case.pdf` is regenerated after the last Markdown change.
- `business/product-spec.md` has a feasibility note on each of F1–F16 and no stale test count.
- `uv run --locked pytest` passes with the same count as the start state (the documentation guards scan every tracked `.md` file).

**Assumptions (about other people's outputs; the reviewer reconciles them):**
- **A3/H5:** `COST.md` gets a "Measured on" line under its "Scale" table with the **average** cost per question over the recorded run (the team's one cost-per-question figure: the deck, the pitch script and `HANDOFF.md`/`DEMO.md` quote the same), and a filled **Pilot** row in its "Scale" table (monthly cost at about 200 questions a month). The "Per question" table's Total row is labelled "Q01 worked example" (one question) and is never quoted as the cost per question. The table and row names are today's `COST.md` on `develop`. A3b's branch `docs/cost-measured` holds these figures from about D2 14:40, before it merges.
- **Eval runs (Linus, H6/L6):** a committed `evals/results/run-<stamp>.json` (`evals/results/` *(new)* is created by the eval runner's first committed run, A5a) holds, for case `Q01`, the fields `seconds` and `cost_usd` and `status`. These names exist today in `evals/run.py` (`run_case` writes `"seconds"` and `"cost_usd"`). Linus records this run at D2 14:00 sharp (B1 plan Task 3 Step 0); A5a's branch `docs/eval-results-<yyyymmdd>-<hhmm>` holds the file before it merges, so B1 reads it there and re-checks after the merge. If Linus's deployed-API asker (L6, `evals/api_asker.py` *(new, L6)*) has run, its results file is preferred, because it times the real `/ask` through API Gateway.
- **L7:** `docs/ROADMAP.md` keeps its "Team (proposed)" section: weeks 1–6 = 3 engineers + 1 delivery lead (part-time); weeks 7–13 = 2 engineers + 1 platform/security engineer (part-time).
- **The session happens at D1 09:30** as booked in TEAM_PLAN §4. If it doesn't, the "not held" variants in §4 apply; nothing is invented.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| What closes a `[TBC]` when the figure isn't confirmed in time | Replace it with the figure we use, labelled *proposed*, plus the assumption and the person who confirms it | Leaving `[TBC]` (reads as unfinished); deleting the row (loses the assumption the reviewer rewards) |
| The quote | Exactly as spoken, attributed by name and role, **only with the speaker's OK** to quote it in a document graders read. Read it back to them before the session ends | A paraphrase in quotation marks; a quote written by us "in their spirit" |
| Where the session is recorded | `business/validation-session.md` *(new)* in the repo (graders can only credit what they can read), plus one line in the vault session note of that day | Only in the vault (graders never see it); only in Slack |
| Time per question (line 31) | The `seconds` of case `Q01` from the committed eval results file, named by file. Prefer the deployed-API run (L6) over the local run (H6), and say which | A stopwatch reading from a rehearsal (not reproducible); the best of several runs (cherry-picked) |
| Cost per question (line 34) | The `COST.md` "Measured on" **average** per question (measured over the recorded run), next to today's 2 × $1,000 = $2,000. The same figure everywhere: deck slide 9, the pitch script, `HANDOFF.md`/`DEMO.md` | The $0.50 budget ceiling (a limit, not a measurement); the "Per question" Total row (the Q01 worked example: one question, not the average) |
| When the measured inputs are read | From A5a's and A3b's open PR branches as soon as they're pushed (about D2 14:40), then re-checked once they merge; variant B only if an input is still missing at D2 15:30 | Waiting for the merges (too late for the 15:00 lead review) |
| Run cost per month (line 46) | The `COST.md` **Pilot** monthly cost (about 200 questions a month, about 10 users). Value still counts only the 6 executive questions, so cost is counted on a higher volume than value: conservative | 6 questions × cost per question (understates cost: entity leads and the delivery lead ask too) |
| Payback (line 51) | Pilot cost ÷ net monthly value, where pilot cost = (3 engineers × 30 working days + a delivery lead at half time × 30 days) × the $1,000 day rate = **$105,000**, all *proposed*. Also state the full 90-day cost ($192,500, *proposed*) against one programme's $261,000 | No payback (1.2 asks for one); a payback on run cost only (ignores the build) |
| Portfolio count (line 79) | The problem owner's number, *(validated)*. If not given: say so, keep the per-company value, and name Vanessa Addo as the confirmer | Guessing a count; using the ten use cases as a proxy |
| Product-spec feasibility notes | A third column, **Feasibility**, on each table in §2, saying "built (where)" or "to build (item, owner)" from the [[Build order]] status on the day | A general feasibility paragraph only (the brief asks for a note per must-do) |
| Who edits | Michael edits the documents; Patrick reviews and presents. Both attend the session | One person doing both (no review before the D2 15:00 lead review) |

## 3. The validation session
**When and who:** D1 09:30, 15 minutes, in person or a call. Patrick asks, Michael writes. Vanessa Addo (problem owner) and Joseph Akayesi (oversight), as the brief names them. Book it with an invite whose title is `ERP Migration Progress Portal: 15-minute validation (Team Cloud 9)` and whose body lists the three questions below, so they can think before the call.

**The three questions (ask them in this order, word for word):**
1. **The executive and the pain.** "We have named the CFO funding the consolidation, with the programme sponsor, as the person whose week gets better. Is that right? What happened the last time one of them asked 'what is blocking cutover?'" Follow-up if needed: "Who signs off the monthly status pack today?"
2. **The cost today.** "We assume 6 status questions a month at 2 consultant-days each, 3 days a month to rebuild the status pack, and a blended day rate of $1,000. Which of these is wrong, and what should it be?"
3. **The portfolio count.** "How many portfolio companies have an ERP consolidation planned or under way in the next 12 to 24 months?"

**Close (1 minute):** read back the one sentence you will quote, and ask: "May we quote you by name and role in the business case the judges read?" Record yes or no.

**The record, `business/validation-session.md`** *(new)*, exactly this structure:
```markdown
# Validation session: ERP Migration Progress Portal

| Field | Value |
|---|---|
| Date and time | <YYYY-MM-DD> 09:30 (15 minutes) |
| Attendees | Vanessa Addo (problem owner, AmaliTech Ventures ERP modernisation track); Joseph Akayesi (oversight); Patrick Noblet Appiah and Michael (Team Cloud 9) |
| Format | <in person / call> |
| Consent to quote by name and role | <yes / no> |

## 1. The executive and the pain
**Asked:** <question 1 as asked>
**Answer (as spoken):** <answer>
**Quote for the business case:** "<one sentence, read back and agreed>", <name>, <role>
**Changes to the business case:** <none, or which line and what>

## 2. The cost today
**Asked:** <question 2 as asked>
**Answer (as spoken):** <answer>
| Assumption | We used | Confirmed / corrected to | By |
|---|---|---|---|
| Status questions per month | 6 | <value> | <name> |
| Consultant days per question | 2 (brief) | <value> | <name> |
| Days to rebuild the status pack per month | 3 | <value> | <name> |
| Blended day rate | $1,000 | <value> | <name> |

## 3. The portfolio count
**Asked:** <question 3 as asked>
**Answer (as spoken):** <answer>
**Count used in the business case:** <number, or "not given">

## Follow-ups
- <anything they asked us to check, with an owner>
```
If the session doesn't happen by D1 12:00, the file says: `Requested for <date> 09:30; not held as of <date> <time> because <reason>. Every figure that needed it stays *proposed*.` Nothing else.

## 4. The seven `[TBC]` lines and their replacements
Line numbers are those of `business/business-case.md` on `develop` today; find each line by its text if they have moved. `<…>` slots are filled from the named source only.

| Line | Today | Closed by | Input needed | Who confirms |
|---|---|---|---|---|
| 3 | the legend: "**[TBC]** marks figures still being confirmed" | B1 Task 2 | none | Michael |
| 23 | `[TBC: session date, and one quote in their words]` | B1 Task 2 | the session record | Vanessa Addo (the quote), Joseph Akayesi (oversight) |
| 31 | `Under 1 minute, every claim cited [TBC: measured in the demo]` | B1 Task 3 | `seconds` of `Q01` in the committed results file | Huvison (timing), Linus (the run) |
| 34 | `[TBC: measured cost per run, COST.md]` | B1 Task 3 | `COST.md` "Measured on" average | Abdul, Huvison |
| 46 | `Portal run cost per month: [TBC]` | B1 Task 3 | `COST.md` Pilot monthly cost | Abdul |
| 51 | `Payback … [TBC: priced by delivery]` | B1 Task 3 | the net monthly value (line 46) and the ROADMAP team | Patrick (delivery pricing) |
| 79 | `[TBC: how many portfolio companies …]` | B1 Task 2 | question 3's answer | Vanessa Addo |

**Replacement text.** Each line has a variant A (the input exists) and a variant B (it doesn't by the deadline). Use exactly one.

- **Line 3, always:**
  `> Facts marked *(brief)* come from the problem statement. *(validated)* figures were confirmed by the problem owner in the validation session (`business/validation-session.md`). *Measured* figures come from recorded runs of the POC (`evals/results/`, local or deployed; each figure names its file). *Proposed* figures are our assumptions, each with who confirms it.`
- **Line 23:**
  - A: `**Validated with:** Vanessa Addo (problem owner, AmaliTech Ventures ERP modernisation track) and Joseph Akayesi (oversight), on <YYYY-MM-DD> (notes: `business/validation-session.md`). In their words: *"<agreed quote>"* (<name>, <role>).`
  - A without consent to quote: the same, ending `… (notes: `business/validation-session.md`). They confirmed the CFO and the programme sponsor as the people who carry this risk.` (only if they did).
  - B: `**Validation:** a session with Vanessa Addo (problem owner) and Joseph Akayesi (oversight) was requested for <YYYY-MM-DD> 09:30 and had not taken place by <YYYY-MM-DD>. The problem above is as the brief states it; every figure that needs the owner is marked *proposed*.`
- **Line 31:**
  - A: `| Time to answer a status question | 2 consultant-days *(brief)* | **<seconds> seconds**, every claim cited (*measured*: question Q01, `evals/results/<file>`, <deployed API / local asker>) |`
  - B: `| Time to answer a status question | 2 consultant-days *(brief)* | Under 1 minute, every claim cited (*proposed*: the product-spec target; not yet measured, Huvison to confirm) |`
- **Line 34:**
  - A: `| Cost per answered question | 2 days × $1,000 = **$2,000** *(brief × proposed day rate)* | **$<average>** (*measured*: average per question over the recorded run, `COST.md` "Measured on") |`
  - B: `| Cost per answered question | 2 days × $1,000 = **$2,000** *(brief × proposed day rate)* | At most **$0.50**, the budget ceiling enforced per run (*proposed*: not yet measured, Abdul to confirm in `COST.md`) |`
- **Line 46:**
  - A: `| Portal run cost per month | **$<pilot monthly>** | *Measured* cost per question × about 200 questions a month by about 10 users (`COST.md`, Pilot row). Value counts only the 6 executive questions, so this is conservative |`
  - B: `| Portal run cost per month | **at most $100** | *Proposed*: 200 questions a month × the $0.50 ceiling, an upper bound until `COST.md` is measured (Abdul) |`
- **After line 49, a new line (both variants):** `- **Net value per month** = $14,500 − $<line 46 figure> = **$<net>** (*proposed* value less the line-46 run cost)`
- **Line 51** (both variants; the figures differ only through `<net>`):
  `- **Payback** = pilot cost ÷ net value per month. *Proposed* pilot cost: (3 engineers × 30 working days + a delivery lead at half time × 30 days) × $1,000 = 105 days × $1,000 = **$105,000** (team from `docs/ROADMAP.md`; the half-time share and the day rate are assumptions, Patrick to confirm the delivery price). Payback = $105,000 ÷ $<net> = **<months> months** of use. The full 90 days add weeks 7–13 ((2 engineers + a half-time platform engineer) × 35 days = 87.5 days, $87,500), so **$192,500** in all, against about $261,000 recovered by one programme.`
- **Line 79:**
  - A: `- **<count> portfolio companies** have an ERP consolidation planned or under way (*validated*: <name>, <YYYY-MM-DD>). Total value is <count> × $261,000 = **$<total>**, against one build and about 5 days of onboarding each (*proposed*, `docs/ROADMAP.md` Phase 3).`
  - B: `- **How many portfolio companies have an ERP consolidation planned or under way** is not yet confirmed (*proposed*: Vanessa Addo to confirm). Each one recovers about $261,000 on the assumptions above, against about 5 days of onboarding (*proposed*, `docs/ROADMAP.md` Phase 3).`

**If question 2 corrects an assumption** (questions per month, pack days, day rate), update the sizing table rows 41–44 to the confirmed value with *(validated: name, date)*, and recompute lines 48–50 and the payback with the same formulas. The arithmetic is shown in the document, so the reviewer can check it.

**Two consistency fixes on the way** (no `[TBC]`, but a reviewer would catch them):
- Line 72: `(EVALS.md Q13)` → `(EVALS.md Q13, a roadmap question, not run in the POC)`.
- Line 74: after `**within 5 working days**` add ` (*proposed*)`.

## 5. The product-spec rubric pass (`business/product-spec.md`)
| Rubric item | Pts | Check | Change |
|---|---|---|---|
| Completeness | 3 | F1–F16 cover the screen, ask, publish, access, plus §2.5 non-functional | none |
| Feasibility | 3 | Each must-do has its own note | Add a **Feasibility** column to the four tables in §2.1–§2.4: `Built: <file>` if the [[Build order]] item behind it is `merged`, else `To build: <ID> (<owner>)`. The mapping is in the plan, Task 4 |
| Priorities | 2 | §4 says what is built first: the POC plus the Cognito slice (D-015) | P1 row: add `(D-015: the one target layer built in the POC)` after "Cognito sign-in with entity scope" |
| User stories | 1 | Five stories with acceptance criteria | none |
| Retry limit (F9) | (part of Completeness) | F9 states the retry limit Huvison decided in writing (his Q09 answer, A1) | F9 row: replace `re-planned at most **2** times` with his wording (the code today allows at most one retry: `max_claim_attempts = 2`, retried only while attempts are below 2) |
| Success measures | 1 | Each is a number or a yes/no | §3 "The test suite" row: replace `140 tests passing` with the real `uv run --locked pytest` count on the day, as `<count> tests passing (`uv run --locked pytest`, <YYYY-MM-DD>)` |

Re-render `business/product-spec.pdf` after the change, with the same tool as the business case.

## 6. Tests and checks
There is no new code. The checks are:
- `grep -c 'TBC' business/business-case.md` → `0`.
- `grep -n -E 'Validat|Time to answer|Cost per answered|Portal run cost|Net value per month|Payback|ERP consolidation planned' business/business-case.md` → at least seven lines, each containing `brief`, `validated`, `measured` or `proposed` (case-insensitive).
- `test -f business/validation-session.md && grep -c 'Answer (as spoken)' business/validation-session.md` → `3`, or the "not held" line exists.
- `git log -1 --format=%ct -- business/business-case.pdf` ≥ `git log -1 --format=%ct -- business/business-case.md` (the PDF is newer than the Markdown).
- `grep -c '140 tests' business/product-spec.md` → `0`; `grep -c '| Feasibility |' business/product-spec.md` → `4`.
- `uv run --locked pytest`: the same pass count as the start state. The guards in `tests/test_dependencies.py` and `tests/test_code_style.py` read every tracked `.md` file, so the documents must not contain a bare `pytest` command in backticks, `uv run pytest`, `python scripts/…` without `uv run`, or a `test_*.py` path outside `tests/`.

## 7. Out of scope
- Measuring the cost or the time (A3, H5, H6, L6). B1 only copies the measured figures, with their source.
- Changing `COST.md`, `EVALS.md`, `docs/ROADMAP.md` or any other workstream's file. If a figure there looks wrong, tell its owner.
- The deck and the one-page value case (B2, B3).

Related: [[Build order]], [[Business case and pitch]], [[B1 - Business case figures and validation - plan]]
