---
tags: [build, plan, area/flow]
id: H4
owner: Huvison
spec: "[[H4 - Publish and approve - spec]]"
status: ready
updated: 2026-10-14
---
# H4: Publish and approve (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[H4 - Publish and approve - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; ledger the conflict.
3. [[Huvison - trust and flow]] §5; [[H1 - Ledger extensions - spec]]; [[H2b - Agent states, local spine and Lambda handlers - spec]] §3 (`infra/functions/states.py` *(new)*); Linus's [[L3 - Ask, publish and approve entry points - spec]].
4. [[Handling security findings]], [[Working with AI assistants]].
5. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Huvison.

**Goal:** publish starts a Standard execution that waits on a task token stored by `run_id`; only a delivery lead's approval releases it; only then is the status pack written to `status-packs/`.

**Architecture:** `infra/functions/publish.py` holds the four functions and the errors; AWS clients are injected (tests) or created on first use. The two machine Lambdas are thin wrappers in `infra/functions/states.py`.

**Tech stack:** Python 3.11, boto3 (lazy), moto 5 for S3, a recording fake for Step Functions, pytest, uv.

**Dry-run status:** every step ran in a throwaway worktree of C1 + H1 + H5 + H3 + H2a + H2b (P1's `agent_support` as a stand-in). No real AWS. The machine itself is Yaw's: its behaviour is **verify in AWS** (Task 5, Step 6).

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: `feature/publish-approve` from an up-to-date `develop` after **H1 and H2b** are merged.
- **Start state:** the dry-run's start was **297 passed**, `TOTAL` 98%. Write your real number in the ledger file; the **deltas** must match (+4, +9, +2, +2).
- **Rules:** `eu-west-1` only; synthetic data; **no secrets** (tests use moto and the fake credential `testing`). Settings only in `config.py`; domain constants only in `tools/constants.py`; descriptive names, no single-character names, no magic numbers. The core imports no boto3. **Never write the status pack before approval; never let anyone but a delivery lead of the run's tenant approve.** Never weaken a security rule. Tests in `tests/` mirroring the code; coverage must not drop; no layout or meta guard tests; no real AWS call in a test. Stay in your folders: `infra/functions/publish.py`, `infra/functions/states.py`, `tests/infra/functions/` *(new)*, and the doc lines in Task 5.
- **Commits:** one per task, the given messages, **no attribution lines**. Never push to `develop` or `main`.

## Review Focus
1. **Two locks on the write:** the machine reaches `WriteStatusPack` only after `SendTaskSuccess`, and `write_status_pack` itself refuses unless the ledger's last decision is `approve`. Read both paths.
2. **Every refusal happens before any AWS call** (`start_publish`, `decide`): check the order of the checks against the client calls.
3. **The decision is logged before the token is used**, so the write's ledger check can't race it.
4. **IAM (verify in AWS with Yaw):** only the `write_status_pack` Lambda has `s3:PutObject`, and only on `<bucket>/status-packs/*`; only the `approve` Lambda can `SendTaskSuccess`/`SendTaskFailure`.
5. **L3's error mapping:** `PublishForbidden` → 403, `RunNotFound`/`NoPendingApproval` → 404, `NothingToPublish` → 400. Check L3's `ERROR_MAP` once both are merged.

---

### Task 1: `start_publish` and the errors

**Files:** Create `infra/functions/publish.py` *(new)*, `tests/infra/functions/test_publish.py` *(new)*

**Produces:** in `infra.functions.publish`: the constants of spec §3; `PublishForbidden(PermissionError)`, `NothingToPublish(ValueError)`, `RunNotFound(KeyError)`, `NoPendingApproval(KeyError)`, `PublishNotConfigured(RuntimeError)`; `start_publish(run_id: str, requester: Scope, *, ledger: Ledger | None = None, stepfunctions=None, state_machine_arn: str | None = None) -> PublishResponse`. **Consumes:** `Ledger.run`, `claims` (H1); `adapters.ledger_from_settings`; `config.get_settings` (`publish_state_machine_arn`, `aws_region`); `tools.api_schema.PublishResponse` (C1). **Consumed by:** L3 (`infra.functions.api.publish`).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/publish-approve
mkdir -p .superpowers && printf '# Ledger: H4 Publish and approve\n' > .superpowers/ledger-H4.md
```
Expected: your start count, `TOTAL ... 98%`.
- [ ] **Step 2: Failing tests.** Create `tests/infra/functions/test_publish.py`:
```python
"""Publish and approve (infra/functions/publish.py): the only write, behind a delivery lead's approval (D-011)."""
import json

import pytest

from adapters.memory_ledger import InMemoryLedger
from config import DEFAULT_TENANT_ID
from infra.functions.publish import NothingToPublish, PublishForbidden, PublishNotConfigured, RunNotFound, start_publish
from tools.constants import ALL_ENTITIES_WILDCARD
from tools.models import Scope

RUN_ID = "run-publish"
STATE_MACHINE_ARN = "arn:aws:states:eu-west-1:000000000000:stateMachine:publish"
TASK_TOKEN = "example-task-token"
BUCKET = "test-artefacts"
STATUS_PACK_PREFIX = "status-packs/"
PASSED_CLAIM = {"claim_id": "claim-1", "statement": "E4 is blocked by open defect DEF-0412",
                "chain": [{"artefact": "defect_log", "row_id": "DEF-0412", "role_in_chain": "cause"}]}
DELIVERY_LEAD = Scope(user_id="user-delivery-lead", role="delivery_lead", tenant_id=DEFAULT_TENANT_ID,
                      entity_ids=(ALL_ENTITIES_WILDCARD,))


class FakeStepFunctions:
    """Records the Step Functions calls infra/functions/publish.py makes (no AWS in unit tests)."""

    def __init__(self):
        self.calls = []

    def start_execution(self, **request):
        self.calls.append(("start_execution", request))
        return {"executionArn": f"{STATE_MACHINE_ARN.replace('stateMachine', 'execution')}:{request['name']}"}

    def send_task_success(self, **request):
        self.calls.append(("send_task_success", request))

    def send_task_failure(self, **request):
        self.calls.append(("send_task_failure", request))


@pytest.fixture
def ledger(cfo_scope):
    ledger = InMemoryLedger()
    ledger.start_run(RUN_ID, cfo_scope, budget_usd=0.5)
    ledger.put_claim(RUN_ID, PASSED_CLAIM)
    ledger.record_verdict(RUN_ID, "claim-1", {"claim_id": "claim-1", "pass": True, "reason": "supported"})
    return ledger


@pytest.fixture
def stepfunctions():
    return FakeStepFunctions()


def publish(ledger, stepfunctions, requester):
    return start_publish(RUN_ID, requester, ledger=ledger, stepfunctions=stepfunctions,
                         state_machine_arn=STATE_MACHINE_ARN)


def test_start_publish_starts_one_execution_named_after_the_run(ledger, stepfunctions, cfo_scope):
    response = publish(ledger, stepfunctions, cfo_scope)
    assert (response.run_id, response.status) == (RUN_ID, "awaiting_approval")
    assert response.execution_arn.endswith(f":{RUN_ID}")
    assert stepfunctions.calls == [("start_execution", {"stateMachineArn": STATE_MACHINE_ARN, "name": RUN_ID,
                                                        "input": json.dumps({"run_id": RUN_ID})})]


def test_only_the_user_who_asked_may_publish_the_run(ledger, stepfunctions):
    with pytest.raises(PublishForbidden):
        publish(ledger, stepfunctions, DELIVERY_LEAD)
    assert stepfunctions.calls == []


def test_a_run_without_a_passed_claim_has_nothing_to_publish(stepfunctions, cfo_scope):
    ledger = InMemoryLedger()
    ledger.start_run(RUN_ID, cfo_scope, budget_usd=0.5)
    with pytest.raises(NothingToPublish):
        publish(ledger, stepfunctions, cfo_scope)
    with pytest.raises(RunNotFound):
        start_publish("run-unknown", cfo_scope, ledger=ledger, stepfunctions=stepfunctions,
                      state_machine_arn=STATE_MACHINE_ARN)


def test_publishing_without_a_state_machine_fails_loudly(ledger, stepfunctions, cfo_scope):
    with pytest.raises(PublishNotConfigured):
        start_publish(RUN_ID, cfo_scope, ledger=ledger, stepfunctions=stepfunctions, state_machine_arn=None)
```
- [ ] **Step 3: Run:** `uv run --locked pytest tests/infra/functions/test_publish.py --no-cov 2>&1 | grep -E "^E  " | head -1`. Expected: `E   ModuleNotFoundError: No module named 'infra.functions.publish'`.
- [ ] **Step 4: Implement.** Create `infra/functions/publish.py`:
```python
"""Publish and approve: the only write in the system, behind a human approval (D-011, non-negotiable #3).

    POST /publish -> start_publish: starts the Standard state machine. Its first state, store_task_token, is a
        `.waitForTaskToken` Lambda that stores the token by run ID (Ledger.put_task_token); the machine then waits.
    POST /approve -> decide: only a delivery lead of the run's tenant. The decision is logged on the run first;
        approve -> SendTaskSuccess, and the machine's last state, write_status_pack, writes
        s3://<ARTEFACTS_BUCKET>/<STATUS_PACK_PREFIX><run_id>.json; send_back -> SendTaskFailure (the run ends).
write_status_pack checks the ledger for the approval itself, so nothing reaches S3 without one.
Linus's infra/functions/api.py calls start_publish and decide; the machine's Lambdas are infra/functions/states.py.
"""
import json
from datetime import datetime, timezone

from adapters import ledger_from_settings
from config import get_settings
from tools.api_schema import ApproveResponse, PublishResponse
from tools.constants import ClaimStatus
from tools.models import Scope
from tools.ports import Ledger, LedgerConflict

APPROVER_ROLE = "delivery_lead"
DECISION_APPROVE = "approve"
DECISION_SEND_BACK = "send_back"
DECISIONS = (DECISION_APPROVE, DECISION_SEND_BACK)
STATUS_AWAITING_APPROVAL = "awaiting_approval"
STATUS_BY_DECISION = {DECISION_APPROVE: "approved", DECISION_SEND_BACK: "sent_back"}
SENT_BACK_ERROR = "SentBack"
SENT_BACK_DEFAULT_CAUSE = "sent back without a note"
STATUS_PACK_SUFFIX = ".json"
JSON_CONTENT_TYPE = "application/json"
JSON_INDENT = 2


class PublishForbidden(PermissionError):
    """The user may not publish or approve this run (API: 403 forbidden)."""


class NothingToPublish(ValueError):
    """The run has no claim the critic passed (API: 400 invalid_input)."""


class RunNotFound(KeyError):
    """No run with this ID in the ledger (API: 404 not_found)."""


class NoPendingApproval(KeyError):
    """No publish of this run is waiting for a decision, or it was already decided (API: 404 not_found)."""


class PublishNotConfigured(RuntimeError):
    """PUBLISH_STATE_MACHINE_ARN or ARTEFACTS_BUCKET is not set (a deployment error, API: 500)."""


def _stepfunctions_client():
    import boto3  # only where AWS is really called; tests pass a fake
    return boto3.client("stepfunctions", region_name=get_settings().aws_region)


def _run(ledger: Ledger, run_id: str) -> dict:
    try:
        return ledger.run(run_id)
    except LedgerConflict as error:
        raise RunNotFound(run_id) from error


def _passed_claims(ledger: Ledger, run_id: str) -> list[dict]:
    return [stored for stored in ledger.claims(run_id) if stored["status"] == ClaimStatus.PASSED]


def start_publish(run_id: str, requester: Scope, *, ledger: Ledger | None = None, stepfunctions=None,
                  state_machine_arn: str | None = None) -> PublishResponse:
    """Start the publish machine for a run the requester asked. Raises RunNotFound (a KeyError) for an unknown run,
    PublishForbidden (a PermissionError) for anyone but the user who asked."""
    ledger = ledger or ledger_from_settings()
    run_scope = _run(ledger, run_id)["scope"]
    if (requester.user_id, requester.tenant_id) != (run_scope["user_id"], run_scope["tenant_id"]):
        raise PublishForbidden(f"only the user who asked run {run_id} may publish it")
    if not _passed_claims(ledger, run_id):
        raise NothingToPublish(f"run {run_id} has no verified claim to publish")
    state_machine_arn = state_machine_arn or get_settings().publish_state_machine_arn
    if not state_machine_arn:
        raise PublishNotConfigured("PUBLISH_STATE_MACHINE_ARN is not set")
    execution = (stepfunctions or _stepfunctions_client()).start_execution(
        stateMachineArn=state_machine_arn, name=run_id, input=json.dumps({"run_id": run_id}))
    return PublishResponse(run_id=run_id, execution_arn=execution["executionArn"], status=STATUS_AWAITING_APPROVAL)
```
- [ ] **Step 5: Run:** `uv run --locked pytest tests/infra/functions/test_publish.py --no-cov 2>&1 | tail -1`. Expected: `4 passed in …s`.
- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/functions/publish.py tests/infra/functions/test_publish.py
git commit -m "start_publish: one Standard execution per run, only by the asker, only with a verified claim"
```
Expected: start + 4 (dry-run `301 passed`).

**Task done when:** `uv run --locked pytest tests/infra/functions/test_publish.py --no-cov 2>&1 | tail -1` prints `4 passed`.

### Task 2: `store_task_token` and `decide`

**Files:** Modify `infra/functions/publish.py` (append), `tests/infra/functions/test_publish.py` (whole file)

**Produces:** `infra.functions.publish.store_task_token(run_id: str, task_token: str, ledger: Ledger) -> None`, `decide(run_id: str, decision: str, note: str, approver: Scope, *, ledger: Ledger | None = None, stepfunctions=None) -> ApproveResponse`. **Consumes:** `Ledger.put_task_token`, `task_token`, `record_decision`, `run` (H1); `tools.api_schema.ApproveResponse`. **Consumed by:** Task 4 (Lambda), L3 (`infra.functions.api.approve`).

- [ ] **Step 1: Failing tests.** Replace the whole of `tests/infra/functions/test_publish.py` with:
```python
"""Publish and approve (infra/functions/publish.py): the only write, behind a delivery lead's approval (D-011)."""
import json

import pytest

from adapters.memory_ledger import InMemoryLedger
from config import DEFAULT_TENANT_ID
from infra.functions.publish import (NoPendingApproval, NothingToPublish, PublishForbidden, PublishNotConfigured, RunNotFound,
                          decide, start_publish, store_task_token)
from tools.constants import ALL_ENTITIES_WILDCARD
from tools.models import Scope
from tools.ports import LedgerConflict

RUN_ID = "run-publish"
STATE_MACHINE_ARN = "arn:aws:states:eu-west-1:000000000000:stateMachine:publish"
TASK_TOKEN = "example-task-token"
BUCKET = "test-artefacts"
STATUS_PACK_PREFIX = "status-packs/"
PASSED_CLAIM = {"claim_id": "claim-1", "statement": "E4 is blocked by open defect DEF-0412",
                "chain": [{"artefact": "defect_log", "row_id": "DEF-0412", "role_in_chain": "cause"}]}
DELIVERY_LEAD = Scope(user_id="user-delivery-lead", role="delivery_lead", tenant_id=DEFAULT_TENANT_ID,
                      entity_ids=(ALL_ENTITIES_WILDCARD,))


class FakeStepFunctions:
    """Records the Step Functions calls infra/functions/publish.py makes (no AWS in unit tests)."""

    def __init__(self):
        self.calls = []

    def start_execution(self, **request):
        self.calls.append(("start_execution", request))
        return {"executionArn": f"{STATE_MACHINE_ARN.replace('stateMachine', 'execution')}:{request['name']}"}

    def send_task_success(self, **request):
        self.calls.append(("send_task_success", request))

    def send_task_failure(self, **request):
        self.calls.append(("send_task_failure", request))


@pytest.fixture
def ledger(cfo_scope):
    ledger = InMemoryLedger()
    ledger.start_run(RUN_ID, cfo_scope, budget_usd=0.5)
    ledger.put_claim(RUN_ID, PASSED_CLAIM)
    ledger.record_verdict(RUN_ID, "claim-1", {"claim_id": "claim-1", "pass": True, "reason": "supported"})
    return ledger


@pytest.fixture
def stepfunctions():
    return FakeStepFunctions()


def publish(ledger, stepfunctions, requester):
    return start_publish(RUN_ID, requester, ledger=ledger, stepfunctions=stepfunctions,
                         state_machine_arn=STATE_MACHINE_ARN)


def test_start_publish_starts_one_execution_named_after_the_run(ledger, stepfunctions, cfo_scope):
    response = publish(ledger, stepfunctions, cfo_scope)
    assert (response.run_id, response.status) == (RUN_ID, "awaiting_approval")
    assert response.execution_arn.endswith(f":{RUN_ID}")
    assert stepfunctions.calls == [("start_execution", {"stateMachineArn": STATE_MACHINE_ARN, "name": RUN_ID,
                                                        "input": json.dumps({"run_id": RUN_ID})})]


def test_only_the_user_who_asked_may_publish_the_run(ledger, stepfunctions):
    with pytest.raises(PublishForbidden):
        publish(ledger, stepfunctions, DELIVERY_LEAD)
    assert stepfunctions.calls == []


def test_a_run_without_a_passed_claim_has_nothing_to_publish(stepfunctions, cfo_scope):
    ledger = InMemoryLedger()
    ledger.start_run(RUN_ID, cfo_scope, budget_usd=0.5)
    with pytest.raises(NothingToPublish):
        publish(ledger, stepfunctions, cfo_scope)
    with pytest.raises(RunNotFound):
        start_publish("run-unknown", cfo_scope, ledger=ledger, stepfunctions=stepfunctions,
                      state_machine_arn=STATE_MACHINE_ARN)


def test_publishing_without_a_state_machine_fails_loudly(ledger, stepfunctions, cfo_scope):
    with pytest.raises(PublishNotConfigured):
        start_publish(RUN_ID, cfo_scope, ledger=ledger, stepfunctions=stepfunctions, state_machine_arn=None)


def awaiting_approval(ledger, stepfunctions, cfo_scope):
    """A published run as the machine leaves it: started, and its first state has stored the task token."""
    publish(ledger, stepfunctions, cfo_scope)
    store_task_token(RUN_ID, TASK_TOKEN, ledger)
    stepfunctions.calls.clear()


def test_store_task_token_keeps_the_first_token_only(ledger):
    store_task_token(RUN_ID, TASK_TOKEN, ledger)
    with pytest.raises(LedgerConflict):
        store_task_token(RUN_ID, "a-second-token", ledger)
    assert ledger.task_token(RUN_ID) == TASK_TOKEN


def test_a_delivery_lead_approves_and_the_machine_is_told(ledger, stepfunctions, cfo_scope):
    awaiting_approval(ledger, stepfunctions, cfo_scope)
    response = decide(RUN_ID, "approve", "looks right", DELIVERY_LEAD, ledger=ledger, stepfunctions=stepfunctions)
    assert (response.run_id, response.status) == (RUN_ID, "approved")
    assert stepfunctions.calls == [("send_task_success", {"taskToken": TASK_TOKEN, "output": json.dumps(
        {"run_id": RUN_ID, "approved_by": DELIVERY_LEAD.user_id})})]
    decision = ledger.run(RUN_ID)["decisions"][0]
    assert (decision["decision"], decision["note"], decision["user_id"]) == ("approve", "looks right",
                                                                            DELIVERY_LEAD.user_id)


def test_sending_back_fails_the_task_and_is_logged(ledger, stepfunctions, cfo_scope):
    awaiting_approval(ledger, stepfunctions, cfo_scope)
    response = decide(RUN_ID, "send_back", "cite the runbook step", DELIVERY_LEAD, ledger=ledger,
                      stepfunctions=stepfunctions)
    assert response.status == "sent_back"
    assert stepfunctions.calls == [("send_task_failure", {"taskToken": TASK_TOKEN, "error": "SentBack",
                                                          "cause": "cite the runbook step"})]
    assert ledger.run(RUN_ID)["decisions"][0]["decision"] == "send_back"


@pytest.mark.parametrize("approver", [
    Scope(user_id="user-cfo", role="cfo", tenant_id=DEFAULT_TENANT_ID, entity_ids=(ALL_ENTITIES_WILDCARD,)),
    Scope(user_id="user-e4-lead", role="entity_lead", tenant_id=DEFAULT_TENANT_ID, entity_ids=("E4",)),
    Scope(user_id="user-other-tenant", role="delivery_lead", tenant_id="t-02", entity_ids=(ALL_ENTITIES_WILDCARD,)),
])
def test_only_a_delivery_lead_of_the_runs_tenant_may_decide(ledger, stepfunctions, cfo_scope, approver):
    awaiting_approval(ledger, stepfunctions, cfo_scope)
    with pytest.raises(PublishForbidden):
        decide(RUN_ID, "approve", "", approver, ledger=ledger, stepfunctions=stepfunctions)
    assert stepfunctions.calls == [] and ledger.run(RUN_ID)["decisions"] == []


def test_nothing_to_decide_before_the_token_or_after_a_decision(ledger, stepfunctions, cfo_scope):
    with pytest.raises(NoPendingApproval):
        decide(RUN_ID, "approve", "", DELIVERY_LEAD, ledger=ledger, stepfunctions=stepfunctions)
    awaiting_approval(ledger, stepfunctions, cfo_scope)
    decide(RUN_ID, "approve", "", DELIVERY_LEAD, ledger=ledger, stepfunctions=stepfunctions)
    with pytest.raises(NoPendingApproval):
        decide(RUN_ID, "send_back", "changed my mind", DELIVERY_LEAD, ledger=ledger, stepfunctions=stepfunctions)
    assert len(stepfunctions.calls) == 1


def test_an_unknown_decision_or_run_is_refused(ledger, stepfunctions, cfo_scope):
    awaiting_approval(ledger, stepfunctions, cfo_scope)
    with pytest.raises(ValueError):
        decide(RUN_ID, "maybe", "", DELIVERY_LEAD, ledger=ledger, stepfunctions=stepfunctions)
    with pytest.raises(KeyError):
        decide("run-unknown", "approve", "", DELIVERY_LEAD, ledger=ledger, stepfunctions=stepfunctions)


def test_the_errors_are_the_kinds_the_api_maps():
    assert issubclass(PublishForbidden, PermissionError)
    assert issubclass(RunNotFound, KeyError) and issubclass(NoPendingApproval, KeyError)
    assert issubclass(NothingToPublish, ValueError)
```
- [ ] **Step 2: Run:** `uv run --locked pytest tests/infra/functions/test_publish.py --no-cov 2>&1 | grep -E "^E  " | head -1`. Expected: `E   ImportError: cannot import name 'decide' from 'infra.functions.publish' (...)`.
- [ ] **Step 3: Implement.** Append to `infra/functions/publish.py`:
```python


def store_task_token(run_id: str, task_token: str, ledger: Ledger) -> None:
    """The publish machine's first state: keep the approval token by run ID (create-once, so it can't be swapped)."""
    ledger.put_task_token(run_id, task_token)


def decide(run_id: str, decision: str, note: str, approver: Scope, *, ledger: Ledger | None = None,
           stepfunctions=None) -> ApproveResponse:
    """A delivery lead's decision on a waiting publish, logged on the run before the machine is told. Raises
    PublishForbidden (a PermissionError) for anyone else, RunNotFound or NoPendingApproval (KeyErrors) when there is
    nothing to decide, ValueError for an unknown decision."""
    if decision not in DECISIONS:
        raise ValueError(f"decision must be one of {DECISIONS}, not {decision!r}")
    ledger = ledger or ledger_from_settings()
    run = _run(ledger, run_id)
    if approver.role != APPROVER_ROLE or approver.tenant_id != run["scope"]["tenant_id"]:
        raise PublishForbidden(f"only a {APPROVER_ROLE} of tenant {run['scope']['tenant_id']} may decide")
    task_token = ledger.task_token(run_id)
    if task_token is None or run["decisions"]:
        raise NoPendingApproval(f"no publish of run {run_id} is waiting for a decision")
    ledger.record_decision(run_id, {"decision": decision, "note": note, "user_id": approver.user_id,
                                    "decided_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    client = stepfunctions or _stepfunctions_client()
    if decision == DECISION_APPROVE:
        client.send_task_success(taskToken=task_token,
                                 output=json.dumps({"run_id": run_id, "approved_by": approver.user_id}))
    else:
        client.send_task_failure(taskToken=task_token, error=SENT_BACK_ERROR, cause=note or SENT_BACK_DEFAULT_CAUSE)
    return ApproveResponse(run_id=run_id, status=STATUS_BY_DECISION[decision])
```
- [ ] **Step 4: Run:** `uv run --locked pytest tests/infra/functions/test_publish.py --no-cov 2>&1 | tail -1`. Expected: `13 passed in …s`.
- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/functions/publish.py tests/infra/functions/test_publish.py
git commit -m "decide: only a delivery lead of the run's tenant; logged on the run before the task token is used"
```
Expected: start + 13 (dry-run `310 passed`).

**Task done when:** `uv run --locked pytest tests/infra/functions/test_publish.py --no-cov -k "only_a_delivery_lead" 2>&1 | tail -1 | cut -d, -f1` prints `3 passed`.

### Task 3: The status pack, written only after approval

**Files:** Modify `infra/functions/publish.py` (append), `tests/infra/functions/test_publish.py`

**Produces:** `infra.functions.publish.status_pack(run_id: str, ledger: Ledger) -> dict`, `write_status_pack(run_id: str, *, ledger: Ledger, s3, bucket: str | None, prefix: str) -> str`. **Consumes:** `Ledger.run`, `claims`, `rejected` (H1). **Consumed by:** Task 4 (Lambda).

- [ ] **Step 1: Failing tests.** In `tests/infra/functions/test_publish.py`, change `from config import DEFAULT_TENANT_ID` to `from config import DEFAULT_REGION, DEFAULT_TENANT_ID` and `decide, start_publish, store_task_token)` to `decide, start_publish, store_task_token, write_status_pack)`, then append:
```python


