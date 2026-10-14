---
tags: [build, plan, area/devops]
id: M4a
owner: Michael
spec: "[[M4a - WebStack - spec]]"
status: ready
updated: 2026-10-14
---
# M4a: WebStack (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it. Deploying (Task 5) and pushing are outward-facing: ask Michael first. **Task 4 needs Yaw's Y1 merged:** do Tasks 1–3 any time after M3b, then wait for Y1.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]]: the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[M4a - WebStack - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger.
3. [[M2 - App, DataStack and LedgerStack - spec]], [[M3b - AuthStack - spec]], [[Y1 - ApiStack - spec]]; [[Michael - DevOps]], [[Clement - front end]], [[Mildred - front end]].
4. [[2026-10-13 Front end]], [[2026-10-13 Scope from the token, enforced twice]] and [[Working with AI assistants]].
5. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Michael (or Yaw for the API, Clement for sign-in).

**Goal:** the Angular portal served from CloudFront with `/api/*` passed to the HTTP API (token forwarded, nothing cached, API errors untouched), a generated `portal-config.json`, and the CloudFront URL added to the Cognito client's callback URLs; unit-tested, synthesised without credentials, deployed and checked end to end.

**Architecture:** `infra/stacks/web_stack.py` *(new)* builds the site bucket, the distribution (S3 origin with origin access control + an SPA-rewrite CloudFront Function on the default behaviour; an HTTP origin for `/api/*`), the upload, and a custom resource. The custom resource's Python handler (`infra/functions/portal_callback.py` *(new)*) is pure logic around two boto3 calls and is unit-tested with a fake client; the CloudFront Function (`infra/functions/spa_rewrite.js`) is tested by running it in Node. `build_stacks` passes the build folder in, so tests use a temporary one.

