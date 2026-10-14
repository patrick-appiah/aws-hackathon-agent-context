---
tags: [build, plan, area/api]
id: L2
owner: Linus
spec: "[[L2 - Entity and rows handlers - spec]]"
status: ready
updated: 2026-10-14
---
# L2: the `/entity` and `/rows` handlers (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[L2 - Entity and rows handlers - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record it in the ledger.
3. [[L1 - Scope from the token and the summary handler - plan]] Task 2: the handler module and the test fixtures you extend here.
4. [[C1 - API and spine contracts - spec]] §3 (`/entity/{id}` and `/rows`).
5. [[Linus - API, identity, blocker-analyst]] §2, and [[Working with AI assistants]].
6. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[Problem statement]], [[Judging rubric]], [[Pitch track grading rubric]], [[Hackathon guideline]]); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Linus. Never invent a name, a shape or a rule.

**Goal:** `GET /entity/{id}` and `GET /rows` answer with the contract models, and refuse what the scope can't see, through the same error body as `/summary`.

**Architecture:** two more handlers in `infra/functions/api.py` *(new)*, each three lines: scope (L1) → C1 builder → `json_response`. The visibility rule stays in `tools/queries.in_entity_view` (via `rows_response`); nothing new in the core.

**Tech stack:** Python 3.11, pydantic 2, pytest, uv. No AWS calls.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: **`feature/api-entity-and-rows`** from an up-to-date `develop` **after L1 is merged**.
- **Start state:** `uv run --locked pytest` → **243 passed**, `TOTAL` **97%** (develop with C1 and L1). If other items merged since, your count is higher: write it in the ledger as START and read each `N passed` below as START + the same increase. If `infra/functions/api.py` has no `returns_contract_errors`, L1 isn't merged: stop.
- **AWS:** `eu-west-1` only; Bedrock `eu.*` inference profiles only, never `global.*` (D-002). Synthetic data only. **No secrets** anywhere: code, tests, fixtures, the repo, the vault, Slack, commit messages.
- **Clean code (enforced by tests):** no single-character names anywhere (comprehensions, lambdas and `except ... as` included); no magic numbers or strings, so every limit, code and key is a named constant; settings only in `config.py`; domain constants only in `tools/constants.py`; descriptive names.
- **The core (`tools/`) never imports** boto3, Strands, `adapters`, `config` or `os` (`tests/test_architecture.py`).
- **Agents reach data only through `tools/agent_tools.py`.** Scope is never a tool argument and never comes from a request body, a query string or a model. Prompts live only in `agents/prompts/<agent>.txt`, versioned and locked (`uv run python scripts/lock_prompts.py`).
- **Never weaken a security rule** (the scope gate, the create-once ledger, the fail-closed critic, the `<evidence>` escaping) to make a test pass.
- **Tests** live in `tests/`, mirroring the code; run `uv run --locked pytest` from the repo root. Coverage must not drop below the start state. **No layout or "meta" guard tests**: test behaviour, not where files sit.
- **Git:** small commits, one per task, with the messages given. **No `Co-Authored-By` and no "Generated with" lines.** Never push to `develop` or `main`; the PR goes to `develop` after the owner's OK, and Patrick merges.
- **Stay in your folders** (`docs/TEAM_PLAN.md` §2, workstream 3: `infra/functions/api.py`, `infra/functions/scope.py` *(new)*, `tests/infra/functions/` *(new)*, `tools/metrics.py`, `tools/queries.py`, `tools/agent_tools.py`, `tools/claims.py`, `agents/blocker_analyst.py` *(new)*, `agents/prompts/blocker_analyst.txt` *(new)*, `scripts/export_summary.py` *(new)*, the eval runner). Any other file this plan touches is named in its task, with the owner who must review it.
- **Thin handlers:** read the path or query parameter, call the C1 builder, return `json_response`. Nothing else.

