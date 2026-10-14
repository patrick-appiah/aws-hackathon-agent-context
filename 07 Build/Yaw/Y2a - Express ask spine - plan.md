---
tags: [build, plan, area/devops]
id: Y2a
owner: Yaw
spec: "[[Y2a - Express ask spine - spec]]"
status: ready
updated: 2026-10-14
---
# Y2a: FlowStack, the Express ask spine (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it. Deploying and pushing are outward-facing: ask Yaw (and Patrick for the PR) first.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Y2a - Express ask spine - spec]]: **the authority**, especially §3 (the step contract). Where this plan and the spec disagree, the spec wins; record the conflict in the ledger.
3. [[Workstreams]] (`06 Workstreams/`): the architecture with owners, the code already built, the contracts and the rules (§7).
4. [[Yaw - DevOps]]: the owner's brief; and [[Michael - DevOps]] (the other half of DevOps).
5. [[Build order]]: what this item depends on and unblocks.
6. [[M2 - App, DataStack and LedgerStack - spec]]: the CDK app, `build_stacks`, the prefix, the test fixtures and the patterns every DevOps item follows.
7. [[Y1 - ApiStack - spec]], [[M3a - GuardrailStack - spec]], [[M4b - Observability - spec]]; [[Huvison - trust and flow]].

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Yaw (owner) or Huvison (step JSON). Never invent a name, a shape or a rule.

**Goal:** `POST /api/ask` runs the Express ask spine in AWS: stubs at D1 18:00 (the walking skeleton), Huvison's real steps after H2, with a ledger-driven retry and a blind critic.

**Architecture:** new `infra/bedrock_access.py` *(new)*, `infra/functions/stub_steps.py` *(new)*, `infra/stacks/flow_stack.py` *(new)*; `ApiStack` takes `flow`; `build_stacks` builds `FlowStack` after `AuthStack` and before `ApiStack`.

**Tech stack:** Python 3.11, `aws-cdk-lib` 2.273+ (`aws_stepfunctions`, `aws_stepfunctions_tasks`), CDK CLI 2.1144.0, pytest, uv.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. **Branch:** `feature/infra-ask-spine` from an up-to-date `develop`, **after Y1 and M3a are merged**. Task 6 additionally needs Huvison's H2 (and Linus's L3 for the `ask` route).
- **Start state:** `uv run --locked pytest` → all passed, `TOTAL` 96%; write the count into the ledger as **S**. Every count below is **S + n** with the dry-run value in brackets (dry-run: C1 + M2 + stand-ins for M3a/M3b + Y1, so S = 240).
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
1. **The JSONPath filter works in AWS:** in the first real execution, `WriteAnswer`'s input shows `passed_claims` with only the passed claims (Step Functions console, the state's input). If Step Functions rejects the filter, stop and tell Yaw: the fallback is to pass `$.judged` and let `write_answer` keep `passed == true` (a contract change with Huvison).
2. **The critic stays blind end to end:** in the execution history, `JudgeClaim`'s input has only `run_id`, `claim`, `scope`.
3. **The loop is bounded by the ledger:** with the real steps, a forced rejection shows `JudgeClaim` → `RetryDecision` (`retry`) → `ReplanClaim` → … → `RetryDecision` (`reject`) → `RecordRejection`, and never more `JudgeClaim`s than `max_claim_attempts` allows.
4. **Bedrock calls succeed from every EU region the profile routes to** (no `AccessDenied` in the agent steps' logs after ten runs). A new region in the profile's route means updating `MODEL_ROUTES`.
5. **Timing:** the D1 18:00 measurement (Huvison) and the decision on §6 of the spec are in the ledger and the PR.

---

### Task 1: Bedrock IAM on the exact EU models (`infra/bedrock_access.py`)

**Files:**
- Create: `infra/bedrock_access.py`, `tests/infra/test_bedrock_access.py` *(new)*

**Produces:** `EU_PROFILE_PREFIX`, `MODEL_INVOKE_ACTIONS`, `MODEL_ROUTES`, `model_resource_arns(stack)`, `model_invoke_statement(stack)`. **Consumes:** `config.DEFAULT_REASONING_MODEL`, `DEFAULT_RETRIEVAL_MODEL`, `DEFAULT_REGION`. **Consumed by:** Task 3, Y3a.

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync --locked && (cd infra && npm ci)
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/infra-ask-spine
```
Expected: S passed (dry-run 240), `TOTAL ... 96%`. Write S into the ledger.

- [ ] **Step 2: Write the failing test.**
Create `tests/infra/test_bedrock_access.py`:
```python
"""Bedrock IAM (infra/bedrock_access.py): the two eu.* profiles and their EU foundation models, never a wildcard."""
import aws_cdk as cdk

from infra.bedrock_access import MODEL_INVOKE_ACTIONS, model_invoke_statement

PARTITION = "aws"
EU_REGIONS = {"eu-north-1", "eu-west-1", "eu-west-3", "eu-south-1", "eu-south-2", "eu-central-1"}


def _rendered(resource) -> str:
    """An ARN as text, with CloudFormation's partition reference filled in."""
    if isinstance(resource, str):
        return resource
    return "".join(PARTITION if isinstance(part, dict) else part for part in resource["Fn::Join"][1])


def _statement() -> dict:
    stack = cdk.Stack(cdk.App(), "BedrockAccessTest", env=cdk.Environment(account="111111111111", region="eu-west-1"))
    statement = stack.resolve(model_invoke_statement(stack).to_statement_json())
    return {**statement, "Resource": [_rendered(resource) for resource in statement["Resource"]]}


def test_the_statement_names_both_actions_and_no_wildcard():
    statement = _statement()
    assert statement["Action"] == MODEL_INVOKE_ACTIONS
    assert "*" not in str(statement["Resource"])


def test_the_profiles_are_eu_profiles_in_eu_west_1():
    profile_arns = [arn for arn in _statement()["Resource"] if "inference-profile" in arn]
    assert sorted(profile_arns) == [
        "arn:aws:bedrock:eu-west-1:111111111111:inference-profile/eu.amazon.nova-lite-v1:0",
        "arn:aws:bedrock:eu-west-1:111111111111:inference-profile/eu.anthropic.claude-sonnet-4-6"]


def test_foundation_models_are_only_in_eu_regions():
    model_arns = [arn for arn in _statement()["Resource"] if "foundation-model" in arn]
    assert len(model_arns) == 10
    for arn in model_arns:
        assert arn.startswith(f"arn:{PARTITION}:bedrock:") and arn.split(":")[3] in EU_REGIONS
```

- [ ] **Step 3: Run it and watch it fail**
```bash
uv run --locked pytest tests/infra/test_bedrock_access.py --no-cov 2>&1 | grep -E "^E |error|passed|failed" | head -4
```
Expected: `E   ModuleNotFoundError: No module named 'infra.bedrock_access'` and `1 error`.

- [ ] **Step 4: Implement.**
Create `infra/bedrock_access.py`:
```python
"""Bedrock IAM on the exact EU inference profiles in config.py and the EU foundation models they route to (D-002).

The routes below are what `aws bedrock get-inference-profile` returned in eu-west-1 on 2026-10-14. If a profile
gains a region, the call fails with AccessDenied in that region: re-run the command and update the tuple.
"""
from aws_cdk import Aws, Stack
from aws_cdk import aws_iam as iam

from config import DEFAULT_REASONING_MODEL, DEFAULT_REGION, DEFAULT_RETRIEVAL_MODEL

EU_PROFILE_PREFIX = "eu."
INFERENCE_PROFILE_RESOURCE = "inference-profile"
# Strands' BedrockModel calls ConverseStream (streaming) by default, Converse otherwise.
MODEL_INVOKE_ACTIONS = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]

