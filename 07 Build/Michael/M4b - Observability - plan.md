---
tags: [build, plan, area/devops]
id: M4b
owner: Michael
spec: "[[M4b - Observability - spec]]"
status: ready
updated: 2026-10-14
---
# M4b: Observability (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it. Deploying (Task 3) and pushing are outward-facing: ask Michael first. **Task 2 needs Y1, Y2a and M4a merged:** do Task 1 any time after M2, then wait.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]]: the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[M4b - Observability - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger.
3. [[M2 - App, DataStack and LedgerStack - spec]], [[Y1 - ApiStack - spec]], [[Y2a - Express ask spine - spec]], [[M4a - WebStack - spec]]; [[Michael - DevOps]], [[Yaw - DevOps]].
4. [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]] and [[Working with AI assistants]].

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Michael (or Yaw for the API and the spine).

**Goal:** one CloudWatch dashboard (API latency and errors, `/ask` run time and outcomes, cost per run, Bedrock tokens by model), Transaction Search for AgentCore traces behind a switch, and tested app-wide rules for log retention and state-machine tracing; deployed and checked with one real `/ask` run.

**Architecture:** `infra/stacks/observability_stack.py` *(new)* reads the HTTP API (Y1) and the Express ask spine and its log group (Y2a) as Python attributes, built last by `build_stacks`. Transaction Search is account-wide, so a context switch (`-c transaction_search=off`) leaves it to the first copy. The retention and tracing rules are tests over every stack's template, so they hold for stacks added later.

**Tech stack:** Python 3.11, `aws-cdk-lib` 2.273+ (`aws_cloudwatch`, `aws_xray.CfnTransactionSearchConfig`, `aws_logs.CfnResourcePolicy`), CDK CLI 2.1144.0, pytest, uv.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your clone). **Branch:** `feature/infra-observability` from an up-to-date `develop`, after M2; Task 2 **after Y1, Y2a and M4a are merged** (`git rebase origin/develop` on your branch then).
- **Start state:** `uv run --locked pytest` → record the count in the ledger as **S**; `TOTAL` 96%. Every count below is S + n, with the dry-run value in brackets (dry-run: `feature/api-and-spine-contracts` + M2 + M3a + M3b + M4a, with stand-ins for Y1's `ApiStack` and Y2a's `FlowStack` that have no tests of their own, so S = 257).
- `eu-west-1` only (`config.DEFAULT_REGION`); Bedrock `eu.*` inference profiles only; synthetic data only; **no secrets anywhere.**
- Settings only in `config.py` (the model IDs are imported from it); domain constants only in `tools/constants.py`; deploy-time constants only in `infra/constants.py` *(new)*; descriptive names; **no single-character names**; no magic numbers or strings. The core (`tools/`) imports no boto3, Strands, adapters, config or os, and never imports `infra`.
- **`RemovalPolicy.DESTROY`** where it applies (dashboards and the resource policy are deleted with the stack by default); every log group uses `LOG_RETENTION`.
- Agents reach data only through `tools/agent_tools.py`; scope is never a tool argument; prompts only in `agents/prompts/<agent>.txt` (nothing here touches them).
- Never weaken a security rule (scope gate, create-once ledger, fail-closed critic, escaping) to pass a test. **Never loosen the retention or tracing tests to make another stack pass;** ask its owner to fix the stack.
- Tests in `tests/`, mirroring the code; `uv run --locked pytest` from the repo root; coverage must not drop (96%).
- Deploys are manual (D-018); CI builds and tests only. `export AWS_PROFILE=hackathon AWS_REGION=eu-west-1` before any `aws` or `cdk deploy` command.
- PR to `develop`; Patrick merges; never push to `develop` or `main`; **no `Co-Authored-By` and no "Generated with" lines**.
- Stay in DevOps's files: `infra/`, `tests/infra/` *(new)*.
- No layout or "meta" guard tests: the app-wide tests check synthesised resources (retention, tracing), not file placement.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **The cost query matches the real log (verify in AWS):** Task 3 Step 4 returns the run's `run_id` and a number for `cost_usd`. If the table is empty, open one `ExecutionSucceeded` event in the log group and compare its `details.output` with the regex; agree any change with Yaw.
2. **The token widget shows data (verify in AWS):** after one run, `InputTokenCount` has a point for at least one of the two model IDs. If the `ModelId` dimension differs, write the real value in the ledger and ask Patrick before changing it.
3. **Only one copy owns Transaction Search:** the second copy (M5) is always deployed with `-c transaction_search=off`; destroying the first copy turns it off for the account.
4. **The app-wide tests cover Yaw's stacks:** after Task 2, `grep -c '"AWS::Logs::LogGroup"' infra/cdk.out/*.template.json` lists Y1's and Y2a's log groups, and the retention test passed over all of them.
5. **No dashboard widget needs a setting nobody owns** (for example per-route API metrics): the dashboard reads only the metrics listed in the spec.

