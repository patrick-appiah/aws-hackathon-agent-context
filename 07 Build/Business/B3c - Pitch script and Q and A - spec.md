---
tags: [build, spec, area/business]
id: B3c
owner: Patrick + Michael
status: awaiting review
updated: 2026-10-14
---
# B3c: The 10-minute pitch and the 8-minute Q&A (spec)
> **The pitch is 10 minutes with the live demo inside it, then 8 minutes of questions** (9 Oct proposal). B3c writes the run of show, word for word, as `business/pitch-script.md` *(new)*, prepares grounded answers to the questions the judges are told to ask as `business/qa-prep.md` *(new)*, and rehearses twice from cold. Part of B3, split in three (B3a value case, B3b slides, **B3c** pitch and Q&A). Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop`.

## 0. Context: read the vault first
The team vault is the shared context space. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Workstreams]] and [[Business case and pitch]] (the brief: rehearse D2 16:00–17:00; Q&A on real vs faked, cost at 100 questions a day, what breaks first, data residency).
3. [[Judging rubric]]: "Questions judges should ask" and the process (10 min pitch/demo + 8 min Q&A; relying on the backup video caps 2.2 at 3). [[Hackathon guideline]] §05 (an unseen input; degrade honestly).
4. [[B2 - Pitch deck - spec]] (the slides the script follows), [[B3b - Architecture and cost slides - spec]] (the appendix used in answers), [[B1 - Business case figures and validation - spec]] (the figures).
5. [[Clement - front end]] (F6: the demo run and the 2-minute backup video), [[2026-10-13 EU-only Bedrock inference profiles]] (D-002), [[global profiles can leave the EU]], [[2026-10-13 Default models]] (D-004).
6. Repo: `DEMO.md` (the 3-minute demo script), `HANDOFF.md`, `COST.md`, `docs/ROADMAP.md`, `EVALS.md` ("What still fails"), `ARCHITECTURE.md` §4 and §7, `DECISIONS.md` D-002, D-004.

**Whenever this spec is silent or unclear, look in the vault before guessing** (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`). If it's still unclear, stop and ask Patrick.

## 1. Intent
**What:**
1. `business/pitch-script.md` *(new)*: the 10-minute run of show: time, slide, who, what they say (word for word), with the live demo from `DEMO.md` at its centre and the fallback if it fails.
2. `business/qa-prep.md` *(new)*: 15 likely questions, each with a two-to-four-sentence answer, its source file, and who answers.
3. Two timed rehearsals from a cold start (D2 16:00–17:00), logged in the vault.

**Why:** the panel decides on what it hears and sees in 18 minutes, and the judges' questions are published in the rubric. Answers prepared from `HANDOFF.md`, `COST.md`, `docs/ROADMAP.md` and D-002 are consistent with the documents the AI reviewers read; improvised ones drift and can overclaim, which the rule of evidence punishes.

**Success means:**
- `business/pitch-script.md` covers 0:00 to 10:00 in rows with no gap or overlap, one row per slide plus the demo, and its spoken figures equal the slides'.
- `business/qa-prep.md` has 15 answers, each with a `Source:` line naming a repo file that holds the fact, and an `Answers:` line naming the person.
- Both rehearsals finish between 9:00 and 10:00 on the clock, from a cold start, and are logged with their times and fixes.
- `uv run --locked pytest` passes with the start count.