# inference profile -> (foundation model it routes to, regions it may route to)
MODEL_ROUTES: dict[str, tuple[str, tuple[str, ...]]] = {
    DEFAULT_REASONING_MODEL: ("anthropic.claude-sonnet-4-6",
                              ("eu-north-1", "eu-west-3", "eu-south-1", "eu-south-2", "eu-west-1", "eu-central-1")),
    DEFAULT_RETRIEVAL_MODEL: ("amazon.nova-lite-v1:0", ("eu-west-3", "eu-west-1", "eu-central-1", "eu-north-1")),
}


def _foundation_model_arn(region: str, model_id: str) -> str:
    return f"arn:{Aws.PARTITION}:bedrock:{region}::foundation-model/{model_id}"


def model_resource_arns(stack: Stack) -> list[str]:
    """The two profile ARNs in eu-west-1 plus every foundation-model ARN they route to. Never a wildcard."""
    profile_arns = [stack.format_arn(service="bedrock", region=DEFAULT_REGION, resource=INFERENCE_PROFILE_RESOURCE,
                                     resource_name=profile_id) for profile_id in MODEL_ROUTES]
    model_arns = [_foundation_model_arn(region, model_id)
                  for model_id, regions in MODEL_ROUTES.values() for region in regions]
    return [*profile_arns, *model_arns]


def model_invoke_statement(stack: Stack) -> iam.PolicyStatement:
    if not all(profile_id.startswith(EU_PROFILE_PREFIX) for profile_id in MODEL_ROUTES):
        raise ValueError("only eu.* inference profiles may be granted (D-002)")
    return iam.PolicyStatement(actions=MODEL_INVOKE_ACTIONS, resources=model_resource_arns(stack))
```

- [ ] **Step 5: Run it**
```bash
uv run --locked pytest tests/infra/test_bedrock_access.py --no-cov 2>&1 | tail -1
```
Expected: `3 passed`.

- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/bedrock_access.py tests/infra/test_bedrock_access.py
git commit -m "infra: Bedrock invoke rights on the two eu.* profiles and the EU models they route to"
```
Expected: S + 3 passed [243].

**Task done when:** `tests/infra/test_bedrock_access.py` → 3 passed; the full suite is at S + 3.

### Task 2: The stand-in steps (`infra/functions/stub_steps.py`)

**Files:**
- Create: `infra/functions/stub_steps.py`, `tests/infra/functions/test_stub_steps.py` *(new)*

**Produces:** `check_budget`, `run_orchestrator`, `store_claims`, `judge_claim`, `retry_decision`, `record_rejection`, `write_answer` (each `(event, context) -> dict`, spec §3), `STUB_CLAIM_ID`. **Consumes:** the C1 models (`Question`, `OrchestratorResult`, `BlockerClaim`, `AskResponse`) in the test only. **Consumed by:** Task 3.

