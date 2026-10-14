---
tags: [build, spec, area/business]
id: B2
owner: Patrick + Michael
status: awaiting review
updated: 2026-10-14
---
# B2: The pitch deck (spec)
> **The deck is 20 of the 100 points**, read by an AI reviewer against four items: named executive (6), what it replaces (5), why it is agentic (5), scope and demo moment (4). B2 turns today's 11-slide plain-language deck (`business/pitch-deck.pptx`, commit `68866af`) into the brief's 10 slides, with every number sourced and the demo moment on its own slide: **the critic rejecting the decoy `DEF-0398` while `RC-C3-E4-customers` still fails.** Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop`.

## 0. Context: read the vault first
The team vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before editing the deck, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure.
2. [[Workstreams]]: the architecture, the timeline, what is graded, the rules (§7).
3. [[Business case and pitch]]: the brief, with the suggested 10 slides. **It is the requirement.**
4. [[Pitch track grading rubric]] (the four deck items), [[Judging rubric]] (the required submissions and the judges' questions), [[Problem statement]], [[Hackathon guideline]] ("the demo lands when the critic catches something on stage").
5. [[B1 - Business case figures and validation - spec]]: the deck reuses its figures, labels and quote.
6. `01 Decisions/`: [[2026-10-13 POC plus one target slice, target as 90-day roadmap]] (D-015), [[2026-10-13 Metrics are code, only the blocker Q&A is agentic]] (D-001), [[2026-10-13 Artefact text is untrusted, critic fails closed]] (D-009); `02 Learnings/`: [[Critic is the highest-value agent]], [[Graders are AI and read only what is written]], [[Rule of evidence caps claims at 2]].
7. Repo: `AGENTS.md`, `ARCHITECTURE.md` §2, §3, §3b, §6, `EVALS.md` (Q01, Q02, Q08, Q11, Q12), `DEMO.md`, `HANDOFF.md`, `COST.md`, `docs/ROADMAP.md`.

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/`, `03 Sessions/`, `Open follow-ups.md`. If the vault doesn't answer it, stop and ask Patrick. Never invent a figure, a verdict or a capability.

## 1. Intent
**What:** `business/pitch-deck.pptx` (source) and `business/pitch-deck.pdf` (export), both committed, with exactly **10 slides** in the brief's order:
1. the CFO's problem; 2. what it replaces and its cost; 3. the one screen; 4. ask "what is blocking E4?", with the cited chain; 5. **the critic rejecting the decoy** (the demo moment); 6. why it is agentic; 7. the POC and target architecture; 8. trust; 9. cost and value; 10. the 90-day plan and the ask.

Also the brief's "why it's agentic" interview (D1 evening, 15 minutes with Patrick and Huvison), whose findings go into slide 6.

**Why:**
- Today's deck scores well on plain language but leaves points on the table: no slide shows the critic rejecting `DEF-0398` by name (slide 8 says "a related problem is fixed"), there is no architecture or cost slide, "secure sign-in" is listed as in the demo before the D2 12:00 Cognito go/no-go, and the IDs the reviewer can check against the repo are missing.
- AI reviewers reward specifics: a named role, real numbers with their source, the exact rows. The plain headline stays for the human panel; a small evidence line under it carries the IDs and sources for the reviewer.

**Success means:**
- The pptx has 10 slides; the PDF has 10 pages and was exported after the last pptx change.
- Slide 1 names **the CFO** (and the programme sponsor) as the executive; the word "CIO" appears only in `Not the CIO`.
- Slide 2 names what it replaces (the hand-built monthly steering deck; 2 consultant-days per question, *(brief)*) and its cost ($14,500 a month, with the assumption).
- Slide 5 shows `DEF-0398` Closed, `RC-C3-E4-customers` failing, and the critic's real verdict from a recorded run, on the path recorded on D1 (§2: `main`, or (a)/(b)).
- Slide 6 says why a Lambda + SQL query wouldn't do, with the real trace of a run.
- Slide 7 separates built (POC + the Cognito slice) from the 90-day target (D-015).
- Every number on every slide has a source in its slide's footer: *(brief)*, *measured* (file), *proposed* (assumption), or *synthetic demo data* (`tools/metrics.py`).

