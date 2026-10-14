---
tags: [build, spec, area/frontend]
id: F1b
owner: Mildred
status: ready
updated: 2026-10-14
---
# F1b: real fixtures and the dashboard on the contract keys (spec)
> **The one screen moves onto the API contract.** Second part of F1 (after [[F1a - Contract types and the 14 artefacts - spec]]): the mock fixtures are exported from the real `tools/metrics.py`, the mock API and the port return the contract types, and every dashboard section reads the new keys. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after F1a is merged.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Mildred - front end]].
3. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
4. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
5. [[F1a - Contract types and the 14 artefacts - spec]]: the types and the validator this item uses.
6. [[L4 - Front-end fixtures from the real summary - spec]] (Linus): the script that will write the same fixtures; the file names are agreed there.
7. [[Clement - front end]]: one line of his `ask-panel.ts` changes here (see §2).
8. `01 Decisions/`: [[2026-10-13 Metrics are code, only the blocker Q&A is agentic]] (D-001).
9. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. **Fixtures from the real core.** `web/src/app/core/api/fixtures/` holds `summary.json` (CFO scope), `summary-entity-lead-E4.json` *(new)*, `entity-E1.json` … `entity-E4.json` and `rows.json` (`RowsResponse`), all written by `tools/api_schema.py`'s builders over the committed dataset. Until L4 is merged they come from a one-off script kept in the git-ignored `.superpowers/` folder; once L4 is merged, `scripts/export_summary.py` *(new)* writes the six shared files identically.
2. **The data layer on the contract:** `PortalApi.summary()` returns `SummaryResponse`, `entity()` returns `EntityResponse`; `MockPortalApi` serves the fixture **the server would return for the scope** (it no longer filters or recomputes a summary); `DashboardStore` holds a `SummaryResponse`.
3. **The dashboard on the new keys:** KPI row, source-target banner, entities table, cutover timeline, blockers table and capacity card. Every percentage is the API's one-decimal value **rounded to a whole number** (58.1 → 58%, 102.7 → 103%), **except the reconciliation pass rate, which keeps one decimal** (96.4%, 94.8%), as the mockup shows it (the lead's ruling D1).
4. **The timeline** shows each entity's **planned (baseline) and forecast cutover** from `entities[].cutover`, the slip between them when the API says the entity is behind plan, and a live bar for a live entity. No build or mock-run bars: `portfolio_summary` has no such figure, and the browser never computes dates.
5. **Retire** `web/scripts/build-fixtures.mjs` (it reads `kpis.json`, deleted in PR #11) and its `fixtures` script; document how fixtures are made in `web/README.md`; add Mildred's `HANDOFF.md` and `DEMO.md` lines.

**Why:** the brief's acceptance: "mock mode shows exactly the figures above", "every KPI on one screen". Judges look for "every figure derived from the migration's own artefacts": the mock must show the same numbers the API will (D-001), and the old mock's client-side filtering of a summary was a KPI computed in the browser.

**Success means (mock mode, `yarn start`, CFO):**
- KPI row: **58%** (18,420 of 31,700 records) · **96.4%** pass rate, "Below the 98% target", "Cycle C3, up from 94.8% in cycle C2" · **7** open blockers, "Oldest open 18 days", "2 on entity 2, 2 on entity 3, 3 on entity 4" · **102** days to final cutover, "6 days behind plan", "Entity 4 cutover weekend, 23 Jan 2027" · **103%** capacity, "Slightly over plan", "38 people used, 37 planned".
- Entities: E1 Live 100%, E2 On track 89%, E3 At risk 54%, E4 Blocked 19%, each "x of y" records.
- Banner "4 source systems → Single cloud ERP, one chart of accounts". Blockers: DEF-0412 (Entity 4, 18 days, Data lead) first, "Showing the 5 oldest of 7". Capacity by role: Tester 8/6, Data migration engineer 14/12, Functional consultant 9/9, Client subject expert 7/10.
- Signed in as the E4 entity lead (role switcher): only E4; 19%, pass rate 95.2%, 3 blockers: the server's own E4 figures.
- Every fixture validates against its contract schema; every citation in the exported fixtures resolves to a row in `rows.json`.
- `yarn test`: 89 passed (F1a's 78 + 11). `yarn build` green. `yarn fixtures` → `Command "fixtures" not found`.

**Assumptions (reconcile with the owners):**
- **L4 (Linus)** writes exactly `summary.json`, `entity-E1.json` … `entity-E4.json` and `rows.json` (`RowsResponse {rows: [...], missing: []}` with every row those five files cite), CFO scope, two-space JSON, and leaves other files alone ([[L4 - Front-end fixtures from the real summary - spec]] §3). **`summary-entity-lead-E4.json` is F1b's own addition** (the mock role switcher needs the server's E4-lead summary); it is written by the `.superpowers` script and is not L4's. *Ask Linus whether L4 should also write it.*
- **Timeline:** the open follow-up "Timeline bars: Patrick + Linus decide whether metrics adds one" is unresolved. F1b ships the brief's fallback (forecast vs baseline from `entities[].cutover`). If they add a timeline figure later, that is a new item.
- **Pass rate shown as 96.4%:** settled by the lead (ruling D1): records reconciled, entity percent complete and capacity show whole numbers (58%, 103%); the reconciliation pass rate and its target show one decimal (96.4% against 94.8%), as the mockup and the brief's "Data facts" do. Two named constants carry the rule: `PERCENT_DISPLAY_DECIMALS = 0` and `PASS_RATE_DISPLAY_DECIMALS = 1`.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Mock for a scoped user | Serve a second exported fixture (`summary-entity-lead-E4.json`), keyed by the scope's entity list; any other scope → 404 "A mock summary for this scope was not found." | Filtering `summary.json` in the browser (computes KPIs client-side, D-001); one fixture per demo user for every role (the other demo users all have `*`) |
| `rows.json` shape | `RowsResponse` (an array), validated against `rows.schema.json`; the mock filters it by citation | The old map keyed `"artefact:row_id"` (not the contract; L4 writes `RowsResponse`) |
| Fixture notes (`_source`, `_temporary`) | Gone from the exported fixtures (they must validate with `additionalProperties: false`); `_mock` stays on the four agent fixtures | Keeping `_source` (fails the schema) |
| Percentages | `formatPercent` rounds to `PERCENT_DISPLAY_DECIMALS = 0` (records, entities, capacity); `formatPassRate` keeps `PASS_RATE_DISPLAY_DECIMALS = 1` (pass rate and its target, lead's ruling D1); the progress meter still gets the exact value | Rounding in the fixtures or the API (that changes the data); one rule for every percentage (the mockup shows 96.4%) |
| Headline citations where the API cites the parts | A card cites all its parts: 58% cites every entity's `reconciled.evidence` (49 rows), the blockers card every blocker's evidence, capacity every role's evidence | No citation on those cards (then "click a number" fails on the headline) |
| Per-entity blocker line | From `entities[].open_blockers` (the API's count), entities with 0 left out | Counting `open_blockers.blockers` per entity in the browser |
| Timeline | Baseline tick + forecast diamond + slip bar (only when `days_behind_plan > 0`) + live bar (only when `live`) | Build and mock-run bars (no API figure); computing slip from dates (the API sends `days_behind_plan`) |
| An empty headline | `pass_rate.latest == null` → "No load cycle has been reconciled yet."; `final_cutover == null` → "Every entity you can see is live." | The old "Awaiting API" block (the fields now exist); `AwaitingApi` is deleted |
| Clement's `ask-panel.ts` | F1b changes its entity type and label (`EntitySummary` → `EntityRow`, `name` → `entity_name`): three lines the type switch forces. **Tell Clement before the commit** | Keeping `EntitySummary` alive for one component |

## 3. The shapes and behaviour
- `PortalApi`: `summary(): Promise<SummaryResponse>`, `entity(entityId: string): Promise<EntityResponse>` (the rest unchanged).
- `MockPortalApi.summary()`: CFO-like scope (`*`) → `summary.json`; `['E4']` → `summary-entity-lead-E4.json`; otherwise `ApiError(404, 'A mock summary for this scope was not found.', 'not_found')`. `rows()` returns the fixture rows the scope may see (mock rule: a row's `entity_id` column) and the rest in `missing`.
- `buildKpiViews(summary: SummaryResponse): KpiView[]` (five cards; `KpiView.emptyText` replaces `awaitingField`). `buildEntityRows(entities: readonly EntityRow[])`. `buildBlockersView(blockers, entities: readonly EntityRow[], total, shown)`. `buildCapacityView(capacity: Capacity)`. `buildTimelineView(entities: readonly EntityRow[], asOf: string)` with `SegmentKind = 'slip' | 'live'` and `TimelineRowView.baselinePercent`.
- `SourceTargetBanner` inputs: `entities: EntityRow[]`, `targetPlatform: string`.
- `formatPercent(58.1) === '58%'`, `formatPassRate(96.4) === '96.4%'`; `PERCENT_DISPLAY_DECIMALS = 0` and `PASS_RATE_DISPLAY_DECIMALS = 1` exported from `core/format/format.ts`. `reconTargetLabel` words the target with `formatPassRate` ("Below the 98% target"). The KPI pass-rate card reads "96.4%" and "Cycle C3, up from 94.8% in cycle C2".
- Removed: `Summary`, `EntitySummary`, `EntityDetail`, `LegacyOverallReconciled`, `CyclePassRate`, `LegacyRoleCapacity`, `EntityCutover`, `Programme`, `ReconPassRate`, `OpenBlockersHeadline`, `FinalCutover`, `PeopleCapacity`, `TimelineEntry` (summary.ts), `shared/ui/awaiting-api/`, `web/scripts/build-fixtures.mjs`.

## 4. Tests
- `core/api/fixtures.spec.ts` (rewritten), 15 tests: 7 contract checks (each exported fixture vs its schema), 6 "every citation resolves" checks, the one-screen figures, the `_mock` notes.
- `core/api/mock-portal-api.spec.ts`, 8 tests: CFO summary; the E4 lead gets the server's E4 summary (19.0, 3 blockers, 95.2); no fixture for E2+E4 → 404; 403 for another entity; entity E4's blockers, failing reconciliation and `CAL-004`; rows and `missing`; ask; publish/approve.
- View specs on the real fixture: `kpi-view` (3), `entities-view` (1), `blockers-view` (2), `capacity-view` (2), `timeline-view` (3), `source-target-banner` (1, new), `format` (5: whole-number rounding, and a new test that the pass rate keeps one decimal).

## 5. Out of scope
- `/rows` live, the error body and the switch to `http`: **F2**.
- The ask, publish and approve fixtures' shapes (Clement: F4a, F5). They keep their `_mock` note and today's shape here.
- Any back-end change; a timeline figure in `metrics`.

Related: [[F1b - Real fixtures and the dashboard on the contract keys - plan]], [[Build order]], [[Mildred - front end]]
