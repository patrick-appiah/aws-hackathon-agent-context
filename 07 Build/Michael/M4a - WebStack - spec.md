---
tags: [build, spec, area/devops]
id: M4a
owner: Michael
status: ready
updated: 2026-10-14
---
# M4a: WebStack, the portal on S3 + CloudFront with `/api/*` and the Cognito callback (spec)
> **Split from M4** (the lead's rule). M4a is web hosting; [[M4b - Observability - spec]] is logs, traces and the dashboard. Each is deployable and mergeable on its own. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after [[M3b - AuthStack - spec]] is merged; the app wiring (Task 4) also needs Yaw's [[Y1 - ApiStack - spec]] merged.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] (`06 Workstreams/`): the architecture, the code already built, the contracts and the rules (§7).
3. [[Michael - DevOps]] (step 6, `WebStack`), [[Mildred - front end]] and [[Clement - front end]] (the build output, `apiBaseUrl: '/api'`, managed login + PKCE), [[Yaw - DevOps]] (the HTTP API behind `/api/*`).
4. [[M2 - App, DataStack and LedgerStack - spec]] (the CDK patterns), [[M3b - AuthStack - spec]] (the pool and client this item extends), [[Y1 - ApiStack - spec]] (`api.http_api`, the stage named `api`).
5. [[Build order]]: M4a depends on M2 and M3b, and on Y1 for the app wiring.
6. `01 Decisions/`: [[2026-10-13 Front end]], [[2026-10-14 Two apps in one repo]], [[2026-10-13 Scope from the token, enforced twice]]; `05 Workflow/`: [[Deploy and demo checks]].

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Michael (owner), Yaw (the API) or Clement (sign-in). Never invent a name, a shape or a rule.

## 1. Intent
**What:** a `WebStack` *(new)* with:
1. A **private site bucket** (S3-managed encryption, TLS only, destroyed and emptied with the stack), reached only through CloudFront **origin access control**.
2. A **CloudFront distribution**: default behaviour = the site bucket, HTTPS (redirect), `index.html` as root, and a **CloudFront Function** that rewrites Angular routes (no file extension) to `/index.html`. **No custom error responses.**
3. An **`/api/*` behaviour** to Yaw's HTTP API: HTTPS only to the origin and the viewer, all methods, the managed **`CachingDisabled`** cache policy and the managed **`AllViewerExceptHostHeader`** origin request policy (forwards `Authorization`).
4. A **`BucketDeployment`** of the Angular build `web/dist/web/browser` plus a generated **`portal-config.json`** (`apiBaseUrl`, `userPoolId`, `userPoolClientId`, `managedLoginDomain`, `redirectUrl`), invalidating the cache on every deploy. Synth stops with a clear message if the build is missing.
5. A **custom resource** (`infra/functions/portal_callback.py` *(new)*) that adds the CloudFront URL (with and without a trailing slash) to the Cognito client's callback and logout URLs, keeping every other client setting.
6. **Outputs** `PortalUrl`, `DistributionId`, `SiteBucketName`.

**Why:**
- The brief's "one screen" must be live on CloudFront by D1 18:00 (walking skeleton) and deploy from clean (hard gate 1).
- **Same origin:** the portal calls `'/api'`, so CloudFront must forward `/api/*` to API Gateway. No CORS to configure or get wrong.
- **The `Authorization` header must reach the JWT authorizer.** CloudFront removes it from `GET` / `HEAD` requests unless a cache policy or an origin request policy forwards it ("Configure CloudFront to forward the Authorization header", AWS CloudFront Developer Guide); `AllViewerExceptHostHeader` forwards every viewer header except `Host`, which API Gateway needs to be its own domain ("This policy is intended for use with Amazon API Gateway", same guide).
- **Never cache API answers:** they are per user and per scope. `CachingDisabled` also makes forwarding `Authorization` without it being in the cache key safe (the guide warns about exactly that).
- **No custom error responses:** distribution-wide error pages would turn the API's `403 out_of_scope` and `404 not_found` (C1 `ErrorResponse`) into `index.html` with a `200`, so the Q11 refusal and the portal's error handling would silently break. The SPA fallback is a viewer-request function on the default behaviour only.
- **The callback cycle:** AuthStack's client must exist before the API (its ID is the JWT audience), the API before the distribution (its `/api/*` origin), and the distribution before the callback URL is known. CloudFormation can't express that loop, so a small custom resource closes it after the distribution exists. `UpdateUserPoolClient` resets every field it isn't given, so the function reads the client and writes it back whole; otherwise `WriteAttributes` would fall back to "all" and users could write their own `custom:entity_ids` (M3b's control).
- **`portal-config.json`:** the pool and client IDs exist only after AuthStack deploys. A build-time `portal-config.ts` would need a second build after the first deploy, which breaks "deploy from clean with no manual steps". The generated file holds the same values with no rebuild.

