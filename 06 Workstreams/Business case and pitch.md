---
tags: [workstream, area/team, area/business]
owner: Patrick + Michael
updated: 2026-10-14
---
# Business case, product spec and pitch deck (Patrick + Michael)
> The repo is the source of truth. Read [[Workstreams]] first. Your row: `docs/TEAM_PLAN.md` §2, workstream 7. Michael wrote `business/business-case.md` (PR #9) and `business/product-spec.md` (PR #14); Patrick co-owns, reviews and presents.

## Why this matters
**Half the score is these documents**:
- pitch deck **20**;
- business case **20**;
- product spec **10**.

The source is the Pitch Track rubric of 13 Oct ([[Pitch track grading rubric]]). Four AI reviewers score them. **They reward specifics over polish** (named roles, real numbers, stated assumptions), and **if it isn't in the document, there's no credit.**

## What the rubric scores
| Document | Item | Pts | What earns them |
|---|---|---|---|
| **Pitch deck** | Named executive | 6 | A named portfolio-company executive whose week gets better: **the CFO** (not the CIO) |
| | What it replaces | 5 | The manual or consultant process and what it costs today: the hand-built monthly steering deck; 2 consultant-days per status question *(brief)* |
| | Why it is agentic | 5 | Multiple steps, a decision about what to fetch next, tools it chooses between. Point to `AGENTS.md` and `ARCHITECTURE.md` §2. If a Lambda + SQL query would do, it's the wrong brief |
| | Scope and demo moment | 4 | Cut to what's buildable in 2 days, with a clear moment where the demo lands: the critic visibly rejecting the decoy (`DEF-0398` closed, `RC-C3-E4-customers` still failing) |
| **Business case** | The problem | 8 | Real, specific, painful, for a named role |
| | Value if solved | 7 | Sized in real numbers with stated assumptions |
| | Reuse across portfolio companies | 5 | A template for the next portfolio company (a tenant = a new prefix + connector config + users, `ARCHITECTURE.md` §4) |
| **Product spec** | Completeness 3 · Feasibility 3 · Priorities 2 · User stories 1 · Success measures 1 | 10 | `business/product-spec.md` is already structured this way (§2–§6) |

## What the 9 Oct proposal also asks you to submit
- **A one-page value case,** derived from `business/business-case.md`.
- **A live demo plus a 2-minute backup video** (Clement records it; `DEMO.md`).
- **The POC and target architecture as 1–2 slides** (`ARCHITECTURE.md` §3 and §3b; Abdul's target diagram v2).
- **A cost and 90-day-plan slide** (`COST.md`, measured; `docs/ROADMAP.md` with phases, top-3 risks and go/no-go criteria).
- **A 10-minute pitch plus 8 minutes of Q&A.**

## What you build
1. **Close every `[TBC]` in `business/business-case.md`.** Each one gets a validated figure, or is clearly marked *proposed* with who confirms it:
   - line 23: the validation session date and **one quote in the problem owner's words**;
   - line 31: time to answer a status question, **measured in the demo** (from Huvison's `/ask` timing);
   - line 34: cost per answered question, the **measured cost per run** from `COST.md` (Abdul, Huvison);
   - line 46: portal run cost per month (`COST.md` × questions per month);
   - line 51: payback, the pilot priced by delivery (`docs/ROADMAP.md` pilot);
   - line 79: how many portfolio companies have an ERP consolidation planned or under way, **from the problem owner**.
2. **Book the 15-minute validation session** with the problem owner (Vanessa Addo) and oversight (Joseph Akayesi) for **D1 09:30** (TEAM_PLAN §4). Bring three questions:
   - the executive and their pain;
   - the cost today;
   - the portfolio count.

   Write the answers into the business case the same day.
3. **Review `business/product-spec.md` against the rubric:**
   - every "must do" has a feasibility note;
   - priorities say what's built first (the POC plus the Cognito slice, D-015);
   - success measures are measurable (for example "answer in under 60 seconds, every claim cited", "58% reconciled shown from source rows").
4. **The pitch deck** (*new*: commit the source and a PDF under `business/`, e.g. `business/pitch-deck.pdf`). Suggested 10 slides:
   1. the CFO's problem;
   2. what it replaces and its cost;
   3. the one screen (58%, E4 Blocked);
   4. ask "what is blocking E4?", with the cited chain;
   5. **the critic rejecting the decoy** (the demo moment);
   6. why it's agentic;
   7. the POC and target architecture;
   8. trust (citations, blind critic, ledger-bounded retry, human approval, guardrails, budget);
   9. cost and value;
   10. the 90-day plan and the ask (pilot).
5. **The one-page value case** from the business case.
6. **The "why it's agentic" interview** (D1 evening): 15 minutes with Patrick and Huvison on how the orchestrator decides the next step and what the critic rejects. Quote the real behaviour, not aspirations.
7. **Rehearse the 10-minute pitch** with the demo (D2 16:00–17:00), and prepare answers for 8 minutes of Q&A:
   - what's real vs faked (`HANDOFF.md`);
   - cost at 100 questions a day;
   - what breaks first;
   - data residency (`eu-west-1`, `eu.*` models).

## Inputs you need from others
| Input | From | Where |
|---|---|---|
| Measured cost per run, scale costs | Abdul, Huvison | `COST.md` |
| `/ask` time per question | Huvison | ledger / `COST.md` |
| Demo numbers and script | Patrick, Clement | `DEMO.md` |
| Target diagram v2 | Abdul | `docs/architecture-target-v2.png` *(new)* |
| Roadmap phases, top-3 risks, go/no-go | Linus + Abdul draft, Patrick reviews | `docs/ROADMAP.md` |
| Eval results ("it visibly rejects") | Abdul, Linus | `EVALS.md` |

## Your milestones
| When | Milestone |
|---|---|
| D1 09:30 | Validation session booked |
| D1 evening | Business case `[TBC]`s for the problem, the quote and the portfolio count closed; deck outline |
| D2 14:00 | Measured cost and time in the business case; the deck drafted |
| **D2 15:00** | **Lead review of all three documents** (TEAM_PLAN §4) |
| D2 16:00–17:00 | Rehearse the pitch twice with the demo |

## Definition of done
- [ ] No `[TBC]` left in `business/business-case.md`; each assumption says who confirms it.
- [ ] Product spec passes its rubric checklist.
- [ ] Deck committed (source + PDF), covering the four scored items, with the demo moment.
- [ ] One-page value case; architecture and cost/roadmap slides.
- [ ] Pitch rehearsed twice; Q&A answers prepared.

## Rules and pitfalls
- **The executive is the CFO, not the CIO.** Name the role precisely.
- **Every number has its source** (*(brief)*, measured, or *proposed* with the assumption). Never present an estimate as measured.
- **No real client data or names** beyond the problem owner and oversight from the brief, as the brief names them. No secrets.
- **Don't promise the target as built.** POC + Cognito slice is built; the rest is the 90-day roadmap (D-015).

## Your AI assistant
Give it `06 Workstreams/prompts/business.txt`.

## Who to ask
| Topic | Person |
|---|---|
| Agents, demo, roadmap | Patrick |
| Critic, cost, timing | Huvison |
| Measured costs, evals, diagram | Abdul |
| Demo video | Clement |

Related: [[Workstreams]], [[Team plan]], [[Pitch track grading rubric]], [[Judging rubric]]
