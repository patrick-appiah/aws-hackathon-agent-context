---
tags: [build, spec, area/api]
id: L1
owner: Linus
status: ready
updated: 2026-10-14
---
# L1: scope from the token, and the `/summary` handler (spec)
> **The door everyone uses.** Every API handler builds the caller's `Scope` from the sign-in token here, and `/summary` is the first route on it. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after C1 is merged.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] §2 (architecture), §3 (code already built) and §7 (rules).
3. [[Linus - API, identity, blocker-analyst]]: the owner's brief. §1 and §2 are this item.
4. [[C1 - API and spine contracts - spec]]: the contracts this item uses (`SummaryResponse`, `ErrorResponse`, `ERROR_STATUS_CODES`, `summary_response`, the `auth_mode` setting). C1 must be **merged** first.
5. [[Build order]]: L1 depends on C1 only; L2, L3, L6 and Yaw's Y1 wait on it.
6. [[Yaw - DevOps]] (the HTTP API v2 JWT authorizer), [[Abdul - evals, Cognito, docs]] and [[Michael - DevOps]] (the Cognito groups and claims), [[Clement - front end]] (the front end sends the ID token).
7. `01 Decisions/`: [[2026-10-13 Scope from the token, enforced twice]] (D-010), [[2026-10-13 Metrics are code, only the blocker Q&A is agentic]] (D-001), [[2026-10-13 POC plus one target slice, target as 90-day roadmap]] (D-015); and `05 Workflow/`: [[Dev loop]], [[Working with AI assistants]], [[Handling security findings]].
8. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[Problem statement]], [[Judging rubric]], [[Pitch track grading rubric]], [[Hackathon guideline]]); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Linus. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. `infra/functions/scope.py` *(new)*: `scope_from_claims(claims, settings) -> Scope` and `scope_from_event(event, settings) -> Scope`, which turn the JWT claims API Gateway's HTTP API (v2) passes in `event["requestContext"]["authorizer"]["jwt"]["claims"]` into the `Scope` every handler uses. With `AUTH_MODE=none`, they return the demo user: a CFO by default, or the role in the new `DEMO_ROLE` setting.
2. `infra/functions/api.py` *(new)*: the shared response and error helpers, and the `summary(event, context)` Lambda handler for `GET /summary`.
3. The error body for the whole API: the core's exceptions mapped once to `ErrorResponse {error, detail}` with `ERROR_STATUS_CODES` (C1). `/summary` needs 401 and 403 already; L2 adds the routes that produce 400 and 404.
4. Coverage of the two new packages, and Linus's rows of `docs/DEVOPS_HANDOVER.md` and `HANDOFF.md` kept true.
5. **`DEMO_ROLE` (lead decision D2):** a setting `demo_role` in `config.py` (env `DEMO_ROLE`, default `"cfo"`, one of the `Role` values in `tools/models.py`, else `ValueError`), read **only** by `demo_scope` when `AUTH_MODE=none`. `config.py` is Patrick's file: this item's PR adds the setting and Patrick reviews it.

**Why:**
- Scope from the token, server-side, is the one rule every workstream touches (`ARCHITECTURE.md` §4, D-010). An entity lead must never see another entity's data, and the client must never be able to send its own scope.
- `/summary` is the one screen. Mildred's dashboard and the D1 18:00 walking skeleton need it live behind API Gateway (Yaw's Y1).
- One error mapping, written once, means every route answers errors in the contract body the front end parses (`api-error.ts`).
- H4's `decide` lets only a `delivery_lead` approve. Without Cognito the demo user would always be the CFO, so the approval beat couldn't be shown; `DEMO_ROLE=delivery_lead` with `AUTH_MODE=none` is the demo-only fallback for it (F5, F3b).

