---
tags: [build, plan, area/frontend]
id: F1a
owner: Mildred
spec: "[[F1a - Contract types and the 14 artefacts - spec]]"
status: ready
updated: 2026-10-14
---
# F1a: contract types and the 14 artefacts (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[F1a - Contract types and the 14 artefacts - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger as a `Ruling:` line.
3. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Mildred - front end]].
4. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
5. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
6. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

**Goal:** a test-only validator against C1's exported JSON Schemas, all 14 artefacts, and the contract's TypeScript types next to today's, each proven against its schema.

**Architecture:** models in `web/src/app/core/models/`; the validator in `web/src/app/core/api/testing/` *(new)* (imported only by `*.spec.ts` files, so it never reaches the bundle). No component changes.

**Tech stack:** Angular 22, TypeScript 6 (strict), Vitest 5 through `ng test` (`@angular/build:unit-test`, jsdom), `ajv` 8.20.0.

**Dry-run:** every step below was run on a throwaway worktree of `feature/api-and-spine-contracts` (C1) on 2026-10-14; the counts and messages are the real output.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your own clone). Branch **`feature/web-contract-types`** from an up-to-date `develop`, after every dependency in [[Build order]] is merged. Never commit to, or push, `develop` or `main`; PR to `develop`; Patrick merges.
- **Start state:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` → `Test Files  25 passed (25)`, `Tests  69 passed (69)` on `develop` with C1 merged. If yours differs, stop: you are not on the expected `develop`.
- **Front-end setup:** Node 22 (`web/.nvmrc`), `corepack enable` (yarn 1.22.22), the read-only npm token in your **home** `~/.npmrc` only (`web/README.md`), then `cd web && yarn install --frozen-lockfile`.
- **Run the tests** from the repo root with `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` (the parentheses keep your shell in the repo root). `--watch=false` stops Vitest staying in watch mode on a terminal. To run one file: `--include <path>`.
- **Front-end rules (non-negotiable):**
  - **Never compute a KPI in the browser** (D-001). Show what `/summary` returns; the only arithmetic allowed is rounding for display and layout positions.
  - **Never send scope in a request.** The server builds scope from the token; the UI only hides what the API would refuse.
  - **Never log, print or persist tokens** yourself (the OIDC library keeps its own state in `sessionStorage`; nothing in `localStorage`).
  - **One lock file: `web/yarn.lock`.** Add a package only with `yarn add <package>@<exact version>` and commit `package.json` and `yarn.lock` together. Never a `package-lock.json`. Never commit the npm token (`web/.npmrc` holds only the scope line).
  - Synthetic data only; no real names in fixtures or UI copy. No secrets anywhere (code, repo, vault, Slack). Region `eu-west-1`, Bedrock `eu.*` only (the back end's rules; you don't touch Python, `config.py` or `tools/`).
  - **Clean code (the lead's standard):** descriptive names, **no single-character names** (not even in arrow functions), no magic numbers or strings (name them as constants), nothing hardcoded that belongs in `portal-config.ts`. Settings live only in `core/config/portal-config.ts`.
  - **No layout or "meta" guard tests** (tests that police file placement). Test behaviour.
- **Stay in your files** (Mildred's list in the brief). This item touches only `web/package.json`, `web/src/app/core/api/testing/` *(new)*, `web/src/app/core/models/` and `web/src/app/core/format/format.ts`.
- **Cross-owner edits:** none in this item.
- **Commits:** small, one per task, with the message given. **No `Co-Authored-By` and no "Generated with" lines** in commits or the PR.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **Every contract field is present, with the same name and nullability**, in `summary.ts`: open `web/src/app/core/api/schema/summary.schema.json` and `entity.schema.json` side by side with the interfaces and tick each `required` key of each `$defs` entry.
2. `ajv` is a **dev** dependency and nothing outside `*.spec.ts` imports `core/api/testing/`: `grep -rn "api/testing" web/src --include=*.ts | grep -v spec.ts` prints nothing.
3. `yarn.lock` did not change, or changed only by the `ajv@8.20.0` key line: `git diff develop -- web/yarn.lock`.
4. The `Legacy…` renames touched nothing outside `summary.ts`: `git diff develop --stat` lists only the files in Tasks 1–3.
5. `yarn build` still passes (the validator imports JSON; the app build must not pull it in).

---

### Task 1: The contract validator

**Files:**
- Modify: `web/package.json` (dev dependency `ajv`)
- Create: `web/src/app/core/api/testing/contract-validator.ts` *(new)*, `web/src/app/core/api/testing/contract-validator.spec.ts` *(new)*

**Produces:** `contractErrors(name: ContractName, body: unknown): string[]` and `type ContractName` (the ten C1 schema names). **Consumes:** `web/src/app/core/api/schema/*.schema.json` (C1).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
git switch -c feature/web-contract-types
mkdir -p .superpowers && printf '# Ledger: F1a contract types\n' > .superpowers/ledger-F1a.md
cd web && corepack enable && yarn install --frozen-lockfile && cd ..
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
```
Expected: `Test Files  25 passed (25)` and `Tests  69 passed (69)`.

- [ ] **Step 2: Write the failing test.** Create `web/src/app/core/api/testing/contract-validator.spec.ts`:
```ts
import { contractErrors } from './contract-validator';

describe('contractErrors', () => {
  it('accepts a body that matches its exported JSON Schema', () => {
    expect(contractErrors('error', { error: 'out_of_scope', detail: 'Entity E2 is outside your access.' })).toEqual([]);
  });

  it('names a renamed, an unknown and a missing key', () => {
    expect(contractErrors('error', { code: 'out_of_scope', detail: 'Entity E2 is outside your access.' })).toEqual([
      "/ must have required property 'error'",
      '/ must NOT have additional properties (code)',
    ]);
  });

  it('rejects a value outside an enum', () => {
    expect(contractErrors('approve_response', { run_id: 'run-1', status: 'done' })).toEqual([
      '/status must be equal to one of the allowed values',
    ]);
  });
});
```

- [ ] **Step 3: Run it and watch it fail**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/api/testing 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: the build fails: `✘ [ERROR] TS2307: Cannot find module './contract-validator' or its corresponding type declarations.`

- [ ] **Step 4: Add `ajv` as a dev dependency** (it is already in `yarn.lock` at 8.20.0, through the Angular CLI):
```bash
cd web && yarn add -D ajv@8.20.0 && cd ..
git diff --stat web/package.json web/yarn.lock
```
Expected: `web/package.json | 5 ++++-` and **no** `yarn.lock` line (yarn also rewrites the one-line `"engines"` object over three lines; keep that).

- [ ] **Step 5: Implement.** Create `web/src/app/core/api/testing/contract-validator.ts`:
```ts
/**
 * Test-only: checks a body against the API contract's JSON Schemas (web/src/app/core/api/schema/, exported from
 * tools/api_schema.py by scripts/export_api_schema.py, D-021). Fixtures and adapters are tested with it, so a key
 * the back end renames fails here the day the schemas are re-exported.
 */