**Tech stack:** Python 3.11, `aws-cdk-lib` 2.273+ (`aws_cloudfront`, `aws_cloudfront_origins`, `aws_s3_deployment`, `custom_resources`, `aws_lambda`), Node 22 (CloudFront Functions JS 2.0 and jsii), CDK CLI 2.1144.0, pytest, uv; yarn for the web build.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your clone). **Branch:** `feature/infra-web` from an up-to-date `develop`, **after M3b is merged**; Task 4 **after Y1 is merged** (`git pull --rebase origin develop` on your branch then).
- **Start state:** `uv run --locked pytest` → record the count in the ledger as **S**; `TOTAL` 96%. With C1, M1, M2, M3a, M3b merged and Y1 not yet merged, S = **235**. Every count below is given as S + n and, in brackets, the dry-run value from S = 235. (Dry-run: measured on `feature/api-and-spine-contracts` + M2 + M3a + M3b, with a stand-in `ApiStack` that has only `http_api` and no tests of its own; with the real Y1 merged, S includes Y1's tests.)
- `eu-west-1` only (`config.DEFAULT_REGION`); Bedrock `eu.*` inference profiles only; synthetic data only; **no secrets anywhere: no tokens or passwords in code, files, the PR, the ledger or Slack.**
- Settings only in `config.py`; domain constants only in `tools/constants.py`; deploy-time constants only in `infra/constants.py` *(new)*; descriptive names; **no single-character names** (the style test scans `infra/`, including `infra/functions/` *(new)*); no magic numbers or strings. The core (`tools/`) imports no boto3, Strands, adapters, config or os, and never imports `infra`.
- **`RemovalPolicy.DESTROY` on every resource; the site bucket also `auto_delete_objects=True`; log groups use `LOG_RETENTION`.** Outputs or attributes for every name another stack or person needs.
- Agents reach data only through `tools/agent_tools.py`; scope is never a tool argument; prompts only in `agents/prompts/<agent>.txt` (nothing here touches them).
- Never weaken a security rule (scope gate, create-once ledger, fail-closed critic, escaping) to pass a test. **Never add custom error responses to the distribution, never cache `/api/*`, never drop a client setting in the callback merge.**
- Tests in `tests/`, mirroring the code; `uv run --locked pytest` from the repo root; coverage must not drop (96%).
- Deploys are manual (D-018); CI builds and tests only. `export AWS_PROFILE=hackathon AWS_REGION=eu-west-1` before any `aws` or `cdk deploy` command.
- PR to `develop`; Patrick merges; never push to `develop` or `main`; **no `Co-Authored-By` and no "Generated with" lines**.
- Stay in DevOps's files: `infra/` (not Linus's `api.py` and `scope.py` or Huvison's `steps`, `spine`, `local`, `states` and `publish` modules in `infra/functions/`), `tests/infra/` *(new)* (not `tests/infra/functions/` *(new)*). The web build is read, never changed.
- No layout or "meta" guard tests.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **The API's errors survive CloudFront (verify in AWS):** Task 5 Step 7 returns `403` with a JSON `{"error": ...}` body, not HTML. If you see HTML, someone added an error page: remove it.
2. **The token reaches the authorizer through CloudFront (verify in AWS):** Task 5 Steps 5 and 6: `401` without, `200` with the CFO's ID token. A `401` with a valid token means `Authorization` was stripped: check the origin request policy.
3. **The callback merge kept the client's security settings (verify in AWS):** after Task 5, `WriteAttributes` is still `["name"]` and the auth flows are unchanged (Step 4).
4. **Re-running the callback merge:** if AuthStack's client is ever changed and redeployed, CloudFormation resets its callback URLs to `http://localhost:4200`. Then bump `PORTAL_CALLBACK_REVISION` and redeploy WebStack. Note this in the PR so M5's runbook carries it.
5. **`portal-config.json` matches the outputs** and holds no secret (only IDs and URLs). Tell Clement and Mildred it exists (spec assumption).
6. **The callback handler's role (known Y4 finding):** a plain `lambda_.Function` gets the AWS-managed `AWSLambdaBasicExecutionRole` (log actions on `*`), which [[Y4 - IAM least-privilege review - spec]]'s template check rejects. If Y1's `PortalFunction` (`infra/portal_function.py` *(new)*) is on `develop` when you reach the WebStack task, build the handler with it instead, exactly as Y4 Task 1 Step 4 shows, and record a `Ruling:`; otherwise Y4 raises it with you after merge.

---

### Task 1: The callback merge function (`infra/functions/portal_callback.py`)

**Files:**
- Create: `infra/functions/__init__.py` *(new)*, `infra/functions/portal_callback.py`, `tests/infra/functions/test_portal_callback.py` *(new)*

**Produces:** `infra.functions.FUNCTIONS_DIRECTORY`, `PORTAL_CALLBACK_SOURCE`, `SPA_REWRITE_SOURCE`; `infra.functions.portal_callback.merged_client_settings(described_client: dict, portal_urls: list[str]) -> dict`, `on_event(event: dict, context: object, cognito_client=None) -> dict`, `URL_LIST_FIELDS`, `UPDATABLE_CLIENT_FIELDS`. **Consumed by:** Task 3 (`WebStack` inlines the file as a Lambda).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync --locked && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/infra-web
mkdir -p .superpowers && printf '# Ledger: M4a WebStack\nS = <the count above>\n' > .superpowers/ledger-M4a.md
cd infra && npm ci && cd ..
```
Expected: S passed (235 if Y1 isn't merged yet), `TOTAL ... 96%`. Write S into the ledger.

- [ ] **Step 2: Write the failing tests.** Create `tests/infra/functions/test_portal_callback.py`:
```python
"""The portal-callback custom resource (infra/functions/portal_callback.py): it adds the CloudFront URL to the
Cognito client's callback and logout URLs and keeps every other setting, above all the write restriction."""
from infra.functions.portal_callback import merged_client_settings, on_event

PORTAL_URLS = ["https://d111.cloudfront.net", "https://d111.cloudfront.net/"]
DESCRIBED_CLIENT = {
    "UserPoolId": "eu-west-1_example", "ClientId": "client-1", "ClientName": "PortalClient",
    "CallbackURLs": ["http://localhost:4200"], "LogoutURLs": ["http://localhost:4200"],
    "AllowedOAuthFlows": ["code"], "AllowedOAuthScopes": ["openid", "profile"],
    "AllowedOAuthFlowsUserPoolClient": True, "SupportedIdentityProviders": ["COGNITO"],
    "WriteAttributes": ["name"], "IdTokenValidity": 60, "TokenValidityUnits": {"IdToken": "minutes"},
    "PreventUserExistenceErrors": "ENABLED",
    "ExplicitAuthFlows": ["ALLOW_ADMIN_USER_PASSWORD_AUTH", "ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"],
    "CreationDate": "2026-10-15T10:00:00Z", "LastModifiedDate": "2026-10-15T10:00:00Z",
}


class FakeCognito:
    """Stands in for boto3's cognito-idp client: returns DESCRIBED_CLIENT and records the update."""
    def __init__(self):
        self.updates = []

    def describe_user_pool_client(self, UserPoolId: str, ClientId: str) -> dict:
        return {"UserPoolClient": {**DESCRIBED_CLIENT, "UserPoolId": UserPoolId, "ClientId": ClientId}}

    def update_user_pool_client(self, **settings) -> dict:
        self.updates.append(settings)
        return {"UserPoolClient": settings}


def test_the_portal_urls_are_added_to_the_callback_and_logout_urls():
    settings = merged_client_settings(DESCRIBED_CLIENT, PORTAL_URLS)
    assert settings["CallbackURLs"] == ["http://localhost:4200", *PORTAL_URLS]
    assert settings["LogoutURLs"] == ["http://localhost:4200", *PORTAL_URLS]


def test_every_other_setting_is_kept_and_read_only_fields_are_dropped():
    settings = merged_client_settings(DESCRIBED_CLIENT, PORTAL_URLS)
    assert settings["WriteAttributes"] == ["name"] and settings["AllowedOAuthFlows"] == ["code"]
    assert settings["ExplicitAuthFlows"] == DESCRIBED_CLIENT["ExplicitAuthFlows"]
    assert "CreationDate" not in settings and "LastModifiedDate" not in settings


def test_running_twice_adds_nothing_twice():
    once = merged_client_settings(DESCRIBED_CLIENT, PORTAL_URLS)
    twice = merged_client_settings({**DESCRIBED_CLIENT, **once}, PORTAL_URLS)
    assert twice["CallbackURLs"] == once["CallbackURLs"]


def test_create_describes_then_updates_the_client():
    cognito = FakeCognito()
    event = {"RequestType": "Create", "ResourceProperties": {
        "UserPoolId": "eu-west-1_example", "ClientId": "client-1", "PortalUrls": PORTAL_URLS}}
    response = on_event(event, None, cognito_client=cognito)
    assert cognito.updates[0]["CallbackURLs"][-1] == PORTAL_URLS[-1]
    assert response == {"PhysicalResourceId": "client-1-portal-callback"}


def test_delete_changes_nothing():
    cognito = FakeCognito()
    event = {"RequestType": "Delete", "PhysicalResourceId": "client-1-portal-callback", "ResourceProperties": {}}
    assert on_event(event, None, cognito_client=cognito) == {"PhysicalResourceId": "client-1-portal-callback"}
    assert cognito.updates == []
```
The fake's parameter names (`UserPoolId`, `ClientId`) are boto3's keyword names, so the fake is called exactly like the real client.

- [ ] **Step 3: Run them and watch them fail**
```bash
uv run --locked pytest tests/infra/functions/test_portal_callback.py --no-cov 2>&1 | grep -E "^E |error"
```
Expected: `E   ModuleNotFoundError: No module named 'infra.functions'` and `1 error`.

- [ ] **Step 4: Implement.** Create `infra/functions/__init__.py`:
```python
"""Code that runs in AWS for the stacks themselves (a custom resource, a CloudFront Function), not for the portal."""
from pathlib import Path

FUNCTIONS_DIRECTORY = Path(__file__).resolve().parent
PORTAL_CALLBACK_SOURCE = FUNCTIONS_DIRECTORY / "portal_callback.py"
SPA_REWRITE_SOURCE = FUNCTIONS_DIRECTORY / "spa_rewrite.js"
```
Create `infra/functions/portal_callback.py`:
```python
"""Custom resource (WebStack, M4a): add the portal's CloudFront URL to the Cognito client's callback and logout URLs.

CloudFormation can't set them itself: the client (AuthStack) must exist before the API (it is the JWT audience),
and the API before the distribution (its /api/* origin). Every other client setting is read and written back
unchanged, because UpdateUserPoolClient resets any field it isn't given (WriteAttributes would fall back to
"all", letting users write their own custom:entity_ids)."""
import boto3

URL_LIST_FIELDS = ("CallbackURLs", "LogoutURLs")
UPDATABLE_CLIENT_FIELDS = (
    "UserPoolId", "ClientId", "ClientName", "RefreshTokenValidity", "AccessTokenValidity", "IdTokenValidity",
    "TokenValidityUnits", "ReadAttributes", "WriteAttributes", "ExplicitAuthFlows", "SupportedIdentityProviders",
    "CallbackURLs", "LogoutURLs", "DefaultRedirectURI", "AllowedOAuthFlows", "AllowedOAuthScopes",
    "AllowedOAuthFlowsUserPoolClient", "AnalyticsConfiguration", "PreventUserExistenceErrors",
    "EnableTokenRevocation", "EnablePropagateAdditionalUserContextData", "AuthSessionValidity",
    "RefreshTokenRotation",
)
DELETE_REQUEST = "Delete"
PHYSICAL_ID_SUFFIX = "-portal-callback"


def merged_client_settings(described_client: dict, portal_urls: list[str]) -> dict:
    """The UpdateUserPoolClient arguments: the client as it is, plus the portal URLs (each once, sorted)."""
    settings = {field: described_client[field] for field in UPDATABLE_CLIENT_FIELDS if field in described_client}
    for field in URL_LIST_FIELDS:
        settings[field] = sorted(set(described_client.get(field, [])) | set(portal_urls))
    return settings


def on_event(event: dict, context: object, cognito_client=None) -> dict:
    """Create and Update merge the URLs in; Delete changes nothing (the pool goes when AuthStack is destroyed)."""
    if event["RequestType"] == DELETE_REQUEST:
        return {"PhysicalResourceId": event["PhysicalResourceId"]}
    properties = event["ResourceProperties"]
    client = cognito_client or boto3.client("cognito-idp")
    described = client.describe_user_pool_client(UserPoolId=properties["UserPoolId"],
                                                 ClientId=properties["ClientId"])["UserPoolClient"]
    client.update_user_pool_client(**merged_client_settings(described, properties["PortalUrls"]))
    return {"PhysicalResourceId": f"{properties['ClientId']}{PHYSICAL_ID_SUFFIX}"}
```
`UPDATABLE_CLIENT_FIELDS` is the request shape of Cognito's `UpdateUserPoolClient` API. The file must stay under 4,096 bytes (Task 3 inlines it; dry-run: 2,438).

- [ ] **Step 5: Run them**
```bash
uv run --locked pytest tests/infra/functions/test_portal_callback.py --no-cov 2>&1 | tail -1
```
Expected: `5 passed`.

- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/functions/__init__.py infra/functions/portal_callback.py tests/infra/functions/test_portal_callback.py
git commit -m "infra: custom-resource handler that adds the portal URL to the Cognito client and keeps every other setting"
```
Expected: S + 5 passed (`240 passed`), `TOTAL ... 96%`.

**Task done when:**
- The five callback tests pass and the suite is at S + 5.
- `wc -c infra/functions/portal_callback.py` is below `4096`.

### Task 2: The SPA-rewrite CloudFront Function (`infra/functions/spa_rewrite.js`)

**Files:**
- Create: `infra/functions/spa_rewrite.js`, `tests/infra/functions/test_spa_rewrite.py` *(new)*

**Produces:** `spa_rewrite.js` `handler(event)`. **Consumes:** `infra.functions.SPA_REWRITE_SOURCE` (Task 1). **Consumed by:** Task 3.

- [ ] **Step 1: Write the failing tests.** Create `tests/infra/functions/test_spa_rewrite.py`:
```python
"""The CloudFront Function on the portal's default behaviour (infra/functions/spa_rewrite.js): Angular routes get
index.html, real files and the API are untouched. Runs the function in Node, which the CDK tests need anyway."""
import json
import subprocess

import pytest

from infra.functions import SPA_REWRITE_SOURCE

NODE_EXECUTABLE = "node"


def _rewritten_uri(uri: str) -> str:
    script = (f"{SPA_REWRITE_SOURCE.read_text()}\n"
              f"process.stdout.write(handler({json.dumps({'request': {'uri': uri}})}).uri);")
    completed = subprocess.run([NODE_EXECUTABLE, "-e", script], capture_output=True, text=True, check=True)
    return completed.stdout


@pytest.mark.parametrize("route", ["/", "/entity/E4", "/ask"])
def test_routes_without_a_file_extension_get_the_app(route):
    assert _rewritten_uri(route) == "/index.html"


@pytest.mark.parametrize("file_path", ["/main-ABC123.js", "/styles.css", "/portal-config.json", "/favicon.ico"])
def test_files_are_served_as_they_are(file_path):
    assert _rewritten_uri(file_path) == file_path
```

- [ ] **Step 2: Run them and watch them fail**
```bash
uv run --locked pytest tests/infra/functions/test_spa_rewrite.py --no-cov 2>&1 | grep -E "^E |passed|failed" | sort | uniq -c
```
Expected: `7 E       FileNotFoundError: [Errno 2] No such file or directory: '.../infra/functions/spa_rewrite.js'` and `7 failed`.

- [ ] **Step 3: Implement.** Create `infra/functions/spa_rewrite.js`:
```javascript
// CloudFront Function (viewer request, the portal's default behaviour only; WebStack, M4a).
// An Angular route such as /entity/E4 has no file behind it, so serve the app's index.html instead.
// Real files (anything whose last path segment has a dot) pass through. /api/* never reaches this function.
function handler(event) {
    var request = event.request;
    var lastSegment = request.uri.split('/').pop();
    if (lastSegment.indexOf('.') === -1) {
        request.uri = '/index.html';
    }
    return request;
}
```
(CloudFront Functions take the request and return it; `var` and `indexOf` are valid in the `cloudfront-js-2.0` runtime.)

- [ ] **Step 4: Run them**
```bash
uv run --locked pytest tests/infra/functions/test_spa_rewrite.py --no-cov 2>&1 | tail -1
```
Expected: `7 passed`.

- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/functions/spa_rewrite.js tests/infra/functions/test_spa_rewrite.py
git commit -m "infra: CloudFront Function that serves index.html for Angular routes and leaves files alone"
```
Expected: S + 12 passed (`247 passed`), `TOTAL ... 96%`.

**Task done when:**
- The seven rewrite cases pass in Node and the suite is at S + 12.

### Task 3: `WebStack` (site, distribution, `/api/*`, upload, callback)

**Files:**
- Modify: `infra/constants.py`
- Create: `infra/stacks/web_stack.py`, `tests/infra/stacks/test_web_stack.py` *(new)*

**Produces:** `infra.stacks.web_stack.WebStack(scope, construct_id, *, http_api, user_pool, user_pool_client, managed_login_domain, web_build_directory: Path, **kwargs)`; `INLINE_HANDLER`, `ENDPOINT_HOST_INDEX`, `INVALIDATE_EVERYTHING`, `API_PATH_PATTERN`; outputs `PortalUrl`, `DistributionId`, `SiteBucketName`; constants `WEB_BUILD_DIRECTORY`, `WEB_INDEX_DOCUMENT`, `PORTAL_CONFIG_FILE`, `PORTAL_CALLBACK_REVISION`, `HTTPS_SCHEME`, `URL_PATH_SEPARATOR`, `CUSTOM_RESOURCE_TIMEOUT_SECONDS`. **Consumes:** `infra.constants.API_BASE_PATH`, `LOG_RETENTION` (M2); `AuthStack` (M3b); `infra.functions` (Tasks 1–2). **Consumed by:** Task 4, M4b (none), M5 (the `PortalUrl` output).

- [ ] **Step 1: Write the failing tests.** Create `tests/infra/stacks/test_web_stack.py`:
```python
"""WebStack: the portal on S3 + CloudFront, /api/* passed to the HTTP API with the Authorization header and no
caching, no custom error pages (they would hide the API's 403/404), and the Cognito callback set to the portal.

Uses a stand-in HTTP API (the real one is Y1's ApiStack) and a temporary build folder (the real one is
web/dist/web/browser, built by `yarn build`)."""
import aws_cdk as cdk
import pytest
from aws_cdk import aws_apigatewayv2 as apigateway
from aws_cdk.assertions import Match, Template

from config import DEFAULT_REGION
from infra.stacks.auth_stack import AuthStack
from infra.stacks.web_stack import WebStack

TEST_PREFIX = "test"
CACHING_DISABLED_POLICY_ID = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"            # Managed-CachingDisabled
ALL_VIEWER_EXCEPT_HOST_POLICY_ID = "b689b0a8-53d0-40ab-baf2-68738e2966ac"      # Managed-AllViewerExceptHostHeader
ALL_HTTP_METHODS = ["GET", "HEAD", "OPTIONS", "PUT", "PATCH", "POST", "DELETE"]


def _web_stack(build_directory) -> WebStack:
    app = cdk.App(context={"aws:cdk:bundling-stacks": []})
    environment = cdk.Environment(region=DEFAULT_REGION)
    auth = AuthStack(app, "AuthStack", prefix=TEST_PREFIX, env=environment)
    stand_in = cdk.Stack(app, "ApiStandIn", env=environment)
    http_api = apigateway.HttpApi(stand_in, "HttpApi", create_default_stage=False)
    return WebStack(app, "WebStack", http_api=http_api, user_pool=auth.user_pool,
                    user_pool_client=auth.user_pool_client, managed_login_domain=auth.managed_login_domain,
                    web_build_directory=build_directory, env=environment)


@pytest.fixture(scope="module")
def web_template(tmp_path_factory) -> Template:
    build_directory = tmp_path_factory.mktemp("browser")
    (build_directory / "index.html").write_text("<!doctype html><title>portal</title>")
    return Template.from_stack(_web_stack(build_directory))


def test_the_api_behaviour_forwards_everything_but_host_and_caches_nothing(web_template):
    web_template.has_resource_properties("AWS::CloudFront::Distribution", {"DistributionConfig": {
        "CacheBehaviors": [Match.object_like({
            "PathPattern": "/api/*", "AllowedMethods": ALL_HTTP_METHODS, "ViewerProtocolPolicy": "https-only",
            "CachePolicyId": CACHING_DISABLED_POLICY_ID, "OriginRequestPolicyId": ALL_VIEWER_EXCEPT_HOST_POLICY_ID,
        })],
    }})


def test_the_api_origin_is_reached_over_https_only(web_template):
    web_template.has_resource_properties("AWS::CloudFront::Distribution", {"DistributionConfig": {
        "Origins": Match.array_with([Match.object_like({
            "CustomOriginConfig": Match.object_like({"OriginProtocolPolicy": "https-only"})})]),
    }})


def test_there_are_no_custom_error_pages_and_routes_are_rewritten_on_the_default_behaviour_only(web_template):
    distribution = next(iter(web_template.find_resources("AWS::CloudFront::Distribution").values()))
    config = distribution["Properties"]["DistributionConfig"]
    assert "CustomErrorResponses" not in config
    assert config["DefaultRootObject"] == "index.html"
    assert config["DefaultCacheBehavior"]["ViewerProtocolPolicy"] == "redirect-to-https"
    assert [association["EventType"] for association in config["DefaultCacheBehavior"]["FunctionAssociations"]] == \
        ["viewer-request"]
    assert "FunctionAssociations" not in config["CacheBehaviors"][0]


def test_the_site_bucket_is_private_reached_through_origin_access_control_and_destroyed(web_template):
    web_template.has_resource("AWS::S3::Bucket", {"DeletionPolicy": "Delete", "Properties": Match.object_like({
        "PublicAccessBlockConfiguration": {"BlockPublicAcls": True, "BlockPublicPolicy": True,
                                           "IgnorePublicAcls": True, "RestrictPublicBuckets": True}})})
    web_template.resource_count_is("AWS::CloudFront::OriginAccessControl", 1)


def test_the_build_and_the_runtime_config_are_uploaded_and_the_cache_invalidated(web_template):
    web_template.has_resource_properties("Custom::CDKBucketDeployment", {"DistributionPaths": ["/*"]})


def test_the_callback_resource_may_only_describe_and_update_clients_of_this_pool(web_template):
    web_template.has_resource_properties("AWS::IAM::Policy", {"PolicyDocument": {"Statement": [{
        "Action": ["cognito-idp:DescribeUserPoolClient", "cognito-idp:UpdateUserPoolClient"],
        "Effect": "Allow", "Resource": Match.any_value()}]}})
    web_template.resource_count_is("AWS::CloudFormation::CustomResource", 1)


def test_the_portal_url_and_ids_are_outputs(web_template):
    assert {"PortalUrl", "DistributionId", "SiteBucketName"} <= set(web_template.find_outputs("*"))


def test_a_missing_build_stops_the_synth_with_the_command_to_run(tmp_path):
    with pytest.raises(FileNotFoundError, match="yarn build"):
        _web_stack(tmp_path / "missing")
```

- [ ] **Step 2: Run them and watch them fail**
```bash
uv run --locked pytest tests/infra/stacks/test_web_stack.py --no-cov 2>&1 | grep -E "^E |error"
```
Expected: `E   ModuleNotFoundError: No module named 'infra.stacks.web_stack'` and `1 error`.

- [ ] **Step 3: Add the constants.** In `infra/constants.py`, change `from config import DEFAULT_ARTEFACTS_URI` to `from config import DEFAULT_ARTEFACTS_URI, REPO_ROOT`, then append:
```python

# Portal hosting (WebStack). The build is Mildred's and Clement's: `cd web && yarn build`.
WEB_BUILD_DIRECTORY = REPO_ROOT / "web" / "dist" / "web" / "browser"
WEB_INDEX_DOCUMENT = "index.html"
PORTAL_CONFIG_FILE = "portal-config.json"         # read by the portal at start-up (proposal to Clement, M4a)
PORTAL_CALLBACK_REVISION = "1"                    # bump to re-run the Cognito callback merge (see M4a, M5)
HTTPS_SCHEME = "https://"
URL_PATH_SEPARATOR = "/"
CUSTOM_RESOURCE_TIMEOUT_SECONDS = 60
```

- [ ] **Step 4: Implement the stack.** Create `infra/stacks/web_stack.py`:
```python
"""WebStack: the Angular portal on S3 + CloudFront, with /api/* passed through to the HTTP API (same origin, no
CORS), and the portal's URL added to the Cognito client's callback URLs."""
from pathlib import Path

from aws_cdk import CfnOutput, CustomResource, Duration, Fn, RemovalPolicy, Stack
from aws_cdk import aws_apigatewayv2 as apigateway
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3_deployment
from aws_cdk import custom_resources
from constructs import Construct

from infra.constants import (API_BASE_PATH, CUSTOM_RESOURCE_TIMEOUT_SECONDS, HTTPS_SCHEME, LOG_RETENTION,
                             PORTAL_CALLBACK_REVISION, PORTAL_CONFIG_FILE, URL_PATH_SEPARATOR, WEB_INDEX_DOCUMENT)
from infra.functions import PORTAL_CALLBACK_SOURCE, SPA_REWRITE_SOURCE

INLINE_HANDLER = "index.on_event"       # Code.from_inline stores the source as index.py
ENDPOINT_HOST_INDEX = 2                 # "https://<id>.execute-api.<region>.amazonaws.com".split("/")[2] is the host
INVALIDATE_EVERYTHING = "/*"
API_PATH_PATTERN = f"{URL_PATH_SEPARATOR}{API_BASE_PATH}{URL_PATH_SEPARATOR}*"   # /api/*


class WebStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, http_api: apigateway.IHttpApi,
                 user_pool: cognito.IUserPool, user_pool_client: cognito.IUserPoolClient,
                 managed_login_domain: cognito.UserPoolDomain, web_build_directory: Path, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        if not (web_build_directory / WEB_INDEX_DOCUMENT).is_file():
            raise FileNotFoundError(f"no portal build in {web_build_directory}: run `cd web && yarn build` first")
        site_bucket = s3.Bucket(self, "SiteBucket", block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                encryption=s3.BucketEncryption.S3_MANAGED, enforce_ssl=True,
                                removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True)
        spa_rewrite = cloudfront.Function(self, "SpaRewrite", runtime=cloudfront.FunctionRuntime.JS_2_0,
                                          code=cloudfront.FunctionCode.from_file(file_path=str(SPA_REWRITE_SOURCE)))
        api_host = Fn.select(ENDPOINT_HOST_INDEX, Fn.split(URL_PATH_SEPARATOR, http_api.api_endpoint))
        distribution = cloudfront.Distribution(
            self, "Distribution",
            default_root_object=WEB_INDEX_DOCUMENT,
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(site_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                function_associations=[cloudfront.FunctionAssociation(
                    function=spa_rewrite, event_type=cloudfront.FunctionEventType.VIEWER_REQUEST)],
            ),
            additional_behaviors={API_PATH_PATTERN: cloudfront.BehaviorOptions(
                origin=origins.HttpOrigin(api_host, protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,   # answers are per user: never cache
                # Every viewer header but Host, so the ID token (Authorization) reaches the JWT authorizer.
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
            )},
        )
        portal_url = f"{HTTPS_SCHEME}{distribution.distribution_domain_name}"
        s3_deployment.BucketDeployment(
            self, "PortalUpload",
            sources=[
                s3_deployment.Source.asset(str(web_build_directory)),
                s3_deployment.Source.json_data(PORTAL_CONFIG_FILE, {
                    "apiBaseUrl": f"{URL_PATH_SEPARATOR}{API_BASE_PATH}",
                    "userPoolId": user_pool.user_pool_id,
                    "userPoolClientId": user_pool_client.user_pool_client_id,
                    "managedLoginDomain": managed_login_domain.base_url(),
                    "redirectUrl": portal_url,
                }),
            ],
            destination_bucket=site_bucket,
            distribution=distribution,
            distribution_paths=[INVALIDATE_EVERYTHING],
        )
        self._add_portal_to_callback_urls(user_pool, user_pool_client, portal_url)
        CfnOutput(self, "PortalUrl", value=portal_url)
        CfnOutput(self, "DistributionId", value=distribution.distribution_id)
        CfnOutput(self, "SiteBucketName", value=site_bucket.bucket_name)

    def _add_portal_to_callback_urls(self, user_pool: cognito.IUserPool, user_pool_client: cognito.IUserPoolClient,
                                     portal_url: str) -> None:
        handler = lambda_.Function(
            self, "PortalCallbackHandler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler=INLINE_HANDLER,
            code=lambda_.Code.from_inline(PORTAL_CALLBACK_SOURCE.read_text()),
            timeout=Duration.seconds(CUSTOM_RESOURCE_TIMEOUT_SECONDS),
            log_group=logs.LogGroup(self, "PortalCallbackLogs", retention=LOG_RETENTION,
                                    removal_policy=RemovalPolicy.DESTROY),
        )
        handler.add_to_role_policy(iam.PolicyStatement(
            actions=["cognito-idp:DescribeUserPoolClient", "cognito-idp:UpdateUserPoolClient"],
            resources=[user_pool.user_pool_arn]))
        provider = custom_resources.Provider(
            self, "PortalCallbackProvider", on_event_handler=handler,
            log_group=logs.LogGroup(self, "PortalCallbackProviderLogs", retention=LOG_RETENTION,
                                    removal_policy=RemovalPolicy.DESTROY))
        CustomResource(self, "PortalCallback", service_token=provider.service_token, properties={
            "UserPoolId": user_pool.user_pool_id,
            "ClientId": user_pool_client.user_pool_client_id,
            "PortalUrls": [portal_url, f"{portal_url}{URL_PATH_SEPARATOR}"],
            "Revision": PORTAL_CALLBACK_REVISION,
        })
```

- [ ] **Step 5: Run them**
```bash
uv run --locked pytest tests/infra/stacks/test_web_stack.py --no-cov 2>&1 | tail -1
```
Expected: `8 passed`.

- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/constants.py infra/stacks/web_stack.py tests/infra/stacks/test_web_stack.py
git commit -m "infra: WebStack, portal on CloudFront with /api/* to the HTTP API, runtime config and Cognito callback (M4a)"
```
Expected: S + 20 passed (`255 passed`), `TOTAL ... 96%`.

**Task done when:**
- The eight WebStack tests pass and the suite is at S + 20.
- `grep -n "error_responses\|ErrorResponse" infra/stacks/web_stack.py` prints nothing.

### Task 4: Wire `WebStack` into the app (after Y1 is merged)

**Files:**
- Modify: `infra/app.py` *(new)*, `tests/infra/conftest.py` *(new)*, `tests/infra/test_app.py` *(new)*

**Produces:** `PortalStacks.web`; `build_stacks(app: cdk.App, *, web_build_directory: Path = WEB_BUILD_DIRECTORY) -> PortalStacks`; the session fixture `web_build_directory` and `PORTAL_BUILD_STAND_IN` in `tests/infra/conftest.py`. **Consumes:** `PortalStacks.api.http_api` (Y1), `PortalStacks.auth` (M3b). **Consumed by:** M4b (`portal_stacks` with `web_build_directory`), M5.

- [ ] **Step 1: Bring in Y1.** Check [[Build order]]: Y1 must be `merged`. Then:
```bash
git fetch origin && git rebase origin/develop
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
grep -n "api = ApiStack\|api: ApiStack" infra/app.py
```
Expected: all passed; write the count into the ledger as **S1** (S + 20 + Y1's tests; dry-run with a stand-in: `255 passed`), and two lines showing Y1's `api: ApiStack` field and `api = ApiStack(...)` call. If Y1 isn't merged or those lines don't exist, stop and wait for Yaw.

- [ ] **Step 2: Write the failing tests.** Append to `tests/infra/test_app.py`:
```python


def test_the_web_stack_is_built_from_the_api_and_auth_stacks(portal_stacks):
    portal_stacks.web.node.root.synth()   # cross-stack dependencies are recorded when the app synthesises
    dependencies = {dependency.stack_name for dependency in portal_stacks.web.dependencies}
    assert {portal_stacks.api.stack_name, portal_stacks.auth.stack_name} <= dependencies


def test_the_app_refuses_to_synth_without_a_portal_build(tmp_path):
    with pytest.raises(FileNotFoundError, match="yarn build"):
        build_stacks(cdk.App(context={STACK_PREFIX_CONTEXT_KEY: "test"}), web_build_directory=tmp_path)
```

- [ ] **Step 3: Run them and watch them fail**
```bash
uv run --locked pytest tests/infra/test_app.py --no-cov 2>&1 | grep -E "^E  "
```
Expected: `E       AttributeError: 'PortalStacks' object has no attribute 'web'` and `E           TypeError: build_stacks() got an unexpected keyword argument 'web_build_directory'`.

- [ ] **Step 4: Wire it.** In `infra/app.py`:
  - change the `infra.constants` import to also import `WEB_BUILD_DIRECTORY` (for example `from infra.constants import STACK_PREFIX_CONTEXT_KEY, WEB_BUILD_DIRECTORY`; keep any names Y1 added);
  - add `from infra.stacks.web_stack import WebStack` as the last `infra.stacks` import;
  - add the field `web: WebStack` after `api: ApiStack` in `PortalStacks`;
  - change the signature to `def build_stacks(app: cdk.App, *, web_build_directory: Path = WEB_BUILD_DIRECTORY) -> PortalStacks:`;
  - directly after the `api = ApiStack(...)` statement, add:
    ```python
        web = WebStack(app, "WebStack", http_api=api.http_api, user_pool=auth.user_pool,
                       user_pool_client=auth.user_pool_client, managed_login_domain=auth.managed_login_domain,
                       web_build_directory=web_build_directory, **stack_options("WebStack"))
    ```
  - add `web=web` to the `PortalStacks(...)` call in the `return`.

  In `tests/infra/conftest.py`, change the `infra.constants` import to `from infra.constants import STACK_PREFIX_CONTEXT_KEY, WEB_INDEX_DOCUMENT`, and replace the `portal_stacks` fixture with:
```python
PORTAL_BUILD_STAND_IN = "<!doctype html><title>portal</title>"   # the real build is `cd web && yarn build`


@pytest.fixture(scope="session")
def web_build_directory(tmp_path_factory):
    build_directory = tmp_path_factory.mktemp("browser")
    (build_directory / WEB_INDEX_DOCUMENT).write_text(PORTAL_BUILD_STAND_IN)
    return build_directory


@pytest.fixture(scope="module")
def portal_stacks(web_build_directory):
    return build_stacks(cdk.App(context={STACK_PREFIX_CONTEXT_KEY: TEST_PREFIX, **SKIP_ALL_BUNDLING}),
                        web_build_directory=web_build_directory)
```
(If Y1 changed the `portal_stacks` fixture, keep its changes and add only the `web_build_directory` argument and fixture.)

- [ ] **Step 5: Run them**
```bash
uv run --locked pytest tests/infra/test_app.py --no-cov 2>&1 | tail -1
```
Expected: all passed (dry-run: `4 passed`; more if Y1 added app tests).

- [ ] **Step 6: Full suite, synth with the real build, commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
(cd web && corepack enable && yarn install --frozen-lockfile && yarn build) 2>&1 | tail -2
ls web/dist/web/browser/index.html
cd infra && env -u AWS_PROFILE AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q 2>&1 | grep -E "Successfully|rror"; ls cdk.out | grep -c "template.json"; cd ..
git add infra/app.py tests/infra/conftest.py tests/infra/test_app.py
git commit -m "infra: build WebStack in the app from the API and Auth stacks; tests use a stand-in portal build"
```
Expected: S1 + 2 passed (dry-run `257 passed`), `TOTAL ... 96%`; the build ends with `Output location: .../web/dist/web`; `web/dist/web/browser/index.html` exists; `Successfully synthesized`; the template count includes `WebStack.template.json` (dry-run with stand-ins: 6 templates). `web/dist/` *(new)* is ignored by git (`git status --short web` prints nothing).

**Task done when:**
- `uv run --locked pytest` is at S1 + 2 with 96%.
- `npx cdk synth -q` with no credentials and the real build writes `WebStack.template.json`.

### Task 5: Deploy, check the portal end to end, open the PR (verify in AWS; ask Michael first)

**Files:** none (deploy, checks and PR only).

**Produces:** a deployed `demo-WebStack`; the `PortalUrl` for everyone; the PR.

- [ ] **Step 1: Deploy (with Michael's OK).** The web build from Task 4 Step 6 must exist.
```bash
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
cd infra && npx cdk deploy WebStack --require-approval never 2>&1 | tail -6; cd ..
```
Expected (verify in AWS): `✅  demo-WebStack` (CloudFront takes several minutes) and outputs `PortalUrl = https://<id>.cloudfront.net`, `DistributionId = <id>`, `SiteBucketName = <name>`. If CDK also wants to deploy stacks WebStack depends on, it lists them first; they must already be deployed with no changes.

- [ ] **Step 2: Read the outputs**
```bash
stack_output() { aws cloudformation describe-stacks --stack-name "$1" --query "Stacks[0].Outputs[?OutputKey=='$2'].OutputValue" --output text; }
PORTAL_URL=$(stack_output demo-WebStack PortalUrl)
USER_POOL_ID=$(stack_output demo-AuthStack UserPoolId)
USER_POOL_CLIENT_ID=$(stack_output demo-AuthStack UserPoolClientId)
echo "$PORTAL_URL"
```
Expected: `https://<id>.cloudfront.net`.

- [ ] **Step 3: The portal and its routes load (verify in AWS)**
```bash
for portal_path in / /entity/E4 /portal-config.json; do
  curl -s -o /dev/null -w "${portal_path} %{http_code} %{content_type}\n" "${PORTAL_URL}${portal_path}"
done
curl -s "${PORTAL_URL}/portal-config.json"; echo
```
Expected: `/ 200 text/html`, `/entity/E4 200 text/html`, `/portal-config.json 200 application/json`, then `{"apiBaseUrl":"/api","userPoolId":"<UserPoolId>","userPoolClientId":"<UserPoolClientId>","managedLoginDomain":"https://demo-erp-portal-796973512193.auth.eu-west-1.amazoncognito.com","redirectUrl":"<PortalUrl>"}`.

- [ ] **Step 4: The callback merge added the portal and kept the rest (verify in AWS; Review Focus 3)**
```bash
aws cognito-idp describe-user-pool-client --user-pool-id "$USER_POOL_ID" --client-id "$USER_POOL_CLIENT_ID" \
  --query "UserPoolClient.[CallbackURLs, WriteAttributes, ExplicitAuthFlows, AllowedOAuthFlows]" --output json
```
Expected: `[ ["<PortalUrl>", "<PortalUrl>/", "http://localhost:4200"], ["name"], ["ALLOW_ADMIN_USER_PASSWORD_AUTH", "ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"], ["code"]]` (the URL list is sorted). If `WriteAttributes` is missing or longer, stop: security finding.

- [ ] **Step 5: `/api/*` reaches the authorizer, which refuses no token (verify in AWS)**
```bash
curl -s -o /dev/null -w "%{http_code}\n" "${PORTAL_URL}/api/summary"
```
Expected: `401`.

- [ ] **Step 6: A signed-in CFO gets the summary through CloudFront (verify in AWS; needs Linus's `/summary` handler behind Y1)**
```bash
read -rsp "Password for cfo-user: " demo_password && echo
CFO_ID_TOKEN=$(aws cognito-idp admin-initiate-auth --user-pool-id "$USER_POOL_ID" --client-id "$USER_POOL_CLIENT_ID" \
  --auth-flow ADMIN_USER_PASSWORD_AUTH --auth-parameters "USERNAME=cfo-user,PASSWORD=${demo_password}" \
  --query AuthenticationResult.IdToken --output text)
unset demo_password
curl -s -w "\n%{http_code} %{content_type}\n" -H "Authorization: Bearer ${CFO_ID_TOKEN}" "${PORTAL_URL}/api/summary" | tail -c 120
```
Expected: the end of the summary JSON, then `200 application/json`. (If Y1 still serves a stub `/summary`, expect its stub JSON and `200`; write which in the ledger.)

- [ ] **Step 7: The API's refusal survives CloudFront (verify in AWS; Review Focus 1; needs Linus's `/entity` handler)**
```bash
read -rsp "Password for e4-lead-user: " demo_password && echo
E4_ID_TOKEN=$(aws cognito-idp admin-initiate-auth --user-pool-id "$USER_POOL_ID" --client-id "$USER_POOL_CLIENT_ID" \
  --auth-flow ADMIN_USER_PASSWORD_AUTH --auth-parameters "USERNAME=e4-lead-user,PASSWORD=${demo_password}" \
  --query AuthenticationResult.IdToken --output text)
unset demo_password
curl -s -w "\n%{http_code} %{content_type}\n" -H "Authorization: Bearer ${E4_ID_TOKEN}" "${PORTAL_URL}/api/entity/E2"
unset CFO_ID_TOKEN E4_ID_TOKEN
```
Expected: `{"error": "out_of_scope", "detail": "..."}` (the C1 `ErrorResponse`), then `403 application/json`. **HTML here means an error page rewrote the API's answer: stop.** If Linus's handler isn't deployed yet, record "Step 7 pending L2" in the ledger and repeat it before the PR is merged.

- [ ] **Step 8: Review Focus, then the PR (with Michael's OK).** Work through the Review Focus list and write each result in the ledger. Then:
```bash
git push -u origin feature/infra-web
gh pr create --repo Amali-Tech/cloud-9-hackathon --base develop --title "infra: WebStack, the portal on CloudFront with /api/* and the Cognito callback (M4a)" --body-file .superpowers/pr-M4a.md
```
Write `.superpowers/pr-M4a.md` first: what changed (the distribution and its two behaviours, why no error pages, why `AllViewerExceptHostHeader` + `CachingDisabled`, the callback custom resource and `PORTAL_CALLBACK_REVISION`, `portal-config.json` for Clement and Mildred), the test count, the results of Steps 3–7 (status codes only; **no tokens**), and the ledger's `Ruling:` lines. No attribution lines.
Expected: the PR opens against `develop`; the Jenkins check goes green.

- [ ] **Step 9: Tell the team.** Post the `PortalUrl` for everyone; tell Clement and Mildred about `/portal-config.json` and its keys. Update [[Build order]]: M4a `in review (PR #nn)`.

**Task done when:**
- Steps 3, 4, 5 and 7 printed the expected status codes and client settings (Step 6 and 7 may be pending the handlers; ledger says so).
- The PR is open with a green Jenkins check.

## Done means
- [ ] **The suite is green with the web tests.** Verify: `uv run --locked pytest 2>&1 | grep -E "passed|TOTAL"` on the branch → S1 + 2 passed (dry-run 257), `TOTAL ... 96%`.
- [ ] **Synth needs no credentials, and there are no error pages.** Verify: with the web build present, `cd infra && env -u AWS_PROFILE AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q && grep -c CustomErrorResponses cdk.out/WebStack.template.json` → `Successfully synthesized` and `0`.
- [ ] **The portal is live (verify in AWS).** Verify: `curl -s -o /dev/null -w "%{http_code}" "$PORTAL_URL/entity/E4"` → `200`.
- [ ] **`/api/*` needs a token (verify in AWS).** Verify: `curl -s -o /dev/null -w "%{http_code}" "$PORTAL_URL/api/summary"` → `401`.
- [ ] **A token passes through CloudFront (verify in AWS).** Verify: Task 5 Step 6 → `200 application/json`.
- [ ] **An out-of-scope request stays a JSON 403 (verify in AWS).** Verify: Task 5 Step 7 → `403 application/json` with `"error": "out_of_scope"`.
- [ ] **Sign-in can return to the portal, and the client is still locked down (verify in AWS).** Verify: Task 5 Step 4 → the portal URL in `CallbackURLs`, `WriteAttributes` `["name"]`.
- [ ] **PR open to `develop`, green, and [[Build order]] says `in review (PR #nn)`.** Verify: `gh pr checks <nn> --repo Amali-Tech/cloud-9-hackathon` → the Jenkins check `pass`.

## Never
- Add custom error responses (403/404 → `index.html`) to the distribution.
- Cache `/api/*`, or forward `Host` to API Gateway.
- Call `UpdateUserPoolClient` with only the URLs (it resets `WriteAttributes` to "all").
- Make the site bucket public or serve it without origin access control.
- Print, save or post a token or password; deploy from CI; push to `develop` or `main`; add attribution lines.

Related: [[M4a - WebStack - spec]], [[Build order]], [[Michael - DevOps]], [[How to execute a plan]]
