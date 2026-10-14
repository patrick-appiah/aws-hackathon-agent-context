---
tags: [build, spec, area/flow]
id: H5
owner: Huvison
status: awaiting review
updated: 2026-10-14
---
# H5: Cost per run, the price table and `tools/cost.py` (spec)
> **Every state that runs an agent turns the agent's `usage` into USD and adds it to the run in the ledger; the budget check and `AskResponse.cost_usd` read that number.** The code needs only C1 and is built **before H2a** (H2a and H2b call `record_usage`); the prices themselves come from Abdul's A3a and replace the placeholders in one later commit. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` once C1 is merged. The repo is the source of truth for code; the vault is the source of context.

## 0. Context: read the vault first
The team vault is the shared context space for this project. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] §3, §4 and §7.
3. [[Huvison - trust and flow]] §6 "Cost": the owner's brief for this item.
4. [[Build order]]: H5 depends on C1 (code) and A3 (prices). Check C1 is `merged`. A3a may still be open: the plan's Task 3 waits for it.
5. [[A3a - Bedrock unit prices - spec]] (Abdul): where the prices and their sources come from, and the exact constant name he fills.
6. [[C1 - API and spine contracts - spec]] §4 (`Usage`, `total_tokens`); [[2026-10-13 Default models]] and [[2026-10-13 EU-only Bedrock inference profiles]]; the repo's `COST.md`.
7. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` ([[Judging rubric]] and [[Pitch track grading rubric]]: COST.md "measured"), `03 Sessions/`, `Open follow-ups.md`. If the vault doesn't answer it, stop and ask Huvison. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. `tools/constants.py`: `TOKENS_PER_PRICE_UNIT = 1000` and `MODEL_PRICES_USD_PER_1K_TOKENS = {model_id: (input_usd, output_usd)}` for every model ID `config.py` can select.
2. `infra/__init__.py` *(new)* and `infra/functions/__init__.py` *(new; create if missing, docstring only)*: the packages the later Lambda glue lands in. `infra/__init__.py` must not import CDK, and neither may import `infra.functions.steps` (P2's assumption A2).
3. `tools/cost.py` *(new)*: `cost_usd(usages) -> float`, `record_usage(ledger, run_id, usages) -> float` (adds tokens and cost to the run via `Ledger.add_cost`), `UnpricedModel`.
4. `pyproject.toml`: `--cov=infra/functions` inserted directly before `--cov-report` if missing (check it is there), so the Lambda glue counts in coverage. `tools/cost.py` is already covered by `--cov=tools`.

**Why:** "COST.md measured, not guessed" is graded (Workstreams §6). The model calls happen in four workstreams; C1 put `usage` on every agent result so one function can price them. The per-run budget ceiling (`RUN_BUDGET_USD`, D-012) is only real if the spent cost in the ledger comes from real calls.

**Success means:**
- `cost_usd` equals tokens × price ÷ 1,000 summed over the calls, for any mix of the configured models; an unknown model raises `UnpricedModel` naming it.
- `record_usage` adds the summed tokens and the cost to the run (`Ledger.run()` shows them, H1).
- A test fails if `config.py` can select a model the table doesn't price.
- `uv run --locked pytest`: start + **5 passed**; coverage not lower.
- After A3a: the two prices are Abdul's, with the source and date in the comment above the table; no test changes.

**Assumptions:**
- H1 is merged (the `record_usage` test reads `Ledger.run()`). If you build H5 before H1, swap that test's `ledger.run("run-1")` read for `ledger.runs["run-1"]` and ledger a Ruling.
- Abdul's A3a uses exactly `MODEL_PRICES_USD_PER_1K_TOKENS` keyed by the `eu.*` model IDs (his spec, A3a-1). Until his values land, the table holds **clearly marked placeholder list prices** (the comment says "Placeholder list prices until A3"); the formula and tests don't depend on the values.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Where the prices live | `tools/constants.py` (the brief; domain constants only there). Keyed by the exact model ID string | `config.py` (prices aren't deployment settings); a JSON file (one more loader) |
| Unit | USD per 1,000 tokens, `(input, output)` tuples, `TOKENS_PER_PRICE_UNIT = 1000` | Per million (Abdul's research is in per-1K, A3a-1) |
| Unknown model | `UnpricedModel` (a `LookupError`), with the fix in the message | Pricing it at zero (the budget would silently stop counting) |
| Who records | `record_usage(ledger, run_id, usages)`, called by every agent-running state (H2b) | Each state computing cost itself (four copies of the formula) |
| Coverage | `--cov=infra/functions` added if missing (C2 §3: whichever item lands first adds it); `tools/cost.py` is covered by `--cov=tools` | Leaving `infra/functions/` *(new)* out of coverage |
| Price values now | Placeholders, marked, replaced in Task 3 when A3a lands | Waiting for A3a before writing any code (H2a needs `record_usage` on D1) |

## 3. Shapes
- `tools.constants.TOKENS_PER_PRICE_UNIT = 1000`
- `tools.constants.MODEL_PRICES_USD_PER_1K_TOKENS: dict[str, tuple[float, float]]`, keys `"eu.anthropic.claude-sonnet-4-6"`, `"eu.amazon.nova-lite-v1:0"` (the two IDs `config.py` selects today; add Haiku's when D-004 switches the retriever).
- `tools.cost.UnpricedModel(LookupError)`
- `tools.cost.cost_usd(usages: list[Usage]) -> float`
- `tools.cost.record_usage(ledger: Ledger, run_id: str, usages: list[Usage]) -> float`: `ledger.add_cost(run_id, tokens_in, tokens_out, cost)` with `total_tokens(usages)`; returns the cost.

## 4. Tests (`tests/tools/test_cost.py` *(new)*, 5)
- One call: tokens × price ÷ 1,000. Several calls and models: the sum; no calls: 0.
- An unpriced model raises `UnpricedModel` naming the model.
- `record_usage` adds tokens and cost to the run.
- Every model ID in `get_settings()` (orchestrator, retriever, analyst, critic, writer) has a price.

## 5. Out of scope
- `COST.md`'s figures (Abdul, A3a and A3b). This item only reads A3a's two prices.
- Calling `record_usage` from the states (H2b).
- AgentCore, Lambda and DynamoDB costs ("~negligible" in `COST.md`).

Related: [[H5 - Cost per run - plan]], [[Huvison - trust and flow]], [[Build order]]