@pytest.fixture
def s3(monkeypatch):
    moto = pytest.importorskip("moto")
    boto3 = pytest.importorskip("boto3")
    for variable in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.setenv(variable, "testing")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    with moto.mock_aws():
        client = boto3.client("s3", region_name=DEFAULT_REGION)
        client.create_bucket(Bucket=BUCKET, CreateBucketConfiguration={"LocationConstraint": DEFAULT_REGION})
        yield client


def objects_in(s3) -> list[str]:
    return [listed["Key"] for listed in s3.list_objects_v2(Bucket=BUCKET).get("Contents", [])]


def write_pack(ledger, s3):
    return write_status_pack(RUN_ID, ledger=ledger, s3=s3, bucket=BUCKET, prefix=STATUS_PACK_PREFIX)


def test_no_status_pack_is_written_without_an_approval(ledger, stepfunctions, s3, cfo_scope):
    with pytest.raises(PublishForbidden):
        write_pack(ledger, s3)
    awaiting_approval(ledger, stepfunctions, cfo_scope)
    decide(RUN_ID, "send_back", "not yet", DELIVERY_LEAD, ledger=ledger, stepfunctions=stepfunctions)
    with pytest.raises(PublishForbidden):
        write_pack(ledger, s3)
    assert objects_in(s3) == []


