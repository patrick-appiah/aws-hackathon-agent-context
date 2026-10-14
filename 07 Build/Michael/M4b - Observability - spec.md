---
tags: [build, spec, area/devops]
id: M4b
owner: Michael
status: ready
updated: 2026-10-14
---
# M4b: Observability, log retention, traces and one dashboard (spec)
> **Split from M4** (the lead's rule). M4b is logs, traces and the dashboard; [[M4a - WebStack - spec]] is web hosting. Each is deployable and mergeable on its own. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop`; the stack and its tests can be built after [[M2 - App, DataStack and LedgerStack - spec]], the app wiring (Task 2) needs [[Y1 - ApiStack - spec]], [[Y2a - Express ask spine - spec]] and M4a merged.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] (`06 Workstreams/`): the architecture, the code already built, the contracts and the rules (§7).
3. [[Michael - DevOps]] (step 7, observability), [[Yaw - DevOps]] (the API, the ask spine, AgentCore), [[Huvison - trust and flow]] (§6 cost per run, §9 latency).
4. [[M2 - App, DataStack and LedgerStack - spec]] (patterns, `LOG_RETENTION`), [[Y1 - ApiStack - spec]] (`api.http_api`), [[Y2a - Express ask spine - spec]] (`flow.ask_state_machine`, `flow.ask_log_group`), [[M4a - WebStack - spec]] (the app fixture with a portal build).
5. [[Build order]]: M4b depends on M2, and on Y1, Y2a and M4a for the wiring.
6. `01 Decisions/`: [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]], [[2026-10-13 Default models]]; `05 Workflow/`: [[Deploy and demo checks]].

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Michael (owner), Yaw (the stacks it reads) or Huvison (cost). Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. An `ObservabilityStack` *(new)* with **one CloudWatch dashboard** `<prefix>-erp-portal`, three rows:
   - API latency (p50, p99) and errors (4xx, 5xx) of Yaw's HTTP API;
   - `/ask` run time (p50, p99) and outcomes (succeeded, failed, timed out) of the Express ask spine;
   - **cost per run** (a Logs Insights table over the ask spine's log group: `run_id`, `cost_usd` from each successful execution's output) and **Bedrock tokens by model** (`InputTokenCount`, `OutputTokenCount` for the two `eu.*` profiles in `config.py`).
