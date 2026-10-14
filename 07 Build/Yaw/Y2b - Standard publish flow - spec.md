---
tags: [build, spec, area/devops]
id: Y2b
owner: Yaw
status: ready
updated: 2026-10-14
---
# Y2b: the Standard publish flow with human approval (spec)
> **Split from Y2.** [[Y2a - Express ask spine - spec]] is the ask spine; Y2b adds the **Standard** publish state machine (`waitForTaskToken`) to the same `FlowStack`, and the `/publish` and `/approve` wiring. Deployable and mergeable on its own after Y2a. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after Y2a is merged.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] (`06 Workstreams/`): the architecture with owners, the code already built, the contracts and the rules (§7).
3. [[Yaw - DevOps]]: the owner's brief; and [[Michael - DevOps]] (the other half of DevOps).
4. [[Build order]]: what this item depends on and unblocks.
5. [[M2 - App, DataStack and LedgerStack - spec]]: the CDK app, `build_stacks`, the prefix, the test fixtures and the patterns every DevOps item follows.
6. [[Y2a - Express ask spine - spec]] (FlowStack, the stub pattern) and [[Y1 - ApiStack - spec]] (the routes, `PortalFunction`).
7. [[Huvison - trust and flow]] §5 (publish and approve: `start_publish`, `decide`, the task token keyed by `run_id`, the status pack) and [[Linus - API, identity, blocker-analyst]] (the `/publish` and `/approve` entry points).
8. `01 Decisions/`: [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]], [[2026-10-13 Team are admins, workload roles least-privilege]]; hard gate 3 in [[Workstreams]] §6 (human approval before the only write).

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Yaw (owner) or Huvison (the publish functions). Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. A **Standard** state machine `Publish` in `FlowStack`: `WaitForApproval` (Lambda `store_task_token`, **`waitForTaskToken`**, 48-hour timeout) → `WriteStatusPack` (Lambda `write_status_pack`) → `Published`. `SendTaskFailure` with error **`SentBack`** ends at `SentBack` (a Succeed, nothing written); a timeout ends at `ApprovalTimedOut` (Fail).
2. Two Lambdas (`PortalFunction`): `store_task_token` (ledger `GetItem`/`PutItem`/`UpdateItem` on the **ledger table only**) and `write_status_pack` (the same, plus **`s3:PutObject` on `status-packs/*` only**: the system's only write). Stubs first (`infra/functions/stub_publish.py` *(new)*: store nothing, write nothing), then Huvison's `flow.publish.*` (`PUBLISH_STEPS_WITH_REAL_HANDLERS`).
3. **API wiring:** `/publish` gets `PUBLISH_STATE_MACHINE_ARN`, `LEDGER_BACKEND=dynamo`, `LEDGER_TABLE`, `states:StartExecution` on this machine and `dynamodb:GetItem` on the ledger; `/approve` gets the same settings, `states:SendTaskSuccess` + `SendTaskFailure` on this machine, and `GetItem` + `UpdateItem` on the ledger. `API_BUNDLE` gains `flow/` (the handlers call `flow.publish`).
4. Output `PublishStateMachineArn`; attributes `.publish_state_machine`, `.publish_log_group`, `.publish_functions`, `.publish_start_statement()`, `.publish_decision_statement()`.

**Why:** hard gate 3, "human approval before the only write": the status pack is written only after a delivery lead approves (Huvison's `decide` checks the role). Standard, not Express, because a human may take hours.

**Success means:**
- `uv run --locked pytest` → **S + 8 passed** (dry-run 257 → **265**), `TOTAL` 96%.
- `npx cdk synth -q` with no credentials writes a `FlowStack.template.json` with one `STANDARD` and one `EXPRESS` machine.
- **Verify in AWS:** a publish execution waits at `WaitForApproval`; `send-task-success` moves it to `Published`; `send-task-failure --error SentBack` ends at `SentBack`; after H4, `POST /api/publish` then `POST /api/approve` as the delivery lead puts `s3://<bucket>/status-packs/<run_id>.json`, and nothing appears before the approval.

**Assumptions** (reconcile with the named owner before the PR):
- **Huvison (H4):** `flow.publish` exposes two more Lambda handlers besides `start_publish` and `decide`: **`store_task_token(event, context)`** with `event = {"run_id", "task_token"}` (calls `Ledger.put_task_token`) and **`write_status_pack(event, context)`** with `event = {"run_id", "approval"}` (writes `<status_pack_prefix><run_id>.json` to `artefacts_bucket`). The handover calls the second one "the status-pack writer"; the names are this spec's proposal.
- **Huvison (H4):** `start_publish` starts the machine with input `{"run_id", "requested_by"}`; `decide` answers with `SendTaskSuccess(output = {"decision": "approve", "note", "approver"})` or `SendTaskFailure(error = "SentBack")`, and logs a send-back on the run in the ledger (hence `UpdateItem` for `/approve`: **a deviation from the handover**, which lists `GetItem` only; tell Patrick).
- **Linus (L3):** `api.handlers.publish` / `approve` call `flow.publish.start_publish` / `decide` and read settings through `config.get_settings()` (`publish_state_machine_arn`, `ledger_table`, `ledger_backend`).
- The status-pack writer needs no artefacts read (the handover gives it `LEDGER_TABLE`, `ARTEFACTS_BUCKET`, `STATUS_PACK_PREFIX` only); `STATUS_PACK_PREFIX` keeps its `config.py` default `status-packs/`, which is also the IAM prefix.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Machine type | Standard, `waitForTaskToken`, 48 h task timeout | Express (5-minute limit); polling the ledger in a loop |
| Where the token lives | The ledger (`sk=TASK`, Huvison H1), written by the first state | An extra table; the execution ARN as the key (C1 decided `run_id`) |
| Send-back | `SendTaskFailure` with error `SentBack`, caught to a `Succeed` state | A Fail state (send-back is a normal outcome, not an error) |
| Write permission | `s3:PutObject` on `status-packs/*`, on the writer's role only | `grant_write` on the bucket; the writer reading `artefacts/` |
| `/approve` ledger access | `GetItem` + `UpdateItem` on the ledger table only | The rejected-records table; `PutItem` |
| Same stack as the ask spine | Yes, `FlowStack` (both flows share the step bundle and the ledger) | A separate `PublishStack` (one more stack for two functions) |

## 3. Tests (new, in `tests/`)
- `tests/infra/functions/test_stub_publish.py` *(new)*: the stubs store and write nothing.
- `tests/infra/stacks/test_publish_flow.py` *(new)*: a Standard machine with tracing; `WaitForApproval` uses `lambda:invoke.waitForTaskToken`, passes `$$.Task.Token`, waits 48 h, then `WriteStatusPack`; `SentBack` and `States.Timeout` are caught; only one policy has `s3:PutObject`, on `/status-packs/*`; the output exists; `/publish` alone may `StartExecution`, `/approve` alone may `SendTaskSuccess`, both with the ledger settings.
- `tests/infra/test_bundling.py` *(new)* (appended): the API bundle carries `flow/publish.py` *(new)*.

## 4. Out of scope
- `flow/publish.py` (Huvison, H4), the handlers (Linus, L3), the portal's publish screens (Clement, F5).
- The status-pack format and the approval role check (Huvison's `decide`).

Related: [[Build order]], [[Yaw - DevOps]], [[Workstreams]]
