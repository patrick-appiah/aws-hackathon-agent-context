---
tags: [build, spec, area/docs, area/business]
id: L7
owner: Linus (with Abdul)
status: ready
updated: 2026-10-14
---
# L7: the `docs/ROADMAP.md` draft (spec)
> **A doc-update item, no code.** `docs/ROADMAP.md` already has the phases, the client dependencies, the top-3 risks and go/no-go criteria. This draft closes what the judging rubric still asks for and checks the rest against the architecture, so Patrick can finalise it on D2. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop`.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Linus - API, identity, blocker-analyst]] §7 and [[Abdul - evals, Cognito, docs]] ("`docs/ROADMAP.md` draft with Linus"): who does what.
3. [[Patrick - contracts, orchestrator, retriever]]: Patrick finalises the roadmap on D2 and adds the monitoring, evaluation and model-update plan (Judging rubric 3.2).
4. [[Judging rubric]] (3.2 cost model and operability, 3.3 delivery roadmap, risks and next steps; the rule of evidence) and [[Pitch track grading rubric]].
5. [[Roadmap]] (`04 Reference/`, a synced copy of the repo's `docs/ROADMAP.md`; the repo copy is canonical).
6. The repo's `docs/ROADMAP.md` (**read it whole first**: most of it already exists), `ARCHITECTURE.md` §3b and §6, `COST.md`, `HANDOFF.md`, `business/business-case.md`.
7. `01 Decisions/`: [[2026-10-13 POC plus one target slice, target as 90-day roadmap]] (D-015), [[2026-10-13 Two architecture views, POC and target]].

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[Problem statement]], [[Judging rubric]], [[Pitch track grading rubric]], [[Hackathon guideline]]); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Linus. Never invent a name, a shape or a rule.

## 1. Intent
**What:** four additions to `docs/ROADMAP.md`, and one consistency check, made by Linus and reviewed line by line by Abdul:
1. **Pointers in the intro:** each target component's phase is in `ARCHITECTURE.md` §6; the monthly cost at pilot and full scale is in `COST.md`.
2. **"Evidence, not claims" under Phase 0:** where the judges can check what Phase 0 proved (`EVALS.md` results with failures, `HANDOFF.md`, `DEMO.md`).
3. **A new section "Monitoring, evaluation and model updates (proposed)":** monitoring, evaluation, model and prompt updates, and who runs it after week 10 (rubric 3.2's "monitoring, evaluation, model-update plan"). Patrick finalises its wording.
4. **A new section "The first week after a yes":** the three actions of week one (the judges ask "what happens on Monday if this works?").
5. **The check:** every phase in the roadmap matches the "Roadmap phase" column of `ARCHITECTURE.md` §6; every go/no-go line is measurable; every risk has a "Stop if"; the client dependencies match what the business case asks for.

**Why:**
- Rubric 3.3 (9 points) scores the phased plan, team, customer dependencies, top-3 risks and go/no-go criteria; 3.2 (9 points) scores the monitoring, evaluation and model-update plan. Half the total score is documents.
- The rule of evidence caps any claim not shown in the demo, repo or diagram at 2: the roadmap must point at evidence for what Phase 0 claims.

**Success means:**
- `docs/ROADMAP.md` contains the two new sections and the two new lines, word for word as in the plan (or as Abdul's review changed them, each change recorded in the PR).
- Abdul's review checklist (plan Task 2) is posted in the PR with every line ticked or commented.
- The repo's doc guards pass (`tests/test_dependencies.py`, `tests/test_code_style.py`: commands run through `uv`, test paths start with `tests/`).
- The PR is merged into `develop` before D2 14:00, so Patrick can finalise it in the D2 14:00–16:00 slot.

**Assumptions:**
- Abdul reviews in the GitHub web interface (no Python, no terminal). Linus makes the edits and runs the guards.
- Patrick, not this item, decides the final wording and any phase or date change. Anything this draft can't settle goes in the PR as a question for him.
- The vault's [[Roadmap]] note is regenerated from the repo by the lead after merge (its header says so); this item doesn't edit it.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Rewrite or extend | Extend: the existing phases, risks and criteria are already concrete; add only what the rubric still asks for | A rewrite (churn, and loses Patrick's earlier wording) |
| Where the monitoring plan goes | A section in `docs/ROADMAP.md`, marked *(proposed)* like the other targets | A new doc (one more file for judges to find) |
| Numbers in the new sections | Only numbers already in the repo (29 s, 14 → ~40 questions, the `COST.md` estimate, week 10) | New targets (Patrick and the problem owner set those) |
| Who edits | Linus edits; Abdul reviews with a checklist and suggests changes in the PR | Abdul editing Markdown with the guards unchecked |

## 3. The exact additions
The plan (Task 1) gives each one as an exact find-and-insert, so the result is checkable line by line.

## 4. Checks (instead of unit tests)
- Doc guards: `uv run --locked pytest tests/test_dependencies.py tests/test_code_style.py --no-cov` → `15 passed`.
- Abdul's eight-line review checklist (plan Task 2), posted in the PR.

## 5. Out of scope
- The final wording, dates and phase changes (Patrick, D2).
- The target diagram v2 (Abdul, A4) and the cost figures (`COST.md`, A3).
- The business case and pitch slides (B1–B3), which reuse this roadmap.

Related: [[L7 - Roadmap draft - plan]], [[Roadmap]], [[Judging rubric]], [[Build order]]
