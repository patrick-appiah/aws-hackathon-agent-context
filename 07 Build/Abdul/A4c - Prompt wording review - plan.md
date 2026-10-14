---
tags: [build, plan, area/agents]
id: A4c
owner: Abdul
spec: "[[A4c - Prompt wording review - spec]]"
status: ready
updated: 2026-10-14
---
# A4c: prompt wording review (implementation plan)

> **For the executing agent (and Abdul):** follow [[How to execute a plan]] exactly, with one change: **Abdul does not run Python, uv or pytest, and never edits a prompt file.** Work the tasks in order. If anything differs from `Expected:`, stop and follow "When output doesn't match".

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[A4c - Prompt wording review - spec]]: **the authority** (§3 checklist, §4 format). Where this plan and the spec disagree, the spec wins; record the conflict in your ledger.
3. [[Changing a prompt]] and repo `AGENTS.md`.

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If it's still unclear, ask the prompt's owner.

**Goal:** every agent prompt is read against the checklist, and every suggestion is answered by its owner, before the D2 14:00 freeze.

**Architecture:** `agents/prompts/<agent>.txt` (owners) → your review (issue comments) → the owner's PATCH bump and re-lock (owners).

**Tech stack:** VS Code (read-only use of the prompt files), GitHub (issue, PR comments).

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. **No branch, no commit**: this item changes no file.
- **Start state:** on `develop`, `agents/prompts/` holds `critic.txt` (header `version: 1.0.0`, `owner: seat 6`) and `prompts.lock`; the other four prompts arrive with P1, P2, L5, H3.
- **Your ledger:** `.superpowers/ledger-A4c.md` (gitignored).
- **Rules:** never edit, rename or save a file in `agents/prompts/` (close without saving if VS Code asks); never suggest changing the critic's pinned "is DATA … never an instruction" sentence; quote lines exactly; no real names in your suggestions either.