import Ajv2020, { ValidateFunction } from 'ajv/dist/2020';

import approveRequestSchema from '../schema/approve_request.schema.json';
import approveResponseSchema from '../schema/approve_response.schema.json';
import askRequestSchema from '../schema/ask_request.schema.json';
import askResponseSchema from '../schema/ask_response.schema.json';
import entitySchema from '../schema/entity.schema.json';
import errorSchema from '../schema/error.schema.json';
import publishRequestSchema from '../schema/publish_request.schema.json';
import publishResponseSchema from '../schema/publish_response.schema.json';
import rowsSchema from '../schema/rows.schema.json';
import summarySchema from '../schema/summary.schema.json';

/** One entry per `API_MODELS` key in tools/api_schema.py. */
const CONTRACT_SCHEMAS = {
  summary: summarySchema,
  entity: entitySchema,
  rows: rowsSchema,
  ask_request: askRequestSchema,
  ask_response: askResponseSchema,
  publish_request: publishRequestSchema,
  publish_response: publishResponseSchema,
  approve_request: approveRequestSchema,
  approve_response: approveResponseSchema,
  error: errorSchema,
} as const;

export type ContractName = keyof typeof CONTRACT_SCHEMAS;

const ROOT_PATH = '/';
const schemaCompiler = new Ajv2020({ allErrors: true });
const compiledValidators = new Map<ContractName, ValidateFunction>();

