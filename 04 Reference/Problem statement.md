---
date: 2026-10-01
source: "[[ERP Migration Portal problem statement.pdf]]"
tags: [reference, area/scope]
---
# Problem statement: ERP Migration Progress Portal
Internal AWS Hackathon · October 2026. Source: Ventures meeting, 1 Oct 2026. Also as [[ERP Migration Portal problem statement.docx|.docx]].
> **Not a duplicate of idea 3** ([[Ten use cases#UC-03 Eighteen ERP systems, one map|UC-03]]). That one is discovery, working out what ERP estate a company has before anything moves. This is execution: showing where the migration has got to once it is under way.

![[ERP Migration Portal problem statement.pdf]]

| # | Field | Content |
|---|---|---|
| 1 | Submitted by | AmaliTech Ventures, ERP modernisation track |
| 2 | Working title | **Show the client where the migration actually is** |
| 3 | Industry / domain | Enterprise software migration. A mid-market industrial group consolidating several ERP systems onto one platform over about eighteen months |
| 4 | The problem | An ERP migration runs 12–24 months and for most of it the client cannot see where it has got to. Progress arrives as a monthly steering deck built by hand, so the sponsor's picture is weeks old and shaped by whoever made the slides. Are we on track, what is blocked, how much is left: each takes a consultant **two days** to answer, every time it is asked |
| 5 | Who feels it | The **programme sponsor** and the **CFO** funding it, carrying the risk without a live view of it, and the **delivery lead** who rebuilds the same status pack by hand every month |
| 6 | What "solved" looks like | One screen both sides open (source systems, target, timeline, capacity, percent complete) with every figure derived from the migration's own artefacts rather than typed into a deck. Ask what is blocking cutover for entity four and get it in seconds, with the evidence attached |
| 7 | Data that exists today | Migration workplan, object inventory per source system, reconciliation results per load cycle, defect log, cutover runbook, team roster. All six can be generated synthetically at the right shape |
| 8 | External data that would matter | Vendor support-lifecycle dates. Published capability of infrastructure tooling such as AWS Transform, for the automation estimate. Holiday and financial-close calendars, which constrain cutover weekends |
| 9 | KPIs | Objects migrated and reconciled; reconciliation pass rate per load cycle; open blockers by age; days to cutover against plan; capacity used against planned. Glossary → [[Glossary]] |
| 10 | Why hasn't it been done? | Not prioritised. Rebuilding the status pack is a few days a month, which never becomes a budget line, so every engagement pays for it again. Existing tooling sits at the infrastructure layer and speaks to engineers, not to the person funding the programme |
| 11 | A convincing 72-hour demo | One screen carrying source, target, timeline, capacity and percent complete, every number derived from the synthetic artefacts, plus **one agent loop that genuinely runs**: what is blocking cutover for this entity, answered with its evidence. *The back end may be stubbed. The agent layer may not: a screen that only looks like the answer is a mockup, and we know what a mockup looks like* |
| 12 | What must be stripped | Portfolio company and system names (describe systems by tier and role instead). The real workplan, dates and record counts. Team member names in the roster |
| 13 | Problem owner | **Vanessa Addo**, with **Joseph Akayesi** for oversight. *Please confirm with both before submitting* |

## How this maps to the grading
- Named executive (deck, 6 pts): **CFO** / programme sponsor, not the CIO.
- What it replaces (deck, 5): hand-built monthly status pack + ~2 consultant-days per status question.
- Why agentic (deck, 5): the blocker question follows a path that depends on what each step finds → [[2026-10-13 Metrics are code, only the blocker Q&A is agentic|Metrics are code]].
- Reuse (business case, 5): every engagement pays for the status pack again (row 10), so it's a template for every portfolio company's migration.

Related: [[Reference]], [[Pitch track grading rubric]], [[Repo]]