- [ ] **Step 1: Write the failing test.**
Create `tests/infra/functions/test_stub_steps.py`:
```python
"""The stand-in steps speak the step contract: their JSON validates against the real step and API models."""
from config import DEFAULT_TENANT_ID
from infra.functions import stub_steps
from tools.api_schema import AskResponse
from tools.models import BlockerClaim, OrchestratorResult, Question

QUESTION = {"run_id": "run-0001", "entity_id": "E4", "question": "What is blocking cutover for E4?",
            "budget_usd": 0.5, "max_attempts": 2,
            "scope": {"user_id": "user-e4-lead", "role": "entity_lead", "tenant_id": DEFAULT_TENANT_ID,
                      "entity_ids": ["E4"]}}


def test_the_stub_orchestrator_returns_an_orchestrator_result_with_a_valid_claim():
    result = stub_steps.run_orchestrator({"question": QUESTION, "replan_claim_id": None}, None)
    OrchestratorResult.model_validate(result)
    assert BlockerClaim.model_validate(result["claims"][0]).claim_id == stub_steps.STUB_CLAIM_ID


def test_a_replan_keeps_the_claim_id():
    result = stub_steps.run_orchestrator({"question": QUESTION, "replan_claim_id": "claim-7"}, None)
    assert result["claims"][0]["claim_id"] == "claim-7"


def test_the_stub_spine_ends_in_a_valid_ask_response():
    Question.model_validate(stub_steps.check_budget(QUESTION, None)["question"])
    claims = stub_steps.run_orchestrator({"question": QUESTION, "replan_claim_id": None}, None)["claims"]
    stored = stub_steps.store_claims({"run_id": QUESTION["run_id"], "claims": claims}, None)["claims"]
    judgement = stub_steps.judge_claim({"run_id": QUESTION["run_id"], "claim": stored[0],
                                        "scope": QUESTION["scope"]}, None)
    assert judgement["passed"] is True
    answer = stub_steps.write_answer({"run_id": QUESTION["run_id"], "question": QUESTION, "passed_claims": stored,
                                      "partial": None}, None)
    assert AskResponse.model_validate(answer).answer.bullets[0].citations[0].row_id == "DEF-0412"


def test_the_stub_retry_decision_never_retries():
    assert stub_steps.retry_decision({"run_id": "run-0001", "claim_id": "claim-1"}, None) == {"decision": "reject"}


def test_a_partial_answer_is_reported_as_partial():
    answer = stub_steps.write_answer({"run_id": "run-0001", "question": QUESTION, "passed_claims": [],
                                      "partial": {"reason": "budget spent", "claims_so_far": []}}, None)
    assert AskResponse.model_validate(answer).partial_reason == "budget spent"
```

- [ ] **Step 2: Run it and watch it fail**
```bash
uv run --locked pytest tests/infra/functions/test_stub_steps.py --no-cov 2>&1 | grep -E "^E |error|passed|failed" | head -4
```
Expected: `E   ImportError: cannot import name 'stub_steps' from 'infra.functions' (unknown location)` and `1 error`.

- [ ] **Step 3: Implement.**
Create `infra/functions/stub_steps.py`:
```python
"""Stand-ins for Huvison's flow/steps.py until H2 is merged (Y2a): the ask spine runs end to end in AWS with canned
answers and a critic that always passes (the D1 18:00 walking skeleton). Same input and output JSON as the real
steps (the Y2a spec, "Step contract")."""
STUB_CLAIM_ID = "claim-1"
STUB_STATEMENT = "Stub: E4 cutover is blocked by DEF-0412 (the ask spine ran with stand-in steps)"
STUB_CITATION = {"artefact": "defect_log", "row_id": "DEF-0412"}
STUB_CHAIN_ROLE = "cause"
STUB_VERDICT_REASON = "stub critic: always passes"
STUB_HEADLINE = "Stub answer from the deployed ask spine"
STUB_STEP_NAME = "stub"


def check_budget(event, context):
    return {"question": event, "partial": None}


def run_orchestrator(event, context):
    claim = {"claim_id": event.get("replan_claim_id") or STUB_CLAIM_ID, "statement": STUB_STATEMENT,
             "chain": [{**STUB_CITATION, "role_in_chain": STUB_CHAIN_ROLE}]}
    return {"plan": {"run_id": event["question"]["run_id"], "steps": []}, "claims": [claim], "partial": None,
            "usage": []}


def store_claims(event, context):
    return {"claims": event["claims"]}


def judge_claim(event, context):
    claim_id = event["claim"]["claim_id"]
    return {"claim_id": claim_id, "passed": True,
            "verdict": {"claim_id": claim_id, "pass": True, "reason": STUB_VERDICT_REASON}}


def retry_decision(event, context):
    return {"decision": "reject"}


def record_rejection(event, context):
    return {"claim_id": event["claim_id"], "rejected": True}


def write_answer(event, context):
    bullets = [{"text": claim["statement"], "citations": [STUB_CITATION]} for claim in event["passed_claims"]]
    return {"run_id": event["run_id"], "answer": {"headline": STUB_HEADLINE, "bullets": bullets, "rejected_count": 0},
            "rejected": [], "cost_usd": 0.0, "partial": event.get("partial") is not None,
            "partial_reason": (event.get("partial") or {}).get("reason"),
            "trace": [{"step": STUB_STEP_NAME, "agent": None, "prompt": None}]}
```

- [ ] **Step 4: Run it**
```bash
uv run --locked pytest tests/infra/functions/test_stub_steps.py --no-cov 2>&1 | tail -1
```
Expected: `5 passed`.

- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/functions/stub_steps.py tests/infra/functions/test_stub_steps.py
git commit -m "infra: stand-in ask-spine steps that speak the C1 step contract"
```
Expected: S + 8 passed [248].

**Task done when:** the stubs' outputs validate against the C1 models (`tests/infra/functions/test_stub_steps.py` → 5 passed); the full suite is at S + 8.

### Task 3: `FlowStack` with the Express ask spine

**Files:**
- Create: `infra/stacks/flow_stack.py`, `tests/infra/stacks/test_flow_stack.py` *(new)*
- Modify: `infra/app.py` *(new)*

**Produces:** `FlowStack(scope, construct_id, *, data, ledger, guardrail, **kwargs)` with `.step_functions`, `.ask_log_group`, `.ask_state_machine`, `.ask_start_statement()`; output `AskStateMachineArn`; `ASK_STEPS`, `FlowStep`, `STEPS_WITH_REAL_HANDLERS`, `FLOW_BUNDLE`, `DYNAMO_LEDGER_BACKEND`, `PASSED_CLAIMS_FILTER`; `PortalStacks.flow`. **Consumes:** `DataStack` (`artefacts_uri`, `artefacts_read_statement()`), `LedgerStack` (`ledger_table`, `rejected_table`, `ledger_statement()`), `GuardrailStack` (`guardrail_id`, `guardrail_version`, `apply_guardrail_statement()`), `PortalFunction`, `bundle_code`, `CORE_CODE`, `BundleSpec` (Y1), `model_invoke_statement` (Task 1). **Consumed by:** Task 4, M4b (`ask_state_machine`, `ask_log_group`), Y2b, Y3b.

- [ ] **Step 1: Write the failing tests.**
Create `tests/infra/stacks/test_flow_stack.py`:
```python
"""FlowStack, the Express ask spine: the states and their order, the ledger-driven retry Choice, a blind critic,
and one least-privilege Lambda per step."""
import json

import pytest
from aws_cdk.assertions import Template

from infra.stacks.flow_stack import ASK_STEPS

TOKEN_PLACEHOLDER = "TOKEN"
CRITIC_INPUT_KEYS = {"run_id.$", "claim.$", "scope.$"}


@pytest.fixture(scope="module")
def flow_template(portal_stacks) -> Template:
    return Template.from_stack(portal_stacks.flow)


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
uv run --locked pytest tests/infra/stacks/test_flow_stack.py --no-cov 2>&1 | grep -E "^E |error|passed|failed" | head -4
```
Expected: `E   ModuleNotFoundError: No module named 'infra.stacks.flow_stack'` and `1 error`.

- [ ] **Step 3: Implement the stack.**
Create `infra/stacks/flow_stack.py`:
```python
"""FlowStack: the Express ask spine (D-007). Every state is one Lambda running one flow/steps.py function.

check_budget -> run_orchestrator -> store_claims -> per claim: judge_claim -> pass? keep it
                                                    : retry_decision (reads the ledger) -> retry: re-plan the claim
                                                                                       -> reject: record_rejection
             -> write_answer (passed claims only) -> AskResponse
The retry is a Choice on the value retry_decision returns, never a model output. The critic's Lambda gets the
run ID, the claim and the scope, never the question, the plan or the attempt count (D-007, D-012).
"""
from dataclasses import dataclass

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk import aws_stepfunctions_tasks as tasks
from constructs import Construct

from config import DEFAULT_ARTEFACT_BACKEND, REPO_ROOT
from infra.bedrock_access import model_invoke_statement
from infra.bundling import CORE_CODE, BundleSpec, bundle_code
from infra.constants import LOG_RETENTION
from infra.portal_function import DEFAULT_MEMORY_MEGABYTES, PortalFunction
from infra.stacks.data_stack import DataStack
from infra.stacks.guardrail_stack import GuardrailStack
from infra.stacks.ledger_stack import LedgerStack

FLOW_BUNDLE = BundleSpec("flow", (*CORE_CODE, "flow"))
REAL_STEP_MODULE = "flow.steps"
STUB_STEP_MODULE = "stub_steps"
STUB_CODE_DIRECTORY = REPO_ROOT / "infra" / "functions"
DYNAMO_LEDGER_BACKEND = "dynamo"
# Steps whose real function is merged (Huvison H2). The others run infra/functions/stub_steps.py.
STEPS_WITH_REAL_HANDLERS: frozenset[str] = frozenset()

LEDGER_STEP_TIMEOUT = Duration.seconds(10)
AGENT_STEP_TIMEOUT = Duration.seconds(60)
AGENT_STEP_MEMORY_MEGABYTES = 1024
ASK_SPINE_TIMEOUT = Duration.minutes(2)         # StartSyncExecution allows 5; API Gateway gives up at 29 s anyway
MAX_PARALLEL_JUDGEMENTS = 4                     # claims judged at once; keeps Bedrock under its request quota
RETRY = "retry"
PASSED_CLAIMS_FILTER = "$.judged[?(@.passed == true)].claim"


@dataclass(frozen=True)
class FlowStep:
    name: str                 # the function in flow/steps.py
    runs_agents: bool         # needs Bedrock, the Guardrail and the artefacts


ASK_STEPS = (
    FlowStep("check_budget", runs_agents=False),
    FlowStep("run_orchestrator", runs_agents=True),
    FlowStep("store_claims", runs_agents=False),
    FlowStep("judge_claim", runs_agents=True),
    FlowStep("retry_decision", runs_agents=False),
    FlowStep("record_rejection", runs_agents=False),
    FlowStep("write_answer", runs_agents=True),
)


def _construct_name(step_name: str) -> str:
    return "".join(word.capitalize() for word in step_name.split("_"))


class FlowStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, data: DataStack, ledger: LedgerStack,
                 guardrail: GuardrailStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        ledger_environment = {
            "LEDGER_BACKEND": DYNAMO_LEDGER_BACKEND,
            "LEDGER_TABLE": ledger.ledger_table.table_name,
            "REJECTED_TABLE": ledger.rejected_table.table_name,
        }
        agent_environment = {
            **ledger_environment,
            "ARTEFACT_BACKEND": DEFAULT_ARTEFACT_BACKEND,
            "ARTEFACTS_URI": data.artefacts_uri,
            "GUARDRAIL_ID": guardrail.guardrail_id,
            "GUARDRAIL_VERSION": guardrail.guardrail_version,
        }
        agent_statements = [model_invoke_statement(self), guardrail.apply_guardrail_statement(),
                            data.artefacts_read_statement()]
        stub_code = lambda_.Code.from_asset(str(STUB_CODE_DIRECTORY))
        flow_code = bundle_code(self, FLOW_BUNDLE) if STEPS_WITH_REAL_HANDLERS else stub_code
        self.step_functions: dict[str, PortalFunction] = {}
        for step in ASK_STEPS:
            is_real = step.name in STEPS_WITH_REAL_HANDLERS
            self.step_functions[step.name] = PortalFunction(
                self, f"{_construct_name(step.name)}Function",
                handler=f"{REAL_STEP_MODULE if is_real else STUB_STEP_MODULE}.{step.name}",
                code=flow_code if is_real else stub_code,
                environment=agent_environment if step.runs_agents else ledger_environment,
                statements=[ledger.ledger_statement(), *(agent_statements if step.runs_agents else [])],
                timeout=AGENT_STEP_TIMEOUT if step.runs_agents else LEDGER_STEP_TIMEOUT,
                memory_megabytes=AGENT_STEP_MEMORY_MEGABYTES if step.runs_agents else DEFAULT_MEMORY_MEGABYTES,
            )
        self.ask_log_group = logs.LogGroup(self, "AskSpineLogs", retention=LOG_RETENTION,
                                           removal_policy=RemovalPolicy.DESTROY)
        self.ask_state_machine = stepfunctions.StateMachine(
            self, "AskSpine",
            definition_body=stepfunctions.DefinitionBody.from_chainable(self._ask_definition()),
            state_machine_type=stepfunctions.StateMachineType.EXPRESS,
            timeout=ASK_SPINE_TIMEOUT,
            tracing_enabled=True,
            logs=stepfunctions.LogOptions(destination=self.ask_log_group, level=stepfunctions.LogLevel.ALL,
                                          include_execution_data=True),
            removal_policy=RemovalPolicy.DESTROY,
        )
        CfnOutput(self, "AskStateMachineArn", value=self.ask_state_machine.state_machine_arn)

    def _invoke(self, state_name: str, step_name: str, payload: dict, result_path: str,
                result_selector: dict | None = None) -> tasks.LambdaInvoke:
        """A state that runs one step in its own Lambda; Step Functions passes the step's JSON input."""
        return tasks.LambdaInvoke(
            self, state_name,
            lambda_function=self.step_functions[step_name].function,
            payload=stepfunctions.TaskInput.from_object(payload),
            payload_response_only=True,
            result_path=result_path,
            result_selector=result_selector,
        )

    def _judge_one_claim(self) -> stepfunctions.IChainable:
        """One Map iteration. Its input: {run_id, scope, question, claim}."""
        judge_claim = self._invoke("JudgeClaim", "judge_claim", {
            "run_id.$": "$.run_id", "claim.$": "$.claim", "scope.$": "$.scope"}, "$.judgement")
        keep_claim = stepfunctions.Pass(self, "KeepClaim", parameters={"passed": True, "claim.$": "$.claim"})
        retry_decision = self._invoke("RetryDecision", "retry_decision", {
            "run_id.$": "$.run_id", "claim_id.$": "$.claim.claim_id"}, "$.retry")
        replan = self._invoke("ReplanClaim", "run_orchestrator", {
            "question.$": "$.question", "replan_claim_id.$": "$.claim.claim_id"}, "$.replan")
        store_revised = self._invoke("StoreRevisedClaim", "store_claims", {
            "run_id.$": "$.run_id", "claims.$": "$.replan.claims"}, "$.revised", {"claim.$": "$.claims[0]"})
        use_revised = stepfunctions.Pass(self, "UseRevisedClaim", parameters={
            "run_id.$": "$.run_id", "scope.$": "$.scope", "question.$": "$.question", "claim.$": "$.revised.claim"})
        record_rejection = self._invoke("RecordRejection", "record_rejection", {
            "run_id.$": "$.run_id", "claim_id.$": "$.claim.claim_id"}, "$.rejection")
        drop_claim = stepfunctions.Pass(self, "DropClaim", parameters={"passed": False})
        record_rejection.next(drop_claim)
        store_revised.next(use_revised).next(judge_claim)
        revised_claim_returned = (stepfunctions.Choice(self, "RevisedClaimReturned")
                                  .when(stepfunctions.Condition.is_present("$.replan.claims[0]"), store_revised)
                                  .otherwise(record_rejection))
        replan.next(revised_claim_returned)
        retry_or_reject = (stepfunctions.Choice(self, "RetryOrReject")
                           .when(stepfunctions.Condition.string_equals("$.retry.decision", RETRY), replan)
                           .otherwise(record_rejection))
        retry_decision.next(retry_or_reject)
        claim_passed = (stepfunctions.Choice(self, "ClaimPassed")
                        .when(stepfunctions.Condition.boolean_equals("$.judgement.passed", True), keep_claim)
                        .otherwise(retry_decision))
        return judge_claim.next(claim_passed)

    def _ask_definition(self) -> stepfunctions.IChainable:
        start = stepfunctions.Pass(self, "Start", parameters={"question.$": "$"})
        check_budget = self._invoke("CheckBudget", "check_budget", {"question.$": "$.question"}, "$.budget")
        run_orchestrator = self._invoke("RunOrchestrator", "run_orchestrator", {
            "question.$": "$.question", "replan_claim_id": None}, "$.orchestrator")
        store_claims = self._invoke("StoreClaims", "store_claims", {
            "run_id.$": "$.question.run_id", "claims.$": "$.orchestrator.claims"}, "$.stored")
        judge_each_claim = stepfunctions.Map(
            self, "JudgeEachClaim", items_path="$.stored.claims", max_concurrency=MAX_PARALLEL_JUDGEMENTS,
            item_selector={"run_id.$": "$.question.run_id", "scope.$": "$.question.scope",
                           "question.$": "$.question", "claim.$": "$$.Map.Item.Value"},
            result_path="$.judged")
        judge_each_claim.item_processor(self._judge_one_claim())
        write_answer = self._invoke("WriteAnswer", "write_answer", {
            "run_id.$": "$.question.run_id", "question.$": "$.question",
            "passed_claims.$": PASSED_CLAIMS_FILTER, "partial.$": "$.orchestrator.partial"}, "$.answer")
        write_partial_answer = self._invoke("WritePartialAnswer", "write_answer", {
            "run_id.$": "$.question.run_id", "question.$": "$.question", "passed_claims": [],
            "partial.$": "$.budget.partial"}, "$.answer")
        answer = stepfunctions.Pass(self, "Answer", output_path="$.answer")
        write_answer.next(answer)
        write_partial_answer.next(answer)
        budget_left = (stepfunctions.Choice(self, "BudgetLeft")
                       .when(stepfunctions.Condition.is_not_null("$.budget.partial"), write_partial_answer)
                       .otherwise(run_orchestrator))
        run_orchestrator.next(store_claims).next(judge_each_claim).next(write_answer)
        return start.next(check_budget).next(budget_left)

    def ask_start_statement(self) -> iam.PolicyStatement:
        """For the /ask Lambda only: start a synchronous run of this machine and nothing else."""
        return iam.PolicyStatement(actions=["states:StartSyncExecution"],
                                   resources=[self.ask_state_machine.state_machine_arn])