**Success means:**
- A CFO token gives `Scope(role="cfo", entity_ids=("*",))`; an E4 entity lead's token gives `entity_ids=("E4",)`; `"E2,E4"` gives two entities.
- No claims → `Unauthenticated` (401 `unauthorized`). Zero or two groups, an unknown group, a missing `sub`, `custom:tenant_id` or `custom:entity_ids`, a malformed entity ID, an empty entity list, or another tenant → `ScopeRefused` (403 `forbidden`).
- `AUTH_MODE=none` gives the demo user whatever the claims: `demo-cfo` with role `cfo` by default; `demo-delivery_lead` with role `delivery_lead` when `DEMO_ROLE=delivery_lead`. `DEMO_ROLE=admin` fails at start-up with `ValueError`.
- `summary` called with a fake HTTP API v2 event returns 200 and a body that validates as `SummaryResponse` (18,420 records reconciled for the CFO; only E4 for the E4 lead), and the contract error body otherwise.
- `uv run --locked pytest`: **243 passed** (C1's 213 + 30), coverage **97%**, with `api` and `auth` measured.

**Assumptions** (reconcile with the named owner before merging):
- C1 is merged exactly as on `feature/api-and-spine-contracts` (`tools/api_schema.py`, `config.AUTH_MODE_NONE`, `config.AUTH_MODE_COGNITO`, `Settings.auth_mode`).
- Cognito (Abdul + Michael, A2/M3*) puts **one** group per user in `cognito:groups` (`cfo`, `sponsor`, `delivery_lead`, `entity_lead`), `custom:tenant_id = "t-01"` and `custom:entity_ids` as a comma-separated string (`"*"`, `"E4"`, `"E2"`). The front end sends the **ID token** (custom claims are only in the ID token), and Yaw's authorizer audience is the app client ID.
- HTTP API (v2) passes a list claim as text, `"[entity_lead]"` (several groups: `"[cfo sponsor]"`). The code accepts that form and a real JSON list. **Verify on the first deployed call** (Review Focus 2).
- The POC serves one tenant, `settings.default_tenant_id` (`t-01`). Cross-tenant isolation is the roadmap (EVALS Q13).

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Where scope is built | `infra/functions/scope.py`, one function used by every handler (C2 gives `infra/functions/scope.py` to workstream 3) | Building scope inside each handler (six copies); in `tools/` (the core may not import `config`) |
| Zero or several groups | 403 `forbidden` (`ScopeRefused`). One group per user is the Cognito design | Picking the "highest" group (a silent widening of scope) |
| Missing claims dict | 401 `unauthorized` (`Unauthenticated`): nothing reached the handler, so the caller isn't signed in | 403 (the caller can't tell "sign in" from "not allowed") |
| A malformed entity ID or an unknown role in the token | 403 `forbidden`: the token is wrong, not the request | 400 `invalid_input` (blames the caller for server-side data) |
| Another tenant's token | 403 `forbidden`: this deployment serves `settings.default_tenant_id` only | Serving it (the CSV repository has one tenant, so a `t-02` token would read `t-01` data) |
| `AUTH_MODE=none` | The demo user (`demo-<role>`, every entity of the default tenant), whatever the claims; the role is `settings.demo_role`, `cfo` by default | Honouring claims when present (two behaviours in one mode) |
| How to demo approval without Cognito (lead decision D2) | `DEMO_ROLE` setting in `config.py`, validated against `Role`, used only by `demo_scope` | A second auth mode (`none-approver`); a role in the request (the client must never choose its scope); a hard-coded demo delivery lead |
| Error mapping | One ordered table `ERROR_CODE_BY_EXCEPTION` and one decorator `returns_contract_errors`. Unknown exceptions propagate: the Lambda fails and API Gateway answers 500 | A try/except per handler (drift); catching everything (hides bugs behind a 4xx) |
| Repository per request | `repository_for(tenant_id)`, cached per Lambda container (the artefacts don't change within a deployment) | A new `CsvRepository` per request (re-reads S3 on every call) |
| Serialisation | `model.model_dump_json(by_alias=True)`, so a `Verdict`'s `passed` goes out as `pass` (C1 Review Focus 3) | `json.dumps(model.model_dump())` (loses the alias) |

## 3. Shapes and behaviour
**`infra/functions/scope.py`:**
| Name | Signature / value | Behaviour |
|---|---|---|
| `claims_from_event` | `(event: dict) -> dict \| None` | `event["requestContext"]["authorizer"]["jwt"]["claims"]`, or `None` if any level is missing |
| `demo_scope` | `(settings: Settings) -> Scope` | `Scope(user_id=f"demo-{settings.demo_role}", role=settings.demo_role, tenant_id=settings.default_tenant_id, entity_ids=("*",))`; with the default it is `demo-cfo`, a CFO |
| `scope_from_claims` | `(claims: dict \| None, settings: Settings) -> Scope` | `AUTH_MODE=none` → `demo_scope`. Else: no claims → `Unauthenticated`; exactly one group from `cognito:groups` (list, or text `"[a b]"`) that is a `Role`; `sub`, `custom:tenant_id`, `custom:entity_ids` present; tenant equals `settings.default_tenant_id`; `custom:entity_ids` split on `,`, trimmed, at least one, each `*` or a valid entity ID. Any failure → `ScopeRefused` |
| `scope_from_event` | `(event: dict, settings: Settings) -> Scope` | `scope_from_claims(claims_from_event(event), settings)` |
| `Unauthenticated`, `ScopeRefused` | `PermissionError` subclasses | mapped to 401 `unauthorized` and 403 `forbidden` |

**`infra/functions/api.py` (this item's part):**
| Name | Behaviour |
|---|---|
| `json_response(status_code, model)` | `{"statusCode", "headers": {"content-type": "application/json"}, "body": model.model_dump_json(by_alias=True)}` (HTTP API v2 Lambda response) |
| `error_response(error_code, detail)` | `ErrorResponse` with the status from `ERROR_STATUS_CODES` |
| `returns_contract_errors(handler)` | `Unauthenticated` → 401 `unauthorized`; `ScopeRefused` → 403 `forbidden`; `OutOfScope` → 403 `out_of_scope`; `KeyError` → 404 `not_found`; `ValueError` (pydantic's `ValidationError` included) → 400 `invalid_input`. `detail` is the exception's first argument. Anything else propagates |
| `repository_for(tenant_id)` | `adapters.repository_from_settings(tenant_id)`, cached |
| `summary(event, context)` | `GET /summary` → 200 `SummaryResponse` from `tools.api_schema.summary_response(repository, scope)` |

**`config.py` (Patrick's file, added here):** `DEFAULT_DEMO_ROLE = "cfo"`, `DEMO_ROLES = get_args(Role)`, `Settings.demo_role: str` from env `DEMO_ROLE`; a value outside `DEMO_ROLES` raises `ValueError("DEMO_ROLE must be one of ...")` in `get_settings()`.

Entry point for Yaw: `infra.functions.api.summary`. Environment (`docs/DEVOPS_HANDOVER.md`): `ARTEFACT_BACKEND`, `ARTEFACTS_URI`, `AUTH_MODE` (C1's default is `cognito`, fail closed; the walking skeleton sets `none` explicitly until the AuthStack is live, then `cognito`), `DEFAULT_TENANT_ID`, and `DEMO_ROLE` only when `AUTH_MODE=none` (`delivery_lead` only to demo approval). Both `api.py` and `scope.py` are in `infra/functions/` *(new)*, which the bundle includes.

## 4. Tests
- `tests/infra/functions/test_scope.py` *(new)*, 18 tests: CFO (list form), E4 lead (HTTP API text form), two entities, no claims (`None` and `{}`), ten bad-claim cases (two groups as text and as a list, no group, unknown group, no tenant, no entities, no subject, malformed entity ID, empty entity list, another tenant), `AUTH_MODE=none` (the default demo CFO), `AUTH_MODE=none` with `demo_role="delivery_lead"`, and claims read from an HTTP API v2 event.
- `tests/test_config.py` (Patrick's), 2 more tests: `DEMO_ROLE` is one more entry in the default and environment-variable tables (`cfo`; `delivery_lead`), and `DEMO_ROLE=admin` raises `ValueError`.
- `tests/infra/functions/conftest.py` *(new)*: fixtures `cognito_mode` (pins `AUTH_MODE=cognito`, C1's default) and `demo_mode` (sets `AUTH_MODE=none`; C1 no longer defaults to it), each clearing the settings cache around the test, and `make_event` (builds a fake HTTP API v2 event). No AWS.
- `tests/infra/functions/test_api.py` *(new)*, 10 tests: `/summary` for the CFO and the E4 lead, 401 without a token, 403 with two groups, the demo CFO in `AUTH_MODE=none` (the `demo_mode` fixture), and each core exception becoming its contract error (5 cases).

## 5. Out of scope
- `/entity`, `/rows` (L2), `/ask`, `/publish`, `/approve` (L3).
- Verifying the token's signature: Yaw's JWT authorizer does it before the Lambda runs.
- Cognito itself (A2, M3*), the authorizer and routes (Y1), front-end sign-in (F3).
- Multi-tenant serving (roadmap, EVALS Q13).

Related: [[L1 - Scope from the token and the summary handler - plan]], [[Build order]], [[Linus - API, identity, blocker-analyst]]
