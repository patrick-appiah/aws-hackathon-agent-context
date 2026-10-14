---
tags: [build, plan, area/api]
id: L3
owner: Linus
spec: "[[L3 - Ask, publish and approve entry points - spec]]"
status: ready
updated: 2026-10-14
---
# L3: the `/ask`, `/publish` and `/approve` entry points (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[L3 - Ask, publish and approve entry points - spec]]: **the authority**, including its Assumptions and interfaces for H2b, H4 and Y2.
3. [[L2 - Entity and rows handlers - plan]]: the state of `infra/functions/api.py` *(new)* and `tests/infra/functions/test_api.py` *(new)* you start from.
4. [[Huvison - trust and flow]] §3, §5 and §9; [[H2b - Agent states, local spine and Lambda handlers - spec]] (the ask machine's input and output) and [[H4 - Publish and approve - plan]] (`start_publish`, `decide` and their errors). Their names win over this plan; record any difference in the ledger.
5. [[Linus - API, identity, blocker-analyst]] §3, and [[Handling security findings]].
6. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[Problem statement]], [[Judging rubric]], [[Pitch track grading rubric]], [[Hackathon guideline]]); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Linus. Never invent a name, a shape or a rule.

**Goal:** `POST /ask` refuses out-of-scope questions before any run starts and otherwise runs the ask spine; `POST /publish` and `POST /approve` hand the token's scope to Huvison's publish flow.

**Architecture:** three more thin handlers in `infra/functions/api.py`. The ask handler is the only one with an AWS call: `stepfunctions.start_sync_execution`, through `ask_spine_client()` so tests use a fake. The publish handlers reach `infra.functions.publish` through `publish_flow()`, imported on first use.

