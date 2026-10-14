---
tags: [build, plan, area/devops]
id: Y3b
owner: Yaw
spec: "[[Y3b - Agent shim and host switch - spec]]"
status: ready
updated: 2026-10-14
---
# Y3b: the agent shim and the `agent_host` switch (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it. Deploying and pushing are outward-facing: ask Yaw (and Patrick for the PR) first.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Y3b - Agent shim and host switch - spec]]: **the authority.**
3. [[Workstreams]] (`06 Workstreams/`): the architecture with owners, the code already built, the contracts and the rules (§7).
4. [[Yaw - DevOps]]: the owner's brief; and [[Michael - DevOps]] (the other half of DevOps).
5. [[Build order]]: what this item depends on and unblocks.
6. [[M2 - App, DataStack and LedgerStack - spec]]: the CDK app, `build_stacks`, the prefix, the test fixtures and the patterns every DevOps item follows.
7. [[Y3a - AgentCore runtime - spec]], [[Y2a - Express ask spine - spec]], [[Y2b - Standard publish flow - spec]].

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Yaw (owner). Never invent a name, a shape or a rule.

**Goal:** by default the ask spine's agent steps run on AgentCore through one shim Lambda; `-c agent_host=lambda` brings back Y2a's in-Lambda agents.

**Architecture:** new `infra/functions/agent_shim.py` *(new)*; `FlowStack` takes `agent` and the `agent_host` context; `_invoke` routes agent steps to the shim in `agentcore` mode.

**Tech stack:** Python 3.11, `boto3` (`bedrock-agentcore` client) in the shim bundle, `aws-cdk-lib` 2.273+, pytest, uv.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. **Branch:** `feature/infra-agent-shim` from an up-to-date `develop`, **after Y3a and Y2b are merged**.
- **Start state:** `uv run --locked pytest` → all passed, `TOTAL` 96%; write the count as **S** (dry-run: C1 + M2 + stand-ins for M3a/M3b + Y1 + Y2a + Y2b + Y3a, S = 277). Every count is **S + n** [dry-run].
- `eu-west-1` only (`config.DEFAULT_REGION`); Bedrock `eu.*` inference profiles only; synthetic data only; **no secrets anywhere** (no tokens, passwords or keys in code, the repo, the vault or Slack).
- Settings only in `config.py`; domain constants only in `tools/constants.py`; deploy-time constants in `infra/` modules as named constants; descriptive names; **no single-character names** (the style test scans `infra/`); no magic numbers or strings. The core (`tools/`) imports no boto3, Strands, adapters, config or os, and never imports `infra`.
- Agents reach data only through `tools/agent_tools.py`; scope is never a tool argument; prompts only in `agents/prompts/<agent>.txt`, versioned, `uv run python scripts/lock_prompts.py` (nothing here edits a prompt, but every bundle ships `agents/prompts/*.txt` and `prompts.lock`).
- **`RemovalPolicy.DESTROY` on every resource**, log groups with `LOG_RETENTION`; **stack outputs or Python attributes for every name**, never a hardcoded table, bucket, ARN or pool ID.
- **Least privilege:** one role per function and state machine; no bare `*` action or resource and no wildcard action in our statements (Y4's test enforces it over every template); no AWS managed policy on our roles (`PortalFunction` builds them).
- Never weaken a security rule (scope gate, create-once ledger, fail-closed critic, escaping, the blind critic input, the ledger-driven retry) to pass a test.
- Tests in `tests/`, mirroring the code; `uv run --locked pytest` from the repo root; coverage must not drop (96%). CDK tests never bundle (`SKIP_ALL_BUNDLING`) and never call AWS.
- **No AWS calls while building:** only `cdk synth` with credentials unset (`env -u AWS_PROFILE AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q`) and the tests. Steps marked **verify in AWS** run only after Yaw's OK, with `export AWS_PROFILE=hackathon AWS_REGION=eu-west-1`. Deploys are manual (D-018); CI never deploys.
- Branch `<type>/<short-topic>` from `develop` after the dependencies are merged; PR to `develop`; Patrick merges; never push to `develop` or `main`; **no `Co-Authored-By` and no "Generated with" lines**.
- Stay in DevOps's files: `infra/`, `tests/infra/` *(new)* (and `Jenkinsfile` *(new)*, Michael's). Need a change elsewhere (`config.py`, `api/`, `flow/`, `docs/`)? Ask its owner.
- No layout or "meta" guard tests: the tests check what the stacks synthesise and what the functions do.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **Same answer on both hosts:** the E4 question's claim IDs and citations match between `agentcore` and `lambda` (Task 3); differences in wording are fine, different citations are not.
2. **The shim's boto3 knows `bedrock-agentcore`:** its first invocation doesn't fail with `UnknownServiceError`.
3. **The critic stays blind through the shim:** the runtime receives `input` = `{run_id, claim, scope}` for `judge_claim` (execution history, `JudgeClaim` input).
4. **Session reuse:** a run's steps reuse one session (the runtime's logs show one session ID per run).
5. **The fallback is one command:** `npx cdk deploy FlowStack -c agent_host=lambda` (and back) works without code changes; record which host the demo uses in `HANDOFF.md` (Task 3).

