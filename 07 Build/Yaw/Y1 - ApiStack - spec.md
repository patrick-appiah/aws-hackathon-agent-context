---
tags: [build, spec, area/devops]
id: Y1
owner: Yaw
status: ready
updated: 2026-10-14
---
# Y1: ApiStack, the HTTP API with the Cognito JWT authorizer and six routes (spec)
> The door every request goes through. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after [[M2 - App, DataStack and LedgerStack - spec]] and [[M3b - AuthStack - spec]] are merged (and [[M3a - GuardrailStack - spec]], which comes before AuthStack in `build_stacks`). Y1 also brings the two building blocks every later Yaw item reuses: the **local bundler** (no Docker) and **`PortalFunction`** (one least-privilege role and log group per Lambda).

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] (`06 Workstreams/`): the architecture with owners, the code already built, the contracts and the rules (§7).
3. [[Yaw - DevOps]]: the owner's brief; and [[Michael - DevOps]] (the other half of DevOps).
4. [[Build order]]: what this item depends on and unblocks.
5. [[M2 - App, DataStack and LedgerStack - spec]]: the CDK app, `build_stacks`, the prefix, the test fixtures and the patterns every DevOps item follows.
6. [[M3b - AuthStack - spec]] (the pool, the app client and `issuer_url` this API trusts) and [[M4a - WebStack - spec]] (CloudFront's `/api/*` behaviour that reaches this API).
7. [[Linus - API, identity, blocker-analyst]] (the handlers this API runs) and `docs/DEVOPS_HANDOVER.md` in the repo (entry points, environment, IAM, bundling).
8. `01 Decisions/`: [[2026-10-13 Scope from the token, enforced twice]], [[2026-10-13 Team are admins, workload roles least-privilege]], [[2026-10-13 EU-only Bedrock inference profiles]], [[2026-10-13 Prompts as versioned locked files]]; `05 Workflow/`: [[Deploy and demo checks]], [[Handling security findings]].
9. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Yaw (owner), Linus (handlers) or Michael (the pool). Never invent a name, a shape or a rule.

## 1. Intent
**What:** an `ApiStack` *(new)* and two shared helpers:
1. **API Gateway HTTP API (v2)** with **no default stage** and one stage named `api` (`infra.constants.API_BASE_PATH`, auto-deploy). CloudFront's `/api/*` behaviour (M4a) forwards `/api/summary` unchanged, and the `api` stage serves it as the route `GET /summary`: no path rewriting anywhere.
2. **Six routes**, each with **its own Lambda and its own role:** `GET /summary`, `GET /entity/{id}`, `GET /rows`, `POST /ask`, `POST /publish`, `POST /approve`.
3. **JWT authorizer** on every route: issuer = `auth.issuer_url` (`https://cognito-idp.eu-west-1.amazonaws.com/<pool id>`), audience = the portal app client ID (`auth.user_pool_client`), identity source `Authorization` header. The front end sends the **ID token** (custom claims live only there).
4. **Stubs first, then the real handlers:** every route first runs `infra/functions/stub_handler.py` *(new)*, which echoes the route and the JWT claims. A route switches to `infra.functions.api.<name>` only when its handler is merged (`ROUTES_WITH_REAL_HANDLERS`): L1 `summary`, L2 `entity` and `rows` (this item), L3 `ask`, `publish`, `approve` (added in Y2a/Y2b once their flow exists).
5. **`infra/bundling.py` *(new)*** *(new)*: builds a Lambda bundle **locally at synth time, with no Docker**: `uv export --locked --no-dev` + `uv pip install --target --python-platform x86_64-manylinux2014 --only-binary :all:`, then our code (`tools/`, `adapters/`, `agents/` with `prompts/*.txt` and `prompts.lock`, `config.py`, and the handler packages) on top. Bundles live in `infra/cdk.out/bundles/` *(new)* (gitignored, outside the style scan). Unit tests never bundle.
6. **`infra/portal_function.py` *(new)*** *(new)*: `PortalFunction`, the one way we build a Lambda: Python 3.11, X-Ray active, its own log group (`LOG_RETENTION`, `DESTROY`), and its **own role with no AWS managed policy**: only log writes to its own group plus the statements the caller passes.
7. **Fallback switch:** `-c auth_mode=none` synthesises the API **without** the authorizer and sets `AUTH_MODE=none` on the Lambdas (the D2 12:00 Cognito go/no-go fallback). A mistyped value fails the synth.
8. **Outputs:** `ApiUrl` (`<endpoint>/api`) and `AuthMode`. Attributes for M4a/M4b: `.http_api`, `.api_stage`, `.functions`.

**Why:**
- The brief's walking skeleton (D1 18:00) needs `/api/summary` live in AWS; the Cognito slice (D2 12:00) needs the authorizer. Scope comes from the token, server-side (D-010): API Gateway checks the signature; the handler (`infra/functions/scope.py` *(new)*, Linus) turns the claims into a `Scope`.
- HTTP API v2, not REST v1: its JWT authorizer reads Cognito tokens natively, and Linus's handler tests use v2 events.
- One role per function (ARCHITECTURE §7). `AWSLambdaBasicExecutionRole` has `logs:*` actions on `*`, so `PortalFunction` gives each role only its own log group.
- No Docker: the clean-deploy check must work on any laptop with `uv` and Node; the bundler only needs `uv` (D-017).

**Success means:**
- `uv run --locked pytest` → **S + 16 passed** (S = the count on `develop` before this item; dry-run 224 → **240**), `TOTAL` 96%.
- `npx cdk synth -q` with no AWS credentials writes `ApiStack.template.json` (stubs: no `infra/functions/api.py` needed; real handlers: needs Linus's `infra/functions/api.py` and `infra/functions/scope.py`).
- **Verify in AWS:** `curl` on `<ApiUrl>/summary` without a token → `401`; with the E4 lead's ID token → `200` and (stub) the claims `cognito:groups` and `custom:entity_ids=E4`; after L1/L2 → the summary JSON.

**Assumptions** (reconcile with the named owner before the PR):
- **Linus (L1–L3):** `infra/functions/api.py` *(new)* exposes `summary`, `entity`, `rows`, `ask`, `publish`, `approve`, each an HTTP API v2 Lambda handler `(event: dict, context) -> dict` (`statusCode`, `headers`, `body`), and imports `infra/functions/scope.py` (both copied into the bundle). Settings only via `config.get_settings()` from the environment variables in §3.
- **Michael (M3b):** `AuthStack` exposes `.issuer_url` and `.user_pool_client` (as his plan states). Dry-run used a stand-in with the same attributes.
- **Michael (M4a):** WebStack reads `api.http_api` and forwards `/api/*` with no origin path; the stage name `api` is the only coupling.
- The Lambda Python 3.11 runtime is Amazon Linux 2, so wheels are `manylinux2014` (glibc 2.17); x86_64 for the API Lambdas.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| How `/api/*` reaches the routes | A stage named `api` (`API_BASE_PATH`), no default stage | `/api` prefix on every route key (route keys would diverge from the contract's `GET /summary`); a CloudFront function rewriting the path (one more moving part) |
| Bundling | Local, at synth: `uv export --no-dev` + `uv pip install --target --python-platform`, then our code; skipped in tests | `PythonFunction` / Docker bundling (Docker on every machine, slower); a hand-written `requirements.txt` (D-017 forbids) |
| Where bundles go | `infra/cdk.out/bundles/<name>` | `infra/build/` *(new)* (the style test would scan the installed packages and fail on their single-letter names) |
| Lambda roles | `PortalFunction`: our own role, log writes to its own group only, X-Ray active | CDK's default role (adds `AWSLambdaBasicExecutionRole`: `logs:CreateLogGroup` on `*`) |
| Stubs before handlers | `ROUTES_WITH_REAL_HANDLERS`; unlisted routes run `stub_handler.handler` (echoes the claims) | Waiting for every handler (no deploy until D1 evening); a flag that guesses from whether `infra/functions/api.py` exists (silent) |
| Auth fallback | `-c auth_mode=none` → no authorizer, `AUTH_MODE=none`; anything else but `cognito` fails the synth | A second API; editing code at the go/no-go |
| Data access | Every route: `s3:GetObject` on `artefacts/*` only (`DataStack.artefacts_read_statement()`) | `bucket.grant_read` (`s3:GetObject*`, `s3:List*`: wildcard actions) |

## 3. Shapes and behaviour
| Route | Construct | Handler (stub / real) | Environment | IAM (besides its own log group and X-Ray) |
|---|---|---|---|---|
| `GET /summary` | `SummaryFunction` | `stub_handler.handler` / `infra.functions.api.summary` | `ARTEFACT_BACKEND=csv`, `ARTEFACTS_URI=s3://<bucket>/artefacts/`, `AUTH_MODE`, `DEFAULT_TENANT_ID=t-01` | `s3:GetObject` on `<bucket>/artefacts/*` |
| `GET /entity/{id}` | `EntityFunction` | … / `infra.functions.api.entity` | same | same |
| `GET /rows` | `RowsFunction` | … / `infra.functions.api.rows` | same | same |
| `POST /ask` | `AskFunction` | stub until L3 (Y2a adds `ASK_STATE_MACHINE_ARN`, `states:StartSyncExecution`) | same | same |
| `POST /publish` | `PublishFunction` | stub until L3 (Y2b adds the publish settings and IAM) | same | same |
| `POST /approve` | `ApproveFunction` | stub until L3 (Y2b) | same | same |

- `infra.bundling`: `BundleSpec(name, code_paths, python_platform=LAMBDA_PYTHON_PLATFORM, root_files=())`, `CORE_CODE = ("tools", "adapters", "agents", "config.py", "infra/__init__.py")`, `API_BUNDLE = BundleSpec("api", (*CORE_CODE, "infra/functions/__init__.py", "infra/functions/api.py", "infra/functions/scope.py"))`, `build_bundle(spec, *, repo_root, output_root, install) -> Path` (missing code path → `FileNotFoundError` naming it), `bundle_code(scope, spec) -> lambda_.Code`, `bundle_path(scope, spec) -> str` (both return placeholders when the stack skips bundling).
- `infra.portal_function.PortalFunction(scope, id, *, handler, code, environment, statements, timeout=29 s, memory_megabytes=512)` with `.function`, `.role`, `.log_group`.
- `infra.stacks.api_stack`: `ApiStack(scope, id, *, data, auth, **kwargs)`, `API_ROUTES`, `ApiRoute`, `ROUTES_WITH_REAL_HANDLERS`, `STUB_HANDLER`, `AUTH_MODE_CONTEXT_KEY = "auth_mode"`, `auth_mode_from_context(value) -> str`.
- `tests/infra/conftest.py` *(new)* gains `stacks_with_context`: a module fixture returning `build(extra_context) -> PortalStacks`, built like `portal_stacks` (later items use it for `-c agent_host=...`).

## 4. Tests (new, in `tests/`)
- `tests/infra/test_bundling.py` *(new)*: the bundle holds the code, `agents/prompts/critic.txt` and `prompts.lock`, never `__pycache__`; root files land at the root; a rebuild starts empty; a missing package stops the build naming it (fake installer, no network).
- `tests/infra/functions/test_stub_handler.py` *(new)*: echoes route and claims; works without an authorizer.
- `tests/infra/stacks/test_api_stack.py` *(new)*: HTTP API with one stage `api`; the six route keys; JWT authorizer on every route; one function and one role (no managed policy) per route; Python 3.11, tracing, the data environment; one log group per function with 14-day retention and `Delete`; `ApiUrl` output; `auth_mode=none` drops the authorizer; a typo fails; merged routes run `infra.functions.api.*` and the rest the stub.

## 5. Out of scope
- The handlers and `infra/functions/scope.py` (Linus, L1–L3). CloudFront (Michael, M4a). The ask and publish wiring (Y2a, Y2b). The async `/ask` fallback (Y2a §6).
- Custom domains, WAF, throttling plans, CORS (same origin through CloudFront).

Related: [[Build order]], [[Yaw - DevOps]], [[Workstreams]]
