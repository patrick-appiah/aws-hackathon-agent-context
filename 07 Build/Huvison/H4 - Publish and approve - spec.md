---
tags: [build, spec, area/flow]
id: H4
owner: Huvison
status: awaiting review
updated: 2026-10-14
---
# H4: Publish and approve, the only write behind a human (spec)
> **The status pack is the system's only write, and it happens only after a delivery lead approves.** Linus's `/publish` and `/approve` (L3) call `start_publish` and `decide`; Yaw's Standard state machine (Y2) runs the two Lambdas `store_task_token` and `write_status_pack`. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` once H1 and **H2b** are merged (H4 adds its Lambdas to H2b's `flow/handlers.py` *(new)*). The repo is the source of truth for code; the vault is the source of context.

## 0. Context: read the vault first
The team vault is the shared context space for this project. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Workstreams]] §2 (`POST /publish, /approve`), §6 (hard gate 3: human approval before the only write) and §7.
3. [[Huvison - trust and flow]] §5 "Publish and approve": the owner's brief.
4. [[Build order]]: H4 depends on C1 and H1; this plan also needs **H2b** (`flow/handlers.py`). Check they are `merged`.
5. [[H1 - Ledger extensions - spec]] (`put_task_token`, `task_token`, `record_decision`, `claims`, `rejected`), [[C1 - API and spine contracts - spec]] §3 (`PublishResponse`, `ApproveResponse`) and §5 (`publish_state_machine_arn`, `artefacts_bucket`, `status_pack_prefix`).
6. Linus's [[L3 - Ask, publish and approve entry points - spec]]: how the API calls these functions and maps their errors.
7. `01 Decisions/`: [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]], [[2026-10-13 Team are admins, workload roles least-privilege]]; the repo's `docs/DEVOPS_HANDOVER.md` (the `status-packs/*` write is the publish writer's only).

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` ([[Hackathon guideline]] non-negotiable 3: "Writes go behind a human approval step. Step Functions `waitForTaskToken`"; the "sent back" edge: "write each return to the same ledger"), `03 Sessions/`, `Open follow-ups.md`. If the vault doesn't answer it, stop and ask Huvison. Never invent a name, a shape or a rule.

## 1. Intent
**What:** `flow/publish.py` *(new)*:
- `start_publish(run_id, requester, *, ledger=None, stepfunctions=None, state_machine_arn=None) -> PublishResponse`: starts the Standard execution, named after the run, for a run the requester asked and that has at least one verified claim;
- `store_task_token(run_id, task_token, ledger)`: the machine's first state (`.waitForTaskToken`) keeps the token, create-once, by `run_id`;
- `decide(run_id, decision, note, approver, *, ledger=None, stepfunctions=None) -> ApproveResponse`: only a `delivery_lead` of the run's tenant; logs the decision on the run first; `approve` → `SendTaskSuccess`, `send_back` → `SendTaskFailure`;
- `status_pack(run_id, ledger) -> dict` and `write_status_pack(run_id, *, ledger, s3, bucket, prefix) -> str`: the machine's last state writes `s3://<ARTEFACTS_BUCKET>/<STATUS_PACK_PREFIX><run_id>.json`, **only if the run's last decision is an approval** (checked in the ledger, again);
- errors that L3 maps: `PublishForbidden` (`PermissionError` → 403), `RunNotFound` and `NoPendingApproval` (`KeyError` → 404), `NothingToPublish` (`ValueError` → 400), `PublishNotConfigured` (`RuntimeError` → 500).

Plus two Lambda entry points in `flow/handlers.py`: `store_task_token(event, context)` and `write_status_pack(event, context)`, and the publish rows of `docs/DEVOPS_HANDOVER.md`.

**Why:** hard gate 3 (Workstreams §6): human approval before the only write; the guideline's non-negotiable 3. Keying by `run_id` is C1's decision (`/approve` takes `run_id`). The sent-back edge is logged so a draft that's been sent back is visible (guideline).

