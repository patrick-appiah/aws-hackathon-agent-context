---
tags: [build, plan, area/devops]
id: Y2b
owner: Yaw
spec: "[[Y2b - Standard publish flow - spec]]"
status: ready
updated: 2026-10-14
---
# Y2b: the Standard publish flow (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it. Deploying and pushing are outward-facing: ask Yaw (and Patrick for the PR) first.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Y2b - Standard publish flow - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger.
3. [[Workstreams]] (`06 Workstreams/`): the architecture with owners, the code already built, the contracts and the rules (§7).
4. [[Yaw - DevOps]]: the owner's brief; and [[Michael - DevOps]] (the other half of DevOps).
5. [[Build order]]: what this item depends on and unblocks.
6. [[M2 - App, DataStack and LedgerStack - spec]]: the CDK app, `build_stacks`, the prefix, the test fixtures and the patterns every DevOps item follows.
7. [[Y2a - Express ask spine - spec]], [[Y1 - ApiStack - spec]]; [[Huvison - trust and flow]] §5.
8. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Yaw (owner) or Huvison (publish functions). Never invent a name, a shape or a rule.

**Goal:** nothing is written until a delivery lead approves: a Standard machine waits on a task token, and only its last state may put an object, under `status-packs/`.

**Architecture:** `FlowStack` gains the publish functions and the `Publish` machine; `ApiStack` takes `ledger` and wires `/publish` and `/approve`; `API_BUNDLE` gains `infra/functions/publish.py`.

