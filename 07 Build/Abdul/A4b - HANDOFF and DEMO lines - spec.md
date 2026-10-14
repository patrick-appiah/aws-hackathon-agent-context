---
tags: [build, spec, area/docs]
id: A4b
owner: Abdul
status: awaiting review
updated: 2026-10-14
---
# A4b: the HANDOFF.md and DEMO.md lines for evals and cost (spec)
> **Split of A4.** [[A4a - Target architecture diagram v2 - spec]] (diagram), A4b (this note: the doc lines), [[A4c - Prompt wording review - spec]] (prompt review). A4b runs **last**, D2 15:00, because it quotes the numbers A5a (eval results) and A3b (measured cost) produce. The Cognito test-user section of `HANDOFF.md` is A2's. No Python.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before you start, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Abdul - evals, Cognito, docs]] §7 ("`HANDOFF.md`: the test users, what the evals cover, what fails. `DEMO.md`: the eval and cost lines").
3. [[A5a - EVALS results write-up - spec]] and [[A3b - COST measured figures - spec]]: where the numbers come from.
4. Repo `HANDOFF.md` and `DEMO.md` as they are on `develop` (other people add lines too: keep theirs).
5. `04 Reference/`: [[Pitch track grading rubric]] ("README, cost and handoff", 8 points: "HANDOFF.md: real / faked / breaks first. DEMO.md … present and useful"), [[Judging rubric]] (Q&A: "What does it cost per month at 10× the users?"). `05 Workflow/`: [[Deploy and demo checks]].

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/`, `03 Sessions/`, `Open follow-ups.md`. If it's still unclear, stop and ask Patrick (demo script) or Clement (rehearsal, F6). Never write a number that isn't in `EVALS.md` or `COST.md` on `develop`.

## 1. Intent
**What:**
1. `HANDOFF.md`: a new section **"Evals and cost"**: what the evals cover, the latest recorded run, the checks a person does, the measured cost.
2. `DEMO.md`: the value-slide row quotes the measured cost; two pre-flight items; a short **"Eval and cost answers (for Q&A)"** section.

**Why:** judges read `HANDOFF.md` for "what does week three look like" and `DEMO.md` for whether the demo is rehearsed. The two numbers people quote on stage (eval pass rate, cost per question) must equal the documents.

**Success means:**
- Both files on `develop` contain the §3 text with every `<…>` filled from `EVALS.md` (latest Results row) and `COST.md` ("Measured on" line).
- Every number in the new lines appears, identically, in `EVALS.md` or `COST.md`.
- Other people's lines in both files are unchanged.

**Assumptions:**
- **A4b-1:** A5a has merged the latest Results row and "What still fails"; A3b has merged the "Measured on" line. If either isn't merged by D2 15:00, the matching lines say "not yet recorded" instead of a number (never an estimate).
- **A4b-2:** the eval command for the local asker is `uv run python -m evals.run --asker flow.local:ask` (`EVALS.md`, H6).

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Where in `HANDOFF.md` | A new `## Evals and cost` section after "Test users (Cognito)" (A2) and before "What breaks first"; if A2's section isn't there, after "What's faked / stubbed" | Mixing into "What's real" (other owners edit that list) |
| Where in `DEMO.md` | Edit the `2:35–3:00` row's "cost per question" words; append two pre-flight items; add a section at the end | Rewriting the script (Patrick's and Clement's) |
| Which numbers | Only the latest **recorded** run (A5a's last Results row) and A3b's "Measured on" figures | A better earlier run |
| Which cost per question | The `COST.md` "Measured on" **average** everywhere (the team's one rule: the business case line 34, deck slide 9, the pitch script and these lines all quote it) | The "Per question" table's Total row: it is labelled "Q01 worked example" and is one question, not the average |
| Pass rate wording | "`<pass>` of `<pass + fail>` scored questions pass" (manual and not-applicable cases aren't scored) | A percentage of 14 |

## 3. The exact text
**`HANDOFF.md`**, new section:
```markdown
## Evals and cost
- **What the evals cover:** 14 fixed questions (`EVALS.md`, files in `evals/inputs/` and `evals/expected/`): the E4 blocker chain (Q01), the closed-defect decoy (Q02), a clean entity (Q03), the year-end close clash (Q04), capacity (Q05), cutover figures (Q06), an unknown entity (Q07), an uncited claim (Q08), the retry limit (Q09), an unseen question chosen on the day (Q10), scope enforcement (Q11) and prompt injection (Q12). Q13 (cross-tenant) and Q14 (CSV vs Athena parity) are roadmap. Run them with `uv run python -m evals.run --asker flow.local:ask`.
- **Latest recorded run** (<run date>, commit `<commit>`): <pass> of <pass + fail> scored questions pass; <fail> fail (<failing question IDs>); Q10 <honest / not honest>. Details and causes: `EVALS.md` "What still fails".
- **Read by a person every run:** Q02 (the conflict is flagged, not just "ready" avoided), Q03 (no invented blocker or defect for E1), Q09 (the number of verdicts on the rejected claim), Q11 (no E2 rows in the ledger).
- **Cost:** $<average> per question on average, measured on that run; about $<pilot> a month at pilot volume (200 questions) and $<full> a month at 100 questions a day (`COST.md`). The dashboard makes no model calls.
```
**`DEMO.md`**:
- In the `| 2:35–3:00 |` row, replace `cost per question` with `$<average> per question, measured (COST.md)`.
- Under "## Pre-flight checklist", append:
```markdown
- [ ] Latest eval run is in `EVALS.md` (<pass> of <pass + fail> pass); the presenter can name the failing questions and why
- [ ] The value slide's cost equals `COST.md`'s "Measured on" average ($<average> per question, not the Q01 worked-example Total row; $<pilot>/month pilot)
```
- At the end of the file, add:
```markdown
## Eval and cost answers (for Q&A)
- *"How do you know it works?"* "<pass> of <pass + fail> scored eval questions pass on the recorded run of <run date>. <fail> fail, and `EVALS.md` says why. Q10 was a question none of us had seen; it <degraded honestly / did not degrade honestly: <one-line reason>>."
- *"What does it cost?"* "$<average> per question, measured, not estimated. About $<pilot> a month for a pilot at 200 questions, $<full> at 100 questions a day. The dashboard itself costs no tokens."
- *"At 10× the users?"* "Cost scales with questions, not users: 10× the pilot's questions (2,000 a month) is about $<10 × pilot> a month at today's prices (`COST.md` cost levers: a cheaper retriever model, answer caching)."
```
(Dry-run: both blocks with sample numbers on the C1 branch → `204 passed`, 96%; the one command they name, `uv run python -m evals.run`, passes the doc guard.)

## 4. Tests
No code. The checks:
- **Same numbers:** every number in the new lines is found (Ctrl+F) in `EVALS.md`'s last Results row or `COST.md`'s "Measured on" line / Scale table.
- **Nothing else changed:** the PR diff shows only added lines plus the one `2:35–3:00` row edit.
- **Doc guards:** Linus runs `uv run --locked pytest` → the baseline count, 0 failed.

## 5. Out of scope
- `HANDOFF.md` "What's real", "What breaks first", "Week one / two / three" (each owner's lines), the Cognito section (A2).
- `DEMO.md`'s script except the one row edit; the rehearsal and video (F6).

Related: [[Build order]], [[Abdul - evals, Cognito, docs]], [[A4b - HANDOFF and DEMO lines - plan]]