**Success means:**
- `start_publish` starts one execution named `run_id` with input `{"run_id"}` and returns `awaiting_approval`; it refuses anyone but the user who asked (`PublishForbidden`), an unknown run (`RunNotFound`), a run with no passed claim (`NothingToPublish`) and a missing state-machine ARN (`PublishNotConfigured`), all before any AWS call.
- The task token is stored once; a second one is refused.
- A delivery lead's `approve` sends `SendTaskSuccess` with the token and logs `{decision, note, user_id, decided_at}` on the run; `send_back` sends `SendTaskFailure` (`error="SentBack"`, `cause=note`) and logs it.
- A CFO, an entity lead or a delivery lead of another tenant is refused, with nothing sent and nothing logged; a decision before the token is stored, or a second decision, raises `NoPendingApproval`; an unknown decision raises `ValueError`.
- No status pack is written without an approval, including after a send-back; after an approval exactly one object `status-packs/<run_id>.json` holds the verified findings with their citations, what could not be verified, the cost, who approved and the note.
- `uv run --locked pytest`: start + **17 passed**; coverage not lower. No real AWS: Step Functions through a recording fake, S3 through moto.

**Assumptions:**
- **Linus (L3)** calls `start_publish(run_id, scope)` and `decide(run_id, decision, note, scope)` positionally with the token's `Scope`, and maps `PermissionError` → 403 `forbidden`, `KeyError` → 404 `not_found` ([[L3 - Ask, publish and approve entry points - plan]], `FakePublishFlow`). It should also map `ValueError` → 400 `invalid_input` (L1/L2 already do for bad input) and let `RuntimeError` fail the Lambda (500).
- **Yaw (Y2)** builds the Standard machine below; its Lambdas are `flow.handlers:store_task_token` and `flow.handlers:write_status_pack`; the `approve` / `publish` Lambdas (Linus's) need `states:StartExecution`, `SendTaskSuccess`, `SendTaskFailure` on it; only `write_status_pack` gets `s3:PutObject` on `<bucket>/status-packs/*`.
- **Michael (M2)** creates the bucket; `ARTEFACTS_BUCKET` and `STATUS_PACK_PREFIX` reach the Lambdas as environment variables.
- A sent-back run is finished: asking again starts a new run (guideline: "sent back → orchestrator"). The execution name is the `run_id`, so the same run can't be published twice.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Who may publish | The user who asked the run (same `user_id` and tenant) | Anyone in the tenant (publishing another user's answer) |
| What may be published | A run with at least one claim the ledger marks passed | An empty pack |
| Who may approve | Role `delivery_lead` and the run's tenant | Any role; the requester themselves |
| One decision per publish | `decide` refuses when the run already has a decision (and AWS refuses a reused token anyway) | Letting a second decision overwrite the first in the log |
| Order in `decide` | Log the decision, then call Step Functions, so the last state's ledger check can't race the log | Call first (the writer could run before the approval is in the ledger) |
| Second check before the write | `write_status_pack` refuses unless the run's last decision is `approve` | Trusting that the machine only reaches the state after success |
| What the pack holds | Built from the ledger: verified findings (statement + citations), could-not-verify list, cost, tenant, approver, time, note; JSON, sorted keys | The writer's wording (not stored in the ledger; the claims are what the critic passed) |
| Step Functions in tests | A recording fake client (`start_execution`, `send_task_success`, `send_task_failure`) | moto's Step Functions (task-token calls not needed to prove our logic; the fake shows the exact requests) |
| AWS clients | Created on first use (`boto3` imported inside the function), injectable | Module-level clients (tests would need AWS settings at import) |
| Error types | Subclasses of the built-ins L3 already maps (`PermissionError`, `KeyError`, `ValueError`) | New error codes in the API contract |

