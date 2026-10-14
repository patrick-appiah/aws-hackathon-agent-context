---
case: today
audited_sha: 2a745c7522ecaa31e872da4361f6039ef8124065
written: 2026-10-14
---
## Setup
`local.json` as normal (`use_gh: true`). Run `/audit-progress --at 2a745c7`. Live GitHub state postdates the sha: PR states below are today's, which is what the collector reports.

## Expected
- C1 (Patrick): `not started` or `in progress`, never `done`; evidence `tools/api_schema.py` absent at 2a745c7 (`git ls-tree` of that path is empty). The Build order says C1 is `merged` (PR #22, after the audited sha): the report notes that mismatch as a gap, not as proof of done. Urgency `overdue` (M0 D1 10:30 passed), provided the run happens after that time; a done row would show `—`.
- `EVALS.md`: the rubric's honest-evals item shows no answer-check results yet (the Results section says "No agent loop yet": 27 of 27 data checks pass, answer checks *not run*), with `EVALS.md@2a745c7` as evidence.
- `COST.md`: all TODO (`COST.md` has 7 TODO lines at 2a745c7; `greps.todo_in_docs` counts TODOs across all docs), cited from `greps.todo_in_docs` or `COST.md@2a745c7`; the rubric's README/cost/handoff item names it. A row whose source is unavailable is `not verified`, not guessed.
- PR #8 (Michael, M1 Jenkins CI): OPEN and draft per `gh` today, so CI is not green on PRs; the process section says so.
- `business/business-case.md`: `[TBC]`s remain (2 lines contain `[TBC]` at 2a745c7: line 3, the legend, and line 46, "Portal run cost per month"), owner Patrick and Michael (B1).
- Q09 verdict count: the fix isn't in the repo at 2a745c7 (`EVALS.md` line 56 and `evals/expected/Q09.json` at that sha still show the old count of 3 verdicts); D-022 (2 verdicts, at most 2 attempts in total) is decided in the vault's `Open follow-ups.md`; PR #21 (`fix/q09-attempt-limit`) is MERGED, after the audited sha. The report must not call the repo's Q09 line `done` at 2a745c7.
- Must not: call anything about AWS more than `not checked`; call a `spec + plan ready` item `done` or `in progress` without repo evidence; name a client person.
