---
tags: [build, plan, area/devops]
id: Y4
owner: Yaw
spec: "[[Y4 - IAM least-privilege review - spec]]"
status: ready
updated: 2026-10-14
---
# Y4: IAM least-privilege review (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it. Deploying and pushing are outward-facing: ask Yaw (and Patrick for the PR) first.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Y4 - IAM least-privilege review - spec]]: **the authority.**
3. [[Workstreams]] (`06 Workstreams/`): the architecture with owners, the code already built, the contracts and the rules (§7).
4. [[Yaw - DevOps]]: the owner's brief; and [[Michael - DevOps]] (the other half of DevOps).
5. [[Build order]]: what this item depends on and unblocks.
6. [[M2 - App, DataStack and LedgerStack - spec]]: the CDK app, `build_stacks`, the prefix, the test fixtures and the patterns every DevOps item follows.
7. Every stack's spec (listed in the Y4 spec §0) and [[M5 - Clean-deploy runbook - spec]].
8. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Yaw (owner) or Patrick (reviewer). Never invent a name, a shape or a rule.

**Goal:** a test proves no workload role has a wildcard action, a bare `*` resource or a managed policy, for both agent hosts; the roles table is in `infra/README.md`; Patrick has reviewed it before clean-deploy check 1.

**Architecture:** one new test module; one section in `infra/README.md`. No stack code changes unless the test finds something (then the stack's owner fixes it).

**Tech stack:** Python 3.11, `aws-cdk-lib` 2.273+ (`aws_cdk.assertions.Template`), pytest, uv.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. **Branch:** `chore/iam-least-privilege` from an up-to-date `develop`, **after every stack item is merged** (Y1, Y2a, Y2b, Y3a, Y3b, M2, M3a, M3b, M4a, M4b). If one isn't, do Task 1 anyway and re-run it when it lands.
- **Start state:** `uv run --locked pytest` → all passed, `TOTAL` 96%; write the count as **S** (dry-run: C1 + M2 + stand-ins for M3a/M3b + Y1–Y3b, without M4a/M4b, S = 284). Every count is **S + n** [dry-run].
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
1. **The deployed roles match the templates:** for two roles (the `approve` function, the shim), `aws iam list-role-policies` + `get-role-policy` show exactly the table's actions (read-only calls, verify in AWS).
2. **Resource policies:** the data bucket's policy only enforces TLS and allows CloudFront's OAC read on the site bucket (M4a); no `Principal: "*"` allow without a condition.
3. **The handover is true:** every row of `docs/DEVOPS_HANDOVER.md`'s IAM column matches the table, plus the two documented deviations (`InvokeModelWithResponseStream`; `UpdateItem` on `/approve`). Send Patrick the diff.
4. **No human credentials in any stack:** `grep -rn "aws_access_key\|secret" infra/ --include=*.py` finds nothing.
5. **Both hosts were checked:** the test names show `agentcore/…` and `lambda/…` keys (run it with `-vv` once).

---

### Task 1: The least-privilege test over every template

**Files:**
- Create: `tests/infra/test_least_privilege.py` *(new)*

**Produces:** `find_violations(template: dict) -> list[str]`, `ACTIONS_WITHOUT_RESOURCE_SCOPE`, `CDK_FRAMEWORK_FRAGMENTS`, `CDK_ASSET_BUCKET_MARKER`, the `all_templates` fixture. **Consumes:** `stacks_with_context` (Y1), `AGENT_HOST_CONTEXT_KEY`, `AGENT_HOSTS` (Y3b). **Consumed by:** CI on every PR from now on.

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync --locked && (cd infra && npm ci)
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c chore/iam-least-privilege
```
Expected: S passed (dry-run 284), `TOTAL ... 96%`.

- [ ] **Step 2: Write the test.** It checks code that already exists, so it may pass at once; its own self-tests prove it catches each kind of violation.
Create `tests/infra/test_least_privilege.py`:
```python
"""Least privilege over every synthesized template (ARCHITECTURE.md §7, Y4): no wildcard action, no "*" resource,
and no AWS managed policy on any workload role, for both agent hosts.

The only exceptions are listed here with their reason, so a reviewer reads one place:
- actions AWS offers no resource-level permission for (X-Ray, CloudWatch Logs delivery, PutMetricData);
- CDK's own deploy-time constructs, which we don't write (the artefacts upload, the bucket emptier);
- the read CDK grants on its bootstrap asset bucket so AgentCore can fetch the runtime's code zip.
"""
import json

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template

from infra.stacks.flow_stack import AGENT_HOST_CONTEXT_KEY, AGENT_HOSTS

ANY_RESOURCE = "*"
WILDCARD = "*"
# https://docs.aws.amazon.com/service-authorization/latest/reference/ : "Resource types: none" for each of these.
ACTIONS_WITHOUT_RESOURCE_SCOPE = frozenset({
    "xray:PutTraceSegments", "xray:PutTelemetryRecords", "xray:GetSamplingRules", "xray:GetSamplingTargets",
    "logs:CreateLogDelivery", "logs:GetLogDelivery", "logs:UpdateLogDelivery", "logs:DeleteLogDelivery",
    "logs:ListLogDeliveries", "logs:PutResourcePolicy", "logs:DescribeResourcePolicies", "logs:DescribeLogGroups",
    "cloudwatch:PutMetricData",
})
# Logical-ID fragments of CDK's framework constructs: their roles are generated by CDK, run only at deploy time,
# and are reviewed as a whole in infra/README.md "Workload roles" rather than rewritten.
CDK_FRAMEWORK_FRAGMENTS = ("CustomCDKBucketDeployment", "CustomS3AutoDeleteObjectsCustomResourceProvider",
                           "ProviderframeworkonEvent", "AWS679f53fac002430cb0da5b7982bd2287")
CDK_ASSET_BUCKET_MARKER = "cdk-hnb659fds-assets"


def _as_list(value) -> list:
    return value if isinstance(value, list) else [value]


@pytest.fixture(scope="module")
def all_templates(stacks_with_context) -> dict[str, dict]:
    """Every stack of the app, for both agent hosts, as synthesized templates keyed by host and stack ID."""
    templates = {}
    for agent_host in AGENT_HOSTS:
        stacks = stacks_with_context({AGENT_HOST_CONTEXT_KEY: agent_host})
        templates.update({f"{agent_host}/{stack.node.id}": Template.from_stack(stack).to_json()
                          for stack in vars(stacks).values() if isinstance(stack, cdk.Stack)})
    return templates


def _is_framework(logical_id: str) -> bool:
    return any(fragment in logical_id for fragment in CDK_FRAMEWORK_FRAGMENTS)


def _statements(template: dict):
    """Every (logical ID, statement) of every identity policy: AWS::IAM::Policy and roles' inline policies."""
    for logical_id, resource in template["Resources"].items():
        if resource["Type"] == "AWS::IAM::Policy":
            documents = [resource["Properties"]["PolicyDocument"]]
        elif resource["Type"] == "AWS::IAM::Role":
            documents = [policy["PolicyDocument"] for policy in resource["Properties"].get("Policies", [])]
        else:
            continue
        for document in documents:
            for statement in document["Statement"]:
                yield logical_id, statement


def find_violations(template: dict) -> list[str]:
    violations = []
    for logical_id, statement in _statements(template):
        if _is_framework(logical_id):
            continue
        actions, resources = _as_list(statement["Action"]), _as_list(statement.get("Resource", ANY_RESOURCE))
        reads_cdk_assets = all(CDK_ASSET_BUCKET_MARKER in json.dumps(resource) for resource in resources)
        if any(WILDCARD in action for action in actions) and not reads_cdk_assets:
            violations.append(f"{logical_id}: wildcard action in {actions}")
        if ANY_RESOURCE in resources and not set(actions) <= ACTIONS_WITHOUT_RESOURCE_SCOPE:
            violations.append(f"{logical_id}: '*' resource for {sorted(set(actions) - ACTIONS_WITHOUT_RESOURCE_SCOPE)}")
    for logical_id, resource in template["Resources"].items():
        if resource["Type"] == "AWS::IAM::Role" and resource["Properties"].get("ManagedPolicyArns") \
                and not _is_framework(logical_id):
            violations.append(f"{logical_id}: AWS managed policy on a workload role")
    return violations


def test_no_stack_grants_wildcards(all_templates):
    violations = {name: find_violations(template) for name, template in all_templates.items()}
    assert {name: found for name, found in violations.items() if found} == {}


def _template_with(statement: dict, logical_id: str = "SomeFunctionRoleDefaultPolicy") -> dict:
    return {"Resources": {logical_id: {"Type": "AWS::IAM::Policy",
                                       "Properties": {"PolicyDocument": {"Statement": [statement]}}}}}


@pytest.mark.parametrize("statement", [
    {"Action": "s3:*", "Resource": "arn:aws:s3:::bucket/artefacts/*"},
    {"Action": "s3:GetObject*", "Resource": "arn:aws:s3:::bucket/artefacts/*"},
    {"Action": "dynamodb:Query", "Resource": "*"},
    {"Action": ["xray:PutTraceSegments", "bedrock:InvokeModel"], "Resource": "*"},
], ids=["service_wildcard", "action_suffix_wildcard", "any_resource", "allowed_action_mixed_with_scoped_one"])
def test_the_check_catches_each_kind_of_wildcard(statement):
    assert len(find_violations(_template_with(statement))) == 1


def test_the_check_allows_scoped_statements_and_unscopable_actions():
    scoped = {"Action": "s3:GetObject", "Resource": "arn:aws:s3:::bucket/artefacts/*"}
    assert find_violations(_template_with(scoped)) == []
    assert find_violations(_template_with({"Action": "xray:PutTraceSegments", "Resource": "*"})) == []
```

- [ ] **Step 3: Run it**
```bash
uv run --locked pytest tests/infra/test_least_privilege.py --no-cov -vv 2>&1 | grep -E "PASSED|FAILED|^E  " | head -20
```
Expected on the dry-run state: `6 passed` (`test_no_stack_grants_wildcards`, the four `test_the_check_catches_each_kind_of_wildcard[...]` cases, `test_the_check_allows_scoped_statements_and_unscopable_actions`). **On `develop` with M4a as planned**, expect `test_no_stack_grants_wildcards` to **fail** with one violation, `'agentcore/WebStack': ['PortalCallbackHandlerServiceRole…: AWS managed policy on a workload role']` (and the same for `lambda/WebStack`). Any other violation is a finding for that stack's owner: record it in the ledger and go to Step 4.

- [ ] **Step 4: Fix findings with their owners (never by widening the exceptions).** For the expected M4a finding, ask Michael to build the callback handler with `PortalFunction` in `infra/stacks/web_stack.py` *(new)* (his file, his commit), replacing the `handler = lambda_.Function(...)` statement and the `handler.add_to_role_policy(...)` call with:
```python
        callback = PortalFunction(
            self, "PortalCallbackHandler",
            handler=INLINE_HANDLER,
            code=lambda_.Code.from_inline(PORTAL_CALLBACK_SOURCE.read_text()),
            environment={},
            statements=[iam.PolicyStatement(
                actions=["cognito-idp:DescribeUserPoolClient", "cognito-idp:UpdateUserPoolClient"],
                resources=[user_pool.user_pool_arn])],
            timeout=Duration.seconds(CUSTOM_RESOURCE_TIMEOUT_SECONDS),
        )
```
  and passing `on_event_handler=callback.function` to the `Provider` (plus `from infra.portal_function import PortalFunction`; the function's own log group replaces `PortalCallbackLogs`). Re-run Step 3 after his fix is merged and rebased in. Do **not** add `PortalCallbackHandler` to `CDK_FRAMEWORK_FRAGMENTS`: it is our role.

- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add tests/infra/test_least_privilege.py
git commit -m "test: least privilege over every synthesized template, both agent hosts"
```
Expected: S + 6 passed [290], `TOTAL ... 96%`, once every finding is fixed.

**Task done when:** `tests/infra/test_least_privilege.py` → 6 passed on `develop` + this branch; every finding is fixed by its owner (ledger lines with the fixing commit).

### Task 2: The roles table in `infra/README.md`

**Files:**
- Modify: `infra/README.md` (append one section; Michael's M5 owns the deploy sections, so keep theirs as they are)

- [ ] **Step 1: Append** this section at the end of `infra/README.md`:
```markdown
## Workload roles (least privilege)
One role per function, state machine and runtime (ARCHITECTURE.md §7). No bare `*` action or resource and no wildcard
action in our statements, and no AWS managed policy on our roles: `tests/infra/test_least_privilege.py` checks every
synthesized template for both agent hosts. `<bucket>`, `<ledger>`, `<rejected>`, the machines and the runtime are
stack attributes, never typed names.

| Role | Stack | Actions | Resources |
|---|---|---|---|
| `summary`, `entity`, `rows` functions | ApiStack | `s3:GetObject` | `<bucket>/artefacts/*` |
| `ask` function | ApiStack | `s3:GetObject`; `states:StartSyncExecution` | `artefacts/*`; the ask machine |
| `publish` function | ApiStack | `s3:GetObject`; `states:StartExecution`; `dynamodb:GetItem` | `artefacts/*`; the publish machine; `<ledger>` |
| `approve` function | ApiStack | `s3:GetObject`; `states:SendTaskSuccess`, `states:SendTaskFailure`; `dynamodb:GetItem`, `dynamodb:UpdateItem` | `artefacts/*`; the publish machine; `<ledger>` |
| `check_budget`, `store_claims`, `retry_decision`, `record_rejection` | FlowStack | `dynamodb:GetItem`, `PutItem`, `UpdateItem`, `Query` | `<ledger>`, `<rejected>` |
| `run_orchestrator`, `judge_claim`, `write_answer` (only with `-c agent_host=lambda`) | FlowStack | the ledger actions above; `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`; `bedrock:ApplyGuardrail`; `s3:GetObject` | `<ledger>`, `<rejected>`; the two `eu.*` inference profiles and the 10 EU foundation-model ARNs they route to; the Guardrail; `artefacts/*` |
| agent shim (default, `agent_host=agentcore`) | FlowStack | `bedrock-agentcore:InvokeAgentRuntime` | the runtime and its `DEFAULT` endpoint |
| `store_task_token` | FlowStack | `dynamodb:GetItem`, `PutItem`, `UpdateItem` | `<ledger>` |
| `write_status_pack` | FlowStack | the three above; `s3:PutObject` (the only write) | `<ledger>`; `<bucket>/status-packs/*` |
| ask and publish state machines | FlowStack | `lambda:InvokeFunction` | their own step functions (and their versions) |
| AgentCore runtime | AgentStack | the agent steps' statements above; plus the L2 defaults: `logs:CreateLogGroup`, `logs:DescribeLogStreams`, `logs:CreateLogStream`, `logs:PutLogEvents`, `logs:DescribeLogGroups`; `bedrock-agentcore:GetWorkloadAccessToken`, `GetWorkloadAccessTokenForJWT`, `GetWorkloadAccessTokenForUserId`; `s3:GetObject*`, `s3:GetBucket*`, `s3:List*` | as above; `/aws/bedrock-agentcore/runtimes/*` log groups; the default workload-identity directory; the CDK asset bucket (its code zip) |
| every function above | all | `logs:CreateLogStream`, `logs:PutLogEvents` | its own log group |

**Actions with no resource-level permission** (AWS allows only `*`), allowed by the test: `xray:PutTraceSegments`,
`xray:PutTelemetryRecords`, `xray:GetSamplingRules`, `xray:GetSamplingTargets` (tracing); `logs:CreateLogDelivery`,
`GetLogDelivery`, `UpdateLogDelivery`, `DeleteLogDelivery`, `ListLogDeliveries`, `PutResourcePolicy`,
`DescribeResourcePolicies`, `DescribeLogGroups` (Step Functions logging); `cloudwatch:PutMetricData` (AgentCore, with a
`cloudwatch:namespace = bedrock-agentcore` condition).

**CDK's own deploy-time roles** (generated by CDK, run only during `cdk deploy`, reviewed here rather than rewritten):
the `BucketDeployment` handler (DataStack, WebStack), the S3 auto-delete provider, the custom-resource provider
framework, and the AgentCore runtime's read on the CDK asset bucket (to fetch its code zip).
```

- [ ] **Step 2: Check the table against the templates**
```bash
cd infra && env -u AWS_PROFILE -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q 2>&1 | grep -E "Successfully|rror"; cd ..
for stack in ApiStack FlowStack AgentStack; do python3 -c "
import json, sys
template = json.load(open('infra/cdk.out/$stack.template.json'))
actions = sorted({action for resource in template['Resources'].values() if resource['Type'] == 'AWS::IAM::Policy'
                  for statement in resource['Properties']['PolicyDocument']['Statement']
                  for action in (statement['Action'] if isinstance(statement['Action'], list) else [statement['Action']])})
print('$stack', actions)"; done
```
Expected: every action printed appears in the table (or in its "no resource-level permission" or CDK-framework paragraphs), and every action in the table appears in a template. Fix the table, never the stacks, for a mismatch here; a stack that grants something the table doesn't explain is a finding (Task 1 Step 4).

- [ ] **Step 3: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/README.md
git commit -m "docs(infra): the workload roles table, one role per function, state machine and runtime"
```
Expected: S + 6 passed (the doc guards in `tests/test_dependencies.py` and `tests/test_code_style.py` still pass).

**Task done when:** `infra/README.md` has the "Workload roles" section and Step 2's action lists are all explained by it.

### Task 3: Patrick's review (before clean-deploy check 1)

**Files:** none.

- [ ] **Step 1:** Send Patrick the branch, the table and the Review Focus list. Walk through it together; for Review Focus 1, run (read-only, verify in AWS):
```bash
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
for role in $(aws iam list-roles --query "Roles[?starts_with(RoleName, 'demo-ApiStack-Approve') || starts_with(RoleName, 'demo-FlowStack-AgentShim')].RoleName" --output text); do
  echo "$role"; for policy in $(aws iam list-role-policies --role-name "$role" --query PolicyNames --output text); do
    aws iam get-role-policy --role-name "$role" --policy-name "$policy" --query "PolicyDocument.Statement[].[Action, Resource]" --output json; done; done
```
Expected (verify in AWS): the `approve` role shows `states:SendTaskSuccess`/`SendTaskFailure` on the publish machine, `dynamodb:GetItem`/`UpdateItem` on the ledger, `s3:GetObject` on `artefacts/*`, its log-group actions and X-Ray; the shim role shows `bedrock-agentcore:InvokeAgentRuntime` on the runtime only, plus logs and X-Ray.
- [ ] **Step 2:** Record Patrick's verdict in the ledger and the PR ("reviewed by Patrick, <date time>, findings: …").

**Task done when:** Patrick's OK (or his findings with their fixes) is written in the PR before D1 18:00.

### Task 4: PR (after Yaw's and Patrick's OK)
- [ ] **Step 1:** `git diff origin/develop --stat` touches only `tests/infra/test_least_privilege.py` and `infra/README.md`.
- [ ] **Step 2:** Push `chore/iam-least-privilege`; PR to `develop` titled "Least privilege: template test for every role, and the roles table". Body: the exceptions and why, the findings and their fixing commits, Patrick's review line. No attribution lines.
- [ ] **Step 3:** Update [[Build order]].

**Task done when:** the PR is open to `develop` with green Jenkins; [[Build order]] shows Y4 `in review (PR #nn)`.

## Done means
- [ ] `uv run --locked pytest tests/infra/test_least_privilege.py --no-cov` → `6 passed` on the merged `develop`. *Verify:* run it.
- [ ] The test covers both hosts: `-vv` output shows no failure and the fixture builds `agentcore/…` and `lambda/…` (Review Focus 5). *Verify:* run with `-vv`.
- [ ] `infra/README.md` contains the "Workload roles" section and its actions match `infra/cdk.out/*.template.json` (Task 2 Step 2). *Verify:* the script output against the table.
- [ ] Patrick's review line is in the PR. *Verify:* the PR body.
- [ ] The PR is open (or merged); [[Build order]] row Y4 updated. *Verify:* the PR page.

## Never
- Add a fragment to `CDK_FRAMEWORK_FRAGMENTS` or an action to `ACTIONS_WITHOUT_RESOURCE_SCOPE` to make a finding go away; fix the role.
- Widen any statement to `*` (even "temporarily for the demo").
- Run anything but read-only `aws iam` calls in Task 3; push to `develop` or `main`; add attribution lines.

Related: [[Build order]], [[Yaw - DevOps]], [[Workstreams]]
