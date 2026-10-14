---
tags: [build, spec, area/frontend]
id: F1a
owner: Mildred
status: ready
updated: 2026-10-14
---
# F1a: TypeScript contract types and all 14 artefacts (spec)
> **First of three front-end data items** (F1a → F1b → F2). F1 in [[Build order]] is split in two, so each part is one agent session and mergeable alone: **F1a** adds the API contract's TypeScript types next to today's, with a schema check; **F1b** ([[F1b - Real fixtures and the dashboard on the contract keys - spec]]) moves the fixtures and the dashboard onto them. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after C1 is merged.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Mildred - front end]].
3. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
4. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
5. [[Clement - front end]]: the other front-end owner; his files use the models you add.
6. `01 Decisions/`: [[2026-10-13 Metrics are code, only the blocker Q&A is agentic]] (D-001) and `DECISIONS.md` (repo) D-020 (two apps in one repo) and D-021 (contracts in code).
7. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. A **test-only contract validator**: `contractErrors(name, body)` checks any body against the JSON Schemas C1 exports to `web/src/app/core/api/schema/` (`ajv`, already in `yarn.lock` as a transitive dependency, added as a direct dev dependency).
2. **All 14 artefacts** in `ARTEFACT_NAMES` (`web/src/app/core/models/citation.ts`) and a label for each in `core/format/format.ts`, in the schema's order.
3. **The contract types** in `core/models/summary.ts` (`SummaryResponse`, `EntityRow`, `EntityResponse`, …) and `core/models/error-response.ts` *(new)* (`ErrorResponse`, `ERROR_CODES`), field for field what `tools/api_schema.py` sends. Today's types stay until F1b switches the screen; the two whose names clash are renamed `Legacy…`.

**Why:**
- C1 froze the API's keys in code; the front end adopts them (brief: "the back end won't reshape to the old front-end types"). Without types that match, every later item (F1b, F2, F3–F5) guesses.
- Q01 cites `field_mappings` and `load_errors`; with 7 of 14 artefacts, a citation chip for them can't even be typed.
- A validator that reads the **exported** schemas means a renamed back-end key fails a front-end test the day the schemas are re-exported, not in the demo.

**Success means:**
- `contractErrors('error', {error: 'out_of_scope', detail: '…'})` is `[]`; a renamed key gives `/ must have required property 'error'`.
- `ARTEFACT_NAMES` equals the `Citation.artefact` enum in `rows.schema.json`, and every artefact has a label.
- A typed `SummaryResponse` sample (with `final_cutover: null`), an `EntityResponse`, a `RowsResponse` and an `ErrorResponse` each compile **and** validate against their schema.
- `yarn test`: 78 passed (69 today + 9). `yarn build` green. Nothing on screen changes.

**Assumptions:**
- C1 is merged as it stands on `feature/api-and-spine-contracts` (`d6ddb39`): ten schemas in `web/src/app/core/api/schema/` named after `API_MODELS` (`summary`, `entity`, `rows`, `ask_request`, `ask_response`, `publish_request`, `publish_response`, `approve_request`, `approve_response`, `error`).
- `EntityRow.status` is typed as the four values of `tools/constants.py` `EntityStatus` although the schema says `string`; F1b's fixture test checks every status is one of them.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Types from the schema: generated or by hand | **By hand**, with a test per model that a typed sample validates against the exported schema | `json-schema-to-typescript` (a second generator and a second generated folder for 10 small models; the generated names would not match `index.ts` exports) |
| How fixtures and bodies are checked | `ajv` 8.20.0 (draft 2020-12 build, `ajv/dist/2020`), test-only, in `core/api/testing/contract-validator.ts` *(new)* | Hand-written key lists (drift again); `zod` (a second schema language) |
| Where the error body type lives | `core/models/error-response.ts` *(new)*, exported from `index.ts`, with `ERROR_CODES` checked against `error.schema.json` | Inside `api-error.ts` (models live in `core/models/`) |
| Clashing old names | Rename today's `OverallReconciled` and `RoleCapacity` to `LegacyOverallReconciled` and `LegacyRoleCapacity` (only `summary.ts` uses them); everything else stays until F1b | Replacing the old types now (breaks every component in one go; that switch is F1b) |
| Artefact order | The schema's (which is `tools/constants.py`'s) | Alphabetical (a second order to keep in sync) |

## 3. The shapes
**`contractErrors(name: ContractName, body: unknown): string[]`** in `web/src/app/core/api/testing/contract-validator.ts` *(new)*. `ContractName` is the union of the ten schema names. Each error is `"<instancePath or /> <ajv message>"`, plus ` (<key>)` for an unknown key. Empty list = valid.

**`ARTEFACT_NAMES`** (in this order): `entities`, `object_inventory`, `load_cycles`, `load_runs`, `load_errors`, `reconciliation_results`, `defect_log`, `workplan`, `cutover_runbook`, `team_roster`, `rate_card`, `field_mappings`, `value_mappings`, `calendar`. Labels: `Entities`, `Object inventory`, `Load cycles`, `Load runs`, `Load errors`, `Reconciliation results`, `Defect log`, `Workplan`, `Cutover runbook`, `Team roster`, `Rate card`, `Field mappings`, `Value mappings`, `Calendar`.

**Contract types** (`core/models/summary.ts`), one interface per C1 model, same field names and types: `SummaryResponse`, `OverallReconciled`, `PassRate`, `CycleTotals`, `OpenBlockers`, `Cutover`, `Capacity`, `RoleCapacity`, `Reconciled`, `EntityRow`, `EntityResponse`, `FailedReconciliation`, `CalendarConflict` (`Blocker` and `RowsResponse` already match). Nullable fields are `T | null` (`final_cutover`, `pass_rate.latest`, `pass_rate.previous`). **`core/models/error-response.ts`**: `ERROR_CODES = ['invalid_input', 'unauthorized', 'forbidden', 'out_of_scope', 'not_found']`, `ErrorCode`, `ErrorResponse {error, detail}`.

## 4. Tests (Vitest, `yarn test`)
- `core/api/testing/contract-validator.spec.ts` *(new)*, 3 tests: a valid body; a renamed + unknown key (exact messages); a value outside an enum.
- `core/models/citation.spec.ts` *(new)*, 2 tests: `ARTEFACT_NAMES` equals the schema enum; every artefact has its label.
- `core/models/contract-types.spec.ts` *(new)*, 4 tests: `SummaryResponse` (with `final_cutover: null`, `previous: null`), `EntityResponse`, `RowsResponse` + `ErrorResponse`, `ERROR_CODES` equals the schema enum.

## 5. Out of scope
- The fixtures, the mock, the port and the dashboard on the new keys: **F1b**.
- `ask.ts` and `publish.ts` (Clement's): **F4a** and **F5**.
- Any change to the schemas (they are generated by C1's `scripts/export_api_schema.py`; ask Patrick).

Related: [[F1a - Contract types and the 14 artefacts - plan]], [[Build order]], [[Mildred - front end]]
