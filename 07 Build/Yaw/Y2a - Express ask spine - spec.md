---
tags: [build, spec, area/devops]
id: Y2a
owner: Yaw
status: ready
updated: 2026-10-14
---
# Y2a: FlowStack, the Express ask spine (spec)
> **Split from Y2** (the lead's rule: one item per agent session). Y2a is the Express ask spine and the `/ask` wiring; [[Y2b - Standard publish flow - spec]] is the publish flow with human approval. Each deploys and merges on its own. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after [[Y1 - ApiStack - spec]] and [[M3a - GuardrailStack - spec]] are merged.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] (`06 Workstreams/`): the architecture with owners, the code already built, the contracts and the rules (§7).
3. [[Yaw - DevOps]]: the owner's brief; and [[Michael - DevOps]] (the other half of DevOps).
4. [[Build order]]: what this item depends on and unblocks.
5. [[M2 - App, DataStack and LedgerStack - spec]]: the CDK app, `build_stacks`, the prefix, the test fixtures and the patterns every DevOps item follows.
6. [[Y1 - ApiStack - spec]] (the bundler, `PortalFunction`, the stub pattern) and [[M3a - GuardrailStack - spec]] (the Guardrail the agent steps use); [[M4b - Observability - spec]] reads this item's state machine and log group.
7. [[Huvison - trust and flow]] (the step functions in `flow/steps.py` *(new)*, the 29-second timing) and [[Patrick - contracts, orchestrator, retriever]] (the step models in `tools/models.py`).
8. `01 Decisions/`: [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]], [[2026-10-13 Artefact text is untrusted, critic fails closed]], [[2026-10-13 EU-only Bedrock inference profiles]], [[2026-10-13 Team are admins, workload roles least-privilege]].

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Yaw (owner) or Huvison (the step functions and their JSON). Never invent a name, a shape or a rule.