---

### Task 1: `ObservabilityStack` and the Transaction Search switch

**Files:**
- Modify: `infra/constants.py`
- Create: `infra/stacks/observability_stack.py`, `tests/infra/stacks/test_observability_stack.py` *(new)*

**Produces:** `infra.stacks.observability_stack.ObservabilityStack(scope, construct_id, *, prefix, http_api, ask_state_machine, ask_log_group, transaction_search: bool, **kwargs)`, `transaction_search_switch(context_value: object) -> bool`, `COST_PER_RUN_QUERY`, `BEDROCK_MODEL_IDS`; output `DashboardName`; constants `DASHBOARD_BASE_NAME`, `DASHBOARD_DEFAULT_HOURS`, `COST_TABLE_ROWS`, `TRANSACTION_SEARCH_CONTEXT_KEY`, `SWITCH_ON`, `SWITCH_OFF`, `TRANSACTION_SEARCH_INDEXING_PERCENT`, `XRAY_SPANS_POLICY_BASE_NAME`. **Consumes:** `config.DEFAULT_REASONING_MODEL`, `config.DEFAULT_RETRIEVAL_MODEL`, `infra.naming.physical_name`. **Consumed by:** Task 2, M5 (the switch).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync --locked && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/infra-observability
mkdir -p .superpowers && printf '# Ledger: M4b Observability\nS = <the count above>\n' > .superpowers/ledger-M4b.md
cd infra && npm ci && cd ..
```
Expected: S passed (dry-run 257), `TOTAL ... 96%`. Write S into the ledger.

- [ ] **Step 2: Write the failing tests.** Create `tests/infra/stacks/test_observability_stack.py`:
```python
"""ObservabilityStack: one dashboard (API latency and errors, ask-spine run time and outcomes, cost per run, Bedrock
tokens by model) and, unless switched off, CloudWatch Transaction Search for AgentCore Observability.

Uses stand-ins for the HTTP API (Y1) and the Express ask spine with its log group (Y2a)."""
import json

import aws_cdk as cdk
import pytest
from aws_cdk import RemovalPolicy
from aws_cdk import aws_apigatewayv2 as apigateway
from aws_cdk import aws_logs as logs
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk.assertions import Template

from config import DEFAULT_REASONING_MODEL, DEFAULT_RETRIEVAL_MODEL, DEFAULT_REGION
from infra.stacks.observability_stack import ObservabilityStack, transaction_search_switch

TEST_PREFIX = "test"


def _observability_template(transaction_search: bool) -> Template:
    app = cdk.App()
    environment = cdk.Environment(region=DEFAULT_REGION)
    stand_in = cdk.Stack(app, "SpineStandIn", env=environment)
    http_api = apigateway.HttpApi(stand_in, "HttpApi", create_default_stage=False)
    ask_log_group = logs.LogGroup(stand_in, "AskLogs", removal_policy=RemovalPolicy.DESTROY)
    ask_state_machine = stepfunctions.StateMachine(
        stand_in, "AskSpine", state_machine_type=stepfunctions.StateMachineType.EXPRESS,
        definition_body=stepfunctions.DefinitionBody.from_chainable(stepfunctions.Pass(stand_in, "Answer")))
    stack = ObservabilityStack(app, "ObservabilityStack", prefix=TEST_PREFIX, http_api=http_api,
                               ask_state_machine=ask_state_machine, ask_log_group=ask_log_group,
                               transaction_search=transaction_search, env=environment)
    return Template.from_stack(stack)


@pytest.fixture(scope="module")
def dashboard_body() -> str:
    dashboards = _observability_template(transaction_search=True).find_resources("AWS::CloudWatch::Dashboard")
    return json.dumps(next(iter(dashboards.values()))["Properties"]["DashboardBody"])