---

### Task 1: The shim (`infra/functions/agent_shim.py`)

**Files:**
- Create: `infra/functions/agent_shim.py`, `tests/infra/functions/test_agent_shim.py` *(new)*

**Produces:** `invoke_step(client, event) -> dict`, `session_id(run_id) -> str`, `AgentRuntimeError`, `handler(event, context)`. **Consumed by:** Task 2.

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync --locked && (cd infra && npm ci)
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/infra-agent-shim
```
Expected: S passed (dry-run 277), `TOTAL ... 96%`.

- [ ] **Step 2: Write the failing test.**
Create `tests/infra/functions/test_agent_shim.py`:
```python
"""The AgentCore shim (infra/functions/agent_shim.py): forwards {step, input} to the one runtime, one session per
run, and fails loudly when the runtime does."""
import io
import json

import pytest

from infra.functions.agent_shim import AgentRuntimeError, invoke_step, session_id

RUNTIME_ARN = "arn:aws:bedrock-agentcore:eu-west-1:111111111111:runtime/test_erp_portal_agents-abc"
JUDGE_EVENT = {"runtime_arn": RUNTIME_ARN, "step": "judge_claim",
               "input": {"run_id": "run-0001", "claim": {"claim_id": "claim-1"}, "scope": {}}}


class FakeAgentCore:
    def __init__(self, status_code: int, body: dict):
        self.status_code, self.body, self.calls = status_code, body, []

    def invoke_agent_runtime(self, **request):
        self.calls.append(request)
        return {"statusCode": self.status_code, "response": io.BytesIO(json.dumps(self.body).encode())}


def test_the_step_and_its_input_reach_the_runtime_and_the_output_comes_back():
    client = FakeAgentCore(200, {"claim_id": "claim-1", "passed": True})
    assert invoke_step(client, JUDGE_EVENT) == {"claim_id": "claim-1", "passed": True}
    (call,) = client.calls
    assert call["agentRuntimeArn"] == RUNTIME_ARN
    assert json.loads(call["payload"]) == {"step": "judge_claim", "input": JUDGE_EVENT["input"]}


def test_every_step_of_a_run_shares_one_long_enough_session():
    orchestrator_event = {"runtime_arn": RUNTIME_ARN, "step": "run_orchestrator",
                          "input": {"question": {"run_id": "run-0001"}, "replan_claim_id": None}}
    client = FakeAgentCore(200, {})
    invoke_step(client, JUDGE_EVENT)
    invoke_step(client, orchestrator_event)
    first, second = (call["runtimeSessionId"] for call in client.calls)
    assert first == second == session_id("run-0001") and len(first) >= 33


def test_a_runtime_failure_fails_the_step():
    with pytest.raises(AgentRuntimeError, match="judge_claim"):
        invoke_step(FakeAgentCore(500, {"error": "step_failed"}), JUDGE_EVENT)
```

- [ ] **Step 3: Run it and watch it fail**
```bash
uv run --locked pytest tests/infra/functions/test_agent_shim.py --no-cov 2>&1 | grep -E "^E |error|passed|failed" | head -4
```
Expected: `E   ModuleNotFoundError: No module named 'infra.functions.agent_shim'` and `1 error`.

- [ ] **Step 4: Implement.**
Create `infra/functions/agent_shim.py`:
```python
"""The shim Step Functions calls for an agent step when the agents run on AgentCore (Y3b): Step Functions can't
invoke a runtime directly. It forwards {step, input} to the runtime and returns the step's output unchanged.

Event: {"runtime_arn": <AgentStack's runtime>, "step": <agent step>, "input": <that step's input>}. IAM lets this
function invoke that one runtime only. One session per run, so a run's steps reuse a warm runtime.
"""
import hashlib
import json