function validatorFor(name: ContractName): ValidateFunction {
  const cached = compiledValidators.get(name);
  if (cached) return cached;
  const compiled = schemaCompiler.compile(CONTRACT_SCHEMAS[name]);
  compiledValidators.set(name, compiled);
  return compiled;
}

/** Every way `body` breaks the named contract, as "<path> <problem>"; an empty list when it matches. */
export function contractErrors(name: ContractName, body: unknown): string[] {
  const validate = validatorFor(name);
  if (validate(body)) return [];
  return (validate.errors ?? []).map((error) => {
    const extraKey = typeof error.params['additionalProperty'] === 'string' ? ` (${error.params['additionalProperty']})` : '';
    return `${error.instancePath || ROOT_PATH} ${error.message}${extraKey}`;
  });
}
```

- [ ] **Step 6: Run it**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/api/testing 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: `Test Files  1 passed (1)`, `Tests  3 passed (3)`.

- [ ] **Step 7: Full suite and commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
git add web/package.json web/src/app/core/api/testing
git commit -m "Check API bodies against the exported contract schemas (ajv, test-only)"
```
Expected: `Test Files  26 passed (26)` and `Tests  72 passed (72)`.

**Task done when:** `git show --stat HEAD` lists exactly `web/package.json` and the two `testing/` files; `yarn test` reports 72 passed.

### Task 2: All 14 artefacts

**Files:**
- Modify: `web/src/app/core/models/citation.ts`, `web/src/app/core/format/format.ts`
- Create: `web/src/app/core/models/citation.spec.ts` *(new)*

**Produces:** `ARTEFACT_NAMES` with 14 entries (the `ArtefactName` type widens with it); a label for each in `artefactLabel`.

- [ ] **Step 1: Write the failing test.** Create `web/src/app/core/models/citation.spec.ts`:
```ts
import rowsSchema from '../api/schema/rows.schema.json';
import { artefactLabel } from '../format/format';
import { ARTEFACT_NAMES } from './citation';

describe('ARTEFACT_NAMES', () => {
  it('lists exactly the artefacts the API contract can cite, in its order', () => {
    expect([...ARTEFACT_NAMES]).toEqual(rowsSchema.$defs.Citation.properties.artefact.enum);
  });

  it('has a label for every artefact', () => {
    expect(ARTEFACT_NAMES.map(artefactLabel)).toEqual([
      'Entities',
      'Object inventory',
      'Load cycles',
      'Load runs',
      'Load errors',
      'Reconciliation results',
      'Defect log',
      'Workplan',
      'Cutover runbook',
      'Team roster',
      'Rate card',
      'Field mappings',
      'Value mappings',
      'Calendar',
    ]);
  });
});
```

- [ ] **Step 2: Run it and watch it fail**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/models 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: `Tests  2 failed (2)`, with `AssertionError: expected [ 'object_inventory', …(6) ] to deeply equal [ 'entities', …(13) ]` and `AssertionError: expected [ 'Object inventory', …(6) ] to deeply equal [ 'Entities', …(13) ]`.