def test_there_is_one_dashboard_named_with_the_prefix():
    _observability_template(transaction_search=True).has_resource_properties(
        "AWS::CloudWatch::Dashboard", {"DashboardName": "test-erp-portal"})


def test_the_dashboard_shows_api_latency_and_errors(dashboard_body):
    for metric_name in ("Latency", "4xx", "5xx"):
        assert f'\\"{metric_name}\\"' in dashboard_body


def test_the_dashboard_shows_the_ask_spine_run_time_and_outcomes(dashboard_body):
    for metric_name in ("ExecutionTime", "ExecutionsSucceeded", "ExecutionsFailed", "ExecutionsTimedOut"):
        assert metric_name in dashboard_body


def test_the_dashboard_reads_cost_per_run_from_the_ask_spine_log(dashboard_body):
    assert "ExecutionSucceeded" in dashboard_body and "cost_usd" in dashboard_body and "run_id" in dashboard_body


def test_the_dashboard_shows_bedrock_tokens_for_both_models(dashboard_body):
    for model_id in (DEFAULT_REASONING_MODEL, DEFAULT_RETRIEVAL_MODEL):
        assert model_id in dashboard_body
    assert "InputTokenCount" in dashboard_body and "OutputTokenCount" in dashboard_body


def test_transaction_search_and_its_log_policy_are_created_when_switched_on():
    template = _observability_template(transaction_search=True)
    template.resource_count_is("AWS::XRay::TransactionSearchConfig", 1)
    template.has_resource_properties("AWS::Logs::ResourcePolicy", {"PolicyName": "test-erp-portal-xray-spans"})


def test_a_second_copy_in_the_same_account_can_leave_transaction_search_alone():
    template = _observability_template(transaction_search=False)
    template.resource_count_is("AWS::XRay::TransactionSearchConfig", 0)
    template.resource_count_is("AWS::Logs::ResourcePolicy", 0)


@pytest.mark.parametrize(("context_value", "expected"), [(None, True), ("on", True), ("off", False)])
def test_the_transaction_search_switch_reads_on_and_off(context_value, expected):
    assert transaction_search_switch(context_value) is expected


def test_the_transaction_search_switch_refuses_anything_else():
    with pytest.raises(ValueError, match="transaction_search"):
        transaction_search_switch("yes")
```
The dashboard body is a JSON string inside the template, so metric names appear with escaped quotes (`\"Latency\"`); the first test matches them exactly so `Latency` can't match inside another word.

- [ ] **Step 3: Run them and watch them fail**
```bash
uv run --locked pytest tests/infra/stacks/test_observability_stack.py --no-cov 2>&1 | grep -E "^E |error"
```
Expected: `E   ModuleNotFoundError: No module named 'infra.stacks.observability_stack'` and `1 error`.

- [ ] **Step 4: Add the constants.** Append to `infra/constants.py`:
```python

# Observability (ObservabilityStack, M4b).
DASHBOARD_BASE_NAME = "erp-portal"
DASHBOARD_DEFAULT_HOURS = 3                       # the demo window
COST_TABLE_ROWS = 20                              # latest runs shown in the cost-per-run table
TRANSACTION_SEARCH_CONTEXT_KEY = "transaction_search"   # -c transaction_search=off for a second copy (M5)
SWITCH_ON = "on"
SWITCH_OFF = "off"
TRANSACTION_SEARCH_INDEXING_PERCENT = 1           # the free tier; AgentCore spans reach aws/spans either way
XRAY_SPANS_POLICY_BASE_NAME = "erp-portal-xray-spans"
```