HTTP_OK = 200
JSON_CONTENT_TYPE = "application/json"
AGENTCORE_SERVICE = "bedrock-agentcore"


class AgentRuntimeError(RuntimeError):
    """The runtime refused or failed the step; the state machine fails the run (no silent pass)."""


def session_id(run_id: str) -> str:
    """AgentCore wants 33+ characters: the run ID's SHA-256, so every step of one run shares a session."""
    return hashlib.sha256(run_id.encode()).hexdigest()


def _run_id(step_input: dict) -> str:
    return step_input.get("run_id") or step_input["question"]["run_id"]


def invoke_step(client, event: dict) -> dict:
    payload = {"step": event["step"], "input": event["input"]}
    response = client.invoke_agent_runtime(agentRuntimeArn=event["runtime_arn"],
                                           runtimeSessionId=session_id(_run_id(event["input"])),
                                           payload=json.dumps(payload).encode(), contentType=JSON_CONTENT_TYPE,
                                           accept=JSON_CONTENT_TYPE)
    body = json.loads(response["response"].read())
    if response.get("statusCode", HTTP_OK) != HTTP_OK:
        raise AgentRuntimeError(f"{event['step']} failed in the runtime: {body}")
    return body


def handler(event, context):
    import boto3  # bundled with the shim (a boto3 that knows bedrock-agentcore)
    return invoke_step(boto3.client(AGENTCORE_SERVICE), event)
```

- [ ] **Step 5: Run it, full suite, commit**
```bash
uv run --locked pytest tests/infra/functions/test_agent_shim.py --no-cov 2>&1 | tail -1
```
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/functions/agent_shim.py tests/infra/functions/test_agent_shim.py
git commit -m "infra: shim that forwards an agent step to AgentCore, one session per run"
```
Expected: `3 passed`; S + 3 passed [280].

**Task done when:** `tests/infra/functions/test_agent_shim.py` → 3 passed; the full suite is at S + 3.

### Task 2: The `agent_host` switch in `FlowStack`

**Files:**
- Modify: `infra/bundling.py` *(new)*, `infra/stacks/flow_stack.py` *(new)*, `infra/app.py` *(new)*, `tests/infra/stacks/test_flow_stack.py` *(new)*
- Create: `tests/infra/stacks/test_agent_host.py` *(new)*

**Produces:** `AGENT_SHIM_BUNDLE`; `FlowStack(scope, construct_id, *, data, ledger, guardrail, agent, **kwargs)` with `.agent_host`, `.agent_runtime_arn`, `.agent_shim` (agentcore mode); `AGENT_HOST_CONTEXT_KEY`, `AGENT_HOST_AGENTCORE`, `AGENT_HOST_LAMBDA`, `AGENT_HOSTS`, `AGENT_SHIM_HANDLER`, `agent_host_from_context(value)`. **Consumes:** `AgentStack.runtime`, `.invoke_statement()` (Y3a); the `stacks_with_context` fixture (Y1). **Consumed by:** Y4 (both hosts), M5 (the fallback command).

