---
tags: [build, spec, area/evals]
id: A5b
owner: Abdul
status: awaiting review
updated: 2026-10-14
---
# A5b: worked examples per agent (spec)
> **Split of A5.** [[A5a - EVALS results write-up - spec]] writes the results; A5b (this note) commits **one real input and its real output per agent** in `evals/expected/<agent>.json` *(new)*, captured with Linus from a real run on D2 (by 14:00). Never hand-written. No Python.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before you start, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Abdul - evals, Cognito, docs]] §3 ("Worked examples per agent … Real outputs only, never hand-written").
3. [[Workstreams]] §4 (the contracts table: "worked examples per agent in `evals/expected/<agent>.json`") and repo `AGENTS.md` (the agent table; its "Worked examples" section says they're committed in `evals/expected/`).
4. [[Linus - API, identity, blocker-analyst]] §8 ("help him capture the worked examples … from real runs"), [[Patrick - contracts, orchestrator, retriever]] (P1, P2, P3 `scripts/ask.py`), [[Huvison - trust and flow]] (H3 writer, H6 local asker).
5. [[C1 - API and spine contracts - spec]] §4 (the step models each agent takes and returns).
6. `04 Reference/`: [[Pitch track grading rubric]] ("Worked examples and tests", 4 points: "a real input and real output committed **for each agent**"). `Open follow-ups.md`: "Commit one real input + output per agent in `evals/expected/`".
7. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/`, `03 Sessions/`, `Open follow-ups.md`. If it's still unclear, stop and ask Linus. Never type or "tidy" an agent's output.

## 1. Intent
**What:** five files, one per agent, each holding one real input and the real output of that agent from **one** real run of Q01 ("What is blocking cutover for E4?", as the CFO), plus where it came from:
| File *(new)* | Agent | Input (C1 / `AGENTS.md`) | Output |
|---|---|---|---|
| `evals/expected/orchestrator.json` *(new)* | orchestrator | `Question {run_id, scope, entity_id, question, budget_usd, max_attempts}` | `OrchestratorResult {plan, claims, partial, usage}` |
| `evals/expected/retriever.json` *(new)* | retriever | `RetrieveRequest {scope, entity_id, lead{kind, id}}` | `Evidence {rows[{artefact, row_id, fields}], usage}` |
| `evals/expected/blocker_analyst.json` *(new)* | blocker-analyst | `{scope, entity_id, evidence}` | `AnalystResult {claims[BlockerClaim], usage}` |
| `evals/expected/critic.json` *(new)* | critic | `{claim, evidence_rows[]}` | `Verdict {claim_id, pass, reason, missing_evidence, prompt}` |
| `evals/expected/writer.json` *(new)* | writer | `WriterInput {scope, question, passed_claims, metrics_snapshot}` | `WriterResult {answer{headline, bullets, rejected_count}, usage}` |

**Why:** 4 rubric points, and the clearest evidence that each agent really runs and does one job.

**Success means:**
- The five files are on `develop`, each valid JSON in the §3 shape, all from the same `run_id`.
- Each file's `prompt.version` equals that agent's version in `agents/prompts/prompts.lock` at the file's `commit`, and its `model_id` equals `config.py`'s model for that agent.
- `uv run --locked pytest` and `uv run python -m evals.run` still pass/run unchanged (the runner reads only `Q*.json`: verified by dry-run, a `critic.json` in `evals/expected/` → `204 passed`, runner unchanged `11 not run · 1 manual · 2 not applicable`).

**Assumptions (to reconcile with the owners):**
- **A5b-1:** Linus (with Patrick's `scripts/ask.py` *(new, P3)* or Huvison's `infra/functions/local.py` *(new, H6)*) can print each agent's input and output as JSON for one run, using the step models' `model_dump(mode="json", by_alias=True)` (so the critic's verdict shows `"pass"`). How he prints them is his choice; you receive JSON text.
- **A5b-2:** each agent's prompt provenance is available as `{agent, version, sha256}` (`agents/prompt_loader.py` `Prompt.provenance()`; `TraceStep.prompt` in C1's `AskResponse.trace`).
- **A5b-3:** the run is local (CSV data, synthetic) or deployed; either way it contains only synthetic data and no token.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Folder | `evals/expected/<agent>.json` (the brief, [[Workstreams]] §4). The runner only reads `Q*.json`, so these never become eval cases | A subfolder for the examples (the brief and the contracts table put them directly in `evals/expected/`, and the brief wins) |
| File names | `orchestrator`, `retriever`, `blocker_analyst`, `critic`, `writer` (the prompt file names) | `blocker-analyst` (doesn't match the prompt file) |
| Which run | One Q01 run, all five agents from the **same** `run_id` | Mixing runs |
| Which call when an agent ran several times | The **first** call of that agent in the run (the critic: the verdict on the first claim) | Choosing the "nicest" one |
| Editing | None: paste exactly; long `rows` stay long | Shortening, re-ordering or reformatting the agent's JSON |
| Where it's linked | `AGENTS.md`'s "Worked examples" TODO line (Patrick's file; change it only with his OK, text in §4) | |

## 3. The file shape (every file)
```json
{
  "agent": "<agent file name, e.g. critic>",
  "source": {
    "eval_question": "Q01",
    "run_id": "<run_id of the run>",
    "commit": "<short commit hash the run used>",
    "captured_at": "<UTC time, e.g. 2026-10-15T11:40:00+00:00>",
    "captured_by": "Linus printed it from <scripts/ask.py | infra.functions.local:ask>; Abdul recorded it unchanged"
  },
  "prompt": {"agent": "<agent>", "version": "<version>", "sha256": "<sha256>"},
  "model_id": "<the model ID the call used, e.g. eu.anthropic.claude-sonnet-4-6>",
  "input": <the agent's input JSON, pasted exactly>,
  "output": <the agent's output JSON, pasted exactly>
}
```
`input` and `output` are JSON objects, not strings. Two-space indent for the wrapper; the pasted parts as Linus sent them.

## 4. The `AGENTS.md` line (Patrick's file; only with his OK)
Replace `One real input → output per agent is committed in \`evals/expected/\`. *(TODO: add these as each agent lands.)*` with `One real input → output per agent, all from one Q01 run (\`run_id\` in each file): \`evals/expected/orchestrator.json\`, \`retriever.json\`, \`blocker_analyst.json\`, \`critic.json\`, \`writer.json\`.`

## 5. Tests
No code. The checks:
- **Valid JSON:** VS Code's Problems panel shows 0 problems for the five files.
- **One run:** the five `source.run_id` values are identical.
- **Provenance:** each `prompt.version` equals `agents/prompts/prompts.lock` at `source.commit` (GitHub → the commit → `agents/prompts/prompts.lock`); each `model_id` equals the agent's model in `config.py` (`DEFAULT_REASONING_MODEL` for orchestrator, blocker-analyst, critic, writer; `DEFAULT_RETRIEVAL_MODEL` for the retriever, unless overridden in that run's environment: Linus says).
- **Suite and runner:** Linus runs `uv run --locked pytest` (baseline count, 0 failed) and `uv run python -m evals.run` (the same 14 lines as before).
- **No secret:** Ctrl+F `eyJ` and `password` in each file → no results.

## 6. Out of scope
- Writing any printing code (Linus/Patrick/Huvison).
- More than one example per agent; examples for Q02–Q14.

Related: [[Build order]], [[Abdul - evals, Cognito, docs]], [[A5b - Worked examples per agent - plan]]