- [ ] **Step 5: Implement the stack.** Create `infra/stacks/observability_stack.py`:
```python
"""ObservabilityStack: one CloudWatch dashboard for the demo and, once per account, CloudWatch Transaction Search,
which AgentCore Observability needs to show the agents' traces. Log retention is set where each log group is made
(LOG_RETENTION); tracing is switched on where each function and state machine is made (Y1, Y2a, Y3)."""
from aws_cdk import Aws, CfnOutput, Duration, Stack
from aws_cdk import aws_apigatewayv2 as apigateway
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_logs as logs
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk import aws_xray as xray
from constructs import Construct

from config import DEFAULT_REASONING_MODEL, DEFAULT_RETRIEVAL_MODEL
from infra.constants import (COST_TABLE_ROWS, DASHBOARD_BASE_NAME, DASHBOARD_DEFAULT_HOURS, SWITCH_OFF, SWITCH_ON,
                             TRANSACTION_SEARCH_CONTEXT_KEY, TRANSACTION_SEARCH_INDEXING_PERCENT,
                             XRAY_SPANS_POLICY_BASE_NAME)
from infra.naming import physical_name

MEDIAN = "p50"
TAIL = "p99"
TOTAL = "Sum"
BEDROCK_NAMESPACE = "AWS/Bedrock"
BEDROCK_MODEL_IDS = (DEFAULT_REASONING_MODEL, DEFAULT_RETRIEVAL_MODEL)
TOKEN_METRICS = ("InputTokenCount", "OutputTokenCount")
# The Express ask spine logs every execution with its data (Y2a); its output is the AskResponse (C1).
COST_PER_RUN_QUERY = (
    "fields @timestamp",
    'filter type = "ExecutionSucceeded"',
    'parse details.output /"run_id":\\s*"(?<run_id>[^"]+)"/',
    'parse details.output /"cost_usd":\\s*(?<cost_usd>[0-9.]+)/',
    "display @timestamp, run_id, cost_usd",
    "sort @timestamp desc",
    f"limit {COST_TABLE_ROWS}",
)
# CloudWatch Transaction Search: X-Ray writes spans to these log groups (AWS docs, "Enable Transaction Search").
XRAY_SPAN_LOG_GROUPS = ("aws/spans", "/aws/application-signals/data")
IAM_POLICY_VERSION = "2012-10-17"


def transaction_search_switch(context_value: object) -> bool:
    """`-c transaction_search=on|off`; on when not given. Anything else is refused, never guessed."""
    if context_value is None or context_value == SWITCH_ON:
        return True
    if context_value == SWITCH_OFF:
        return False
    raise ValueError(f"{TRANSACTION_SEARCH_CONTEXT_KEY} must be {SWITCH_ON!r} or {SWITCH_OFF!r}, "
                     f"not {context_value!r}")


class ObservabilityStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, prefix: str, http_api: apigateway.IHttpApi,
                 ask_state_machine: stepfunctions.IStateMachine, ask_log_group: logs.ILogGroup,
                 transaction_search: bool, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        dashboard = cloudwatch.Dashboard(self, "Dashboard",
                                         dashboard_name=physical_name(prefix, DASHBOARD_BASE_NAME),
                                         default_interval=Duration.hours(DASHBOARD_DEFAULT_HOURS))
        dashboard.add_widgets(
            cloudwatch.GraphWidget(title="API latency (ms)", left=[
                http_api.metric_latency(statistic=MEDIAN), http_api.metric_latency(statistic=TAIL)]),
            cloudwatch.GraphWidget(title="API errors", left=[
                http_api.metric_client_error(statistic=TOTAL), http_api.metric_server_error(statistic=TOTAL)]),
        )
        dashboard.add_widgets(
            cloudwatch.GraphWidget(title="/ask run time (ms)", left=[
                ask_state_machine.metric_time(statistic=MEDIAN), ask_state_machine.metric_time(statistic=TAIL)]),
            cloudwatch.GraphWidget(title="/ask runs", left=[
                ask_state_machine.metric_succeeded(statistic=TOTAL),
                ask_state_machine.metric_failed(statistic=TOTAL),
                ask_state_machine.metric_timed_out(statistic=TOTAL)]),
        )
        dashboard.add_widgets(
            cloudwatch.LogQueryWidget(title="Cost per run (USD)", log_group_names=[ask_log_group.log_group_name],
                                      query_lines=list(COST_PER_RUN_QUERY),
                                      view=cloudwatch.LogQueryVisualizationType.TABLE),
            cloudwatch.GraphWidget(title="Bedrock tokens by model", left=[
                cloudwatch.Metric(namespace=BEDROCK_NAMESPACE, metric_name=metric_name,
                                  dimensions_map={"ModelId": model_id}, statistic=TOTAL)
                for model_id in BEDROCK_MODEL_IDS for metric_name in TOKEN_METRICS]),
        )
        if transaction_search:
            self._enable_transaction_search(prefix)
        CfnOutput(self, "DashboardName", value=dashboard.dashboard_name)

    def _enable_transaction_search(self, prefix: str) -> None:
        """Account-wide, so only one copy of the app may own it (M5 deploys a second copy with it off)."""
        policy = logs.CfnResourcePolicy(self, "XRaySpansPolicy",
                                        policy_name=physical_name(prefix, XRAY_SPANS_POLICY_BASE_NAME),
                                        policy_document=self.to_json_string(_xray_spans_policy()))
        search = xray.CfnTransactionSearchConfig(self, "TransactionSearch",
                                                 indexing_percentage=TRANSACTION_SEARCH_INDEXING_PERCENT)
        search.add_dependency(policy)


def _xray_spans_policy() -> dict:
    """Lets X-Ray, from this account only, write spans to the two Transaction Search log groups."""
    account_arn_prefix = f"arn:{Aws.PARTITION}:logs:{Aws.REGION}:{Aws.ACCOUNT_ID}:log-group:"
    return {
        "Version": IAM_POLICY_VERSION,
        "Statement": [{
            "Sid": "TransactionSearchXRayAccess",
            "Effect": "Allow",
            "Principal": {"Service": "xray.amazonaws.com"},
            "Action": "logs:PutLogEvents",
            "Resource": [f"{account_arn_prefix}{log_group}:*" for log_group in XRAY_SPAN_LOG_GROUPS],
            "Condition": {
                "ArnLike": {"aws:SourceArn": f"arn:{Aws.PARTITION}:xray:{Aws.REGION}:{Aws.ACCOUNT_ID}:*"},
                "StringEquals": {"aws:SourceAccount": Aws.ACCOUNT_ID},
            },
        }],
    }
```
The resource policy is a CloudWatch Logs resource policy (who may write to which log group), not an IAM role: the `:*` on the two named log-group ARNs and the source-ARN condition are what AWS documents for Transaction Search, and no action or resource is a bare `*`.

