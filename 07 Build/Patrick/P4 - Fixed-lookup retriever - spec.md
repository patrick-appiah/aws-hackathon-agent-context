---
tags: [build, spec, area/agents, area/cost]
id: P4
owner: Patrick
status: merged (PR #72)
updated: 2026-10-15
---
# P4: the retriever as a fixed lookup, no model (spec)
> **The retriever stops calling a model.** Its prompt is already a fixed table, lead kind → tools. P4 writes that table in code, so every `retrieve` is a few in-process tool calls: no Haiku agent loop, no model cost, the same rows for the same lead every time. The orchestrator still decides which leads to follow; that is where the judgement is. Repo: `Amali-Tech/cloud-9-hackathon`, branch `refactor/retriever-fixed-lookup` from `develop` (ad58454 or later). The repo is the source of truth for code; the vault is the source of context.

## 0. Context: read the vault first
The team vault is the shared context space for this project. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[P1 - Retriever agent - spec]]: what the retriever is today (scope narrowed to the entity, rows recorded from tool results, never from the reply).
3. [[P2 - Orchestrator agent - spec]] and `DECISIONS.md` D-027: the orchestrator's `retrieve` tool and its lead digest, which call this retriever.
4. [[Whole-code review 2026-10-14]], "Open decisions (Patrick)": where this change was proposed.
5. [[2026-10-15]] and [[2026-10-14]] (the three live E4 runs: 26 s, 87 s, 2 min 42 s; $0.31, $0.46, $0.62), and [[2026-10-15 Ask is asynchronous with start and poll]] (D-023).
6. `01 Decisions/`: [[2026-10-13 Metrics are code, only the blocker Q&A is agentic]] (D-010's spirit: code where no judgement is needed), [[2026-10-13 Artefact text is untrusted, critic fails closed]] (D-009), [[2026-10-13 Scope from the token, enforced twice]].
7. [[C2 - Repo layout - spec]]: where every file goes.

**Whenever this spec is silent or unclear, look in the vault before guessing** (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`). If the vault doesn't answer it, stop and ask Patrick. Never invent a name, a shape or a rule.

## 1. Intent
**What:** `agents/retriever.py` keeps `retrieve(request, repository) -> Evidence`, but fetches with a fixed lookup per lead kind instead of a Strands agent:

| Lead kind | Tools called, in this order (all with the request's `entity_id`) |
|---|---|
| `entity` | `open_blockers`, `failing_reconciliations`, `runbook_for_entity`, `calendar_conflicts` |
| `object` (`id` = an object ID) | `failing_reconciliations`, `load_errors_for_object(object)`, then `mapping_for_field(object, field)` once per distinct `field` value in the load-error rows (sorted), then `defects_for_object(object)` |
| `defect` (`id` = a defect ID) | `open_blockers`, then `defects_for_object(object)` where `object` is that defect's `object_id` in the entity's defect log (read in code); an unknown defect ID skips the second call |
| `runbook_step` | `runbook_for_entity` |
| `task` | `workplan_for_entity`, `team_capacity_rows` |

An `object` lead with no `id` fetches nothing (a warning is logged). A tool that returns an error adds no rows (the error code is logged).

**Why:**
- **Time:** each `retrieve` today is a Haiku agent loop of several model calls, about 1–3 s each; a plan has up to 5 retrieves, and a re-plan more. Measured runs are 87 s and 2 min 42 s. This removes roughly 10–15 s per ask.
- **Cost:** the retriever's model calls go to zero.
- **Reliability:** the prompt had to warn the model to pass the load error's `field`, "never the error code". In code the chain is always right, and the same lead always gives the same rows (easier evals).
- **Judgement stays where it is needed:** the orchestrator chooses the leads, the analyst reasons over the rows, the critic judges, the writer words. Fetching by a known table needs no model (D-010's rule: code where code can do it).

**Success means:**
- `retrieve` makes no model call and imports no Strands. A test for each lead kind shows the cited rows (for E4: `object`/`customers` gives `RC-C3-E4-customers`, the E4 customers load errors, the `field_mappings` row for `tax_id`, and `DEF-0412`).
- An entity outside the request's scope still gives `Evidence(rows=[])`, with no tool call (unchanged).
- Rows are kept once, in first-fetch order (unchanged).
- `Evidence.usage` is empty, so the run's cost has no retriever line.
- The retriever's prompt file, its lock entry, its model setting (`RETRIEVER_MODEL_ID`, `DEFAULT_RETRIEVAL_MODEL`) and its loop caps (`MAX_RETRIEVER_TOOL_CALLS`, `MAX_RETRIEVER_MODEL_CALLS`) are gone; docs and `DECISIONS.md` (D-028) say so.
- `uv run --locked pytest` green, coverage ≥ 98%. Live (verify in AWS, Patrick's OK): an E4 run's trace shows no retriever model usage and the time drops.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Model or code for fetching | Code: the fixed table above (D-028) | Keep Haiku (time and cost for a table lookup); a smaller model (still a loop per retrieve) |
| The defect's object | Read from the entity's defect log in code (`queries`), after the scope check | Only from `open_blockers` rows (a closed defect, such as the decoy DEF-0398, would fetch nothing); a new "defect by ID" tool (one more tool for one lookup) |
| `task` and people | Always fetch `team_capacity_rows` (a few rows) | Guessing "about people" from the lead (that was the model's only judgement, and the analyst does it better) |
| Name and module | Keep `agents/retriever.py` and `retrieve(...)`; the orchestrator's call doesn't change | Moving it to `tools/` (the orchestrator and docs call it the retriever; a move is churn) |
| `AgentFactory` | Moves to `agents/agent_support.py`: the orchestrator types its own factory with it | Leaving it in a module that no longer builds agents |
| The Haiku price in `tools/constants.py` and `COST.md` | Kept in the price table (a priced model, harmless); `COST.md` says "not used since D-028" | Deleting it (an upgrade path for a future cheap agent) |
| Tool-call cap | Gone: the table bounds the calls (at most 4 + distinct load-error fields) | Keeping a cap no model can hit |

## 3. Shapes and behaviour (`agents/retriever.py`)
| Name | Signature / value | Behaviour |
|---|---|---|
| `retrieve(request, repository)` | `(RetrieveRequest, ArtefactRepository) -> Evidence` | scope check → tools on the narrowed scope → the lead's lookup → `Evidence(rows=…)` (no usage) |
| `narrowed_to_entity(scope, entity_id)` | unchanged | the orchestrator imports it |
| `LOOKUP_BY_LEAD_KIND` | `dict[str, Callable[[dict[str, Callable], str, str \| None, ArtefactRepository], list[dict]]]` | lead kind → a function returning the tool results in order |
| `RowRecorder` | `.record(result: dict)`, `.rows` | keeps each row once, in first-fetch order; no cap, no lock (no threads now) |
| `LOAD_ERROR_FIELD_KEY` | `"field"` | the load-error column whose value names the mapped field |

`agents/agent_support.py` gains `AgentFactory` (moved as is). The orchestrator imports it from there.

## 4. Tests
`tests/agents/test_retriever.py` is rewritten (the model-loop tests go: caps, throttling, usage, the reply never used, make_agent). Kept or new, about 7:
- each lead kind's cited rows for E4 (`entity`, `object` with the mapping chain, `defect` with its object from the defect log, `runbook_step`, `task`), one parametrised test;
- an unknown defect ID fetches the open blockers only;
- an `object` lead with no `id`, or an unknown object, gives no load-error or mapping rows (the entity's failing reconciliations still come back: the table calls `failing_reconciliations` first);
- an out-of-scope entity gives no rows and no tool call (kept);
- a row fetched by two tools is kept once, in first-fetch order (kept);
- `team_capacity_rows` returns only that entity's people and programme-wide ones (kept: the narrowed scope).

`tests/agents/test_prompts.py` loses the retriever's prompt test; `tests/test_config.py` and `tests/tools/test_cost.py` lose `RETRIEVER_MODEL_ID`; `tests/agents/test_orchestrator.py`'s real-retriever test drops `agent_factory`.

## 5. Out of scope
- The orchestrator's prompt and its `retrieve` tool (the lead digest stays as built, PR #58).
- The analyst, critic and writer.
- ~~IAM: the Haiku grant left to Y4.~~ **Built differently:** `infra/bedrock_access.py` imported the Haiku default this item removes, so the Haiku profile left the agent Lambdas' Bedrock statement in P4 itself (Michael reviews; tighter IAM, no agent calls Haiku).

Related: [[Build order]], [[P1 - Retriever agent - spec]], [[P4 - Fixed-lookup retriever - plan]]