def test_an_approved_run_writes_its_status_pack_under_the_prefix(ledger, stepfunctions, s3, cfo_scope):
    awaiting_approval(ledger, stepfunctions, cfo_scope)
    decide(RUN_ID, "approve", "ship it", DELIVERY_LEAD, ledger=ledger, stepfunctions=stepfunctions)
    key = write_pack(ledger, s3)
    assert key == f"{STATUS_PACK_PREFIX}{RUN_ID}.json" and objects_in(s3) == [key]
    pack = json.loads(s3.get_object(Bucket=BUCKET, Key=key)["Body"].read())
    assert (pack["run_id"], pack["approved_by"], pack["note"]) == (RUN_ID, DELIVERY_LEAD.user_id, "ship it")
    assert pack["findings"] == [{"claim_id": "claim-1", "statement": PASSED_CLAIM["statement"],
                                 "citations": [{"artefact": "defect_log", "row_id": "DEF-0412"}]}]
    assert pack["could_not_verify"] == []
    with pytest.raises(PublishNotConfigured):
        write_status_pack(RUN_ID, ledger=ledger, s3=s3, bucket=None, prefix=STATUS_PACK_PREFIX)
```
- [ ] **Step 2: Run:** `uv run --locked pytest tests/infra/functions/test_publish.py --no-cov 2>&1 | grep -E "^E  " | head -1`. Expected: `E   ImportError: cannot import name 'write_status_pack' from 'infra.functions.publish' (...)`.
- [ ] **Step 3: Implement.** Append to `infra/functions/publish.py`:
```python


