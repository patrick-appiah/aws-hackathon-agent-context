---
tags: [build, plan, area/devops]
id: Y3a
owner: Yaw
spec: "[[Y3a - AgentCore runtime - spec]]"
status: ready
updated: 2026-10-14
---
# Y3a: AgentStack, the AgentCore Runtime (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it. Deploying and pushing are outward-facing: ask Yaw (and Patrick for the PR) first.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Y3a - AgentCore runtime - spec]]: **the authority.**
3. [[Workstreams]] (`06 Workstreams/`): the architecture with owners, the code already built, the contracts and the rules (§7).
4. [[Yaw - DevOps]]: the owner's brief; and [[Michael - DevOps]] (the other half of DevOps).
5. [[Build order]]: what this item depends on and unblocks.
6. [[M2 - App, DataStack and LedgerStack - spec]]: the CDK app, `build_stacks`, the prefix, the test fixtures and the patterns every DevOps item follows.
7. [[Y2a - Express ask spine - spec]] §3, [[Y1 - ApiStack - spec]], [[M4b - Observability - spec]].

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Yaw (owner). Never invent a name, a shape or a rule.

**Goal:** the agent steps can run on AgentCore Runtime from a Docker-free code zip, with the same JSON in and out as the Lambdas.

**Architecture:** new `infra/agent_runtime/server.py` *(new)* and `infra/stacks/agent_stack.py` *(new)*; `infra/bundling.py` *(new)* gains `AGENT_RUNTIME_BUNDLE`; `build_stacks` builds `AgentStack` before `FlowStack`.

**Tech stack:** Python 3.11 standard library (`http.server`), `aws-cdk-lib` 2.273+ (`aws_bedrockagentcore.Runtime`, `AgentRuntimeArtifact`, `AgentCoreRuntime`), CDK CLI 2.1144.0, pytest, uv.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. **Branch:** `feature/infra-agentcore` from an up-to-date `develop`, **after Y2a and H2 are merged** (the runtime bundle needs `flow/`).
- **Start state:** `uv run --locked pytest` → all passed, `TOTAL` 96%; write the count as **S** (dry-run: C1 + M2 + stand-ins for M3a/M3b + Y1 + Y2a + Y2b, S = 265; Y2b isn't required, the n is the same without it). Every count is **S + n** [dry-run].
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
1. **The zip runs on ARM64:** the deployed runtime reaches `READY`, and `/ping` answers (the `invoke-agent-runtime` call in Task 3 works). An x86 wheel in the bundle shows up as an `ImportError` in the runtime's logs.
2. **Prompts are in the zip:** `unzip -l infra/cdk.out/asset.*.zip` for the runtime asset (or `ls infra/cdk.out/bundles/agent-runtime/agents/prompts/`) lists `prompts.lock`.
3. **`server.py` refuses everything but the three agent steps** (a `retry_decision` request returns 400; the retry must stay in Step Functions).
4. **The runtime role is no broader than the agent-step Lambdas':** compare the two policies in the synthesized templates (CDK's own additions on the runtime role: logs on `/aws/bedrock-agentcore/runtimes/*`, X-Ray, `cloudwatch:PutMetricData` with the `bedrock-agentcore` namespace condition, the workload-identity token actions, and read on the CDK asset bucket; Y4 lists them).
5. **A second copy gets its own runtime:** `npx cdk synth -c prefix=demo2` shows `demo2_erp_portal_agents`.

---

### Task 1: The AgentCore entry point (`infra/agent_runtime/server.py`)

**Files:**
- Create: `infra/agent_runtime/server.py`, `tests/infra/agent_runtime/test_server.py` *(new)*