- [ ] **Step 6: Run them**
```bash
uv run --locked pytest tests/infra/stacks/test_observability_stack.py --no-cov 2>&1 | tail -1
```
Expected: `11 passed`.

- [ ] **Step 7: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/constants.py infra/stacks/observability_stack.py tests/infra/stacks/test_observability_stack.py
git commit -m "infra: ObservabilityStack, one dashboard with cost per run and Transaction Search behind a switch (M4b)"
```
Expected: S + 11 passed (`268 passed`), `TOTAL ... 96%`.

**Task done when:**
- The eleven observability tests pass and the suite is at S + 11.

### Task 2: Wire it into the app, with the app-wide retention and tracing rules (after Y1, Y2a and M4a are merged)

**Files:**
- Modify: `infra/app.py` *(new)*, `tests/infra/test_app.py` *(new)*

**Produces:** `PortalStacks.observability`; the context switch read in `build_stacks`; four app-wide tests. **Consumes:** `PortalStacks.api.http_api` (Y1), `PortalStacks.flow.ask_state_machine`, `PortalStacks.flow.ask_log_group` (Y2a), the `web_build_directory` fixture (M4a). **Consumed by:** M5 (`-c transaction_search=off`).

- [ ] **Step 1: Bring in Y1, Y2a and M4a.** Check [[Build order]]: all three must be `merged`. Then:
```bash
git fetch origin && git rebase origin/develop
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
grep -n "ask_state_machine\|ask_log_group" infra/stacks/flow_stack.py | head -4
grep -n "web = WebStack\|flow = FlowStack\|api = ApiStack" infra/app.py
```
Expected: all passed; write the count into the ledger as **S1** (dry-run with stand-ins: `268 passed`); `flow_stack.py` defines `self.ask_state_machine` and `self.ask_log_group`; `app.py` has the three lines. If any is missing, stop and ask Yaw or Michael.

- [ ] **Step 2: Write the failing tests.** In `tests/infra/test_app.py`:
  - add `from aws_cdk.assertions import Template` after `import pytest`;
  - change the `infra.constants` import to `from infra.constants import STACK_PREFIX_CONTEXT_KEY, TRANSACTION_SEARCH_CONTEXT_KEY` (keep any other names already imported there);
  - below the imports, add `TWO_WEEKS_IN_DAYS = 14   # infra.constants.LOG_RETENTION as CloudFormation writes it`;
  - append:
