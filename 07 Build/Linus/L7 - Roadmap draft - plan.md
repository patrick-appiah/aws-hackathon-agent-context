---
tags: [build, plan, area/docs, area/business]
id: L7
owner: Linus (with Abdul)
spec: "[[L7 - Roadmap draft - spec]]"
status: ready
updated: 2026-10-14
---
# L7: the `docs/ROADMAP.md` draft (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]] (the doc-only parts: setup, ledger, PR, Build order).
2. [[L7 - Roadmap draft - spec]]: **the authority.**
3. The repo's `docs/ROADMAP.md`, read whole, then `ARCHITECTURE.md` §6 and `COST.md`.
4. [[Judging rubric]] 3.2 and 3.3, and [[Abdul - evals, Cognito, docs]] (how Abdul works: no Python).

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[Problem statement]], [[Judging rubric]], [[Pitch track grading rubric]], [[Hackathon guideline]]); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Linus. Never invent a name, a shape or a rule.

**Goal:** `docs/ROADMAP.md` answers everything rubric 3.2 and 3.3 ask, points at evidence for Phase 0, and is consistent with `ARCHITECTURE.md` §6, ready for Patrick's final pass.

**Architecture:** one Markdown file. No code.

**Tech stack:** a text editor and git for Linus; the GitHub web interface for Abdul. Linus runs the doc guards with `uv run --locked pytest ... --no-cov` (Abdul never runs Python).

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: **`docs/roadmap-draft`** from an up-to-date `develop`. No dependency: start any time on D1 evening.
- **Start state:** `docs/ROADMAP.md` has the headings `## Phase 0: hackathon POC (2 days, done at the demo)`, `## Phase 1: pilot (weeks 1–6), one portfolio company, one programme`, `## Phase 2: production hardening (weeks 7–10)`, `## Phase 3: scale and reuse (weeks 11–13)`, `## Team (proposed)`, `## What we need from the client` and `## Top 3 risks`. *Check:* `grep -c "^## " docs/ROADMAP.md` prints `7`. If it doesn't, someone changed the file: read it again and adapt the insert points, recording each change in the ledger.
- **Rules:** synthetic data only (no real company, system or person names; the problem owner and oversight are named only in `HANDOFF.md` Contacts, not here); no secrets; no claims the repo or demo can't show (rule of evidence); no new targets or dates (Patrick's call); no `Co-Authored-By` or "Generated with" lines; never push to `develop` or `main`. `docs/` is Patrick's folder: he reviews the PR.
- **Abdul does not write Python and never runs `uv`, `pytest` or a terminal.** His steps are in the GitHub web interface.

## Review Focus (check by hand at the end)
1. **Every go/no-go line is measurable** by someone outside the team (a percentage, a count, a yes/no event).
2. **Phases match `ARCHITECTURE.md` §6** row by row (the table in Task 2).
3. **Each top-3 risk has a mitigation and a "Stop if".**
4. **Client dependencies match the business case** (`business/business-case.md`): nothing the business case asks for is missing here.
5. **No claim beyond the evidence.** Every "Phase 0" statement is visible in the demo, the repo or `EVALS.md`.

---

### Task 1: The four additions (Linus)

**Files:**
- Modify: `docs/ROADMAP.md`

