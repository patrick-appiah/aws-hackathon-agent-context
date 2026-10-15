---
tags: [build, spec, area/agents, area/cost]
id: P7
owner: Patrick
status: ready
updated: 2026-10-15
---
# P7: the analyst gets a few sample load errors, not fifty (spec)
> **The analyst's single call over all the evidence is the biggest piece of an answer's time** (about 38–44 s of RunOrchestrator on the deployed spine). For an object lead the retriever hands it up to 50 load-error rows (`MAX_ROWS_PER_TOOL_RESULT`), while the prompt lets a claim cite at most 3 and the reconciliation row already carries how many records failed. P7 keeps a few samples in code. Repo: `Amali-Tech/cloud-9-hackathon`, branch `perf/retriever-load-error-samples` from `develop` (729 tests or more). Before the 14:00 code freeze.

## 0. Context: read the vault first
Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`. Read: [[How to execute a plan]]; [[P4 - Fixed-lookup retriever - spec]] (the lookup table, D-028); [[2026-10-15]] ("UI answer time": where the 60–140 s go); the repo's `agents/retriever.py` and `agents/prompts/blocker_analyst.txt` (v1.3.0: at most 3 load-error rows per claim). If unclear, look in the vault, then ask Patrick.

## 1. Intent
**What:** in `agents/retriever.py`'s object lookup, keep at most **`LOAD_ERROR_SAMPLE_ROWS = 5`** (`tools/constants.py`) load-error rows in the evidence. Two things don't change:
- the distinct `field` values for `mapping_for_field` are still read from **all** the load-error rows the tool returned, so every failing field still gets its mapping rule;
- the other tools' rows (reconciliations, defects, mappings, runbook, calendar) are untouched.

**Why:** fewer input tokens for the analyst's one big call: faster and cheaper, with no claim losing evidence (it cites at most 3; the count of failed records is on the reconciliation row).

**Not this (considered and rejected, P8):** fetching the entity's rows in code before the orchestrator plans would save about 5–8 s, but it removes the orchestrator's first decision; "why it is agentic" and "orchestrator plans and routes" are scored (pitch 5, repo 10), and the guideline asks for "a decision about what to do next". Recorded in `DECISIONS.md` (D-033); a roadmap optimisation if ever.

**Success means:**
- For E4's `object:customers` lead, the evidence has at most 5 `load_errors` rows, and still the `field_mappings` row for `tax_id` (`E4#CUSMST#TAXNO`), `RC-C3-E4-customers` and `DEF-0412`.
- `uv run --locked pytest` green, coverage ≥ 98%.
- **Live (Patrick's OK, about $0.30):** Q01 still passes; RunOrchestrator's time drops (compare with run 5's 1 min 29 s and the eval run's 63 s).

## 2. Out of scope
Parallel judging (Michael, FlowStack); the warm-up (Clement); the orchestrator (P8, rejected).

Related: [[Build order]], [[P7 - Fewer load-error rows for the analyst - plan]]
