---
tags: [build, spec, area/api, area/frontend]
id: L4
owner: Linus
status: ready
updated: 2026-10-14
---
# L4: front-end fixtures from the real summary (spec)
> **Gets the front end off hand-made mock data.** One script writes the dashboard's mock responses from the same builders the API handlers use, so mock mode shows exactly the back end's figures. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after C1 is merged.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Workstreams]] §3 (the dashboard figures) and §7; [[Linus - API, identity, blocker-analyst]] §4.
3. [[Mildred - front end]]: the consumer. Her item F1 (types from the schema, fixtures from L4) and the "Mismatches the scope sweep found" list.
4. [[C1 - API and spine contracts - spec]] §3 (`summary_response`, `entity_response`, `rows_response`) and §6 (`scripts/export_api_schema.py`, the pattern this script follows).
5. [[Build order]]: L4 depends on C1; F1 waits on it.
6. `01 Decisions/`: [[2026-10-13 Metrics are code, only the blocker Q&A is agentic]] (D-001), [[2026-10-14 ERP-layer dataset is the single source]] (D-019), [[2026-10-14 Two apps in one repo]] (D-020); [[Synthetic data rules]], [[Dev loop]].

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[Problem statement]], [[Judging rubric]], [[Pitch track grading rubric]], [[Hackathon guideline]]); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Linus. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. `scripts/export_summary.py` *(new)*: `uv run python scripts/export_summary.py` writes, to `web/src/app/core/api/fixtures/` (or `--out <folder>`), for a CFO scope:
   - `summary.json`: the `GET /summary` body;
   - `entity-E1.json` … `entity-E4.json`: one `GET /entity/{id}` body per entity on the summary;
   - `rows.json`: a `GET /rows` body (`RowsResponse`) holding **every row the files above cite**, with `missing: []`.
2. Tests that the files are the API's bodies (they validate against the C1 models), show the dashboard figures, and are deterministic.
3. **Later, with Mildred's F1:** the generated fixtures are committed and a drift test keeps them equal to a fresh export (Task 3, a separate PR after F1 merges).

**Why:**
- `web/scripts/build-fixtures.mjs` reads `kpis.json`, which PR #11 deleted, and its fixtures use the old shape (`pass_rate_by_cycle`, `open_defects_by_age`, capacity in hours). The front end must show what `tools/metrics.py` computes (D-001), and the judges check that figures come from the artefacts.
- Generating from `tools/api_schema.py`'s builders means mock and live mode can't disagree.

**Success means:**
- The script writes exactly six files and leaves every other file in the folder untouched (`ask-E4.json`, `ask-partial.json`, `publish.json`, `approve.json` stay Clement's and Mildred's mocks).
- `summary.json` validates as `SummaryResponse` and shows: 18,420 of 31,700 records reconciled (58.1); pass rate C3 96.4 (C2 94.8); 7 open blockers, oldest 18 days; final cutover E4 on 2027-01-23, 102 days away, 6 behind plan; capacity 38 of 37 people; E1 Live, E2 On track, E3 At risk, E4 Blocked.
- Each `entity-<id>.json` validates as `EntityResponse` for that entity; `rows.json` validates as `RowsResponse`, has `missing == []`, and its rows are exactly the set of citations in the other five files.
- Two exports are byte-identical.
- `uv run --locked pytest`: **218 passed** (213 + 5), coverage unchanged (96%; `scripts/` is not measured, like `scripts/export_api_schema.py`).

**Assumptions:**
- **File names agreed with Mildred** (her brief lists the same): `summary.json`, `entity-E1.json` … `entity-E4.json`, `rows.json`. `ask-E4.json` comes later, from a local run, once the flow exists (not this item).
- **`rows.json` becomes a `RowsResponse` `{rows: [...], missing: []}`**, replacing today's map keyed `"artefact:row_id"`. Mildred's mock `rows()` filters it by the requested citations in F1. *Confirm with Mildred before Task 3.*
- The fixtures carry no `_source` / `_temporary` / `_mock` keys (the schemas forbid extra keys). Mildred's `fixtures.spec.ts` changes in F1.
- Committing the new files **before F1** breaks `yarn test` (dry-run: `TS2339: Property 'blockers' does not exist on type ...` in `fixtures.spec.ts`), so Tasks 1–2 don't commit them; Task 3 does, together with or after F1.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Source of the figures | C1's `summary_response`, `entity_response`, `rows_response`, the same builders the handlers call | Calling `metrics` directly (a second path that could drift from the API) |
| Which scope | A CFO (`fixtures-cfo`, every entity of `settings.default_tenant_id`): the mock filters for other roles | One file set per role (the mock already filters; four times the files) |
| Which entities | The ones on the summary (`summary.entities`), not a hard-coded list | `E1`–`E4` written into the script (breaks on a new entity) |
| `rows.json` | Every row cited anywhere in the other files, as one `RowsResponse` | A sample (clicking an uncovered number in mock mode would show nothing) |
| Format | `model_dump(mode="json", by_alias=True)`, two-space indent, UTF-8, trailing newline, model field order | Sorted keys (harder to read next to the schema) |
| Committing the generated files | Only with F1 (Task 3), plus a drift test then | Committing now (breaks the front-end build until F1) |

## 3. Shapes and behaviour
`scripts/export_summary.py`:
| Name | Signature | Behaviour |
|---|---|---|
| `citations_in` | `(body) -> list[Citation]` | every dict with exactly the keys `artefact` and `row_id`, depth-first, in order |
| `fixture_bodies` | `(repository: ArtefactRepository, scope: Scope) -> dict[str, dict]` | file name → JSON body: summary, one entity file per summary entity, then `rows.json` over all their citations |
| `export` | `(output_folder: Path) -> list[Path]` | builds the CFO scope and the repository from settings, writes the files, returns their paths |
| `main` | `() -> int` | `--out` (default `web/src/app/core/api/fixtures/`); prints one path per line; exit 0 |
Constants: `DEFAULT_OUTPUT_FOLDER`, `SUMMARY_FILE_NAME`, `ENTITY_FILE_NAME = "entity-{entity_id}.json"`, `ROWS_FILE_NAME`, `FIXTURE_USER_ID`, `FIXTURE_ROLE`, `CITATION_KEYS`, `JSON_INDENT`, `EXIT_OK`.

## 4. Tests
`tests/scripts/test_export_summary.py` *(new)*, 5 tests (the script runs as a subprocess into `tmp_path`, as C1's export test does): six files written and another file left alone; the summary's dashboard figures; each entity file is that entity's `EntityResponse`; `rows.json` covers every citation; deterministic. Task 3 adds a sixth: the committed fixtures equal a fresh export.

## 5. Out of scope
- Front-end code: types, the mock adapter, `fixtures.spec.ts`, retiring `web/scripts/build-fixtures.mjs` and its `package.json` line (Mildred, F1).
- `ask-E4.json` and the other agent fixtures (later, from a real local run).
- New figures (for example timeline bars: an open decision for Patrick and Linus).

Related: [[L4 - Front-end fixtures from the real summary - plan]], [[Mildred - front end]], [[Build order]]
