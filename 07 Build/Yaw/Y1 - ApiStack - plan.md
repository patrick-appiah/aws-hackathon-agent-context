---
tags: [build, plan, area/devops]
id: Y1
owner: Yaw
spec: "[[Y1 - ApiStack - spec]]"
status: ready
updated: 2026-10-14
---
# Y1: ApiStack (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it. Deploying and pushing are outward-facing: ask Yaw (and Patrick for the PR) first.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Y1 - ApiStack - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger.
3. [[Workstreams]] (`06 Workstreams/`): the architecture with owners, the code already built, the contracts and the rules (§7).
4. [[Yaw - DevOps]]: the owner's brief; and [[Michael - DevOps]] (the other half of DevOps).
5. [[Build order]]: what this item depends on and unblocks.
6. [[M2 - App, DataStack and LedgerStack - spec]]: the CDK app, `build_stacks`, the prefix, the test fixtures and the patterns every DevOps item follows.
7. [[M3b - AuthStack - spec]] and [[M4a - WebStack - spec]]; `docs/DEVOPS_HANDOVER.md` in the repo.

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Yaw (owner). Never invent a name, a shape or a rule.

**Goal:** `/api/*` reaches six Lambdas behind the Cognito JWT authorizer, stubs first, then Linus's handlers; every later Yaw item reuses the bundler and `PortalFunction` built here.

**Architecture:** new modules `infra/bundling.py` *(new)*, `infra/portal_function.py` *(new)*, `infra/functions/stub_handler.py` *(new)*, `infra/stacks/api_stack.py` *(new)*; `build_stacks` builds `ApiStack` after `AuthStack`. No AWS call anywhere in the tests.