**Assumptions (about other people's outputs):**
- **A recorded eval run exists** by D2 14:30: `evals/results/run-<stamp>.json`, in which case `Q01` has `answer.bullets[].citations` and `trace`, and case `Q02` has `answer.rejected[]` entries shaped `{claim_id, statement, reason, verdicts}` (the C1 `AskResponse`, `tools/api_schema.py` on `feature/api-and-spine-contracts`; `evals/run.py` stores the response under `"answer"`).
- **The decoy produces a visible rejection.** AGENTS.md says the blocker-analyst emits the `DEF-0398` / `RC-C3-E4-customers` conflict *as a claim*; the critic rejects a claim that the customer master is ready or resolved. If the recorded Q02 run has **no** rejected claim mentioning `DEF-0398`, slide 5 cannot show one: stop and ask Patrick (see §3, slide 5). This is the item's main open risk, so the slide 5 path is settled on D1 (§2).
- **The live portal** (F1–F5, Mildred and Clement) is deployed by D2 14:00, so slides 3–5 use real screenshots; otherwise the screenshots come from `cd web && yarn start` on mock data, labelled "mock data".
- **B1's figures** (line 23 quote, value per month, payback, portfolio count) are merged or at least final on B1's branch when slide 9 is filled.
- **`COST.md`** has its "Measured on" line (the **average** cost per question, the team's one cost-per-question figure) and its **Pilot** and **Full** rows filled (A3b/H5). Its "Per question" Total row is labelled "Q01 worked example" and is not quoted as the cost per question. A3b's branch `docs/cost-measured` and A5a's branch `docs/eval-results-<yyyymmdd>-<hhmm>` hold the figures from about D2 14:40, before they merge; B2 reads them there and re-checks after the merges.
- **The retry limit** is Huvison's written answer to A1's Q09 question (A1 plan Task 4 Step 2). The code today allows at most one retry (`max_claim_attempts = 2`, retried only while attempts are below 2), but slide 8 states only his written decision.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Edit or rebuild | **Edit `business/pitch-deck.pptx`**: keep its look, footer (`ERP Migration Progress Portal · Team Cloud 9`) and plain headlines; restructure to the brief's 10 slides | A new deck from scratch (loses Michael's design; two days is short) |
| Number of slides | Exactly 10. The product name and team move into slide 1's header, so there is no separate title slide | 11 with a title slide (the brief's outline is 10, and a title slide earns nothing) |
| Plain language or IDs | Both: a plain headline and body for people; one **evidence line** per slide (small, grey, bottom) with the IDs and sources the AI reviewer can check | Plain only (the reviewer can't verify "a related problem"); IDs only (the human panel loses the story) |
| The demo moment's content | The critic's **real** verdict text from the recorded run (`rejected[].statement` and `reason`), quoted, with the run file named | A verdict written by us; a mock-data screenshot presented as live |
| The slide 5 path | Decided **on D1** (plan Task 2 Step 4): Patrick and Huvison say which run shows a rejection naming `DEF-0398` (Q01 live, Q02 eval, or neither) and the ledger records `Slide 5 path: main \| (a) \| (b)`. Slide 5 is built on that path from the start. `main` if a run shows it; otherwise **(a) by default** (the flagged conflict plus a labelled Q08 rejection), or (b) if Patrick picks it. The path goes in the PR body for B3c's script | Deciding at D2 14:30 when the run lands (no time to rebuild the slide) |
| The cost per question | The `COST.md` "Measured on" **average**, everywhere (slide 9, business case line 34, the pitch script, `HANDOFF.md`/`DEMO.md`) | The "Per question" Total row (the Q01 worked example: one question) |
| The retry limit (slide 8) | Huvison's written Q09 answer, recorded as `Fact: retry limit` | "At most 2 re-plans" from the old product spec (the code allows at most one retry today; the decision is his) |
| Measured numbers | Filled only at D2 14:00–15:00 from `COST.md` and the results file. Before that, the slide says "measured at the D2 run" in words, never a guessed number | A placeholder number "for now" (it ships by accident) |
| Cognito on slides | Slide 7 says "built" only if the D2 12:00 go/no-go was **go**; otherwise "no-go at D2 12:00: the demo runs as a CFO demo user (`AUTH_MODE=none`)" | Listing sign-in as built before the decision (today's slide 9 does) |
| Architecture on slide 7 | One slide, two columns: **Built in 2 days** and **The 90-day target** with the roadmap phase on each target box (from `ARCHITECTURE.md` §6). The full diagrams are B3b's appendix slides | Both full diagrams on one slide (unreadable) |
| Tool | PowerPoint (desktop or Microsoft 365 web); Google Slides as the fallback (upload the pptx, edit, then File → Download → `.pptx` and `.pdf`) | Converting to another format (the source must stay editable) |
| Screenshots | Taken from the deployed portal after the D2 14:00 freeze, at 1920×1080, browser zoom 100%. Crop out the address bar, account IDs, tokens and anything not synthetic | Screenshots with the AWS console or a URL carrying a token |

## 3. The 10 slides: exact content
Each slide is: **kicker** (small caps line above the title), **title**, **body**, **evidence line** (small grey text at the bottom left), and the footer + slide number as today. `<…>` slots are filled from the named source only; the plan says when.

**Slide 1: the CFO's problem**
- Kicker: `ERP MIGRATION PROGRESS PORTAL · TEAM CLOUD 9`
- Title: `The CFO funding an 18-month ERP consolidation can't see where it is`
- Body, three cards:
  - `The CFO` / `Funds the consolidation and carries its risk. Decides cutover dates, staffing and spend on a picture up to four weeks old.`
  - `The programme sponsor` / `Steers the programme and decides go / no-go for each entity.`
  - `The delivery lead` / `Rebuilds the same status pack by hand every month.`
- Strip under the cards: `A mid-market industrial group is moving several ERPs onto one platform over about 18 months. Not the CIO's IT project: the CFO's business risk.`
- If B1 line 23 is variant A with consent: a quote box `"<agreed quote>" — <name>, <role>`. Otherwise no quote box.
- Evidence: `Sources: problem statement, AmaliTech Ventures ERP modernisation track (brief); validation session <YYYY-MM-DD> (business/validation-session.md)`. Drop the second part if the session wasn't held.

**Slide 2: what it replaces and its cost**
- Kicker: `WHAT IT REPLACES`
- Title: `It replaces the hand-built steering deck, and two consultant-days per question`
- Body, three stat tiles:
  - `2 days` / `of a consultant's time to answer "are we on track? what is blocked?", every time it's asked`
  - `3 days a month` / `rebuilding the same status pack by hand`
  - `4 weeks old` / `the CFO's picture when a decision is made`
- Strip: `About $14,500 of consultant time a month, before a single blocker is found late.`
- Evidence: `2 days per question, monthly pack, weeks-old picture: brief. 3 pack days ("a few"), 6 questions a month, $1,000 a day: proposed, <confirmed by Vanessa Addo on <date> | to be confirmed by the problem owner>. $14,500 = (6 × 2 + 3 − 0.5 review) × $1,000 (business/business-case.md §2).` If B1 Task 2 corrected an assumption, use the corrected figures and value.

**Slide 3: the one screen**
- Kicker: `WHAT THE CFO GETS`
- Title: `One live screen instead of a monthly deck`
- Body: a screenshot of the portal's one screen (all four entities, E4 marked Blocked), and five KPI tiles beside it:
  - `58 %` / `of records migrated and reconciled (18,420 of 31,700)`
  - `96.4 %` / `pass rate in the latest load cycle (target 98 %)`
  - `7` / `open blockers, the oldest 18 days`
  - `102 days` / `to final cutover, 6 days behind plan`
  - `103 %` / `of planned people working this month (38 vs 37)`
- Strip: `Every number is computed from the migration's own records, never typed in. Click one to see the rows behind it.`
- Evidence: `Synthetic demo programme: 4 entities onto 1 platform (demo/data/erp, seed 2026, as of 2026-10-13). Figures from tools/metrics.py, pinned in tests/tools/test_metrics.py.`

**Slide 4: ask "what is blocking E4?"**
- Kicker: `ASK A QUESTION`
- Title: `"What is blocking cutover for E4?" Answered with its evidence`
- Body, the chain as five numbered rows, each with its citation chip on the right:
  1. `Customer master reconciles at 91.2 % against 98 %` → `RC-C3-E4-customers`
  2. `212 customer records rejected for invalid tax IDs; the defect is open, High, 18 days old` → `DEF-0412`
  3. `The cutover runbook step needs that reconciliation to pass` → `E4#RB-010`
  4. `The tax-ID mapping rule behind the rejections` → `E4#CUSMST#TAXNO`
  5. `And the 23 Jan 2027 cutover sits inside the year-end close` → `CAL-004`
- Right: a screenshot of the answer card from the real run (bullets with their citation chips).
- Strip: `Answered in <seconds> seconds instead of 2 consultant-days. Every line links to its row.`
- Evidence: `Measured: question Q01, evals/results/<file> (<deployed API | local asker>), <seconds> s, status <status>. 2 consultant-days: brief.` Keep only the rows the real answer cites; a row the run didn't cite is removed, not kept "for the story".

**Slide 5: the critic rejects the decoy (the demo moment)**
- Kicker: `THE MOMENT IT EARNS TRUST`
- Title: `The defect log says fixed. The data says it isn't. The critic catches it.`
- Body, three panels left to right:
  - `The defect log` / `DEF-0398, duplicate customer records: Closed`
  - `The reconciliation` / `RC-C3-E4-customers: still FAIL at 91.2 % against 98 %; runbook step E4#RB-010 needs it to pass`
  - `The critic's verdict` (red border) / `Rejected: "<rejected[].statement, verbatim>"` / `Reason: "<rejected[].reason, verbatim>"`
- Strip: `A hand-built status report would have shown green. The critic sees only the claim and its cited rows: not the plan, not the attempt count.`
- Evidence: `Measured: eval Q02, evals/results/<file>, claim <claim_id>, <n> verdicts. Critic: agents/critic.py, prompt agents/prompts/critic.txt v<version>. Planted decoy: demo/data/erp/README.md.`
- **The path is recorded on D1** (`Slide 5 path:` in the ledger, §2) and the slide is built on it from the start:
  - `main` (a run shows a rejection naming `DEF-0398`): the three panels above.
  - `(a)`, the **default** when no run shows one: the title `The defect log says fixed. The data says it isn't. The answer says so.`; the first two panels as above; the third panel `The answer` / the Q02 answer's sentence that flags the conflict, quoted; and a fourth, labelled panel `Another check, same run: the critic rejects an uncited claim (eval Q08)` / `Rejected: "<Q08 rejected[].statement, verbatim>"` / `Reason: "<Q08 rejected[].reason, verbatim>"`. Evidence: `Measured: evals Q02 and Q08, evals/results/<file>, claim <claim_id>, <n> verdicts. Q08 strips citations on purpose (inject). …` (the rest as above).
  - `(b)` (Patrick's choice): the three panels, the verdict panel titled `A real rejection from the same run`, with another `rejected[]` entry of the run, verbatim, and its question ID in the evidence line.
- **If the recorded run doesn't fit the recorded path:** don't fill this slide from anything else. Stop and ask Patrick, who decides between (a) and (b). The choice and the reason go in the ledger and the PR.

**Slide 6: why it is agentic**
- Kicker: `WHY IT NEEDS AN AGENT`
- Title: `The numbers are code. The question isn't.`
- Left column `The screen: plain code` / `Known formulas, no model call, no tokens (D-001). A Lambda and a query are the right tool for 58 %.`
- Right column `"What is blocking E4?": an agent` / `No fixed checklist answers it. From what it just found, the orchestrator decides which of 14 scoped tools its two helpers use next, and re-plans when the critic rejects a claim.`
- Under it, the real trace of the Q01 run as a horizontal step strip: `<trace[].step (trace[].agent)>` for each step, in order.
- Strip: `Fixed steps are a Step Functions flow. Exactly one agent plans; four others each do one job.`
- Evidence: `AGENTS.md (5 agents; 9 retriever + 5 analyst tools); ARCHITECTURE.md §2 (which steps are flows, which are agents); trace: evals/results/<file>, Q01.` Add the one sentence from the interview (plan Task 2) that best states the orchestrator's real decision, attributed to Patrick or Huvison.

**Slide 7: the POC and the target**
- Kicker: `SCOPE: WHAT'S BUILT, WHAT'S NEXT`
- Title: `Built in two days, with a 90-day path to production`
- Left column `Built in 2 days (the POC)`:
  - `The one screen from the migration's records`
  - `The agent loop: orchestrator, retriever, blocker-analyst, blind critic, writer`
  - `Run ledger with the retry counter; budget ceiling; Guardrails`
  - `Publish only after the delivery lead approves`
  - Cognito line, one of: `Sign-in with role and entity scope: an entity lead can't see another entity (the one target layer we built)` **or** `Sign-in: no-go at D2 12:00; the demo runs as a CFO demo user`
- Right column `The 90-day target (docs/ROADMAP.md)`, each with its phase tag:
  - `Live connectors and scheduled refresh; Glue + Athena` `Phase 1`
  - `Client sign-in federation; Verified Permissions policies` `Phase 1`
  - `Lake Formation row filters; CloudTrail "who saw what"; evals in CI` `Phase 2`
  - `The next portfolio company as a new tenant, no code changes` `Phase 3`
- Strip: `We cut what wasn't needed to prove it. We never cut the citations, the critic or the retry guard.`
- Evidence: `ARCHITECTURE.md §3 (POC), §3b (target), §6 (component by component); DECISIONS.md D-015. Full diagrams: appendix slides (B3b).`

**Slide 8: trust**
- Kicker: `WHY THE CFO CAN ACT ON IT`
- Title: `Six controls, each one in the code`
- Body, six tiles (name / one line / where):
  - `Every claim cited` / `A claim without its rows never reaches the screen` / `tools/claims.py`
  - `A blind critic` / `Judges each claim on its cited rows only; fails closed` / `agents/critic.py`
  - `Bounded retries` / `<Fact: retry limit, Huvison's words, e.g. "At most one retry">, counted in the run ledger, then "could not verify"` / `DynamoDB run ledger`
  - `Human approval` / `Nothing is published until the delivery lead approves` / `Step Functions waitForTaskToken`
  - `Guardrails` / `PII and prompt-attack filters on every model call; artefact text is data` / `Bedrock Guardrails; probe DEF-0462`
  - `A budget per question` / `$0.50 ceiling, or a partial answer that says why` / `config.py`
- Strip: `<pass> of <total> eval questions pass; what still fails is written down in EVALS.md.` (from `EVALS.md` Results, the run used on slides 4–6)
- Evidence: `AGENTS.md; EVALS.md Q08 (uncited claim rejected), Q09 (retry limit), Q11 (scope refusal), Q12 (prompt injection); ARCHITECTURE.md §7.`

**Slide 9: cost and value**
- Kicker: `WHAT IT COSTS, WHAT IT'S WORTH`
- Title: `Cents per answer instead of $2,000`. Use this title only if the measured cost per question is under $1.00; otherwise `$<cost> per answer instead of $2,000`.
- Left `Cost (measured)`:
  - `$<cost> per question` (COST.md "Measured on" average; the same figure as business case line 34) vs `$2,000 today` (2 days × $1,000)
  - `$<pilot monthly> a month` for a pilot of about 200 questions (COST.md Pilot)
  - `$<full monthly> a month` at 100 questions a day (COST.md Full)
- Right `Value (proposed, assumptions stated)`:
  - `$14,500 a month` of consultant time back (14.5 days)
  - `About $261,000` over one 18-month programme
  - `Payback in <months> months` on a $105,000 pilot
  - `<count> portfolio companies` with a consolidation planned or under way, each about 5 days to onboard. If B1 line 79 is variant B: `The next portfolio company: about 5 days to onboard, no code changes`.
- Evidence: `Measured: COST.md (<date>). Proposed: business/business-case.md §2–§3 (6 questions and 3 pack days a month, $1,000 a day, 18 months). <Validated: <count>, Vanessa Addo, <date>.>`

**Slide 10: the 90-day plan and the ask**
- Kicker: `THE ASK`
- Title: `Prove it on one real programme in 6 weeks`
- Left `90 days, three gates (docs/ROADMAP.md)`: `Weeks 1–6 pilot: real connectors, real users, a 40-question eval set written with the delivery lead` / `Weeks 7–10 hardening: data-layer scope, audit, evals in CI` / `Weeks 11–13 the next portfolio company as a tenant`
- Middle `Go at week 6 if (proposed)`: `≥ 85 % of 40 questions right, with citations` / `Zero answers outside the asker's scope` / `Two status packs approved with minor edits` / `Cost per question within the COST.md estimate`
- Right `What we need from you`: `A sponsor (the CFO or programme sponsor) and the delivery lead as product owner` / `Read access to the project tool, defect tracker and reconciliation exports` / `Your sign-in federation and finance calendar`
- Strip: `Top risks: IDs that don't match across tools · accuracy on real data · slow access approvals. Each has a stop condition.`
- Evidence: `docs/ROADMAP.md (phases, go / no-go, team, top-3 risks). Pilot: 3 engineers + a part-time delivery lead, $105,000 proposed (business/business-case.md).`

**Global wording rules:** "CFO" on slides 1, 2 and 10 at least; never "CIO" except slide 1's `Not the CIO`. Never "real-time", "production-ready" or "AI-powered" for the POC. Percentages with a space (`58 %`) as today's deck.

## 4. The "why it's agentic" interview (D1 evening)
15 minutes, Patrick and Huvison, Michael writes. Four questions, verbatim:
1. "For 'what is blocking E4?', what does the orchestrator fetch first, and what makes it fetch the next thing?"
2. "Name one run where it took a different path from the one you expected."
3. "What did the critic reject in the last run, and why?"
4. "Which step is a fixed flow, and why isn't it an agent?"
Answers go in the vault session note of that day under "Why it's agentic interview", as spoken. Slide 6 quotes at most one sentence, and only behaviour that is in the code or a recorded run.

## 5. Checks
- Slide count: `unzip -l business/pitch-deck.pptx | grep -c -E 'ppt/slides/slide[0-9]+\.xml$'` → `10`.
- Text per slide: `for number in $(seq 1 10); do printf 'slide %s: ' "$number"; unzip -p business/pitch-deck.pptx "ppt/slides/slide${number}.xml" | sed 's/<[^>]*>/ /g' | tr -s ' ' | cut -c1-160; echo; done`. PowerPoint numbers the slide files in order when it saves; if the order looks wrong, check it in the PDF.
- Required strings, each `→ ≥ 1`: on slide 1 `CFO`; slide 5 `DEF-0398`, `RC-C3-E4-customers`, `Rejected`; slide 6 `14 scoped tools`; slide 7 `90-day`; slide 9 `COST.md`; slide 10 `ROADMAP`.
- Forbidden: `grep -c 'TBC\|TODO\|&lt;'` on the extracted text of every slide → `0` (no unfilled slot).
- The PDF: opens with 10 pages; `git log -1 --format=%ct -- business/pitch-deck.pdf` ≥ the same for `business/pitch-deck.pptx`.
- `uv run --locked pytest` passes with the start count (B2 changes no tracked `.md` or code, but run it before the PR).

## 6. Out of scope
- The appendix architecture, cost and 90-day slides (B3b), the one-page value case (B3a), the pitch script and Q&A (B3c).
- The live demo and the backup video (F6, Clement); `DEMO.md`.
- Any figure not yet in `COST.md`, `EVALS.md` or the business case: B2 copies, never computes.

Related: [[Build order]], [[Business case and pitch]], [[B2 - Pitch deck - plan]]