**Tech stack:** Python 3.11, `aws-cdk-lib` 2.273+ (`aws_stepfunctions`, `aws_stepfunctions_tasks`), CDK CLI 2.1144.0, pytest, uv.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. **Branch:** `feature/infra-publish-flow` from an up-to-date `develop`, **after Y2a is merged**. Task 5 additionally needs Huvison's H4 and Linus's L3.
- **Start state:** `uv run --locked pytest` → all passed, `TOTAL` 96%; write the count as **S** (dry-run: C1 + M2 + stand-ins for M3a/M3b + Y1 + Y2a, S = 257). Every count is **S + n** [dry-run].
- `eu-west-1` only (`config.DEFAULT_REGION`); Bedrock `eu.*` inference profiles only; synthetic data only; **no secrets anywhere** (no tokens, passwords or keys in code, the repo, the vault or Slack).
- Settings only in `config.py`; domain constants only in `tools/constants.py`; deploy-time constants in `infra/` modules as named constants; descriptive names; **no single-character names** (the style test scans `infra/`); no magic numbers or strings. The core (`tools/`) imports no boto3, Strands, adapters, config or os, and never imports `infra`.
- Agents reach data only through `tools/agent_tools.py`; scope is never a tool argument; prompts only in `agents/prompts/<agent>.txt`, versioned, `uv run python scripts/lock_prompts.py` (nothing here edits a prompt, but every bundle ships `agents/prompts/*.txt` and `prompts.lock`).
- **`RemovalPolicy.DESTROY` on every resource**, log groups with `LOG_RETENTION`; **stack outputs or Python attributes for every name**, never a hardcoded table, bucket, ARN or pool ID.
- **Least privilege:** one role per function and state machine; no bare `*` action or resource and no wildcard action in our statements (Y4's test enforces it over every template); no AWS managed policy on our roles (`PortalFunction` builds them).
- Never weaken a security rule (scope gate, create-once ledger, fail-closed critic, escaping, the blind critic input, the ledger-driven retry) to pass a test.
- Tests in `tests/`, mirroring the code; `uv run --locked pytest` from the repo root; coverage must not drop (96%). CDK tests never bundle (`SKIP_ALL_BUNDLING`) and never call AWS.
- **No AWS calls while building:** only `cdk synth` with credentials unset (`env -u AWS_PROFILE AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q`) and the tests. Steps marked **verify in AWS** run only after Yaw's OK, with `export AWS_PROFILE=hackathon AWS_REGION=eu-west-1`. Deploys are manual (D-018); CI never deploys.
- Branch `<type>/<short-topic>` from `develop` after the dependencies are merged; PR to `develop`; Patrick merges; never push to `develop` or `main`; **no `Co-Authored-By` and no "Generated with" lines**.
- Stay in DevOps's files: `infra/` (`app.py`, `stacks/`, `agent_runtime/`, `bundling.py`, and in `infra/functions/` *(new)* only `agent_shim.py` and the stubs), `tests/infra/` *(new; `tests/infra/functions/` is Linus's and Huvison's)* (and `Jenkinsfile` *(new)*, Michael's). Need a change elsewhere (`config.py`, `tools/`, Linus's and Huvison's modules in `infra/functions/`, `docs/`)? Ask its owner.
- No layout or "meta" guard tests: the tests check what the stacks synthesise and what the functions do.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **No write before approval:** after a publish starts, `aws s3 ls s3://<bucket>/status-packs/` shows nothing until `/approve`; after a send-back, still nothing.
2. **Only a delivery lead can approve** (Huvison's `decide`): the CFO's token on `/approve` returns 403 and the execution keeps waiting.
3. **`SendTaskSuccess` on the machine ARN works** (IAM resource-level permission for the task-token APIs): the first real `/approve` succeeds without `AccessDenied`. If it is denied, stop and tell Yaw and Patrick; never widen it to `*` without a ruling.
4. **The token never leaves AWS:** it is not logged by our functions (`grep -rn task_token infra/functions/` shows only the stub's parameter), not pasted in the ledger or Slack.
5. **A timeout is visible:** an execution left alone shows `ApprovalTimedOut` after 48 hours (or check the definition's `TimeoutSeconds` = `172800`).

---

### Task 1: The publish stand-ins

**Files:**
- Create: `infra/functions/stub_publish.py` *(new)*, `tests/infra/functions/test_stub_publish.py` *(new)*

**Produces:** `infra.functions.stub_publish.store_task_token`, `write_status_pack` (`(event, context) -> dict`). **Consumed by:** Task 2.

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync --locked && (cd infra && npm ci)
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/infra-publish-flow
```
Expected: S passed (dry-run 257), `TOTAL ... 96%`.

- [ ] **Step 2: Write the failing test.**
Create `tests/infra/functions/test_stub_publish.py`:
```python
"""The publish stand-ins store no token and write no status pack: the only write stays behind H4's approval."""
from infra.functions import stub_publish


def test_the_publish_stubs_store_nothing_and_write_nothing():
    assert stub_publish.store_task_token({"run_id": "run-0001", "task_token": "token"}, None)["stored"] is False
    assert stub_publish.write_status_pack({"run_id": "run-0001", "approval": {}}, None)["written"] is False
```

- [ ] **Step 3: Run it and watch it fail**
```bash
uv run --locked pytest tests/infra/functions/test_stub_publish.py --no-cov 2>&1 | grep -E "^E |error|passed|failed" | head -4
```
Expected: `E   ImportError: cannot import name 'stub_publish' from 'infra.functions' (unknown location)` and `1 error`.

- [ ] **Step 4: Implement.**
Create `infra/functions/stub_publish.py`:
```python
"""Stand-ins for Huvison's infra/functions/publish.py states until H4 is merged (Y2b). They prove the Standard machine waits
for a task token and continues only after SendTaskSuccess. The stub stores no token and writes no status pack:
the token is read from the execution history by hand (the Y2b plan), and the only write stays behind H4."""


def store_task_token(event, context):
    return {"run_id": event["run_id"], "stored": False}


def write_status_pack(event, context):
    return {"run_id": event["run_id"], "written": False}
```

- [ ] **Step 5: Run it, full suite, commit**
```bash
uv run --locked pytest tests/infra/functions/test_stub_publish.py --no-cov 2>&1 | tail -1
```
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/functions/stub_publish.py tests/infra/functions/test_stub_publish.py
git commit -m "infra: publish stand-ins that store no token and write nothing"
```
Expected: `1 passed`; S + 1 passed [258].

**Task done when:** `tests/infra/functions/test_stub_publish.py` → 1 passed; the full suite is at S + 1.

### Task 2: The `Publish` machine in `FlowStack`

**Files:**
- Modify: `infra/stacks/flow_stack.py` *(new)*
- Create: `tests/infra/stacks/test_publish_flow.py` *(new)*

**Produces:** `FlowStack.publish_functions`, `.publish_log_group`, `.publish_state_machine`, `.publish_start_statement()`, `.publish_decision_statement()`; output `PublishStateMachineArn`; constants `REAL_PUBLISH_MODULE`, `STUB_PUBLISH_MODULE`, `PUBLISH_STEPS_WITH_REAL_HANDLERS`, `PUBLISH_STEPS`, `TASK_TOKEN_LEDGER_ACTIONS`, `APPROVAL_WAIT`, `SENT_BACK_ERROR`. **Consumes:** `DataStack.bucket`, `status_pack_write_statement()`, `LedgerStack.ledger_statement(actions, include_rejected=False)` (M2), `PortalFunction`, `bundle_code` (Y1), `FLOW_BUNDLE` (Y2a). **Consumed by:** Task 3, Linus (`PUBLISH_STATE_MACHINE_ARN`), Huvison.

- [ ] **Step 1: Write the failing tests.**
Create `tests/infra/stacks/test_publish_flow.py`:
```python
"""FlowStack, the Standard publish flow: it waits for a task token, writes the status pack only after approval, and
only the publish writer may write, only under status-packs/."""
import json

import pytest
from aws_cdk.assertions import Template

TOKEN_PLACEHOLDER = "TOKEN"


@pytest.fixture(scope="module")
def flow_template(portal_stacks) -> Template:
    return Template.from_stack(portal_stacks.flow)


def _publish_machine(template: Template) -> dict:
    machines = template.find_resources("AWS::StepFunctions::StateMachine").values()
    (machine,) = [machine["Properties"] for machine in machines
                  if machine["Properties"]["StateMachineType"] == "STANDARD"]
    return machine


def _publish_states(template: Template) -> dict:
    parts = _publish_machine(template)["DefinitionString"]["Fn::Join"][1]
    return json.loads("".join(part if isinstance(part, str) else TOKEN_PLACEHOLDER for part in parts))["States"]


def test_the_publish_flow_is_a_standard_machine(flow_template):
    assert _publish_machine(flow_template)["TracingConfiguration"] == {"Enabled": True}


def test_it_waits_for_the_task_token_then_writes(flow_template):
    states = _publish_states(flow_template)
    wait = states["WaitForApproval"]
    assert wait["Resource"].endswith("lambda:invoke.waitForTaskToken")
    assert wait["Parameters"]["Payload"]["task_token.$"] == "$$.Task.Token"
    assert wait["Next"] == "WriteStatusPack"
    assert wait["TimeoutSeconds"] == 48 * 60 * 60


def test_send_back_ends_without_a_write(flow_template):
    wait = _publish_states(flow_template)["WaitForApproval"]
    catches = {tuple(catch["ErrorEquals"]): catch["Next"] for catch in wait["Catch"]}
    assert catches[("SentBack",)] == "SentBack"
    assert catches[("States.Timeout",)] == "ApprovalTimedOut"
    assert _publish_states(flow_template)["SentBack"]["Type"] == "Succeed"


def _policies_with(template: Template, action: str) -> list[dict]:
    return [policy["Properties"]["PolicyDocument"] for policy in template.find_resources("AWS::IAM::Policy").values()
            if action in json.dumps(policy["Properties"]["PolicyDocument"])]


def test_only_the_status_pack_writer_may_put_objects_and_only_under_status_packs(flow_template):
    (writer_policy,) = _policies_with(flow_template, "s3:PutObject")
    (put_statement,) = [statement for statement in writer_policy["Statement"] if statement["Action"] == "s3:PutObject"]
    assert put_statement["Resource"]["Fn::Join"][1][-1] == "/status-packs/*"


def test_the_publish_machine_arn_is_an_output(flow_template):
    assert "PublishStateMachineArn" in flow_template.find_outputs("*")
```

- [ ] **Step 2: Run them and watch them fail**
```bash
uv run --locked pytest tests/infra/stacks/test_publish_flow.py --no-cov 2>&1 | grep -E "^E  |passed|failed" | head -4
```
Expected: `5 failed`, with `E       ValueError: not enough values to unpack (expected 1, got 0)` (no Standard machine yet) and `E       AssertionError: assert 'PublishStateMachineArn' in {...}`.

- [ ] **Step 3: Implement.**
In `infra/stacks/flow_stack.py`, replace exactly:
```python
ASK_SPINE_TIMEOUT = Duration.minutes(2)
```
with:
```python
REAL_PUBLISH_MODULE = "infra.functions.publish"
STUB_PUBLISH_MODULE = "stub_publish"
# Publish states whose real function is merged (Huvison H4). The others run infra/functions/stub_publish.py.
PUBLISH_STEPS_WITH_REAL_HANDLERS: frozenset[str] = frozenset()
PUBLISH_STEPS = ("store_task_token", "write_status_pack")
TASK_TOKEN_LEDGER_ACTIONS = ("dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem")
APPROVAL_WAIT = Duration.hours(48)              # an unanswered publish request times out after two days
SENT_BACK_ERROR = "SentBack"                    # the error infra.functions.publish.decide sends with SendTaskFailure
ASK_SPINE_TIMEOUT = Duration.minutes(2)
```

In `infra/stacks/flow_stack.py`, replace exactly:
```python
        CfnOutput(self, "AskStateMachineArn", value=self.ask_state_machine.state_machine_arn)

    def _invoke(
```
with:
```python
        CfnOutput(self, "AskStateMachineArn", value=self.ask_state_machine.state_machine_arn)
        self.publish_functions = self._publish_functions(data, ledger, stub_code)
        self.publish_log_group = logs.LogGroup(self, "PublishLogs", retention=LOG_RETENTION,
                                               removal_policy=RemovalPolicy.DESTROY)
        self.publish_state_machine = stepfunctions.StateMachine(
            self, "Publish",
            definition_body=stepfunctions.DefinitionBody.from_chainable(self._publish_definition()),
            state_machine_type=stepfunctions.StateMachineType.STANDARD,
            tracing_enabled=True,
            logs=stepfunctions.LogOptions(destination=self.publish_log_group, level=stepfunctions.LogLevel.ALL),
            removal_policy=RemovalPolicy.DESTROY,
        )
        CfnOutput(self, "PublishStateMachineArn", value=self.publish_state_machine.state_machine_arn)

    def _publish_functions(self, data: DataStack, ledger: LedgerStack,
                           stub_code: lambda_.Code) -> dict[str, PortalFunction]:
        """store_task_token writes the token to the ledger; write_status_pack is the system's only S3 write."""
        environment = {"LEDGER_BACKEND": DYNAMO_LEDGER_BACKEND, "LEDGER_TABLE": ledger.ledger_table.table_name,
                       "ARTEFACTS_BUCKET": data.bucket.bucket_name}
        token_statement = ledger.ledger_statement(TASK_TOKEN_LEDGER_ACTIONS, include_rejected=False)
        statements = {"store_task_token": [token_statement],
                      "write_status_pack": [token_statement, data.status_pack_write_statement()]}
        publish_code = bundle_code(self, FLOW_BUNDLE) if PUBLISH_STEPS_WITH_REAL_HANDLERS else stub_code
        functions = {}
        for step_name in PUBLISH_STEPS:
            is_real = step_name in PUBLISH_STEPS_WITH_REAL_HANDLERS
            functions[step_name] = PortalFunction(
                self, f"{_construct_name(step_name)}Function",
                handler=f"{REAL_PUBLISH_MODULE if is_real else STUB_PUBLISH_MODULE}.{step_name}",
                code=publish_code if is_real else stub_code,
                environment=environment, statements=statements[step_name], timeout=LEDGER_STEP_TIMEOUT)
        return functions

    def _publish_definition(self) -> stepfunctions.IChainable:
        """Wait for a human: the token goes to the ledger, and only SendTaskSuccess from /approve continues."""
        wait_for_approval = tasks.LambdaInvoke(
            self, "WaitForApproval",
            lambda_function=self.publish_functions["store_task_token"].function,
            integration_pattern=stepfunctions.IntegrationPattern.WAIT_FOR_TASK_TOKEN,
            payload=stepfunctions.TaskInput.from_object({"run_id.$": "$.run_id",
                                                         "task_token": stepfunctions.JsonPath.task_token}),
            result_path="$.approval",
            task_timeout=stepfunctions.Timeout.duration(APPROVAL_WAIT),
        )
        write_status_pack = tasks.LambdaInvoke(
            self, "WriteStatusPack",
            lambda_function=self.publish_functions["write_status_pack"].function,
            payload=stepfunctions.TaskInput.from_object({"run_id.$": "$.run_id", "approval.$": "$.approval"}),
            payload_response_only=True,
            result_path="$.status_pack",
        )
        sent_back = stepfunctions.Succeed(self, "SentBack", comment="Sent back by the approver: nothing written")
        timed_out = stepfunctions.Fail(self, "ApprovalTimedOut", error="ApprovalTimedOut",
                                       cause="nobody approved or sent back within the wait")
        wait_for_approval.add_catch(sent_back, errors=[SENT_BACK_ERROR], result_path="$.sent_back")
        wait_for_approval.add_catch(timed_out, errors=[stepfunctions.Errors.TIMEOUT], result_path="$.timeout")
        published = stepfunctions.Succeed(self, "Published")
        return wait_for_approval.next(write_status_pack).next(published)

    def publish_start_statement(self) -> iam.PolicyStatement:
        """For the /publish Lambda only."""
        return iam.PolicyStatement(actions=["states:StartExecution"],
                                   resources=[self.publish_state_machine.state_machine_arn])

    def publish_decision_statement(self) -> iam.PolicyStatement:
        """For the /approve Lambda only: answer the waiting task, approve or send back."""
        return iam.PolicyStatement(actions=["states:SendTaskSuccess", "states:SendTaskFailure"],
                                   resources=[self.publish_state_machine.state_machine_arn])

    def _invoke(
```

- [ ] **Step 4: Run them**
```bash
uv run --locked pytest tests/infra/stacks/test_publish_flow.py --no-cov 2>&1 | tail -1
```
Expected: `5 passed`.

- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/stacks/flow_stack.py tests/infra/stacks/test_publish_flow.py
git commit -m "infra: Standard publish flow that waits for a human's task token before the only write"
```
Expected: S + 6 passed [263].

**Task done when:** `tests/infra/stacks/test_publish_flow.py` → 5 passed; the full suite is at S + 6.

### Task 3: Wire `/publish` and `/approve`; the API bundle carries `infra/functions/publish.py`

**Files:**
- Modify: `infra/stacks/api_stack.py` *(new)*, `infra/bundling.py` *(new)*, `infra/app.py` *(new)*, `tests/infra/stacks/test_publish_flow.py`, `tests/infra/test_bundling.py` *(new)*

**Produces:** `ApiStack(scope, construct_id, *, data, auth, flow, ledger, **kwargs)`; `_environment_for(route, flow, ledger)`, `_statements_for(route, data, flow, ledger)`; `API_BUNDLE` with `infra/functions/publish.py`. **Consumes:** Task 2's statements; `DYNAMO_LEDGER_BACKEND` (Y2a). **Consumed by:** Linus (L3).

- [ ] **Step 1: Write the failing tests.**
Append to `tests/infra/stacks/test_publish_flow.py` (keep everything already there):
```python


def test_publish_starts_and_approve_answers_the_publish_run(portal_stacks):
    api_template = Template.from_stack(portal_stacks.api)
    assert len(_policies_with(api_template, "states:StartExecution")) == 1
    assert len(_policies_with(api_template, "states:SendTaskSuccess")) == 1
    for function in api_template.find_resources("AWS::Lambda::Function").values():
        variables = function["Properties"]["Environment"]["Variables"]
        if "PUBLISH_STATE_MACHINE_ARN" in variables:
            assert variables["LEDGER_BACKEND"] == "dynamo" and "LEDGER_TABLE" in variables
```

Append to `tests/infra/test_bundling.py` (keep everything already there):
```python


def test_the_api_bundle_carries_the_publish_module_for_publish_and_approve(tmp_path):
    bundle = build_bundle(API_BUNDLE, repo_root=_fake_repo(tmp_path), output_root=tmp_path / "build",
                          install=_record_install([]))
    assert (bundle / "infra" / "functions" / "publish.py").exists()
```

- [ ] **Step 2: Run them and watch them fail**
```bash
uv run --locked pytest tests/infra/stacks/test_publish_flow.py tests/infra/test_bundling.py --no-cov 2>&1 | grep -E "^E  |passed|failed" | head -4
```
Expected: `2 failed, 9 passed`, with `E       AssertionError: assert 0 == 1` (no `StartExecution` yet) and `E       AssertionError: assert False` (no `infra/functions/publish.py` *(new)* in the bundle).

- [ ] **Step 3: Implement.**
In `infra/stacks/api_stack.py`, replace exactly:
```python
from infra.stacks.flow_stack import FlowStack
```
with:
```python
from infra.stacks.flow_stack import DYNAMO_LEDGER_BACKEND, FlowStack
from infra.stacks.ledger_stack import LedgerStack
```

In `infra/stacks/api_stack.py`, replace exactly:
```python
auth: AuthStack, flow: FlowStack,
                 **kwargs) -> None:
```
with:
```python
auth: AuthStack, flow: FlowStack,
                 ledger: LedgerStack, **kwargs) -> None:
```

In `infra/stacks/api_stack.py`, replace exactly:
```python
                environment={**base_environment, **self._environment_for(route, flow)},
                statements=self._statements_for(route, data, flow),
```
with:
```python
                environment={**base_environment, **self._environment_for(route, flow, ledger)},
                statements=self._statements_for(route, data, flow, ledger),
```

In `infra/stacks/api_stack.py`, replace everything from the line `@staticmethod` (the `_environment_for` method) to the end of the file with:
```python
    @staticmethod
    def _environment_for(route: ApiRoute, flow: FlowStack, ledger: LedgerStack) -> dict[str, str]:
        """What a route needs beyond the data settings: /ask, /publish and /approve reach the flow (the handover)."""
        publish_environment = {"PUBLISH_STATE_MACHINE_ARN": flow.publish_state_machine.state_machine_arn,
                               "LEDGER_BACKEND": DYNAMO_LEDGER_BACKEND, "LEDGER_TABLE": ledger.ledger_table.table_name}
        extra_environment = {"ask": {"ASK_STATE_MACHINE_ARN": flow.ask_state_machine.state_machine_arn},
                             "publish": publish_environment, "approve": publish_environment}
        return extra_environment.get(route.name, {})

    @staticmethod
    def _statements_for(route: ApiRoute, data: DataStack, flow: FlowStack,
                        ledger: LedgerStack) -> list[iam.PolicyStatement]:
        """Every route reads artefacts/; /ask starts the ask spine; /publish and /approve drive the publish run."""
        read_ledger = ledger.ledger_statement(("dynamodb:GetItem",), include_rejected=False)
        log_send_back = ledger.ledger_statement(("dynamodb:GetItem", "dynamodb:UpdateItem"), include_rejected=False)
        extra_statements = {"ask": [flow.ask_start_statement()],
                            "publish": [flow.publish_start_statement(), read_ledger],
                            "approve": [flow.publish_decision_statement(), log_send_back]}
        return [data.artefacts_read_statement(), *extra_statements.get(route.name, [])]
```

In `infra/bundling.py`, replace exactly:
```python
API_BUNDLE = BundleSpec("api", (*CORE_CODE, "infra/functions/__init__.py", "infra/functions/api.py", "infra/functions/scope.py"))
```
with:
```python
API_BUNDLE = BundleSpec("api", (*CORE_CODE, "infra/functions/__init__.py", "infra/functions/api.py", "infra/functions/scope.py",
                               "infra/functions/publish.py"))   # /publish and /approve call infra.functions.publish
```

  In `infra/app.py`, pass the ledger to the API: `api = ApiStack(app, "ApiStack", data=data, auth=auth, flow=flow, ledger=ledger, **stack_options("ApiStack"))` (wrap under 120 characters).

- [ ] **Step 4: Run them, full suite, synth, commit**
```bash
uv run --locked pytest tests/infra/stacks/test_publish_flow.py tests/infra/test_bundling.py --no-cov 2>&1 | tail -1
```
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/stacks/api_stack.py infra/bundling.py infra/app.py tests/infra/stacks/test_publish_flow.py tests/infra/test_bundling.py
git commit -m "infra: publish may start and approve may answer the publish run; the API bundle carries infra/functions/publish.py"
```
```bash
cd infra && env -u AWS_PROFILE -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q 2>&1 | grep -E "Successfully|rror"; cd ..
grep -c '"StateMachineType": "STANDARD"' infra/cdk.out/FlowStack.template.json
```
Expected: `11 passed`; S + 8 passed [265], `TOTAL ... 96%`; `Successfully synthesized`; `1`. (While the `api` routes still run stubs the synth needs no `infra/functions/publish.py`; once Task 5 makes them real it bundles it.)

**Task done when:** the full suite is at S + 8 with 96%; the synthesized FlowStack has one Standard machine.

### Task 4: Deploy and prove the wait (verify in AWS; ask Yaw first)

**Files:** none.

- [ ] **Step 1: Deploy**
```bash
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
cd infra && npx cdk deploy FlowStack ApiStack --require-approval never 2>&1 | grep -E "✅|PublishStateMachineArn"; cd ..
PUBLISH_ARN=$(aws cloudformation describe-stacks --stack-name demo-FlowStack --query "Stacks[0].Outputs[?OutputKey=='PublishStateMachineArn'].OutputValue" --output text)
```
Expected (verify in AWS): both stacks `✅`; `PublishStateMachineArn = arn:aws:states:eu-west-1:796973512193:stateMachine:Publish...`.

- [ ] **Step 2: Start one, see it wait, approve it by hand**
```bash
EXECUTION=$(aws stepfunctions start-execution --state-machine-arn "$PUBLISH_ARN" --input '{"run_id": "run-publish-1", "requested_by": "user-delivery-lead"}' --query executionArn --output text)
aws stepfunctions describe-execution --execution-arn "$EXECUTION" --query status --output text
TOKEN=$(aws stepfunctions get-execution-history --execution-arn "$EXECUTION" --query "events[?type=='TaskScheduled'].taskScheduledEventDetails.parameters" --output text | python3 -c "import json,sys; print(json.loads(sys.stdin.read())['Payload']['task_token'])")
aws stepfunctions send-task-success --task-token "$TOKEN" --task-output '{"decision": "approve", "note": "", "approver": "user-delivery-lead"}'; unset TOKEN
aws stepfunctions describe-execution --execution-arn "$EXECUTION" --query status --output text
```
Expected (verify in AWS): `RUNNING` (waiting at `WaitForApproval`), then after the token `SUCCEEDED` (through `WriteStatusPack`, which the stub makes a no-op). Repeat with `send-task-failure --task-token "$TOKEN" --error SentBack` on a second execution: `SUCCEEDED` at the `SentBack` state. Never paste the token anywhere.

**Task done when:** two ledger lines: one approved execution `SUCCEEDED` via `Published`, one sent back `SUCCEEDED` via `SentBack`.

### Task 5: Switch to Huvison's publish functions and the real routes (after H4 and L3)

**Files:**
- Modify: `infra/stacks/flow_stack.py`, `infra/stacks/api_stack.py`

- [ ] **Step 1: Bring them in.**
```bash
git fetch origin && git rebase origin/develop
grep -n "^def store_task_token\|^def write_status_pack\|^def start_publish\|^def decide" infra/functions/publish.py
grep -n "^def publish\|^def approve" infra/functions/api.py
```
Expected: four `def` lines in `infra/functions/publish.py` and two in `infra/functions/api.py` *(new)*. If `store_task_token` or `write_status_pack` has another name, stop and agree it with Huvison (spec §1 Assumptions).

- [ ] **Step 2: Switch.** In `infra/stacks/flow_stack.py`, replace the line that starts with `PUBLISH_STEPS_WITH_REAL_HANDLERS` with:
```python
PUBLISH_STEPS_WITH_REAL_HANDLERS = frozenset({"store_task_token", "write_status_pack"})
```
  In `infra/stacks/api_stack.py`, make the `ROUTES_WITH_REAL_HANDLERS` line list every route that is merged, which after L3 is all six: `ROUTES_WITH_REAL_HANDLERS = frozenset({"summary", "entity", "rows", "ask", "publish", "approve"})`.

- [ ] **Step 3: Tests and a bundling synth**
```bash
uv run --locked pytest tests/infra --no-cov 2>&1 | tail -1
cd infra && env -u AWS_PROFILE -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q 2>&1 | grep -E "Successfully|rror"; cd ..
ls infra/cdk.out/bundles/api/infra/functions/publish.py infra/cdk.out/bundles/flow/infra/functions/publish.py
```
Expected: all `tests/infra` passed, the same count as before the switch (dry-run: the switch changes no test count); `Successfully synthesized`; both files listed. (Dry-run note: `infra/functions/api.py`, `infra/functions/scope.py` *(new)* and the other `infra/functions/` modules didn't exist when this plan was written, so its synth was dry-run with empty stand-in packages; on `develop` they are the real ones.)

- [ ] **Step 4: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/stacks/flow_stack.py infra/stacks/api_stack.py
git commit -m "infra: publish runs Huvison's functions; publish and approve run Linus's handlers"
```
Expected: S + 8 passed plus the tests H4/L3 brought, `TOTAL` not below 96%.

- [ ] **Step 5: End to end (verify in AWS; ask Yaw first)**
```bash
cd infra && npx cdk deploy FlowStack ApiStack --require-approval never 2>&1 | grep "✅"; cd ..
BUCKET=$(aws cloudformation describe-stacks --stack-name demo-DataStack --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text)
read -rs ID_TOKEN   # the delivery lead's ID token
curl -s -X POST -H "Authorization: Bearer $ID_TOKEN" -H "Content-Type: application/json" -d '{"run_id": "<a run_id from /ask>"}' "$API_URL/publish"; echo
aws s3 ls "s3://$BUCKET/status-packs/"
curl -s -X POST -H "Authorization: Bearer $ID_TOKEN" -H "Content-Type: application/json" -d '{"run_id": "<the same run_id>", "decision": "approve"}' "$API_URL/approve"; echo; unset ID_TOKEN
sleep 5; aws s3 ls "s3://$BUCKET/status-packs/"
```
Expected (verify in AWS): `/publish` → `{"run_id": ..., "execution_arn": ..., "status": "awaiting_approval"}`; the first `ls` lists nothing; `/approve` → `{"run_id": ..., "status": "approved"}`; the second `ls` lists `<run_id>.json`.

**Task done when:** the status pack appears only after `/approve` (two `ls` lines in the ledger: empty, then the file).

### Task 6: Review, then PR (after Yaw's and Patrick's OK)
- [ ] **Step 1:** Work through the Review Focus; write each result in the ledger.
- [ ] **Step 2:** `git diff origin/develop --stat` touches only `infra/` and `tests/infra/`.
- [ ] **Step 3:** Push `feature/infra-publish-flow`; PR to `develop` titled "FlowStack: Standard publish flow with human approval". Body: the machine (spec §1), the IAM table, the two handover deviations (`UpdateItem` on `/approve`; the two publish function names), the AWS checks, the rulings. No attribution lines.
- [ ] **Step 4:** Tell Huvison, Linus and Clement (F5). Update [[Build order]].

**Task done when:** the PR is open to `develop` with green Jenkins; [[Build order]] shows Y2b `in review (PR #nn)`.

## Done means
- [ ] `uv run --locked pytest` → S + 8 passed, `TOTAL` ≥ 96%. *Verify:* run it.
- [ ] `infra/cdk.out/FlowStack.template.json` *(new)* has one `STANDARD` machine whose `WaitForApproval` resource ends in `lambda:invoke.waitForTaskToken`; exactly one IAM policy in the template contains `s3:PutObject`, on `/status-packs/*`. *Verify:* `tests/infra/stacks/test_publish_flow.py` passing, and `grep -c waitForTaskToken infra/cdk.out/FlowStack.template.json` ≥ 1.
- [ ] Deployed: a manual execution waits (`RUNNING`), then `SUCCEEDED` after `send-task-success`; a send-back ends at `SentBack`. *Verify in AWS:* the ledger lines and the console's execution graph.
- [ ] After H4/L3: no object under `status-packs/` before `/approve`, one after. *Verify in AWS:* `aws s3 ls` before and after.
- [ ] The PR is open (or merged) to `develop`; [[Build order]] row Y2b updated. *Verify:* the PR page.

## Never
- Give any role but the status-pack writer `s3:PutObject`, or give it any prefix but `status-packs/`.
- Write the status pack in a state before `WaitForApproval` returns, or catch `SentBack` into `WriteStatusPack`.
- Paste, log or store a task token outside the ledger.
- Run `cdk deploy` or `aws` commands before Yaw's OK; push to `develop` or `main`; add attribution lines.

Related: [[Build order]], [[Yaw - DevOps]], [[Workstreams]]
