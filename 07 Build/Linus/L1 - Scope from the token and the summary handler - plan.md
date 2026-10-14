---
tags: [build, plan, area/api]
id: L1
owner: Linus
spec: "[[L1 - Scope from the token and the summary handler - spec]]"
status: ready
updated: 2026-10-14
---
# L1: scope from the token, and the `/summary` handler (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]]: the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[L1 - Scope from the token and the summary handler - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger.
3. [[Workstreams]] §3 and §7, and [[Linus - API, identity, blocker-analyst]] §1–§2.
4. [[C1 - API and spine contracts - spec]] §3 (the API models) and §5 (`AUTH_MODE`).
5. `01 Decisions/` D-001, D-010, D-015, and [[Working with AI assistants]].
6. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[Problem statement]], [[Judging rubric]], [[Pitch track grading rubric]], [[Hackathon guideline]]); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Linus. Never invent a name, a shape or a rule.

**Goal:** every handler gets its `Scope` from the token's claims through one tested function, and `GET /summary` serves the one screen with the contract error body. With `AUTH_MODE=none`, the demo user's role comes from the new `DEMO_ROLE` setting (lead decision D2), so the approval step can be demonstrated without Cognito.

**Architecture:** `infra/functions/scope.py` *(new)* turns claims into a `Scope`. `infra/functions/api.py` *(new)* is a thin HTTP adapter: scope → one builder from `tools/api_schema.py` → JSON. No business logic and no arithmetic in either (D-001). Both import `config`, so neither lives in `tools/`.

**Tech stack:** Python 3.11, pydantic 2, pytest, uv. AWS Lambda handlers for API Gateway HTTP API (payload format 2.0). No AWS calls in this item, and none in the tests.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (your clone of `Amali-Tech/cloud-9-hackathon`). Branch: **`feature/api-summary-and-scope`** from an up-to-date `develop` **after C1 is merged**.
- **Start state:** `uv run --locked pytest` → **213 passed**, `TOTAL` coverage **96%** (develop with C1 merged). If yours is higher because other items merged since, that's fine: write your count in the ledger as START; what must match is the number of tests each step adds. If it's lower, or C1's `tools/api_schema.py` is missing, stop.
- **`AUTH_MODE` defaults to `cognito`** (C1, fail closed). A test or a local run that needs the demo user sets `AUTH_MODE=none` explicitly (the `demo_mode` fixture, or `dataclasses.replace(get_settings(), auth_mode=AUTH_MODE_NONE)`); never change the default.
- **AWS:** `eu-west-1` only; Bedrock `eu.*` inference profiles only, never `global.*` (D-002). Synthetic data only. **No secrets** anywhere: code, tests, fixtures, the repo, the vault, Slack, commit messages.
- **Clean code (enforced by tests):** no single-character names anywhere (comprehensions, lambdas and `except ... as` included); no magic numbers or strings, so every limit, code and key is a named constant; settings only in `config.py`; domain constants only in `tools/constants.py`; descriptive names.
- **The core (`tools/`) never imports** boto3, Strands, `adapters`, `config` or `os` (`tests/test_architecture.py`).
- **Agents reach data only through `tools/agent_tools.py`.** Scope is never a tool argument and never comes from a request body, a query string or a model. Prompts live only in `agents/prompts/<agent>.txt`, versioned and locked (`uv run python scripts/lock_prompts.py`).
- **Never weaken a security rule** (the scope gate, the create-once ledger, the fail-closed critic, the `<evidence>` escaping) to make a test pass.
- **Tests** live in `tests/`, mirroring the code; run `uv run --locked pytest` from the repo root. Coverage must not drop below the start state. **No layout or "meta" guard tests**: test behaviour, not where files sit.
- **Git:** small commits, one per task, with the messages given. **No `Co-Authored-By` and no "Generated with" lines.** Never push to `develop` or `main`; the PR goes to `develop` after the owner's OK, and Patrick merges.
- **Stay in your folders** (`docs/TEAM_PLAN.md` §2, workstream 3: `infra/functions/api.py`, `infra/functions/scope.py`, `tests/infra/functions/` *(new)*, `tools/metrics.py`, `tools/queries.py`, `tools/agent_tools.py`, `tools/claims.py`, `agents/blocker_analyst.py` *(new)*, `agents/prompts/blocker_analyst.txt` *(new)*, `scripts/export_summary.py` *(new)*, the eval runner). Any other file this plan touches is named in its task, with the owner who must review it.
- **Thin handlers:** a handler calls `scope_from_event`, one builder from `tools/api_schema.py` and `json_response`. No `if` on business data, no arithmetic, no reshaping. A missing figure goes into `tools/metrics.py` with a pinned test (a separate change), never into `infra/functions/api.py`.
- **Shared files touched:** `pyproject.toml` (`addopts`: two `--cov` flags, each inserted directly before `--cov-report` so it merges cleanly with the single `--cov=infra/functions` that C2 adds), **Patrick's `config.py` and `tests/test_config.py`** (the `DEMO_ROLE` setting, lead decision D2: settings live only in `config.py`, so this item adds it there and Patrick reviews it in this PR), and Patrick's `docs/DEVOPS_HANDOVER.md` (your rows only). Patrick reviews all of them in the PR.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **Another tenant is refused, never served.** With one CSV tenant, a `t-02` token would otherwise read `t-01` data. Read `scope_from_claims`: the tenant check runs before the `Scope` is built.
2. **The claim format on a real token.** HTTP API v2 is documented to send `cognito:groups` as `"[entity_lead]"`. On the first deployed call (D1 18:00, with Yaw), log the claim **keys** and the group value once (never the token), confirm the 200, then remove the log line.
3. **`AUTH_MODE=none` is a fallback, set explicitly.** C1's default is `cognito`; the walking skeleton sets `AUTH_MODE=none` on purpose until Michael's AuthStack is live, then the summary Lambda's environment must say `AUTH_MODE=cognito` (or leave it unset), and `DEMO_ROLE` is then ignored. `DEMO_ROLE=delivery_lead` is only for demonstrating approval while the Cognito slice is off; with it, every caller is a delivery lead. Check Yaw's ApiStack environment, and say so in the PR.
4. **`KeyError` → 404 can hide a bug.** A `KeyError` from deep inside `metrics` would also come back as 404 `not_found`. Check the Lambda logs for `refused: not_found` on routes that shouldn't produce it.
5. **Error details leak nothing.** `detail` is the exception's own message: our messages name claims and entity IDs, never token contents. Read every `raise` in `infra/functions/scope.py`.

