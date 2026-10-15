---
tags: [build, spec, area/agents, area/metrics, area/business]
id: P9
owner: Patrick (Linus away: Patrick builds his metrics and tools files too)
status: ready
updated: 2026-10-15
---
# P9: the CFO can ask about value for money (spec)
> **From the validation session (2026-10-15):** Joseph Akayesi asked whether a CFO can ask if the programme is value for money, or is saving cash. P9 adds three money figures, computed in code from data we already have (the roster's planned and worked days, the rate card's day rates, the workplan's slip), as figure tools for the analyst. Every number stays computed by code and cited (D-010, D-030). Repo: `Amali-Tech/cloud-9-hackathon`, branch `feature/value-for-money` from `develop`. **After the 14:00 code freeze, by Patrick's exception.**

## 0. Context: read the vault first
Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`. Read: [[How to execute a plan]]; [[2026-10-15]] (the validation session, Joseph's question); [[2026-10-13 Metrics are code, only the blocker Q&A is agentic]] (D-010); [[2026-10-15 Figures are verified by code and the critic judges rows]] (D-030); [[P6 - Analyst claim coverage - spec]] (prompt v1.3.0); the repo's `tools/metrics.py` (`effort_cost`, `days_to_cutover`, `capacity_used`), `tools/agent_tools.py` (`make_analyst_tools`), `agents/prompts/blocker_analyst.txt` and `orchestrator.txt`, `EVALS.md` and `evals/`. If unclear, look in the vault, then ask Patrick.

## 1. Intent
### 1.1 Three figures (`tools/metrics.py`)
| Function | Returns (top-level fields, so they can be figures) | Computed as | E4 today |
|---|---|---|---|
| `spend_vs_plan(repository, entity_id)` | `months`, `planned_cost`, `actual_cost`, `variance`, `currency`, `evidence` | over the **completed** roster months (`month_complete == "Y"`) of people whose primary entity is this one: `planned_days × day_rate` vs `days_worked × day_rate`; `variance = actual − planned` | Jul–Sep: planned **$276,400**, actual **$292,500**, variance **+$16,100** |
| `cost_of_delay(repository, entity_id)` | `days_behind_plan`, `working_days_behind`, `team_daily_cost`, `cost_of_delay`, `currency`, `evidence` | the working days (Mon–Fri) from the baseline to the forecast cutover (`days_to_cutover`) × the daily cost of the entity's people planned in the as-of month (the sum of their day rates) | 6 days behind, **5 working days** × **$7,150** = **$35,750** |
| `unused_capacity(repository, entity_id)` | `unused_days`, `unused_cost`, `currency`, `evidence` | over the **completed** months: `max(0, planned_days − days_worked) × day_rate` | **9 days, $4,500** (P-041, September: 0 of 9) |

- Evidence: the roster rows and rate-card rows used (and `WP-034` for the delay), as `effort_cost` cites them today.
- Programme-wide people (primary entity "All") are not apportioned to an entity, as in `effort_cost`.
- The current month is never in `spend_vs_plan` or `unused_capacity`: its plan is a full month, its worked days run only to the as-of date.
- There is **no budget** in the data: no figure says "over or under budget".

### 1.2 Figure tools for the analyst (`tools/agent_tools.py`)
`make_analyst_tools` gains `spend_vs_plan`, `cost_of_delay`, `unused_capacity`, entity-scoped like the others (`_requires_entity_in`), returning the fields above without `evidence`. `validate_claim` recomputes them like every figure.

### 1.3 Prompts
- **Analyst v1.4.0:** the three tools in the tool list; "for a question about cost, spend or value for money, state these figures with their tools; never compute money yourself". "Over plan" and "under plan" are relative to the planned days; never say "budget" (no budget in the data).
- **Orchestrator v1.3.0:** "for a question about cost, spend or value, follow a `task` lead" (the workplan and the roster the analyst cites).

### 1.4 Eval, docs
- **EVALS Q15:** "Is E4 giving us value for money?" (CFO). Must say one of the three amounts; metrics checks pin `spend_vs_plan.actual_cost == 292500`, `variance == 16100`, `cost_of_delay.cost_of_delay == 35750`; must not say "budget".
- `DECISIONS.md` **D-034** (value for money as code figures; rejected: a model estimating cost, a budget we don't have); `AGENTS.md` analyst tools; `EVALS.md` Q15 row; the business case gains one line under "What changes for the CFO".

**Success means:** the three functions return the E4 values above; the analyst can use them as figures; Q15 passes live (local asker, Guardrail on); the suite is green with coverage ≥ 98%.

## 2. Out of scope
A dashboard card (would change `SummaryResponse` and the front end on the last day); a budget figure (no data); cost forecasts at completion.

Related: [[Build order]], [[P9 - Value for money - plan]]