**Tech stack:** Python 3.11, pydantic 2, boto3 (Step Functions client, created lazily), pytest, uv. **Dry-run status:** every step ran on C1 + L1 + L2 plus H4's `infra/functions/publish.py` *(new)* (Huvison's dry-run copy, so the tests import its real exception classes), with fakes for the ask machine (H2b) and for `start_publish` / `decide` (no Step Functions); the counts below are real.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: **`feature/api-ask-publish-approve`** from an up-to-date `develop` **after L1, L2, H2b and H4 are merged** ([[Build order]]: L3 ← L1, H2b, H4). The tests import H4's exception classes from `infra.functions.publish`; the ask machine and the publish calls are still fakes, so no AWS is touched.
- **Start state:** `uv run --locked pytest` passes with `TOTAL` **97%** or more; write the count in the ledger as START. Every `N passed` below is START + the same increase (the dry-run base, C1 at 213 + L1 + L2 + H4's `infra/functions/publish.py`, was **255 passed**; a higher START is fine, what must match is the number each step adds). If `infra/functions/api.py` has no `def rows(`, L2 isn't merged; if `uv run python -c "from infra.functions.publish import NoPendingApproval, NothingToPublish, PublishForbidden, RunNotFound"` fails, H4 isn't merged: stop.
- **AWS:** `eu-west-1` only; Bedrock `eu.*` inference profiles only, never `global.*` (D-002). Synthetic data only. **No secrets** anywhere: code, tests, fixtures, the repo, the vault, Slack, commit messages.
- **Clean code (enforced by tests):** no single-character names anywhere (comprehensions, lambdas and `except ... as` included); no magic numbers or strings, so every limit, code and key is a named constant; settings only in `config.py`; domain constants only in `tools/constants.py`; descriptive names.
- **The core (`tools/`) never imports** boto3, Strands, `adapters`, `config` or `os` (`tests/test_architecture.py`).
- **Agents reach data only through `tools/agent_tools.py`.** Scope is never a tool argument and never comes from a request body, a query string or a model. Prompts live only in `agents/prompts/<agent>.txt`, versioned and locked (`uv run python scripts/lock_prompts.py`).
- **Never weaken a security rule** (the scope gate, the create-once ledger, the fail-closed critic, the `<evidence>` escaping) to make a test pass.
- **Tests** live in `tests/`, mirroring the code; run `uv run --locked pytest` from the repo root. Coverage must not drop below the start state. **No layout or "meta" guard tests**: test behaviour, not where files sit.
- **Git:** small commits, one per task, with the messages given. **No `Co-Authored-By` and no "Generated with" lines.** Never push to `develop` or `main`; the PR goes to `develop` after the owner's OK, and Patrick merges.
- **Stay in your folders** (`docs/TEAM_PLAN.md` §2, workstream 3: `infra/functions/api.py`, `infra/functions/scope.py` *(new)*, `tests/infra/functions/` *(new)*, `tools/metrics.py`, `tools/queries.py`, `tools/agent_tools.py`, `tools/claims.py`, `agents/blocker_analyst.py` *(new)*, `agents/prompts/blocker_analyst.txt` *(new)*, `scripts/export_summary.py` *(new)*, the eval runner). Any other file this plan touches is named in its task, with the owner who must review it.
- **Q11 is a security rule.** `scope.require(request.entity_id)` stays before the ARN check, the client and the `Question`. Never move it later, never catch `OutOfScope` around it.
- **Scope only from the token.** `AskRequest`, `PublishRequest` and `ApproveRequest` forbid extra keys (C1), so a `scope` in the body is a 400; keep it that way.
- **This handler builds its own `Question`** (lead decision): server-made `run_id`, the token's scope, `budget_usd = settings.run_budget_usd`, `max_attempts = settings.max_claim_attempts`. The execution input is the bare `Question` JSON, and the execution output is the `AskResponse` JSON with no wrapper key (H2b spec).

## Review Focus (check by hand at the end)
1. **Refusal before anything starts.** Read `ask` top to bottom: scope → body → `scope.require` → ARN check → `Question` → client. Nothing before `scope.require` touches AWS, the ledger or a model.
2. **The run ID is server-made** (`new_run_id()`), and the execution is named with it. Nothing from the body reaches `Question` except `entity_id` and `question`.
3. **A failed run is 500 `internal` with the contract body.** C1 added `ERROR_INTERNAL` (500) for exactly this; `AskSpineFailed` maps to it, so F4 gets `{error: "internal", detail}`. Check with Clement that F4a shows it as a failure with Retry, not a refusal, and that `detail` (the run ID, the status and the Step Functions error name) leaks nothing. Write the answer in the ledger.
4. **H4's errors map exactly.** `PublishForbidden` (a `PermissionError`) → 403 `forbidden`; `RunNotFound` and `NoPendingApproval` (`KeyError`s) → 404 `not_found`; `NothingToPublish` (a `ValueError`) → 400 `invalid_input`; `PublishNotConfigured` (a `RuntimeError`) propagates → 500. Read `infra/functions/publish.py` on `develop`: the four classes still subclass those bases, and `start_publish(run_id, requester, *, ...)` / `decide(run_id, decision, note, approver, *, ...)` still take the token's `Scope` positionally as the second / fourth argument, as `FakePublishFlow` does.
5. **Express sync limits.** `StartSyncExecution` returns `status` and `output` (a JSON string) or `error` and `cause`. Confirm with Yaw that the ASL's last state outputs exactly the `AskResponse` JSON (no wrapper key), and that the ask Lambda's timeout is at least API Gateway's 29 seconds.

---

### Task 1: `POST /ask`, `POST /publish`, `POST /approve`

**Files:**
- Modify: `infra/functions/api.py`, `tests/infra/functions/test_api.py`

**Produces:** `infra.functions.api.ask`, `publish`, `approve` (each `(event: dict, context: object) -> dict`); `AskSpineFailed`; `body_text(event: dict) -> str`; `new_run_id() -> str`; `ask_spine_client()`; `publish_flow()`. **Consumes:** L1/L2 helpers; C1's `AskRequest`, `AskResponse`, `PublishRequest`, `PublishResponse`, `ApproveRequest`, `ApproveResponse`, `tools.models.Question`; `config.Settings.ask_state_machine_arn`, `run_budget_usd`, `max_claim_attempts`, `aws_region`; Huvison's H4: `infra.functions.publish.start_publish(run_id: str, requester: Scope, *, ledger=None, stepfunctions=None, state_machine_arn=None) -> PublishResponse`, `decide(run_id: str, decision: str, note: str, approver: Scope, *, ledger=None, stepfunctions=None) -> ApproveResponse`, and its errors `PublishForbidden(PermissionError)`, `RunNotFound(KeyError)`, `NoPendingApproval(KeyError)`, `NothingToPublish(ValueError)`; H2b's ask machine contract (input: the bare `Question` JSON; output: the `AskResponse` JSON, no wrapper key). **Consumed by:** Yaw (Y1/Y2 routes), Clement (F4, F5), L6 (the deployed-API asker calls `/ask`).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/api-ask-publish-approve
mkdir -p .superpowers && printf '# Ledger: L3 ask, publish and approve entry points\n' > .superpowers/ledger-L3.md
```
Expected: `243 passed` (or your START), `TOTAL ... 97%`.

- [ ] **Step 2: Write the failing tests.** In `tests/infra/functions/test_api.py`:
  - replace the import block at the top (everything from `import json` to the `from tools.api_schema import ...` line) with:
```python
import base64
import json

import pytest

from adapters.memory_ledger import InMemoryLedger
from api import handlers
from config import DEFAULT_TENANT_ID, get_settings
from infra.functions.publish import NoPendingApproval, NothingToPublish, PublishForbidden, RunNotFound
from tools.api_schema import (ERROR_STATUS_CODES, ApproveResponse, AskResponse, EntityResponse, ErrorResponse,
                              PublishResponse, RowsResponse, SummaryResponse)
from tools.models import Answer, Bullet, Citation, Question
```
  - append at the end of the file (two blank lines before it):
```python
ASK_MACHINE_ARN = "arn:aws:states:eu-west-1:000000000000:stateMachine:ask"
PUBLISH_EXECUTION_ARN = "arn:aws:states:eu-west-1:000000000000:execution:publish:run-1"
DELIVERY_LEAD_CLAIMS = {**CFO_CLAIMS, "sub": "user-delivery-lead", "cognito:groups": "[delivery_lead]"}
E4_QUESTION = {"entity_id": "E4", "question": "What is blocking cutover for E4?"}
RUN_ID = "run-1"
DECIDED_RUN_ID = "run-decided"


class FakeAskSpine:
    """Stands in for the Step Functions client. Its first state starts the run in the ledger (H2's check_budget)."""

    def __init__(self, ledger, status="SUCCEEDED"):
        self.ledger, self.status, self.requests = ledger, status, []

    def start_sync_execution(self, **execution_request):
        question = Question.model_validate_json(execution_request["input"])
        self.requests.append({**execution_request, "question": question})
        self.ledger.start_run(question.run_id, question.scope, question.budget_usd)
        answer = Answer(headline="E4 is blocked", bullets=[Bullet(
            text="DEF-0412 is open", citations=[Citation(artefact="defect_log", row_id=E4_BLOCKER)])])
        return {"status": self.status,
                "output": AskResponse(run_id=question.run_id, answer=answer, cost_usd=0.01).model_dump_json()}


@pytest.fixture
def ledger():
    return InMemoryLedger()


@pytest.fixture
def ask_spine(monkeypatch, cognito_mode, ledger):
    monkeypatch.setenv("ASK_STATE_MACHINE_ARN", ASK_MACHINE_ARN)
    get_settings.cache_clear()
    fake_spine = FakeAskSpine(ledger)
    monkeypatch.setattr(handlers, "ask_spine_client", lambda: fake_spine)
    return fake_spine


def test_ask_starts_one_run_with_the_scope_from_the_token(ask_spine, make_event):
    response = handlers.ask(make_event(claims=CFO_CLAIMS, body=E4_QUESTION), None)
    answer = AskResponse.model_validate_json(response["body"])
    [request] = ask_spine.requests
    question = request["question"]
    assert response["statusCode"] == HTTP_OK and answer.run_id == question.run_id == request["name"]
    assert request["stateMachineArn"] == ASK_MACHINE_ARN
    assert (question.scope.user_id, question.entity_id, question.budget_usd, question.max_attempts) == (
        "user-cfo", "E4", get_settings().run_budget_usd, get_settings().max_claim_attempts)


def test_q11_out_of_scope_ask_is_refused_before_any_run_starts(ask_spine, ledger, make_event):
    e2_question = {"entity_id": "E2", "question": "What is blocking cutover for E2?"}
    response = handlers.ask(make_event(claims=ENTITY_FOUR_LEAD_CLAIMS, body=e2_question), None)
    assert_error(response, "out_of_scope")
    assert ask_spine.requests == [] and ledger.runs == {}


@pytest.mark.parametrize("body", [
    {"entity_id": "E-4", "question": "What blocks E4?"},
    {"entity_id": "E4", "question": ""},
    {**E4_QUESTION, "scope": {"role": "cfo", "entity_ids": ["*"]}},
    "not json",
    "",
], ids=["malformed_entity_id", "empty_question", "scope_in_the_body", "not_json", "empty_body"])
def test_ask_with_a_bad_body_is_400_and_starts_nothing(ask_spine, make_event, body):
    assert_error(handlers.ask(make_event(claims=CFO_CLAIMS, body=body), None), "invalid_input")
    assert ask_spine.requests == []


def test_ask_reads_a_base64_body(ask_spine, make_event):
    event = make_event(claims=CFO_CLAIMS, body=base64.b64encode(json.dumps(E4_QUESTION).encode()).decode())
    response = handlers.ask({**event, "isBase64Encoded": True}, None)
    assert response["statusCode"] == HTTP_OK and len(ask_spine.requests) == 1


def test_ask_without_a_token_is_401_and_starts_nothing(ask_spine, make_event):
    assert_error(handlers.ask(make_event(body=E4_QUESTION), None), "unauthorized")
    assert ask_spine.requests == []


def test_a_failed_ask_run_is_500_internal(ask_spine, make_event):
    ask_spine.status = "FAILED"
    response = handlers.ask(make_event(claims=CFO_CLAIMS, body=E4_QUESTION), None)
    assert_error(response, "internal")
    assert "ended FAILED" in body_of(response)["detail"]


def test_ask_without_a_state_machine_is_500_internal(cognito_mode, make_event):
    response = handlers.ask(make_event(claims=CFO_CLAIMS, body=E4_QUESTION), None)
    assert_error(response, "internal")
    assert body_of(response)["detail"] == "ASK_STATE_MACHINE_ARN is not set"


def test_the_ask_spine_client_is_in_the_configured_region():
    assert handlers.ask_spine_client().meta.region_name == get_settings().aws_region


class FakePublishFlow:
    """Stands in for infra/functions/publish.py (H4): its start_publish and decide signatures, return models and exceptions,
    without Step Functions or the ledger."""

    def __init__(self):
        self.calls, self.publish_error = [], None

    def start_publish(self, run_id, requester):
        self.calls.append(("start_publish", run_id, requester))
        if self.publish_error is not None:
            raise self.publish_error
        return PublishResponse(run_id=run_id, execution_arn=PUBLISH_EXECUTION_ARN, status="awaiting_approval")

    def decide(self, run_id, decision, note, approver):
        self.calls.append(("decide", run_id, decision, note, approver))
        if run_id not in (RUN_ID, DECIDED_RUN_ID):
            raise RunNotFound(run_id)
        if approver.role != "delivery_lead":
            raise PublishForbidden(f"only a delivery_lead of tenant {DEFAULT_TENANT_ID} may decide")
        if run_id == DECIDED_RUN_ID:
            raise NoPendingApproval(f"no publish of run {run_id} is waiting for a decision")
        return ApproveResponse(run_id=run_id, status="approved" if decision == "approve" else "sent_back")


@pytest.fixture
def publish_flow(monkeypatch, cognito_mode):
    fake_flow = FakePublishFlow()
    monkeypatch.setattr(handlers, "publish_flow", lambda: fake_flow)
    return fake_flow


def test_publish_starts_the_approval_flow_as_the_signed_in_user(publish_flow, make_event):
    response = handlers.publish(make_event(claims=CFO_CLAIMS, body={"run_id": RUN_ID}), None)
    published = PublishResponse.model_validate_json(response["body"])
    assert response["statusCode"] == HTTP_OK and published.execution_arn == PUBLISH_EXECUTION_ARN
    [(_function, run_id, requester)] = publish_flow.calls
    assert (run_id, requester.user_id) == (RUN_ID, "user-cfo")


@pytest.mark.parametrize("flow_error, error_code", [
    (PublishForbidden(f"only the user who asked run {RUN_ID} may publish it"), "forbidden"),
    (RunNotFound(RUN_ID), "not_found"),
    (NothingToPublish(f"run {RUN_ID} has no verified claim to publish"), "invalid_input"),
], ids=["not_the_asker", "unknown_run", "nothing_verified"])
def test_each_start_publish_error_is_its_contract_error(publish_flow, make_event, flow_error, error_code):
    publish_flow.publish_error = flow_error
    response = handlers.publish(make_event(claims=CFO_CLAIMS, body={"run_id": RUN_ID}), None)
    assert_error(response, error_code)
    assert body_of(response)["detail"] == flow_error.args[0]


@pytest.mark.parametrize("decision, status", [("approve", "approved"), ("send_back", "sent_back")])
def test_a_delivery_lead_decides(publish_flow, make_event, decision, status):
    body = {"run_id": RUN_ID, "decision": decision, "note": "checked"}
    response = handlers.approve(make_event(claims=DELIVERY_LEAD_CLAIMS, body=body), None)
    assert ApproveResponse.model_validate_json(response["body"]).status == status
    assert publish_flow.calls[0][1:4] == (RUN_ID, decision, "checked")


def test_approval_by_anyone_else_is_403_forbidden(publish_flow, make_event):
    response = handlers.approve(make_event(claims=CFO_CLAIMS, body={"run_id": RUN_ID, "decision": "approve"}), None)
    assert_error(response, "forbidden")


def test_approving_an_unknown_run_is_404(publish_flow, make_event):
    body = {"run_id": "run-unknown", "decision": "approve"}
    assert_error(handlers.approve(make_event(claims=DELIVERY_LEAD_CLAIMS, body=body), None), "not_found")


def test_approving_a_run_with_no_pending_publish_is_404(publish_flow, make_event):
    body = {"run_id": DECIDED_RUN_ID, "decision": "approve"}
    assert_error(handlers.approve(make_event(claims=DELIVERY_LEAD_CLAIMS, body=body), None), "not_found")


@pytest.mark.parametrize("handler, body", [
    (handlers.publish, {"run_id": ""}),
    (handlers.approve, {"run_id": RUN_ID, "decision": "maybe"}),
    (handlers.approve, {"run_id": RUN_ID, "decision": "approve", "scope": {"role": "delivery_lead"}}),
], ids=["publish_without_run_id", "unknown_decision", "scope_in_the_body"])
def test_publish_and_approve_with_a_bad_body_are_400_and_call_nothing(publish_flow, make_event, handler, body):
    assert_error(handler(make_event(claims=DELIVERY_LEAD_CLAIMS, body=body), None), "invalid_input")
    assert publish_flow.calls == []
```

- [ ] **Step 3: Run them and watch them fail**
```bash
uv run --locked pytest tests/infra/functions/test_api.py --no-cov 2>&1 | tail -1
uv run --locked pytest tests/infra/functions/test_api.py --no-cov 2>&1 | grep -E "^E  "
```
Expected: `1 error` (at collection); `E   AttributeError: module 'infra.functions.api' has no attribute 'publish'` (the parametrised test names `handlers.publish`).

- [ ] **Step 4: Implement.** Replace the whole of `infra/functions/api.py` with the following. Compared with L2's version it adds the `base64`, `importlib` and `uuid` imports, `ApproveRequest`, `AskRequest`, `AskResponse`, `PublishRequest` and `Question` to the imports, five constants, `ERROR_INTERNAL` (C1) to the imports, `AskSpineFailed` above the mapping table, the `PermissionError` and `(AskSpineFailed, ERROR_INTERNAL)` rows (and the comments naming H4's errors on the `KeyError` and `ValueError` rows), and everything from `body_text` down; the L1 and L2 code is unchanged. `publish` and `approve` return H4's `PublishResponse` / `ApproveResponse` as they are.
```python
"""API Gateway HTTP API (v2) Lambda handlers: thin adapters from HTTP to the core (docs/TEAM_PLAN.md §3, D-021).

Every handler does the same three things:
  1. the scope from the token's claims (infra/functions/scope.py), never from the body or the query string;
  2. one builder from tools/api_schema.py, which calls tools/metrics.py and tools/queries.py;
  3. the contract model as JSON, or the contract error body ErrorResponse {error, detail}.
No business logic and no arithmetic here (D-001). DevOps entry points: infra.functions.api:<route> (docs/DEVOPS_HANDOVER.md).
"""
import base64
import functools
import importlib
import logging
import uuid
from typing import Callable

from pydantic import BaseModel

from adapters import repository_from_settings
from infra.functions.scope import ScopeRefused, Unauthenticated, scope_from_event
from config import get_settings
from tools.agent_tools import ERROR_INVALID_INPUT, ERROR_OUT_OF_SCOPE
from tools.api_schema import (ERROR_FORBIDDEN, ERROR_INTERNAL, ERROR_NOT_FOUND, ERROR_STATUS_CODES, ERROR_UNAUTHORIZED,
                              ApproveRequest, AskRequest, AskResponse, ErrorResponse, PublishRequest,
                              citations_from_query, entity_response, rows_response, summary_response)
from tools.models import OutOfScope, Question
from tools.ports import ArtefactRepository

HTTP_OK = 200
JSON_HEADERS = {"content-type": "application/json"}
ENTITY_PATH_PARAMETER = "id"      # GET /entity/{id}
CITE_QUERY_PARAMETER = "cite"     # GET /rows?cite=artefact:row_id,...
BODY_ENCODING = "utf-8"
RUN_ID_PREFIX = "run-"
STEP_FUNCTIONS_SERVICE = "stepfunctions"
EXECUTION_SUCCEEDED = "SUCCEEDED"
PUBLISH_FLOW_MODULE = "infra.functions.publish"   # Huvison's H4: start_publish and decide


class AskSpineFailed(RuntimeError):
    """The ask state machine didn't succeed, or isn't configured: 500 `internal` with the contract body (C1)."""


# The core's exceptions and the contract error each becomes, most specific first (ErrorResponse, D-021).
ERROR_CODE_BY_EXCEPTION: tuple[tuple[type[Exception], str], ...] = (
    (Unauthenticated, ERROR_UNAUTHORIZED),
    (ScopeRefused, ERROR_FORBIDDEN),
    (OutOfScope, ERROR_OUT_OF_SCOPE),
    (PermissionError, ERROR_FORBIDDEN),  # infra.functions.publish.PublishForbidden: not the asker, or not a delivery lead
    (KeyError, ERROR_NOT_FOUND),         # infra.functions.publish.RunNotFound and NoPendingApproval included
    (ValueError, ERROR_INVALID_INPUT),   # pydantic's ValidationError and infra.functions.publish.NothingToPublish included
    (AskSpineFailed, ERROR_INTERNAL),    # a failed, timed-out or unconfigured ask run: the request was fine
)
LambdaHandler = Callable[..., dict]   # (event: dict, context: object) -> dict, the Lambda handler shape
logger = logging.getLogger(__name__)


def json_response(status_code: int, model: BaseModel) -> dict:
    """An HTTP API (v2) Lambda response. by_alias=True so a Verdict's `passed` goes out as `pass`."""
    return {"statusCode": status_code, "headers": JSON_HEADERS, "body": model.model_dump_json(by_alias=True)}


def error_response(error_code: str, detail: str) -> dict:
    return json_response(ERROR_STATUS_CODES[error_code], ErrorResponse(error=error_code, detail=detail))


def _detail(error: Exception) -> str:
    return str(error.args[0]) if error.args else type(error).__name__


def returns_contract_errors(handler: LambdaHandler) -> LambdaHandler:
    """Turn the core's exceptions into the contract error body. Anything else propagates (API Gateway sends 500)."""
    @functools.wraps(handler)
    def guarded_handler(event: dict, context: object) -> dict:
        try:
            return handler(event, context)
        except tuple(exception_type for exception_type, _code in ERROR_CODE_BY_EXCEPTION) as error:
            error_code = next(code for exception_type, code in ERROR_CODE_BY_EXCEPTION
                              if isinstance(error, exception_type))
            logger.info("%s refused: %s %s", handler.__name__, error_code, type(error).__name__)
            return error_response(error_code, _detail(error))
    return guarded_handler


@functools.lru_cache(maxsize=None)
def repository_for(tenant_id: str) -> ArtefactRepository:
    """One repository per tenant per Lambda container: the artefacts don't change within a deployment."""
    return repository_from_settings(tenant_id)


@returns_contract_errors
def summary(event: dict, context: object) -> dict:
    """GET /summary: the one screen, limited to the caller's scope."""
    scope = scope_from_event(event, get_settings())
    return json_response(HTTP_OK, summary_response(repository_for(scope.tenant_id), scope))


@returns_contract_errors
def entity(event: dict, context: object) -> dict:
    """GET /entity/{id}: the entity's row, open blockers, failing reconciliations and calendar conflicts."""
    scope = scope_from_event(event, get_settings())
    entity_id = (event.get("pathParameters") or {}).get(ENTITY_PATH_PARAMETER, "")
    return json_response(HTTP_OK, entity_response(repository_for(scope.tenant_id), scope, entity_id))


@returns_contract_errors
def rows(event: dict, context: object) -> dict:
    """GET /rows?cite=artefact:row_id,...: the cited rows the scope may see; the rest come back in `missing`."""
    scope = scope_from_event(event, get_settings())
    cite = (event.get("queryStringParameters") or {}).get(CITE_QUERY_PARAMETER, "")
    return json_response(HTTP_OK, rows_response(repository_for(scope.tenant_id), scope, citations_from_query(cite)))


def body_text(event: dict) -> str:
    """The request body as text; HTTP API may base64-encode it."""
    raw_body = event.get("body") or ""
    return base64.b64decode(raw_body).decode(BODY_ENCODING) if event.get("isBase64Encoded") else raw_body


def new_run_id() -> str:
    return f"{RUN_ID_PREFIX}{uuid.uuid4().hex}"


def ask_spine_client():
    """Step Functions client for the Express ask spine. Imported here so the dashboard routes never load boto3."""
    import boto3
    return boto3.client(STEP_FUNCTIONS_SERVICE, region_name=get_settings().aws_region)


def publish_flow():
    """Huvison's infra/functions/publish.py (H4), imported on first use so the other routes run without it."""
    return importlib.import_module(PUBLISH_FLOW_MODULE)


@returns_contract_errors
def ask(event: dict, context: object) -> dict:
    """POST /ask: refuse an out-of-scope entity BEFORE any run starts (EVALS Q11), then run the ask spine."""
    settings = get_settings()
    scope = scope_from_event(event, settings)
    request = AskRequest.model_validate_json(body_text(event))
    scope.require(request.entity_id)   # nothing has started yet: no run, no ledger row, no model call
    if not settings.ask_state_machine_arn:
        raise AskSpineFailed("ASK_STATE_MACHINE_ARN is not set")
    question = Question(run_id=new_run_id(), scope=scope, entity_id=request.entity_id, question=request.question,
                        budget_usd=settings.run_budget_usd, max_attempts=settings.max_claim_attempts)
    execution = ask_spine_client().start_sync_execution(stateMachineArn=settings.ask_state_machine_arn,
                                                        name=question.run_id, input=question.model_dump_json())
    if execution.get("status") != EXECUTION_SUCCEEDED:
        raise AskSpineFailed(f"ask run {question.run_id} ended {execution.get('status')}: {execution.get('error')}")
    return json_response(HTTP_OK, AskResponse.model_validate_json(execution["output"]))


@returns_contract_errors
def publish(event: dict, context: object) -> dict:
    """POST /publish: start the human-approved status-pack flow for a run (Huvison's start_publish)."""
    scope = scope_from_event(event, get_settings())
    request = PublishRequest.model_validate_json(body_text(event))
    return json_response(HTTP_OK, publish_flow().start_publish(request.run_id, scope))


@returns_contract_errors
def approve(event: dict, context: object) -> dict:
    """POST /approve: approve or send back a run's status pack (Huvison's decide; only a delivery lead may approve)."""
    scope = scope_from_event(event, get_settings())
    request = ApproveRequest.model_validate_json(body_text(event))
    return json_response(HTTP_OK, publish_flow().decide(request.run_id, request.decision, request.note, scope))
```

- [ ] **Step 5: Run them and watch them pass**
```bash
uv run --locked pytest tests/infra/functions/test_api.py --no-cov 2>&1 | tail -1
```
Expected: `46 passed`.

- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL|infra/functions/api.py"
git add infra/functions/api.py tests/infra/functions/test_api.py
git commit -m "POST /ask refuses out-of-scope entities before any run starts (Q11); /publish and /approve call the flow"
```
Expected: START + 24 passed (`279 passed` on the dry-run base), `TOTAL ... 97%`, and `infra/functions/api.py ... 99%` with one line missed: the body of `publish_flow()` (the real `infra.functions.publish` import; the tests replace it with `FakePublishFlow`).

**Task done when:** `uv run --locked pytest tests/infra/functions/test_api.py -k "q11" --no-cov` prints `1 passed, 45 deselected`; `uv run --locked pytest tests/infra/functions/test_api.py -k "start_publish_error or no_pending" --no-cov` prints `4 passed, 42 deselected`; the full suite is START + 24; the commit is on the branch.

### Task 2: Handover and HANDOFF

**Files:**
- Modify: `docs/DEVOPS_HANDOVER.md` (your two rows), `HANDOFF.md` (your lines)

- [ ] **Step 1: `docs/DEVOPS_HANDOVER.md`.** Two exact replacements:
  - `` | `ask` | `infra.functions.api.ask` *(planned)* | API Gateway `POST /ask` | as above, plus `ASK_STATE_MACHINE_ARN` | `` → `` | `ask` | `infra.functions.api.ask` (built) | API Gateway `POST /ask` | as above, plus `ASK_STATE_MACHINE_ARN`, `RUN_BUDGET_USD`, `MAX_CLAIM_ATTEMPTS` (the handler puts them on the `Question`) | ``
  - `` `infra.functions.api.publish` / `approve` *(planned)* `` → `` `infra.functions.api.publish` / `approve` (built; they call `infra.functions.publish`, which is in the same `infra/functions/` *(new)* bundle) ``
- [ ] **Step 2: `HANDOFF.md`.**
  - Under "What's real", directly above `- TODO: agent loop, critic, ledger, approval flow, as each lands.`, add:
    ```markdown
    - `POST /ask` refuses an entity outside the user's scope with 403 **before** any run starts (EVALS Q11: no ledger row, no model call), then runs the Express ask spine synchronously. `POST /publish` and `POST /approve` call `infra.functions.publish.start_publish` and `decide`.
    ```
  - Directly under the heading `## What breaks first`, add:
    ```markdown
    - `POST /ask` is synchronous: API Gateway ends it at 29 seconds (a cut-off there is API Gateway's own timeout response, not our body). A run that fails, or a missing `ASK_STATE_MACHINE_ARN`, is 500 with `{"error": "internal", "detail": ...}`.
    ```
- [ ] **Step 3: Guards, full suite and commit**
```bash
uv run --locked pytest tests/test_dependencies.py tests/test_code_style.py --no-cov 2>&1 | tail -1
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add docs/DEVOPS_HANDOVER.md HANDOFF.md
git commit -m "Handover and HANDOFF: ask, publish and approve are built; the ask Lambda's settings; the 29 s limit"
```
Expected: `15 passed`; then START + 24 passed (`279` on the dry-run base), `TOTAL ... 97%`.

**Task done when:** `grep -n "RUN_BUDGET_USD" docs/DEVOPS_HANDOVER.md` shows the `ask` row; `grep -c "29 seconds" HANDOFF.md` prints `1`; `grep -c '"error": "internal"' HANDOFF.md` prints `1`.

### Task 3: Review, then PR (after Linus's OK)
- [ ] **Step 1:** Work through the Review Focus; write each result in the ledger. Lines 3 and 5 need Patrick, Clement and Yaw: write their answers, or "asked <name>, <time>".
- [ ] **Step 2:** `git diff develop --stat` lists only `infra/functions/api.py`, `tests/infra/functions/test_api.py`, `docs/DEVOPS_HANDOVER.md`, `HANDOFF.md`. Expected: `4 files changed`.
- [ ] **Step 3:** A fresh reviewer checks the diff against the spec, **with the security focus**: the order in `ask`, scope only from the token. Fix critical and important findings test-first.
- [ ] **Step 4: With the OK only:** `git push -u origin feature/api-ask-publish-approve`; PR to `develop`, titled "/ask, /publish and /approve entry points, Q11 refused before any run (L3)". The body: the counts, the H4 error mapping (Review Focus 4), the Y2 assumption from the spec, the rulings. No attribution lines.
- [ ] **Step 5:** L3's [[Build order]] row → `in review (PR #nn)`. Tell Yaw the entry points and the `ask` Lambda's environment; tell Huvison the exact `start_publish` / `decide` calls; tell Clement the error cases.

**Task done when:** the PR is open to `develop` and L3's [[Build order]] row says `in review (PR #nn)`.

## Done means (checklist)
- [ ] `uv run --locked pytest` prints START + 24 passed (279 on the dry-run base) and `TOTAL` ≥ 97%. *Verify:* run it.
- [ ] The Q11 test passes: the E4 lead's `/ask` about E2 is 403 `out_of_scope`, the fake state machine got no request and `ledger.runs == {}`. *Verify:* `uv run --locked pytest tests/infra/functions/test_api.py -k "q11" --no-cov` prints `1 passed`.
- [ ] A failed or unconfigured ask run is 500 `internal` with the contract body. *Verify:* `uv run --locked pytest tests/infra/functions/test_api.py -k "internal" --no-cov` prints `2 passed, 44 deselected`.
- [ ] Approval by a non-delivery lead is 403 `forbidden`. *Verify:* `uv run --locked pytest tests/infra/functions/test_api.py -k "anyone_else" --no-cov` prints `1 passed, 45 deselected`.
- [ ] H4's errors map exactly: `PublishForbidden` → 403 `forbidden`, `RunNotFound` and `NoPendingApproval` → 404 `not_found`, `NothingToPublish` → 400 `invalid_input`. *Verify:* `uv run --locked pytest tests/infra/functions/test_api.py -k "start_publish_error or no_pending" --no-cov` prints `4 passed, 42 deselected`.
- [ ] `docs/DEVOPS_HANDOVER.md` lists `RUN_BUDGET_USD` and `MAX_CLAIM_ATTEMPTS` for `ask`, and marks `infra.functions.api.publish` / `approve` as built. *Verify:* `grep -n "MAX_CLAIM_ATTEMPTS\|api.publish" docs/DEVOPS_HANDOVER.md`.
- [ ] After H2/H4/Y2 are deployed: the E4 lead's `POST /api/ask` about E2 returns 403 with `"error": "out_of_scope"`, and the ledger table has no item for that request. *Verify (in AWS, with Yaw):* `curl -s -o /dev/stderr -w "%{http_code}" -X POST -H "Authorization: Bearer <E4 lead ID token>" -d '{"entity_id":"E2","question":"What is blocking cutover for E2?"}' https://<portal domain>/api/ask` prints `403`; L6's asker records Q11 as `pass`.
- [ ] PR open or merged, no attribution lines; [[Build order]] row L3 updated. *Verify:* `gh pr view <nn> --json state`; open the note.

## Never
- Start a run, write the ledger or call a model before `scope.require` has passed.
- Take a `run_id`, a scope or a role from the request body.
- Check "is this a delivery lead?" in the handler (H4's `decide` owns that rule), or catch one of H4's exceptions in the handler: `returns_contract_errors` maps them by their base class.
- Swallow `AskSpineFailed` into a 200, or let it escape without the `internal` body.
- Push to `develop` or `main`, or add attribution lines.

Related: [[L3 - Ask, publish and approve entry points - spec]], [[L2 - Entity and rows handlers - plan]], [[Huvison - trust and flow]], [[Build order]], [[How to execute a plan]]
