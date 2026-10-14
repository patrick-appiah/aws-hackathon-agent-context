---
tags: [workstream, area/team]
owner: Mildred
updated: 2026-10-14
---
# Mildred: front end, data and the one screen
> The repo is the source of truth. Read [[Workstreams]] first. Your row: `docs/TEAM_PLAN.md` §2, workstream 6 (with Clement, [[Clement - front end]]).
> **Proposal: confirm this split with Clement at the first stand-up.** You take the **data layer and the one screen**; Clement takes **sign-in, ask, publish and approve**. File ownership is listed below so you never edit the same files.

## Your job in one paragraph
You built the portal (PR #12: Angular 22, the AmaliTech design system, mock and http adapters, the dashboard, ask and publish screens, its own unit tests). Your job now is to move **the one screen off mock data and onto the real API**, with every number matching the back end exactly:
- align the TypeScript models with the API schema;
- replace the fixtures with ones generated from the real summary;
- show all five KPIs from `/summary`;
- make "click a number to see its source rows" work through `/rows`.

Judges look for "every figure derived from the migration's own artefacts", and your screen is where they see it.

## Shared front-end context (same in Clement's brief)
- **Setup:** Node 22 (`web/.nvmrc`), yarn 1.22.22 via `corepack enable`, the read-only npm token in your **home** `~/.npmrc` (`web/README.md`). Then `cd web && yarn install --frozen-lockfile && yarn start`; `yarn test`; `yarn build` → `web/dist/web/browser`.
- **Switches:** `web/src/app/core/config/portal-config.ts`: `dataSource` (`mock` | `http`), `authMode` (`none` | `cognito`), `apiBaseUrl` (`/api`, same origin through Michael's CloudFront `/api/*` behaviour, so no CORS).
- **The API contract** is Patrick's `tools/api_schema.py` *(new)*, exported as JSON Schema by `scripts/export_api_schema.py` *(new)*. **The front end adopts the back end's keys;** the back end won't reshape to the old front-end types.
- **Mismatches the scope sweep found** (fix them when the schema lands):
  - **Summary:** `overall{records_reconciled, records_in_scope, pct}` (not `reconciled/total`); `pass_rate{latest, previous, target_pct}` (not `pass_rate_by_cycle`); `open_blockers{count, oldest_days, blockers[]}` (not `open_defects_by_age`); `final_cutover{cutover_forecast, cutover_baseline, days_remaining, days_behind_plan, live}`; `capacity{month, people_used, people_planned, pct, by_role[]}` in **people**, not hours; programme fields flat (`programme_name`, `target_platform`, `currency`).
  - **Entity rows:** `entity_name`, `business_role`, `source_tier`, `source_description`, `target_company_code`, `reconciled{records_reconciled, records_in_scope, pct}`, `cutover{...}`, `open_blockers`, `status`.
  - **Citations:** `ARTEFACT_NAMES` in `web/src/app/core/models/citation.ts` lists 7 of the **14** artefacts (`tools/constants.py`). Q01 cites `field_mappings` and `load_errors`.
  - **`/rows`** returns `{rows, missing}`; out-of-scope citations come back in `missing`.
  - **Errors:** `{error, detail}` with 400/403/404.
  - **Percentages:** the API sends one decimal (`58.1`). The screen shows whole numbers (58%).
- **Data facts to show:**
  - 18,420 of 31,700 records reconciled (58%);
  - C3 pass rate 96.4% (C2 94.8%, target 98%);
  - 7 open blockers, oldest 18 days;
  - final cutover E4, 2027-01-23, 102 days away, 6 behind plan;
  - capacity 38 of 37 people;
  - entities: E1 Live, E2 On track, E3 At risk, E4 Blocked.

## What you own
| Path | Notes |
|---|---|
| `web/src/app/core/models/summary.ts`, `citation.ts`, `scope.ts`, `index.ts` | data models (Clement owns `ask.ts`, `publish.ts`) |
| `web/src/app/core/api/` except `bearer-token-interceptor.ts` | the `PortalApi` port, `http-portal-api.ts`, `mock-portal-api.ts`, `provide-portal-api.ts`, `api-error.ts`, `fixtures/` |
| `web/src/app/core/config/portal-config.ts`, `display-rules.ts`, `core/format/` | shared config. Clement asks you before changing `authMode` handling |
| `web/src/app/features/dashboard/` | the one screen: KPI row, entities table, timeline, blockers table, capacity card, source-target banner |
| `web/src/app/shared/citations/`, `web/src/app/shared/ui/`, `web/src/app/shared/forms/` | citation viewer, row viewer, shared UI and form helpers |
| `web/scripts/build-fixtures.mjs` | to retire: it reads `kpis.json`, which PR #11 deleted |
| `web/README.md` | front-end docs (shared; keep Clement's sections) |

## What you build
1. **Types from the schema.** When Patrick's contracts PR lands, generate or hand-align `core/models/summary.ts` and `citation.ts` from the exported JSON Schema (`json-schema-to-typescript`, or by hand with a test that a fixture parses). Add all 14 artefacts to `ARTEFACT_NAMES`. Acceptance: `yarn test` passes against the new fixtures.
2. **Fixtures from the real code.** Use Linus's `scripts/export_summary.py` *(new)* output in `core/api/fixtures/` (`summary.json`, `entity-E1…E4.json`, `rows.json`, `ask-E4.json`); agree the file names with Linus. Remove `build-fixtures.mjs` and its `fixtures` script line in `package.json`. Acceptance: mock mode shows exactly the figures above.
3. **The dashboard on the new keys:**
   - KPI row: records reconciled, pass rate latest vs previous, open blockers with the oldest age, days to final cutover with days behind, capacity.
   - Entities table with statuses.
   - Blockers table (`reference`, entity, age, owner).
   - Capacity by role (people).

   Acceptance: every KPI on one screen, matching the numbers above.
4. **The timeline.** `portfolio_summary` doesn't produce timeline bars today (the old mockup had build, mock-run and cutover dates). Ask Patrick and Linus whether the back end should add a timeline figure to `metrics` (a pinned test, a schema field), or whether the timeline shows cutover forecast vs baseline only from `entities[].cutover`. Don't compute dates in the front end.
5. **Click a number → its source rows.** Every cited number calls `GET /rows?cite=artefact:row_id,...` with the number's `evidence`; the row viewer shows the rows and lists `missing` separately. Acceptance: clicking 58% shows the passing reconciliation rows.
6. **Switch to `http`** against the deployed API (D1 18:00 walking skeleton, with Linus and Yaw). Keep `mock` as the default for local development and tests.

## Interfaces
| You consume | From |
|---|---|
| JSON Schema, response shapes | Patrick (`tools/api_schema.py`, `scripts/export_api_schema.py`) |
| Fixtures | Linus (`scripts/export_summary.py`) |
| `/summary`, `/entity/{id}`, `/rows` live | Linus (handlers), Yaw (API), Michael (CloudFront) |

| You produce | For |
|---|---|
| The `PortalApi` port and http adapter used by every screen | Clement |
| The one screen | the demo (`DEMO.md` 0:30–1:00) |

## Dependencies
- **You wait on:** the schema (Patrick, D1 10:30); fixtures (Linus, D1 afternoon); the live API (D1 18:00). Until then, keep building on mock data and the field names listed above.
- **Waiting on you:** Clement (the http adapter and models), the demo.

## Your milestones
| When | Milestone |
|---|---|
| D1 12:00 | Models aligned to the schema; all 14 artefacts |
| D1 16:00 | Fixtures from `export_summary.py`; dashboard on the new keys (mock) |
| D1 18:00 | The one screen on the live `/summary` (walking skeleton) |
| D2 12:00 | Click-a-number via `/rows` live; role-based views tested with Clement |

## Definition of done
- [ ] All five KPIs on one screen from `/summary`, matching the back end's figures.
- [ ] Clicking any number shows its source rows from `/rows`.
- [ ] Models match the schema; 14 artefacts; `build-fixtures.mjs` retired.
- [ ] `yarn test` and `yarn build` green; Jenkins front-end build green.
- [ ] Your `HANDOFF.md` and `DEMO.md` lines (what the screen shows, what's mocked).

## Rules and pitfalls specific to you
- **Never compute a KPI in the front end.** Display what `/summary` returns (D-001); only rounding for display.
- **Never commit the npm token** (`web/.npmrc` holds only the scope line).
- **One lock file:** `yarn.lock` only. Add packages with `yarn add`, then commit `package.json` and `yarn.lock` together.
- **Synthetic data only;** no real names in fixtures or UI copy.

## Getting started
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
cd web && corepack enable && yarn install --frozen-lockfile && yarn test
git switch -c feature/web-api-contract
```
Then give your assistant `06 Workstreams/prompts/mildred.txt`.

## Who to ask
| Topic | Person |
|---|---|
| Schema, timeline decision | Patrick |
| Fixtures, `/summary`, `/rows` | Linus |
| CloudFront, `/api` | Michael, Yaw |
| Sign-in, ask, publish | Clement |

Related: [[Workstreams]], [[Team plan]]