- [ ] **Step 1: Branch and check the start state**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
git switch -c docs/roadmap-draft
grep -c "^## " docs/ROADMAP.md
mkdir -p .superpowers && printf '# Ledger: L7 roadmap draft\n' > .superpowers/ledger-L7.md
```
Expected: `7`.

- [ ] **Step 2: Intro pointers.** In the opening quote line, replace `Targets marked *proposed* are ours until confirmed with the problem owner.` with:
```markdown
Targets marked *proposed* are ours until confirmed with the problem owner. Each target component's phase is in `ARCHITECTURE.md` §6; the monthly cost at pilot and full scale is in `COST.md`.
```
- [ ] **Step 3: Evidence under Phase 0.** Directly after the line ``- What's faked is listed in `HANDOFF.md`.``, add:
```markdown
- **Evidence, not claims:** the eval results with their failures (`EVALS.md`, Results), what's real and what's faked (`HANDOFF.md`), and the live demo (`DEMO.md`).
```
- [ ] **Step 4: The two new sections.** Directly **above** the heading `## Team (proposed)`, add (with one blank line before `## Team (proposed)`):
```markdown
## Monitoring, evaluation and model updates (proposed)
- **Monitoring:** per-route latency and error rates (API Gateway ends synchronous calls at 29 s), cost and tokens per run from the run ledger, the weekly rate of claims the critic rejects, and Guardrail interventions. Alarms: daily model spend above the `COST.md` pilot estimate, a jump in rejected claims, any 5xx burst.
- **Evaluation:** the eval set in `evals/` (14 questions today, about 40 by week 6, written with the delivery lead) runs on every prompt, model or agent change, in CI from Phase 2; a score below the Phase 1 bar blocks the release. The rejected-records queue is triaged weekly and every real miss becomes a new eval question.
- **Model and prompt updates:** model IDs are settings (`config.py`, EU inference profiles only), so a model change is a configuration change that must pass the eval run first. Prompts are versioned, locked files (`agents/prompts/`, D-014): an edit bumps the version, and every eval result records the prompt versions it ran with.
- **Who runs it:** the delivery team until week 10, then the client's IT team from the runbook handed over in Phase 2.

## The first week after a yes
1. The sponsor names the client's delivery lead as product owner.
2. We send the data-access and identity-federation requests (items 2 and 3 under "What we need from the client").
3. The pilot starts on synthetic data the same day, so no week is lost waiting for access (`HANDOFF.md`, week one).
```
- [ ] **Step 5: Doc guards and commit**
```bash
grep -c "^## " docs/ROADMAP.md
uv run --locked pytest tests/test_dependencies.py tests/test_code_style.py --no-cov 2>&1 | tail -1
git diff --stat
git add docs/ROADMAP.md
git commit -m "ROADMAP draft: monitoring, evaluation and model-update plan; week one; evidence for Phase 0"
```
Expected: `9`; `15 passed`; `docs/ROADMAP.md | 14 +++++++++++++-` (13 insertions, 1 deletion).

**Task done when:** `grep -n "^## Monitoring, evaluation and model updates (proposed)" docs/ROADMAP.md` and `grep -n "^## The first week after a yes" docs/ROADMAP.md` each print one line; the commit is on the branch.

### Task 2: Consistency check and Abdul's review

**Files:**
- Modify: `docs/ROADMAP.md` only if a check fails (each fix is one commit, message `ROADMAP: <what was inconsistent>`).

- [ ] **Step 1 (Linus): the phase table.** Fill in this table in the ledger from `ARCHITECTURE.md` §6 and `docs/ROADMAP.md`:

| `ARCHITECTURE.md` §6 component | §6 phase | Where `docs/ROADMAP.md` puts it | Match? |
|---|---|---|---|
| Identity: federation, Verified Permissions | 1 | Phase 1, "Real users" | |
| Data: connectors, EventBridge, Glue + Athena | 1 | Phase 1, "Real data in" | |
| Data-layer scope: Lake Formation row filters | 2 | Phase 2, first bullet | |
| Tenants: onboarding a new tenant | 3 | Phase 3, first bullet | |
| Agents and flow: evals in CI | 2 | Phase 2, third bullet | |
| Audit and monitoring: CloudTrail, dashboards, alarms | 2 | Phase 2, second bullet | |
| External data: vendor dates, client calendars, AWS Transform estimate | 3 | Phase 3, second bullet | |