def status_pack(run_id: str, ledger: Ledger) -> dict:
    """The approved status pack: the verified findings with their citations, what could not be verified, the cost
    and who approved it. Built from the ledger only, so it says exactly what the critic passed."""
    run = ledger.run(run_id)
    approval = run["decisions"][-1]
    return {
        "run_id": run_id,
        "tenant_id": run["scope"]["tenant_id"],
        "approved_by": approval["user_id"],
        "approved_at": approval["decided_at"],
        "note": approval["note"],
        "findings": [{"claim_id": stored["claim_id"], "statement": stored["claim"]["statement"],
                      "citations": [{"artefact": link["artefact"], "row_id": link["row_id"]}
                                    for link in stored["claim"]["chain"]]}
                     for stored in _passed_claims(ledger, run_id)],
        "could_not_verify": [{"claim_id": record["claim_id"], "statement": record["claim"]["statement"]}
                             for record in ledger.rejected(run_id)],
        "cost_usd": run["cost_usd"],
    }


def write_status_pack(run_id: str, *, ledger: Ledger, s3, bucket: str | None, prefix: str) -> str:
    """The publish machine's last state: write the status pack, only if the run's last decision is an approval.
    Returns the object key."""
    decisions = ledger.run(run_id)["decisions"]
    if not decisions or decisions[-1]["decision"] != DECISION_APPROVE:
        raise PublishForbidden(f"run {run_id} has no approval: no status pack is written")
    if not bucket:
        raise PublishNotConfigured("ARTEFACTS_BUCKET is not set")
    key = f"{prefix}{run_id}{STATUS_PACK_SUFFIX}"
    body = json.dumps(status_pack(run_id, ledger), indent=JSON_INDENT, sort_keys=True)
    s3.put_object(Bucket=bucket, Key=key, Body=body.encode("utf-8"), ContentType=JSON_CONTENT_TYPE)
    return key