```

- [ ] **Step 4: Build it in the app.** In `infra/app.py`:
  - add `from infra.stacks.flow_stack import FlowStack` (alphabetical, after the `DataStack` import);
  - add the field `flow: FlowStack` after `auth: AuthStack` (before `api: ApiStack`) in `PortalStacks`;
  - directly before the `api = ApiStack(...)` statement, add:
```python
    flow = FlowStack(app, "FlowStack", data=data, ledger=ledger, guardrail=guardrail, **stack_options("FlowStack"))
```
  - add `flow=flow` to the `PortalStacks(...)` call (before `api=api`; wrap under 120 characters).

- [ ] **Step 5: Run the tests**
```bash
uv run --locked pytest tests/infra/stacks/test_flow_stack.py --no-cov 2>&1 | tail -1
```
Expected: `8 passed`.

- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/stacks/flow_stack.py infra/app.py tests/infra/stacks/test_flow_stack.py
git commit -m "infra: FlowStack, the Express ask spine with a ledger-driven retry and a blind critic"
```
Expected: S + 16 passed [256], `TOTAL ... 96%`.

**Task done when:**
- `tests/infra/stacks/test_flow_stack.py` → 8 passed; the full suite is at S + 16.

### Task 4: Let `/ask` start the spine

**Files:**
- Modify: `infra/stacks/api_stack.py` *(new)*, `infra/app.py`, `tests/infra/stacks/test_api_stack.py` *(new)*

**Produces:** `ApiStack(scope, construct_id, *, data, auth, flow, **kwargs)`; `ApiStack._environment_for(route, flow)`, `_statements_for(route, data, flow)`. **Consumes:** `FlowStack.ask_state_machine`, `ask_start_statement()` (Task 3). **Consumed by:** Linus (L3, reads `ASK_STATE_MACHINE_ARN` through `config.get_settings().ask_state_machine_arn`).

- [ ] **Step 1: Write the failing test.**
Append to `tests/infra/stacks/test_api_stack.py` (keep everything already there):
```python


def test_only_the_ask_function_may_start_the_ask_spine(api_template):
    starters = [policy for policy in api_template.find_resources("AWS::IAM::Policy").values()
                if "states:StartSyncExecution" in str(policy["Properties"]["PolicyDocument"])]
    assert len(starters) == 1
    api_template.has_resource_properties("AWS::Lambda::Function", {
        "Environment": {"Variables": {"ASK_STATE_MACHINE_ARN": Match.any_value()}}})
```

- [ ] **Step 2: Run it and watch it fail**
```bash
uv run --locked pytest tests/infra/stacks/test_api_stack.py --no-cov 2>&1 | grep -E "^E |passed|failed" | head -3
```
Expected: `E       assert 0 == 1` and `1 failed, 10 passed`.

- [ ] **Step 3: Implement.**
In `infra/stacks/api_stack.py`, replace exactly:
```python
from infra.stacks.data_stack import DataStack
```
with:
```python
from infra.stacks.data_stack import DataStack
from infra.stacks.flow_stack import FlowStack
```

In `infra/stacks/api_stack.py`, replace exactly:
```python
    def __init__(self, scope: Construct, construct_id: str, *, data: DataStack, auth: AuthStack,
                 **kwargs) -> None:
```
with:
```python
    def __init__(self, scope: Construct, construct_id: str, *, data: DataStack, auth: AuthStack, flow: FlowStack,
                 **kwargs) -> None:
```