**Tech stack:** Python 3.11, `aws-cdk-lib` 2.273+ (`aws_apigatewayv2`, `aws_apigatewayv2_authorizers`, `aws_apigatewayv2_integrations`, `aws_lambda`), CDK CLI 2.1144.0 (`infra/package.json` *(new)*), uv 0.9+, pytest.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your clone). **Branch:** `feature/infra-api` from an up-to-date `develop`, **after M2, M3a and M3b are merged** ([[Build order]]). Task 5 additionally needs Linus's L1 and L2 merged.
- **Start state:** `uv run --locked pytest` → all passed, `TOTAL` 96%. Write the count into the ledger as **S**. Every count below is **S + n**, with the dry-run value in brackets. (Dry-run: `feature/api-and-spine-contracts` + M2, with stand-ins for M3a's `GuardrailStack` and M3b's `AuthStack` that have the same attributes and no tests of their own, so S = 224. With the real M3a/M3b merged, S is higher by their test counts; the **n** must match exactly.)
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
1. **Audience is the app client ID, issuer is the pool URL** (no trailing slash): compare the deployed authorizer (`aws apigatewayv2 get-authorizers --api-id <id>`) with the `UserPoolClientId` and `IssuerUrl` outputs of AuthStack.
2. **The ID token, not the access token, is what the portal sends** (Clement's F3). An access token has no `aud`, so the authorizer would reject it: if `curl` with a token gives 401, check which token it is first.
3. **Every bundle carries the prompts:** after Task 5's synth, `ls infra/cdk.out/bundles/api/agents/prompts/` lists `critic.txt` and `prompts.lock` (and every other locked prompt).
4. **No role has a managed policy or a wildcard:** `grep -c ManagedPolicyArns infra/cdk.out/ApiStack.template.json` prints `0`.
5. **`auth_mode=none` is only ever a deliberate fallback:** the default synth shows `AuthMode = cognito`; nobody commits `auth_mode` into `cdk.json`.

---

### Task 1: The local bundler (`infra/bundling.py`)

**Files:**
- Create: `infra/bundling.py`, `tests/infra/test_bundling.py` *(new)*

**Produces:** `BUILD_DIRECTORY`, `LAMBDA_PYTHON_VERSION`, `LAMBDA_PYTHON_PLATFORM`, `CORE_CODE`, `PLACEHOLDER_DIRECTORY`, `BundleSpec`, `API_BUNDLE`, `install_requirements(bundle_directory, python_platform, requirements_file)`, `build_bundle(spec, *, repo_root, output_root, install) -> Path`, `bundle_path(scope, spec) -> str`, `bundle_code(scope, spec) -> lambda_.Code` (all in `infra.bundling`). **Consumes:** `config.REPO_ROOT`. **Consumed by:** Task 3, Y2a, Y2b, Y3a, Y3b.

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync --locked && (cd infra && npm ci)
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/infra-api
```
Expected: S passed (dry-run 224), `TOTAL ... 96%`. Write S into the ledger.

- [ ] **Step 2: Write the failing test.**
Create `tests/infra/test_bundling.py`:
```python
"""Lambda bundles (infra/bundling.py): our code with the locked prompts on top of the dependencies, no Docker."""
import pytest

from infra.bundling import API_BUNDLE, CORE_CODE, BundleSpec, build_bundle

PROMPT_FILE = "agents/prompts/critic.txt"
PROMPT_LOCK = "agents/prompts/prompts.lock"


def _fake_repo(tmp_path):
    repo = tmp_path / "repo"
    for file_path in ("tools/metrics.py", "adapters/csv_repo.py", PROMPT_FILE, PROMPT_LOCK, "agents/critic.py",
                      "agents/__pycache__/critic.cpython-311.pyc", "config.py", "api/handlers.py", "auth/scope.py",
                      "flow/publish.py", "infra/agent_runtime/server.py"):
        (repo / file_path).parent.mkdir(parents=True, exist_ok=True)
        (repo / file_path).write_text("# fake\n")
    return repo


def _record_install(calls):
    def install(bundle_directory, python_platform, requirements_file):
        calls.append((bundle_directory.name, python_platform, requirements_file.name))
        (bundle_directory / "pydantic").mkdir()
    return install


def test_the_bundle_holds_the_code_the_prompts_and_the_lock(tmp_path):
    calls = []
    bundle = build_bundle(API_BUNDLE, repo_root=_fake_repo(tmp_path), output_root=tmp_path / "build",
                          install=_record_install(calls))
    for expected in ("tools/metrics.py", "adapters/csv_repo.py", PROMPT_FILE, PROMPT_LOCK, "config.py",
                     "api/handlers.py", "auth/scope.py", "pydantic"):
        assert (bundle / expected).exists(), expected
    assert not (bundle / "agents" / "__pycache__").exists()
    assert calls == [("api", "x86_64-manylinux2014", "api-requirements.txt")]


def test_root_files_land_at_the_bundle_root(tmp_path):
    spec = BundleSpec("runtime", CORE_CODE, root_files=("infra/agent_runtime/server.py",))
    bundle = build_bundle(spec, repo_root=_fake_repo(tmp_path), output_root=tmp_path / "build",
                          install=_record_install([]))
    assert (bundle / "server.py").exists()


def test_a_rebuild_starts_from_an_empty_directory(tmp_path):
    repo, output_root = _fake_repo(tmp_path), tmp_path / "build"
    stale_file = output_root / "api" / "stale.py"
    stale_file.parent.mkdir(parents=True)
    stale_file.write_text("")
    build_bundle(API_BUNDLE, repo_root=repo, output_root=output_root, install=_record_install([]))
    assert not stale_file.exists()


def test_a_missing_package_stops_the_build_with_the_reason(tmp_path):
    spec = BundleSpec("flow", (*CORE_CODE, "flow", "evals"))
    with pytest.raises(FileNotFoundError, match="evals"):
        build_bundle(spec, repo_root=_fake_repo(tmp_path), output_root=tmp_path / "build",
                     install=_record_install([]))
```

- [ ] **Step 3: Run it and watch it fail**
```bash
uv run --locked pytest tests/infra/test_bundling.py --no-cov 2>&1 | grep -E "^E |error|passed|failed" | head -4
```
Expected: `E   ModuleNotFoundError: No module named 'infra.bundling'` and `1 error`.

- [ ] **Step 4: Implement.**
Create `infra/bundling.py`:
```python
"""Python bundles for the Lambdas and the agent runtime, built locally at synth time: no Docker (D-017).

A bundle is our code (the core, the adapters, the agents with their locked prompts, config.py and the handler
packages) plus the runtime dependencies from `uv export --no-dev`, installed for the target platform.
"""
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from aws_cdk import Stack
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

from config import REPO_ROOT

# Inside cdk.out: gitignored, and skipped by the style test and bandit like the rest of the synth output.
BUILD_DIRECTORY = REPO_ROOT / "infra" / "cdk.out" / "bundles"
LAMBDA_PYTHON_VERSION = "3.11"                      # .python-version; the Lambda runtime is PYTHON_3_11
LAMBDA_PYTHON_PLATFORM = "x86_64-manylinux2014"     # Lambda x86_64 on Amazon Linux 2
CORE_CODE = ("tools", "adapters", "agents", "config.py")  # agents/ carries prompts/*.txt and prompts.lock (D-014)
IGNORED_WHILE_COPYING = shutil.ignore_patterns("__pycache__", "*.pyc")
REQUIREMENTS_FILE_SUFFIX = "-requirements.txt"
PLACEHOLDER_HANDLER_CODE = "def handler(event, context):\n    raise RuntimeError('bundling was skipped')\n"
PLACEHOLDER_DIRECTORY = REPO_ROOT / "infra" / "functions"   # stands in for a bundle directory when bundling is skipped
UV_EXECUTABLE = "uv"


@dataclass(frozen=True)
class BundleSpec:
    """What goes into one bundle: repo-relative code paths, the platform, and extra files copied to its root."""
    name: str
    code_paths: tuple[str, ...]
    python_platform: str = LAMBDA_PYTHON_PLATFORM
    root_files: tuple[str, ...] = ()


API_BUNDLE = BundleSpec("api", (*CORE_CODE, "api", "auth"))


def install_requirements(bundle_directory: Path, python_platform: str, requirements_file: Path) -> None:
    """The locked runtime dependencies (never the dev or infra groups), as wheels for the target platform."""
    subprocess.run([UV_EXECUTABLE, "export", "--locked", "--no-dev", "--format", "requirements-txt", "--no-hashes",
                    "--quiet", "--output-file", str(requirements_file)], cwd=REPO_ROOT, check=True)
    subprocess.run([UV_EXECUTABLE, "pip", "install", "--quiet", "--target", str(bundle_directory),
                    "--python-platform", python_platform, "--python-version", LAMBDA_PYTHON_VERSION,
                    "--only-binary", ":all:", "--requirement", str(requirements_file)], cwd=REPO_ROOT, check=True)


def build_bundle(spec: BundleSpec, *, repo_root: Path = REPO_ROOT, output_root: Path = BUILD_DIRECTORY,
                 install: Callable[ [Path, str, Path], None] = install_requirements) -> Path:
    """A fresh bundle directory: dependencies first, then our code on top. A missing code path is an error."""
    missing = [code_path for code_path in (*spec.code_paths, *spec.root_files) if not (repo_root / code_path).exists()]
    if missing:
        raise FileNotFoundError(f"bundle {spec.name!r} needs {missing}: merge the item that builds them first")
    bundle_directory = output_root / spec.name
    shutil.rmtree(bundle_directory, ignore_errors=True)
    bundle_directory.mkdir(parents=True)
    install(bundle_directory, spec.python_platform, output_root / f"{spec.name}{REQUIREMENTS_FILE_SUFFIX}")
    for code_path in spec.code_paths:
        source = repo_root / code_path
        if source.is_dir():
            shutil.copytree(source, bundle_directory / code_path, ignore=IGNORED_WHILE_COPYING, dirs_exist_ok=True)
        else:
            shutil.copy2(source, bundle_directory / code_path)
    for root_file in spec.root_files:
        shutil.copy2(repo_root / root_file, bundle_directory / Path(root_file).name)
    return bundle_directory


def bundle_path(scope: Construct, spec: BundleSpec) -> str:
    """The built bundle's directory, or a small existing directory when this synth skips bundling (the tests)."""
    if not Stack.of(scope).bundling_required:
        return str(PLACEHOLDER_DIRECTORY)
    return str(build_bundle(spec))


def bundle_code(scope: Construct, spec: BundleSpec) -> lambda_.Code:
    """The bundle as Lambda code, or an inline placeholder when this synth skips bundling (the unit tests)."""
    if not Stack.of(scope).bundling_required:
        return lambda_.Code.from_inline(PLACEHOLDER_HANDLER_CODE)
    return lambda_.Code.from_asset(str(build_bundle(spec)))
```

- [ ] **Step 5: Run it**
```bash
uv run --locked pytest tests/infra/test_bundling.py --no-cov 2>&1 | tail -1
```
Expected: `4 passed`.

- [ ] **Step 6: Build one real bundle by hand** (network to PyPI, no AWS)
```bash
uv run --locked python -c "from infra.bundling import BundleSpec, CORE_CODE, build_bundle; print(build_bundle(BundleSpec('core-check', CORE_CODE)))"
ls infra/cdk.out/bundles/core-check/agents/prompts/; du -sh infra/cdk.out/bundles/core-check
git status --short infra/ && rm -rf infra/cdk.out/bundles/core-check
```
Expected: the path `.../infra/cdk.out/bundles/core-check`; `critic.txt  prompts.lock` (plus any prompt merged since); about `76M` (well under Lambda's 250 MB); `git status` shows only `infra/bundling.py` (the bundle is gitignored).

- [ ] **Step 7: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/bundling.py tests/infra/test_bundling.py
git commit -m "infra: local Lambda bundler from uv export, with the locked prompts, no Docker"
```
Expected: S + 4 passed [228], `TOTAL ... 96%`.

**Task done when:**
- `tests/infra/test_bundling.py` → 4 passed; the full suite is at S + 4.
- A hand-built bundle contains `agents/prompts/prompts.lock` and is not tracked by git.

### Task 2: `PortalFunction` and the stub handler

**Files:**
- Create: `infra/portal_function.py`, `infra/functions/stub_handler.py`, `tests/infra/functions/test_stub_handler.py` *(new)*

**Produces:** `PortalFunction` (`.function`, `.role`, `.log_group`), `DEFAULT_MEMORY_MEGABYTES`, `DEFAULT_TIMEOUT`, `LOG_WRITE_ACTIONS` (in `infra.portal_function`); `infra.functions.stub_handler.handler(event, context) -> dict`. **Consumes:** `infra.constants.LOG_RETENTION` (M2). **Consumed by:** Task 3, Y2a, Y2b, Y3b.

- [ ] **Step 1: Write the failing test.**
Create `tests/infra/functions/test_stub_handler.py`:
```python
"""The stub every route serves until api/handlers.py lands: it echoes the route and the JWT claims it received."""
import json

from infra.functions.stub_handler import handler

E4_LEAD_CLAIMS = {"cognito:groups": "[entity_lead]", "custom:entity_ids": "E4", "custom:tenant_id": "t-01"}


def test_the_stub_echoes_the_route_and_the_claims():
    event = {"routeKey": "GET /summary", "requestContext": {"authorizer": {"jwt": {"claims": E4_LEAD_CLAIMS}}}}
    response = handler(event, None)
    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"stub": True, "route": "GET /summary", "claims": E4_LEAD_CLAIMS}


def test_the_stub_answers_without_an_authorizer_too():
    assert json.loads(handler({"routeKey": "GET /rows"}, None)["body"])["claims"] == {}
```

- [ ] **Step 2: Run it and watch it fail**
```bash
uv run --locked pytest tests/infra/functions/test_stub_handler.py --no-cov 2>&1 | grep -E "^E |error|passed|failed" | head -4
```
Expected: `E   ModuleNotFoundError: No module named 'infra.functions'` and `1 error`.

- [ ] **Step 3: Implement both.** (`PortalFunction` is exercised through ApiStack's tests in Task 3.)
Create `infra/functions/stub_handler.py`:
```python
"""Stand-in for every API route until Linus's api/handlers.py is merged (Y1): proves the path, the authorizer
and the claims end to end. Returns the route and the JWT claims API Gateway passed, nothing else."""
import json

HTTP_OK = 200
JSON_CONTENT_TYPE = {"content-type": "application/json"}


def handler(event, context):
    authorizer = event.get("requestContext", {}).get("authorizer", {})
    claims = authorizer.get("jwt", {}).get("claims", {})
    body = {"stub": True, "route": event.get("routeKey"), "claims": claims}
    return {"statusCode": HTTP_OK, "headers": JSON_CONTENT_TYPE, "body": json.dumps(body)}
```

Create `infra/portal_function.py`:
```python
"""One Lambda the way every portal function is built: its own role, its own log group, tracing on (ARCHITECTURE §7).

The role starts empty (no AWSLambdaBasicExecutionRole, whose logs actions are on every resource) and gets exactly
the statements the caller passes, plus write access to its own log group.
"""
from aws_cdk import Duration, RemovalPolicy
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from constructs import Construct

from infra.constants import LOG_RETENTION

LAMBDA_SERVICE_PRINCIPAL = "lambda.amazonaws.com"
DEFAULT_MEMORY_MEGABYTES = 512
DEFAULT_TIMEOUT = Duration.seconds(29)        # API Gateway's own integration limit
LOG_WRITE_ACTIONS = ["logs:CreateLogStream", "logs:PutLogEvents"]


class PortalFunction(Construct):
    def __init__(self, scope: Construct, construct_id: str, *, handler: str, code: lambda_.Code,
                 environment: dict[str, str], statements: list[iam.PolicyStatement],
                 timeout: Duration = DEFAULT_TIMEOUT, memory_megabytes: int = DEFAULT_MEMORY_MEGABYTES) -> None:
        super().__init__(scope, construct_id)
        self.log_group = logs.LogGroup(self, "Logs", retention=LOG_RETENTION, removal_policy=RemovalPolicy.DESTROY)
        self.role = iam.Role(self, "Role", assumed_by=iam.ServicePrincipal(LAMBDA_SERVICE_PRINCIPAL))
        self.role.add_to_policy(iam.PolicyStatement(actions=LOG_WRITE_ACTIONS,
                                                    resources=[self.log_group.log_group_arn]))
        for statement in statements:
            self.role.add_to_policy(statement)
        self.function = lambda_.Function(
            self, "Function",
            runtime=lambda_.Runtime.PYTHON_3_11,
            architecture=lambda_.Architecture.X86_64,
            handler=handler,
            code=code,
            environment=environment,
            role=self.role,
            log_group=self.log_group,
            timeout=timeout,
            memory_size=memory_megabytes,
            tracing=lambda_.Tracing.ACTIVE,
        )
```

- [ ] **Step 4: Run it**
```bash
uv run --locked pytest tests/infra/functions/test_stub_handler.py --no-cov 2>&1 | tail -1
```
Expected: `2 passed`.

- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/portal_function.py infra/functions/stub_handler.py tests/infra/functions/test_stub_handler.py
git commit -m "infra: PortalFunction (own role, own log group, X-Ray) and the route stub"
```
Expected: S + 6 passed [230].

**Task done when:**
- `tests/infra/functions/test_stub_handler.py` → 2 passed; the full suite is at S + 6.

### Task 3: `ApiStack` with six stub routes behind the JWT authorizer

**Files:**
- Create: `infra/stacks/api_stack.py`, `tests/infra/stacks/test_api_stack.py` *(new)*
- Modify: `tests/infra/conftest.py` *(new)* (append `stacks_with_context`), `infra/app.py` *(new)*

**Produces:** `ApiStack(scope, construct_id, *, data, auth, **kwargs)` with `.http_api`, `.api_stage`, `.functions`, `.auth_mode`; outputs `ApiUrl`, `AuthMode`; `API_ROUTES`, `ApiRoute`, `ROUTES_WITH_REAL_HANDLERS`, `STUB_HANDLER`, `REAL_HANDLER_MODULE`, `AUTH_MODE_CONTEXT_KEY`, `auth_mode_from_context`; `PortalStacks.api`; the `stacks_with_context` fixture. **Consumes:** `DataStack.artefacts_uri`, `DataStack.artefacts_read_statement()` (M2), `AuthStack.issuer_url`, `AuthStack.user_pool_client` (M3b), `config.AUTH_MODE_COGNITO`, `AUTH_MODES`, `DEFAULT_ARTEFACT_BACKEND`, `DEFAULT_TENANT_ID` (C1). **Consumed by:** M4a (`api.http_api`), M4b, Y2a, Y2b, L6 (the `ApiUrl`).

- [ ] **Step 1: Write the failing tests.**
Append to `tests/infra/conftest.py` (keep everything already there):
```python


@pytest.fixture(scope="module")
def stacks_with_context(request):
    """build_stacks with extra context (for example -c auth_mode=none), built like portal_stacks. Once M4a adds
    the `web_build_directory` fixture, its stand-in portal build is passed too."""
    try:
        build_options = {"web_build_directory": request.getfixturevalue("web_build_directory")}
    except pytest.FixtureLookupError:
        build_options = {}

    def build(extra_context: dict):
        context = {STACK_PREFIX_CONTEXT_KEY: TEST_PREFIX, **SKIP_ALL_BUNDLING, **extra_context}
        return build_stacks(cdk.App(context=context), **build_options)
    return build
```

Create `tests/infra/stacks/test_api_stack.py`:
```python
"""ApiStack: an HTTP API (v2) whose only stage is `api`, six routes behind the Cognito JWT authorizer, one Lambda
and one least-privilege role per route."""
import pytest
from aws_cdk.assertions import Match, Template

from infra.stacks.api_stack import (API_ROUTES, AUTH_MODE_CONTEXT_KEY, ROUTES_WITH_REAL_HANDLERS, STUB_HANDLER,
                                    auth_mode_from_context)

EXPECTED_ROUTE_KEYS = {"GET /summary", "GET /entity/{id}", "GET /rows", "POST /ask", "POST /publish", "POST /approve"}


@pytest.fixture(scope="module")
def api_template(portal_stacks) -> Template:
    return Template.from_stack(portal_stacks.api)


def _route_keys(template: Template) -> set[str]:
    return {route["Properties"]["RouteKey"] for route in template.find_resources("AWS::ApiGatewayV2::Route").values()}


def test_it_is_an_http_api_with_one_stage_named_api(api_template):
    api_template.has_resource_properties("AWS::ApiGatewayV2::Api", {"ProtocolType": "HTTP"})
    api_template.resource_count_is("AWS::ApiGatewayV2::Stage", 1)
    api_template.has_resource_properties("AWS::ApiGatewayV2::Stage", {"StageName": "api", "AutoDeploy": True})


def test_the_six_routes_exist(api_template):
    assert _route_keys(api_template) == EXPECTED_ROUTE_KEYS


def test_every_route_needs_a_cognito_jwt(api_template):
    api_template.has_resource_properties("AWS::ApiGatewayV2::Authorizer", {
        "AuthorizerType": "JWT",
        "IdentitySource": ["$request.header.Authorization"],
        "JwtConfiguration": {"Audience": [Match.any_value()], "Issuer": Match.any_value()},
    })
    for route in api_template.find_resources("AWS::ApiGatewayV2::Route").values():
        assert route["Properties"]["AuthorizationType"] == "JWT"


def test_one_function_and_one_role_per_route(api_template):
    api_template.resource_count_is("AWS::Lambda::Function", len(API_ROUTES))
    api_template.resource_count_is("AWS::IAM::Role", len(API_ROUTES))
    for role in api_template.find_resources("AWS::IAM::Role").values():
        assert "ManagedPolicyArns" not in role["Properties"]


def test_functions_are_traced_python_3_11_with_the_data_settings(api_template):
    api_template.has_resource_properties("AWS::Lambda::Function", {
        "Runtime": "python3.11",
        "TracingConfig": {"Mode": "Active"},
        "Environment": {"Variables": {"ARTEFACT_BACKEND": "csv", "AUTH_MODE": "cognito", "DEFAULT_TENANT_ID": "t-01",
                                      "ARTEFACTS_URI": Match.any_value()}},
    })


def test_every_function_logs_to_its_own_group_with_retention_and_destroy(api_template):
    log_groups = api_template.find_resources("AWS::Logs::LogGroup")
    assert len(log_groups) == len(API_ROUTES)
    for log_group in log_groups.values():
        assert log_group["Properties"]["RetentionInDays"] == 14 and log_group["DeletionPolicy"] == "Delete"


def test_the_api_url_is_an_output(api_template):
    assert "ApiUrl" in api_template.find_outputs("*")


def test_auth_mode_none_drops_the_authorizer(stacks_with_context):
    template = Template.from_stack(stacks_with_context({AUTH_MODE_CONTEXT_KEY: "none"}).api)
    template.resource_count_is("AWS::ApiGatewayV2::Authorizer", 0)
    template.has_resource_properties("AWS::Lambda::Function", {"Environment": {"Variables": {"AUTH_MODE": "none"}}})


def test_a_mistyped_auth_mode_fails_the_synth():
    with pytest.raises(ValueError, match="auth_mode"):
        auth_mode_from_context("cognitoo")


def test_merged_routes_run_api_handlers_and_the_rest_the_stub(api_template):
    handlers = {function["Properties"]["Handler"]
                for function in api_template.find_resources("AWS::Lambda::Function").values()}
    expected_real = {f"api.handlers.{route_name}" for route_name in ROUTES_WITH_REAL_HANDLERS}
    assert expected_real <= handlers
    assert (STUB_HANDLER in handlers) == (len(ROUTES_WITH_REAL_HANDLERS) < len(API_ROUTES))
```

- [ ] **Step 2: Run them and watch them fail**
```bash
uv run --locked pytest tests/infra/stacks/test_api_stack.py --no-cov 2>&1 | grep -E "^E |error|passed|failed" | head -4
```
Expected: `E   ModuleNotFoundError: No module named 'infra.stacks.api_stack'` and `1 error`.

- [ ] **Step 3: Implement the stack, with every route on the stub** (`ROUTES_WITH_REAL_HANDLERS` empty; Task 5 fills it).
Create `infra/stacks/api_stack.py`:
```python
"""ApiStack: the HTTP API (v2) with the Cognito JWT authorizer and the six routes, one Lambda each.

The API has no default stage: its one stage is named `api`, so CloudFront's /api/* behaviour (M4a) reaches
`GET /summary` as /api/summary with no rewriting. Scope comes from the token claims, in the handler (D-010).
"""
from dataclasses import dataclass

from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_apigatewayv2 as apigateway
from aws_cdk import aws_apigatewayv2_authorizers as authorizers
from aws_cdk import aws_apigatewayv2_integrations as integrations
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

from config import AUTH_MODE_COGNITO, AUTH_MODES, DEFAULT_ARTEFACT_BACKEND, DEFAULT_TENANT_ID, REPO_ROOT
from infra.bundling import API_BUNDLE, bundle_code
from infra.constants import API_BASE_PATH
from infra.portal_function import PortalFunction
from infra.stacks.auth_stack import AuthStack
from infra.stacks.data_stack import DataStack

AUTH_MODE_CONTEXT_KEY = "auth_mode"            # -c auth_mode=none: the D2 12:00 Cognito fallback (no authorizer)
STUB_HANDLER = "stub_handler.handler"
REAL_HANDLER_MODULE = "api.handlers"
# Routes whose real handler is merged (Linus: L1 summary, L2 entity + rows, L3 ask + publish + approve).
# The others keep serving the stub. Add a route here only after its handler is on develop.
ROUTES_WITH_REAL_HANDLERS: frozenset[str] = frozenset()
STUB_CODE_DIRECTORY = REPO_ROOT / "infra" / "functions"


@dataclass(frozen=True)
class ApiRoute:
    name: str                       # the handler function in api/handlers.py and the Lambda's construct ID
    method: apigateway.HttpMethod
    path: str


API_ROUTES = (
    ApiRoute("summary", apigateway.HttpMethod.GET, "/summary"),
    ApiRoute("entity", apigateway.HttpMethod.GET, "/entity/{id}"),
    ApiRoute("rows", apigateway.HttpMethod.GET, "/rows"),
    ApiRoute("ask", apigateway.HttpMethod.POST, "/ask"),
    ApiRoute("publish", apigateway.HttpMethod.POST, "/publish"),
    ApiRoute("approve", apigateway.HttpMethod.POST, "/approve"),
)


def auth_mode_from_context(context_value: object) -> str:
    """`cognito` unless told otherwise; a typo fails the synth, never silently drops the authorizer."""
    auth_mode = AUTH_MODE_COGNITO if context_value is None else str(context_value)
    if auth_mode not in AUTH_MODES:
        raise ValueError(f"auth_mode must be one of {AUTH_MODES}, not {auth_mode!r}")
    return auth_mode


class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, data: DataStack, auth: AuthStack,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.auth_mode = auth_mode_from_context(self.node.try_get_context(AUTH_MODE_CONTEXT_KEY))
        self.http_api = apigateway.HttpApi(self, "HttpApi", create_default_stage=False)
        self.api_stage = apigateway.HttpStage(self, "ApiStage", http_api=self.http_api, stage_name=API_BASE_PATH,
                                              auto_deploy=True)
        authorizer = (authorizers.HttpJwtAuthorizer(
            "CognitoAuthorizer", auth.issuer_url, jwt_audience=[auth.user_pool_client.user_pool_client_id])
            if self.auth_mode == AUTH_MODE_COGNITO else apigateway.HttpNoneAuthorizer())
        base_environment = {
            "ARTEFACT_BACKEND": DEFAULT_ARTEFACT_BACKEND,
            "ARTEFACTS_URI": data.artefacts_uri,
            "AUTH_MODE": self.auth_mode,
            "DEFAULT_TENANT_ID": DEFAULT_TENANT_ID,
        }
        stub_code = lambda_.Code.from_asset(str(STUB_CODE_DIRECTORY))
        api_code = bundle_code(self, API_BUNDLE) if ROUTES_WITH_REAL_HANDLERS else stub_code
        self.functions: dict[str, PortalFunction] = {}
        for route in API_ROUTES:
            is_real = route.name in ROUTES_WITH_REAL_HANDLERS
            portal_function = PortalFunction(
                self, f"{route.name.capitalize()}Function",
                handler=f"{REAL_HANDLER_MODULE}.{route.name}" if is_real else STUB_HANDLER,
                code=api_code if is_real else stub_code,
                environment=base_environment,
                statements=self._statements_for(route, data),
            )
            self.functions[route.name] = portal_function
            self.http_api.add_routes(
                path=route.path, methods=[route.method], authorizer=authorizer,
                integration=integrations.HttpLambdaIntegration(f"{route.name.capitalize()}Integration",
                                                               portal_function.function))
        CfnOutput(self, "ApiUrl", value=f"{self.http_api.api_endpoint}/{API_BASE_PATH}")
        CfnOutput(self, "AuthMode", value=self.auth_mode)

    @staticmethod
    def _statements_for(route: ApiRoute, data: DataStack) -> list[iam.PolicyStatement]:
        """Every route reads artefacts/ (scope checks and figures). Later items add the flow permissions."""
        return [data.artefacts_read_statement()]
```

- [ ] **Step 4: Build it in the app.** In `infra/app.py`:
  - add `from infra.stacks.api_stack import ApiStack` as the first `infra.stacks` import (alphabetical);
  - add the field `api: ApiStack` after `auth: AuthStack` in `PortalStacks`;
  - directly after the `auth = AuthStack(...)` statement, add:
```python
    api = ApiStack(app, "ApiStack", data=data, auth=auth, **stack_options("ApiStack"))
```
  - add `api=api` to the `PortalStacks(...)` call in the `return` (wrap the line under 120 characters).

- [ ] **Step 5: Run the tests**
```bash
uv run --locked pytest tests/infra/stacks/test_api_stack.py --no-cov 2>&1 | tail -1
```
Expected: `10 passed`.

- [ ] **Step 6: Full suite, synth with no credentials, commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/stacks/api_stack.py infra/app.py tests/infra/conftest.py tests/infra/stacks/test_api_stack.py
git commit -m "infra: ApiStack, HTTP API with the Cognito JWT authorizer and six stub routes on the api stage"
```
```bash
cd infra && env -u AWS_PROFILE -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q 2>&1 | grep -E "Successfully|rror"; cd ..
ls infra/cdk.out | grep -c template.json
```
Expected: S + 16 passed [240], `TOTAL ... 96%`; `Successfully synthesized`; the template count includes `ApiStack.template.json` (dry-run with stand-ins: 5).

**Task done when:**
- The full suite is at S + 16 with 96%.
- `npx cdk synth -q` with no credentials writes `infra/cdk.out/ApiStack.template.json` *(new)* containing six `AWS::ApiGatewayV2::Route` resources (`grep -c '"AWS::ApiGatewayV2::Route"' infra/cdk.out/ApiStack.template.json` → `6`).

### Task 4: Deploy the stubs and prove the authorizer (verify in AWS; ask Yaw first)

**Files:** none (deploy and checks only).

**Produces:** `demo-ApiStack` deployed; the `ApiUrl` for Michael (M4a) and Linus. **Consumes:** deployed `demo-AuthStack` (M3b) and a test user's password from Patrick (never written down).

- [ ] **Step 1: Deploy.** The CDK CLI selects stacks by their construct ID (`ApiStack`), not the CloudFormation name (`demo-ApiStack`); `npx cdk list` shows both.
```bash
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
cd infra && npx cdk deploy ApiStack --require-approval never 2>&1 | tail -4; cd ..
```
Expected (verify in AWS): `✅  ApiStack (demo-ApiStack)` and the outputs `ApiUrl = https://<id>.execute-api.eu-west-1.amazonaws.com/api`, `AuthMode = cognito`.

- [ ] **Step 2: No token → 401**
```bash
API_URL=$(aws cloudformation describe-stacks --stack-name demo-ApiStack --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text)
curl -s -o /dev/null -w "%{http_code}\n" "$API_URL/summary"
```
Expected (verify in AWS): `401`.

- [ ] **Step 3: The E4 lead's ID token → 200 with the claims.** Get an ID token for the E4 lead (Abdul's test user; the password comes from Patrick, typed at the prompt, never saved): sign in through the portal's managed login, or ask Michael for the `aws cognito-idp admin-initiate-auth` command his M3b plan documents. Then:
```bash
read -rs ID_TOKEN   # paste the token; it is not echoed or saved
curl -s -H "Authorization: Bearer $ID_TOKEN" "$API_URL/summary"; echo; unset ID_TOKEN
```
Expected (verify in AWS): `{"stub": true, "route": "GET /summary", "claims": {... "cognito:groups": "[entity_lead]", "custom:entity_ids": "E4", "custom:tenant_id": "t-01" ...}}`. Copy the line into the ledger **without** the token.

**Task done when:**
- `curl` without a token returns `401`, and with the E4 lead's ID token returns the stub body with `custom:entity_ids` `E4` (ledger lines).
- `ApiUrl` is posted to Michael and Linus.

### Task 5: Switch `/summary`, `/entity`, `/rows` to Linus's handlers (after L1 and L2 are merged)

**Files:**
- Modify: `infra/stacks/api_stack.py`

**Produces:** the three dashboard routes on `api.handlers.*`, bundled with `API_BUNDLE`. **Consumes:** `api/handlers.py` *(new)* `summary`, `entity`, `rows` and `auth/` (Linus).

- [ ] **Step 1: Bring in the handlers.** Check [[Build order]]: L1 and L2 are `merged`. Then:
```bash
git fetch origin && git rebase origin/develop
grep -n "^def summary\|^def entity\|^def rows" api/handlers.py; ls auth/
```
Expected: three `def` lines and `scope.py` (at least). If any is missing, stop and ask Linus.

- [ ] **Step 2: Switch the routes.**
In `infra/stacks/api_stack.py`, replace exactly:
```python
ROUTES_WITH_REAL_HANDLERS: frozenset[str] = frozenset()
```
with:
```python
ROUTES_WITH_REAL_HANDLERS = frozenset({"summary", "entity", "rows"})
```

- [ ] **Step 3: Tests, then a real synth (this one bundles)**
```bash
uv run --locked pytest tests/infra/stacks/test_api_stack.py --no-cov 2>&1 | tail -1
```
```bash
cd infra && env -u AWS_PROFILE -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q 2>&1 | grep -E "Successfully|rror"; cd ..
ls infra/cdk.out/bundles/api/api/handlers.py infra/cdk.out/bundles/api/agents/prompts/prompts.lock
```
Expected: `10 passed` (`test_merged_routes_run_api_handlers_and_the_rest_the_stub` now sees three real handlers); `Successfully synthesized`; both files listed. (Dry-run note: `api/`, `auth/` and `flow/` didn't exist when this plan was written, so its synth was dry-run with empty stand-in packages; on `develop` they are the real ones.)

- [ ] **Step 4: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/stacks/api_stack.py
git commit -m "infra: dashboard routes run Linus's handlers from the uv-built bundle"
```
Expected: S + 16 passed (plus Linus's own tests from the rebase), `TOTAL` not below 96%.

- [ ] **Step 5: Redeploy and check the summary (verify in AWS; ask Yaw first)**
```bash
cd infra && npx cdk deploy ApiStack --require-approval never 2>&1 | tail -2; cd ..
read -rs ID_TOKEN; curl -s -H "Authorization: Bearer $ID_TOKEN" "$API_URL/summary" | head -c 300; echo; unset ID_TOKEN
```
Expected (verify in AWS): the CFO's token returns JSON starting `{"as_of": ...` with `"tenant_id": "t-01"` (the `SummaryResponse` keys from `tools/api_schema.py`); the E4 lead's token on `$API_URL/entity/E2` returns `403` with `{"error": "out_of_scope", ...}`.

**Task done when:**
- `infra/cdk.out/bundles/api/` *(new)* holds `api/handlers.py`, `auth/` and `agents/prompts/prompts.lock` after a synth.
- The deployed `/summary` returns the real summary for the CFO and `/entity/E2` returns 403 for the E4 lead (ledger lines).

### Task 6: Review, then PR (after Yaw's and Patrick's OK)
- [ ] **Step 1:** Work through the Review Focus by hand; write each result in the ledger.
- [ ] **Step 2:** `git diff origin/develop --stat` touches only `infra/` and `tests/infra/`. Expected: the files named in Tasks 1–5, nothing else.
- [ ] **Step 3:** Push `feature/infra-api` and open the PR to `develop`, titled "ApiStack: HTTP API with the Cognito JWT authorizer, six routes, local bundler". Body: the routes table (spec §3), the test count (S + 16), the deployed checks (401 / 200 / 403), the rulings. No attribution lines.
- [ ] **Step 4:** Tell Michael (M4a can wire `/api/*`) and Linus (the `ApiUrl`; the ask, publish and approve routes switch in Y2a/Y2b once L3 lands). Update [[Build order]] (`in review (PR #nn)`).

**Task done when:** the PR is open to `develop` with green Jenkins, and [[Build order]] shows Y1 `in review (PR #nn)`.

## Done means
- [ ] `uv run --locked pytest` on the branch → S + 16 passed, `TOTAL` ≥ 96%. *Verify:* run it; compare with the ledger's S.
- [ ] `npx cdk synth -q` with credentials unset succeeds, and `grep -c '"AWS::ApiGatewayV2::Route"' infra/cdk.out/ApiStack.template.json` prints `6`. *Verify:* run both.
- [ ] `grep -c ManagedPolicyArns infra/cdk.out/ApiStack.template.json` prints `0`. *Verify:* run it after the synth.
- [ ] After Task 5's synth, `infra/cdk.out/bundles/api/agents/prompts/prompts.lock` *(new)* exists. *Verify:* `ls` it.
- [ ] Deployed: `curl "$API_URL/summary"` → `401`; with the CFO's ID token → summary JSON; with the E4 lead's token, `/entity/E2` → `403`. *Verify in AWS:* the three ledger lines (no tokens in them).
- [ ] The PR to `develop` is open with a green Jenkins check; [[Build order]] row Y1 says `in review (PR #nn)` or `merged`. *Verify:* the PR page.

## Never
- Commit or paste an ID token, a password or an `.npmrc` token anywhere (ledger, PR, Slack).
- Use `bucket.grant_read`, `grant_read_write` or a role with `AWSLambdaBasicExecutionRole`: build every function with `PortalFunction`.
- Put `auth_mode` into `cdk.json` or deploy `-c auth_mode=none` without Patrick's go/no-go call.
- Point a route at `api.handlers.<name>` before that handler is merged.
- Run `cdk deploy` or any `aws` command before Yaw's OK; push to `develop` or `main`; add attribution lines.

Related: [[Build order]], [[Yaw - DevOps]], [[Workstreams]]