```
- [ ] **Step 4: Run:** `uv run --locked pytest tests/infra/functions/test_publish.py --no-cov 2>&1 | tail -1`. Expected: `15 passed in …s`.
- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL|infra/functions/publish"
git add infra/functions/publish.py tests/infra/functions/test_publish.py
git commit -m "Status pack: written to status-packs/<run_id>.json only when the ledger shows an approval"
```
Expected: start + 15 (dry-run `312 passed`); `infra/functions/publish.py ... 97%`, the only misses being `_stepfunctions_client`'s two lines (the real boto3 client).

**Task done when:** `uv run --locked pytest tests/infra/functions/test_publish.py --no-cov -k status_pack 2>&1 | tail -1 | cut -d, -f1` prints `2 passed`.

### Task 4: The publish machine's Lambdas

**Files:** Modify `infra/functions/states.py`, `tests/infra/functions/test_states.py` *(new)*

**Produces:** `infra.functions.states.store_task_token(event, context) -> dict`, `write_status_pack(event, context) -> dict`, `TaskTokenEvent`, `RunEvent`, `make_s3()`, `status_pack_location() -> tuple[str | None, str]`. **Consumes:** Tasks 2–3; `config.get_settings` (`aws_region`, `artefacts_bucket`, `status_pack_prefix`). **Consumed by:** Yaw's Standard machine (Y2).