```python


def _resources_of_type(portal_stacks, resource_type: str) -> list[dict]:
    return [resource for stack in _all_stacks(portal_stacks)
            for resource in Template.from_stack(stack).find_resources(resource_type).values()]


def test_every_log_group_keeps_two_weeks_and_goes_with_its_stack(portal_stacks):
    log_groups = _resources_of_type(portal_stacks, "AWS::Logs::LogGroup")
    assert log_groups
    for log_group in log_groups:
        assert log_group["Properties"]["RetentionInDays"] == TWO_WEEKS_IN_DAYS
        assert log_group["DeletionPolicy"] == "Delete"


def test_every_state_machine_sends_traces_to_x_ray(portal_stacks):
    for state_machine in _resources_of_type(portal_stacks, "AWS::StepFunctions::StateMachine"):
        assert state_machine["Properties"]["TracingConfiguration"] == {"Enabled": True}


def test_the_dashboard_is_built_from_the_api_and_the_ask_spine(portal_stacks):
    portal_stacks.observability.node.root.synth()
    dependencies = {dependency.stack_name for dependency in portal_stacks.observability.dependencies}
    assert {portal_stacks.api.stack_name, portal_stacks.flow.stack_name} <= dependencies


def test_transaction_search_can_be_switched_off_for_a_second_copy(web_build_directory):
    second_copy = build_stacks(cdk.App(context={STACK_PREFIX_CONTEXT_KEY: "demo2",
                                                TRANSACTION_SEARCH_CONTEXT_KEY: "off",
                                                "aws:cdk:bundling-stacks": []}),
                               web_build_directory=web_build_directory)
    Template.from_stack(second_copy.observability).resource_count_is("AWS::XRay::TransactionSearchConfig", 0)
```