**Success means:**
- `uv run --locked pytest` → **22 more tests** than before M4a plus whatever Y1 brought (dry-run: 235 → 257, with a stand-in for Y1's ApiStack that has no tests of its own), `TOTAL` 96%.
- `cd web && yarn build && cd ../infra && npx cdk synth -q` succeeds with no AWS credentials.
- **Verify in AWS:** the portal loads from the `PortalUrl` (`200`); `/entity/E4` loads the app (`200`, HTML); `/api/summary` without a token returns `401` from the authorizer; with the CFO's ID token `200` JSON; the E4 lead's `GET /api/entity/E2` returns **`403` JSON**, not HTML; the client's callback URLs list the portal URL; `/portal-config.json` shows the IDs.

**Assumptions** (reconcile with the named owner before the PR):
- **Yaw (Y1):** `PortalStacks.api.http_api` is an `aws_apigatewayv2.HttpApi` with `create_default_stage=False` and an auto-deployed stage named `infra.constants.API_BASE_PATH` (`"api"`), so CloudFront's `/api/summary` reaches route `GET /summary` on stage `api`. Routes return `401` without a token (JWT authorizer). If Y1 maps `/api` differently, stop and agree it with Yaw before Task 4.
- **Clement and Mildred (F1, F3):** the portal reads `/portal-config.json` at start-up (keys above) instead of hardcoding the IDs in `portal-config.ts`. If they keep build-time config, the file is harmless, but the clean-deploy runbook (M5) then needs a rebuild after AuthStack; tell Patrick.
- **Linus (L1–L3):** handlers return `403` / `404` with the C1 `ErrorResponse` JSON body (the check in Task 5 relies on it).
- **Mildred:** `cd web && yarn build` writes `web/dist/web/browser/index.html` (dry-run: 28 files including `index.html`).

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Site origin | `S3BucketOrigin.with_origin_access_control` on a private bucket | A public website bucket; origin access identity (legacy) |
| SPA routing | CloudFront Function (`cloudfront-js-2.0`), viewer request, default behaviour only: no dot in the last path segment → `/index.html` | Custom error responses 403/404 → `index.html` (rewrites the API's errors too) |
| `/api/*` caching | Managed `CachingDisabled` (`4135ea2d-6df8-44a3-9df3-4b5a84be39ad`) | A custom policy with `Authorization` in the cache key and a short TTL (caches per-user answers) |
| `/api/*` headers | Managed `AllViewerExceptHostHeader` (`b689b0a8-53d0-40ab-baf2-68738e2966ac`) | `AllViewer` (forwards `Host`; API Gateway rejects it); no policy (`Authorization` stripped on `GET`) |
| `/api` path | Forwarded unchanged; the stage named `api` receives it (Y1) | An origin path or a rewrite function (two places to keep in step) |
| API origin host | `Fn.select(2, Fn.split("/", http_api.api_endpoint))` | A hardcoded or output-copied domain |
| Runtime config | `Source.json_data("portal-config.json", ...)` with deploy-time tokens | Rebuilding the portal after AuthStack (a manual step); IDs in the repo |
| Callback URL | Custom resource: describe the client, merge the URLs, update with every field kept; Delete does nothing; a `Revision` property to force a re-run | `AwsCustomResource` calling `UpdateUserPoolClient` directly (resets unspecified fields, including `WriteAttributes`); the client in WebStack (Y1 would then depend on WebStack, which depends on Y1) |
| Handler code | `Code.from_inline` of `infra/functions/portal_callback.py` (2.4 KB, under the 4 KB inline limit), Python 3.12, boto3 from the runtime | An asset bundle (needs bundling; nothing to bundle) |
| Handler IAM | `cognito-idp:DescribeUserPoolClient`, `cognito-idp:UpdateUserPoolClient` on this pool's ARN only | `cognito-idp:*`; `*` resources |
| Missing build | `FileNotFoundError("no portal build in <dir>: run `cd web && yarn build` first")` at synth | Deploying an empty site |
| Test seams | `WebStack` takes `web_build_directory`; `build_stacks(app, *, web_build_directory=WEB_BUILD_DIRECTORY)`; tests pass a temporary folder | Tests depending on a real `yarn build` (CI's Python stage has no web build) |

## 3. Exact shapes
**`infra/constants.py` *(new)* additions:** import `REPO_ROOT` from `config` (`from config import DEFAULT_ARTEFACTS_URI, REPO_ROOT`), and:
| Name | Value |
|---|---|
| `WEB_BUILD_DIRECTORY` | `REPO_ROOT / "web" / "dist" / "web" / "browser"` |
| `WEB_INDEX_DOCUMENT` | `"index.html"` |
| `PORTAL_CONFIG_FILE` | `"portal-config.json"` |
| `PORTAL_CALLBACK_REVISION` | `"1"` |
| `HTTPS_SCHEME` | `"https://"` |
| `URL_PATH_SEPARATOR` | `"/"` |
| `CUSTOM_RESOURCE_TIMEOUT_SECONDS` | `60` |

**`infra/functions/` *(new)*:**
- `__init__.py`: `FUNCTIONS_DIRECTORY`, `PORTAL_CALLBACK_SOURCE`, `SPA_REWRITE_SOURCE` (paths).
- `portal_callback.py`: `URL_LIST_FIELDS`, `UPDATABLE_CLIENT_FIELDS`, `merged_client_settings(described_client: dict, portal_urls: list[str]) -> dict`, `on_event(event: dict, context: object, cognito_client=None) -> dict` (Create/Update → describe, merge, update, `{"PhysicalResourceId": "<client id>-portal-callback"}`; Delete → no call, the same ID back).
- `spa_rewrite.js`: `handler(event)` (CloudFront Functions 2.0).

**`infra/stacks/web_stack.py` *(new)*:** `WebStack(scope, construct_id, *, http_api: apigwv2.IHttpApi, user_pool: cognito.IUserPool, user_pool_client: cognito.IUserPoolClient, managed_login_domain: cognito.UserPoolDomain, web_build_directory: Path, **kwargs)`; module constants `INLINE_HANDLER = "index.on_event"`, `ENDPOINT_HOST_INDEX = 2`, `INVALIDATE_EVERYTHING = "/*"`, `API_PATH_PATTERN = "/api/*"`; outputs `PortalUrl` (`https://<distribution domain>`), `DistributionId`, `SiteBucketName`.

**`portal-config.json` (deployed):** `{"apiBaseUrl": "/api", "userPoolId": "<UserPoolId>", "userPoolClientId": "<UserPoolClientId>", "managedLoginDomain": "<ManagedLoginUrl>", "redirectUrl": "<PortalUrl>"}`.

**`infra/app.py` *(new)*:** `PortalStacks.web: WebStack`, built after `api` (Y1); `build_stacks(app: cdk.App, *, web_build_directory: Path = WEB_BUILD_DIRECTORY) -> PortalStacks`.

**`tests/infra/conftest.py` *(new)*:** a session fixture `web_build_directory` (a temporary folder with a stand-in `index.html`, `PORTAL_BUILD_STAND_IN`), passed to `build_stacks` by `portal_stacks`.

## 4. Tests (22 new)
- `tests/infra/functions/test_portal_callback.py` *(new)*, 5: URLs added to both lists; every other setting kept and read-only fields (`CreationDate`, `LastModifiedDate`) dropped; idempotent; Create describes then updates and returns the physical ID; Delete calls nothing.
- `tests/infra/functions/test_spa_rewrite.py` *(new)*, 7 (two parametrised tests): `/`, `/entity/E4`, `/ask` → `/index.html`; `/main-ABC123.js`, `/styles.css`, `/portal-config.json`, `/favicon.ico` unchanged. Runs the function in Node (the CDK tests already need Node).
- `tests/infra/stacks/test_web_stack.py` *(new)*, 8 (stand-in HTTP API, real `AuthStack`, temporary build): `/api/*` uses the two managed policy IDs, all seven methods, `https-only`; the API origin is `https-only`; no `CustomErrorResponses`, root `index.html`, default behaviour `redirect-to-https` with exactly one `viewer-request` function and none on `/api/*`; private bucket, `Delete`, one origin access control; the deployment invalidates `/*`; the callback handler's policy is exactly the two Cognito actions; the three outputs; a missing build raises `FileNotFoundError` mentioning `yarn build`.
- `tests/infra/test_app.py` *(new)*, 2 added: WebStack depends on the API and Auth stacks; `build_stacks` refuses to synth without a build.

## 5. Out of scope
- The `/api/*` routes, the authorizer and the handlers (Yaw Y1, Linus).
- Reading `portal-config.json` and the sign-in flow in Angular (Clement F3, Mildred).
- A custom domain, WAF, and CloudFront access logs (roadmap).
- The dashboard and log retention rule (M4b).

Related: [[M4a - WebStack - plan]], [[Build order]], [[Michael - DevOps]]
