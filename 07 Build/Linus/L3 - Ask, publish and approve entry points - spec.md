---
tags: [build, spec, area/api]
id: L3
owner: Linus
status: ready
updated: 2026-10-14
---
# L3: the `/ask`, `/publish` and `/approve` entry points (spec)
> **Where a question enters the agent loop, and where a human approves the only write.** Thin HTTP entry points on L1's scope and error body, in front of Huvison's flow. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after L1, L2, H2b and H4 are merged.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Workstreams]] §2 (the ask spine and the publish flow) and §7; [[Linus - API, identity, blocker-analyst]] §3.
3. [[L1 - Scope from the token and the summary handler - spec]] and [[L2 - Entity and rows handlers - plan]]: the handler module this item extends. **L1 and L2 must be merged.**
4. [[C1 - API and spine contracts - spec]] §3 (`AskRequest`, `AskResponse`, `PublishRequest`, `PublishResponse`, `ApproveRequest`, `ApproveResponse`) and §4 (`Question`).
5. [[Huvison - trust and flow]] §3 (`check_budget` starts the run), §5 (`infra/functions/publish.py` *(new)*: `start_publish`, `decide`) and §9 (the 29-second limit); [[H2b - Agent states, local spine and Lambda handlers - spec]] (the ask machine's input and output) and [[H4 - Publish and approve - spec]] (the publish functions and their errors) are the authority for those names.
6. [[Yaw - DevOps]] (FlowStack: the Express ask machine and the Standard publish machine; the `/ask`, `/publish`, `/approve` routes) and [[Clement - front end]] (F4, F5 call these routes).
7. `01 Decisions/`: [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]] (D-007), [[2026-10-13 Scope from the token, enforced twice]] (D-010); EVALS Q11 in the repo's `EVALS.md`.
8. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[Problem statement]], [[Judging rubric]], [[Pitch track grading rubric]], [[Hackathon guideline]]); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Linus. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. `ask(event, context)`: validate the body as `AskRequest`; build the scope from the token; **refuse an entity outside the scope with 403 before anything starts** (EVALS Q11); build a `Question` (server-made `run_id`, budget and attempt limit from settings); run the Express ask state machine synchronously (`StartSyncExecution`); return its output as `AskResponse`.
2. `publish(event, context)`: `PublishRequest` → Huvison's `infra.functions.publish.start_publish(run_id, requester)` with the token's `Scope` → `PublishResponse`.
3. `approve(event, context)`: `ApproveRequest` → `infra.functions.publish.decide(run_id, decision, note, approver)` with the token's `Scope` → `ApproveResponse`.
4. H4's errors mapped exactly, by their base classes in L1's `ERROR_CODE_BY_EXCEPTION`: `PublishForbidden` (`PermissionError`) → 403 `forbidden`; `RunNotFound` and `NoPendingApproval` (`KeyError`) → 404 `not_found`; `NothingToPublish` (`ValueError`) → 400 `invalid_input`. A failed or unconfigured ask run raises `AskSpineFailed`, mapped to C1's `internal` (500, with the `{error, detail}` body). H4's `PublishNotConfigured` (`RuntimeError`, a deployment error) is not mapped: it propagates, the Lambda fails and API Gateway answers a bare 500.

**Why:**
- Q11 is a scored eval: "no E2 rows may reach the ledger". The only way to guarantee it is to refuse before the state machine starts, because the run's first state (`check_budget`) writes the ledger.
- Human approval before the only write is a hard gate. The approval entry point must pass the **token's** scope to `decide`, never one from the body.