## Review Focus (check by hand at the end)
1. **`/rows` never returns a row the scope can't see.** It reuses `rows_response`, which reuses `queries.in_entity_view`. Grep `infra/functions/api.py` for `in_entity_view`: it must not appear (no second copy of the rule).
2. **The route names match Yaw's ApiStack:** the path parameter is `id` and the query parameter is `cite`. Compare with Y1's route definitions before the PR, and write the result in the ledger.
3. **An entity lead can't probe existence:** `/entity/E9` as the E4 lead is 403 `out_of_scope`, not 404. Call it once with `make_event` in a Python shell (`uv run python`) and write the status in the ledger.
4. **Response size:** the largest `/rows` body (every citation on the summary, about 140 rows, about 100 KB) is far below the 6 MB Lambda response limit. Note the size you measure in L4, or `len(response["body"])` for a CFO call citing every summary row.
5. **No arithmetic slipped in:** `git diff develop -- infra/functions/api.py` adds no operators on figures (`+ - * /` between numbers, `round`, `sum`).

---

### Task 1: `GET /entity/{id}` and `GET /rows`

**Files:**
- Modify: `infra/functions/api.py`, `tests/infra/functions/test_api.py` *(new)*

**Produces:** `infra.functions.api.entity(event: dict, context: object) -> dict`, `infra.functions.api.rows(event: dict, context: object) -> dict`, constants `ENTITY_PATH_PARAMETER`, `CITE_QUERY_PARAMETER`. **Consumes:** L1's `returns_contract_errors`, `json_response`, `repository_for`, `scope_from_event`, `HTTP_OK`; C1's `entity_response(repository, scope, entity_id)`, `rows_response(repository, scope, citations)`, `citations_from_query(cite)`, `EntityResponse`, `RowsResponse`. **Consumed by:** Yaw (Y1 routes `infra.functions.api.entity`, `infra.functions.api.rows`), Mildred (F2).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/api-entity-and-rows
mkdir -p .superpowers && printf '# Ledger: L2 entity and rows handlers\n' > .superpowers/ledger-L2.md
```
Expected: `243 passed`, `TOTAL ... 97%` (or your START).

- [ ] **Step 2: Write the failing tests.** In `tests/infra/functions/test_api.py`:
  - replace the import line `from tools.api_schema import ERROR_STATUS_CODES, ErrorResponse, SummaryResponse` with:
    ```python
    from tools.api_schema import ERROR_STATUS_CODES, EntityResponse, ErrorResponse, RowsResponse, SummaryResponse
    ```
  - append at the end of the file (two blank lines before it):
```python
E4_BLOCKER = "DEF-0412"
E4_FAILING_RECONCILIATION = "RC-C3-E4-customers"
E4_CALENDAR_CLASH = ["CAL-004"]
E2_DEFECT = "DEF-0447"
UNKNOWN_DEFECT = "DEF-9999"


def test_entity_e4_for_the_cfo(cognito_mode, make_event):
    response = handlers.entity(make_event(claims=CFO_CLAIMS, path_parameters={"id": "E4"}), None)
    detail = EntityResponse.model_validate_json(response["body"])
    assert response["statusCode"] == HTTP_OK and detail.entity.status == "Blocked"
    assert E4_BLOCKER in {blocker.reference for blocker in detail.blockers}
    assert E4_FAILING_RECONCILIATION in {failed.recon_id for failed in detail.failing_reconciliations}
    assert [conflict.window_id for conflict in detail.calendar_conflicts] == E4_CALENDAR_CLASH


@pytest.mark.parametrize("claims, entity_id, error_code", [
    (ENTITY_FOUR_LEAD_CLAIMS, "E2", "out_of_scope"),
    (CFO_CLAIMS, "E9", "not_found"),
    (CFO_CLAIMS, "E-4", "invalid_input"),
    (None, "E4", "unauthorized"),
], ids=["another_entity", "unknown_entity", "malformed_entity_id", "no_token"])
def test_entity_errors_use_the_contract_body(cognito_mode, make_event, claims, entity_id, error_code):
    assert_error(handlers.entity(make_event(claims=claims, path_parameters={"id": entity_id}), None), error_code)


def test_entity_without_a_path_parameter_is_400(cognito_mode, make_event):
    assert_error(handlers.entity(make_event(claims=CFO_CLAIMS), None), "invalid_input")


