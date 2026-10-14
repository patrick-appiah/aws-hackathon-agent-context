---
tags: [build, spec, area/evals]
id: A5a
owner: Abdul
status: awaiting review
updated: 2026-10-14
---
# A5a: EVALS.md results rows and "What still fails" (spec)
> **Split of A5.** A5a (this note): one `EVALS.md` Results row per recorded run, an honest "What still fails", and the results file committed. [[A5b - Worked examples per agent - spec]]: one real input and output per agent in `evals/expected/<agent>.json`. Both with Linus; both need H6 (the local asker). No Python.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before you start, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Abdul - evals, Cognito, docs]] §2 and §7 ("Write failures honestly: a perfect `EVALS.md` is treated as a missing one").
3. [[A1 - Eval set review and manual checks - spec]] §4 (the four manual checks whose lines go into each row).
4. [[Linus - API, identity, blocker-analyst]] §6 (he runs the evals and hands you the file) and [[Huvison - trust and flow]] §7 (H6, the Q09 count).
5. [[Build order]]: A5 depends on H6; L6 adds the deployed-API run.
6. `04 Reference/`: [[Hackathon guideline]] ("Record eval scores as they are, failures included"), [[Pitch track grading rubric]] ("Honest evals", 6 points; hard gate 2 "eval set runs and results written down, including failures"), [[Judging rubric]] 2.2.

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/`, `03 Sessions/`, `Open follow-ups.md`. If it's still unclear, stop and ask Linus (the run) or the failing agent's owner (the cause). Never round a failure into a pass.

## 1. Intent
**What**, for every run Linus marks as **recorded** (at least: the first run with an asker on D2, and the final run before 15:00; plus the deployed-API run if L6 lands):
1. Commit the results file `evals/results/run-<date>-<time>.json` unchanged (the folder `evals/results/` *(new)* is created by the eval runner's first committed run, this item's first PR) (`EVALS.md`: "Commit the results file of every run you record below").
2. Add one row to `EVALS.md` "## Results" (§3).
3. Rewrite "## What still fails" for the latest run (§4).
4. Update the deterministic-layer heading's test count and coverage to Linus's latest `uv run --locked pytest` output.

**Why:** it's a hard gate (results written down, failures included) and 6 rubric points. Judges look at "What still fails" first.

**Success means:**
- Each recorded run has a file in `evals/results/` on `develop` and a Results row whose Pass and Fail equal the file's `summary`.
- "What still fails" names every failing question of the latest run with its first failing check and a cause from the owner, plus the manual checks and the blunt-phrase caveat.
- No row hides a failure: `summary.fail` in the file = the Fail column.

**Assumptions (to reconcile with the owners):**
- **A5a-1:** the results file format is `evals/run.py` `run_all`: top-level `run_at`, `commit`, `asker`, `prompt_versions` (`{agent: version}`), `summary` (`{status: count}`, only statuses that occur, e.g. `{"pass": 8, "fail": 3, "manual": 1, "not applicable": 2}`), `cases[]` with `id`, `question`, `status`, `detail` (the failing checks joined by `; `), `checks[]` (`name`, `passed`, `detail`, `warning`), `answer`, `seconds`, `cost_usd`, `manual_check`.
- **A5a-2:** Linus sends the file itself (it holds synthetic data only: questions, answers, row IDs, costs). For a deployed run, he confirms it contains no token (A5a checks: no `eyJ`).
- **A5a-3:** the cause of each failure comes from the failing agent's owner (via Linus): Patrick (orchestrator, retriever), Linus (blocker-analyst, API), Huvison (critic, writer, flow).

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Which runs get a row | Every run Linus marks recorded; never a cherry-picked best run only | Only the final run |
| Pass / Fail columns | Exactly `summary.pass` and `summary.fail` (missing key = 0) | Counting manual or not-applicable as pass |
| "Prompt versions" column | Every entry of `prompt_versions`, as `agent version` joined by `, ` (for example `critic 1.0.1, writer 1.0.0`) | Only the changed ones |
| Commit column | `` `<commit>` `` from the file (short hash), plus ` (deployed)` for an L6 run | The branch name (the first row used one; from now on the hash) |
| Warnings (`should_cite` misses) | Listed in Notes as "Warnings:", never counted as failures (the runner doesn't) | Hiding them |
| The first row (no agent loop) | Kept as it is: it's history | Deleting it |
| "No question can be answered yet" bullet | Removed once a run with an asker is recorded (it's no longer true) | Keeping a stale claim |
| Heading count | `(<N> tests, <C>% coverage, passing)` from Linus's latest output on `develop` | Leaving 160 / 95% (stale after C1: 204 / 96%) |

## 3. The Results row (exact template)
```markdown
| <run_at as YYYY-MM-DD> | `<commit>`<" (deployed)" if L6> | <agent version, …> | <summary.pass or 0> | <summary.fail or 0> | Asker `<asker>`. <not run> not run · <manual> manual · <not applicable> not applicable. Failed: <Qxx> (<first failing check>), …<or "none">. Warnings: <Qxx: should cite <row>>, …<or "none">. <A1's four lines: "Q02 manual: …", "Q03 manual: …", "Q09 manual: …", "Q11 manual: …">. File: `evals/results/<file name>`. |
```
"First failing check" = the case's `detail` up to the first `; `.

## 4. "What still fails" (structure, latest run)
```markdown
## What still fails
*(Kept honest: judges look here first.)* Latest recorded run: `evals/results/<file name>` (<date>, commit `<commit>`): <pass> pass, <fail> fail.
- **<Qxx> fails: <first failing check>.** <cause, one sentence, from the owner>. Owner: <name>. <"Fix in progress (PR #nn)" / "Not fixed before the freeze">.
- … (one bullet per failing question)
- **Four checks are still by hand.** Q02 (the answer must *flag* the conflict, not just avoid "ready"), Q03 (no invented blocker or defect for E1), Q09 (the rejected claim has <Huvison's number> verdicts) and Q11 (no E2 rows in the ledger) need a person; this run: Q02 <pass/fail>, Q03 <pass/fail>, Q09 <pass/fail>, Q11 <pass/fail>.
- **Phrase checks are blunt.** "Must not say *is ready for cutover*" can't catch every way of wrongly saying the customer master is fine, and `\b6\b` in Q06 matches any 6. Read Q02's and Q06's answers every run.
- <if any `not run` cases remain: "**<Qxx> not answered by the agent loop yet:** <why>.">
```
If the run has **zero** failures, the first bullet is: `- **No automatic check failed on this run.** That doesn't mean nothing fails: <the manual checks' result>; Q10 <honest/not honest>; <the blunt-check caveat>.` (A perfect page is read as a missing one.)

(Dry-run: a sample row and this section, plus a results file in `evals/results/`, on the C1 branch → `204 passed`, 96%; the runner still pairs only `Q*.json`.)

## 5. Tests
No code. The checks:
- **Counts:** the row's Pass/Fail equal the file's `summary`; the number of "fails" bullets equals `summary.fail`.
- **Trace:** every Qxx named as failing has `"status": "fail"` in the file.
- **No secret:** Ctrl+F `eyJ` in the results file → no results.
- **Doc guards:** Linus runs `uv run --locked pytest` on the branch → the baseline count, 0 failed.

## 6. Out of scope
- Running the evals (Linus), the askers (H6, L6), fixing failures (the owners).
- The manual checks themselves (A1 Task 6; this item pastes their lines).
- Worked examples ([[A5b - Worked examples per agent - spec]]), `COST.md` ([[A3b - COST measured figures - spec]]).

Related: [[Build order]], [[Abdul - evals, Cognito, docs]], [[A5a - EVALS results write-up - plan]]