- [ ] **Step 1: Write the failing tests** (the new file, and the flow tests pinned to the Lambda path).
Create `tests/infra/stacks/test_agent_host.py`:
```python
"""The agent_host switch (Y3b): by default the agent steps run on AgentCore through the shim, with the same blind
inputs; `-c agent_host=lambda` is the documented fallback; a typo fails the synth."""
import json

import pytest
from aws_cdk.assertions import Template

from infra.stacks.flow_stack import ASK_STEPS, agent_host_from_context

TOKEN_PLACEHOLDER = "TOKEN"
AGENT_STEP_NAMES = {step.name for step in ASK_STEPS if step.runs_agents}


@pytest.fixture(scope="module")
def flow_template(portal_stacks) -> Template:
    return Template.from_stack(portal_stacks.flow)


def _ask_states(template: Template) -> dict:
    machines = template.find_resources("AWS::StepFunctions::StateMachine").values()
    (machine,) = [machine["Properties"] for machine in machines
                  if machine["Properties"]["StateMachineType"] == "EXPRESS"]
    parts = machine["DefinitionString"]["Fn::Join"][1]
    return json.loads("".join(part if isinstance(part, str) else TOKEN_PLACEHOLDER for part in parts))["States"]


def test_agentcore_is_the_default_and_agent_steps_have_no_lambda_of_their_own(flow_template):
    handlers = [function["Properties"]["Handler"]
                for function in flow_template.find_resources("AWS::Lambda::Function").values()]
    assert "agent_shim.handler" in handlers
    assert not [handler for handler in handlers if handler.split(".")[-1] in AGENT_STEP_NAMES]


def test_the_shim_carries_the_step_name_and_the_same_blind_critic_input(flow_template):
    judge_claim = _ask_states(flow_template)["JudgeEachClaim"]["ItemProcessor"]["States"]["JudgeClaim"]
    assert judge_claim["Parameters"]["step"] == "judge_claim"
    assert set(judge_claim["Parameters"]["input"]) == {"run_id.$", "claim.$", "scope.$"}


def test_only_the_shim_may_invoke_the_runtime(flow_template):
    invokers = [policy for policy in flow_template.find_resources("AWS::IAM::Policy").values()
                if "bedrock-agentcore:InvokeAgentRuntime" in json.dumps(policy)]
    assert len(invokers) == 1
    assert "bedrock:InvokeModel" not in json.dumps(invokers[0])


def test_a_mistyped_agent_host_fails_the_synth():
    with pytest.raises(ValueError, match="agent_host"):
        agent_host_from_context("agentcor")
```

Create `tests/infra/stacks/test_flow_stack.py`:
```python
"""FlowStack, the Express ask spine: the states and their order, the ledger-driven retry Choice, a blind critic,
and one least-privilege Lambda per step."""
import json

import pytest
from aws_cdk.assertions import Template

from infra.stacks.flow_stack import AGENT_HOST_CONTEXT_KEY, AGENT_HOST_LAMBDA, ASK_STEPS

TOKEN_PLACEHOLDER = "TOKEN"
CRITIC_INPUT_KEYS = {"run_id.$", "claim.$", "scope.$"}


@pytest.fixture(scope="module")
def flow_template(stacks_with_context) -> Template:
    """The Lambda path (-c agent_host=lambda): every step, agents included, is its own Lambda."""
    return Template.from_stack(stacks_with_context({AGENT_HOST_CONTEXT_KEY: AGENT_HOST_LAMBDA}).flow)


def _state_machine(template: Template, machine_type: str = "EXPRESS") -> dict:
    (state_machine,) = [state_machine["Properties"]
                        for state_machine in template.find_resources("AWS::StepFunctions::StateMachine").values()
                        if state_machine["Properties"]["StateMachineType"] == machine_type]
    return state_machine


def _definition(template: Template, machine_type: str = "EXPRESS") -> dict:
    """The ASL with every CloudFormation token (a Lambda ARN) replaced by a placeholder string."""
    parts = _state_machine(template, machine_type)["DefinitionString"]["Fn::Join"][1]
    return json.loads("".join(part if isinstance(part, str) else TOKEN_PLACEHOLDER for part in parts))


def _iteration_states(template: Template) -> dict:
    return _definition(template)["States"]["JudgeEachClaim"]["ItemProcessor"]["States"]


def test_the_ask_spine_is_an_express_machine_with_full_logs_and_tracing(flow_template):
    properties = _state_machine(flow_template)
    assert properties["StateMachineType"] == "EXPRESS"
    assert properties["TracingConfiguration"] == {"Enabled": True}
    assert properties["LoggingConfiguration"]["Level"] == "ALL"
    assert properties["LoggingConfiguration"]["IncludeExecutionData"] is True


def test_the_states_run_in_the_contract_order(flow_template):
    states = _definition(flow_template)["States"]
    assert _definition(flow_template)["StartAt"] == "Start"
    assert states["Start"]["Next"] == "CheckBudget"
    assert states["CheckBudget"]["Next"] == "BudgetLeft"
    assert states["BudgetLeft"]["Default"] == "RunOrchestrator"
    assert states["BudgetLeft"]["Choices"][0]["Next"] == "WritePartialAnswer"
    assert states["RunOrchestrator"]["Next"] == "StoreClaims"
    assert states["StoreClaims"]["Next"] == "JudgeEachClaim"
    assert states["JudgeEachClaim"]["Next"] == "WriteAnswer"
    assert states["WriteAnswer"]["Next"] == "Answer"


def test_the_retry_is_a_choice_on_the_ledger_decision_never_a_model_output(flow_template):
    iteration = _iteration_states(flow_template)
    assert iteration["ClaimPassed"]["Default"] == "RetryDecision"
    assert iteration["RetryDecision"]["Next"] == "RetryOrReject"
    (retry_rule,) = iteration["RetryOrReject"]["Choices"]
    assert retry_rule == {"Variable": "$.retry.decision", "StringEquals": "retry", "Next": "ReplanClaim"}
    assert iteration["RetryOrReject"]["Default"] == "RecordRejection"
    assert iteration["UseRevisedClaim"]["Next"] == "JudgeClaim"


def test_the_critic_gets_only_the_run_id_the_claim_and_the_scope(flow_template):
    judge_claim = _iteration_states(flow_template)["JudgeClaim"]
    assert set(judge_claim["Parameters"]) == CRITIC_INPUT_KEYS


def test_only_passed_claims_reach_the_writer(flow_template):
    payload = _definition(flow_template)["States"]["WriteAnswer"]["Parameters"]
    assert payload["passed_claims.$"] == "$.judged[?(@.passed == true)].claim"


def _functions(template: Template) -> list[dict]:
    return [function["Properties"] for function in template.find_resources("AWS::Lambda::Function").values()]


def test_one_function_with_its_own_role_per_ask_step(flow_template):
    step_handlers = [function["Handler"].split(".")[-1] for function in _functions(flow_template)]
    for step in ASK_STEPS:
        assert step_handlers.count(step.name) == 1, step.name
    roles = [str(function["Role"]) for function in _functions(flow_template)]
    assert len(set(roles)) == len(roles)


def test_only_agent_steps_get_the_guardrail_and_the_artefacts(flow_template):
    agent_steps = {step.name for step in ASK_STEPS if step.runs_agents}
    for function in _functions(flow_template):
        variables = function["Environment"]["Variables"]
        assert variables["LEDGER_BACKEND"] == "dynamo"
        assert ("GUARDRAIL_ID" in variables) == (function["Handler"].split(".")[-1] in agent_steps)


def test_the_ask_machine_arn_is_an_output(flow_template):
    assert "AskStateMachineArn" in flow_template.find_outputs("*")
```