**Success means:**
- A CFO's `POST /ask {"entity_id": "E4", ...}` starts exactly one execution on `ASK_STATE_MACHINE_ARN`, named with the new `run_id`, whose input is a `Question` with the token's scope, `budget_usd = settings.run_budget_usd` and `max_attempts = settings.max_claim_attempts`; the 200 body is the execution's `AskResponse`.
- The E4 lead asking about E2 gets 403 `out_of_scope`, and **no execution starts and the ledger stays empty** (tested with a fake state machine that writes an `InMemoryLedger`).
- A malformed entity ID, an empty question, a `scope` key in the body, a body that isn't JSON or an empty body is 400, and nothing starts. No token is 401, and nothing starts.
- A delivery lead's approve and send-back reach `decide` with the token's scope and return `approved` / `sent_back`; anyone else gets 403 `forbidden`; an unknown run, or a run with no publish waiting, is 404; a bad body is 400 and calls nothing.
- `start_publish`'s `PublishForbidden`, `RunNotFound` and `NothingToPublish` come back as 403 `forbidden`, 404 `not_found` and 400 `invalid_input`, with the exception's message as `detail`.
- A failed ask run and a missing `ASK_STATE_MACHINE_ARN` are 500 `internal` with the exception's message as `detail`.
- `uv run --locked pytest`: START + 24 passed (279 on the dry-run base: C1 at 213, L1, L2 and H4's `infra/functions/publish.py`), coverage 97%.

**Assumptions and interfaces** (Huvison's and Yaw's; the tests use fakes for the ask machine and for the publish calls, and import H4's real exception classes):
- **H2b / Y2:** the execution input is the bare `Question` JSON (`Question.model_dump_json()`, built here). The ASL passes `$$.Execution.Input` as `question` to `run_orchestrator` and `write_answer`, and the `WriteAnswer` result is the execution output, with no wrapper key; this handler validates it with `AskResponse.model_validate_json`. The machine's first state (`check_budget`) calls `Ledger.start_run`.
- **H4 (merged first):** `infra.functions.publish.start_publish(run_id: str, requester: Scope, *, ledger=None, stepfunctions=None, state_machine_arn=None) -> PublishResponse` and `decide(run_id: str, decision: str, note: str, approver: Scope, *, ledger=None, stepfunctions=None) -> ApproveResponse`. `start_publish` raises `PublishForbidden` for anyone but the asker, `RunNotFound` for an unknown run and `NothingToPublish` when no claim passed; `decide` raises `ValueError` for an unknown decision, `RunNotFound`, `PublishForbidden` for anyone but a `delivery_lead` of the run's tenant, and `NoPendingApproval` when nothing is waiting. This handler passes the **token's `Scope`** positionally.
- Who may *publish* (as opposed to approve) is decided in `infra.functions.publish`, not in the handler.
- Yaw's IAM for the ask Lambda allows `states:StartSyncExecution` on the ask machine (`docs/DEVOPS_HANDOVER.md`).

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Where the Q11 refusal happens | In the handler, `scope.require(entity_id)` right after the body is validated and **before** the ARN check, the client and the `Question` | Inside the state machine (its first state already writes the ledger); in the orchestrator (a model would be one step from the decision) |
| Who makes the `run_id` | The handler: `run-<uuid4 hex>`, also the execution name | The client (could collide with or overwrite another run); Step Functions' execution ID (not known before the call) |
| A failed, timed-out or unconfigured ask run | `AskSpineFailed` → C1's `internal` (500) with `{error, detail}`, one row in `ERROR_CODE_BY_EXCEPTION` | Letting it propagate (a bare 500 the front end can't parse); 200 with an empty answer (hides the failure) |
| How the flow module is reached | `publish_flow()` imports `infra.functions.publish` on first use; `ask_spine_client()` imports boto3 on first use. Tests replace both with fakes | Importing `infra.functions.publish` at the top (the dashboard routes couldn't load before H4 exists); moto for Step Functions (no `StartSyncExecution` support worth relying on) |
| `PermissionError` from the flow (`PublishForbidden`) | 403 `forbidden`, after `OutOfScope` in the mapping table so `out_of_scope` keeps its own code | A role check in the handler (duplicates H4's rule) |
| H4's other errors | By base class, no new rows: `RunNotFound` / `NoPendingApproval` (`KeyError`) → 404 `not_found`; `NothingToPublish` (`ValueError`) → 400 `invalid_input` | One row per H4 class (couples `api.py` to `publish.py` at import time; the dashboard routes would need the publish module) |
| Who builds the `Question` (lead decision) | This handler: server-made `run_id`, the token's scope, `settings.run_budget_usd`, `settings.max_claim_attempts` | A builder in `infra/functions/` *(new)* (one more cross-item interface for one constructor call) |
| Status code of `/publish` | 200 with `PublishResponse` (the contract) | 202 (not in the contract; the front end checks `status: "awaiting_approval"`) |
| Base64 bodies | Decoded when `isBase64Encoded` is true (HTTP API sets it for some content types) | Assuming plain text |

## 3. Shapes and behaviour
| Handler | Body | 200 | Errors |
|---|---|---|---|
| `infra.functions.api.ask` | `AskRequest {entity_id, question}` | `AskResponse` (the execution's output) | 400 bad body; 401; 403 `forbidden` bad token, `out_of_scope` other entity (before any run); 500 `internal` run failed or `ASK_STATE_MACHINE_ARN` unset |
| `infra.functions.api.publish` | `PublishRequest {run_id}` | `PublishResponse {run_id, execution_arn, status}` | 400 bad body or `NothingToPublish`; 401; 403 `forbidden` bad token or `PublishForbidden` (not the asker); 404 `RunNotFound`; 500 `PublishNotConfigured` |
| `infra.functions.api.approve` | `ApproveRequest {run_id, decision, note}` | `ApproveResponse {run_id, status}` | 400 bad body; 401; 403 `forbidden` `PublishForbidden` (not a delivery lead); 404 `RunNotFound` or `NoPendingApproval` |

New in `infra/functions/api.py` *(new)*: `AskSpineFailed(RuntimeError)`, `body_text(event) -> str`, `new_run_id() -> str`, `ask_spine_client()`, `publish_flow()`, constants `BODY_ENCODING`, `RUN_ID_PREFIX`, `STEP_FUNCTIONS_SERVICE`, `EXECUTION_SUCCEEDED`, `PUBLISH_FLOW_MODULE`, and the `(PermissionError, ERROR_FORBIDDEN)` and `(AskSpineFailed, ERROR_INTERNAL)` rows of `ERROR_CODE_BY_EXCEPTION`.

Environment for the `ask` Lambda: the dashboard settings plus `ASK_STATE_MACHINE_ARN`, `RUN_BUDGET_USD`, `MAX_CLAIM_ATTEMPTS` (the handler puts the last two on the `Question`). The `publish` / `approve` functions use the same `infra/functions/` bundle.

## 4. Tests
`tests/infra/functions/test_api.py` *(new)*, 24 new tests: `FakeAskSpine` (records each `start_sync_execution` call and starts the run in an `InMemoryLedger`, as `check_budget` will) and `FakePublishFlow` (H4's signatures, return models and real exception classes from `infra.functions.publish`). Ask: one run with the token's scope; **Q11 refused before any run, ledger empty**; five bad bodies start nothing; a base64 body; no token starts nothing; a failed run is 500 `internal`; no ARN is 500 `internal`; the client's region. Publish and approve: publish as the signed-in user; `start_publish`'s three errors (`PublishForbidden` 403, `RunNotFound` 404, `NothingToPublish` 400); approve and send back as a delivery lead; 403 for anyone else; 404 for an unknown run; 404 when no publish is waiting (`NoPendingApproval`); three bad bodies call nothing.

## 5. Out of scope
- The state functions (`infra/functions/steps.py` *(new)*, H2b), the publish flow (`infra/functions/publish.py`, H4), the state machines (Y2), the 29-second timing and any async `/ask` (Huvison, §9 of his brief).
- The front-end ask and approve screens (F4, F5).

Related: [[L3 - Ask, publish and approve entry points - plan]], [[Huvison - trust and flow]], [[Build order]]
