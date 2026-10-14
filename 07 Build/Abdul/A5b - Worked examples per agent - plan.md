---
tags: [build, plan, area/evals]
id: A5b
owner: Abdul
spec: "[[A5b - Worked examples per agent - spec]]"
status: ready
updated: 2026-10-14
---
# A5b: worked examples per agent (implementation plan)

> **For the executing agent (and Abdul):** follow [[How to execute a plan]] exactly, with one change: **Abdul does not run Python, uv or pytest.** Linus runs Q01 and prints each agent's input and output; you paste them unchanged and compare every check with `Expected:`. If anything differs from `Expected:`, stop and follow "When output doesn't match".

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[A5b - Worked examples per agent - spec]]: **the authority** (§3 file shape). Where this plan and the spec disagree, the spec wins; record the conflict in your ledger.
3. Repo `AGENTS.md` (the agent table) and [[C1 - API and spine contracts - spec]] §4.

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If it's still unclear, stop and ask Linus.

**Goal:** five files `evals/expected/<agent>.json` on `develop`, each with one real input and output from the same Q01 run.

**Architecture:** one Q01 run (Linus) → each agent's input and output as JSON → your files → `AGENTS.md` link (Patrick's OK).

**Tech stack:** VS Code, Git, GitHub.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: `docs/worked-examples` from an up-to-date `develop`.
- **Start state:** all five agents merged (P1, P2, L5, H3, and the critic) and H6 merged; `evals/expected/` holds only `Q01.json`…`Q14.json`; `agents/prompts/` holds five `.txt` files and `prompts.lock`. Linus's `uv run --locked pytest` on `develop`: your baseline count (≥ `204 passed`, ≥ 96%). If an agent isn't merged by D2 13:30, capture the others and write the missing one into `EVALS.md` "What still fails" via A5a ("no worked example for <agent>: not merged").
- **Your ledger:** `.superpowers/ledger-A5b.md` (gitignored).
- **Rules:** real outputs only, pasted unchanged (never "Format Document" on the pasted parts); all five from one `run_id`; no token or password (check `eyJ`); stay in `evals/expected/` (the `AGENTS.md` line only with Patrick's OK); commits with the given messages; **no `Co-Authored-By` and no "Generated with" lines**; never push to `develop` or `main`; PR to `develop`; Linus reviews; Patrick merges.

## Review Focus (what nothing tests; check by hand at the end)
1. The five `source.run_id` values are identical.
2. Nothing in `input` or `output` was typed by you (compare one long value, for example a row's `fields`, with Linus's printout character by character).
3. The critic example shows `"pass"` (not `"passed"`) in its output (the alias; C1 Review Focus 3).
4. Each `prompt.version` equals `prompts.lock` at `source.commit`.
5. The runner still finds exactly 14 cases (Linus's runner output still lists Q01–Q14 only).

---

### Task 1: Capture the run (D2 12:30–13:30)

**Files:** none yet.

- [ ] **Step 1: Ask Linus.** *"For the worked examples: please run Q01 once (as the CFO, E4) with all five real agents, and send me, for each agent (orchestrator, retriever, blocker_analyst, critic, writer), its first call's input and output as JSON (`model_dump(mode="json", by_alias=True)`), the model_id, the prompt provenance `{agent, version, sha256}`, plus the run_id, the commit and the UTC time."*
Expected: five pairs of JSON blocks, one `run_id`, one commit hash, one time. The orchestrator's input has `"question": "What is blocking cutover for E4?"` and `"entity_id": "E4"`.

- [ ] **Step 2: Sanity-check what you got.**
Expected:
  - orchestrator: input has `run_id`, `scope`, `entity_id`, `question`, `budget_usd`, `max_attempts`; output has `plan` (with `steps`), `claims`, `partial`, `usage`.
  - retriever: input has `scope`, `entity_id`, `lead` (`kind`, `id`); output has `rows` (each `artefact`, `row_id`, `fields`) and `usage`.
  - blocker_analyst: input has `scope`, `entity_id`, `evidence`; output has `claims` (each `claim_id`, `statement`, `chain`, …) and `usage`.
  - critic: input has `claim` and `evidence_rows`; output has `claim_id`, `pass`, `reason`, `missing_evidence`, `prompt`.
  - writer: input has `scope`, `question`, `passed_claims`, `metrics_snapshot`; output has `answer` (`headline`, `bullets`, `rejected_count`) and `usage`.
  - Ctrl+F `eyJ` and `password` in what he sent: no results.
  Anything missing: ask Linus for it; don't fill it in.

**Task done when:**
- you have five complete input/output pairs from one `run_id`, with commit, time, model IDs and prompt provenance, and no `eyJ`/`password`.

### Task 2: Write the five files (D2 13:30–13:50)

**Files:** Create `evals/expected/orchestrator.json` *(new)*, `evals/expected/retriever.json` *(new)*, `evals/expected/blocker_analyst.json` *(new)*, `evals/expected/critic.json` *(new)*, `evals/expected/writer.json` *(new)* (all five created by this item).

- [ ] **Step 1: Branch and ledger.**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
git switch -c docs/worked-examples
mkdir -p .superpowers && printf '# Ledger: A5b worked examples\n' > .superpowers/ledger-A5b.md
```
Expected: `Switched to a new branch 'docs/worked-examples'`.

- [ ] **Step 2: Create each file.** In VS Code, New File in `evals/expected/`, named exactly as above. Paste the spec §3 wrapper; fill `agent`, `source` (`eval_question` `Q01`, the run_id, commit, time, and `captured_by` with the tool Linus used), `prompt`, `model_id`; replace `<the agent's input JSON…>` with the input block and `<the agent's output JSON…>` with the output block, pasted as he sent them.
Expected: five files; the Problems panel (Ctrl+Shift+M) shows **0 problems**; Ctrl+F `<` in each finds nothing.

- [ ] **Step 3: Cross-check.** For each file: `source.run_id` equals the others; open `agents/prompts/prompts.lock` on GitHub at the commit (github.com/Amali-Tech/cloud-9-hackathon/blob/<commit>/agents/prompts/prompts.lock) and compare `version` and `sha256`; compare `model_id` with `config.py` (`eu.anthropic.claude-sonnet-4-6` for four agents, `eu.amazon.nova-lite-v1:0` for the retriever unless Linus says the run overrode it).
Expected: all equal. Ledger: `<agent>: run_id ok, prompt <version> ok, model ok`.

- [ ] **Step 4: Commit and push.**
```bash
git add evals/expected/orchestrator.json evals/expected/retriever.json evals/expected/blocker_analyst.json evals/expected/critic.json evals/expected/writer.json
git commit -m "Worked examples: one real input and output per agent from one Q01 run"
git push -u origin docs/worked-examples
```
Expected: `5 files changed`, all `create mode`.

- [ ] **Step 5: Ask Linus** to run on the branch `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"` and `uv run python -m evals.run`.
Expected: the baseline count, no `failed`; the runner lists Q01–Q14 (14 lines, nothing for the agent files) and ends with the same summary as on `develop` (dry-run with a `critic.json` on the C1 branch: `204 passed`, `11 not run · 1 manual · 2 not applicable`).

**Task done when:**
- the five files are pushed, valid, from one run, with matching provenance;
- Linus's outputs show 0 failed and the runner unchanged.

### Task 3: PR and the `AGENTS.md` line (D2, by 14:00)

**Files:** Modify `AGENTS.md` (one line, only with Patrick's OK).

- [ ] **Step 1: PR.** Base `develop`, title `Worked examples per agent from one Q01 run (A5b)`, body: the run_id, commit, the five files, Linus's outputs, and "@Patrick: OK to replace the AGENTS.md 'Worked examples' TODO line (A5b spec §4)?". Reviewers: Linus, Patrick.
Expected: the PR shows five new files in `evals/expected/`.

- [ ] **Step 2: Only with Patrick's OK:** replace the `AGENTS.md` line exactly as spec §4; commit `AGENTS: link the worked examples per agent`; push; ask Linus to re-run `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"`.
Expected: `1 file changed, 1 insertion(+), 1 deletion(-)`; the baseline count, no `failed`.

**Task done when:**
- the PR is open (then merged) with the five files and Linus's green outputs;
- the `AGENTS.md` line is updated, or Patrick said no.

## Never
- Hand-write, shorten, reformat or "fix" an agent's input or output.
- Mix calls from different runs.
- Commit anything containing `eyJ` or a password.
- Name a file `Q*.json` (the runner would read it as a question).
- Push to `develop` or `main`, or add attribution lines.

## Done means
- [ ] **Five files are on `develop`:** `evals/expected/orchestrator.json`, `retriever.json`, `blocker_analyst.json`, `critic.json`, `writer.json`. *Verify:* GitHub → `develop` → `evals/expected/`.
- [ ] **They come from one real run.** *Verify:* the five `source.run_id` values are identical, and `source.commit` exists in the repo history.
- [ ] **Provenance matches.** *Verify:* each `prompt.version`/`sha256` equals `agents/prompts/prompts.lock` at `source.commit`; each `model_id` equals the agent's `config.py` model.
- [ ] **Nothing broke.** *Verify:* the merged PR's body has Linus's `uv run --locked pytest` (0 failed) and `uv run python -m evals.run` (14 cases, unchanged summary) outputs.
- [ ] **`AGENTS.md` links them** (if Patrick agreed). *Verify:* `AGENTS.md` "Worked examples" on `develop` names the five files.

Related: [[A5b - Worked examples per agent - spec]], [[A5a - EVALS results write-up - plan]], [[Build order]], [[How to execute a plan]]
