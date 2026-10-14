---
tags: [build, spec, area/contracts]
id: C1
owner: Patrick
status: awaiting review
updated: 2026-10-14
---
# C1: API and ask-spine contracts (spec)
> **Every other build item depends on this one.** Until C1 is merged, no plan may invent its own names for these types. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop`. The repo is the source of truth for code; the vault is the source of context.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] (`06 Workstreams/`): the architecture with owners, the code already built, the contracts table, the timeline, what's graded, and the non-negotiable rules.
3. [[Patrick - contracts, orchestrator, retriever]]: the owner's brief for this item.
4. [[Build order]] (`07 Build/`): what C1 unblocks.
5. `01 Decisions/` (D-001, D-007, D-009, D-011, D-012, D-014, D-019, D-020) and `05 Workflow/` ([[Dev loop]], [[Working with AI assistants]], [[Handling security findings]]).

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask the owner. Never invent a name, a shape or a rule.

## 1. Intent
**What:** freeze, in code, the shapes every workstream builds against:
1. **API response and request models** for the six routes, with an error body. These live in `tools/api_schema.py` *(new)*, exported as JSON Schema for the Angular front end.
2. **Ask-spine step models**, the inputs and outputs passed between Step Functions states and agents. These go in `tools/models.py`, and every agent result carries **`usage`** so cost can be measured.
3. **New settings** in `config.py`: auth mode, the rejected-records table, the bucket, the status-pack prefix, the state-machine ARNs and the Cognito IDs.
4. **The DevOps handover** (`docs/DEVOPS_HANDOVER.md` *(new)*): what each Lambda or runtime is, which environment variables it reads, which IAM actions on which resources it needs, and how it is bundled.
5. **Doc updates:** `docs/TEAM_PLAN.md` §3 API table, `ARCHITECTURE.md` §3c, and `DECISIONS.md` D-021.

**Why:**
- Eight people build in parallel (`06 Workstreams/`). Four back-end workstreams and the front end meet at these shapes.
- If the shapes exist only in prose, everyone guesses and the walking skeleton (D1 18:00) breaks at the seams. Code plus tests means every later plan quotes signatures that exist and can be checked.
- `usage` on every agent result is the only way to measure cost per run. The model calls happen inside Patrick's and Linus's agents, but Huvison records the cost (COST.md "measured": 8 points shared).

**Success means:**
- `tools/api_schema.py` exists. Its models are tested against the **real** outputs of `tools/metrics.py` (a CFO scope and an E4-lead scope), against today's front-end fixtures where the shape is already agreed (`/ask`), and against the eval runner's asker contract (`evals/run.py`).
- The step models in `tools/models.py` are tested: valid ones accepted; malformed, wrong role or extra fields rejected; usage totals computed.
- The new settings live in `config.py`, each with a default and an environment override test; an invalid `AUTH_MODE` fails at `get_settings()`.
- `uv run python scripts/export_api_schema.py` writes one JSON Schema per API model. The committed schemas match the models (a test fails if someone changes a model without re-exporting).
- `docs/DEVOPS_HANDOVER.md`, TEAM_PLAN §3, ARCHITECTURE §3c and D-021 describe the contracts.
- `uv run --locked pytest` green (160 tests plus the new ones), coverage not lower than today (95%). The architecture guard still passes: the core imports no boto3, Strands, adapters, config or os.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Where the API models live | `tools/api_schema.py`, the core. Plain pydantic, no AWS, shared by handlers, the eval runner and the schema export | an `api/` subfolder (Linus's folder: "stay in your folders"); OpenAPI written by hand (a second source of truth) |
| Summary shape | **Exactly what `metrics.portfolio_summary` returns today.** The models describe it; they don't reshape it. The front end adopts these keys (spec decision in the briefs) | Reshaping to the old front-end types |
| Model strictness | Responses: `extra="forbid"`, so a renamed key fails the tests instead of silently disappearing. Requests (`AskRequest`, `PublishRequest`, `ApproveRequest`): `extra="forbid"` plus field validators (entity ID pattern, question 1–500 chars, `run_id` non-empty) | Lenient models (drift goes unnoticed) |
| Where step models live | `tools/models.py`, next to `BlockerClaim` and `Verdict`, which they reuse | A new module (more imports, no gain) |
| Usage | `Usage {model_id, tokens_in, tokens_out}`. **Every agent result has `usage: list[Usage]`**, one entry per model call (an agent may call the model several times). `total_tokens(usages)` helper | Usage only on the final answer (cost per agent lost) |
| Answer model | `Answer {headline, bullets[Bullet{text, citations[Citation]}], rejected_count}` defined once in `tools/models.py`. The writer returns it; `AskResponse.answer` reuses it | Two copies |
| Approval key | `/approve` takes **`run_id`** (the task token is stored by `run_id`, Huvison H1); `/publish` returns `run_id` and `execution_arn` | `execution_arn` as the key (in a `run_id`-keyed ledger) |
| Error body | `ErrorResponse {error, detail}`, with `error` in `invalid_input` (400), `unauthorized` (401), `forbidden` / `out_of_scope` (403), `not_found` (404); constants for the codes. `invalid_input` and `out_of_scope` reuse `tools/agent_tools.py`'s values | Free-form error strings |
| Refused `/ask` | An out-of-scope `/ask` returns **403 `ErrorResponse`**, and the eval asker maps it to `"refused": true`. `AskResponse` has no `refused` field (the API never sends one) | A 200 with `refused: true` |
| Settings defaults | `AUTH_MODE` default `none` (local and tests); allowed `none` / `cognito`; anything else raises `ValueError` in `get_settings()`. Table, prefix and pool defaults are named constants; the ARNs, bucket and pool IDs default to `None` (not configured locally), like `guardrail_id` | Silent fallback on a typo (a mistyped `AUTH_MODE` would disable sign-in) |
| JSON Schema location | Exported to `web/src/app/core/api/schema/` *(new)*, committed, with a header comment that it is generated. A test compares the committed files with the models. Mildred agreed the folder (her brief) | Front end running Python to generate them; schemas not committed (front end can't use them) |
| DevOps handover | A Markdown table per function in `docs/DEVOPS_HANDOVER.md`, with entry points marked *planned* until the code exists | Code-generated handover (overkill for two days) |

## 3. The API models (`tools/api_schema.py`)
All `ConfigDict(extra="forbid", frozen=True)`. `Citation` and `Row` are reused from `tools/models.py`.

**`/summary` → `SummaryResponse`** (the keys `metrics.portfolio_summary` returns):
| Model | Fields |
|---|---|
| `SummaryResponse` | `as_of: str`, `tenant_id: str`, `programme_name: str`, `target_platform: str`, `currency: str`, `overall: OverallReconciled`, `pass_rate: PassRate`, `open_blockers: OpenBlockers`, `final_cutover: Cutover | None`, `capacity: Capacity`, `entities: list[EntityRow]` |
| `OverallReconciled` | `records_reconciled: int`, `records_in_scope: int`, `pct: float` |
| `PassRate` | `latest: CycleTotals | None`, `previous: CycleTotals | None`, `target_pct: float` |
| `CycleTotals` | `cycle_id: str`, `records_matched: int`, `records_sent: int`, `pct: float`, `evidence: list[Citation]` |
| `OpenBlockers` | `count: int`, `oldest_days: int`, `blockers: list[Blocker]` |
| `Blocker` | `reference: str`, `entity_id: str`, `blocker: str`, `age_days: int`, `owner_role: str`, `evidence: list[Citation]` |
| `Cutover` | `entity_id: str`, `cutover_forecast: str`, `cutover_baseline: str`, `days_remaining: int`, `days_behind_plan: int`, `live: bool`, `evidence: list[Citation]` |
| `Capacity` | `month: str`, `people_used: int`, `people_planned: int`, `pct: float`, `by_role: list[RoleCapacity]` |
| `RoleCapacity` | `role: str`, `people_used: int`, `people_planned: int`, `pct: float`, `evidence: list[Citation]` |
| `EntityRow` | `entity_id`, `entity_name`, `business_role`, `source_tier`, `source_description`, `target_company_code` (all `str`), `reconciled: Reconciled`, `cutover: Cutover`, `open_blockers: int`, `status: str` (one of `EntityStatus` values) |
| `Reconciled` | `records_reconciled: int`, `records_in_scope: int`, `pct: float`, `evidence: list[Citation]` |

**`/entity/{id}` → `EntityResponse`:** `entity: EntityRow`, `blockers: list[Blocker]`, `failing_reconciliations: list[FailedReconciliation]`, `calendar_conflicts: list[CalendarConflict]`.
- `FailedReconciliation`: `recon_id`, `cycle_id`, `entity_id`, `object_id`, `records_sent`, `records_rejected`, `records_matched`, `match_rate_pct`, `target_pct`, `status` (all `str`, as the CSV holds them; `metrics.FAILED_RECONCILIATION_FIELDS`), plus `evidence`.
- `CalendarConflict`: `window_id`, `label`, `type`, `evidence`.
- Built by `entity_response(repository, scope, entity_id)` *(new, in `tools/api_schema.py`)*: one function, so Linus's handler and the tests share it. It raises `OutOfScope` or `KeyError`, which the handler maps to 403/404.

**`/rows?cite=...` → `RowsResponse`:** `rows: list[Row]`, `missing: list[Citation]`. Built by `rows_response(repository, scope, citations)` *(new)*. Citations that don't exist **or** aren't visible to the scope (`queries.in_entity_view`) go to `missing`, and their rows are never returned.

**`POST /ask`:**
- `AskRequest {entity_id, question}` (entity ID validated with `validate_entity_id`; question 1–500 characters).
- `AskResponse {run_id, answer: Answer | None, rejected: list[RejectedClaim], cost_usd: float, partial: bool, partial_reason: str | None, trace: list[TraceStep]}`.
- `RejectedClaim {claim_id, statement, reason, verdicts: list[Verdict]}`.
- `TraceStep {step: str, agent: str | None, prompt: PromptRef | None}`.
- `PromptRef {agent, version, sha256}` (the same keys as `Prompt.provenance()`).

**`POST /publish`:** `PublishRequest {run_id}` → `PublishResponse {run_id, execution_arn, status: Literal["awaiting_approval"]}`.

**`POST /approve`:** `ApproveRequest {run_id, decision: Literal["approve", "send_back"], note: str = ""}` → `ApproveResponse {run_id, status: Literal["approved", "sent_back"]}`.

**Errors:** `ErrorResponse {error: ErrorCode, detail: str}`. `ErrorCode` is `Literal["invalid_input", "unauthorized", "forbidden", "out_of_scope", "not_found"]`. Status codes are in a constant map, `ERROR_STATUS_CODES` (400, 401, 403, 403, 404).

**Export list:** `API_MODELS = {"summary": SummaryResponse, "entity": EntityResponse, "rows": RowsResponse, "ask_request": AskRequest, "ask_response": AskResponse, "publish_request": PublishRequest, "publish_response": PublishResponse, "approve_request": ApproveRequest, "approve_response": ApproveResponse, "error": ErrorResponse}`. The export script and the drift test both use it.

## 4. The step models (`tools/models.py`)
| Model | Fields | Used by |
|---|---|---|
| `Usage` | `model_id: str`, `tokens_in: int ≥ 0`, `tokens_out: int ≥ 0` | every agent result; Huvison's cost (`add_cost`) |
| `Question` | `run_id: str`, `scope: Scope`, `entity_id: str` (validated), `question: str` (1–500), `budget_usd: float > 0`, `max_attempts: int ≥ 1` | input to the ask spine (`check_budget`) |
| `PlanStep` | `agent: Literal["retriever", "blocker_analyst"]`, `tool_hint: str`, `reason: str` | orchestrator |
| `Plan` | `run_id: str`, `steps: list[PlanStep]` | orchestrator output |
| `Lead` | `kind: Literal["entity", "object", "defect", "runbook_step", "task"]`, `id: str | None` | retriever input |
| `RetrieveRequest` | `scope: Scope`, `entity_id: str`, `lead: Lead` | retriever input |
| `Evidence` | `rows: list[Row]`, `usage: list[Usage]` | retriever output |
| `AnalystResult` | `claims: list[BlockerClaim]`, `usage: list[Usage]` | blocker-analyst output |
| `OrchestratorResult` | `plan: Plan`, `claims: list[BlockerClaim]`, `partial: PartialAnswer | None`, `usage: list[Usage]` (its own plus its sub-agents') | `run_orchestrator` state |
| `PartialAnswer` | `reason: str`, `claims_so_far: list[BlockerClaim]` | orchestrator, `check_budget` |
| `Bullet` | `text: str` (no angle brackets, like `BlockerClaim.statement`), `citations: list[Citation]` | writer |
| `Answer` | `headline: str`, `bullets: list[Bullet]`, `rejected_count: int ≥ 0` | writer output; `AskResponse.answer` |
| `WriterInput` | `scope: Scope`, `question: str`, `passed_claims: list[BlockerClaim]`, `metrics_snapshot: dict` | writer input |
| `WriterResult` | `answer: Answer`, `usage: list[Usage]` | writer output |

Helper: `total_tokens(usages: list[Usage]) -> tuple[int, int]`, the sum of input and output tokens.

Step models are `extra="forbid"`. Scope is still **never** a tool argument: `Scope` appears in step inputs because Step Functions carries it between states, as the TEAM_PLAN §3 scope rule says ("passed in every request and tool call", built server-side).

## 5. The new settings (`config.py`)
| Setting (`Settings` field) | Environment variable | Default |
|---|---|---|
| `auth_mode` | `AUTH_MODE` | `none` (allowed `none`, `cognito`; otherwise `ValueError`) |
| `rejected_table` | `REJECTED_TABLE` | `erp-portal-rejected-records` |
| `artefacts_bucket` | `ARTEFACTS_BUCKET` | `None` |
| `status_pack_prefix` | `STATUS_PACK_PREFIX` | `status-packs/` |
| `ask_state_machine_arn` | `ASK_STATE_MACHINE_ARN` | `None` |
| `publish_state_machine_arn` | `PUBLISH_STATE_MACHINE_ARN` | `None` |
| `user_pool_id` | `USER_POOL_ID` | `None` |
| `user_pool_client_id` | `USER_POOL_CLIENT_ID` | `None` |

Defaults are named constants at the top of `config.py`, like the existing ones. `ledger_table` stays `erp-portal-run-ledger`.

## 6. `scripts/export_api_schema.py` *(new)*
- `uv run python scripts/export_api_schema.py` writes `web/src/app/core/api/schema/<name>.schema.json` for every entry in `API_MODELS` (`model_json_schema()`, sorted keys, two-space indent, trailing newline), plus a `README.md` saying the files are generated: don't edit, re-run the script.
- `--out <dir>` overrides the folder (the tests use a temporary folder).
- Exit code 0; prints the files written.
- **Drift test:** the committed schema files equal a fresh export.

## 7. `docs/DEVOPS_HANDOVER.md`
One row per function: **name**, **entry point** (planned until built), **trigger**, **environment variables** (from §5 and the existing settings), **IAM** (actions on specific resources: the S3 `artefacts/` prefix read; the `status-packs/` write for the publish writer only; the ledger and rejected tables; `states:StartSyncExecution` on the ask machine; `states:StartExecution` / `SendTaskSuccess` / `SendTaskFailure` on the publish machine; `bedrock:InvokeModel` on the **specific** `eu.anthropic.claude-sonnet-4-6` and `eu.amazon.nova-lite-v1:0` inference-profile ARNs and the Guardrail ARN), and **bundling** (`uv export --no-dev --format requirements-txt --no-hashes`; include `agents/prompts/` and `prompts.lock` wherever prompts load).

Functions:
- `summary`, `entity`, `rows`, `ask`, `publish`, `approve` (Linus, `api/handlers.py` *(new)* *(planned)*);
- `check_budget`, `run_orchestrator`, `store_claims`, `judge_claim`, `retry_decision`, `record_rejection`, `write_answer` (Huvison, `flow/steps.py` *(new)* *(planned)*);
- `start_publish`, `decide` and the status-pack writer (Huvison, `flow/publish.py` *(new)* *(planned)*);
- the AgentCore runtime and its shim (Yaw).

## 8. Doc updates
- `docs/TEAM_PLAN.md` §3 API table: point each route at its model in `tools/api_schema.py`, with `/publish` returning `run_id` and `execution_arn`, `/approve` taking `run_id`, and errors in the `{error, detail}` body.
- `ARCHITECTURE.md` §3c: a line saying the contracts live in `tools/api_schema.py` and the step models in `tools/models.py`.
- `DECISIONS.md` **D-021** "API and ask-spine contracts in code": what, why, rejected, from §2.

## 9. Tests (new, in `tests/`)
- `tests/tools/test_api_schema.py` *(new)*:
  - `SummaryResponse` validates `portfolio_summary` for the CFO and E4-lead scopes;
  - a renamed or extra key fails;
  - `entity_response` for E4 (blockers include `DEF-0412`, failing includes `RC-C3-E4-customers`, the calendar includes `CAL-004`);
  - an E2 request with E4-lead scope raises `OutOfScope`, and an unknown entity raises `KeyError`;
  - `rows_response` returns existing visible rows, and puts missing and out-of-scope citations in `missing`;
  - request validation (a bad entity ID, an empty or over-long question, an unknown `decision`);
  - an `AskResponse` built in the test passes the eval runner's answer checks (`evals/run.py` reads `answer.bullets[].citations` as `{artefact, row_id}`; `partial`, `rejected`, `cost_usd`). The front end's mock `ask-E4.json` uses an older `rejected[{claim, reason}]` shape; the contract's `rejected[{claim_id, statement, reason, verdicts}]` wins, and Mildred aligns the fixture in F1;
  - `ErrorResponse` codes map to `ERROR_STATUS_CODES`.
- `tests/tools/test_step_models.py` *(new)*: each step model accepts a valid example and rejects extra fields and bad values; `total_tokens`; `Bullet` rejects angle brackets.
- `tests/test_config.py` *(new)*: each new setting's default and environment override; an invalid `AUTH_MODE` raises. `get_settings` is cached, so clear `get_settings.cache_clear()` around the tests.
- `tests/scripts/test_export_api_schema.py` *(new)*: exporting to a temporary folder writes one file per `API_MODELS` entry; the committed schemas match a fresh export.

## 10. Out of scope
- Any handler, agent, flow or CDK code: L1–L6, P1–P3, H1–H6, M/Y.
- Changing `metrics.portfolio_summary`'s output, including the timeline-bars question, which is a later decision.
- Changing front-end code. Mildred aligns her types to the exported schemas in F1.

Related: [[Build order]], [[Patrick - contracts, orchestrator, retriever]], [[Workstreams]]