- [ ] **Step 2: Run them and watch them fail**
```bash
uv run --locked pytest tests/infra/stacks/test_agent_host.py tests/infra/stacks/test_flow_stack.py --no-cov 2>&1 | grep -E "^E |error|passed|failed" | head -4
```
Expected: `E   ImportError: cannot import name 'agent_host_from_context' from 'infra.stacks.flow_stack' (...)`, `E   ImportError: cannot import name 'AGENT_HOST_CONTEXT_KEY' from 'infra.stacks.flow_stack' (...)` and `2 errors`.

- [ ] **Step 3: Implement.**
In `infra/bundling.py`, replace exactly:
```python
API_BUNDLE = BundleSpec(
```
with:
```python
AGENT_SHIM_BUNDLE = BundleSpec("agent-shim", (), root_files=("infra/functions/agent_shim.py",))  # brings its boto3
API_BUNDLE = BundleSpec(
```

In `infra/stacks/flow_stack.py`, replace exactly:
```python
from infra.bundling import CORE_CODE, BundleSpec, bundle_code
```
with:
```python
from infra.bundling import AGENT_SHIM_BUNDLE, CORE_CODE, BundleSpec, bundle_code
```

In `infra/stacks/flow_stack.py`, replace exactly:
```python
from infra.stacks.data_stack import DataStack
```
with:
```python
from infra.stacks.agent_stack import AgentStack
from infra.stacks.data_stack import DataStack
```

In `infra/stacks/flow_stack.py`, replace exactly:
```python
REAL_PUBLISH_MODULE = "flow.publish"
```
with:
```python
AGENT_HOST_CONTEXT_KEY = "agent_host"          # -c agent_host=lambda: the fallback, agents run inside the step Lambdas
AGENT_HOST_AGENTCORE = "agentcore"
AGENT_HOST_LAMBDA = "lambda"
AGENT_HOSTS = (AGENT_HOST_AGENTCORE, AGENT_HOST_LAMBDA)
AGENT_SHIM_HANDLER = "agent_shim.handler"
REAL_PUBLISH_MODULE = "flow.publish"
```