## 1. Intent
**What:** a `FlowStack` *(new)* holding the **Express ask spine** (D-007), and the `/ask` route's permission to start it:
1. **One Lambda per state**, built with `PortalFunction` (Y1): `check_budget`, `run_orchestrator`, `store_claims`, `judge_claim`, `retry_decision`, `record_rejection`, `write_answer`. **Stubs first** (`infra/functions/stub_steps.py` *(new)*: canned answers, the critic always passes; the D1 18:00 walking skeleton), then Huvison's `flow.steps.<name>` once H2 is merged (`STEPS_WITH_REAL_HANDLERS`).
2. **The definition:** `Start` → `CheckBudget` → `BudgetLeft` (partial → `WritePartialAnswer`) → `RunOrchestrator` → `StoreClaims` → **Map `JudgeEachClaim`** (≤ 4 at once): `JudgeClaim` → `ClaimPassed`? keep : `RetryDecision` → **`RetryOrReject` Choice on `$.retry.decision == "retry"`** → `ReplanClaim` → `RevisedClaimReturned`? `StoreRevisedClaim` → `UseRevisedClaim` → `JudgeClaim` (loop) : `RecordRejection`. Then `WriteAnswer` with **only the passed claims** → `Answer` (the machine's output is the `AskResponse`).
3. **Logging and tracing:** a log group with level `ALL` and execution data (M4b's dashboard reads `cost_usd` from it), X-Ray on; timeout 2 minutes.
4. **Least privilege:** ledger-only steps get the ledger actions on the two tables; agent steps also get `bedrock:InvokeModel` + `InvokeModelWithResponseStream` on the **two `eu.*` inference profiles in eu-west-1 and the EU foundation-model ARNs they route to** (`infra/bedrock_access.py` *(new)*), `bedrock:ApplyGuardrail` on the Guardrail, and `s3:GetObject` on `artefacts/*`.
5. **`/ask` wiring:** `ApiStack` takes `flow`; the `ask` Lambda gets `ASK_STATE_MACHINE_ARN` and `states:StartSyncExecution` on this machine only.
6. **Output** `AskStateMachineArn`; attributes `.ask_state_machine`, `.ask_log_group`, `.step_functions`, `.ask_start_statement()`.

**Why:**
- "One agent loop that genuinely runs" is what judges weigh most; the spine is the loop in AWS. Express + `StartSyncExecution` answers within the HTTP request.
- The retry must be a `Choice` on a value the ledger produced, never a model output (D-007, D-012). The critic must stay blind: its input is the run ID, the claim and the scope only.
- The guideline's hard rule: `eu.*` profiles only, IAM on the exact ARNs (no `bedrock:*`, no `*`).

**Success means:**
- `uv run --locked pytest` → **S + 17 passed** (dry-run 240 → **257**), `TOTAL` 96%.
- `npx cdk synth -q` with no AWS credentials writes `FlowStack.template.json` with one `EXPRESS` state machine and seven Lambdas.
- **Verify in AWS:** a `POST /api/ask` for E4 (stubs, then the real steps) returns an `AskResponse` within 29 s; the execution's graph shows every state; the Q09-style forced rejection (real steps, Huvison's eval asker) loops through `ReplanClaim` and lands in `RecordRejection`.

**Assumptions** (reconcile with the named owner before the PR):
- **Huvison (H2), the step contract below:** each `flow.steps.<name>` is a Lambda handler `(event: dict, context) -> dict` taking and returning exactly this JSON (validated against the C1 step models on the way in). If H2 chooses other keys, change the state's `payload` in `flow_stack.py` and the stub together, test-first.
- **`run_orchestrator` re-plans one claim** when given `replan_claim_id` (Patrick's P2 inside Huvison's step) and checks the budget itself (`flow.budget.require_budget`); an empty `claims` means "can't retry" and the claim is rejected.
- **Linus (L3):** `api.handlers.ask` builds the `Question` (scope from the token, `run_id`, budget and attempts from `config.py`) and calls `StartSyncExecution` with it; it returns the execution's `output` as the response. The Q11 refusal happens before any execution.
- **Huvison (timing):** a full `/ask` with one retry fits in API Gateway's **29 s** (H2/H6 measure it by D1 18:00). If it doesn't, §6 applies.
- Bedrock routes (from `aws bedrock get-inference-profile` in eu-west-1, 2026-10-14): `eu.anthropic.claude-sonnet-4-6` → `anthropic.claude-sonnet-4-6` in eu-north-1, eu-west-3, eu-south-1, eu-south-2, eu-west-1, eu-central-1; `eu.amazon.nova-lite-v1:0` → `amazon.nova-lite-v1:0` in eu-west-3, eu-west-1, eu-central-1, eu-north-1.
- **Handover deviation:** `docs/DEVOPS_HANDOVER.md` lists `bedrock:InvokeModel` only; Strands' `BedrockModel` streams (`ConverseStream`), which needs `bedrock:InvokeModelWithResponseStream` too. Tell Patrick to add it to the handover.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Per-claim loop | A `Map` over the stored claims; each iteration judges, retries and records on its own | One claim at a time in a loop of Choices (slower; harder to read) |
| Retry trigger | `Choice` on `$.retry.decision`, returned by `retry_decision` from the ledger counter | A model output; a counter kept in the state input (resettable, D-012) |
| Critic input | `{run_id, claim, scope}`, set explicitly in the `JudgeClaim` payload; a test asserts the keys | Passing the iteration's whole state (it carries the question) |
| Passed claims to the writer | JSONPath filter `$.judged[?(@.passed == true)].claim` in the `WriteAnswer` payload | Letting `write_answer` filter (puts flow logic in Huvison's function and hides it from the graph) |
| Express logs | Level `ALL` with execution data, 14 days | Errors only (the dashboard's cost per run reads the output; M4b) |
| Bedrock IAM | The two profile ARNs plus their EU foundation-model ARNs, both invoke actions | `bedrock:*`; `foundation-model/*`; `global.*` profiles |
| Stubs | `infra/functions/stub_steps.py` with the same JSON shapes, validated against the C1 models in tests | Waiting for H2 (no skeleton at D1 18:00) |

## 3. Step contract (the JSON each state passes)
| State (Lambda) | Function (H2) | Input JSON | Output JSON |
|---|---|---|---|
| `CheckBudget` | `flow.steps.check_budget` | a `Question` (`run_id`, `scope`, `entity_id`, `question`, `budget_usd`, `max_attempts`) | `{"question": Question, "partial": PartialAnswer \| null}` |
| `RunOrchestrator`, `ReplanClaim` | `flow.steps.run_orchestrator` | `{"question": Question, "replan_claim_id": str \| null}` | an `OrchestratorResult` (`plan`, `claims`, `partial`, `usage`); on a re-plan, `claims[0]` is the revised claim with the **same** `claim_id`, or `claims` is empty (budget spent) |
| `StoreClaims`, `StoreRevisedClaim` | `flow.steps.store_claims` | `{"run_id", "claims": [BlockerClaim]}` | `{"claims": [BlockerClaim]}` as stored |
| `JudgeClaim` | `flow.steps.judge_claim` | `{"run_id", "claim": BlockerClaim, "scope": Scope}` **only** (D-007: no question, plan or attempts) | `{"claim_id", "passed": bool, "verdict": Verdict}` |
| `RetryDecision` | `flow.steps.retry_decision` | `{"run_id", "claim_id"}` | `{"decision": "retry" \| "reject"}`, from `Ledger.attempts(...) < max_claim_attempts` |
| `RecordRejection` | `flow.steps.record_rejection` | `{"run_id", "claim_id"}` | any JSON (ignored) |
| `WriteAnswer`, `WritePartialAnswer` | `flow.steps.write_answer` | `{"run_id", "question": Question, "passed_claims": [BlockerClaim], "partial": PartialAnswer \| null}` | an `AskResponse` (C1, `tools/api_schema.py`): the machine's output |

## 4. Shapes and behaviour
- `infra.bedrock_access`: `MODEL_ROUTES`, `MODEL_INVOKE_ACTIONS`, `model_resource_arns(stack) -> list[str]`, `model_invoke_statement(stack) -> iam.PolicyStatement` (refuses a non-`eu.` profile).
- `infra.stacks.flow_stack`: `FlowStack(scope, id, *, data, ledger, guardrail, **kwargs)`; `FlowStep(name, runs_agents)`, `ASK_STEPS`, `STEPS_WITH_REAL_HANDLERS`, `FLOW_BUNDLE = BundleSpec("flow", (*CORE_CODE, "flow"))`, `DYNAMO_LEDGER_BACKEND`, timeouts (ledger steps 10 s, agent steps 60 s / 1024 MB), `ASK_SPINE_TIMEOUT` 2 min, `MAX_PARALLEL_JUDGEMENTS` 4.
- Environment: ledger steps `LEDGER_BACKEND=dynamo`, `LEDGER_TABLE`, `REJECTED_TABLE`; agent steps also `ARTEFACT_BACKEND=csv`, `ARTEFACTS_URI`, `GUARDRAIL_ID`, `GUARDRAIL_VERSION` (model IDs keep their `config.py` defaults).
- `ApiStack(scope, id, *, data, auth, flow, **kwargs)`: the `ask` function gets `ASK_STATE_MACHINE_ARN` and `flow.ask_start_statement()`.

## 5. Tests (new, in `tests/`)
- `tests/infra/test_bedrock_access.py` *(new)*: both actions, no wildcard; the two profile ARNs in eu-west-1; ten foundation-model ARNs, all in EU regions.
- `tests/infra/functions/test_stub_steps.py` *(new)*: the stubs' JSON validates as `Question`, `OrchestratorResult`, `BlockerClaim` and `AskResponse`; a re-plan keeps the claim ID; the stub never retries; a partial answer is reported.
- `tests/infra/stacks/test_flow_stack.py` *(new)*: Express, logs `ALL` with data, tracing; the state order; the retry Choice reads `$.retry.decision`; the critic's payload keys; the writer gets the filter; one function and one role per step; only agent steps get the Guardrail; the output exists.
- `tests/infra/stacks/test_api_stack.py` *(new)* (appended): only the ask function may `StartSyncExecution`, and it has `ASK_STATE_MACHINE_ARN`.

## 6. The 29-second limit and the async fallback (conditional)
API Gateway ends a synchronous integration at **29 s**. Huvison times a full `/ask` with one retry (H7, D1 18:00). **If the p95 is over 20 s** (D-023), the agreed fallback is: `POST /ask` starts the run and returns `run_id` at once; `GET /ask/{run_id}` polls for the stored `AskResponse`. That changes the API contract (a new route and response, C1), so it goes through Patrick as a decision first (D-023, raised by H7). The DevOps part, once decided, is small and gets its own short plan:
- the ask Lambda's statement becomes `states:StartExecution` (asynchronous Express) instead of `StartSyncExecution`;
- a seventh route `GET /ask/{run_id}` → `api.handlers.ask_result` (Linus) with `dynamodb:GetItem` on the ledger only;
- `write_answer` stores the `AskResponse` on the run in the ledger (Huvison).
Until that decision, this item keeps the synchronous path and records the measured time in the PR.

## 7. Out of scope
- The step functions themselves (Huvison, H2), the agents (Patrick, Linus), `api.handlers.ask` (Linus, L3).
- The publish flow (Y2b). AgentCore and the shim (Y3a, Y3b): here, agent steps run inside their Lambdas (the documented fallback path).
- The async `/ask` implementation (§6, only after D-023 records the async choice).

Related: [[Build order]], [[Yaw - DevOps]], [[Workstreams]]