- [ ] **Step 3: Implement.** In `web/src/app/core/models/citation.ts`, replace the `ARTEFACT_NAMES` constant with:
```ts
/** The 14 artefacts (tools/constants.py `ArtefactName`), in the order of the exported JSON Schema. */
export const ARTEFACT_NAMES = [
  'entities',
  'object_inventory',
  'load_cycles',
  'load_runs',
  'load_errors',
  'reconciliation_results',
  'defect_log',
  'workplan',
  'cutover_runbook',
  'team_roster',
  'rate_card',
  'field_mappings',
  'value_mappings',
  'calendar',
] as const;
```
In `web/src/app/core/format/format.ts`, replace `ARTEFACT_LABELS` with:
```ts
const ARTEFACT_LABELS: Record<ArtefactName, string> = {
  entities: 'Entities',
  object_inventory: 'Object inventory',
  load_cycles: 'Load cycles',
  load_runs: 'Load runs',
  load_errors: 'Load errors',
  reconciliation_results: 'Reconciliation results',
  defect_log: 'Defect log',
  workplan: 'Workplan',
  cutover_runbook: 'Cutover runbook',
  team_roster: 'Team roster',
  rate_card: 'Rate card',
  field_mappings: 'Field mappings',
  value_mappings: 'Value mappings',
  calendar: 'Calendar',
};
```

- [ ] **Step 4: Run it**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/models 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: `Test Files  1 passed (1)`, `Tests  2 passed (2)`. (If the first run after an edit still shows the old failure, run it once more: the build cache occasionally lags one edit. Ledger it if it happens twice.)

- [ ] **Step 5: Full suite and commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
git add web/src/app/core/models/citation.ts web/src/app/core/models/citation.spec.ts web/src/app/core/format/format.ts
git commit -m "All 14 artefacts the API can cite, in the contract's order, each with a label"
```
Expected: `Test Files  27 passed (27)` and `Tests  74 passed (74)`.

**Task done when:** `ARTEFACT_NAMES.length` is 14 (the test proves it); `yarn test` reports 74 passed.

### Task 3: The contract types

**Files:**
- Modify: `web/src/app/core/models/summary.ts`, `web/src/app/core/models/index.ts`
- Create: `web/src/app/core/models/error-response.ts` *(new)*, `web/src/app/core/models/contract-types.spec.ts` *(new)*

**Produces** (all exported from `core/models`): `SummaryResponse`, `OverallReconciled`, `PassRate`, `CycleTotals`, `OpenBlockers`, `Cutover`, `Capacity`, `RoleCapacity`, `Reconciled`, `EntityRow`, `EntityResponse`, `FailedReconciliation`, `CalendarConflict`, `ERROR_CODES`, `ErrorCode`, `ErrorResponse`; renames `LegacyOverallReconciled`, `LegacyRoleCapacity`. **Consumed by:** F1b, F2, Clement's F3–F5.

- [ ] **Step 1: Write the failing test.** Create `web/src/app/core/models/contract-types.spec.ts`:
```ts
import errorSchema from '../api/schema/error.schema.json';
import { contractErrors } from '../api/testing/contract-validator';
import { ERROR_CODES, EntityResponse, ErrorResponse, RowsResponse, SummaryResponse } from './index';

const E4_CUTOVER_EVIDENCE = [{ artefact: 'workplan', row_id: 'WP-034' }] as const;

const E4_CUTOVER = {
  entity_id: 'E4',
  cutover_forecast: '2027-01-23',
  cutover_baseline: '2027-01-17',
  days_remaining: 102,
  days_behind_plan: 6,
  live: false,
  evidence: [...E4_CUTOVER_EVIDENCE],
};

const E4_ROW: SummaryResponse['entities'][number] = {
  entity_id: 'E4',
  entity_name: 'Entity 4',
  business_role: 'Manufacturing',
  source_tier: 'Tier 3',
  source_description: 'Legacy ERP, tier 3, manufacturing',
  target_company_code: '4000',
  reconciled: {
    records_reconciled: 2000,
    records_in_scope: 10500,
    pct: 19.0,
    evidence: [{ artefact: 'reconciliation_results', row_id: 'RC-C3-E4-company_codes' }],
  },
  cutover: E4_CUTOVER,
  open_blockers: 3,
  status: 'Blocked',
};

