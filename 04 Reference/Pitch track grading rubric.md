---
date: 2026-10-13
source: "[[Pitch Track Grading Rubrics.pdf]]"
tags: [reference, area/judging]
---
# Pitch track grading rubric (AmaliTech-AWS Hackathon Rubrics, 13 Oct 2026)
> **This is how we are actually scored.** It is newer than the [[Judging rubric|judging rubric proposal]] (9 Oct) and replaces its 40/30/30 human-panel model with **four AI reviewers**. Confirm with the organisers if the two ever conflict.

![[Pitch Track Grading Rubrics.pdf]]

## Overview
- Scored out of **100**. **Four AI reviewers**, each scoring a different part of the submission; points are added up.
- Demo is presented **on site**: nothing needs to be hosted or sent as a link.
- **GitHub repo = 50/100**: agent design, documentation and trust count more than pitch polish. Inside the repo, **the markdown files and the agent definitions count most**.
- The problems are inside existing companies, so the deck and business case ask about **the executive and the value**, not market size or go-to-market.
- The AI is set up for consistency: same submission → same score, same written criteria for all.
- Rating per item **0 (missing) – 4 (exceptional)** → that share of the item's points (e.g. 3/4 on 8 pts = 6).

## Pitch deck: 20
| Item | Pts | What earns them |
|---|---|---|
| Named executive | 6 | A named portfolio-company executive (COO, CFO, VP ops) whose week gets better. **Not the CIO** |
| What it replaces | 5 | The manual or consultant process it replaces, and what that costs today |
| Why it is agentic | 5 | Multiple steps, a decision about what to do next, tools it chooses between. If a Lambda + SQL query would do, it's the wrong brief |
| Scope and demo moment | 4 | Cut down to what's buildable in 2 days, with a clear moment where the demo lands |

## Business case: 20
| Item | Pts | What earns them |
|---|---|---|
| The problem | 8 | Real, specific, painful problem for a named role inside a portfolio company |
| Value if solved | 7 | Impact sized in real numbers with the assumption stated (days saved, margin recovered, cost removed) |
| Reuse across portfolio companies | 5 | A clear case that it works as a template for the next portfolio company |

The reviewer rewards **specifics over polish**: named roles, real numbers, stated assumptions. **If it isn't in the document, no credit.**

## Product spec: 10
| Item | Pts | What earns them |
|---|---|---|
| Completeness | 3 | Clearly states what the product must do |
| Feasibility | 3 | Features realistic to build |
| Priorities | 2 | Clear about what gets built first |
| User stories | 1 | How real users will use it |
| Success measures | 1 | Measurable targets for knowing it works |

## GitHub repo: 50
Read as laid out in §4 of the [[Hackathon guideline]]: the 8 markdown files (README, ARCHITECTURE, AGENTS, EVALS, DEMO, COST, DECISIONS, HANDOFF) + agents, tools, evals, infra, demo folders. **It also checks the history of changes.**

| Item | Pts | What earns them |
|---|---|---|
| AGENTS.md | 10 | One row per agent, all 7 columns (name, single responsibility, input schema, output schema, tools, guardrail, failure mode). Every row complete |
| Roles and orchestration | 10 | One job per agent, nameable in six words. Orchestrator plans and routes, no domain work. ARCHITECTURE.md says which steps are fixed Step Functions flows and which are agents |
| Trust built in | 12 | Every claim cites a source. Critic judges blind and **visibly rejects something**. Reject loop bounded by a counter in the run ledger. Human approval before any write, guardrails on, budget ceiling per run |
| Honest evals | 6 | EVALS.md: fixed input set, real scores, what still fails. No failures = missing |
| README, cost and handoff | 8 | README runs in 5 commands; brief's layout followed. COST.md: **measured** cost per run and at 100 runs/day. HANDOFF.md: real / faked / breaks first. DEMO.md and DECISIONS.md present and useful |
| Worked examples and tests | 4 | A real input and real output committed **for each agent**; unit tests on deterministic tools |

### Five hard gates (fail any → repo fails)
1. Deploys from a clean account with the documented commands.
2. Eval set runs and results are written down, including failures.
3. No autonomous write to any system of record.
4. No real client data in repo, logs or prompts.
5. AGENTS.md exists and every row is complete.

## Totals
| Area | Pts |
|---|---|
| Pitch deck | 20 |
| Business case | 20 |
| Product spec | 10 |
| GitHub repo | 50 |
| **Total** | **100** |

Related: [[Reference]], [[Judging rubric]], [[Hackathon guideline]], [[Graders are AI and read only what is written]]