- [ ] **Step 1: Failing tests.** In `tests/infra/functions/test_states.py`, change `import json` (the first import) to `import json` followed by a new line `from types import SimpleNamespace`, then append:
```python


def test_the_publish_machines_lambdas_store_the_token_and_write_only_after_approval(ledger, monkeypatch, cfo_scope):
    from infra.functions.publish import PublishForbidden
    written = []
    monkeypatch.setattr(states, "make_s3", lambda: SimpleNamespace(put_object=lambda **request: written.append(
        request["Key"])))
    monkeypatch.setattr(states, "status_pack_location", lambda: ("test-artefacts", "status-packs/"))
    ledger.start_run(RUN_ID, cfo_scope, budget_usd=0.5)
    assert states.store_task_token({"run_id": RUN_ID, "task_token": "example-task-token"}, None) == {}
    assert ledger.task_token(RUN_ID) == "example-task-token"
    with pytest.raises(PublishForbidden):
        states.write_status_pack({"run_id": RUN_ID}, None)
    ledger.record_decision(RUN_ID, {"decision": "approve", "note": "", "user_id": "user-delivery-lead",
                                    "decided_at": "2026-10-14T15:00:00+00:00"})
    assert states.write_status_pack({"run_id": RUN_ID}, None) == {
        "bucket": "test-artefacts", "key": f"status-packs/{RUN_ID}.json"}
    assert written == [f"status-packs/{RUN_ID}.json"]


def test_the_status_pack_goes_to_the_configured_bucket_and_prefix(monkeypatch):
    from config import get_settings
    monkeypatch.setenv("ARTEFACTS_BUCKET", "demo-artefacts")
    monkeypatch.setenv("STATUS_PACK_PREFIX", "packs/")
    get_settings.cache_clear()
    try:
        assert states.status_pack_location() == ("demo-artefacts", "packs/")
        assert hasattr(states.make_s3(), "put_object")
    finally:
        get_settings.cache_clear()
```
- [ ] **Step 2: Run:** `uv run --locked pytest tests/infra/functions/test_states.py --no-cov 2>&1 | tail -1`. Expected: `2 failed, 4 passed`, with `AttributeError: <module 'infra.functions.states' ...> has no attribute 'make_s3'` and `AttributeError: module 'infra.functions.states' has no attribute 'status_pack_location'`.
- [ ] **Step 3: Implement.** In `infra/functions/states.py`:
  - in the module docstring, after the `write_answer` line of the table, add:
