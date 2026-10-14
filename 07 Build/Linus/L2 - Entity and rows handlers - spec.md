---
tags: [build, spec, area/api]
id: L2
owner: Linus
status: ready
updated: 2026-10-14
---
# L2: the `/entity` and `/rows` handlers (spec)
> **Drill-down and "click a number to see its rows".** Two more thin handlers on L1's scope builder and error body. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after L1 is merged.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] §3 and §7; [[Linus - API, identity, blocker-analyst]] §2 (the dashboard handlers).
3. [[L1 - Scope from the token and the summary handler - spec]]: the scope builder and the error mapping this item reuses. **L1 must be merged.**
4. [[C1 - API and spine contracts - spec]] §3: `EntityResponse`, `RowsResponse`, `entity_response`, `rows_response`, `citations_from_query`, `ErrorResponse`, `ERROR_STATUS_CODES`.
5. [[Build order]]: L2 depends on C1 and L1; Mildred's F2 (click a number → `/rows`) waits on it.
6. [[Mildred - front end]] (what the screen calls, `{rows, missing}`), [[Yaw - DevOps]] (the routes `GET /entity/{id}` and `GET /rows`).
7. `01 Decisions/`: [[2026-10-13 Scope from the token, enforced twice]] (D-010), [[2026-10-13 Metrics are code, only the blocker Q&A is agentic]] (D-001); [[Dev loop]].
8. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[Problem statement]], [[Judging rubric]], [[Pitch track grading rubric]], [[Hackathon guideline]]); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Linus. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. `entity(event, context)` in `infra/functions/api.py` *(new)*: `GET /entity/{id}` → `EntityResponse` (the entity row, its open blockers, failing reconciliations and calendar conflicts), built by C1's `entity_response(repository, scope, entity_id)`.
2. `rows(event, context)`: `GET /rows?cite=artefact:row_id,...` → `RowsResponse {rows, missing}`, built by `rows_response(repository, scope, citations_from_query(cite))`.
3. The 400 and 404 paths of the error body, which L1's `returns_contract_errors` already maps (`ValueError` → 400 `invalid_input`, `KeyError` → 404 `not_found`, `OutOfScope` → 403 `out_of_scope`).

**Why:**
- The judges look for "every figure derived from the migration's own artefacts". `/rows` is how the screen proves it: every number carries `evidence`, and clicking it fetches those rows (Mildred's F2).
- `/entity/{id}` is the drill-down for one entity, and the place an entity lead is visibly refused another entity (the D2 12:00 Cognito go/no-go).

**Success means:**
- `/entity/E4` for the CFO is 200: status `Blocked`, blockers include `DEF-0412`, failing reconciliations include `RC-C3-E4-customers`, calendar conflicts are `["CAL-004"]`.
- `/entity/E2` for the E4 lead is 403 `out_of_scope`; `/entity/E9` is 404 `not_found`; `/entity/E-4` and a missing path parameter are 400 `invalid_input`; no token (with `AUTH_MODE=cognito`) is 401.
- `/rows?cite=defect_log:DEF-0412,defect_log:DEF-0447,defect_log:DEF-9999` for the E4 lead returns only `DEF-0412` in `rows`, and `DEF-0447` (E2's) and `DEF-9999` (unknown) in `missing`.
- `/rows` with no `cite`, an empty one, `defect_log` (no row ID) or `not_an_artefact:X` is 400; without a token it is 401 **before** the `cite` is read.
- `uv run --locked pytest`: **255 passed** (L1's 243 + 12), coverage 97%.

**Assumptions:**
- L1 is merged as planned ([[L1 - Scope from the token and the summary handler - plan]]): `returns_contract_errors`, `json_response`, `repository_for`, `scope_from_event`, `HTTP_OK`.
- Yaw's routes are exactly `GET /entity/{id}` (path parameter `id`) and `GET /rows` with the query parameter `cite` (Y1). HTTP API joins a repeated query parameter with commas, which `citations_from_query` already splits.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Where the logic lives | Nowhere new: `entity_response`, `rows_response` and `citations_from_query` (C1) do it; the handlers only read the path or query and call them | Re-implementing the visibility rule in `infra/functions/api.py` (C1 Review Focus 2: reuse `queries.in_entity_view`) |
| Missing path parameter | Read as `""`, so `Scope.require` raises `ValueError` → 400 | A `KeyError` (that would read as 404 "not found") |
| Order of checks in `/rows` | Scope first, then the `cite` parameter: an unsigned caller always gets 401 | Parsing first (a malformed request would leak 400 to someone not signed in) |
| An unknown entity for an entity lead (`E9` asked by the E4 lead) | 403 `out_of_scope` (`Scope.require` runs before the lookup), so a lead can't probe which entities exist | 404 (tells a lead an entity doesn't exist) |
| Rows the user may not see | Listed in `missing`, never in `rows`, exactly like unknown rows | 403 for the whole request (one stale citation would break the row viewer) |

## 3. Shapes and behaviour
| Handler | Request | 200 body | Errors |
|---|---|---|---|
| `infra.functions.api.entity` | `pathParameters.id` | `EntityResponse {entity, blockers, failing_reconciliations, calendar_conflicts}` | 400 malformed or missing ID; 401 no token; 403 `forbidden` bad token, `out_of_scope` other entity; 404 unknown entity |
| `infra.functions.api.rows` | `queryStringParameters.cite` = `artefact:row_id,...` | `RowsResponse {rows: [Row], missing: [Citation]}` | 400 missing or malformed `cite`, unknown artefact; 401; 403 `forbidden` |

New constants in `infra/functions/api.py`: `ENTITY_PATH_PARAMETER = "id"`, `CITE_QUERY_PARAMETER = "cite"`. Same environment and IAM as `summary` (`docs/DEVOPS_HANDOVER.md`: `s3:GetObject` on `artefacts/*`).

## 4. Tests
`tests/infra/functions/test_api.py` *(new)*, 12 new tests (with fake HTTP API v2 events from L1's `make_event`): E4 for the CFO; four `/entity` errors (another entity, unknown entity, malformed ID, no token); a missing path parameter; `/rows` visible vs missing; four malformed `cite` cases; `/rows` without a token.

## 5. Out of scope
- `/ask`, `/publish`, `/approve` (L3).
- New figures or fields on the entity view (they would be a `tools/metrics.py` change with a pinned test, and a C1 contract change through Patrick).
- The row viewer in the front end (Mildred, F2).

Related: [[L2 - Entity and rows handlers - plan]], [[L1 - Scope from the token and the summary handler - spec]], [[Build order]]