Expected: seven `yes`. A `no` is a one-line fix in `docs/ROADMAP.md` (never in `ARCHITECTURE.md`, which is Patrick's), committed and noted in the PR.

- [ ] **Step 2 (Linus): push for review only.** With Linus's OK: `git push -u origin docs/roadmap-draft`, then open a **draft** PR to `develop` titled "ROADMAP draft for Patrick's final pass (L7)", with this body (no attribution lines):
```markdown
Draft of docs/ROADMAP.md for Patrick's final pass (L7, Linus + Abdul).

Added: pointers to ARCHITECTURE §6 and COST.md; "Evidence, not claims" under Phase 0; "Monitoring, evaluation and model updates (proposed)"; "The first week after a yes".
Checked: every phase matches ARCHITECTURE §6 (7 of 7); doc guards pass.

Abdul's review checklist: see the first comment.
Questions for Patrick: (list any line the review couldn't settle)
```
Expected: the PR page shows "Draft" and one changed file, `docs/ROADMAP.md`.

- [ ] **Step 3 (Abdul, GitHub web, no Python): review.** Open the PR → **Files changed**. Then post one PR comment with this checklist, ticking each line (`[x]`) or writing why not:
```markdown
- [ ] Every go/no-go line (weeks 6, 10, 13) has a number or a yes/no test someone outside the team could check.
- [ ] Every top-3 risk has an Effect, a Mitigation and a "Stop if".
- [ ] "What we need from the client" lists everything business/business-case.md asks the client for.
- [ ] Every Phase 0 bullet is visible in the demo, the repo or EVALS.md (no claim without evidence).
- [ ] The new monitoring section names what is watched, what alarms, how evals gate changes, and who runs it.
- [ ] "The first week after a yes" has three concrete actions, and none needs something we haven't asked the client for.
- [ ] No real company, system or person names anywhere in the file.
- [ ] Wording is plain: no sentence over about 30 words, no unexplained acronym (Glue, Athena and Lake Formation are explained in ARCHITECTURE.md).
```
  For a wording change, use **Add a suggestion** on the line (the ± icon in the comment box) so Linus can apply it with one click.
  Expected: the comment shows eight lines, each `[x]` or with a note.

- [ ] **Step 4 (Linus): apply the review.** For each suggestion: **Commit suggestion** in GitHub, or answer why not. Then pull and re-run the guards:
```bash
git pull && uv run --locked pytest tests/test_dependencies.py tests/test_code_style.py --no-cov 2>&1 | tail -1
```
Expected: `15 passed`.

**Task done when:** the phase table in the ledger has seven `yes`; Abdul's checklist comment is on the PR with eight lines settled; the guards still print `15 passed`.

### Task 3: Hand over to Patrick
- [ ] **Step 1:** Mark the PR **Ready for review** and request Patrick. In a comment, list any open question from Abdul's checklist.
- [ ] **Step 2:** Set L7's row in [[Build order]] to `in review (PR #nn)` (then `merged` when Patrick merges).
- [ ] **Step 3:** Tell Patrick and Michael (business case and pitch, B3) the PR link: the cost and 90-day-plan slide reuses these sections.

**Task done when:** the PR is "Ready for review" with Patrick requested, and the [[Build order]] row says `in review (PR #nn)`.

## Done means (checklist)
- [ ] `docs/ROADMAP.md` on the branch has 9 `## ` headings, including `## Monitoring, evaluation and model updates (proposed)` and `## The first week after a yes`. *Verify:* `grep -n "^## " docs/ROADMAP.md`.
- [ ] Phase 0 has the "Evidence, not claims" line, and the intro points at `ARCHITECTURE.md` §6 and `COST.md`. *Verify:* `grep -c "Evidence, not claims" docs/ROADMAP.md` and `grep -c "the monthly cost at pilot and full scale is in" docs/ROADMAP.md` each print `1`.
- [ ] The doc guards pass. *Verify:* `uv run --locked pytest tests/test_dependencies.py tests/test_code_style.py --no-cov` prints `15 passed`.
- [ ] Abdul's eight-line checklist is posted on the PR, every line ticked or answered. *Verify:* open the PR's conversation tab.
- [ ] The PR is ready for review with Patrick requested (or merged) before D2 14:00, without attribution lines. *Verify:* `gh pr view <nn> --json isDraft,reviewRequests,state`.
- [ ] [[Build order]] row L7 updated. *Verify:* open the note.

## Never
- Rewrite sections the rubric already covers, or change a phase, date or target (Patrick's call).
- Add a claim the repo, `EVALS.md` or the demo can't show.
- Put a real company, system or person name in the roadmap.
- Ask Abdul to run Python, `uv`, `pytest` or a terminal.
- Push to `develop` or `main`, or add attribution lines.

Related: [[L7 - Roadmap draft - spec]], [[Roadmap]], [[Abdul - evals, Cognito, docs]], [[Build order]], [[How to execute a plan]]