const DEF_0412 = {
  reference: 'DEF-0412',
  entity_id: 'E4',
  blocker: 'Customer master tax ID mapping fails for 212 records',
  age_days: 18,
  owner_role: 'Data lead',
  evidence: [{ artefact: 'defect_log' as const, row_id: 'DEF-0412' }],
};

/** Each typed sample compiles against the TypeScript models AND validates against the exported JSON Schema. */
describe('contract types', () => {
  it('SummaryResponse matches summary.schema.json, including a missing final cutover', () => {
    const summary: SummaryResponse = {
      as_of: '2026-10-13',
      tenant_id: 't-01',
      programme_name: 'Group ERP consolidation',
      target_platform: 'Single cloud ERP, one chart of accounts',
      currency: 'USD',
      overall: { records_reconciled: 2000, records_in_scope: 10500, pct: 19.0 },
      pass_rate: {
        latest: { cycle_id: 'C3', records_matched: 4197, records_sent: 4409, pct: 95.2, evidence: [] },
        previous: null,
        target_pct: 98.0,
      },
      open_blockers: { count: 1, oldest_days: 18, blockers: [DEF_0412] },
      final_cutover: null,
      capacity: {
        month: '2026-10',
        people_used: 3,
        people_planned: 3,
        pct: 100.0,
        by_role: [
          { role: 'Tester', people_used: 3, people_planned: 3, pct: 100.0, evidence: [{ artefact: 'team_roster', row_id: '2026-10#P-024' }] },
        ],
      },
      entities: [E4_ROW],
    };
    expect(contractErrors('summary', summary)).toEqual([]);
  });

  it('EntityResponse matches entity.schema.json', () => {
    const entity: EntityResponse = {
      entity: E4_ROW,
      blockers: [DEF_0412],
      failing_reconciliations: [
        {
          recon_id: 'RC-C3-E4-customers',
          cycle_id: 'C3',
          entity_id: 'E4',
          object_id: 'customers',
          records_sent: '2410',
          records_rejected: '212',
          records_matched: '2198',
          match_rate_pct: '91.2',
          target_pct: '98.0',
          status: 'FAIL',
          evidence: [{ artefact: 'reconciliation_results', row_id: 'RC-C3-E4-customers' }],
        },
      ],
      calendar_conflicts: [
        { window_id: 'CAL-004', label: 'Year-end close', type: 'close', evidence: [{ artefact: 'calendar', row_id: 'CAL-004' }] },
      ],
    };
    expect(contractErrors('entity', entity)).toEqual([]);
  });

  it('RowsResponse and ErrorResponse match their schemas', () => {
    const rows: RowsResponse = {
      rows: [{ artefact: 'defect_log', row_id: 'DEF-0412', fields: { defect_id: 'DEF-0412', status: 'Open' } }],
      missing: [{ artefact: 'defect_log', row_id: 'DEF-0447' }],
    };
    const error: ErrorResponse = { error: 'out_of_scope', detail: 'Entity E2 is outside your access.' };
    expect(contractErrors('rows', rows)).toEqual([]);
    expect(contractErrors('error', error)).toEqual([]);
  });

  it('ERROR_CODES are exactly the error codes of error.schema.json', () => {
    expect([...ERROR_CODES]).toEqual(errorSchema.properties.error.enum);
  });
});
```

- [ ] **Step 2: Run it and watch it fail**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/models 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: the build fails with `✘ [ERROR] TS2305: Module '"./index"' has no exported member 'EntityResponse'.` (and the same for `SummaryResponse`, and `TS2724 … 'ErrorResponse'`).

- [ ] **Step 3: Rename the two clashing legacy types** in `web/src/app/core/models/summary.ts` (nothing else uses them):
  - `  overall: OverallReconciled;` (in `Summary`) → `  overall: LegacyOverallReconciled;`
  - `  capacity: RoleCapacity[];` (in `Summary`) → `  capacity: LegacyRoleCapacity[];`
  - `export interface OverallReconciled {` → `/** Legacy (pre-D-021) shape; removed in F1b. */` on the line above, and `export interface LegacyOverallReconciled {`
  - `export interface RoleCapacity {` (the one with `planned`, `actual`, `utilisation_pct`) → the same comment above, and `export interface LegacyRoleCapacity {`

- [ ] **Step 4: Append the contract types** to the end of `web/src/app/core/models/summary.ts` (after one blank line):
```ts
// ---- The API contract (D-021): tools/api_schema.py, exported to core/api/schema/*.schema.json ----------------
// Field for field what the back end sends. Every percentage arrives with one decimal (58.1); the screen only rounds.

/** GET /summary: exactly tools/metrics.py `portfolio_summary()`, filtered to the caller's scope. */
export interface SummaryResponse {
  as_of: string;
  tenant_id: string;
  programme_name: string;
  target_platform: string;
  currency: string;
  overall: OverallReconciled;
  pass_rate: PassRate;
  open_blockers: OpenBlockers;
  /** null when no entity in the scope still has a cutover ahead (an E1-only scope). */
  final_cutover: Cutover | null;
  capacity: Capacity;
  entities: EntityRow[];
}

export interface OverallReconciled {
  records_reconciled: number;
  records_in_scope: number;
  pct: number;
}

export interface PassRate {
  latest: CycleTotals | null;
  previous: CycleTotals | null;
  target_pct: number;
}

export interface CycleTotals {
  cycle_id: string;
  records_matched: number;
  records_sent: number;
  pct: number;
  evidence: Citation[];
}

export interface OpenBlockers {
  count: number;
  oldest_days: number;
  blockers: Blocker[];
}

export interface Cutover {
  entity_id: string;
  cutover_forecast: string;
  cutover_baseline: string;
  days_remaining: number;
  days_behind_plan: number;
  live: boolean;
  evidence: Citation[];
}

export interface Capacity {
  /** "2026-10" */
  month: string;
  people_used: number;
  people_planned: number;
  pct: number;
  by_role: RoleCapacity[];
}

export interface RoleCapacity {
  role: string;
  people_used: number;
  people_planned: number;
  pct: number;
  evidence: Citation[];
}

export interface Reconciled {
  records_reconciled: number;
  records_in_scope: number;
  pct: number;
  evidence: Citation[];
}

export interface EntityRow {
  entity_id: string;
  entity_name: string;
  business_role: string;
  source_tier: string;
  source_description: string;
  target_company_code: string;
  reconciled: Reconciled;
  cutover: Cutover;
  open_blockers: number;
  /** The schema says string; tools/constants.py `EntityStatus` holds exactly these four values. */
  status: EntityStatus;
}

/** GET /entity/{id} */
export interface EntityResponse {
  entity: EntityRow;
  blockers: Blocker[];
  failing_reconciliations: FailedReconciliation[];
  calendar_conflicts: CalendarConflict[];
}

/** One failing reconciliation, every value as text, as the CSV holds it (metrics.FAILED_RECONCILIATION_FIELDS). */
export interface FailedReconciliation {
  recon_id: string;
  cycle_id: string;
  entity_id: string;
  object_id: string;
  records_sent: string;
  records_rejected: string;
  records_matched: string;
  match_rate_pct: string;
  target_pct: string;
  status: string;
  evidence: Citation[];
}

export interface CalendarConflict {
  window_id: string;
  label: string;
  type: string;
  evidence: Citation[];
}
```

- [ ] **Step 5: The error body.** Create `web/src/app/core/models/error-response.ts`:
```ts
/** Every API error body (tools/api_schema.py `ErrorResponse`, D-021). */
export const ERROR_CODES = ['invalid_input', 'unauthorized', 'forbidden', 'out_of_scope', 'not_found'] as const;

export type ErrorCode = (typeof ERROR_CODES)[number];

export interface ErrorResponse {
  error: ErrorCode;
  detail: string;
}
```
In `web/src/app/core/models/index.ts`, add `export * from './error-response';` directly after `export * from './citation';`.

- [ ] **Step 6: Run it**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/models 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: `Test Files  2 passed (2)`, `Tests  6 passed (6)`.

- [ ] **Step 7: Full suite, build, commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
(cd web && yarn build 2>&1 | grep -E "ERROR|bundle generation complete")
git add web/src/app/core/models
git commit -m "API contract types next to today's, each proven against its exported schema (D-021)"
```
Expected: `Test Files  28 passed (28)` and `Tests  78 passed (78)`. The build prints `Application bundle generation complete.` and no `ERROR`.

**Task done when:** `contract-types.spec.ts` passes 4 tests; `yarn test` reports 78 passed; `yarn build` is green.

### Task 4: Review, then PR (after Mildred's OK)
- [ ] **Step 1:** Work through the Review Focus by hand; write each result in the ledger.
- [ ] **Step 2:** `git diff develop --stat` lists only: `web/package.json`, `web/src/app/core/api/testing/contract-validator.ts`, `…/contract-validator.spec.ts`, `web/src/app/core/models/citation.ts`, `citation.spec.ts`, `contract-types.spec.ts`, `error-response.ts`, `index.ts`, `summary.ts`, `web/src/app/core/format/format.ts`. Expected: 10 files.
- [ ] **Step 3:** Fresh review of the diff against [[F1a - Contract types and the 14 artefacts - spec]]; fix critical and important findings test-first.
- [ ] **Step 4 (with Mildred's OK only):** `git push -u origin feature/web-contract-types`; open the PR to `develop` titled "Front end: contract types and all 14 artefacts (F1a)". Body: what changed, `yarn test` 78 passed, the rulings, deferred minors. No attribution lines.
- [ ] **Step 5:** Set F1a's status in [[Build order]] to `in review (PR #nn)`, then `merged` when Patrick merges.

**Task done when:** the PR is open to `develop` with a green Jenkins front-end build, and [[Build order]] shows `in review (PR #nn)`.

## Never
- Compute a KPI, a status or a date in the browser; show what the API returns.
- Send scope (role, entities, tenant) in a request body, query string or header.
- Log, print or store a token yourself.
- Add a `package-lock.json`, or change `yarn.lock` other than with `yarn add`.
- Commit the npm token, a password or any secret.
- Push to `develop` or `main`, or add attribution lines.
- Edit a file in `web/src/app/core/api/schema/` by hand (it is generated; ask Patrick).
- Remove today's types in this item (F1b does, together with the screen).

## Done means
- [ ] **Tests:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` prints `Test Files  28 passed (28)` and `Tests  78 passed (78)` on the branch. *Verify:* run it.
- [ ] **14 artefacts:** `grep -c "^  '" web/src/app/core/models/citation.ts` prints `14`. *Verify:* run it.
- [ ] **Types match the schema:** `web/src/app/core/models/contract-types.spec.ts` exists with 4 passing tests. *Verify:* `(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/models/contract-types.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)` → `Tests  4 passed (4)`.
- [ ] **One lock file, ajv a dev dependency:** `grep -n '"ajv": "8.20.0"' web/package.json` prints one line inside `devDependencies`; `ls web/package-lock.json` fails. *Verify:* run both.
- [ ] **Build green:** `(cd web && yarn build)` ends with `Application bundle generation complete.` *Verify:* run it.
- [ ] **PR:** open to `develop` titled "Front end: contract types and all 14 artefacts (F1a)", no attribution lines; [[Build order]] row F1a says `in review (PR #nn)` or `merged`. *Verify:* `gh pr list --head feature/web-contract-types`.

Related: [[F1a - Contract types and the 14 artefacts - spec]], [[Build order]], [[How to execute a plan]]