---

### Task 1: `infra/functions/scope.py`, the scope builder

**Files:**
- Create: `infra/__init__.py` *(new)* and `infra/functions/__init__.py` *(new; create if missing)*, `infra/functions/scope.py`, `tests/infra/functions/test_scope.py` *(new)* (the test folder is new; no `__init__.py` in `tests/`)
- Modify: `config.py` and `tests/test_config.py` (**Patrick's files**: one setting, `demo_role`; Patrick reviews it in this PR), `pyproject.toml` (one `--cov` flag, and `norecursedirs`: drop `"infra"`)

**Produces:** `config.Settings.demo_role: str` (env `DEMO_ROLE`, default `DEFAULT_DEMO_ROLE = "cfo"`, must be one of `DEMO_ROLES`, the values of `tools.models.Role`, else `ValueError`); `infra.functions.scope.claims_from_event(event: dict) -> dict | None`, `demo_scope(settings: Settings) -> Scope`, `scope_from_claims(claims: dict | None, settings: Settings) -> Scope`, `scope_from_event(event: dict, settings: Settings) -> Scope`, exceptions `Unauthenticated` and `ScopeRefused` (both `PermissionError`), constants `GROUPS_CLAIM`, `TENANT_CLAIM`, `ENTITY_IDS_CLAIM`, `USER_ID_CLAIM`, `DEMO_USER_ID_PREFIX`. **Consumes:** `config.AUTH_MODE_NONE`, `config.Settings` (C1), `tools.models.Role`, `Scope`, `validate_entity_id`, `tools.constants.ALL_ENTITIES_WILDCARD`. **Consumed by:** Task 2, L2, L3, P3 (`demo_scope(settings)` for the local runner), Clement's F3b and F5 (the `AUTH_MODE=none` demo path).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/api-summary-and-scope
mkdir -p .superpowers && printf '# Ledger: L1 scope from the token and the summary handler\n' > .superpowers/ledger-L1.md
```
Expected: `TOTAL ... 96%` and `213 passed` (or your START, see Global Constraints).

- [ ] **Step 2: Write the failing `DEMO_ROLE` tests.** `tests/test_config.py` is Patrick's file: change only these three places.
  - In `NEW_SETTING_DEFAULTS`, directly after the line `    "user_pool_id": None, "user_pool_client_id": None,`, add (on its own line, so L6's edit of that line still applies):
```python
    "demo_role": "cfo",
```
  - In `ENVIRONMENT_VARIABLES`, directly after the line `    "user_pool_id": ("USER_POOL_ID", "eu-west-1_example"), "user_pool_client_id": ("USER_POOL_CLIENT_ID", "client"),`, add:
```python
    "demo_role": ("DEMO_ROLE", "delivery_lead"),
```
  - Append at the end of the file (two blank lines before it):
```python
def test_an_unknown_demo_role_is_refused(monkeypatch):
    monkeypatch.setenv("DEMO_ROLE", "admin")
    with pytest.raises(ValueError, match="DEMO_ROLE"):
        config.get_settings()
```

- [ ] **Step 3: Run them and watch them fail**
```bash
uv run --locked pytest tests/test_config.py --no-cov 2>&1 | tail -1
uv run --locked pytest tests/test_config.py --no-cov 2>&1 | grep -E "^E  " | sort -u
```
Expected: `3 failed, 9 passed`; the `E` lines are `E   AttributeError: 'Settings' object has no attribute 'demo_role'`, `E       AttributeError: 'Settings' object has no attribute 'demo_role'` and `E       Failed: DID NOT RAISE ValueError`.

- [ ] **Step 4: Implement the setting.** In `config.py` (Patrick's file), make exactly these four changes:
  - directly after the line `from pathlib import Path`, add:
```python
from typing import get_args

from tools.models import Role
```
  - directly after the line that starts `DEFAULT_AUTH_MODE = AUTH_MODE_COGNITO` (it ends with the comment `# fail closed: a stack that forgets AUTH_MODE serves no one`), add:
```python
DEFAULT_DEMO_ROLE = "cfo"                         # the AUTH_MODE=none user's role; delivery_lead only to demo approval
DEMO_ROLES = get_args(Role)
```
  - in `class Settings`, directly after `    user_pool_client_id: str | None`, add the field `    demo_role: str`;
  - directly above `@lru_cache(maxsize=1)`, add the function below, and in `get_settings()` directly after `        user_pool_client_id=os.environ.get("USER_POOL_CLIENT_ID"),` add `        demo_role=_demo_role(),`:
```python
def _demo_role() -> str:
    demo_role = _env("DEMO_ROLE", DEFAULT_DEMO_ROLE)
    if demo_role not in DEMO_ROLES:
        raise ValueError(f"DEMO_ROLE must be one of {DEMO_ROLES}, not {demo_role!r}")
    return demo_role
```
`config.py` may import `tools.models`: the rule is the other way round (the core never imports `config`), and `tools/models.py` imports neither `config` nor `os`.

- [ ] **Step 5: Run them and watch them pass**
```bash
uv run --locked pytest tests/test_config.py --no-cov 2>&1 | tail -1
```
Expected: `12 passed`.

- [ ] **Step 6: Write the failing scope test.** Create `tests/infra/functions/test_scope.py`:
```python
"""Scope from the sign-in token (infra/functions/scope.py): group, tenant and entity claims, or the AUTH_MODE=none demo user."""
import dataclasses

import pytest

from infra.functions.scope import (ScopeRefused, Unauthenticated, claims_from_event, demo_scope, scope_from_claims,
                        scope_from_event)
from config import AUTH_MODE_COGNITO, AUTH_MODE_NONE, DEFAULT_TENANT_ID, get_settings

CFO_CLAIMS = {"sub": "user-cfo", "cognito:groups": ["cfo"], "custom:tenant_id": DEFAULT_TENANT_ID,
              "custom:entity_ids": "*"}
ENTITY_FOUR_LEAD_CLAIMS = {"sub": "user-e4-lead", "cognito:groups": "[entity_lead]",
                           "custom:tenant_id": DEFAULT_TENANT_ID, "custom:entity_ids": "E4"}
OTHER_TENANT_ID = "t-02"


@pytest.fixture
def cognito_settings():
    return dataclasses.replace(get_settings(), auth_mode=AUTH_MODE_COGNITO)


def test_a_cfo_token_gives_every_entity(cognito_settings):
    scope = scope_from_claims(CFO_CLAIMS, cognito_settings)
    assert (scope.user_id, scope.role, scope.tenant_id, scope.entity_ids) == ("user-cfo", "cfo", DEFAULT_TENANT_ID,
                                                                              ("*",))


def test_an_entity_lead_token_in_the_http_api_string_form_gives_one_entity(cognito_settings):
    scope = scope_from_claims(ENTITY_FOUR_LEAD_CLAIMS, cognito_settings)
    assert (scope.role, scope.entity_ids) == ("entity_lead", ("E4",))


def test_a_comma_separated_entity_claim_gives_several_entities(cognito_settings):
    scope = scope_from_claims({**ENTITY_FOUR_LEAD_CLAIMS, "custom:entity_ids": "E2, E4"}, cognito_settings)
    assert scope.entity_ids == ("E2", "E4")


@pytest.mark.parametrize("missing_claims", [None, {}])
def test_no_claims_is_unauthenticated(cognito_settings, missing_claims):
    with pytest.raises(Unauthenticated):
        scope_from_claims(missing_claims, cognito_settings)


@pytest.mark.parametrize("bad_claims", [
    {**CFO_CLAIMS, "cognito:groups": "[cfo sponsor]"},
    {**CFO_CLAIMS, "cognito:groups": ["cfo", "sponsor"]},
    {key: value for key, value in CFO_CLAIMS.items() if key != "cognito:groups"},
    {**CFO_CLAIMS, "cognito:groups": "[admin]"},
    {key: value for key, value in CFO_CLAIMS.items() if key != "custom:tenant_id"},
    {key: value for key, value in CFO_CLAIMS.items() if key != "custom:entity_ids"},
    {key: value for key, value in CFO_CLAIMS.items() if key != "sub"},
    {**ENTITY_FOUR_LEAD_CLAIMS, "custom:entity_ids": "E-4"},
    {**ENTITY_FOUR_LEAD_CLAIMS, "custom:entity_ids": " , "},
    {**CFO_CLAIMS, "custom:tenant_id": OTHER_TENANT_ID},
], ids=["two_groups_as_text", "two_groups_as_list", "no_group", "unknown_group", "no_tenant", "no_entities",
        "no_subject", "malformed_entity_id", "empty_entity_list", "another_tenant"])
def test_bad_claims_are_refused(cognito_settings, bad_claims):
    with pytest.raises(ScopeRefused):
        scope_from_claims(bad_claims, cognito_settings)


def test_auth_mode_none_gives_the_demo_cfo_whatever_the_claims():
    settings = dataclasses.replace(get_settings(), auth_mode=AUTH_MODE_NONE)
    assert scope_from_claims(None, settings) == scope_from_claims(ENTITY_FOUR_LEAD_CLAIMS, settings) == demo_scope(
        settings)
    assert (demo_scope(settings).user_id, demo_scope(settings).role, demo_scope(settings).entity_ids) == (
        "demo-cfo", "cfo", ("*",))


def test_auth_mode_none_with_demo_role_delivery_lead_gives_a_demo_delivery_lead():
    settings = dataclasses.replace(get_settings(), auth_mode=AUTH_MODE_NONE, demo_role="delivery_lead")
    assert (scope_from_claims(None, settings).user_id, scope_from_claims(None, settings).role) == (
        "demo-delivery_lead", "delivery_lead")


def test_claims_come_from_the_http_api_v2_authorizer_context(cognito_settings):
    event = {"requestContext": {"authorizer": {"jwt": {"claims": CFO_CLAIMS, "scopes": None}}}}
    assert claims_from_event(event) == CFO_CLAIMS
    assert scope_from_event(event, cognito_settings) == scope_from_claims(CFO_CLAIMS, cognito_settings)
    assert claims_from_event({"requestContext": {}}) is None
    assert claims_from_event({}) is None
```

- [ ] **Step 7: Run it and watch it fail**
```bash
uv run --locked pytest tests/infra/functions/test_scope.py --no-cov 2>&1 | grep -E "^E  "
```
Expected: `E   ModuleNotFoundError: No module named 'infra.functions'` (an error at collection; nothing ran; `infra/` holds only a README, so Python sees a namespace package).

- [ ] **Step 8: Implement.** Create `infra/__init__.py` (docstring only: `"""Infrastructure and Lambda glue. This package must not import aws_cdk (a handler import never pulls CDK)."""`) and `infra/functions/__init__.py` (docstring only: `"""Lambda and Step Functions handlers, and the user's Scope built server-side from the sign-in token's claims (ARCHITECTURE.md §4)."""`), each only if missing (whichever item lands first creates them). Create `infra/functions/scope.py`:
```python
"""Scope from the sign-in token: the only place a Scope is built for a request (ARCHITECTURE.md §4).

API Gateway's HTTP API (v2) JWT authorizer has already checked the Cognito ID token's signature, issuer, audience and
expiry. It passes the token's claims in event["requestContext"]["authorizer"]["jwt"]["claims"]:
  cognito:groups     exactly one of the four roles. HTTP API sends a list claim as text, "[entity_lead]".
  custom:tenant_id   the tenant, e.g. "t-01". The POC serves one tenant: settings.default_tenant_id.
  custom:entity_ids  a comma-separated string: "E4", "E2,E4" or "*" (Cognito custom attributes are strings).
  sub                the user ID.
AUTH_MODE=none ignores the claims and gives the demo user: settings.demo_role (DEMO_ROLE, default cfo) over every
entity (the fallback if the Cognito slice slips, D-015). DEMO_ROLE=delivery_lead is a demo-only way to show approval.
The client never sends scope, and a model never supplies it.
"""
import re
from typing import get_args

from config import AUTH_MODE_NONE, Settings
from tools.constants import ALL_ENTITIES_WILDCARD
from tools.models import Role, Scope, validate_entity_id

GROUPS_CLAIM = "cognito:groups"
TENANT_CLAIM = "custom:tenant_id"
ENTITY_IDS_CLAIM = "custom:entity_ids"
USER_ID_CLAIM = "sub"
REQUIRED_CLAIMS = (USER_ID_CLAIM, TENANT_CLAIM, ENTITY_IDS_CLAIM)
ENTITY_IDS_SEPARATOR = ","
HTTP_API_LIST_BRACKETS = "[]"
GROUP_SEPARATORS = re.compile(r"[\s,]+")
ROLES = frozenset(get_args(Role))
DEMO_USER_ID_PREFIX = "demo-"


class Unauthenticated(PermissionError):
    """No token claims reached the handler (HTTP 401)."""


class ScopeRefused(PermissionError):
    """The token's claims don't describe exactly one valid scope (HTTP 403 forbidden)."""


def claims_from_event(event: dict) -> dict | None:
    """The JWT claims an HTTP API (v2) JWT authorizer put on the event, or None if there are none."""
    authorizer = (event.get("requestContext") or {}).get("authorizer") or {}
    return (authorizer.get("jwt") or {}).get("claims")


def demo_scope(settings: Settings) -> Scope:
    """The AUTH_MODE=none user: settings.demo_role (a CFO by default), seeing every entity of the default tenant."""
    return Scope(user_id=f"{DEMO_USER_ID_PREFIX}{settings.demo_role}", role=settings.demo_role,
                 tenant_id=settings.default_tenant_id,
                 entity_ids=(ALL_ENTITIES_WILDCARD,))


def _groups(raw_groups) -> list[str]:
    if isinstance(raw_groups, (list, tuple)):
        return [str(group) for group in raw_groups]
    if isinstance(raw_groups, str):
        return [group for group in GROUP_SEPARATORS.split(raw_groups.strip(HTTP_API_LIST_BRACKETS)) if group]
    return []


def _entity_ids(raw_entity_ids: str) -> tuple[str, ...]:
    entity_ids = tuple(part.strip() for part in raw_entity_ids.split(ENTITY_IDS_SEPARATOR) if part.strip())
    if not entity_ids:
        raise ScopeRefused(f"{ENTITY_IDS_CLAIM} lists no entity")
    try:
        for entity_id in entity_ids:
            if entity_id != ALL_ENTITIES_WILDCARD:
                validate_entity_id(entity_id)
    except ValueError as error:
        raise ScopeRefused(f"{ENTITY_IDS_CLAIM}: {error}") from error
    return entity_ids


def scope_from_claims(claims: dict | None, settings: Settings) -> Scope:
    """The Scope for a request. Raises Unauthenticated (401) or ScopeRefused (403)."""
    if settings.auth_mode == AUTH_MODE_NONE:
        return demo_scope(settings)
    if not claims:
        raise Unauthenticated("no token claims: sign in and send the ID token")
    groups = _groups(claims.get(GROUPS_CLAIM))
    if len(groups) != 1:
        raise ScopeRefused(f"a user needs exactly one group in {GROUPS_CLAIM}, this token has {len(groups)}")
    role = groups[0]
    if role not in ROLES:
        raise ScopeRefused(f"{role!r} is not a portal role")
    missing = [claim_name for claim_name in REQUIRED_CLAIMS if not claims.get(claim_name)]
    if missing:
        raise ScopeRefused(f"the token has no {', '.join(missing)} claim")
    tenant_id = str(claims[TENANT_CLAIM])
    if tenant_id != settings.default_tenant_id:
        raise ScopeRefused(f"tenant {tenant_id} is not served by this deployment")
    return Scope(user_id=str(claims[USER_ID_CLAIM]), role=role, tenant_id=tenant_id,
                 entity_ids=_entity_ids(str(claims[ENTITY_IDS_CLAIM])))


def scope_from_event(event: dict, settings: Settings) -> Scope:
    """The Scope for an API Gateway HTTP API (v2) event."""
    return scope_from_claims(claims_from_event(event), settings)
```

- [ ] **Step 9: Run it and watch it pass**
```bash
uv run --locked pytest tests/infra/functions/test_scope.py --no-cov 2>&1 | tail -1
```
Expected: `18 passed`.

- [ ] **Step 10: Measure the new package, and let pytest collect `tests/infra/` *(new)*.** In `pyproject.toml`, in `addopts`, insert `--cov=infra/functions ` (with its trailing space) directly before `--cov-report` if it is missing (another item may already have added it: then check it is there). In `norecursedirs`, drop `"infra"` (it would skip `tests/infra/`) and keep the rest. Don't rewrite the rest of the lines: C2's other items make the same two edits, and the first to land wins.

- [ ] **Step 11: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra tests/infra/functions pyproject.toml config.py tests/test_config.py
git commit -m "Build the user's scope from the sign-in token's claims; AUTH_MODE=none gives the DEMO_ROLE demo user (D-010)"
```
Expected: `233 passed` (START + 20), `TOTAL ... 96%` (`infra/functions/scope.py` is fully covered, so `skip-covered` doesn't list it).

**Task done when:** `uv run --locked pytest tests/infra/functions/test_scope.py tests/test_config.py --no-cov` prints `30 passed`; `git log -1 --format=%s` shows the commit above; `git show --stat HEAD` lists only `infra/__init__.py`, `infra/functions/__init__.py`, `infra/functions/scope.py`, `tests/infra/functions/test_scope.py`, `config.py`, `tests/test_config.py` and `pyproject.toml`.

### Task 2: `infra/functions/api.py`, the error body and `GET /summary`

**Files:**
- Create: `infra/functions/api.py`, `tests/infra/functions/conftest.py` *(new)*, `tests/infra/functions/test_api.py` *(new)*
- Modify: `pyproject.toml` (check only: `--cov=infra/functions` is there from Task 1)

**Produces:** `infra.functions.api.summary(event: dict, context: object) -> dict`; helpers `json_response(status_code: int, model: BaseModel) -> dict`, `error_response(error_code: str, detail: str) -> dict`, `returns_contract_errors(handler: LambdaHandler) -> LambdaHandler`, `repository_for(tenant_id: str) -> ArtefactRepository`; constants `HTTP_OK`, `JSON_HEADERS`, `ERROR_CODE_BY_EXCEPTION`; the type alias `LambdaHandler = Callable[..., dict]`. Test fixtures `cognito_mode`, `demo_mode` (`AUTH_MODE=none`) and `make_event` (in `tests/infra/functions/conftest.py`). **Consumes:** Task 1; `tools.api_schema.summary_response`, `ErrorResponse`, `ERROR_STATUS_CODES`, `ERROR_UNAUTHORIZED`, `ERROR_FORBIDDEN`, `ERROR_NOT_FOUND` (C1); `tools.agent_tools.ERROR_INVALID_INPUT`, `ERROR_OUT_OF_SCOPE`; `adapters.repository_from_settings`. **Consumed by:** L2, L3, Yaw (Y1: `infra.functions.api.summary`), Mildred (F1/F2).

- [ ] **Step 1: The test fixtures.** Create `tests/infra/functions/conftest.py`:
```python
"""Fake API Gateway HTTP API (v2) events and the Cognito sign-in mode, for the handler tests. No AWS."""
import json

import pytest

from config import AUTH_MODE_COGNITO, AUTH_MODE_NONE, get_settings


def _settings_with_auth_mode(monkeypatch, auth_mode: str):
    """Handlers read get_settings(): pin AUTH_MODE for one test, then clear the cache again."""
    monkeypatch.setenv("AUTH_MODE", auth_mode)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def cognito_mode(monkeypatch):
    """AUTH_MODE=cognito (also C1's default; pinned so a developer's shell can't change the test)."""
    yield from _settings_with_auth_mode(monkeypatch, AUTH_MODE_COGNITO)


@pytest.fixture
def demo_mode(monkeypatch):
    """AUTH_MODE=none: the demo user from DEMO_ROLE (a CFO by default), whatever the token says."""
    yield from _settings_with_auth_mode(monkeypatch, AUTH_MODE_NONE)


@pytest.fixture
def make_event():
    """An HTTP API v2 event as API Gateway sends it to Lambda, with the JWT authorizer's claims when given."""
    def build_event(claims: dict | None = None, path_parameters: dict | None = None,
                    query: dict | None = None, body: dict | str | None = None) -> dict:
        request_context = {"http": {"method": "GET" if body is None else "POST"}}
        if claims is not None:
            request_context["authorizer"] = {"jwt": {"claims": claims, "scopes": None}}
        event = {"version": "2.0", "requestContext": request_context, "isBase64Encoded": False}
        if path_parameters is not None:
            event["pathParameters"] = path_parameters
        if query is not None:
            event["queryStringParameters"] = query
        if body is not None:
            event["body"] = body if isinstance(body, str) else json.dumps(body)
        return event
    return build_event
```

- [ ] **Step 2: Write the failing test.** Create `tests/infra/functions/test_api.py`:
```python
"""The API handlers (infra/functions/api.py) called with fake HTTP API v2 events: scope from the token, contract bodies."""
import json

import pytest

from api import handlers
from config import DEFAULT_TENANT_ID
from tools.api_schema import ERROR_STATUS_CODES, ErrorResponse, SummaryResponse

CFO_CLAIMS = {"sub": "user-cfo", "cognito:groups": "[cfo]", "custom:tenant_id": DEFAULT_TENANT_ID,
              "custom:entity_ids": "*"}
ENTITY_FOUR_LEAD_CLAIMS = {"sub": "user-e4-lead", "cognito:groups": "[entity_lead]",
                           "custom:tenant_id": DEFAULT_TENANT_ID, "custom:entity_ids": "E4"}
TWO_GROUP_CLAIMS = {**CFO_CLAIMS, "cognito:groups": "[cfo sponsor]"}
EXPECTED_RECORDS_RECONCILED = 18420
HTTP_OK = 200


def body_of(response: dict) -> dict:
    return json.loads(response["body"])


def assert_error(response: dict, error_code: str):
    assert response["statusCode"] == ERROR_STATUS_CODES[error_code]
    assert ErrorResponse.model_validate_json(response["body"]).error == error_code


def test_summary_for_the_cfo_is_the_whole_programme(cognito_mode, make_event):
    response = handlers.summary(make_event(claims=CFO_CLAIMS), None)
    assert response["statusCode"] == HTTP_OK and response["headers"]["content-type"] == "application/json"
    summary = SummaryResponse.model_validate_json(response["body"])
    assert summary.overall.records_reconciled == EXPECTED_RECORDS_RECONCILED
    assert summary.final_cutover.entity_id == "E4"


def test_summary_for_the_e4_lead_shows_only_e4(cognito_mode, make_event):
    response = handlers.summary(make_event(claims=ENTITY_FOUR_LEAD_CLAIMS), None)
    assert [entity["entity_id"] for entity in body_of(response)["entities"]] == ["E4"]


def test_summary_without_a_token_is_401(cognito_mode, make_event):
    assert_error(handlers.summary(make_event(), None), "unauthorized")


def test_summary_with_two_groups_is_403_forbidden(cognito_mode, make_event):
    assert_error(handlers.summary(make_event(claims=TWO_GROUP_CLAIMS), None), "forbidden")


def test_summary_in_auth_mode_none_serves_the_demo_cfo(demo_mode, make_event):
    response = handlers.summary(make_event(), None)
    assert response["statusCode"] == HTTP_OK and body_of(response)["overall"]["records_reconciled"] == \
        EXPECTED_RECORDS_RECONCILED


@pytest.mark.parametrize("error, error_code", [
    (handlers.Unauthenticated("no token"), "unauthorized"), (handlers.ScopeRefused("two groups"), "forbidden"),
    (handlers.OutOfScope("entity E2"), "out_of_scope"), (KeyError("unknown entity: E9"), "not_found"),
    (ValueError("not an entity id: 'E-4'"), "invalid_input"),
])
def test_each_core_exception_becomes_its_contract_error(error, error_code):
    def failing_handler(event, context):
        raise error
    response = handlers.returns_contract_errors(failing_handler)({}, None)
    assert_error(response, error_code)
    assert body_of(response)["detail"] == error.args[0]
```

- [ ] **Step 3: Run it and watch it fail**
```bash
uv run --locked pytest tests/infra/functions/test_api.py --no-cov 2>&1 | grep -E "^E  "
```
Expected: `E   ModuleNotFoundError: No module named 'infra.functions.api'`.

- [ ] **Step 4: Implement.** `infra/__init__.py` and `infra/functions/__init__.py` already exist from Task 1. Create `infra/functions/api.py`:
```python
"""API Gateway HTTP API (v2) Lambda handlers: thin adapters from HTTP to the core (docs/TEAM_PLAN.md §3, D-021).

Every handler does the same three things:
  1. the scope from the token's claims (infra/functions/scope.py), never from the body or the query string;
  2. one builder from tools/api_schema.py, which calls tools/metrics.py and tools/queries.py;
  3. the contract model as JSON, or the contract error body ErrorResponse {error, detail}.
No business logic and no arithmetic here (D-001). DevOps entry points: infra.functions.api:<route> (docs/DEVOPS_HANDOVER.md).
"""
import functools
import logging
from typing import Callable

from pydantic import BaseModel

from adapters import repository_from_settings
from infra.functions.scope import ScopeRefused, Unauthenticated, scope_from_event
from config import get_settings
from tools.agent_tools import ERROR_INVALID_INPUT, ERROR_OUT_OF_SCOPE
from tools.api_schema import (ERROR_FORBIDDEN, ERROR_NOT_FOUND, ERROR_STATUS_CODES, ERROR_UNAUTHORIZED, ErrorResponse,
                              summary_response)
from tools.models import OutOfScope
from tools.ports import ArtefactRepository

HTTP_OK = 200
JSON_HEADERS = {"content-type": "application/json"}
# The core's exceptions and the contract error each becomes, most specific first (ErrorResponse, D-021).
ERROR_CODE_BY_EXCEPTION: tuple[tuple[type[Exception], str], ...] = (
    (Unauthenticated, ERROR_UNAUTHORIZED),
    (ScopeRefused, ERROR_FORBIDDEN),
    (OutOfScope, ERROR_OUT_OF_SCOPE),
    (KeyError, ERROR_NOT_FOUND),
    (ValueError, ERROR_INVALID_INPUT),   # pydantic's ValidationError included
)
LambdaHandler = Callable[..., dict]   # (event: dict, context: object) -> dict, the Lambda handler shape
logger = logging.getLogger(__name__)


def json_response(status_code: int, model: BaseModel) -> dict:
    """An HTTP API (v2) Lambda response. by_alias=True so a Verdict's `passed` goes out as `pass`."""
    return {"statusCode": status_code, "headers": JSON_HEADERS, "body": model.model_dump_json(by_alias=True)}


def error_response(error_code: str, detail: str) -> dict:
    return json_response(ERROR_STATUS_CODES[error_code], ErrorResponse(error=error_code, detail=detail))


def _detail(error: Exception) -> str:
    return str(error.args[0]) if error.args else type(error).__name__


def returns_contract_errors(handler: LambdaHandler) -> LambdaHandler:
    """Turn the core's exceptions into the contract error body. Anything else propagates (API Gateway sends 500)."""
    @functools.wraps(handler)
    def guarded_handler(event: dict, context: object) -> dict:
        try:
            return handler(event, context)
        except tuple(exception_type for exception_type, _code in ERROR_CODE_BY_EXCEPTION) as error:
            error_code = next(code for exception_type, code in ERROR_CODE_BY_EXCEPTION
                              if isinstance(error, exception_type))
            logger.info("%s refused: %s %s", handler.__name__, error_code, type(error).__name__)
            return error_response(error_code, _detail(error))
    return guarded_handler


@functools.lru_cache(maxsize=None)
def repository_for(tenant_id: str) -> ArtefactRepository:
    """One repository per tenant per Lambda container: the artefacts don't change within a deployment."""
    return repository_from_settings(tenant_id)


@returns_contract_errors
def summary(event: dict, context: object) -> dict:
    """GET /summary: the one screen, limited to the caller's scope."""
    scope = scope_from_event(event, get_settings())
    return json_response(HTTP_OK, summary_response(repository_for(scope.tenant_id), scope))
```

- [ ] **Step 5: Run it and watch it pass**
```bash
uv run --locked pytest tests/infra/functions/test_api.py --no-cov 2>&1 | tail -1
```
Expected: `10 passed`.

- [ ] **Step 6: Check the measurement.** In `pyproject.toml`, in `addopts`, check `--cov=infra/functions` is there (Task 1 added it); `infra/functions/api.py` is covered by it.

- [ ] **Step 7: Guards, full suite and commit**
```bash
uv run --locked pytest tests/test_architecture.py tests/test_code_style.py --no-cov 2>&1 | tail -1
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra tests/infra/functions pyproject.toml
git commit -m "GET /summary handler: scope from the token, the contract error body for every route (D-021)"
```
Expected: the guards `15 passed`; then `243 passed` (START + 30), `TOTAL ... 97%`.

**Task done when:** `uv run --locked pytest tests/infra/functions --no-cov` prints `28 passed`; `TOTAL` coverage is 97% or more; the commit is on the branch.

### Task 3: Keep the handover and HANDOFF true

**Files:**
- Modify: `docs/DEVOPS_HANDOVER.md` (Patrick's file; your rows only), `HANDOFF.md` (your line only)

- [ ] **Step 1: `docs/DEVOPS_HANDOVER.md`.** One exact replacement and one check:
  - In the `summary`, `entity`, `rows` row, replace `` `infra.functions.api.summary` / `entity` / `rows` *(planned)* `` with `` `infra.functions.api.summary` (built, L1) / `entity` / `rows` *(planned)* ``.
  - In "Bundling", no edit: C2 already lists `infra/__init__.py` and `infra/functions/` *(new)* in the Lambda asset, and `scope.py` is in it. Check with `grep -n "infra/functions" docs/DEVOPS_HANDOVER.md`, which must print the bundling line.
- [ ] **Step 2: `HANDOFF.md`.** Under "What's real", directly **above** the line `- TODO: agent loop, critic, ledger, approval flow, as each lands.`, add:
```markdown
- `GET /summary` (`infra/functions/api.py`): the scope comes from the Cognito ID token's claims (`infra/functions/scope.py`: exactly one group, `custom:tenant_id`, `custom:entity_ids`), never from the request. Tested with fake API Gateway HTTP API v2 events. `AUTH_MODE=none` serves a demo CFO and is only the fallback if the Cognito slice slips.
- AUTH_MODE=none with DEMO_ROLE=delivery_lead is a demo-only fallback for the approval step if the Cognito slice is off
```
- [ ] **Step 3: Doc guards, full suite and commit**
```bash
uv run --locked pytest tests/test_dependencies.py tests/test_code_style.py --no-cov 2>&1 | tail -1
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add docs/DEVOPS_HANDOVER.md HANDOFF.md
git commit -m "Handover and HANDOFF: the summary handler is built"
```
Expected: `15 passed`; then `243 passed`, `TOTAL ... 97%`.

**Task done when:** `grep -c "built, L1" docs/DEVOPS_HANDOVER.md` prints `1`; `grep -c "infra/functions/scope.py" HANDOFF.md` prints `1`; `grep -c "DEMO_ROLE=delivery_lead" HANDOFF.md` prints `1`; the suite is still `243 passed`.

### Task 4: Review, then PR (after Linus's OK)
- [ ] **Step 1:** Work through the Review Focus by hand; write each result in the ledger. Line 2 waits for the first deployed call: write "pending Y1" and do it with Yaw.
- [ ] **Step 2:** `git diff develop --stat` lists only: `infra/__init__.py`, `infra/functions/__init__.py`, `infra/functions/scope.py`, `infra/functions/api.py`, `tests/infra/functions/test_scope.py`, `tests/infra/functions/conftest.py`, `tests/infra/functions/test_api.py`, `config.py`, `tests/test_config.py`, `pyproject.toml`, `docs/DEVOPS_HANDOVER.md`, `HANDOFF.md`. Expected: `12 files changed`.
- [ ] **Step 3:** A fresh reviewer (a person, or an agent with no prior context) reviews the diff against the spec. Fix critical and important findings test-first; list minor ones in the PR.
- [ ] **Step 4: With the OK only:** `git push -u origin feature/api-summary-and-scope`; open the PR to `develop`, titled "Scope from the token and the /summary handler (L1)". The body: what changed, `243 passed` and the coverage, the rulings from the ledger, "Patrick: `config.py` and `tests/test_config.py` gain the `DEMO_ROLE` setting (lead decision D2), please review", and "Michael: please add `infra/functions` to the bandit paths in the Jenkinsfile". No attribution lines.
- [ ] **Step 5:** Set L1's row in [[Build order]] to `in review (PR #nn)`; tell Yaw the entry point is `infra.functions.api.summary` and the bundle is `infra/functions/` (scope.py is in it); tell Mildred `/summary` is ready for the walking skeleton; tell Clement and Patrick `DEMO_ROLE` exists (F3b, F5 and P3 use it).

**Task done when:** the PR is open to `develop` with the test count in its body, and L1's [[Build order]] row says `in review (PR #nn)`.

## Done means (checklist)
- [ ] `uv run --locked pytest` on the branch prints `243 passed` (START + 30) and `TOTAL` 97% or more. *Verify:* run it from the repo root.
- [ ] `uv run --locked pytest tests/infra/functions/test_scope.py --no-cov` prints `18 passed`, `tests/infra/functions/test_api.py` prints `10 passed`, and `tests/test_config.py` prints `12 passed`. *Verify:* run all three.
- [ ] `DEMO_ROLE` works and refuses typos. *Verify:* `DEMO_ROLE=delivery_lead uv run python -c "from infra.functions.scope import demo_scope; from config import get_settings; print(demo_scope(get_settings()).role)"` prints `delivery_lead`, and `DEMO_ROLE=admin uv run python -c "import config; config.get_settings()" 2>&1 | tail -1` prints `ValueError: DEMO_ROLE must be one of ('cfo', 'sponsor', 'delivery_lead', 'entity_lead'), not 'admin'`.
- [ ] `grep -n "def scope_from_claims\|def scope_from_event" infra/functions/scope.py` shows both functions, and `grep -n "^def summary" infra/functions/api.py` shows the handler. *Verify:* run the greps.
- [ ] `docs/DEVOPS_HANDOVER.md` says `infra.functions.api.summary` is built, and its Bundling section lists `infra/functions/`. *Verify:* `grep -n "infra/functions" docs/DEVOPS_HANDOVER.md`.
- [ ] The PR to `develop` is open (or merged), with no `Co-Authored-By` or "Generated with" line. *Verify:* `gh pr view <nn> --json state,body` and `git log develop..HEAD --format=%B | grep -ci "co-authored"` prints `0`.
- [ ] [[Build order]] row L1 shows `in review (PR #nn)` or `merged`. *Verify:* open the note.

## Never
- Read scope, role, tenant or entities from the request body or the query string.
- Fall back to `AUTH_MODE=none` on an unknown or missing setting (C1 defaults to `cognito` and makes a typo fail loudly; keep both). The same for `DEMO_ROLE`: an unknown role is a `ValueError`, never a silent CFO.
- Read `demo_role` anywhere but `demo_scope`, or let it change a Cognito-mode scope.
- Catch every exception in a handler to return a 4xx.
- Do arithmetic or reshape a figure in `infra/functions/`.
- Push to `develop` or `main`, or add attribution lines.

Related: [[L1 - Scope from the token and the summary handler - spec]], [[Build order]], [[How to execute a plan]]