In `infra/stacks/api_stack.py`, replace exactly:
```python
                environment=base_environment,
                statements=self._statements_for(route, data),
```
with:
```python
                environment={**base_environment, **self._environment_for(route, flow)},
                statements=self._statements_for(route, data, flow),
```

In `infra/stacks/api_stack.py`, replace exactly:
```python
    @staticmethod
    def _statements_for(route: ApiRoute, data: DataStack) -> list[iam.PolicyStatement]:
        """Every route reads artefacts/ (scope checks and figures). Later items add the flow permissions."""
        return [data.artefacts_read_statement()]
```
with:
```python
    @staticmethod
    def _environment_for(route: ApiRoute, flow: FlowStack) -> dict[str, str]:
        """What a route needs beyond the data settings: /ask starts the ask spine (the handover)."""
        extra_environment = {"ask": {"ASK_STATE_MACHINE_ARN": flow.ask_state_machine.state_machine_arn}}
        return extra_environment.get(route.name, {})

    @staticmethod
    def _statements_for(route: ApiRoute, data: DataStack, flow: FlowStack) -> list[iam.PolicyStatement]:
        """Every route reads artefacts/ (scope checks and figures); /ask may also start the ask spine."""
        extra_statements = {"ask": [flow.ask_start_statement()]}
        return [data.artefacts_read_statement(), *extra_statements.get(route.name, [])]
```

  In `infra/app.py`, pass the flow to the API: `api = ApiStack(app, "ApiStack", data=data, auth=auth, flow=flow, **stack_options("ApiStack"))`.

- [ ] **Step 4: Run the tests**
```bash
uv run --locked pytest tests/infra/stacks/test_api_stack.py --no-cov 2>&1 | tail -1
```
Expected: `11 passed`.