- [ ] **Step 3: Run them and watch two fail**
```bash
uv run --locked pytest tests/infra/test_app.py --no-cov 2>&1 | grep -E "^E  |passed|failed"
```
Expected: two lines `E       AttributeError: 'PortalStacks' object has no attribute 'observability'`, then `2 failed, ... passed` (dry-run: `2 failed, 6 passed`). **The retention and tracing tests already pass:** that is expected, because they check rules every earlier stack was built to follow; they exist to keep later stacks honest. If either of them **fails**, stop: a stack (yours or Yaw's) breaks the rule; tell its owner, don't change the test.

- [ ] **Step 4: Wire it.** In `infra/app.py`:
  - change the `infra.constants` import to also import `TRANSACTION_SEARCH_CONTEXT_KEY` (for example `from infra.constants import STACK_PREFIX_CONTEXT_KEY, TRANSACTION_SEARCH_CONTEXT_KEY, WEB_BUILD_DIRECTORY`; keep any other names);
  - add `from infra.stacks.observability_stack import ObservabilityStack, transaction_search_switch` among the `infra.stacks` imports (alphabetical: after `ledger_stack`);
  - add the field `observability: ObservabilityStack` as the last field of `PortalStacks`;
  - directly after the `web = WebStack(...)` statement, add:
    ```python
        observability = ObservabilityStack(
            app, "ObservabilityStack", prefix=prefix, http_api=api.http_api, ask_state_machine=flow.ask_state_machine,
            ask_log_group=flow.ask_log_group,
            transaction_search=transaction_search_switch(app.node.try_get_context(TRANSACTION_SEARCH_CONTEXT_KEY)),
            **stack_options("ObservabilityStack"))
    ```
  - add `observability=observability` to the `PortalStacks(...)` call in the `return`.

- [ ] **Step 5: Run them**
```bash
uv run --locked pytest tests/infra/test_app.py --no-cov 2>&1 | tail -1
```
Expected: all passed (dry-run: `8 passed`).

- [ ] **Step 6: Full suite, both synths, commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
ls web/dist/web/browser/index.html || (cd web && corepack enable && yarn install --frozen-lockfile && yarn build)
cd infra
env -u AWS_PROFILE AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q 2>&1 | grep -E "Successfully|rror"
grep -c TransactionSearchConfig cdk.out/ObservabilityStack.template.json
env -u AWS_PROFILE AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q -c prefix=demo2 -c transaction_search=off 2>&1 | grep -E "Successfully|rror"
grep -c TransactionSearchConfig cdk.out/ObservabilityStack.template.json
cd ..
git add infra/app.py tests/infra/test_app.py
git commit -m "infra: build ObservabilityStack last; every log group keeps two weeks and every state machine is traced"
```
Expected: S1 + 4 passed (dry-run `272 passed`), `TOTAL ... 96%`; `Successfully synthesized` then `1`; `Successfully synthesized` then `0`.

**Task done when:**
- `uv run --locked pytest` is at S1 + 4 with 96%.
- The default synth has one `TransactionSearchConfig`; the `transaction_search=off` synth has none.

### Task 3: Deploy, check one `/ask` run end to end, open the PR (verify in AWS; ask Michael first)

**Files:** none (deploy, checks and PR only).

**Produces:** a deployed `demo-ObservabilityStack`; the dashboard name for the demo; the PR.

- [ ] **Step 1: Deploy (with Michael's OK).** The web build must exist (Task 2 Step 6).
```bash
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
cd infra && npx cdk deploy ObservabilityStack --require-approval never 2>&1 | tail -4; cd ..
```
Expected (verify in AWS): `✅  demo-ObservabilityStack` and `DashboardName = demo-erp-portal`. If the deploy fails on `TransactionSearchConfig` with "already exists" or "already enabled", Transaction Search was turned on outside CDK in this account: stop and ask Patrick (either turn it off by hand once, which he decides, or deploy with `-c transaction_search=off` and record it in the PR).

- [ ] **Step 2: Transaction Search is on (verify in AWS)**
```bash
aws xray get-trace-segment-destination --output text
```
Expected: `CloudWatchLogs	ACTIVE`.

- [ ] **Step 3: Run one `/ask` through the deployed API (verify in AWS; needs Y2a, Linus's `/ask` handler and a demo password).** Use the E4 lead through CloudFront, as in [[M4a - WebStack - plan]] Task 5:
```bash
stack_output() { aws cloudformation describe-stacks --stack-name "$1" --query "Stacks[0].Outputs[?OutputKey=='$2'].OutputValue" --output text; }
PORTAL_URL=$(stack_output demo-WebStack PortalUrl)
USER_POOL_ID=$(stack_output demo-AuthStack UserPoolId)
USER_POOL_CLIENT_ID=$(stack_output demo-AuthStack UserPoolClientId)
read -rsp "Password for e4-lead-user: " demo_password && echo
E4_ID_TOKEN=$(aws cognito-idp admin-initiate-auth --user-pool-id "$USER_POOL_ID" --client-id "$USER_POOL_CLIENT_ID" \
  --auth-flow ADMIN_USER_PASSWORD_AUTH --auth-parameters "USERNAME=e4-lead-user,PASSWORD=${demo_password}" \
  --query AuthenticationResult.IdToken --output text)
unset demo_password
curl -s -X POST -H "Authorization: Bearer ${E4_ID_TOKEN}" -H "Content-Type: application/json" \
  -d '{"entity_id": "E4", "question": "What is blocking cutover for E4?"}' "${PORTAL_URL}/api/ask" \
  | uv run python -c "import json, sys; response = json.load(sys.stdin); print(response['run_id'], response['cost_usd'])"
unset E4_ID_TOKEN
```
Expected: one line `<run_id> <cost_usd>` (for example `run-... 0.03`). Write both into the ledger.

- [ ] **Step 4: The dashboard's cost query finds that run (verify in AWS; Review Focus 1)**
```bash
ASK_LOG_GROUP=$(aws cloudwatch get-dashboard --dashboard-name demo-erp-portal --query DashboardBody --output text \
  | uv run python -c "import json, sys; body = json.load(sys.stdin); print(next(widget['properties']['query'] for widget in body['widgets'] if widget['type'] == 'log').split(\"'\")[1])")
echo "$ASK_LOG_GROUP"
QUERY_ID=$(aws logs start-query --log-group-name "$ASK_LOG_GROUP" --start-time $(( $(date +%s) - 3600 )) --end-time $(date +%s) \
  --query-string 'fields @timestamp | filter type = "ExecutionSucceeded" | parse details.output /"run_id":\s*"(?<run_id>[^"]+)"/ | parse details.output /"cost_usd":\s*(?<cost_usd>[0-9.]+)/ | display @timestamp, run_id, cost_usd | sort @timestamp desc | limit 20' \
  --query queryId --output text)
sleep 10; aws logs get-query-results --query-id "$QUERY_ID" --query "results[0][?field=='run_id' || field=='cost_usd'].value" --output text
```
Expected: the ask spine's log group name (the dashboard widget's query starts `SOURCE '<log group>'`), then the `run_id` and `cost_usd` from Step 3. An empty result: see Review Focus 1.

- [ ] **Step 5: Tokens and the trace (verify in AWS; Review Focus 2)**
```bash
aws cloudwatch get-metric-statistics --namespace AWS/Bedrock --metric-name InputTokenCount \
  --dimensions Name=ModelId,Value=eu.anthropic.claude-sonnet-4-6 --statistics Sum \
  --start-time $(date -u -d '-1 hour' +%Y-%m-%dT%H:%M:%SZ) --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) --period 3600 \
  --query "Datapoints[0].Sum"
