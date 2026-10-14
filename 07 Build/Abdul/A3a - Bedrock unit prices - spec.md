---
tags: [build, spec, area/cost]
id: A3a
owner: Abdul
status: awaiting review
updated: 2026-10-14
---
# A3a: Bedrock eu-west-1 unit prices for COST.md (spec)
> **Split of A3.** A3a (this note, D1) researches the unit prices and puts them in `COST.md` with sources and the date; it unblocks Huvison's price table (H5). [[A3b - COST measured figures - spec]] (D2, after H5 and the first eval run with an asker) fills the measured per-question and scale rows. No Python.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before you start, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure.
2. [[Workstreams]] §7 (eu-west-1 only, `eu.*` profiles only).
3. [[Abdul - evals, Cognito, docs]] §6 (your brief for this item).
4. [[Huvison - trust and flow]] §6: his price table `MODEL_PRICES_USD_PER_1K_TOKENS = {model_id: (input, output)}` in `tools/constants.py` is built from your numbers (item H5).
5. [[Build order]]: A3 → H5 → B1/B3 (the business case and the cost slide use `COST.md`).
6. `01 Decisions/`: [[2026-10-13 Default models]] (D-004: Sonnet 4.6 for four agents, Nova Lite for the retriever until Haiku 4.5 activates), [[2026-10-13 EU-only Bedrock inference profiles]] (D-002). `04 Reference/`: [[Judging rubric]] (3.2 cost model, 9 points), [[Pitch track grading rubric]] ("COST.md: measured cost per run and at 100 runs/day").

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/`, `03 Sessions/` (the Bedrock smoke test), `Open follow-ups.md` (Haiku re-test). If it's still unclear, stop and ask Huvison (prices in code) or Patrick. Never invent a price.

## 1. Intent
**What:** for every model ID in `config.py`, the on-demand price per **1,000** input tokens and per **1,000** output tokens in **eu-west-1**, read from the AWS Bedrock pricing page, with the source link, the exact price row used and the date you checked. Plus Claude Haiku 4.5 (for when it activates) and the AgentCore Runtime unit price, because `COST.md`'s per-question table has a row for each. All of it goes into a new `COST.md` section "Unit prices", the "Unit price" column of the per-question table, and a message to Huvison.

**The model IDs** (`config.py`, verified on the C1 branch):
| Constant | Model ID | Used by (`get_settings()`) |
|---|---|---|
| `DEFAULT_REASONING_MODEL` | `eu.anthropic.claude-sonnet-4-6` | `orchestrator_model_id`, `analyst_model_id`, `critic_model_id`, `writer_model_id` |
| `DEFAULT_RETRIEVAL_MODEL` | `eu.amazon.nova-lite-v1:0` | `retriever_model_id` (comment: "until Haiku access is active (D-004)") |
| *(none yet)* | Claude Haiku 4.5, `eu.*` profile ID to copy from the Bedrock console | the retriever, if access activates (D-004) |

**Why:**
- "Cost per run" must be **measured** (rubric), and measuring needs a price per token. Huvison's `flow/cost.py` *(new)* (created by H5) multiplies tokens by your prices.
- Judges check sources. A price without a link and date is a guess.

**Success means:**
- `COST.md` on `develop` has the "Unit prices" section of §3 with every `<…>` field filled: four rows (Sonnet 4.6, Nova Lite, Haiku 4.5, AgentCore Runtime), each with a source link and the check date.
- The per-question table's "Unit price (eu-west-1)" cells for the two Bedrock rows and the AgentCore row are filled.
- Huvison has the table in writing and confirms it matches the prices he puts in `MODEL_PRICES_USD_PER_1K_TOKENS`.

**Assumptions (to reconcile with the owners):**
- **A3a-1:** Huvison's constant is `MODEL_PRICES_USD_PER_1K_TOKENS = {model_id: (input, output)}` in `tools/constants.py` *(new name, H5)*, in **USD per 1,000 tokens**, keyed by the exact model ID strings above.
- **A3a-2:** the price for an `eu.*` model ID is the page's **"Geo Cross-region inference and in-region"** (or "cross-region inference, EU") row for Europe (Ireland), not the "Global Cross-region Inference" row (we never use `global.*`, D-002). If the page shows only one price for the model in Europe (Ireland), that's the one.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Source | The AWS pricing page `https://aws.amazon.com/bedrock/pricing/` (region selector: Europe (Ireland)); the AgentCore page `https://aws.amazon.com/bedrock/agentcore/pricing/` | Third-party price lists, memory, the US price |
| Unit | **USD per 1,000 tokens**, the page's per-1M figure divided by 1,000, written with every significant digit (e.g. `$3.00` per 1M → `0.003`) | Per 1M in `COST.md` (Huvison's table is per 1K; one unit everywhere) |
| Which tier | On-demand, standard context. Not batch, not provisioned throughput, not prompt caching, not the long-context (over 200K tokens) tier | Batch or cache prices (we don't use them) |
| Which row for `eu.*` | The EU geo / cross-region row (A3a-2), with its label copied into the "Page row used" column | The global row |
| Haiku 4.5 | Priced now, marked "not in `config.py` yet (D-004)". Huvison's table gets it only when `config.py` names it | Leaving it out (the retriever may switch on D2) |
| AgentCore Runtime | Its unit prices (per vCPU-hour and per GB-hour, as the page states them) | Estimating "seconds × something" without a price |
| Lambda, API Gateway, DynamoDB, S3 | Stay "~negligible" (the existing `COST.md` row) | Pricing them now (A3b may add them if a judge question needs it) |

## 3. The `COST.md` changes (exact)
**(1) A new section**, inserted after the line `> **Measured, not guessed.** …` and its blank line, before `## Per question`:
```markdown
## Unit prices (on-demand, eu-west-1)
Checked on <YYYY-MM-DD> on the AWS pricing pages, region **Europe (Ireland)**. Every model ID is an `eu.*` inference profile (D-002), so the price is the page's EU cross-region (geo) row. The page quotes USD per 1,000,000 tokens; the figures here are per **1,000** (divided by 1,000), the unit of the price table in code (`tools/constants.py` `MODEL_PRICES_USD_PER_1K_TOKENS`).

| Model / service | Used by | Input, USD per 1K tokens | Output, USD per 1K tokens | Page row used | Source |
|---|---|---|---|---|---|
| `eu.anthropic.claude-sonnet-4-6` | orchestrator, blocker-analyst, critic, writer | <input per 1K> | <output per 1K> | <the row label as the page shows it> | [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/), checked <YYYY-MM-DD> |
| `eu.amazon.nova-lite-v1:0` | retriever (until Haiku activates) | <input per 1K> | <output per 1K> | <row label> | [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/), checked <YYYY-MM-DD> |
| Claude Haiku 4.5 (`<eu.* profile ID from the console>`) | retriever, once access activates (D-004); not in `config.py` yet | <input per 1K> | <output per 1K> | <row label> | [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/), checked <YYYY-MM-DD> |
| AgentCore Runtime | hosts the agents | <price> per vCPU-hour | <price> per GB-hour | <row label> | [Amazon Bedrock AgentCore pricing](https://aws.amazon.com/bedrock/agentcore/pricing/), checked <YYYY-MM-DD> |
```
**(2) The per-question table's "Unit price (eu-west-1)" column**, three cells:
- Sonnet row: `$<input per 1K> in / $<output per 1K> out per 1K tokens`
- Haiku / Nova row: `Nova Lite: $<input per 1K> in / $<output per 1K> out per 1K tokens`
- AgentCore Runtime row: `$<vCPU-hour price> per vCPU-hour + $<GB-hour price> per GB-hour`

Every `<…>` is filled from the page; none stays in the committed file. (Dry-run: the section with sample numbers added to `COST.md` on the C1 branch → `204 passed`, 96%; it names no command, so the doc guards are unaffected.)

## 4. Tests
No code. The checks:
- Linus runs `uv run --locked pytest` on the branch → the baseline count, 0 failed.
- Every row has a link that opens the AWS page, and a date.
- Huvison confirms in writing that his `MODEL_PRICES_USD_PER_1K_TOKENS` values equal the table.
- Sanity: for each model, output costs more than input; Nova Lite is cheaper than Sonnet on both. If not, re-read the page.

## 5. Out of scope
- The measured rows and the scale table ([[A3b - COST measured figures - spec]]).
- The price table in code and `flow/cost.py` (Huvison, H5).
- The "Value side" TODO in `COST.md` (business case, B1).

Related: [[Build order]], [[Abdul - evals, Cognito, docs]], [[A3a - Bedrock unit prices - plan]]