```text

The publish machine's two Lambdas (infra/functions/publish.py):

  store_task_token  {run_id, task_token}   (a .waitForTaskToken state) -> {}
  write_status_pack {run_id}               (after the approval)        -> {bucket, key}
```
  - replace `from infra.functions import steps` with:
```python
from config import get_settings
from infra.functions import publish, steps
```
  - insert before `class WriteAnswerEvent(StateIO):`:
```python
class TaskTokenEvent(StateIO):
    run_id: str = Field(min_length=1)
    task_token: str = Field(min_length=1)


class RunEvent(StateIO):
    run_id: str = Field(min_length=1)


```
  - insert before `def _as_json(model: BaseModel) -> dict:`:
```python
def make_s3():
    import boto3  # only where AWS is really called
    return boto3.client("s3", region_name=get_settings().aws_region)


def status_pack_location() -> tuple[str | None, str]:
    settings = get_settings()
    return settings.artefacts_bucket, settings.status_pack_prefix


```
  - append at the end:
```python


# ---- the publish machine -----------------------------------------------------------------------------------------
def store_task_token(event: dict, context) -> dict:
    request = TaskTokenEvent.model_validate(event)
    publish.store_task_token(request.run_id, request.task_token, make_ledger())
    return {}


def write_status_pack(event: dict, context) -> dict:
    request = RunEvent.model_validate(event)
    bucket, prefix = status_pack_location()
    key = publish.write_status_pack(request.run_id, ledger=make_ledger(), s3=make_s3(), bucket=bucket, prefix=prefix)
    return {"bucket": bucket, "key": key}
```
- [ ] **Step 4: Run:** `uv run --locked pytest tests/infra/functions/test_states.py --no-cov 2>&1 | tail -1`. Expected: `6 passed in …s`.
- [ ] **Step 5: Guards, full suite and commit**
```bash
uv run --locked pytest tests/test_architecture.py tests/test_code_style.py --no-cov 2>&1 | tail -1
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/functions/states.py tests/infra/functions/test_states.py
git commit -m "Publish machine Lambdas: store the task token; write the status pack after approval"
```
Expected: guards pass; start + 17 (dry-run `314 passed`), `TOTAL ... 98%`.

**Task done when:** `uv run --locked pytest tests/infra/functions/test_states.py --no-cov -k publish_machines 2>&1 | tail -1 | cut -d, -f1` prints `1 passed`.