In `infra/stacks/flow_stack.py`, replace exactly:
```python
def _construct_name(
```
with:
```python
def agent_host_from_context(context_value: object) -> str:
    """AgentCore unless told otherwise; a typo fails the synth instead of picking a host."""
    agent_host = AGENT_HOST_AGENTCORE if context_value is None else str(context_value)
    if agent_host not in AGENT_HOSTS:
        raise ValueError(f"agent_host must be one of {AGENT_HOSTS}, not {agent_host!r}")
    return agent_host


def _construct_name(
```

In `infra/stacks/flow_stack.py`, replace exactly:
```python
                 guardrail: GuardrailStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
```
with:
```python
                 guardrail: GuardrailStack, agent: AgentStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.agent_host = agent_host_from_context(self.node.try_get_context(AGENT_HOST_CONTEXT_KEY))
        self.agent_runtime_arn = agent.runtime.agent_runtime_arn
```

In `infra/stacks/flow_stack.py`, replace exactly:
```python
        for step in ASK_STEPS:
            is_real = step.name in STEPS_WITH_REAL_HANDLERS
```
with:
```python
        for step in ASK_STEPS:
            if step.runs_agents and self.agent_host == AGENT_HOST_AGENTCORE:
                continue   # the runtime runs it, through the shim below
            is_real = step.name in STEPS_WITH_REAL_HANDLERS
```

In `infra/stacks/flow_stack.py`, replace exactly:
```python
        self.ask_log_group = logs.LogGroup(self, "AskSpineLogs",
```
with:
```python
        if self.agent_host == AGENT_HOST_AGENTCORE:
            self.agent_shim = PortalFunction(
                self, "AgentShimFunction", handler=AGENT_SHIM_HANDLER, code=bundle_code(self, AGENT_SHIM_BUNDLE),
                environment={}, statements=[agent.invoke_statement()], timeout=AGENT_STEP_TIMEOUT)
        self.ask_log_group = logs.LogGroup(self, "AskSpineLogs",
```

In `infra/stacks/flow_stack.py`, replace exactly:
```python
        """A state that runs one step in its own Lambda; Step Functions passes the step's JSON input."""
        return tasks.LambdaInvoke(
            self, state_name,
            lambda_function=self.step_functions[step_name].function,
            payload=stepfunctions.TaskInput.from_object(payload),
```
with:
```python
        """A state that runs one step: its own Lambda, or the shim wrapping the same input for the runtime."""
        if step_name in self.step_functions:
            target, task_payload = self.step_functions[step_name].function, payload
        else:
            target = self.agent_shim.function
            task_payload = {"runtime_arn": self.agent_runtime_arn, "step": step_name, "input": payload}
        return tasks.LambdaInvoke(
            self, state_name,
            lambda_function=target,
            payload=stepfunctions.TaskInput.from_object(task_payload),
```

  In `infra/app.py`, pass the agent stack to the flow: `flow = FlowStack(app, "FlowStack", data=data, ledger=ledger, guardrail=guardrail, agent=agent, **stack_options("FlowStack"))` (wrap under 120 characters).