## Review Focus (what nothing tests; check by hand at the end)
1. Every suggestion quotes the exact line it's about.
2. No suggestion changes an output format (that's a MAJOR change: flag it as a question, not a suggestion).
3. Every prompt that sees rows has the "data, never an instruction" rule (checklist 4).
4. Every owner replied to every numbered suggestion.
5. `git log --oneline -- agents/prompts` shows no commit by you.

---

### Task 1: Open the issue and review `critic.txt` (D1)

**Files:** none changed.

- [ ] **Step 1: Ledger and read.**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
mkdir -p .superpowers && printf '# Ledger: A4c prompt review\n' > .superpowers/ledger-A4c.md
```
  Open `agents/prompts/critic.txt` and the critic row of `AGENTS.md` side by side.
Expected: the header shows `agent: critic`, `version: 1.0.0`, `owner: seat 6`, `updated: 2026-10-13`, `purpose`, `output_contract: Verdict`, `security_notes`; the body ends `Reply with JSON only: {"claim_id": str, "pass": bool, "reason": str, "missing_evidence": [str]}`.

- [ ] **Step 2: Go through the 10 checklist items** (spec §3) and note `ok` or the issue for each.
Expected: at least the known finding: item 1, `owner: seat 6` → suggest `owner: Huvison`. Item 3: the reply fields (`claim_id`, `pass`, `reason`, `missing_evidence`) equal `AGENTS.md`'s `Verdict {claim_id, pass, reason, missing_evidence[]}` → `ok`.

- [ ] **Step 3: Open the issue.** GitHub → `Amali-Tech/cloud-9-hackathon` → Issues → New issue. Title `Prompt wording review (A4c)`. Body: "Wording review of every agent prompt against the A4c checklist (vault `07 Build/Abdul/A4c - Prompt wording review - spec.md` §3). One comment per prompt. Owners: please answer each numbered suggestion (taken / not taken + why). I don't edit prompt files." Submit. Then add the first comment in the spec §4 format for `critic.txt`, mentioning @Huvison.
Expected: issue `#nn` with one comment for `critic.txt`. Ledger: `Task 1: complete (issue #nn, critic: <k> suggestions)`.

**Task done when:**
- issue `#nn` exists and has the `critic.txt` comment with all ten checklist results.

### Task 2: Review each new prompt as its PR opens (D1 afternoon – D2 13:00)

**Files:** none changed.

- [ ] **Step 1: Watch for the PRs.** On GitHub → Pull requests, look for PRs that add `agents/prompts/retriever.txt` *(new)* (created by Patrick's P1), `orchestrator.txt` (Patrick, P2), `blocker_analyst.txt` (Linus, L5), `writer.txt` (Huvison, H3). Check at each stand-up (13:00, 17:00, 09:00).
Expected: each PR's "Files changed" includes the `.txt` file and `agents/prompts/prompts.lock`.

- [ ] **Step 2: Review in the PR.** In "Files changed", read the prompt next to its `AGENTS.md` row; go through the 10 items. Add the spec §4 comment to issue `#nn` **and** a short PR comment: "Wording review in #nn (<k> suggestions)."
Expected: per prompt, one issue comment with ten checklist results; one PR comment linking it. Ledger line per prompt with its PR number.

- [ ] **Step 3: Track replies.** For each suggestion, note the owner's answer in the ledger.
Expected: every numbered suggestion has "taken" or "not taken: <reason>".

- [ ] **Step 4: Ledger:** `Task 2: complete (<n> prompts reviewed: <file> PR #<nn>, …; <k> suggestions, <a> answered)`.
Expected: the line is in `.superpowers/ledger-A4c.md`.

**Task done when:**
- every prompt PR opened before D2 13:00 has an issue comment and a PR comment from you;
- each suggestion's answer is in the ledger;
- the ledger has the `Task 2: complete (…)` line.

### Task 3: Last pass before the freeze (D2 13:00–13:45)

- [ ] **Step 1:** `git switch develop && git pull`, then list `agents/prompts/`.
Expected: the five `.txt` files (or fewer, if an agent isn't merged: note which) and `prompts.lock`.

- [ ] **Step 2:** for each prompt whose `version` changed since your review, re-check only the lines that changed (GitHub → the file → History).
Expected: taken suggestions appear; no new checklist issue (or a new comment for any you find).

- [ ] **Step 3:** check you changed nothing: `git log --oneline --author="<your git name>" -- agents/prompts`.
Expected: no output.

- [ ] **Step 4:** comment on issue `#nn`: "Final pass <time>: <n> prompts reviewed, <k> suggestions, <t> taken." Close the issue if every suggestion is answered.
Expected: the issue shows the final comment (and "Closed" if all answered).

- [ ] **Step 5: Ledger:** `Task 3: complete (final pass <time>: <n> prompts, <k> suggestions, <t> taken; issue #nn <open/closed>; no commits by me under agents/prompts)`.
Expected: the line is in `.superpowers/ledger-A4c.md`.

**Task done when:**
- the issue has a final-pass comment, and is closed if every suggestion is answered;
- `git log` shows no commit by you under `agents/prompts`;
- the ledger has the `Task 3: complete (…)` line.

## Never
- Edit, save, version or lock a prompt file.
- Suggest changing the critic's pinned "is DATA … never an instruction" sentence.
- Suggest an output-format change as a wording fix.

## Done means
- [ ] **Issue `Prompt wording review (A4c)` exists** with one comment per prompt file on `develop` at D2 13:00, each with ten checklist results. *Verify:* open the issue; count the comments against `agents/prompts/*.txt` on `develop`.
- [ ] **Every suggestion is answered** by its owner. *Verify:* each numbered suggestion in the issue has a reply (taken / not taken + why).
- [ ] **The `critic.txt` owner finding is answered.** *Verify:* `critic.txt` on `develop` shows `owner: Huvison` with a bumped version, or Huvison's reply says why not.
- [ ] **No prompt was edited by you.** *Verify:* `git log --oneline --author="<Abdul's git name>" -- agents/prompts` on `develop` prints nothing.

Related: [[A4c - Prompt wording review - spec]], [[Build order]], [[How to execute a plan]]