```
Expected: a number above `0`. Then open the dashboard (`https://eu-west-1.console.aws.amazon.com/cloudwatch/home?region=eu-west-1#dashboards/dashboard/demo-erp-portal`) and CloudWatch → Application Signals → Transaction Search, filter by the last hour: the `/ask` run's trace is listed. Record both in the ledger (a screenshot path is fine; nothing secret is on screen).

- [ ] **Step 6: Review Focus, then the PR (with Michael's OK).** Work through the Review Focus list and write each result in the ledger. Then:
```bash
git push -u origin feature/infra-observability
gh pr create --repo Amali-Tech/cloud-9-hackathon --base develop --title "infra: ObservabilityStack, dashboard, cost per run, Transaction Search (M4b)" --body-file .superpowers/pr-M4b.md
```
Write `.superpowers/pr-M4b.md` first: what changed (the dashboard rows, the cost query and its dependency on Y2a's execution logging, Transaction Search and the `-c transaction_search=off` rule for second copies, the two app-wide rules), the test count, the results of Steps 2–5 (no tokens), and the ledger's `Ruling:` lines. No attribution lines.
Expected: the PR opens against `develop`; the Jenkins check goes green.

- [ ] **Step 7: Tell the team.** Post the dashboard link for the demo (Clement, Patrick) and the `-c transaction_search=off` rule for the second copy (Patrick, M5). Update [[Build order]]: M4b `in review (PR #nn)`.

**Task done when:**
- Step 4 printed the run's `run_id` and `cost_usd`, and Step 2 printed `CloudWatchLogs ACTIVE`.
- The PR is open with a green Jenkins check.

## Done means
- [ ] **The suite is green with the observability tests.** Verify: `uv run --locked pytest 2>&1 | grep -E "passed|TOTAL"` on the branch → S1 + 4 passed (dry-run 272), `TOTAL ... 96%`.
- [ ] **Every log group keeps two weeks and every state machine is traced.** Verify: `uv run --locked pytest tests/infra/test_app.py --no-cov -k "log_group or traces" 2>&1 | tail -1` → `2 passed`.
- [ ] **The switch works offline.** Verify: Task 2 Step 6 → `1` for the default synth and `0` for `-c transaction_search=off`.
- [ ] **The dashboard exists (verify in AWS).** Verify: `aws cloudwatch get-dashboard --dashboard-name demo-erp-portal --query DashboardName --output text` → `demo-erp-portal`.
- [ ] **One `/ask` run shows its cost (verify in AWS).** Verify: Task 3 Step 4 → the `run_id` and `cost_usd` of Step 3.
- [ ] **Traces are collected (verify in AWS).** Verify: `aws xray get-trace-segment-destination --output text` → `CloudWatchLogs	ACTIVE`; the run's trace is in Transaction Search (ledger note).
- [ ] **PR open to `develop`, green, and [[Build order]] says `in review (PR #nn)`.** Verify: `gh pr checks <nn> --repo Amali-Tech/cloud-9-hackathon` → the Jenkins check `pass`.

## Never
- Turn Transaction Search on or off in the console, or deploy a second copy without `-c transaction_search=off`.
- Loosen the retention or tracing test to let a stack through (ask its owner to fix the stack).
- Compute cost in the dashboard (it shows `AskResponse.cost_usd`, computed by `flow/cost.py` *(new)*).
- Print or save tokens or passwords; deploy from CI; push to `develop` or `main`; add attribution lines.

Related: [[M4b - Observability - spec]], [[Build order]], [[Michael - DevOps]], [[How to execute a plan]]