### Task 5: Handover, docs, review and PR
- [ ] **Step 1: `docs/DEVOPS_HANDOVER.md`.** In the row `` `start_publish`, `decide`, status-pack writer ``, change the entry point to: `` `infra.functions.publish.start_publish` / `decide` (called by `infra.functions.api.publish` / `approve`); Lambdas `infra.functions.states.store_task_token`, `infra.functions.states.write_status_pack` `` and the IAM cell to: `` `store_task_token`: `dynamodb:GetItem`, `PutItem` on `<ledger>`. `write_status_pack`: `dynamodb:GetItem`, `Query` on `<ledger>` and `<rejected>`; `s3:PutObject` **only** on `<bucket>/status-packs/*` ``. Below the table add:
```markdown
### Publish machine (Standard, Huvison's Lambdas)
`StoreTaskToken`: `arn:aws:states:::lambda:invoke.waitForTaskToken` on `infra.functions.states.store_task_token`, payload `{"run_id.$": "$.run_id", "task_token.$": "$$.Task.Token"}`; `Catch` `States.TaskFailed` → `SentBack` (the decision is already logged). On success → `WriteStatusPack`: `infra.functions.states.write_status_pack` with `{"run_id.$": "$.run_id"}`. Execution name = `run_id` (one publish per run).
```
- [ ] **Step 2: `HANDOFF.md`.** Under `## What's real`, add: `- Publish and approve (\`infra/functions/publish.py\`): a Standard execution per run waits on a task token stored by \`run_id\`; only a delivery lead of the run's tenant decides; every decision is logged on the run; the status pack is written to \`status-packs/<run_id>.json\` only after an approval, checked again in the ledger.`
- [ ] **Step 3: Commit:** `git add docs/DEVOPS_HANDOVER.md HANDOFF.md && git commit -m "Handover and HANDOFF: the publish machine and its two Lambdas"`; then `uv run --locked pytest tests/test_dependencies.py --no-cov 2>&1 | tail -1`. Expected: `4 passed`.
- [ ] **Step 4:** Review Focus by hand; results in `.superpowers/ledger-H4.md`.
- [ ] **Step 5:** `git diff develop --stat`. Expected: `HANDOFF.md`, `docs/DEVOPS_HANDOVER.md`, `infra/functions/states.py`, `infra/functions/publish.py`, `tests/infra/functions/test_states.py`, `tests/infra/functions/test_publish.py` (6 files).
- [ ] **Step 6: Verify in AWS (after Yaw's Y2 and Linus's L3 are deployed, with Yaw):** with `AWS_PROFILE=hackathon AWS_REGION=eu-west-1`, run one `/ask` as the CFO, `POST /publish` with its `run_id`, then `aws s3 ls s3://<ARTEFACTS_BUCKET>/status-packs/`. Expected: no object for the run. `POST /approve` as a delivery-lead test user with `decision: approve`, then the same `ls`. Expected: `<run_id>.json` listed once. Write both outputs in the ledger file. If the stacks aren't deployed yet, write "verify in AWS: pending Y2/L3" and do it at D2 12:00.
- [ ] **Step 7: With Huvison's OK only:** push `feature/publish-approve`, PR to `develop` ("Publish and approve: task token by run_id, delivery-lead approval, status pack after approval (H4)"), body with the count, the error mapping for Linus, the machine for Yaw, and the rulings. No attribution lines.
- [ ] **Step 8:** [[Build order]] row H4 → `in review (PR #nn)`, then `merged`. Tell Linus (exceptions and signatures), Yaw (the machine and IAM) and Clement (F5 can use the real API).

**Task done when:** the PR is open with the error-mapping table in its body; the ledger file has the AWS check's output or "pending Y2/L3".

## Done means
- [ ] **Publish and approve are tested.** *Verify:* on `develop`, `uv run --locked pytest tests/infra/functions/test_publish.py --no-cov 2>&1 | tail -1` prints `15 passed`.
- [ ] **Only a delivery lead of the run's tenant decides.** *Verify:* `uv run --locked pytest tests/infra/functions/test_publish.py --no-cov -k only_a_delivery_lead 2>&1 | tail -1 | cut -d, -f1` prints `3 passed`.
- [ ] **No pack without approval.** *Verify:* `uv run --locked pytest tests/infra/functions/test_publish.py --no-cov -k "no_status_pack" 2>&1 | tail -1 | cut -d, -f1` prints `1 passed`.
- [ ] **The Lambdas exist.** *Verify:* `uv run python -c "from infra.functions import states; print(callable(states.store_task_token), callable(states.write_status_pack))"` prints `True True`.
- [ ] **End to end in AWS.** *Verify:* the ledger file (copied into the PR) shows the empty `status-packs/` listing after publish and the single `<run_id>.json` after approval.
- [ ] **Nothing broke.** *Verify:* full suite after merge: start + 17, `TOTAL` ≥ 98%.
- [ ] **Merged.** *Verify:* PR merged into `develop`; [[Build order]] row H4 `merged`.

## Never
- Write to S3 anywhere but `write_status_pack`, or before the ledger shows an approval.
- Let a non-delivery-lead, or a delivery lead of another tenant, decide.
- Call AWS before the permission and state checks.
- Use real AWS in a test.
- Push to `develop` or `main`, or add attribution lines.

Related: [[H4 - Publish and approve - spec]], [[Build order]], [[How to execute a plan]]
