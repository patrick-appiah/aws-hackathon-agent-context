---
date: 2026-10-09
source: "[[Judging Rubric Proposal.pdf]]"
tags: [reference, area/judging]
---
# Judging rubric **proposal** (9 Oct 2026)
> Earlier **proposal** for a human judging panel. The [[Pitch track grading rubric]] (13 Oct) is the newer scoring model. Keep this for its gates, judge questions and the required submissions, which still describe what a good POC looks like.

![[Judging Rubric Proposal.pdf]]

## Purpose
The winning POC is one the customer would fund next quarter *and* our architects would put their name on. Sales: problem, measurable outcome, credible path to a paid engagement. Architecture: must run on AWS, be honest about what's mocked, show a path to production (security, cost, operability). Every criterion has written level descriptors so judges score evidence, not charisma.

## Scoring (proposal): 40 / 30 / 30, each criterion rated 1–4
| Pillar | Criterion | Pts | Lead |
|---|---|---|---|
| Business value 40 | 1.1 Customer problem & stakeholder fit | 12 | Sales |
| | 1.2 Quantified impact & ROI | 16 | Sales |
| | 1.3 Path to adoption & commercial follow-on | 12 | Sales |
| Problem solving 30 | 2.1 Appropriateness of the AI approach | 12 | Architect |
| | 2.2 Working demo & evidence of quality | 12 | Architect |
| | 2.3 Creativity & use of AWS services | 6 | Joint |
| Implementation 30 | 3.1 Target architecture & production readiness | 12 | Architect |
| | 3.2 Cost model & operability | 9 | Joint |
| | 3.3 Delivery roadmap, risks & next steps | 9 | Sales |

Rating: 4 Exemplary (customer-ready) 100% · 3 Strong 75% · 2 Developing 40% · 1 Weak 10%.

## Gates (pass/fail)
- **Security & data handling:** no customer data or secrets in code or prompts; least-privilege IAM; data stays in region. Fail = disqualified until fixed.
- **Responsible AI:** name the main failure mode (hallucination, bias, harmful output) and show ≥1 guardrail (Bedrock Guardrails, grounding with citations, human review).
- **Rule of evidence:** any claim not shown in demo, repo or diagram caps that criterion at 2 → [[Rule of evidence caps claims at 2]].

## Level descriptors: what a 4 looks like
- **1.1:** names business owner, user and pain in the customer's language; validated with customer input *during the event*.
- **1.2:** baseline vs target on 1–2 KPIs (e.g. handling time 12 → 4 min), stated assumptions, payback estimate.
- **1.3:** specific next engagement (pilot scope, users, duration, sponsor), change-management needs, how success is signed off.
- **2.1:** justifies rules vs ML vs GenAI vs agent and model choice on accuracy, latency, cost; RAG/tools where grounding matters.
- **2.2:** end-to-end live on AWS with realistic data; small eval set with results (e.g. 40 questions, 88%); failure cases shown honestly.
- **2.3:** novel angle; managed services chosen well (Bedrock, KB/Agents, SageMaker, Lambda, Step Functions) without over-engineering.
- **3.1:** POC vs target diagram covering identity, data flow, integration, security controls, Well-Architected trade-offs.
- **3.2:** monthly run cost at pilot and full scale (tokens, compute, storage), cost levers; monitoring, evaluation, model-update plan.
- **3.3:** phased plan (e.g. 6-week pilot, 3-month production), team, customer dependencies, top-3 risks with mitigations, go/no-go criteria.

## Questions judges should ask
- Who signs the PO? What happens on Monday if this works? Which number moves, and by how much?
- Why this model and not a cheaper one? Show me an answer it gets wrong. What is mocked?
- What does it cost per month at 10× the users? What do you need from the customer's IT team? What would make us stop?

## Process (proposal)
Panel of sales lead + solutions architect + customer rep. Calibration → gate check (architect checks repo and IAM) → **10 min pitch/demo + 8 min Q&A, demo must be live** → independent scoring with evidence notes → reconcile 2+ level gaps → average. Tie-breaks: business value, then 2.2, then customer preference. Optional awards: Customer's Choice, Best Architecture.

## Required submissions (1 h before pitches)
| Item | Format | Evidences |
|---|---|---|
| One-page value case: problem, owner, KPIs with baseline and target, ROI assumptions | 1 page | 1.1–1.3 |
| Live demo in team's AWS account + 2-min backup recording | URL + video | 2.2, 2.3 |
| Repo with README (real vs mocked) + eval results | Git repo | gates, 2.1, 2.2 |
| Architecture diagram: POC + target | 1–2 slides | 3.1 |
| Cost estimate + 90-day plan with top-3 risks | 1 slide/sheet | 3.2, 3.3 |
Relying on the backup recording caps 2.2 at 3.

## Tensions and resolutions
Weighting (sales vs architect) → 40/30/30 with pillar 3 shared · polish vs working system → rule of evidence + live demo · ambition vs honesty → pitch the vision but label mocks · security/RAI → pass/fail gates · cost → required estimate.

## Open decisions for organisers (as of the proposal)
40/30/30 or 50/25/25 · customer rep judging, counted or advisory · sanitised vs synthetic data only · AWS budget cap per team account and region.

Related: [[Reference]], [[Pitch track grading rubric]]