**Assumptions:**
- B2 is merged (the 10 slides exist) and B3b is merged or final (A1–A3 for answers). B2's PR body carries its `Slide 5 path:` and `Fact: retry limit` lines; the script follows both.
- **One cost per question:** the `COST.md` "Measured on" average, the same figure as slide 9 and business case line 34. The `COST.md` Total row is the Q01 worked example and is never quoted.
- **The retry limit** is Huvison's written answer to A1's Q09 question (A1 plan Task 4 Step 2), as on slide 8; the code today allows at most one retry, but the script says only his decided wording.
- `HANDOFF.md` has "What's real", "What's faked / stubbed" and "What breaks first" filled by D2 15:00 (Abdul, Patrick). "What breaks first" is `TODO` on `develop` today; if it still is at 15:30, the answer uses `docs/ROADMAP.md` "Top 3 risks" and Patrick is told.
- `DEMO.md`'s script is final (Patrick, Clement, Abdul's lines), and Clement drives the demo (F6).
- **Known inconsistency to settle before Q&A:** `ARCHITECTURE.md` §4 says "The demo runs two synthetic tenants" while §6 says "One synthetic tenant" and `EVALS.md` Q13 is a roadmap question. Patrick decides and fixes the doc; the tenants answer (Q10 below) follows his fix.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Who speaks | **Patrick presents** (brief: Patrick presents), **Clement drives the demo**, Michael keeps time and holds the backup video. Q&A answers are owned by topic (§4) | Everyone takes a slide (handovers cost time) |
| The demo inside the pitch | Live, 3:00, following `DEMO.md`, at 1:30–4:30. Slides 3–5 are the backup if the screen fails mid-demo | The demo at the end (if it fails there's no time to recover); the video by default (caps 2.2 at 3) |
| Fallback order | (1) retry once; (2) slides 3–5, narrated, plus the recorded run's results; (3) the 2-minute backup video (Clement) | Debugging on stage |
| Answer length | Two to four sentences, a number with its source, then stop | Long answers (8 minutes is about 10 questions) |
| Unknowns | "We haven't measured that; here's what we did measure" + the file | A guess |
| Where the rehearsal log goes | The vault session note of D2, not the repo (it is about the team, not the product) | A repo file written after the submission deadline |

## 3. `business/pitch-script.md` *(new)*: exact content
`<…>` slots are copied from the slide or file named; the spoken figure must equal the slide's.

```markdown
# Pitch script: ERP Migration Progress Portal (10 minutes)

> Patrick presents; Clement drives the demo; Michael keeps time and holds the backup video. The live demo follows `DEMO.md`. Every figure said aloud is on a slide, with its source.

| Time | Slide | Who | What we say |
|---|---|---|---|
| 0:00–0:45 | 1 | Patrick | "The CFO of a mid-market industrial group is funding an 18-month consolidation of several ERPs onto one. The CFO carries the risk, and decides cutover dates, staffing and spend on a picture that can be four weeks old. Not the CIO: the person paying for it." <If the quote box is on slide 1: "In the problem owner's words: <quote>."> |
| 0:45–1:30 | 2 | Patrick | "Today that picture is a hand-built monthly steering deck. Every 'are we on track, what's blocked?' costs a consultant two days. On our stated assumptions that's about $14,500 of consultant time a month. This replaces both." |
| 1:30–4:30 | demo (backup: 3–5) | Clement drives, Patrick narrates | The `DEMO.md` script from 0:30 to 2:35: the one screen (58 % reconciled, E4 Blocked; click a number to its rows) → ask "What is blocking cutover for E4?" with the trace running → the answer, each line cited → <by `Fact: slide 5 path`: path `main`: "**the critic rejecting the DEF-0398 claim while RC-C3-E4-customers still fails**"; path (a) or (b): "**the answer flagging the DEF-0398 conflict, and the critic rejecting <the claim slide 5 shows> (labelled <eval Q08 / its question ID>)**"> → publish → approve. Patrick's line at that moment: <path `main`: "The defect log says fixed. The data says it isn't. A status deck would have shown green. The critic only sees the claim and its rows, so it can't be talked round."; path (a) or (b): "The defect log says fixed. The data says it isn't, and the answer says so. A status deck would have shown green. And when a claim has no rows behind it, the critic rejects it: it only sees the claim and its rows, so it can't be talked round."> |
| 4:30–5:30 | 6 | Patrick | "The numbers on that screen are plain code: no model, no tokens. The question isn't. There's no fixed checklist for 'what's blocking E4', so from what it just found, one orchestrator decides which of 14 scoped tools its two helpers use next, and re-plans when the critic rejects a claim. Everything with a known order is a Step Functions flow." |
| 5:30–6:30 | 7 | Patrick | "What you saw is the POC, built in two days, plus one production layer: <Cognito line from slide 7, spoken>. The rest, live connectors, policy-based access, data-layer row filters, audit, the next tenant, is the 90-day plan, phase by phase." |
| 6:30–7:30 | 8 | Patrick | "Six controls, each in the code: every claim cited, a blind critic that fails closed, <Fact: retry limit, as on slide 8> counted in the ledger, nothing published without the delivery lead, Guardrails on every model call, and a $0.50 budget per question. <pass> of <total> eval questions pass; what still fails is written down." |
| 7:30–8:45 | 9 | Patrick | "A question costs $<cost> measured, against $2,000 today. A pilot runs at about $<pilot monthly> a month. The value is about $14,500 a month and $261,000 over one programme, on assumptions we state, with payback in <months> months on the pilot. <count sentence from slide 9>." |
| 8:45–10:00 | 10 | Patrick | "We're asking for a 6-week pilot on one real programme: a sponsor, your delivery lead as product owner, read access to three tools. We go on at week 6 only if 85 % of 40 questions come back right with citations, nobody sees outside their scope, and two status packs are approved with minor edits. From two days per answer to seconds, with the proof attached." |

## If the demo fails
1. Clement retries the step once (10 seconds).
2. If it fails again, Patrick says "Here's the same run, recorded at <time> today" and walks slides 3–5, which carry the real run's answer and rejection.
3. If the screen itself is gone, Michael plays the 2-minute backup video.
The pitch still ends at 10:00: cut slide 8 to one sentence first.
```

## 4. `business/qa-prep.md` *(new)*: exact content
Each answer: **Q**, the answer (2–4 sentences), `Source:` (repo file and section), `Answers:` (person). `<…>` slots from the named source.

```markdown
# Q&A preparation: ERP Migration Progress Portal (8 minutes)

> Two to four sentences, a number with its source, then stop. If we haven't measured it, say so and give what we did measure.

## 1. What's real and what's faked?
Real: every number on the screen is computed from the artefacts by tested code; the agent loop, the blind critic, the retry limit in the run ledger, Guardrails, the budget ceiling and approved publishing run in AWS <Cognito: "with Cognito sign-in and entity scope" | "and sign-in fell back to a CFO demo user at our 12:00 go/no-go">. Faked: all data is synthetic, ingestion is CSV files in S3 rather than live feeds, and the as-of date is fixed at 13 October 2026. Not built, by design: Verified Permissions, Athena and Glue, Lake Formation, connectors, CloudTrail and multi-tenant onboarding, which are the 90-day plan.
Source: `HANDOFF.md` "What's real", "What's faked / stubbed"; `DECISIONS.md` D-015. Answers: Patrick.

## 2. What does it cost at 100 questions a day?
About $<Full> a month: $<average> per question, the measured average over the recorded run (`COST.md` "Measured on"), times 3,000 questions. The dashboard makes no model calls, so viewing is nearly free. Levers: a cheaper model for retrieval, cached answers per entity and data version, and the per-question ceiling.
Source: `COST.md` "Measured on", "Scale", "Cost levers". Answers: Patrick (Huvison if present).

## 3. What breaks first?
<HANDOFF.md "What breaks first", first bullet, in one sentence.> On real data, the first risk is IDs that don't line up across the workplan, the defect tracker and the reconciliation exports; the pilot's week-2 data-quality report and an ID mapping table owned by the client's delivery lead address it, and we stop if the mapping isn't agreed by week 4.
Source: `HANDOFF.md` "What breaks first"; `docs/ROADMAP.md` "Top 3 risks". Answers: Patrick.

## 4. Where does the data go? (data residency)
Everything runs in eu-west-1 (Ireland). Models are called only through Bedrock's EU inference profiles (`eu.*`), which keep requests inside EU regions; we rejected the global profiles because they can route outside the EU. Guardrails filter PII on every model call, and the demo uses synthetic data only.
Source: `DECISIONS.md` D-002; `config.py` (region); `ARCHITECTURE.md` §7. Answers: Patrick.

## 5. Who signs the purchase order?
The CFO or the programme sponsor of the portfolio company running the consolidation; the delivery lead is the product owner day to day. The pilot needs both named before week 1.
Source: `docs/ROADMAP.md` "What we need from the client"; `business/business-case.md` §1. Answers: Patrick.

## 6. Which number moves, and by how much?
Time to answer a status question: from 2 consultant-days to <seconds> seconds measured. The monthly status pack: from about 3 days of building to half a day of review. Both on assumptions stated in the business case.
Source: `business/business-case.md` §2 (KPI table). Answers: Michael.

## 7. Why this model and not a cheaper one?
Claude Sonnet 4.6, through the EU profile, does the judgement steps: planning, analysis, the critic and the writer. Retrieval uses Amazon Nova Lite (or Claude Haiku 4.5 if its access was activated), which is cheaper and faster, because it interprets nothing. We rejected Opus-class models as too slow and costly for a live loop; the measured cost per question is $<average> on average.
Source: `DECISIONS.md` D-004; `config.py`; `COST.md`. Answers: Patrick.

## 8. Show us an answer it gets wrong.
<EVALS.md "What still fails", the first real failure from the recorded run, in one sentence, with its question number.> We record failures as they are; a perfect eval sheet would be a missing one.
Source: `EVALS.md` "Results", "What still fails". Answers: Patrick.

## 9. What if the critic rejects something true?
Then the claim shows as "could not verify" with the critic's reason, never as a guess, and lands in the rejected-records store for a person to work through. The critic fails closed by design: we prefer a missing claim to a wrong one in front of a CFO.
Source: `AGENTS.md` (critic row); `ARCHITECTURE.md` §2. Answers: Patrick.

## 10. How does the next portfolio company get this?
A new tenant: a data prefix, a connector configuration and its users, with no code changes, live within about 5 working days of data access (proposed). Each tenant sees only its own rows, enforced in code today and in the data layer in the target.
Source: `ARCHITECTURE.md` §4; `docs/ROADMAP.md` Phase 3; `business/business-case.md` §3. Answers: Michael.

## 11. What do you need from the client's IT team?
Read access to the project tool, the defect tracker and the migration tool's reconciliation outputs; identity-provider federation and the users per role; a security reviewer in weeks 6 to 9; the financial-close and holiday calendars.
Source: `docs/ROADMAP.md` "What we need from the client". Answers: Michael.

## 12. What would make you stop?
Three stop conditions, set in advance: the ID mapping isn't agreed by week 4; accuracy is below 85 % after week 6; or there's no data access by week 3.
Source: `docs/ROADMAP.md` "Top 3 risks" (Stop if). Answers: Patrick.

## 13. What stops a defect note from hijacking the agent?
Artefact text is treated as data: it reaches the agents inside evidence tags, the Guardrail's prompt-attack filter is on, citations are checked in code before the critic runs, and the critic fails closed. We planted a defect whose text says "ignore previous instructions": <EVALS.md Q12 result from the recorded run>.
Source: `ARCHITECTURE.md` §7; `EVALS.md` Q12; `DECISIONS.md` D-009. Answers: Patrick.

## 14. Why is this agentic, not a dashboard with a query?
The dashboard is a query, and we built it as plain code. The question "what is blocking E4?" has no fixed path: the next row to read depends on what the last one said, from a failing reconciliation to its load errors to the defect to the runbook step. That's the one place we use a planning agent.
Source: `DECISIONS.md` D-001; `ARCHITECTURE.md` §2; `AGENTS.md`. Answers: Patrick.

## 15. What happens with 10 times the users?
Cost scales with questions, not users: everything is serverless and pay-per-request, and the dashboard spends no tokens. At 100 questions a day it is about $<Full> a month; the 29-second API limit is the first thing to watch on long questions, <the `/ask` timing decision from Huvison, one clause>.
Source: `COST.md` "Scale"; `ARCHITECTURE.md` §8. Answers: Patrick (Huvison if present).
```

## 5. Rehearsals (D2 16:00–17:00)
Twice, from a cold start (fresh browser profile, signed out, the portal not yet opened; `DEMO.md` pre-flight checklist done). Michael times each section against the script's rows. After each, record in the vault session note of D2 under `## Pitch rehearsals`: `Run <1|2>: total <m:ss>; demo <m:ss>; over/under by section: <list>; fixes: <list>`. Run 2 must finish between 9:00 and 10:00. Then Michael asks five questions from `business/qa-prep.md` at random; Patrick answers each in under 45 seconds; any answer over 45 seconds or with a wrong figure is fixed in the file.

## 6. Checks
- `test -f business/pitch-script.md && test -f business/qa-prep.md`.
- `grep -c -E '^\| [0-9]+:[0-9]{2}–[0-9]+:[0-9]{2} \|' business/pitch-script.md` → `8` (rows), and the last row ends at `10:00`.
- `grep -c '^## [0-9]' business/qa-prep.md` → `15`; `grep -c '^Source: ' business/qa-prep.md` → `15`; `grep -c 'Answers: ' business/qa-prep.md` → `15`.
- `grep -c 'TBC\|TODO\|<' business/pitch-script.md business/qa-prep.md` → `0` for both (every slot filled).
- `grep -c 'CIO' business/pitch-script.md` → `1` (only "Not the CIO").
- `uv run --locked pytest`: the start count.

## 7. Out of scope
- `DEMO.md` (its owners), the backup video (F6, Clement), any slide change (B2, B3b): report mismatches to their owners.
- Answering questions about code that isn't merged: say it's on the roadmap.

Related: [[Build order]], [[Business case and pitch]], [[B3c - Pitch script and Q and A - plan]]