**Produces:** `handle_invocation(body: bytes, load_steps=...) -> tuple[int, dict]`, `AgentRequestHandler`, `AGENT_STEPS`, `HEALTHY`, `LISTEN_ADDRESS`. **Consumes:** `flow.steps` at run time only (imported lazily). **Consumed by:** Task 2 (the bundle's root file), Y3b's shim (the payload).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync --locked && (cd infra && npm ci)
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/infra-agentcore
```
Expected: S passed (dry-run 265), `TOTAL ... 96%`.

- [ ] **Step 2: Write the failing test.**
Create `tests/infra/agent_runtime/test_server.py`:
```python
"""The AgentCore entry point (infra/agent_runtime/server.py): runs only the three agent steps, refuses the rest,
and answers /ping, over real HTTP on a free local port."""
import json
import threading
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from types import SimpleNamespace

import pytest

from infra.agent_runtime.server import HEALTHY, AgentRequestHandler, handle_invocation

LOCALHOST_ANY_PORT = ("127.0.0.1", 0)


def _fake_steps():
    return SimpleNamespace(judge_claim=lambda step_input, context: {"claim_id": step_input["claim"]["claim_id"],
                                                                     "passed": False},
                           run_orchestrator=lambda step_input, context: 1 / 0)


def test_a_known_step_runs_with_its_input_and_returns_its_output():
    body = json.dumps({"step": "judge_claim", "input": {"claim": {"claim_id": "claim-1"}}}).encode()
    assert handle_invocation(body, load_steps=_fake_steps) == (HTTPStatus.OK, {"claim_id": "claim-1",
                                                                              "passed": False})


@pytest.mark.parametrize("body", [b"not json", b"{}", b'{"step": "retry_decision", "input": {}}',
                                  b'{"step": "judge_claim", "input": "text"}'])
def test_anything_else_is_refused(body):
    status, reply = handle_invocation(body, load_steps=_fake_steps)
    assert status == HTTPStatus.BAD_REQUEST and reply["error"] == "invalid_input"


def test_a_failing_step_is_a_500_without_the_message():
    body = json.dumps({"step": "run_orchestrator", "input": {}}).encode()
    assert handle_invocation(body, load_steps=_fake_steps) == (HTTPStatus.INTERNAL_SERVER_ERROR,
                                                               {"error": "step_failed",
                                                                "detail": "ZeroDivisionError"})


def test_ping_over_http_reports_healthy():
    server = ThreadingHTTPServer(LOCALHOST_ANY_PORT, AgentRequestHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        address = f"http://127.0.0.1:{server.server_address[1]}"
        with urllib.request.urlopen(f"{address}/ping") as response:  # nosec B310: a local test server
            assert json.loads(response.read()) == HEALTHY
        with pytest.raises(urllib.error.HTTPError) as refused:
            urllib.request.urlopen(urllib.request.Request(f"{address}/invocations", data=b"{}"))  # nosec B310
        assert refused.value.code == HTTPStatus.BAD_REQUEST
    finally:
        server.shutdown()
```

- [ ] **Step 3: Run it and watch it fail**
```bash
uv run --locked pytest tests/infra/agent_runtime/test_server.py --no-cov 2>&1 | grep -E "^E |error|passed|failed" | head -4
```
Expected: `E   ModuleNotFoundError: No module named 'infra.agent_runtime'` and `1 error`.

- [ ] **Step 4: Implement.**
Create `infra/agent_runtime/server.py`:
```python
"""The AgentCore Runtime entry point (Y3a): the HTTP contract AgentCore expects, on port 8080, with no extra
dependency. POST /invocations runs one agent step of flow/steps.py; GET /ping reports health.

Payload: {"step": "run_orchestrator" | "judge_claim" | "write_answer", "input": <that step's input JSON>}.
The step's own output JSON is returned unchanged, so the state machine sees the same shape as the Lambda path.
"""
import importlib
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LISTEN_ADDRESS = ("0.0.0.0", 8080)   # nosec B104: AgentCore requires 0.0.0.0:8080 inside its microVM
INVOCATIONS_PATH = "/invocations"
PING_PATH = "/ping"
HEALTHY = {"status": "Healthy"}
STEPS_MODULE = "flow.steps"
AGENT_STEPS = frozenset({"run_orchestrator", "judge_claim", "write_answer"})
JSON_CONTENT_TYPE = "application/json"


def handle_invocation(body: bytes, load_steps=lambda: importlib.import_module(STEPS_MODULE)) -> tuple[int, dict]:
    """Run one agent step. Anything but a known step with a JSON object input is refused, never guessed."""
    try:
        request = json.loads(body)
        step_name, step_input = request["step"], request["input"]
    except (ValueError, KeyError, TypeError):
        return HTTPStatus.BAD_REQUEST, {"error": "invalid_input", "detail": "expected {step, input}"}
    if step_name not in AGENT_STEPS or not isinstance(step_input, dict):
        return HTTPStatus.BAD_REQUEST, {"error": "invalid_input", "detail": f"unknown step {step_name!r}"}
    try:
        return HTTPStatus.OK, getattr(load_steps(), step_name)(step_input, None)
    except Exception as error:  # the state machine fails the run; the detail stays in the runtime's logs
        return HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "step_failed", "detail": type(error).__name__}


class AgentRequestHandler(BaseHTTPRequestHandler):
    def _reply(self, status: int, body: dict) -> None:
        encoded = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", JSON_CONTENT_TYPE)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        self._reply(HTTPStatus.OK if self.path == PING_PATH else HTTPStatus.NOT_FOUND, HEALTHY)

    def do_POST(self) -> None:
        if self.path != INVOCATIONS_PATH:
            self._reply(HTTPStatus.NOT_FOUND, {"error": "not_found", "detail": self.path})
            return
        length = int(self.headers.get("Content-Length", 0))
        self._reply(*handle_invocation(self.rfile.read(length)))


if __name__ == "__main__":
    ThreadingHTTPServer(LISTEN_ADDRESS, AgentRequestHandler).serve_forever()
```

- [ ] **Step 5: Run it, full suite, commit**
```bash
uv run --locked pytest tests/infra/agent_runtime/test_server.py --no-cov 2>&1 | tail -1
```
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/agent_runtime/server.py tests/infra/agent_runtime/test_server.py
git commit -m "infra: AgentCore entry point that runs only the three agent steps, standard library only"
```
Expected: `7 passed`; S + 7 passed [272].

**Task done when:** `tests/infra/agent_runtime/test_server.py` → 7 passed (including the real-HTTP `/ping`); the full suite is at S + 7.

### Task 2: `AgentStack` with the runtime from an ARM64 code zip

**Files:**
- Modify: `infra/bundling.py`, `infra/app.py` *(new)*
- Create: `infra/stacks/agent_stack.py`, `tests/infra/stacks/test_agent_stack.py` *(new)*

**Produces:** `AGENT_RUNTIME_PYTHON_PLATFORM`, `AGENT_RUNTIME_BUNDLE` (in `infra.bundling`); `AgentStack(scope, construct_id, *, prefix, data, ledger, guardrail, **kwargs)` with `.runtime`, `.invoke_statement()`; `runtime_name(prefix)`, `RUNTIME_ENTRYPOINT`; output `AgentRuntimeArn`; `PortalStacks.agent`. **Consumes:** `bundle_path` (Y1), `model_invoke_statement` (Y2a), M2's and M3a's statements. **Consumed by:** Y3b.

- [ ] **Step 1: Write the failing tests.**
Create `tests/infra/stacks/test_agent_stack.py`:
```python
"""AgentStack: an AgentCore Runtime from a code zip (ARM64 Python 3.11, no Docker), named per copy, whose role
gets the same data, ledger, model and Guardrail access as the agent-step Lambdas and nothing broader."""
import json

import pytest
from aws_cdk.assertions import Match, Template

from infra.bundling import AGENT_RUNTIME_BUNDLE
from infra.stacks.agent_stack import runtime_name


@pytest.fixture(scope="module")
def agent_template(portal_stacks) -> Template:
    return Template.from_stack(portal_stacks.agent)


def test_the_runtime_runs_the_server_from_a_python_code_zip(agent_template):
    agent_template.has_resource_properties("AWS::BedrockAgentCore::Runtime", {
        "AgentRuntimeName": "test_erp_portal_agents",
        "AgentRuntimeArtifact": {"CodeConfiguration": {"EntryPoint": ["server.py"], "Runtime": "PYTHON_3_11",
                                                       "Code": Match.any_value()}},
        "EnvironmentVariables": {"LEDGER_BACKEND": "dynamo", "ARTEFACT_BACKEND": "csv",
                                 "LEDGER_TABLE": Match.any_value(), "REJECTED_TABLE": Match.any_value(),
                                 "ARTEFACTS_URI": Match.any_value(), "GUARDRAIL_ID": Match.any_value(),
                                 "GUARDRAIL_VERSION": Match.any_value()},
    })


def test_the_bundle_is_built_for_arm64_with_the_server_at_its_root():
    assert AGENT_RUNTIME_BUNDLE.python_platform == "aarch64-manylinux2014"
    assert AGENT_RUNTIME_BUNDLE.root_files == ("infra/agent_runtime/server.py",)
    assert "flow" in AGENT_RUNTIME_BUNDLE.code_paths


def test_the_role_can_use_the_ledger_the_models_the_guardrail_and_artefacts(agent_template):
    (policy,) = agent_template.find_resources("AWS::IAM::Policy").values()
    document = json.dumps(policy["Properties"]["PolicyDocument"])
    for action in ("dynamodb:Query", "bedrock:InvokeModel", "bedrock:ApplyGuardrail", "s3:GetObject"):
        assert action in document
    assert "s3:PutObject" not in document and "dynamodb:Scan" not in document


def test_runtime_names_are_valid_and_unique_per_copy():
    assert runtime_name("demo-2") == "demo_2_erp_portal_agents"


def test_the_runtime_arn_is_an_output(agent_template):
    assert "AgentRuntimeArn" in agent_template.find_outputs("*")
```

- [ ] **Step 2: Run them and watch them fail**
```bash
uv run --locked pytest tests/infra/stacks/test_agent_stack.py --no-cov 2>&1 | grep -E "^E |error|passed|failed" | head -4
```
Expected: `E   ImportError: cannot import name 'AGENT_RUNTIME_BUNDLE' from 'infra.bundling' (...)` and `1 error`.

- [ ] **Step 3: Implement.**
In `infra/bundling.py`, replace exactly:
```python
LAMBDA_PYTHON_PLATFORM = "x86_64-manylinux2014"     # Lambda x86_64 on Amazon Linux 2
```
with:
```python
LAMBDA_PYTHON_PLATFORM = "x86_64-manylinux2014"     # Lambda x86_64 on Amazon Linux 2
AGENT_RUNTIME_PYTHON_PLATFORM = "aarch64-manylinux2014"   # AgentCore Runtime runs ARM64
```

In `infra/bundling.py`, replace exactly:
```python
API_BUNDLE = BundleSpec(
```
with:
```python
AGENT_RUNTIME_BUNDLE = BundleSpec("agent-runtime", (*CORE_CODE, "flow"), python_platform=AGENT_RUNTIME_PYTHON_PLATFORM,
                                  root_files=("infra/agent_runtime/server.py",))
API_BUNDLE = BundleSpec(
```

Create `infra/stacks/agent_stack.py`:
```python
"""AgentStack: the AgentCore Runtime that hosts the Strands agents (Y3a). It runs the agent steps of flow/steps.py
behind infra/agent_runtime/server.py, from a code zip (no container image, no Docker), on ARM64 Python 3.11.

Its role gets exactly what the agent steps' Lambdas get (FlowStack): the ledger, the two eu.* models, the Guardrail
and artefacts/ read. The shim Lambda that Step Functions calls is Y3b.
"""
from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_bedrockagentcore as agentcore
from aws_cdk import aws_iam as iam
from constructs import Construct

from config import DEFAULT_ARTEFACT_BACKEND
from infra.bedrock_access import model_invoke_statement
from infra.bundling import AGENT_RUNTIME_BUNDLE, bundle_path
from infra.constants import NAME_SEPARATOR
from infra.stacks.data_stack import DataStack
from infra.stacks.guardrail_stack import GuardrailStack
from infra.stacks.ledger_stack import LedgerStack

RUNTIME_BASE_NAME = "erp_portal_agents"
RUNTIME_NAME_SEPARATOR = "_"                    # runtime names allow letters, digits and underscores only
RUNTIME_ENTRYPOINT = ["server.py"]              # AGENT_RUNTIME_BUNDLE copies it to the bundle root
DYNAMO_LEDGER_BACKEND = "dynamo"


def runtime_name(prefix: str) -> str:
    """`demo-2` -> `demo_2_erp_portal_agents`: unique per copy, and valid for AgentCore."""
    return f"{prefix.replace(NAME_SEPARATOR, RUNTIME_NAME_SEPARATOR)}{RUNTIME_NAME_SEPARATOR}{RUNTIME_BASE_NAME}"


class AgentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, prefix: str, data: DataStack, ledger: LedgerStack,
                 guardrail: GuardrailStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.runtime = agentcore.Runtime(
            self, "AgentRuntime",
            runtime_name=runtime_name(prefix),
            agent_runtime_artifact=agentcore.AgentRuntimeArtifact.from_code_asset(
                path=bundle_path(self, AGENT_RUNTIME_BUNDLE),
                runtime=agentcore.AgentCoreRuntime.PYTHON_3_11,
                entrypoint=RUNTIME_ENTRYPOINT,
            ),
            environment_variables={
                "LEDGER_BACKEND": DYNAMO_LEDGER_BACKEND,
                "LEDGER_TABLE": ledger.ledger_table.table_name,
                "REJECTED_TABLE": ledger.rejected_table.table_name,
                "ARTEFACT_BACKEND": DEFAULT_ARTEFACT_BACKEND,
                "ARTEFACTS_URI": data.artefacts_uri,
                "GUARDRAIL_ID": guardrail.guardrail_id,
                "GUARDRAIL_VERSION": guardrail.guardrail_version,
            },
            tracing_enabled=True,
        )
        for statement in (ledger.ledger_statement(), model_invoke_statement(self),
                          guardrail.apply_guardrail_statement(), data.artefacts_read_statement()):
            self.runtime.add_to_role_policy(statement)
        CfnOutput(self, "AgentRuntimeArn", value=self.runtime.agent_runtime_arn)

    def invoke_statement(self) -> iam.PolicyStatement:
        """For the shim Lambda only (Y3b): invoke this runtime and nothing else."""
        return iam.PolicyStatement(actions=["bedrock-agentcore:InvokeAgentRuntime"],
                                   resources=[self.runtime.agent_runtime_arn,
                                              f"{self.runtime.agent_runtime_arn}/runtime-endpoint/DEFAULT"])
```

- [ ] **Step 4: Build it in the app.** In `infra/app.py`:
  - add `from infra.stacks.agent_stack import AgentStack` as the first `infra.stacks` import (alphabetical);
  - add the field `agent: AgentStack` after `auth: AuthStack` (before `flow: FlowStack`) in `PortalStacks`;
  - directly before the `flow = FlowStack(...)` statement, add:
```python
    agent = AgentStack(app, "AgentStack", prefix=prefix, data=data, ledger=ledger, guardrail=guardrail,
                       **stack_options("AgentStack"))
```
  - add `agent=agent` to the `PortalStacks(...)` call (after `auth=auth`).

- [ ] **Step 5: Run them, full suite, synth (bundles ARM64), commit**
```bash
uv run --locked pytest tests/infra/stacks/test_agent_stack.py --no-cov 2>&1 | tail -1
```
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/bundling.py infra/stacks/agent_stack.py infra/app.py tests/infra/stacks/test_agent_stack.py
git commit -m "infra: AgentStack, AgentCore Runtime from an ARM64 code zip with the agent steps' least-privilege role"
```
```bash
cd infra && env -u AWS_PROFILE -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q 2>&1 | grep -E "Successfully|rror"; cd ..
ls infra/cdk.out/bundles/agent-runtime/ | grep -E '^server.py$|aarch64'; ls infra/cdk.out/bundles/agent-runtime/agents/prompts/prompts.lock
```
Expected: `5 passed`; S + 12 passed [277], `TOTAL ... 96%`; `Successfully synthesized`; `_cffi_backend.cpython-311-aarch64-linux-gnu.so` and `server.py`; the lock file listed. (Dry-run note: `api/`, `auth/` and `flow/` didn't exist when this plan was written, so its synth was dry-run with empty stand-in packages; on `develop` they are the real ones.)

**Task done when:** the full suite is at S + 12; the synthesized runtime bundle holds `server.py`, ARM64 wheels and `prompts.lock`.

### Task 3: Deploy and invoke the runtime directly (verify in AWS; ask Yaw first)

**Files:** none.

- [ ] **Step 1: Deploy**
```bash
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
cd infra && npx cdk deploy AgentStack --require-approval never 2>&1 | grep -E "✅|AgentRuntimeArn"; cd ..
RUNTIME_ARN=$(aws cloudformation describe-stacks --stack-name demo-AgentStack --query "Stacks[0].Outputs[?OutputKey=='AgentRuntimeArn'].OutputValue" --output text)
```
Expected (verify in AWS): `✅  AgentStack (demo-AgentStack)` and `AgentRuntimeArn = arn:aws:bedrock-agentcore:eu-west-1:486128667962:runtime/demo_erp_portal_agents-...`.

- [ ] **Step 2: Refused step, then a real one**
```bash
aws bedrock-agentcore invoke-agent-runtime --agent-runtime-arn "$RUNTIME_ARN" --runtime-session-id "$(printf 'check%.0s' {1..8})" --cli-binary-format raw-in-base64-out --payload '{"step": "retry_decision", "input": {}}' --content-type application/json --accept application/json /dev/stdout; echo
aws bedrock-agentcore invoke-agent-runtime --agent-runtime-arn "$RUNTIME_ARN" --runtime-session-id "$(printf 'check%.0s' {1..8})" --cli-binary-format raw-in-base64-out --payload '{"step": "judge_claim", "input": {"run_id": "run-agentcore-1", "claim": {"claim_id": "claim-1", "statement": "E4 is blocked by DEF-0412", "chain": [{"artefact": "defect_log", "row_id": "DEF-0412", "role_in_chain": "cause"}]}, "scope": {"user_id": "user-cfo", "role": "cfo", "tenant_id": "t-01", "entity_ids": ["*"]}}}' --content-type application/json --accept application/json /dev/stdout; echo
```
Expected (verify in AWS): the first prints `{"error": "invalid_input", "detail": "unknown step 'retry_decision'"}`; the second prints `judge_claim`'s JSON (`{"claim_id": "claim-1", "passed": ..., "verdict": {...}}`; the run must exist in the ledger for H2's step, so use a `run_id` from an `/ask` run if it refuses an unknown run). Runtime logs: `/aws/bedrock-agentcore/runtimes/demo_erp_portal_agents-*`.

**Task done when:** both invocations answer as above (ledger lines), and the runtime shows `READY` (`aws bedrock-agentcore-control get-agent-runtime --agent-runtime-id <id> --query status`).

### Task 4: Review, then PR (after Yaw's and Patrick's OK)
- [ ] **Step 1:** Work through the Review Focus; write each result in the ledger.
- [ ] **Step 2:** `git diff origin/develop --stat` touches only `infra/` and `tests/infra/`.
- [ ] **Step 3:** Push `feature/infra-agentcore`; PR to `develop` titled "AgentStack: AgentCore Runtime from a code zip, no Docker". Body: the runtime contract (spec §1), the role, the AWS checks, the rulings. No attribution lines.
- [ ] **Step 4:** Tell Patrick and Huvison; update [[Build order]]. Y3b wires it into the ask spine.

**Task done when:** the PR is open to `develop` with green Jenkins; [[Build order]] shows Y3a `in review (PR #nn)`.

## Done means
- [ ] `uv run --locked pytest` → S + 12 passed, `TOTAL` ≥ 96%. *Verify:* run it.
- [ ] `infra/cdk.out/AgentStack.template.json` *(new)* has one `AWS::BedrockAgentCore::Runtime` with `"Runtime": "PYTHON_3_11"` and `"EntryPoint": ["server.py"]`, and `infra/cdk.out/bundles/agent-runtime/agents/prompts/prompts.lock` *(new)* exists. *Verify:* `grep -c PYTHON_3_11 infra/cdk.out/AgentStack.template.json` → `1`; `ls` the lock.
- [ ] Deployed: the runtime is `READY`; an unknown step returns `invalid_input`; `judge_claim` returns its JSON. *Verify in AWS:* Task 3's ledger lines.
- [ ] The PR is open (or merged) to `develop`; [[Build order]] row Y3a updated. *Verify:* the PR page.

## Never
- Let `server.py` run `retry_decision`, `store_claims` or any non-agent step, or accept a step name it doesn't know.
- Build the runtime from a container or with Docker; ship a bundle without `agents/prompts/prompts.lock`.
- Give the runtime role a write on S3 or a wildcard; widen the shim's `invoke_statement()` beyond this runtime.
- Run `cdk deploy` or `aws` commands before Yaw's OK; push to `develop` or `main`; add attribution lines.

Related: [[Build order]], [[Yaw - DevOps]], [[Workstreams]]