## 3. Shapes and behaviour (`flow/publish.py`)
Constants: `APPROVER_ROLE = "delivery_lead"`, `DECISION_APPROVE = "approve"`, `DECISION_SEND_BACK = "send_back"`, `DECISIONS`, `STATUS_AWAITING_APPROVAL = "awaiting_approval"`, `STATUS_BY_DECISION = {"approve": "approved", "send_back": "sent_back"}`, `SENT_BACK_ERROR = "SentBack"`, `SENT_BACK_DEFAULT_CAUSE`, `STATUS_PACK_SUFFIX = ".json"`, `JSON_CONTENT_TYPE = "application/json"`, `JSON_INDENT = 2`.

| Function | Signature | Behaviour |
|---|---|---|
| `start_publish` | `(run_id: str, requester: Scope, *, ledger: Ledger \| None = None, stepfunctions=None, state_machine_arn: str \| None = None) -> PublishResponse` | §1; `None` → `ledger_from_settings()`, a boto3 client in `aws_region`, `publish_state_machine_arn` |
| `store_task_token` | `(run_id: str, task_token: str, ledger: Ledger) -> None` | `ledger.put_task_token` |
| `decide` | `(run_id: str, decision: str, note: str, approver: Scope, *, ledger: Ledger \| None = None, stepfunctions=None) -> ApproveResponse` | §1 |
| `status_pack` | `(run_id: str, ledger: Ledger) -> dict` | keys `run_id`, `tenant_id`, `approved_by`, `approved_at`, `note`, `findings[{claim_id, statement, citations[{artefact, row_id}]}]`, `could_not_verify[{claim_id, statement}]`, `cost_usd` |
| `write_status_pack` | `(run_id: str, *, ledger: Ledger, s3, bucket: str \| None, prefix: str) -> str` | refuses without an approval (`PublishForbidden`) or a bucket (`PublishNotConfigured`); `put_object(Bucket, Key=<prefix><run_id>.json, Body, ContentType)`; returns the key |

**Lambdas** (`flow/handlers.py`): `store_task_token({run_id, task_token}) -> {}`; `write_status_pack({run_id}) -> {bucket, key}` (bucket and prefix from settings via `status_pack_location()`, S3 client via `make_s3()`).

**The Standard machine, for Yaw (Y2):** `StoreTaskToken`: Lambda `flow.handlers:store_task_token`, resource `arn:aws:states:::lambda:invoke.waitForTaskToken`, payload `{"run_id.$": "$.run_id", "task_token.$": "$$.Task.Token"}`, `Catch` `States.TaskFailed` (the `SentBack` failure) → `SentBack` (a `Succeed` or `Fail` state; the decision is already in the ledger) → on success `WriteStatusPack`: Lambda `flow.handlers:write_status_pack` with `{"run_id.$": "$.run_id"}` → end. Execution name = `run_id`.

## 4. Tests (new)
- `tests/flow/test_publish.py` *(new)*, 15: start (execution named after the run, exact request); only the asker may publish; nothing to publish and unknown run; no ARN; the token kept once; a delivery lead approves (exact `send_task_success` request, decision logged); send back (exact `send_task_failure`, logged); CFO, entity lead and other-tenant delivery lead refused (×3) with nothing sent or logged; nothing to decide before the token or after a decision; unknown decision or run; the error types L3 maps; no pack without approval (also after a send-back; bucket empty); an approved run writes exactly its pack under the prefix with findings and citations, and refuses without a bucket.
- `tests/flow/test_handlers.py` *(new)* (appended, 2): the publish Lambdas store the token and write only after approval; the bucket and prefix come from settings.

## 5. Out of scope
- The `/publish` and `/approve` HTTP handlers (Linus, L3) and the front end (Clement, F5).
- The Standard machine's CDK (Yaw, Y2) and the bucket (Michael, M2).
- Notifying the approver (email, Slack): roadmap.

Related: [[H4 - Publish and approve - plan]], [[Huvison - trust and flow]], [[Build order]]