2. **CloudWatch Transaction Search** (the prerequisite for AgentCore Observability's traces): an `AWS::XRay::TransactionSearchConfig` and the CloudWatch Logs resource policy that lets X-Ray write spans, **behind a context switch** `-c transaction_search=on|off` (default `on`), because the setting is account-wide and a second copy in the same account would collide.
3. **App-wide rules, tested:** every log group any stack declares keeps logs **14 days** (`LOG_RETENTION`) and is deleted with its stack; every state machine sends traces to X-Ray.

**Why:**
- [[Michael - DevOps]] step 7: "one `/ask` run is visible end to end (trace) with its cost". The dashboard is what the demo and the cost slide show; cost per run is part of `COST.md` "measured".
- Traces: the brief weighs "the agent loop genuinely runs"; AgentCore Observability shows each agent's spans only when Transaction Search is on.
- Retention: log groups without a retention policy keep data forever and cost; a two-day event needs two weeks at most.

**Success means:**
- `uv run --locked pytest` → **15 more tests** than before M4b (dry-run with stand-ins for Y1 and Y2a: 257 → 272), `TOTAL` 96%.
- `npx cdk synth -q` succeeds with no credentials; with `-c transaction_search=off` the Observability template has no `TransactionSearchConfig`.
- **Verify in AWS:** the dashboard `demo-erp-portal` exists; after one `/ask` run its cost table shows that run's `run_id` and `cost_usd`; `aws xray get-trace-segment-destination` → `CloudWatchLogs` / `ACTIVE`; the run's trace is visible in CloudWatch.

**Assumptions** (reconcile with the named owner before the PR):
- **Yaw (Y1):** `api.http_api` is an `aws_apigatewayv2.HttpApi`; its standard `AWS/ApiGateway` metrics (`Latency`, `4xx`, `5xx` by `ApiId`) are what the dashboard reads.
- **Yaw (Y2a):** `flow.ask_state_machine` is the **Express** ask spine and `flow.ask_log_group` its log group, with logging level `ALL` and `include_execution_data=True`, `tracing_enabled=True`, and the group created with `retention=LOG_RETENTION` and `RemovalPolicy.DESTROY`. Its successful execution's output is the C1 `AskResponse` JSON (with `run_id` and `cost_usd`). The app-wide tests in Task 2 enforce the tracing and retention parts.
- **Yaw (Y1, Y3):** every log group his stacks declare uses `LOG_RETENTION` and `DESTROY` (enforced by the same test), and his Lambdas and the AgentCore runtime have tracing / observability switched on where they are created (Y3 enables AgentCore observability on the runtime; M4b only turns Transaction Search on).
- **Huvison (H5):** `cost_usd` in `AskResponse` is the run's real cost (`flow/cost.py` *(new)*). The dashboard shows what the spine returns; it doesn't compute cost.
- **Bedrock metrics:** the `AWS/Bedrock` `ModelId` dimension carries the inference-profile IDs the agents call (`eu.anthropic.claude-sonnet-4-6`, `eu.amazon.nova-lite-v1:0`). **Verify in AWS** after the first run; if the dimension differs, change only `BEDROCK_MODEL_IDS`' source.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Cost per run source | Logs Insights over the Express log group: `filter type = "ExecutionSucceeded"`, `parse details.output` for `run_id` and `cost_usd` | Reading the DynamoDB ledger (a dashboard can't query DynamoDB); a custom metric from H5 (new code in another workstream) |
| Tokens | `AWS/Bedrock` `InputTokenCount` / `OutputTokenCount` per model ID, summed | Parsing each state's `usage` list from logs (a regex reads only the first entry per event) |
| `/ask` latency | The ask spine's `ExecutionTime` p50/p99 (what the user waits for, minus API overhead) plus the API's overall `Latency` | Per-route API metrics (need detailed metrics on the stage, Y1's setting) |
| Transaction Search | `CfnTransactionSearchConfig` (indexing 1%, the free tier) + `CfnResourcePolicy` for `aws/spans` and `/aws/application-signals/data`, behind `-c transaction_search=on|off` | Turning it on by hand (clean-deploy gate); always on (the second copy in the same account fails) |
| Switch values | `on` / `off` / not given (= `on`); anything else raises `ValueError` | Truthy strings (`yes`, `1`): a typo would silently pick a side |
| Retention rule | An app-wide test: every `AWS::Logs::LogGroup` in every stack has `RetentionInDays: 14` and `DeletionPolicy: Delete` | A CDK Aspect that rewrites log groups (hides mistakes instead of showing them) |
| Tracing rule | An app-wide test: every `AWS::StepFunctions::StateMachine` has `TracingConfiguration: {Enabled: true}` | Trusting each stack (Y2a, Y2b) to remember |
| Names | Dashboard `<prefix>-erp-portal`; policy `<prefix>-erp-portal-xray-spans` | Fixed names (the second copy collides) |

## 3. Exact shapes
**`infra/constants.py` *(new)* additions:**
| Name | Value |
|---|---|
| `DASHBOARD_BASE_NAME` | `"erp-portal"` |
| `DASHBOARD_DEFAULT_HOURS` | `3` |
| `COST_TABLE_ROWS` | `20` |
| `TRANSACTION_SEARCH_CONTEXT_KEY` | `"transaction_search"` |
| `SWITCH_ON` / `SWITCH_OFF` | `"on"` / `"off"` |
| `TRANSACTION_SEARCH_INDEXING_PERCENT` | `1` |
| `XRAY_SPANS_POLICY_BASE_NAME` | `"erp-portal-xray-spans"` |

**`infra/stacks/observability_stack.py` *(new)*:**
- `transaction_search_switch(context_value: object) -> bool`.
- `ObservabilityStack(scope, construct_id, *, prefix: str, http_api: apigwv2.IHttpApi, ask_state_machine: sfn.IStateMachine, ask_log_group: logs.ILogGroup, transaction_search: bool, **kwargs)`; output `DashboardName`.
- Module constants: `MEDIAN = "p50"`, `TAIL = "p99"`, `TOTAL = "Sum"`, `BEDROCK_NAMESPACE`, `BEDROCK_MODEL_IDS = (config.DEFAULT_REASONING_MODEL, config.DEFAULT_RETRIEVAL_MODEL)`, `TOKEN_METRICS`, `COST_PER_RUN_QUERY` (7 lines), `XRAY_SPAN_LOG_GROUPS`, `IAM_POLICY_VERSION`.

**The cost query:**
```
fields @timestamp | filter type = "ExecutionSucceeded" | parse details.output /"run_id":\s*"(?<run_id>[^"]+)"/ | parse details.output /"cost_usd":\s*(?<cost_usd>[0-9.]+)/ | display @timestamp, run_id, cost_usd | sort @timestamp desc | limit 20
```

**`infra/app.py` *(new)*:** `PortalStacks.observability: ObservabilityStack`, built last (after `web`), with `transaction_search=transaction_search_switch(app.node.try_get_context(TRANSACTION_SEARCH_CONTEXT_KEY))`.

## 4. Tests (15 new)
- `tests/infra/stacks/test_observability_stack.py` *(new)*, 11 (stand-in HTTP API, Express state machine and log group): one dashboard named `test-erp-portal`; API `Latency`, `4xx`, `5xx`; `ExecutionTime`, `ExecutionsSucceeded`, `ExecutionsFailed`, `ExecutionsTimedOut`; the cost query (`ExecutionSucceeded`, `cost_usd`, `run_id`); both model IDs and both token metrics; Transaction Search + the policy when on; neither when off; the switch reads `None`/`on`/`off` (3 cases) and refuses `yes`.
- `tests/infra/test_app.py` *(new)*, 4 added: every log group 14 days and `Delete`; every state machine traced; the dashboard depends on the API and Flow stacks; a second copy with `transaction_search=off` has no `TransactionSearchConfig`.

## 5. Out of scope
- Tracing on Lambdas and the AgentCore runtime's observability settings (Yaw, where each is created).
- Alarms and notifications (no on-call for a two-day event).
- Computing cost (Huvison H5) or writing `COST.md` (Abdul A3).

Related: [[M4b - Observability - plan]], [[Build order]], [[Michael - DevOps]]