- [ ] **Step 4: Run them, full suite, synth both hosts, commit**
```bash
uv run --locked pytest tests/infra/stacks/test_agent_host.py tests/infra/stacks/test_flow_stack.py --no-cov 2>&1 | tail -1
```
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/bundling.py infra/stacks/flow_stack.py infra/app.py tests/infra/stacks/test_flow_stack.py tests/infra/stacks/test_agent_host.py
git commit -m "infra: agent steps run on AgentCore through the shim; -c agent_host=lambda is the fallback"
```
```bash
cd infra && env -u AWS_PROFILE -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q 2>&1 | grep -E "Successfully|rror"; cd ..
grep -o '"Handler": "[a-z_.]*"' infra/cdk.out/FlowStack.template.json | sort | uniq -c
cd infra && env -u AWS_PROFILE AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q -c agent_host=lambda 2>&1 | grep -E "Successfully|rror"; cd ..
grep -o '"Handler": "[a-z_.]*"' infra/cdk.out/FlowStack.template.json | sort | uniq -c
```
Expected: `12 passed`; S + 7 passed [284], `TOTAL ... 96%`; the default synth lists `agent_shim.handler` and the four ledger steps plus the two publish functions, no `run_orchestrator`/`judge_claim`/`write_answer`; the `lambda` synth lists all seven ask steps and no shim. (Dry-run note: `api/`, `auth/` and `flow/` didn't exist when this plan was written, so its synth was dry-run with empty stand-in packages; on `develop` they are the real ones.)

**Task done when:** the full suite is at S + 7; the two synths differ exactly as above.

### Task 3: Same question, both hosts (verify in AWS; ask Yaw first)

**Files:** none in `infra/`; one line in `HANDOFF.md` (ask Abdul, who edits it, or add it with his OK).

- [ ] **Step 1: AgentCore (default)**
```bash
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
cd infra && npx cdk deploy AgentStack FlowStack --require-approval never 2>&1 | grep "✅"; cd ..
read -rs ID_TOKEN; curl -s -X POST -H "Authorization: Bearer $ID_TOKEN" -H "Content-Type: application/json" -d '{"entity_id": "E4", "question": "What is blocking cutover for E4?"}' "$API_URL/ask" > /tmp/ask-agentcore.json; unset ID_TOKEN
python3 -c "import json; answer = json.load(open('/tmp/ask-agentcore.json'))['answer']; print(sorted({(citation['artefact'], citation['row_id']) for bullet in answer['bullets'] for citation in bullet['citations']}))"
```
Expected (verify in AWS): both stacks `✅`; a sorted list of citations including `('defect_log', 'DEF-0412')`.

- [ ] **Step 2: The Lambda fallback, then back**
```bash
cd infra && npx cdk deploy FlowStack -c agent_host=lambda --require-approval never 2>&1 | grep "✅"; cd ..
# repeat Step 1's curl into /tmp/ask-lambda.json and the same python line
cd infra && npx cdk deploy FlowStack --require-approval never 2>&1 | grep "✅"; cd ..
```
Expected (verify in AWS): the same citation list as Step 1. Write both lists into the ledger. If they differ, stop and tell Patrick (an agent difference, not infra).

- [ ] **Step 3: Record the host** in `HANDOFF.md` (with Abdul's OK): "Agents run on AgentCore Runtime (`demo_erp_portal_agents`); fallback: `cd infra && npx cdk deploy FlowStack -c agent_host=lambda` runs the same steps inside Lambdas."

**Task done when:** both citation lists are in the ledger and equal; the `HANDOFF.md` line exists (or Abdul has it).

### Task 4: Review, then PR (after Yaw's and Patrick's OK)
- [ ] **Step 1:** Work through the Review Focus; write each result in the ledger.
- [ ] **Step 2:** `git diff origin/develop --stat` touches only `infra/`, `tests/infra/` (and the `HANDOFF.md` line if Abdul agreed).
- [ ] **Step 3:** Push `feature/infra-agent-shim`; PR to `develop` titled "Agent shim: the ask spine runs agents on AgentCore, Lambda fallback behind a switch". Body: the switch, the shim payload, the both-hosts comparison, the rulings. No attribution lines.
- [ ] **Step 4:** Tell Patrick and Michael (M5: the fallback command); update [[Build order]].

**Task done when:** the PR is open to `develop` with green Jenkins; [[Build order]] shows Y3b `in review (PR #nn)`.

## Done means
- [ ] `uv run --locked pytest` → S + 7 passed, `TOTAL` ≥ 96%. *Verify:* run it.
- [ ] Default synth: `FlowStack.template.json` has `agent_shim.handler` and none of the three agent-step handlers; `-c agent_host=lambda`: all seven step handlers and no shim. *Verify:* Task 2 Step 4's `grep | uniq -c`.
- [ ] Deployed: the E4 question's citations are the same through AgentCore and through the Lambda fallback. *Verify in AWS:* the two ledger lists.
- [ ] `HANDOFF.md` states the host and the one-line fallback. *Verify:* `grep -n agent_host HANDOFF.md`.
- [ ] The PR is open (or merged) to `develop`; [[Build order]] row Y3b updated. *Verify:* the PR page.

## Never
- Give the shim Bedrock model rights, or any action beyond `InvokeAgentRuntime` on this runtime.
- Put anything but `{run_id, claim, scope}` in the critic's input on either path.
- Swallow a runtime error in the shim (the state must fail).
- Commit `agent_host` into `cdk.json`; run `cdk deploy` before Yaw's OK; push to `develop` or `main`; add attribution lines.

Related: [[Build order]], [[Yaw - DevOps]], [[Workstreams]]