- [ ] **Step 5: Full suite, synth with no credentials, commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/stacks/api_stack.py infra/app.py tests/infra/stacks/test_api_stack.py
git commit -m "infra: the ask route may start the ask spine, and nothing else may"
```
```bash
cd infra && env -u AWS_PROFILE -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q 2>&1 | grep -E "Successfully|rror"; cd ..
grep -c '"StateMachineType": "EXPRESS"' infra/cdk.out/FlowStack.template.json
grep -o '"AWS::Lambda::Function"' infra/cdk.out/FlowStack.template.json | wc -l
```
Expected: S + 17 passed [257], `TOTAL ... 96%`; `Successfully synthesized`; `1`; `7`.

**Task done when:**
- The full suite is at S + 17 with 96%.
- `infra/cdk.out/FlowStack.template.json` *(new)* has one Express machine and seven functions.

### Task 5: Deploy the skeleton and ask E4 (verify in AWS; ask Yaw first)

**Files:** none.

**Produces:** `demo-FlowStack` deployed; the walking skeleton for Patrick (D1 18:00). **Consumes:** deployed Data, Ledger, Guardrail, Auth stacks.

- [ ] **Step 1: Deploy.** (Construct IDs select stacks: `FlowStack`, `ApiStack`.)
```bash
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
cd infra && npx cdk deploy FlowStack ApiStack --require-approval never 2>&1 | grep -E "✅|AskStateMachineArn"; cd ..
```
Expected (verify in AWS): `✅  FlowStack (demo-FlowStack)`, `✅  ApiStack (demo-ApiStack)`, and `AskStateMachineArn = arn:aws:states:eu-west-1:486128667962:stateMachine:AskSpine...`.

- [ ] **Step 2: Run one question straight on the machine (stubs)**
```bash
ASK_ARN=$(aws cloudformation describe-stacks --stack-name demo-FlowStack --query "Stacks[0].Outputs[?OutputKey=='AskStateMachineArn'].OutputValue" --output text)
time aws stepfunctions start-sync-execution --state-machine-arn "$ASK_ARN" --input '{"run_id": "run-skeleton-1", "entity_id": "E4", "question": "What is blocking cutover for E4?", "budget_usd": 0.5, "max_attempts": 2, "scope": {"user_id": "user-cfo", "role": "cfo", "tenant_id": "t-01", "entity_ids": ["*"]}}' --query "[status, output]" --output text | head -c 400; echo
```
Expected (verify in AWS): `SUCCEEDED` and an output starting `{"run_id": "run-skeleton-1", "answer": {"headline": "Stub answer from the deployed ask spine", ...` with the `DEF-0412` citation. Write `SUCCEEDED` and `time`'s `real` value into the ledger.

- [ ] **Step 3: Tell Patrick and Huvison** the skeleton runs, with `AskStateMachineArn`. The `/api/ask` route still serves the stub until L3 (Task 6).

**Task done when:** the execution's status is `SUCCEEDED` with the stub `AskResponse` (ledger line), and Patrick has the ARN.

### Task 6: Switch to the real steps and the real `/ask` (after H2, and L3 for the route)

**Files:**
- Modify: `infra/stacks/flow_stack.py`, `infra/stacks/api_stack.py`

- [ ] **Step 1: Bring them in.** Check [[Build order]]: H2 (and L3 for the route) are `merged`.
```bash
git fetch origin && git rebase origin/develop
grep -n "^def check_budget\|^def run_orchestrator\|^def store_claims\|^def judge_claim\|^def retry_decision\|^def record_rejection\|^def write_answer" flow/steps.py
grep -n "^def ask\|^from flow\|^import flow" api/handlers.py
```
Expected: seven `def` lines in `flow/steps.py` *(new)*; `def ask` in `api/handlers.py` *(new)* once L3 is merged. If a step is missing, stop and ask Huvison; check its signature and JSON against spec §3 and stop on any difference.

- [ ] **Step 2: Switch the steps.** In `infra/stacks/flow_stack.py`, replace the line that **starts with** `STEPS_WITH_REAL_HANDLERS` (only that line; Y2b later adds a `PUBLISH_STEPS_WITH_REAL_HANDLERS` line that must not change) with:
```python
STEPS_WITH_REAL_HANDLERS = frozenset({"check_budget", "run_orchestrator", "store_claims", "judge_claim",
                                      "retry_decision", "record_rejection", "write_answer"})
```
  If L3 is merged, in `infra/stacks/api_stack.py` change the `ROUTES_WITH_REAL_HANDLERS` line to `ROUTES_WITH_REAL_HANDLERS = frozenset({"summary", "entity", "rows", "ask"})`. If Step 1 showed `api/handlers.py` importing `flow`, also make `API_BUNDLE` in `infra/bundling.py` *(new)* `BundleSpec("api", (*CORE_CODE, "api", "auth", "flow"))` (Y2b does the same; keep one of the two edits when rebasing).

- [ ] **Step 3: Tests and a bundling synth**
```bash
uv run --locked pytest tests/infra --no-cov 2>&1 | tail -1
cd infra && env -u AWS_PROFILE -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q 2>&1 | grep -E "Successfully|rror"; cd ..
ls infra/cdk.out/bundles/flow/flow/steps.py infra/cdk.out/bundles/flow/agents/prompts/prompts.lock
```
Expected: all `tests/infra` passed (the handler names are now `flow.steps.*`; dry-run: unchanged count); `Successfully synthesized`; both files listed. (Dry-run note: `api/`, `auth/` and `flow/` didn't exist when this plan was written, so its synth was dry-run with empty stand-in packages; on `develop` they are the real ones.)

- [ ] **Step 4: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/stacks/flow_stack.py infra/stacks/api_stack.py infra/bundling.py
git commit -m "infra: the ask spine runs Huvison's steps; /ask runs Linus's handler"
```
Expected: S + 17 passed plus the tests H2/L3 brought in, `TOTAL` not below 96%.

- [ ] **Step 5: Deploy and ask through the API (verify in AWS; ask Yaw first)**
```bash
cd infra && npx cdk deploy FlowStack ApiStack --require-approval never 2>&1 | grep "✅"; cd ..
read -rs ID_TOKEN
time curl -s -X POST -H "Authorization: Bearer $ID_TOKEN" -H "Content-Type: application/json" -d '{"entity_id": "E4", "question": "What is blocking cutover for E4?"}' "$API_URL/ask" | head -c 400; echo; unset ID_TOKEN
```
Expected (verify in AWS): an `AskResponse` whose `answer.bullets[].citations` include `DEF-0412` and whose `trace` lists the steps, `cost_usd` > 0; `real` under 29 s. Write the time into the ledger and the PR. **If the p95 is over 20 s**, stop: spec §6 (D-023, Huvison's H7 latency decision, with Patrick) before anything else.

**Task done when:** a real `/api/ask` for E4 answers with cited bullets in under 29 s (ledger line with the time), or the async decision is raised under D-023 (H7).

### Task 7: Review, then PR (after Yaw's and Patrick's OK)
- [ ] **Step 1:** Work through the Review Focus; write each result in the ledger.
- [ ] **Step 2:** `git diff origin/develop --stat` touches only `infra/` and `tests/infra/`. Expected: the files of Tasks 1–6.
- [ ] **Step 3:** Push `feature/infra-ask-spine`; open the PR to `develop` titled "FlowStack: the Express ask spine (stubs, then H2's steps)". Body: the state graph (spec §1), the step contract (§3), the measured `/ask` time, the handover deviation (`InvokeModelWithResponseStream`), the rulings. No attribution lines.
- [ ] **Step 4:** Tell Michael (M4b can wire the dashboard to `flow.ask_state_machine` and `flow.ask_log_group`), Huvison and Linus. Update [[Build order]].

**Task done when:** the PR is open to `develop` with green Jenkins; [[Build order]] shows Y2a `in review (PR #nn)`.

## Done means
- [ ] `uv run --locked pytest` → S + 17 passed, `TOTAL` ≥ 96%. *Verify:* run it.
- [ ] The synthesized `FlowStack.template.json` has one `EXPRESS` state machine and seven Lambda functions, and `JudgeClaim`'s payload keys are `run_id`, `claim`, `scope` only. *Verify:* Task 4 Step 5's commands, and `tests/infra/stacks/test_flow_stack.py` passing.
- [ ] Deployed: a direct `start-sync-execution` returns `SUCCEEDED` (stubs); after Task 6, `/api/ask` for E4 returns a cited answer in under 29 s. *Verify in AWS:* the ledger lines and the Step Functions console graph.
- [ ] The `/ask` time and the §6 decision (sync kept, or the async decision raised as the next free `DECISIONS.md` entry) are in the PR body. *Verify:* the PR.
- [ ] The PR is open (or merged) to `develop`; [[Build order]] row Y2a is updated. *Verify:* the PR page and the note.

## Never
- Feed the question, the plan or an attempt count into `JudgeClaim` (D-007).
- Decide the retry from anything but `retry_decision`'s ledger-based value; never add a counter to the state input.
- Grant `bedrock:*`, `foundation-model/*`, a `global.*` profile or a `*` resource.
- Switch a step to `flow.steps` before H2 is merged, or change the step JSON without Huvison.
- Run `cdk deploy` or `aws` commands before Yaw's OK; push to `develop` or `main`; add attribution lines.

Related: [[Build order]], [[Yaw - DevOps]], [[Workstreams]]