def test_rows_returns_visible_rows_and_lists_the_rest_as_missing(cognito_mode, make_event):
    cite = ",".join(f"defect_log:{row_id}" for row_id in (E4_BLOCKER, E2_DEFECT, UNKNOWN_DEFECT))
    response = handlers.rows(make_event(claims=ENTITY_FOUR_LEAD_CLAIMS, query={"cite": cite}), None)
    rows = RowsResponse.model_validate_json(response["body"])
    assert response["statusCode"] == HTTP_OK and [row.row_id for row in rows.rows] == [E4_BLOCKER]
    assert [citation.row_id for citation in rows.missing] == [E2_DEFECT, UNKNOWN_DEFECT]


@pytest.mark.parametrize("query", [None, {"cite": ""}, {"cite": "defect_log"}, {"cite": "not_an_artefact:X"}],
                         ids=["no_query", "empty_cite", "no_row_id", "unknown_artefact"])
def test_rows_with_a_malformed_cite_is_400(cognito_mode, make_event, query):
    assert_error(handlers.rows(make_event(claims=CFO_CLAIMS, query=query), None), "invalid_input")


def test_rows_without_a_token_is_401_before_the_cite_is_read(cognito_mode, make_event):
    assert_error(handlers.rows(make_event(query={"cite": "defect_log"}), None), "unauthorized")
```

- [ ] **Step 3: Run them and watch them fail**
```bash
uv run --locked pytest tests/infra/functions/test_api.py --no-cov 2>&1 | tail -1
uv run --locked pytest tests/infra/functions/test_api.py --no-cov 2>&1 | grep -E "^E  " | sort | uniq -c
```
Expected: `12 failed, 10 passed`; then `6 E       AttributeError: module 'infra.functions.api' has no attribute 'entity'` and `6 E       AttributeError: module 'infra.functions.api' has no attribute 'rows'`.

- [ ] **Step 4: Implement.** In `infra/functions/api.py`:
  - replace the `from tools.api_schema import (...)` statement with:
    ```python
    from tools.api_schema import (ERROR_FORBIDDEN, ERROR_NOT_FOUND, ERROR_STATUS_CODES, ERROR_UNAUTHORIZED, ErrorResponse,
                                  citations_from_query, entity_response, rows_response, summary_response)
    ```
  - directly after `JSON_HEADERS = {"content-type": "application/json"}`, add:
    ```python
    ENTITY_PATH_PARAMETER = "id"      # GET /entity/{id}
    CITE_QUERY_PARAMETER = "cite"     # GET /rows?cite=artefact:row_id,...
    ```
  - append at the end of the file (two blank lines after `summary`):
```python
@returns_contract_errors
def entity(event: dict, context: object) -> dict:
    """GET /entity/{id}: the entity's row, open blockers, failing reconciliations and calendar conflicts."""
    scope = scope_from_event(event, get_settings())
    entity_id = (event.get("pathParameters") or {}).get(ENTITY_PATH_PARAMETER, "")
    return json_response(HTTP_OK, entity_response(repository_for(scope.tenant_id), scope, entity_id))


@returns_contract_errors
def rows(event: dict, context: object) -> dict:
    """GET /rows?cite=artefact:row_id,...: the cited rows the scope may see; the rest come back in `missing`."""
    scope = scope_from_event(event, get_settings())
    cite = (event.get("queryStringParameters") or {}).get(CITE_QUERY_PARAMETER, "")
    return json_response(HTTP_OK, rows_response(repository_for(scope.tenant_id), scope, citations_from_query(cite)))
```

- [ ] **Step 5: Run them and watch them pass**
```bash
uv run --locked pytest tests/infra/functions/test_api.py --no-cov 2>&1 | tail -1
```
Expected: `22 passed`.

- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/functions/api.py tests/infra/functions/test_api.py
git commit -m "GET /entity/{id} and GET /rows: scope-checked drill-down and source rows, missing rows listed (D-021)"
```
Expected: `255 passed`, `TOTAL ... 97%`.

**Task done when:** `uv run --locked pytest tests/infra/functions/test_api.py --no-cov` prints `22 passed`; `grep -c "in_entity_view" infra/functions/api.py` prints `0`; the commit is on the branch.

### Task 2: Handover and HANDOFF

**Files:**
- Modify: `docs/DEVOPS_HANDOVER.md` (your row), `HANDOFF.md` (your line)

- [ ] **Step 1: `docs/DEVOPS_HANDOVER.md`:** replace `` `infra.functions.api.summary` (built, L1) / `entity` / `rows` *(planned)* `` with `` `infra.functions.api.summary` / `entity` / `rows` (built) ``.
- [ ] **Step 2: `HANDOFF.md`:** under "What's real", directly above `- TODO: agent loop, critic, ledger, approval flow, as each lands.`, add:
```markdown
- `GET /entity/{id}` and `GET /rows` (`infra/functions/api.py`): another entity is a 403 `out_of_scope`; cited rows the user may not see come back in `missing`, never as rows. Every error uses the contract body `{error, detail}`.
```
- [ ] **Step 3: Guards, full suite and commit**
```bash
uv run --locked pytest tests/test_dependencies.py tests/test_code_style.py --no-cov 2>&1 | tail -1
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add docs/DEVOPS_HANDOVER.md HANDOFF.md
git commit -m "Handover and HANDOFF: the entity and rows handlers are built"
```
Expected: `15 passed`; then `255 passed`, `TOTAL ... 97%`.

**Task done when:** `grep -c "(built)" docs/DEVOPS_HANDOVER.md` prints `1`; `HANDOFF.md` has the `/entity` line; the suite is `255 passed`.

### Task 3: Review, then PR (after Linus's OK)
- [ ] **Step 1:** Work through the Review Focus; write each result in the ledger.
- [ ] **Step 2:** `git diff develop --stat` lists only `infra/functions/api.py`, `tests/infra/functions/test_api.py`, `docs/DEVOPS_HANDOVER.md`, `HANDOFF.md`. Expected: `4 files changed`.
- [ ] **Step 3:** Fresh review of the diff against the spec; fix critical and important findings test-first.
- [ ] **Step 4: With the OK only:** `git push -u origin feature/api-entity-and-rows`; PR to `develop`, titled "GET /entity and GET /rows handlers (L2)", body with `255 passed`, the coverage and the rulings. No attribution lines.
- [ ] **Step 5:** L2's [[Build order]] row → `in review (PR #nn)`. Tell Yaw the entry points `infra.functions.api.entity` and `infra.functions.api.rows`; tell Mildred `/rows` returns `{rows, missing}` and the 400 cases.

**Task done when:** the PR is open to `develop` and L2's [[Build order]] row says `in review (PR #nn)`.

## Done means (checklist)
- [ ] `uv run --locked pytest` prints `255 passed` (START + 12) and `TOTAL` ≥ 97%. *Verify:* run it.
- [ ] A CFO `/entity/E4` call returns 200 with `DEF-0412` among the blockers, and an E4 lead's `/entity/E2` returns 403 `out_of_scope`. *Verify:* `uv run --locked pytest tests/infra/functions/test_api.py -k "entity" --no-cov` prints `6 passed`.
- [ ] `/rows` lists out-of-scope and unknown citations in `missing`. *Verify:* `uv run --locked pytest tests/infra/functions/test_api.py -k "visible_rows" --no-cov` prints `1 passed`.
- [ ] `docs/DEVOPS_HANDOVER.md` marks `entity` and `rows` built. *Verify:* `grep -n "(built)" docs/DEVOPS_HANDOVER.md`.
- [ ] PR open or merged, no attribution lines. *Verify:* `gh pr view <nn> --json state`; `git log develop..HEAD --format=%B | grep -ci "co-authored"` prints `0`.
- [ ] [[Build order]] row L2 updated. *Verify:* open the note.

## Never
- Filter rows by scope in `infra/functions/api.py` (the rule lives once, in `tools/queries.in_entity_view`).
- Return a 404 for an entity the user isn't allowed to see.
- Read the scope from the query string.
- Push to `develop` or `main`, or add attribution lines.

Related: [[L2 - Entity and rows handlers - spec]], [[L1 - Scope from the token and the summary handler - plan]], [[Build order]], [[How to execute a plan]]
