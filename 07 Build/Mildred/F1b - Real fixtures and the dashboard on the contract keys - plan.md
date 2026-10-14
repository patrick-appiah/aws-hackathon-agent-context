---
tags: [build, plan, area/frontend]
id: F1b
owner: Mildred
spec: "[[F1b - Real fixtures and the dashboard on the contract keys - spec]]"
status: ready
updated: 2026-10-14
---
# F1b: real fixtures and the dashboard on the contract keys (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[F1b - Real fixtures and the dashboard on the contract keys - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger as a `Ruling:` line.
3. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Mildred - front end]].
4. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
5. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
6. [[F1a - Contract types and the 14 artefacts - spec]] and its plan: what is already in place (`contractErrors`, the contract types).
7. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

**Goal:** the fixtures are exported from the real core, and the one screen reads the contract's keys, showing exactly the back end's figures.

**Architecture:** data flows `fixtures/*.json` → `MockPortalApi` (or `HttpPortalApi`) → `DashboardStore` (`SummaryResponse`) → pure view builders (`build*View`) → components. The builders select and word; they never compute a figure.

**Tech stack:** Angular 22 (signals, standalone components), TypeScript 6, Vitest through `ng test`; Python 3.11 + uv only to export the fixtures.

**Dry-run:** done on 2026-10-14 in a throwaway worktree of C1 with F1a applied; the counts and messages below are the real output. The big switch (Task 1) is one commit because the types, the fixtures and the views only compile together.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your own clone). Branch **`feature/web-dashboard-contract`** from an up-to-date `develop`, after every dependency in [[Build order]] is merged. Never commit to, or push, `develop` or `main`; PR to `develop`; Patrick merges.
- **Start state:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` → `Test Files  28 passed (28)`, `Tests  78 passed (78)` (C1 and F1a merged). If yours differs, stop.
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
- **Stay in your files** (Mildred's list in the brief). This item touches `web/src/app/core/` (api, models, format, config), `web/src/app/features/dashboard/`, `web/src/app/shared/ui/awaiting-api/` (deleted), `web/scripts/`, `web/package.json`, `web/README.md`, and one line each in `HANDOFF.md` and `DEMO.md`.
- **Cross-owner edits:** **Clement's `web/src/app/features/ask/ask-panel/ask-panel.ts`**: exactly the three lines in Task 1 Step 6 (the type switch forces them). Message Clement before you commit Task 1. **`DEMO.md`** (Clement's, with Patrick): one pre-flight line in Task 3.
- **Commits:** small, one per task, with the message given. **No `Co-Authored-By` and no "Generated with" lines** in commits or the PR.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **The screen in mock mode shows exactly the spec's figures** (§1 "Success means"): `(cd web && yarn start)`, open http://localhost:4200, compare every number, then switch user to the entity lead and compare again.
2. **No KPI is computed in the browser:** `git diff develop -- web/src/app/features | grep -E "^\+.*(reduce|\.length \*| / |Math\.(round|floor|ceil))"` shows only `capacityScale` (bar scale, layout) and the timeline's `position()` (layout). Anything else is a bug.
3. **The fixtures are the exporter's, byte for byte:** run the export again; `git status --short web/src/app/core/api/fixtures` prints nothing.
4. **Nothing still reads a removed field:** `grep -rn "pass_rate_by_cycle\|capacity_people\|source_systems\|days_to_final_cutover\|awaitingField\|AwaitingApi" web/src` prints nothing.
5. **The timeline at narrow widths:** at 375 px wide the timeline scrolls inside its card and the page never scrolls sideways.

---

### Task 1: The switch: fixtures, data layer and dashboard on the contract

**Files:**
- Regenerate: `web/src/app/core/api/fixtures/summary.json`, `entity-E1.json` … `entity-E4.json`, `rows.json`; create `summary-entity-lead-E4.json` *(new)*
- Create (git-ignored, not committed): `.superpowers/f1b_export_fixtures.py`
- Modify: `web/src/app/core/models/summary.ts`, `core/api/portal-api.ts`, `core/api/http-portal-api.ts`, `core/api/mock-portal-api.ts`, `core/format/format.ts`, `core/config/display-rules.ts`, everything under `web/src/app/features/dashboard/` named below, and Clement's `features/ask/ask-panel/ask-panel.ts` (3 lines)
- Create: `web/src/app/features/dashboard/source-target-banner/source-target-banner.spec.ts` *(new)*
- Delete: `web/src/app/shared/ui/awaiting-api/awaiting-api.ts`

**Produces:** `PortalApi.summary(): Promise<SummaryResponse>`, `PortalApi.entity(entityId): Promise<EntityResponse>`, `PERCENT_DISPLAY_DECIMALS`, `PASS_RATE_DISPLAY_DECIMALS`, `formatPassRate(value: number): string`, `buildKpiViews(summary: SummaryResponse)`, `buildEntityRows(entities: readonly EntityRow[])`, `buildBlockersView(blockers, entities: readonly EntityRow[], total, shown)`, `buildCapacityView(capacity: Capacity)`, `buildTimelineView(entities: readonly EntityRow[], asOf: string)`. **Consumes:** F1a's types and `contractErrors`; C1's `tools/api_schema.py` builders (`summary_response`, `entity_response`, `rows_response`).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
git switch -c feature/web-dashboard-contract
mkdir -p .superpowers && printf '# Ledger: F1b dashboard on the contract\n' > .superpowers/ledger-F1b.md
uv sync
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
```
Expected: `Test Files  28 passed (28)`, `Tests  78 passed (78)`.

- [ ] **Step 2: Export the fixtures from the real core.** Create `.superpowers/f1b_export_fixtures.py` (git-ignored; L4 owns the committed exporter):
```python
"""F1b, until Linus's scripts/export_summary.py (L4) is merged: write the mock fixtures from the real core.

Run from the repo root: uv run python .superpowers/f1b_export_fixtures.py
Writes the six files L4 will write (summary.json, entity-E1.json ... entity-E4.json, rows.json) plus
summary-entity-lead-E4.json (the E4 lead's summary, for the mock role switcher) to web/src/app/core/api/fixtures/.
rows.json holds every row the six L4 files cite, exactly as L4 builds it.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.csv_repo import CsvRepository  # noqa: E402
from config import DEFAULT_ARTEFACTS_URI, DEFAULT_TENANT_ID, REPO_ROOT
from tools.api_schema import entity_response, rows_response, summary_response
from tools.constants import ALL_ENTITIES_WILDCARD
from tools.models import Citation, Scope

FIXTURE_FOLDER = REPO_ROOT / "web" / "src" / "app" / "core" / "api" / "fixtures"
ENTITY_IDS = ("E1", "E2", "E3", "E4")
LEAD_ENTITY_ID = "E4"
JSON_INDENT = 2

repository = CsvRepository(DEFAULT_ARTEFACTS_URI)
cfo_scope = Scope(user_id="u-demo", role="cfo", tenant_id=DEFAULT_TENANT_ID, entity_ids=(ALL_ENTITIES_WILDCARD,))
lead_scope = Scope(user_id="u-demo-entity-lead-e4", role="entity_lead", tenant_id=DEFAULT_TENANT_ID,
                   entity_ids=(LEAD_ENTITY_ID,))


def citations_in(value) -> list[Citation]:
    """Every {artefact, row_id} pair anywhere inside a JSON value, rows (which carry `fields`) excluded."""
    if isinstance(value, dict):
        own = [Citation(artefact=value["artefact"], row_id=value["row_id"])] if {
            "artefact", "row_id"} <= value.keys() and "fields" not in value else []
        return own + [citation for child in value.values() for citation in citations_in(child)]
    if isinstance(value, list):
        return [citation for child in value for citation in citations_in(child)]
    return []


def write(file_name: str, body: dict) -> None:
    (FIXTURE_FOLDER / file_name).write_text(json.dumps(body, indent=JSON_INDENT) + "\n", encoding="utf-8")
    print(FIXTURE_FOLDER / file_name)


bodies = {"summary.json": summary_response(repository, cfo_scope).model_dump(mode="json")}
for entity_id in ENTITY_IDS:
    bodies[f"entity-{entity_id}.json"] = entity_response(repository, cfo_scope, entity_id).model_dump(mode="json")
all_citations = [citation for body in bodies.values() for citation in citations_in(body)]
bodies["rows.json"] = rows_response(repository, cfo_scope, all_citations).model_dump(mode="json")
bodies[f"summary-entity-lead-{LEAD_ENTITY_ID}.json"] = summary_response(repository, lead_scope).model_dump(mode="json")
for file_name, body in bodies.items():
    write(file_name, body)
```
Run it from the repo root:
```bash
uv run python .superpowers/f1b_export_fixtures.py | wc -l
python3 -c "import json; body = json.load(open('web/src/app/core/api/fixtures/rows.json')); print(len(body['rows']), body['missing'])"
```
Expected: `7`, then `139 []`. **If L4 is merged:** also run `uv run python scripts/export_summary.py`; then `git status --short web/src/app/core/api/fixtures` must list the same files as before that run, unchanged (the two exporters agree). If they differ, stop and ask Linus.

- [ ] **Step 3: Write the failing tests.** Replace (or create) each file with exactly this content:

- `web/src/app/core/api/fixtures.spec.ts`:
```ts
import { Citation, ENTITY_STATUSES } from '../models';
import approveFixture from './fixtures/approve.json';
import askEntity4Fixture from './fixtures/ask-E4.json';
import askPartialFixture from './fixtures/ask-partial.json';
import entity1Fixture from './fixtures/entity-E1.json';
import entity2Fixture from './fixtures/entity-E2.json';
import entity3Fixture from './fixtures/entity-E3.json';
import entity4Fixture from './fixtures/entity-E4.json';
import publishFixture from './fixtures/publish.json';
import rowsFixture from './fixtures/rows.json';
import summaryEntityLead4Fixture from './fixtures/summary-entity-lead-E4.json';
import summaryFixture from './fixtures/summary.json';
import { ContractName, contractErrors } from './testing/contract-validator';

/** Every {artefact, row_id} pair anywhere inside a fixture (rows themselves, which carry `fields`, excluded). */
function citationsIn(fixture: unknown): Citation[] {
  const found: Citation[] = [];
  JSON.stringify(fixture, (_key, value: unknown) => {
    if (value && typeof value === 'object' && 'artefact' in value && 'row_id' in value && !('fields' in value)) {
      found.push(value as Citation);
    }
    return value;
  });
  return found;
}

const rowKeys = new Set(rowsFixture.rows.map((row) => `${row.artefact}:${row.row_id}`));

/** The fixtures exported from the real core, each with the contract it must match. */
const EXPORTED_FIXTURES: [string, ContractName, unknown][] = [
  ['summary.json', 'summary', summaryFixture],
  ['summary-entity-lead-E4.json', 'summary', summaryEntityLead4Fixture],
  ['entity-E1.json', 'entity', entity1Fixture],
  ['entity-E2.json', 'entity', entity2Fixture],
  ['entity-E3.json', 'entity', entity3Fixture],
  ['entity-E4.json', 'entity', entity4Fixture],
  ['rows.json', 'rows', rowsFixture],
];

/** Every exported fixture whose figures carry citations; the row viewer must find each cited row. */
const CITED_FIXTURES = EXPORTED_FIXTURES.filter(([fileName]) => fileName !== 'rows.json');

describe('API fixtures', () => {
  for (const [fileName, contract, fixture] of EXPORTED_FIXTURES) {
    it(`${fileName} matches the ${contract} contract`, () => {
      expect(contractErrors(contract, fixture)).toEqual([]);
    });
  }

  for (const [fileName, , fixture] of CITED_FIXTURES) {
    it(`${fileName}: every citation resolves to a row in rows.json`, () => {
      const citations = citationsIn(fixture);
      expect(citations.length).toBeGreaterThan(0);
      expect(citations.filter((citation) => !rowKeys.has(`${citation.artefact}:${citation.row_id}`))).toEqual([]);
    });
  }

  it('summary.json holds the figures of the one screen (tools/metrics.py, CFO scope)', () => {
    expect(summaryFixture.overall).toEqual({ records_reconciled: 18420, records_in_scope: 31700, pct: 58.1 });
    expect([summaryFixture.pass_rate.latest?.pct, summaryFixture.pass_rate.previous?.pct, summaryFixture.pass_rate.target_pct]).toEqual([96.4, 94.8, 98]);
    expect([summaryFixture.open_blockers.count, summaryFixture.open_blockers.oldest_days]).toEqual([7, 18]);
    expect(summaryFixture.final_cutover).toMatchObject({ entity_id: 'E4', cutover_forecast: '2027-01-23', days_remaining: 102, days_behind_plan: 6 });
    expect([summaryFixture.capacity.people_used, summaryFixture.capacity.people_planned]).toEqual([38, 37]);
    expect(summaryFixture.entities.map((entity) => [entity.entity_id, entity.status])).toEqual([
      ['E1', 'Live'],
      ['E2', 'On track'],
      ['E3', 'At risk'],
      ['E4', 'Blocked'],
    ]);
    for (const entity of summaryFixture.entities) expect(ENTITY_STATUSES).toContain(entity.status);
  });

  it('marks the agent responses as mock', () => {
    for (const mock of [askEntity4Fixture, askPartialFixture, publishFixture, approveFixture]) {
      expect(mock._mock).toContain('Mock response');
    }
    expect(askPartialFixture.partial).toBe(true);
    expect(publishFixture.status).toBe('awaiting_approval');
  });
});
```

- `web/src/app/core/format/format.spec.ts`:
```ts
import {
  citationLabel,
  dayOffset,
  entityLabel,
  formatCount,
  formatDayMonth,
  formatDays,
  formatFullDate,
  formatMonth,
  formatPassRate,
  formatPercent,
  roleLabel,
} from './format';

describe('format', () => {
  it("formats counts, and rounds the API's one-decimal percentages to whole numbers", () => {
    expect(formatCount(31700)).toBe('31,700');
    expect([58.1, 88.5, 102.7, 100].map(formatPercent)).toEqual(['58%', '89%', '103%', '100%']);
  });

  it('keeps one decimal on the reconciliation pass rate, as the design shows it', () => {
    expect([96.4, 94.8, 95.2, 98].map(formatPassRate)).toEqual(['96.4%', '94.8%', '95.2%', '98%']);
  });

  it('formats calendar dates the way the design shows them', () => {
    expect(formatDayMonth('2026-10-13')).toBe('13 Oct');
    expect(formatFullDate('2027-01-23')).toBe('23 Jan 2027');
    expect(formatMonth('2026-07-01')).toBe('Jul');
    expect(formatDayMonth('2026-09-05')).toBe('5 Sep');
  });

  it('labels days, roles, entities and citations', () => {
    expect(formatDays(1)).toBe('1 day');
    expect(formatDays(18)).toBe('18 days');
    expect(roleLabel('delivery_lead')).toBe('Delivery lead');
    expect(entityLabel('E4')).toBe('Entity 4');
    expect(citationLabel({ artefact: 'defect_log', row_id: 'DEF-0412' })).toBe('Defect log, DEF-0412');
  });

  it('measures the distance between two dates in whole days', () => {
    expect(dayOffset('2026-10-13', '2026-10-14')).toBe(86_400_000);
  });
});
```

- `web/src/app/features/dashboard/kpi-row/kpi-view.spec.ts`:
```ts
import summaryFixture from '../../../core/api/fixtures/summary.json';
import { SummaryResponse } from '../../../core/models';
import { buildKpiViews } from './kpi-view';

const SUMMARY = summaryFixture as unknown as SummaryResponse;

describe('buildKpiViews', () => {
  it('shows the API figures as the design words them: whole percentages, the pass rate to one decimal', () => {
    const [records, passRate, blockers, cutover, capacity] = buildKpiViews(SUMMARY);
    expect(records.value?.text).toBe('58%');
    expect(records.progress?.value).toBe(58.1);
    expect(records.detail?.text).toBe('18,420 of 31,700 records');
    expect(passRate.value?.text).toBe('96.4%');
    expect(passRate.badge?.text).toBe('Below the 98% target');
    expect(passRate.detail?.text).toBe('Cycle C3, up from 94.8% in cycle C2');
    expect(blockers.value?.text).toBe('7');
    expect(blockers.badge?.text).toBe('Oldest open 18 days');
    expect(blockers.detail?.text).toBe('2 on entity 2, 2 on entity 3, 3 on entity 4');
    expect(cutover.value?.text).toBe('102');
    expect(cutover.badge?.text).toBe('6 days behind plan');
    expect(cutover.detail?.text).toBe('Entity 4 cutover weekend, 23 Jan 2027');
    expect(capacity.value?.text).toBe('103%');
    expect(capacity.badge?.text).toBe('Slightly over plan');
    expect(capacity.detail?.text).toBe('38 people used, 37 planned');
  });

  it('cites every figure: 58% opens the reconciled rows of all four entities', () => {
    const cards = buildKpiViews(SUMMARY);
    expect(cards[0].value?.citations).toHaveLength(49);
    expect(cards[0].value?.citations?.every((citation) => citation.artefact === 'reconciliation_results')).toBe(true);
    for (const card of cards) {
      expect(card.value?.citations?.length).toBeGreaterThan(0);
      expect(card.detail?.citations?.length).toBeGreaterThan(0);
    }
  });

  it('says so when the scope has no reconciled cycle and no cutover ahead', () => {
    const liveOnly: SummaryResponse = {
      ...SUMMARY,
      pass_rate: { latest: null, previous: null, target_pct: 98 },
      final_cutover: null,
    };
    const [, passRate, , cutover] = buildKpiViews(liveOnly);
    expect(passRate.emptyText).toBe('No load cycle has been reconciled yet.');
    expect(cutover.emptyText).toBe('Every entity you can see is live.');
    expect(cutover.value).toBeUndefined();
  });
});
```

- `web/src/app/features/dashboard/entities-table/entities-view.spec.ts`:
```ts
import summaryFixture from '../../../core/api/fixtures/summary.json';
import { SummaryResponse } from '../../../core/models';
import { buildEntityRows } from './entities-view';

const SUMMARY = summaryFixture as unknown as SummaryResponse;

describe('buildEntityRows', () => {
  it('shows each entity as the design does, from the API figures', () => {
    const rows = buildEntityRows(SUMMARY.entities);
    expect(rows.map((row) => [row.name, row.sourceSystem, row.reconciledText, row.percentText, row.status.text])).toEqual([
      ['Entity 1', 'Legacy ERP, tier 1, finance core', '6,200 of 6,200', '100%', 'Live'],
      ['Entity 2', 'Legacy ERP, tier 2, regional operations', '5,400 of 6,100', '89%', 'On track'],
      ['Entity 3', 'Legacy ERP, tier 2, distribution', '4,820 of 8,900', '54%', 'At risk'],
      ['Entity 4', 'Legacy ERP, tier 3, manufacturing', '2,000 of 10,500', '19%', 'Blocked'],
    ]);
    expect(rows.map((row) => row.status.tone)).toEqual(['success', 'success', 'warning', 'danger']);
    expect(rows.map((row) => row.live)).toEqual([true, false, false, false]);
    expect(rows.every((row) => row.citations.length > 0)).toBe(true);
  });
});
```

- `web/src/app/features/dashboard/blockers-table/blockers-view.spec.ts`:
```ts
import summaryFixture from '../../../core/api/fixtures/summary.json';
import { SummaryResponse } from '../../../core/models';
import { buildBlockersView } from './blockers-view';

const SUMMARY = summaryFixture as unknown as SummaryResponse;
const BLOCKERS = SUMMARY.open_blockers.blockers;

describe('buildBlockersView', () => {
  it('lists the five oldest, as the design does', () => {
    const view = buildBlockersView(BLOCKERS, SUMMARY.entities, 7, 5);
    expect(view.caption).toBe('Showing the 5 oldest of 7 open blockers.');
    expect(view.hiddenCount).toBe(2);
    expect(view.rows.map((row) => [row.reference, row.entity, row.age.text, row.age.tone, row.ownerRole])).toEqual([
      ['DEF-0412', 'Entity 4', '18 days', 'danger', 'Data lead'],
      ['DEF-0431', 'Entity 3', '14 days', 'warning', 'Finance lead'],
      ['RB-014', 'Entity 4', '9 days', 'warning', 'Delivery lead'],
      ['DEF-0447', 'Entity 2', '6 days', 'neutral', 'Data lead'],
      ['WP-022', 'Entity 4', '4 days', 'neutral', 'Platform lead'],
    ]);
    expect(view.rows.every((row) => row.citations.length > 0)).toBe(true);
  });

  it('shows them all when asked', () => {
    const view = buildBlockersView(BLOCKERS, SUMMARY.entities, 7, BLOCKERS.length);
    expect(view.rows.length).toBe(7);
    expect(view.caption).toBe('Showing all 7 open blockers, oldest first.');
  });
});
```

- `web/src/app/features/dashboard/capacity-card/capacity-view.spec.ts`:
```ts
import summaryFixture from '../../../core/api/fixtures/summary.json';
import { capacityScale } from '../../../core/config/display-rules';
import { SummaryResponse } from '../../../core/models';
import { buildCapacityView } from './capacity-view';

const CAPACITY = (summaryFixture as unknown as SummaryResponse).capacity;

describe('buildCapacityView', () => {
  it('lists each role in the API order with people used and planned, on one shared scale', () => {
    const view = buildCapacityView(CAPACITY);
    expect(view.scale).toBe(16);
    expect(view.rows.map((row) => [row.role, row.countsText])).toEqual([
      ['Tester', '8 used, 6 planned'],
      ['Data migration engineer', '14 used, 12 planned'],
      ['Functional consultant', '9 used, 9 planned'],
      ['Client subject expert', '7 used, 10 planned'],
    ]);
    expect(view.rows.every((row) => row.citations.length > 0)).toBe(true);
  });

  it('rounds the scale up to the next step', () => {
    expect([1, 4, 5, 14, 17].map(capacityScale)).toEqual([4, 4, 8, 16, 20]);
  });
});
```

- `web/src/app/features/dashboard/timeline/timeline-view.spec.ts`:
```ts
import summaryFixture from '../../../core/api/fixtures/summary.json';
import { SummaryResponse } from '../../../core/models';
import { buildTimelineView } from './timeline-view';

const SUMMARY = summaryFixture as unknown as SummaryResponse;

describe('buildTimelineView', () => {
  const view = buildTimelineView(SUMMARY.entities, SUMMARY.as_of);

  it('runs the month axis from the first cutover to the month after the last', () => {
    expect(view.months.map((month) => month.label)).toEqual(['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan']);
    expect(view.months[0].leftPercent).toBe(0);
    expect(view.todayLabel).toBe('Today, 13 Oct');
  });

  it("marks each entity's forecast cutover, from entities[].cutover", () => {
    expect(view.rows.map((row) => row.cutoverText)).toEqual(['Cutover 8 Aug', 'Cutover 24 Oct', 'Cutover 12 Dec', 'Cutover 23 Jan']);
    for (const row of view.rows) {
      expect(row.cutoverPercent).toBeGreaterThanOrEqual(0);
      expect(row.cutoverPercent).toBeLessThanOrEqual(100);
      expect(row.citations.length).toBeGreaterThan(0);
    }
  });

  it('draws the slip only where the API says the entity is behind plan, and the live bar only for a live entity', () => {
    expect(view.rows.map((row) => row.segments.map((segment) => segment.kind))).toEqual([
      ['live'],
      [],
      [],
      ['slip'],
    ]);
    const entity4 = view.rows[3];
    expect(entity4.baselinePercent).toBeLessThan(entity4.cutoverPercent);
    expect(entity4.summary).toBe('Entity 4: cutover weekend 23 Jan 2027, planned for 17 Jan 2027.');
    expect(view.rows[0].summary).toBe('Entity 1: cutover weekend 8 Aug 2026, on the planned date; live.');
  });
});
```

- `web/src/app/features/dashboard/source-target-banner/source-target-banner.spec.ts`:
```ts
import { TestBed } from '@angular/core/testing';

import summaryFixture from '../../../core/api/fixtures/summary.json';
import { SummaryResponse } from '../../../core/models';
import { SourceTargetBanner } from './source-target-banner';

const SUMMARY = summaryFixture as unknown as SummaryResponse;

describe('SourceTargetBanner', () => {
  it('shows one source system per entity moving onto the target platform', async () => {
    const fixture = TestBed.createComponent(SourceTargetBanner);
    fixture.componentRef.setInput('entities', SUMMARY.entities);
    fixture.componentRef.setInput('targetPlatform', SUMMARY.target_platform);
    await fixture.whenStable();
    const boldTexts = [...(fixture.nativeElement as HTMLElement).querySelectorAll('strong')].map((element) => element.textContent);
    expect(boldTexts).toEqual(['4 source systems', 'Single cloud ERP, one chart of accounts']);
  });
});
```

- `web/src/app/core/api/mock-portal-api.spec.ts`:
```ts
import { TestBed } from '@angular/core/testing';

import { PORTAL_CONFIG, PORTAL_CONFIG_VALUES } from '../config/portal-config';
import { Scope } from '../models';
import { SessionStore } from '../session/session-store';
import { MockPortalApi } from './mock-portal-api';

const ENTITY_4_LEAD: Scope = { user_id: 'u-e4', role: 'entity_lead', tenant_id: 't-01', entity_ids: ['E4'] };
const ENTITY_2_AND_4_LEAD: Scope = { user_id: 'u-e2-e4', role: 'entity_lead', tenant_id: 't-01', entity_ids: ['E2', 'E4'] };

describe('MockPortalApi', () => {
  let api: MockPortalApi;
  let session: SessionStore;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [MockPortalApi, { provide: PORTAL_CONFIG, useValue: { ...PORTAL_CONFIG_VALUES, mockLatencyMs: 0 } }],
    });
    api = TestBed.inject(MockPortalApi);
    session = TestBed.inject(SessionStore);
  });

  it('returns the whole-programme summary to the CFO', async () => {
    const summary = await api.summary();
    expect(summary.entities.map((entity) => entity.entity_id)).toEqual(['E1', 'E2', 'E3', 'E4']);
    expect(summary.overall).toEqual({ records_reconciled: 18420, records_in_scope: 31700, pct: 58.1 });
  });

  it("returns the server's own E4 summary to the E4 lead, not a filtered copy", async () => {
    session.setScope(ENTITY_4_LEAD);
    const summary = await api.summary();
    expect(summary.entities.map((entity) => entity.entity_id)).toEqual(['E4']);
    expect(summary.overall.pct).toBe(19.0);
    expect(summary.open_blockers.count).toBe(3);
    expect(summary.pass_rate.latest?.pct).toBe(95.2);
  });

  it('has no summary for a scope it holds no fixture for', async () => {
    session.setScope(ENTITY_2_AND_4_LEAD);
    await expect(api.summary()).rejects.toMatchObject({ status: 404 });
  });

  it('refuses another entity with a 403', async () => {
    session.setScope(ENTITY_4_LEAD);
    await expect(api.entity('E2')).rejects.toMatchObject({ status: 403 });
    await expect(api.ask({ entity_id: 'E2', question: 'Why?' })).rejects.toMatchObject({ status: 403 });
  });

  it("returns an entity's blockers, failing reconciliations and calendar clash", async () => {
    const entity = await api.entity('E4');
    expect(entity.entity.status).toBe('Blocked');
    expect(entity.blockers.map((blocker) => blocker.reference)).toContain('DEF-0412');
    expect(entity.failing_reconciliations.map((failed) => failed.recon_id)).toContain('RC-C3-E4-customers');
    expect(entity.calendar_conflicts.map((conflict) => conflict.window_id)).toEqual(['CAL-004']);
  });

  it('returns cited rows and lists out-of-scope or unknown citations as missing', async () => {
    session.setScope(ENTITY_4_LEAD);
    const response = await api.rows([
      { artefact: 'defect_log', row_id: 'DEF-0412' },
      { artefact: 'defect_log', row_id: 'DEF-0431' },
      { artefact: 'defect_log', row_id: 'DEF-9999' },
    ]);
    expect(response.rows.map((row) => row.row_id)).toEqual(['DEF-0412']);
    expect(response.missing.map((citation) => citation.row_id)).toEqual(['DEF-0431', 'DEF-9999']);
  });

  it('answers entity 4 and gives a partial answer elsewhere', async () => {
    const answered = await api.ask({ entity_id: 'E4', question: 'What is blocking cutover for entity 4?' });
    expect(answered.partial).toBe(false);
    expect(answered.answer.bullets.length).toBe(3);
    expect(answered.rejected.length).toBe(1);

    const partial = await api.ask({ entity_id: 'E2', question: 'Are we on track?' });
    expect(partial.partial).toBe(true);
    expect(partial.partial_reason).toBeTruthy();
  });

  it('publishes and approves', async () => {
    expect((await api.publish({ run_id: 'run-mock-e4-0001' })).status).toBe('awaiting_approval');
    expect((await api.approve({ execution_arn: 'arn', decision: 'approve', note: '' })).status).toBe('approved');
  });
});
```

- [ ] **Step 4: Run them and watch the build fail**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "ERROR\\]" | sort | uniq -c)
```
Expected: the build fails with these TypeScript errors (counts in brackets), and no test runs:
```text
✘ [ERROR] TS2345: Argument of type 'SummaryResponse' is not assignable to parameter of type 'Summary'.   (×3)
✘ [ERROR] TS2345: Argument of type 'EntityRow[]' is not assignable to parameter of type 'readonly EntitySummary[]'.   (×2)
✘ [ERROR] TS2339: Property 'emptyText' does not exist on type 'KpiView'.   (×2)
✘ [ERROR] TS18048: 'row.status' is possibly 'undefined'.   (×2)
✘ [ERROR] TS2554: Expected 3 arguments, but got 2.
✘ [ERROR] TS2554: Expected 2 arguments, but got 1.
✘ [ERROR] TS2345: Argument of type 'Capacity' is not assignable to parameter of type 'PeopleCapacity'.
✘ [ERROR] TS2339: Property 'pass_rate' does not exist on type 'Summary'.
✘ [ERROR] TS2339: Property 'failing_reconciliations' does not exist on type 'EntityDetail'.
✘ [ERROR] TS2339: Property 'calendar_conflicts' does not exist on type 'EntityDetail'.
✘ [ERROR] TS2339: Property 'baselinePercent' does not exist on type 'TimelineRowView'.
✘ [ERROR] TS18048: 'summary.open_blockers' is possibly 'undefined'.
✘ [ERROR] TS18048: 'entity.blockers' is possibly 'undefined'.
✘ [ERROR] TS7006: Parameter 'failed' implicitly has an 'any' type.
✘ [ERROR] TS7006: Parameter 'conflict' implicitly has an 'any' type.
✘ [ERROR] TS2305: Module '"./format"' has no exported member 'formatPassRate'.
✘ [ERROR] No matching export in "src/app/core/format/format.ts" for import "formatPassRate"
```

- [ ] **Step 5: Implement the data layer and the views.** Write each file with exactly this content:

- `web/src/app/core/models/summary.ts`:
```ts
import { Citation } from './citation';

/** The four values of tools/constants.py `EntityStatus`. The API decides them (tools/metrics.entity_status). */
export const ENTITY_STATUSES = ['Live', 'On track', 'At risk', 'Blocked'] as const;

export type EntityStatus = (typeof ENTITY_STATUSES)[number];

/** One open blocker: a defect, a blocked workplan task or unowned runbook steps (tools/metrics.open_blockers). */
export interface Blocker {
  reference: string;
  entity_id: string;
  blocker: string;
  age_days: number;
  owner_role: string;
  evidence: Citation[];
}

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

- `web/src/app/core/api/mock-portal-api.ts`:
```ts
import { Injectable, inject } from '@angular/core';

import { PORTAL_CONFIG } from '../config/portal-config';
import {
  ApproveRequest,
  ApproveResponse,
  AskRequest,
  AskResponse,
  Citation,
  EntityResponse,
  PublishRequest,
  PublishResponse,
  RowsResponse,
  Scope,
  SummaryResponse,
  scopeAllows,
  scopeCoversAllEntities,
} from '../models';
import { SessionStore } from '../session/session-store';
import { ApiError } from './api-error';
import { PortalApi } from './portal-api';

/** The ask, publish and approve fixtures carry a `_mock` note; the API never would. */
const FIXTURE_NOTE_PREFIX = '_';
const ENTITY_ID_FIELD = 'entity_id';
const ASK_ANSWERED_ENTITY = 'E4';

type FixtureLoader = () => Promise<{ default: object }>;

/**
 * The summary as the server returns it for each demo scope, exported from tools/metrics.py (never filtered here:
 * the KPIs for a scope are the server's to compute). Keyed by the scope's entity list.
 */
const ALL_ENTITIES_SUMMARY: FixtureLoader = () => import('./fixtures/summary.json');
const SCOPED_SUMMARIES: Record<string, FixtureLoader> = {
  E4: () => import('./fixtures/summary-entity-lead-E4.json'),
};

const ENTITY_FIXTURES: Record<string, FixtureLoader> = {
  E1: () => import('./fixtures/entity-E1.json'),
  E2: () => import('./fixtures/entity-E2.json'),
  E3: () => import('./fixtures/entity-E3.json'),
  E4: () => import('./fixtures/entity-E4.json'),
};

function withoutFixtureNotes<T>(fixture: object): T {
  return Object.fromEntries(
    Object.entries(fixture).filter(([key]) => !key.startsWith(FIXTURE_NOTE_PREFIX)),
  ) as T;
}

function summaryLoaderFor(scope: Scope): FixtureLoader | undefined {
  return scopeCoversAllEntities(scope) ? ALL_ENTITIES_SUMMARY : SCOPED_SUMMARIES[scope.entity_ids.join(',')];
}

/** PortalApi over the JSON fixtures in ./fixtures, exported from the real core (see web/README.md, "Data"). */
@Injectable()
export class MockPortalApi extends PortalApi {
  private readonly latencyMs = inject(PORTAL_CONFIG).mockLatencyMs;
  private readonly session = inject(SessionStore);

  override async summary(): Promise<SummaryResponse> {
    const loader = summaryLoaderFor(this.session.scope());
    if (!loader) throw ApiError.notFound('A mock summary for this scope');
    return (await this.load(loader)) as SummaryResponse;
  }

  override async entity(entityId: string): Promise<EntityResponse> {
    this.requireInScope(entityId);
    const loader = ENTITY_FIXTURES[entityId];
    if (!loader) throw ApiError.notFound(`Entity ${entityId}`);
    return (await this.load(loader)) as EntityResponse;
  }

  /**
   * Like GET /rows: the cited rows the scope may see, and every other citation in `missing`.
   * Mock limitation: only a row's `entity_id` column decides visibility (the server's rule is queries.in_entity_view).
   */
  override async rows(citations: readonly Citation[]): Promise<RowsResponse> {
    const fixture = (await this.load(() => import('./fixtures/rows.json'))) as RowsResponse;
    const scope = this.session.scope();
    const response: RowsResponse = { rows: [], missing: [] };
    for (const citation of citations) {
      const row = fixture.rows.find(
        (candidate) => candidate.artefact === citation.artefact && candidate.row_id === citation.row_id,
      );
      const entityId = row?.fields[ENTITY_ID_FIELD];
      if (row && (!entityId || scopeAllows(scope, entityId))) response.rows.push(row);
      else response.missing.push(citation);
    }
    return response;
  }

  override async ask(request: AskRequest): Promise<AskResponse> {
    this.requireInScope(request.entity_id);
    const fixture =
      request.entity_id === ASK_ANSWERED_ENTITY
        ? await this.load(() => import('./fixtures/ask-E4.json'))
        : await this.load(() => import('./fixtures/ask-partial.json'));
    return withoutFixtureNotes<AskResponse>(fixture);
  }

  override async publish(_request: PublishRequest): Promise<PublishResponse> {
    return withoutFixtureNotes<PublishResponse>(await this.load(() => import('./fixtures/publish.json')));
  }

  override async approve(_request: ApproveRequest): Promise<ApproveResponse> {
    return withoutFixtureNotes<ApproveResponse>(await this.load(() => import('./fixtures/approve.json')));
  }

  private requireInScope(entityId: string): void {
    if (!scopeAllows(this.session.scope(), entityId)) throw ApiError.outOfScope(entityId);
  }

  private async load(loader: FixtureLoader): Promise<object> {
    const [module] = await Promise.all([loader(), this.delay()]);
    return module.default;
  }

  private delay(): Promise<void> {
    return this.latencyMs > 0 ? new Promise((resolve) => setTimeout(resolve, this.latencyMs)) : Promise.resolve();
  }
}
```

- `web/src/app/features/dashboard/kpi-row/kpi-view.ts`:
```ts
import {
  ToneLabel,
  behindPlanLabel,
  capacityLabel,
  cycleTrendWord,
  reconTargetLabel,
} from '../../../core/config/display-rules';
import { entityLabel, formatCount, formatDays, formatFullDate, formatPassRate, formatPercent } from '../../../core/format/format';
import { Citation, EntityRow, SummaryResponse } from '../../../core/models';

/** A figure or line of figures; with citations it renders as one clickable figure. */
export interface Fragment {
  text: string;
  citations?: readonly Citation[];
}

export interface KpiView {
  label: string;
  /** Shown instead of a figure when the API has none for this scope (no reconciled cycle, nothing left to cut over). */
  emptyText?: string;
  value?: Fragment;
  progress?: { value: number };
  badge?: ToneLabel;
  detail?: Fragment;
}

/**
 * Builds the five headline cards from GET /summary. Selection and wording only: every figure is the API's.
 * Where the API puts the evidence on the parts (per entity, per role, per blocker), a card cites all the parts.
 */
export function buildKpiViews(summary: SummaryResponse): KpiView[] {
  return [recordsReconciled(summary), reconPassRate(summary), openBlockers(summary), finalCutover(summary), capacity(summary)];
}

function entityName(entities: readonly EntityRow[], entityId: string): string {
  return entities.find((entity) => entity.entity_id === entityId)?.entity_name ?? entityLabel(entityId);
}

function recordsReconciled({ overall, entities }: SummaryResponse): KpiView {
  const citations = entities.flatMap((entity) => entity.reconciled.evidence);
  return {
    label: 'Records migrated and reconciled',
    value: { text: formatPercent(overall.pct), citations },
    progress: { value: overall.pct },
    detail: {
      text: `${formatCount(overall.records_reconciled)} of ${formatCount(overall.records_in_scope)} records`,
      citations,
    },
  };
}

function reconPassRate({ pass_rate: passRate }: SummaryResponse): KpiView {
  const label = 'Reconciliation pass rate, latest cycle';
  const { latest, previous } = passRate;
  if (!latest) return { label, emptyText: 'No load cycle has been reconciled yet.' };
  return {
    label,
    value: { text: formatPassRate(latest.pct), citations: latest.evidence },
    badge: reconTargetLabel(latest.pct, passRate.target_pct),
    detail: previous
      ? {
          text: `Cycle ${latest.cycle_id}, ${cycleTrendWord(latest.pct, previous.pct)} ${formatPassRate(previous.pct)} in cycle ${previous.cycle_id}`,
          citations: previous.evidence,
        }
      : { text: `Cycle ${latest.cycle_id}, the first reconciled cycle`, citations: latest.evidence },
  };
}

function openBlockers({ open_blockers: blockers, entities }: SummaryResponse): KpiView {
  const citations = blockers.blockers.flatMap((blocker) => blocker.evidence);
  const perEntity = entities
    .filter((entity) => entity.open_blockers > 0)
    .map((entity) => `${formatCount(entity.open_blockers)} on ${entity.entity_name.toLowerCase()}`);
  return {
    label: 'Open blockers',
    value: { text: formatCount(blockers.count), citations },
    badge: blockers.count ? { text: `Oldest open ${formatDays(blockers.oldest_days)}`, tone: 'danger' } : undefined,
    detail: { text: perEntity.length ? perEntity.join(', ') : 'No open blockers', citations },
  };
}

function finalCutover({ final_cutover: cutover, entities }: SummaryResponse): KpiView {
  const label = 'Days to final cutover';
  if (!cutover) return { label, emptyText: 'Every entity you can see is live.' };
  return {
    label,
    value: { text: formatCount(cutover.days_remaining), citations: cutover.evidence },
    badge: behindPlanLabel(cutover.days_behind_plan),
    detail: {
      text: `${entityName(entities, cutover.entity_id)} cutover weekend, ${formatFullDate(cutover.cutover_forecast)}`,
      citations: cutover.evidence,
    },
  };
}

function capacity({ capacity: people }: SummaryResponse): KpiView {
  const citations = people.by_role.flatMap((role) => role.evidence);
  return {
    label: 'Capacity used against planned',
    value: { text: formatPercent(people.pct), citations },
    badge: capacityLabel(people.pct),
    detail: {
      text: `${formatCount(people.people_used)} people used, ${formatCount(people.people_planned)} planned`,
      citations,
    },
  };
}
```

- `web/src/app/features/dashboard/kpi-row/kpi-row.ts`:
```ts
import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';

import { Citation, SummaryResponse } from '../../../core/models';
import { CitationRequest } from '../../../shared/citations/citation-viewer';
import { CitedNumber } from '../../../shared/ui/cited-number/cited-number';
import { KpiCard } from '../../../shared/ui/kpi-card/kpi-card';
import { ProgressMeter } from '../../../shared/ui/progress-meter/progress-meter';
import { ToneBadge } from '../../../shared/ui/tone-badge/tone-badge';
import { buildKpiViews } from './kpi-view';

/** The five headline figures. Clicking a figure asks for its source rows. */
@Component({
  selector: 'app-kpi-row',
  imports: [KpiCard, CitedNumber, ProgressMeter, ToneBadge],
  templateUrl: './kpi-row.html',
  styleUrl: './kpi-row.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class KpiRow {
  readonly summary = input.required<SummaryResponse>();
  readonly showSources = output<CitationRequest>();

  protected readonly cards = computed(() => buildKpiViews(this.summary()));

  protected openSources(title: string, citations: readonly Citation[]): void {
    this.showSources.emit({ title, citations });
  }
}
```

- `web/src/app/features/dashboard/kpi-row/kpi-row.html`:
```html
@for (card of cards(); track card.label) {
  <app-kpi-card [label]="card.label">
    @if (card.emptyText) {
      <p class="detail">{{ card.emptyText }}</p>
    } @else {
      @if (card.value; as value) {
        <p class="value">
          <app-cited-number
            [text]="value.text"
            [description]="card.label"
            [citations]="value.citations"
            (showSources)="openSources(card.label, $event)"
          />
        </p>
      }
      @if (card.progress; as progress) {
        <app-progress-meter class="progress" [value]="progress.value" />
      }
      @if (card.badge; as badge) {
        <app-tone-badge [text]="badge.text" [tone]="badge.tone" />
      }
      @if (card.detail; as detail) {
        <p class="detail">
          <app-cited-number
            [text]="detail.text"
            [description]="card.label"
            [citations]="detail.citations"
            (showSources)="openSources(card.label, $event)"
          />
        </p>
      }
    }
  </app-kpi-card>
}
```

- `web/src/app/features/dashboard/entities-table/entities-view.ts`:
```ts
import { ENTITY_STATUS_TONES, Tone } from '../../../core/config/display-rules';
import { MeterColor } from '../../../shared/ui/progress-meter/progress-meter';
import { formatCount, formatPercent } from '../../../core/format/format';
import { Citation, EntityRow } from '../../../core/models';

export interface EntityRowView {
  entityId: string;
  name: string;
  sourceSystem: string;
  reconciledText: string;
  percentText: string;
  percent: number;
  citations: readonly Citation[];
  reconciledDescription: string;
  percentDescription: string;
  meterColor: MeterColor;
  live: boolean;
  status: { text: string; tone: Tone };
}

/** Rows for "Where each entity has got to". Every figure and the status are copied from the API. */
export function buildEntityRows(entities: readonly EntityRow[]): EntityRowView[] {
  return entities.map((entity) => ({
    entityId: entity.entity_id,
    name: entity.entity_name,
    sourceSystem: entity.source_description,
    reconciledText: `${formatCount(entity.reconciled.records_reconciled)} of ${formatCount(entity.reconciled.records_in_scope)}`,
    percentText: formatPercent(entity.reconciled.pct),
    percent: entity.reconciled.pct,
    citations: entity.reconciled.evidence,
    reconciledDescription: `${entity.entity_name} records reconciled`,
    percentDescription: `${entity.entity_name} percent complete`,
    meterColor: entity.cutover.live ? 'live' : 'bar',
    live: entity.cutover.live,
    status: { text: entity.status, tone: ENTITY_STATUS_TONES[entity.status] },
  }));
}
```

- `web/src/app/features/dashboard/entities-table/entities-table.ts`:
```ts
import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';
import {
  AtTable,
  AtTableBody,
  AtTableCell,
  AtTableHead,
  AtTableHeadCell,
  AtTableRow,
} from '@amalitechnpm/at-design-system/angular';

import { Citation, EntityRow } from '../../../core/models';
import { CitationRequest } from '../../../shared/citations/citation-viewer';
import { CitedNumber } from '../../../shared/ui/cited-number/cited-number';
import { ProgressMeter } from '../../../shared/ui/progress-meter/progress-meter';
import { ToneBadge } from '../../../shared/ui/tone-badge/tone-badge';
import { buildEntityRows } from './entities-view';

/** One row per entity: source system, records reconciled, percent complete and status. */
@Component({
  selector: 'app-entities-table',
  imports: [AtTable, AtTableHead, AtTableBody, AtTableRow, AtTableHeadCell, AtTableCell, CitedNumber, ProgressMeter, ToneBadge],
  templateUrl: './entities-table.html',
  styleUrl: './entities-table.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EntitiesTable {
  readonly entities = input.required<readonly EntityRow[]>();
  readonly showSources = output<CitationRequest>();

  protected readonly rows = computed(() => buildEntityRows(this.entities()));

  protected openSources(entityName: string, citations: readonly Citation[]): void {
    this.showSources.emit({ title: `${entityName}: records reconciled`, citations });
  }
}
```

- `web/src/app/features/dashboard/entities-table/entities-table.html`:
```html
@if (rows().length) {
  <at-table class="portal-table" [isBordered]="true" [isRounded]="false" size="md">
    <at-table-head>
      <at-table-row>
        <at-table-head-cell>Entity</at-table-head-cell>
        <at-table-head-cell>Source system</at-table-head-cell>
        <at-table-head-cell>Records reconciled</at-table-head-cell>
        <at-table-head-cell>Percent complete</at-table-head-cell>
        <at-table-head-cell>Status</at-table-head-cell>
      </at-table-row>
    </at-table-head>
    <at-table-body>
      @for (row of rows(); track row.entityId) {
        <at-table-row>
          <at-table-cell><span class="entity-name">{{ row.name }}</span></at-table-cell>
          <at-table-cell>{{ row.sourceSystem }}</at-table-cell>
          <at-table-cell>
            <app-cited-number
              [text]="row.reconciledText"
              [description]="row.reconciledDescription"
              [citations]="row.citations"
              (showSources)="openSources(row.name, $event)"
            />
          </at-table-cell>
          <at-table-cell>
            <span class="percent">
              <app-progress-meter class="meter" [value]="row.percent" [color]="row.meterColor" />
              <app-cited-number
                class="percent-value"
                [text]="row.percentText"
                [description]="row.percentDescription"
                [citations]="row.citations"
                (showSources)="openSources(row.name, $event)"
              />
            </span>
          </at-table-cell>
          <at-table-cell>
            <app-tone-badge [text]="row.status.text" [tone]="row.status.tone" />
          </at-table-cell>
        </at-table-row>
      }
    </at-table-body>
  </at-table>
} @else {
  <p class="empty">No entities are visible to you.</p>
}
```

- `web/src/app/features/dashboard/blockers-table/blockers-view.ts`:
```ts
import { Tone, blockerAgeTone } from '../../../core/config/display-rules';
import { entityLabel, formatDays } from '../../../core/format/format';
import { Blocker, Citation, EntityRow } from '../../../core/models';

export interface BlockerRowView {
  reference: string;
  referenceDescription: string;
  sourcesTitle: string;
  citations: readonly Citation[];
  entity: string;
  blocker: string;
  age: { text: string; tone: Tone };
  ownerRole: string;
}

export interface BlockersView {
  rows: BlockerRowView[];
  caption: string;
  hiddenCount: number;
}

/** The oldest blockers first, as the API orders them, limited to `shown`. */
export function buildBlockersView(
  blockers: readonly Blocker[],
  entities: readonly EntityRow[],
  total: number,
  shown: number,
): BlockersView {
  const visible = blockers.slice(0, shown);
  const nameOf = (entityId: string) => entities.find((entity) => entity.entity_id === entityId)?.entity_name ?? entityLabel(entityId);
  return {
    rows: visible.map((blocker) => ({
      reference: blocker.reference,
      referenceDescription: `Blocker ${blocker.reference}`,
      sourcesTitle: `${blocker.reference}: ${blocker.blocker}`,
      citations: blocker.evidence,
      entity: nameOf(blocker.entity_id),
      blocker: blocker.blocker,
      age: { text: formatDays(blocker.age_days), tone: blockerAgeTone(blocker.age_days) },
      ownerRole: blocker.owner_role,
    })),
    caption:
      visible.length < total
        ? `Showing the ${visible.length} oldest of ${total} open blockers.`
        : `Showing all ${total} open blockers, oldest first.`,
    hiddenCount: blockers.length - visible.length,
  };
}
```

- `web/src/app/features/dashboard/blockers-table/blockers-table.ts`:
```ts
import { ChangeDetectionStrategy, Component, computed, input, output, signal } from '@angular/core';
import {
  AtButton,
  AtTable,
  AtTableBody,
  AtTableCell,
  AtTableHead,
  AtTableHeadCell,
  AtTableRow,
} from '@amalitechnpm/at-design-system/angular';

import { BLOCKERS_SHOWN_BY_DEFAULT } from '../../../core/config/display-rules';
import { Blocker, Citation, EntityRow } from '../../../core/models';
import { CitationRequest } from '../../../shared/citations/citation-viewer';
import { CitedNumber } from '../../../shared/ui/cited-number/cited-number';
import { ToneBadge } from '../../../shared/ui/tone-badge/tone-badge';
import { buildBlockersView } from './blockers-view';

/** "Open blockers by age": the oldest blockers with their owner role. The reference opens the cited row. */
@Component({
  selector: 'app-blockers-table',
  imports: [
    AtButton,
    AtTable,
    AtTableHead,
    AtTableBody,
    AtTableRow,
    AtTableHeadCell,
    AtTableCell,
    CitedNumber,
    ToneBadge,
  ],
  templateUrl: './blockers-table.html',
  styleUrl: './blockers-table.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BlockersTable {
  /** `open_blockers.blockers` from GET /summary, oldest first. */
  readonly blockers = input.required<readonly Blocker[]>();
  /** `open_blockers.count` from GET /summary. */
  readonly total = input.required<number>();
  readonly entities = input.required<readonly EntityRow[]>();
  readonly showSources = output<CitationRequest>();

  private readonly showAll = signal(false);

  protected readonly view = computed(() => {
    const blockers = this.blockers();
    return buildBlockersView(blockers, this.entities(), this.total(), this.showAll() ? blockers.length : BLOCKERS_SHOWN_BY_DEFAULT);
  });
  protected readonly toggleLabel = computed(() => (this.showAll() ? 'Show the oldest only' : 'Show all blockers'));
  protected readonly canToggle = computed(() => this.showAll() || (this.view()?.hiddenCount ?? 0) > 0);

  protected toggle(): void {
    this.showAll.update((showAll) => !showAll);
  }

  protected openSources(title: string, citations: readonly Citation[]): void {
    this.showSources.emit({ title, citations });
  }
}
```

- `web/src/app/features/dashboard/blockers-table/blockers-table.html`:
```html
@if (view(); as view) {
  <p class="caption">{{ view.caption }}</p>
  @if (view.rows.length) {
    <at-table class="portal-table" [isBordered]="true" [isRounded]="false" size="md">
      <at-table-head>
        <at-table-row>
          <at-table-head-cell>Reference</at-table-head-cell>
          <at-table-head-cell>Entity</at-table-head-cell>
          <at-table-head-cell>Blocker</at-table-head-cell>
          <at-table-head-cell>Age</at-table-head-cell>
          <at-table-head-cell>Owner role</at-table-head-cell>
        </at-table-row>
      </at-table-head>
      <at-table-body>
        @for (row of view.rows; track row.reference) {
          <at-table-row>
            <at-table-cell>
              <app-cited-number
                class="reference"
                [text]="row.reference"
                [description]="row.referenceDescription"
                [citations]="row.citations"
                (showSources)="openSources(row.sourcesTitle, $event)"
              />
            </at-table-cell>
            <at-table-cell><span class="nowrap">{{ row.entity }}</span></at-table-cell>
            <at-table-cell><span class="blocker">{{ row.blocker }}</span></at-table-cell>
            <at-table-cell><app-tone-badge [text]="row.age.text" [tone]="row.age.tone" /></at-table-cell>
            <at-table-cell><span class="nowrap">{{ row.ownerRole }}</span></at-table-cell>
          </at-table-row>
        }
      </at-table-body>
    </at-table>
  } @else {
    <p class="empty">There are no open blockers.</p>
  }
  @if (canToggle()) {
    <at-button class="toggle" variant="outline" color="brand-dark-blue" size="sm" (atClick)="toggle()">
      {{ toggleLabel() }}
    </at-button>
  }
}
```

- `web/src/app/features/dashboard/capacity-card/capacity-view.ts`:
```ts
import { capacityScale } from '../../../core/config/display-rules';
import { formatCount } from '../../../core/format/format';
import { Capacity, Citation } from '../../../core/models';

export interface CapacityRowView {
  role: string;
  countsText: string;
  barLabel: string;
  used: number;
  planned: number;
  citations: readonly Citation[];
}

export interface CapacityView {
  scale: number;
  rows: CapacityRowView[];
}

/** One row per role: people used against planned this month, all on one shared scale. */
export function buildCapacityView(capacity: Capacity): CapacityView {
  const largest = capacity.by_role.reduce((most, role) => Math.max(most, role.people_used, role.people_planned), 0);
  return {
    scale: capacityScale(largest),
    rows: capacity.by_role.map((role) => ({
      role: role.role,
      countsText: `${formatCount(role.people_used)} used, ${formatCount(role.people_planned)} planned`,
      barLabel: `${role.role}: ${formatCount(role.people_used)} people used against ${formatCount(role.people_planned)} planned`,
      used: role.people_used,
      planned: role.people_planned,
      citations: role.evidence,
    })),
  };
}
```

- `web/src/app/features/dashboard/capacity-card/capacity-card.ts`:
```ts
import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';

import { Capacity, Citation } from '../../../core/models';
import { CitationRequest } from '../../../shared/citations/citation-viewer';
import { CitedNumber } from '../../../shared/ui/cited-number/cited-number';
import { PlanMarkerBar } from '../../../shared/ui/plan-marker-bar/plan-marker-bar';
import { buildCapacityView } from './capacity-view';

/** "Capacity used against planned": people per role this month, with the plan marked. */
@Component({
  selector: 'app-capacity-card',
  imports: [CitedNumber, PlanMarkerBar],
  templateUrl: './capacity-card.html',
  styleUrl: './capacity-card.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CapacityCard {
  /** `capacity` from GET /summary: people per role this month. */
  readonly capacity = input.required<Capacity>();
  readonly showSources = output<CitationRequest>();

  protected readonly view = computed(() => buildCapacityView(this.capacity()));

  protected openSources(role: string, citations: readonly Citation[]): void {
    this.showSources.emit({ title: `${role}: capacity this month`, citations });
  }
}
```

- `web/src/app/features/dashboard/capacity-card/capacity-card.html`:
```html
@if (view(); as view) {
  <ul class="roles">
    @for (row of view.rows; track row.role) {
      <li class="role">
        <div class="role-line">
          <span class="role-name">{{ row.role }}</span>
          <app-cited-number
            class="counts"
            [text]="row.countsText"
            [description]="row.role"
            [citations]="row.citations"
            (showSources)="openSources(row.role, $event)"
          />
        </div>
        <app-plan-marker-bar [actual]="row.used" [planned]="row.planned" [scale]="view.scale" [label]="row.barLabel" />
      </li>
    }
  </ul>
}
```

- `web/src/app/features/dashboard/source-target-banner/source-target-banner.ts`:
```ts
import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { AtIcon } from '@amalitechnpm/at-design-system/angular';

import { EntityRow } from '../../../core/models';

/** "4 source systems → Single cloud ERP": one legacy source per entity in the summary, and the target platform. */
@Component({
  selector: 'app-source-target-banner',
  imports: [AtIcon],
  template: `
    <p class="banner">
      <strong>{{ sourceText() }}</strong>
      <at-icon icon="arrow-right" size="sm" aria-hidden="true"></at-icon>
      <span class="visually-hidden">moving onto</span>
      <strong>{{ targetPlatform() }}</strong>
    </p>
  `,
  styleUrl: './source-target-banner.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SourceTargetBanner {
  readonly entities = input.required<readonly EntityRow[]>();
  readonly targetPlatform = input.required<string>();

  protected readonly sourceText = computed(() => {
    const count = this.entities().length;
    return `${count} source ${count === 1 ? 'system' : 'systems'}`;
  });
}
```

- `web/src/app/features/dashboard/timeline/timeline-view.ts`:
```ts
import { dayOffset, formatDayMonth, formatFullDate, formatMonth } from '../../../core/format/format';
import { Citation, EntityRow } from '../../../core/models';

/** `slip`: from the planned (baseline) cutover to the forecast; `live`: from the cutover to today. */
export type SegmentKind = 'slip' | 'live';

export interface TimelineSegment {
  kind: SegmentKind;
  className: string;
  leftPercent: number;
  widthPercent: number;
}

export interface TimelineRowView {
  entityId: string;
  name: string;
  cutoverText: string;
  cutoverDescription: string;
  sourcesTitle: string;
  /** Read out instead of the bars, which are hidden from screen readers. */
  summary: string;
  citations: readonly Citation[];
  segments: TimelineSegment[];
  baselinePercent: number;
  cutoverPercent: number;
}

export interface TimelineView {
  months: { label: string; leftPercent: number }[];
  todayLabel: string;
  todayPercent: number;
  rows: TimelineRowView[];
}

const FULL_WIDTH_PERCENT = 100;

/** First day of the month an ISO date falls in, as an ISO date. */
function monthStart(isoDate: string): string {
  return `${isoDate.slice(0, 7)}-01`;
}

function nextMonthStart(isoDate: string): string {
  const [year, month] = isoDate.slice(0, 7).split('-').map(Number);
  return month === 12 ? `${year + 1}-01-01` : `${year}-${String(month + 1).padStart(2, '0')}-01`;
}

function cutoverSummary(entity: EntityRow): string {
  const { cutover } = entity;
  const plan =
    cutover.cutover_forecast === cutover.cutover_baseline
      ? 'on the planned date'
      : `planned for ${formatFullDate(cutover.cutover_baseline)}`;
  return `${entity.entity_name}: cutover weekend ${formatFullDate(cutover.cutover_forecast)}, ${plan}${cutover.live ? '; live.' : '.'}`;
}

/**
 * Positions for the cutover timeline: each entity's planned (baseline) and forecast cutover from
 * `entities[].cutover`, on a month axis (layout only; every date is the API's). The axis runs from the month of the
 * earliest date shown to the month after the latest.
 */
export function buildTimelineView(entities: readonly EntityRow[], asOf: string): TimelineView {
  const dates = [asOf, ...entities.flatMap((entity) => [entity.cutover.cutover_baseline, entity.cutover.cutover_forecast])];
  const earliest = dates.reduce((first, date) => (date < first ? date : first));
  const latest = dates.reduce((last, date) => (date > last ? date : last));
  const axisStart = monthStart(earliest);
  const axisEnd = nextMonthStart(latest);
  const axisLength = dayOffset(axisStart, axisEnd);
  const position = (isoDate: string) => (FULL_WIDTH_PERCENT * dayOffset(axisStart, isoDate)) / axisLength;
  const span = (kind: SegmentKind, from: string, to: string): TimelineSegment => ({
    kind,
    className: `segment segment-${kind}`,
    leftPercent: position(from),
    widthPercent: Math.max(position(to) - position(from), 0),
  });

  const months: TimelineView['months'] = [];
  for (let month = axisStart; month < axisEnd; month = nextMonthStart(month)) {
    months.push({ label: formatMonth(month), leftPercent: position(month) });
  }

  return {
    months,
    todayLabel: `Today, ${formatDayMonth(asOf)}`,
    todayPercent: position(asOf),
    rows: entities.map((entity) => {
      const { cutover } = entity;
      const segments: TimelineSegment[] = [];
      if (cutover.days_behind_plan > 0) segments.push(span('slip', cutover.cutover_baseline, cutover.cutover_forecast));
      if (cutover.live) segments.push(span('live', cutover.cutover_forecast, asOf));
      return {
        entityId: entity.entity_id,
        name: entity.entity_name,
        cutoverText: `Cutover ${formatDayMonth(cutover.cutover_forecast)}`,
        cutoverDescription: `${entity.entity_name} cutover date`,
        sourcesTitle: `${entity.entity_name} cutover`,
        summary: cutoverSummary(entity),
        citations: cutover.evidence,
        segments,
        baselinePercent: position(cutover.cutover_baseline),
        cutoverPercent: position(cutover.cutover_forecast),
      };
    }),
  };
}
```

- `web/src/app/features/dashboard/timeline/cutover-timeline.ts`:
```ts
import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';

import { Citation, EntityRow } from '../../../core/models';
import { CitationRequest } from '../../../shared/citations/citation-viewer';
import { CitedNumber } from '../../../shared/ui/cited-number/cited-number';
import { buildTimelineView } from './timeline-view';

/** Planned and forecast cutover per entity on a month axis, with today's line (custom: ADS has no Gantt). */
@Component({
  selector: 'app-cutover-timeline',
  imports: [CitedNumber],
  templateUrl: './cutover-timeline.html',
  styleUrl: './cutover-timeline.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CutoverTimeline {
  readonly entities = input.required<readonly EntityRow[]>();
  readonly asOf = input.required<string>();
  readonly showSources = output<CitationRequest>();

  protected readonly view = computed(() => buildTimelineView(this.entities(), this.asOf()));

  protected openSources(title: string, citations: readonly Citation[]): void {
    this.showSources.emit({ title, citations });
  }
}
```

- `web/src/app/features/dashboard/timeline/cutover-timeline.html`:
```html
@if (view(); as view) {
  <div class="scroller">
    <div class="timeline">
      <div class="axis" aria-hidden="true">
        <span class="label-column"></span>
        <div class="track">
          @for (month of view.months; track month.label) {
            <span class="month" [style.left.%]="month.leftPercent">{{ month.label }}</span>
          }
          <span class="today-pill" [style.left.%]="view.todayPercent">{{ view.todayLabel }}</span>
        </div>
      </div>

      <ol class="rows">
        @for (row of view.rows; track row.entityId) {
          <li class="row">
            <div class="label-column">
              <span class="entity-name">{{ row.name }}</span>
              <app-cited-number
                class="cutover"
                [text]="row.cutoverText"
                [description]="row.cutoverDescription"
                [citations]="row.citations"
                (showSources)="openSources(row.sourcesTitle, $event)"
              />
            </div>
            <div class="track">
              <span class="visually-hidden">{{ row.summary }}</span>
              @for (month of view.months; track month.label) {
                <span class="gridline" aria-hidden="true" [style.left.%]="month.leftPercent"></span>
              }
              @for (segment of row.segments; track segment.kind) {
                <span
                  aria-hidden="true"
                  [class]="segment.className"
                  [style.left.%]="segment.leftPercent"
                  [style.width.%]="segment.widthPercent"
                ></span>
              }
              <span class="baseline" aria-hidden="true" [style.left.%]="row.baselinePercent"></span>
              <span class="diamond" aria-hidden="true" [style.left.%]="row.cutoverPercent"></span>
            </div>
          </li>
        }
      </ol>
      <span class="today-line" aria-hidden="true" [style.--today]="view.todayPercent"></span>
    </div>
  </div>
}
```

- `web/src/app/features/dashboard/timeline/timeline-legend.ts`:
```ts
import { ChangeDetectionStrategy, Component } from '@angular/core';

/** Key for the timeline: planned cutover, forecast cutover weekend, slip behind plan, live. */
@Component({
  selector: 'app-timeline-legend',
  template: `
    <ul class="legend" aria-label="Timeline key">
      <li><span class="swatch-baseline" aria-hidden="true"></span>Planned cutover</li>
      <li><span class="swatch-diamond" aria-hidden="true"></span>Forecast cutover weekend</li>
      <li><span class="swatch swatch-slip" aria-hidden="true"></span>Behind plan</li>
      <li><span class="swatch swatch-live" aria-hidden="true"></span>Live</li>
    </ul>
  `,
  styles: `
    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: var(--portal-space-2) var(--portal-space-4);
      margin: 0;
      padding: 0;
      list-style: none;
      color: var(--portal-color-primary);
      font-size: var(--portal-font-size-xs);
    }
    li { display: inline-flex; align-items: center; gap: var(--portal-space-2); }
    .swatch { width: 1rem; height: 0.5rem; border-radius: var(--portal-radius-pill); }
    .swatch-baseline { width: 0; height: 0.75rem; border-left: 2px solid var(--portal-color-primary); }
    .swatch-slip { background: var(--portal-color-cutover); }
    .swatch-live { background: var(--portal-color-live); }
    .swatch-diamond {
      width: 0.625rem;
      height: 0.625rem;
      transform: rotate(45deg);
      border: 1.5px solid var(--portal-color-primary);
      background: var(--portal-color-cutover);
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TimelineLegend {}
```

- `web/src/app/features/dashboard/dashboard-page.html`:
```html
<app-header
  [heading]="heading"
  [subheading]="subheading()"
  [signedInAs]="signedInAs()"
  switchUserLink="/sign-in"
  [shareStatus]="shareStatus()"
  (share)="share()"
/>

<main class="page">
  @if (store.errorMessage(); as message) {
    <app-load-error title="The dashboard could not be loaded" [message]="message" (retry)="store.reload()" />
  } @else if (store.loading()) {
    <app-loading-block label="Loading the dashboard" [lines]="8" />
  } @else if (store.summary(); as summary) {
    <section class="kpis" aria-label="Headline figures">
      <app-kpi-row [summary]="summary" (showSources)="showSources($event)" />
    </section>

    <div class="columns">
      <div class="main-column">
        <app-section-card
          heading="Where each entity has got to"
          description="Source systems, described by tier and role, moving onto one consolidated ERP platform."
          footnote="Derived from the entity register and the reconciliation results per load cycle."
        >
          <app-source-target-banner [entities]="summary.entities" [targetPlatform]="summary.target_platform" />
          <app-entities-table [entities]="summary.entities" (showSources)="showSources($event)" />
        </app-section-card>

        <app-section-card
          heading="Timeline to final cutover"
          description="Planned and forecast cutover weekend for each entity."
          footnote="Derived from the cutover tasks in the migration workplan."
        >
          <app-timeline-legend sectionAside />
          <app-cutover-timeline [entities]="summary.entities" [asOf]="summary.as_of" (showSources)="showSources($event)" />
        </app-section-card>

        <app-section-card
          heading="Open blockers by age"
          footnote="Derived from the defect log, the workplan and the cutover runbook."
        >
          <app-blockers-table
            [blockers]="summary.open_blockers.blockers"
            [total]="summary.open_blockers.count"
            [entities]="summary.entities"
            (showSources)="showSources($event)"
          />
        </app-section-card>
      </div>
      <aside class="side-column" aria-label="Ask the programme and capacity">
        <app-ask-panel [entities]="summary.entities" (showSources)="showSources($event)" />

        <app-section-card
          class="capacity"
          heading="Capacity used against planned"
          description="People per role this month. The marker shows the plan."
          footnote="Derived from the team roster and the workplan."
        >
          <app-capacity-card [capacity]="summary.capacity" (showSources)="showSources($event)" />
        </app-section-card>
      </aside>
    </div>
  }
</main>

<app-row-viewer />
```

- `web/src/app/features/dashboard/dashboard-page.ts`:
```ts
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';

import { roleLabel } from '../../core/format/format';
import { SessionStore } from '../../core/session/session-store';
import { AskPanel } from '../ask/ask-panel/ask-panel';
import { CitationRequest, CitationViewer } from '../../shared/citations/citation-viewer';
import { RowViewer } from '../../shared/citations/row-viewer/row-viewer';
import { AppHeader } from '../../shared/layout/app-header/app-header';
import { LoadError } from '../../shared/ui/load-error/load-error';
import { LoadingBlock } from '../../shared/ui/loading-block/loading-block';
import { SectionCard } from '../../shared/ui/section-card/section-card';
import { BlockersTable } from './blockers-table/blockers-table';
import { CapacityCard } from './capacity-card/capacity-card';
import { DashboardStore } from './dashboard-store';
import { EntitiesTable } from './entities-table/entities-table';
import { KpiRow } from './kpi-row/kpi-row';
import { SourceTargetBanner } from './source-target-banner/source-target-banner';
import { CutoverTimeline } from './timeline/cutover-timeline';
import { TimelineLegend } from './timeline/timeline-legend';

const PAGE_HEADING = 'ERP migration progress';
const SHARE_COPIED = 'Link to this view copied.';
const SHARE_FAILED = 'The link could not be copied. Copy it from the address bar.';

/** The one screen: headline figures, entities, timeline, blockers, capacity and the ask panel. */
@Component({
  selector: 'app-dashboard-page',
  imports: [AppHeader, LoadError, LoadingBlock, SectionCard, KpiRow, SourceTargetBanner, EntitiesTable, CutoverTimeline, TimelineLegend, BlockersTable, CapacityCard, AskPanel, RowViewer],
  templateUrl: './dashboard-page.html',
  styleUrl: './dashboard-page.scss',
  providers: [DashboardStore, CitationViewer],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardPage {
  protected readonly store = inject(DashboardStore);
  private readonly session = inject(SessionStore);
  private readonly citationViewer = inject(CitationViewer);

  protected readonly heading = PAGE_HEADING;
  protected readonly subheading = computed(() => this.store.summary()?.programme_name);
  protected readonly signedInAs = computed(() => roleLabel(this.session.role()));
  protected readonly shareStatus = signal('');

  protected showSources(request: CitationRequest): void {
    this.citationViewer.open(request);
  }

  protected async share(): Promise<void> {
    try {
      await navigator.clipboard.writeText(window.location.href);
      this.shareStatus.set(SHARE_COPIED);
    } catch {
      this.shareStatus.set(SHARE_FAILED);
    }
  }
}
```

- `web/src/app/core/api/portal-api.ts`:
```ts
import {
  ApproveRequest,
  ApproveResponse,
  AskRequest,
  AskResponse,
  Citation,
  EntityResponse,
  PublishRequest,
  PublishResponse,
  RowsResponse,
  SummaryResponse,
} from '../models';

/**
 * The portal's one door to data: the routes in docs/TEAM_PLAN.md §3.
 * Implemented by MockPortalApi (fixtures) and HttpPortalApi (API Gateway); PORTAL_CONFIG.dataSource picks one.
 * Failures reject with an ApiError.
 */
export abstract class PortalApi {
  abstract summary(): Promise<SummaryResponse>;
  abstract entity(entityId: string): Promise<EntityResponse>;
  abstract rows(citations: readonly Citation[]): Promise<RowsResponse>;
  abstract ask(request: AskRequest): Promise<AskResponse>;
  abstract publish(request: PublishRequest): Promise<PublishResponse>;
  abstract approve(request: ApproveRequest): Promise<ApproveResponse>;
}

/** The `cite` query value for GET /rows: `artefact:row_id,artefact:row_id`. */
export function citeParameter(citations: readonly Citation[]): string {
  return citations.map((citation) => `${citation.artefact}:${citation.row_id}`).join(',');
}
```

- [ ] **Step 6: The edits.**
  - `web/src/app/core/format/format.ts`: after `const LOCALE = 'en-GB';` add the two display constants (the lead's ruling D1: whole numbers for records reconciled and capacity, one decimal for the pass rate, as the mockup shows 96.4% against 94.8%)
```ts

/** The API sends percentages with one decimal (58.1); records reconciled and capacity show whole numbers (58%, 103%). Rounding only. */
export const PERCENT_DISPLAY_DECIMALS = 0;

/** The reconciliation pass rate keeps one decimal (96.4%, 94.8%), as the design shows it: cycle-to-cycle moves are small. */
export const PASS_RATE_DISPLAY_DECIMALS = 1;
```
    and replace the whole `formatPercent` function with
```ts
function percentText(value: number, decimals: number): string {
  return `${value.toLocaleString(LOCALE, { maximumFractionDigits: decimals })}%`;
}

/** Records reconciled, an entity's percent complete, capacity: "58%". */
export function formatPercent(value: number): string {
  return percentText(value, PERCENT_DISPLAY_DECIMALS);
}

/** The reconciliation pass rate and its target: "96.4%". */
export function formatPassRate(value: number): string {
  return percentText(value, PASS_RATE_DISPLAY_DECIMALS);
}
```
  - `web/src/app/core/config/display-rules.ts`: add `import { formatPassRate } from '../format/format';` above `import { EntityStatus } from '../models';`, and in `reconTargetLabel` replace the two `${targetPercent}%` with `${formatPassRate(targetPercent)}` (the target is a pass rate: 98 → "98%", 98.5 → "98.5%").
  - `web/src/app/core/api/http-portal-api.ts`: in the models import replace `EntityDetail,` with `EntityResponse,` and `Summary,` with `SummaryResponse,`; replace `Promise<Summary>` and `get<Summary>` with `Promise<SummaryResponse>` and `get<SummaryResponse>`, and `Promise<EntityDetail>` and `get<EntityDetail>` with `Promise<EntityResponse>` and `get<EntityResponse>`.
  - `web/src/app/features/dashboard/dashboard-store.ts` and `dashboard-store.spec.ts`: replace every `Summary` type with `SummaryResponse` (the import, `computed<SummaryResponse | undefined>`, the spec's cast and `storeWith` parameter). Result:
```ts
import { Injectable, computed, inject, resource } from '@angular/core';

import { ApiError } from '../../core/api/api-error';
import { PortalApi } from '../../core/api/portal-api';
import { SummaryResponse } from '../../core/models';

const UNKNOWN_ERROR_MESSAGE = 'The dashboard could not be loaded. Check your connection and try again.';

/** The one-screen summary (GET /summary) and its loading state. Components read; they never compute. */
@Injectable()
export class DashboardStore {
  private readonly api = inject(PortalApi);
  private readonly summaryResource = resource({ loader: () => this.api.summary() });

  readonly summary = computed<SummaryResponse | undefined>(() =>
    this.summaryResource.hasValue() ? this.summaryResource.value() : undefined,
  );
  readonly loading = computed(() => this.summaryResource.isLoading() && !this.summary());
  readonly errorMessage = computed(() => {
    const error = this.summaryResource.error();
    if (!error) return undefined;
    return error instanceof ApiError ? error.message : UNKNOWN_ERROR_MESSAGE;
  });

  reload(): void {
    this.summaryResource.reload();
  }
}
```
```ts
import { ApplicationRef } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { ApiError } from '../../core/api/api-error';
import { PortalApi } from '../../core/api/portal-api';
import { SummaryResponse } from '../../core/models';
import { DashboardStore } from './dashboard-store';

const MINIMAL_SUMMARY = { as_of: '2026-10-13', entities: [] } as unknown as SummaryResponse;

function storeWith(summary: () => Promise<SummaryResponse>): DashboardStore {
  TestBed.configureTestingModule({
    providers: [DashboardStore, { provide: PortalApi, useValue: { summary } }],
  });
  return TestBed.inject(DashboardStore);
}

async function settle(): Promise<void> {
  await TestBed.inject(ApplicationRef).whenStable();
}

describe('DashboardStore', () => {
  it('is loading, then holds the summary', async () => {
    const store = storeWith(() => Promise.resolve(MINIMAL_SUMMARY));
    expect(store.loading()).toBe(true);
    await settle();
    expect(store.loading()).toBe(false);
    expect(store.summary()).toEqual(MINIMAL_SUMMARY);
    expect(store.errorMessage()).toBeUndefined();
  });

  it('shows the API error message, and loads again on reload', async () => {
    let calls = 0;
    const store = storeWith(() =>
      ++calls === 1 ? Promise.reject(new ApiError(403, 'Entity E2 is outside your access.')) : Promise.resolve(MINIMAL_SUMMARY),
    );
    await settle();
    expect(store.errorMessage()).toBe('Entity E2 is outside your access.');

    store.reload();
    await settle();
    expect(store.errorMessage()).toBeUndefined();
    expect(store.summary()).toEqual(MINIMAL_SUMMARY);
  });

  it('uses a plain message for unexpected errors', async () => {
    const store = storeWith(() => Promise.reject(new Error('socket hang up')));
    await settle();
    expect(store.errorMessage()).toContain('could not be loaded');
  });
});
```
  - `web/src/app/features/dashboard/entities-table/entities-table.scss`: replace the selector line `.awaiting,` + `.empty {` with `.empty {`.
  - `web/src/app/features/dashboard/source-target-banner/source-target-banner.scss`: delete the `.target-description { … }` rule.
  - `web/src/app/features/dashboard/timeline/cutover-timeline.scss`: replace the `.segment-build`, `.segment-mock` and `.segment-live` rules with:
```scss
.segment-slip {
  background: var(--portal-color-cutover);
}

.segment-live {
  border-radius: 0 var(--portal-radius-pill) var(--portal-radius-pill) 0;
  background: var(--portal-color-live);
}

// The planned (baseline) cutover: a short upright tick.
.baseline {
  position: absolute;
  top: 50%;
  width: 0;
  height: 1.25rem;
  transform: translate(-50%, -50%);
  border-left: 2px solid var(--portal-color-primary);
}
```
  - **Clement's** `web/src/app/features/ask/ask-panel/ask-panel.ts` (tell him first): `import { EntitySummary } from '../../../core/models';` → `import { EntityRow } from '../../../core/models';`; `input.required<readonly EntitySummary[]>()` → `input.required<readonly EntityRow[]>()`; `({ label: entity.name, value: entity.entity_id })` → `({ label: entity.entity_name, value: entity.entity_id })`.
  - Delete the now unused "Awaiting API" component: `git rm -r web/src/app/shared/ui/awaiting-api`.

- [ ] **Step 7: Run the suite and the build**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
(cd web && yarn build 2>&1 | grep -E "ERROR|bundle generation complete")
```
Expected: `Test Files  29 passed (29)` and `Tests  89 passed (89)`. The build prints `Application bundle generation complete.` and no `ERROR`.
  - A view test fails with an `AssertionError` on a figure: the **view** is wrong, never the fixture. Fix the view; ledger it.

- [ ] **Step 8: Look at it.** `(cd web && yarn start)`, open http://localhost:4200. Expected: the figures in [[F1b - Real fixtures and the dashboard on the contract keys - spec]] §1 "Success means", for the CFO and (Switch user → Entity lead) for E4. Stop the server.

- [ ] **Step 9: Commit**
```bash
git add -A web/src/app
git status --short | grep -v "^[AMDR] " ; git commit -m "Dashboard on the API contract keys, with fixtures exported from the real core (D-001, D-021)"
```
Expected: the `grep` prints nothing (every change staged; `.superpowers/` is ignored).

**Task done when:** `yarn test` reports 89 passed in 29 files; the screen in mock mode shows 58%, 96.4%, 7, 102 and 103% for the CFO; `git show --stat HEAD` includes `summary-entity-lead-E4.json` and deletes `awaiting-api.ts`.

### Task 2: Retire `build-fixtures.mjs`; document the fixtures

**Files:**
- Delete: `web/scripts/build-fixtures.mjs`
- Modify: `web/package.json` (remove the `fixtures` script), `web/README.md` (the "Data" section)

- [ ] **Step 1: Watch the old script fail** (proof it is dead):
```bash
(cd web && node scripts/build-fixtures.mjs 2>&1 | grep -o "ENOENT[^,]*" | head -1)
```
Expected: `ENOENT: no such file or directory` (it reads `demo/data/erp/output/kpis.json` *(new)*, deleted in PR #11).

- [ ] **Step 2: Remove it**
```bash
git rm web/scripts/build-fixtures.mjs
sed -i '/"fixtures": "node scripts\/build-fixtures.mjs",/d' web/package.json
(cd web && yarn fixtures 2>&1 | grep -E "error")
```
Expected: `error Command "fixtures" not found.`

- [ ] **Step 3: README.** In `web/README.md`, replace the whole `### Data` section (its heading and paragraph, up to `### Troubleshooting`) with:
```markdown
### Data

The app runs on mock fixtures by default (`dataSource: 'mock'` in `src/app/core/config/portal-config.ts`), so no back end is needed. The fixtures in `src/app/core/api/fixtures/` are **exported from the real back end**, never typed by hand:

- `summary.json`, `entity-E1.json` … `entity-E4.json`, `rows.json`: written by `uv run python scripts/export_summary.py` from the repo root (L4), from `tools/metrics.py` over the committed synthetic dataset. Re-run it after a change to the metrics or the data, and commit the result.
- `summary-entity-lead-E4.json`: the summary the API returns to the E4 entity lead, for the mock role switcher.
- `ask-E4.json`, `ask-partial.json`, `publish.json`, `approve.json`: mock agent responses (each says so in `_mock`).

Each fixture is checked against the API contract (`src/app/core/api/schema/`, generated by `scripts/export_api_schema.py`) by `src/app/core/api/fixtures.spec.ts`. The screen rounds percentages to whole numbers (58.1 → 58%), except the reconciliation pass rate, which keeps one decimal (96.4%), and computes nothing else.
```

- [ ] **Step 4: Full suite and commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
git add web/package.json web/README.md
git commit -m "Retire build-fixtures.mjs (it read the deleted kpis.json); document the exported fixtures"
```
Expected: `Test Files  29 passed (29)` and `Tests  89 passed (89)`.

**Task done when:** `ls web/scripts` fails (the folder is gone), `grep -c fixtures web/package.json` prints `0`, and the README's "Data" section names `scripts/export_summary.py` *(new)*.

### Task 3: Your `HANDOFF.md` and `DEMO.md` lines

**Files:** Modify `HANDOFF.md` (repo root), `DEMO.md` (one line; Clement's file, with Patrick: tell him).

- [ ] **Step 1:** In `HANDOFF.md` under `## What's real`, replace the line `- Every KPI on the screen is computed from the artefacts by \`tools/metrics.py\` (unit-tested).` with:
```markdown
- Every KPI on the screen is computed from the artefacts by `tools/metrics.py` (unit-tested). The portal (`web/`) shows `/summary` as returned: five KPIs, the entities, the cutover timeline (planned vs forecast cutover, from `entities[].cutover`), the blockers and capacity by role. Percentages are rounded to whole numbers for display (the reconciliation pass rate to one decimal, 96.4%); nothing else is computed in the browser.
```
  Under `## What's faked / stubbed`, add as the last bullet:
```markdown
- **Local mock data:** with `dataSource: 'mock'` (the default for `yarn start` and the tests) the portal reads fixtures exported from `tools/metrics.py` (`web/src/app/core/api/fixtures/`). The ask, publish and approve fixtures are mock agent responses, marked `_mock`. The deployed portal uses the real API.
```
- [ ] **Step 2:** In `DEMO.md` under `## Pre-flight checklist`, add:
```markdown
- [ ] The portal's one screen shows 58 %, 96.4 %, 7 blockers (oldest 18 days), 102 days (6 behind plan) and 103 % capacity: the same as `web/src/app/core/api/fixtures/summary.json`
```
- [ ] **Step 3: Commit**
```bash
git add HANDOFF.md DEMO.md
git commit -m "HANDOFF and DEMO: what the one screen shows and what is mocked"
```
Expected: `2 files changed`.

**Task done when:** `grep -c "Local mock data" HANDOFF.md` prints `1` and `grep -c "58 %, 96.4 %" DEMO.md` prints `1`.

### Task 4: Review, then PR (after Mildred's OK)
- [ ] **Step 1:** Work through the Review Focus by hand; write each result in the ledger.
- [ ] **Step 2:** `git diff develop --stat` touches only the files in Tasks 1–3.
- [ ] **Step 3:** Fresh review of the diff against [[F1b - Real fixtures and the dashboard on the contract keys - spec]]; fix critical and important findings test-first.
- [ ] **Step 4 (with Mildred's OK only):** `git push -u origin feature/web-dashboard-contract`; PR to `develop` titled "Front end: the one screen on the API contract, with exported fixtures (F1b)", with a screenshot of the CFO screen in mock mode, `yarn test` 89 passed, the rulings and deferred minors. No attribution lines. Tell Clement (his `ask-panel.ts` changed) and Linus (fixture names).
- [ ] **Step 5:** [[Build order]] row F1: `in review (PR #nn)`, then `merged`.

**Task done when:** the PR is open to `develop`, Jenkins' front-end build is green, and the PR shows the screenshot.

## Never
- Compute a KPI, a status or a date in the browser; show what the API returns.
- Send scope (role, entities, tenant) in a request body, query string or header.
- Log, print or store a token yourself.
- Add a `package-lock.json`, or change `yarn.lock` other than with `yarn add`.
- Commit the npm token, a password or any secret.
- Push to `develop` or `main`, or add attribution lines.
- Edit a fixture by hand; re-export it.
- Filter, sum or average a summary in the mock; serve the server's own export for the scope.
- Change `tools/metrics.py` or a schema to fit the screen.

## Done means
- [ ] **Tests:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` → `Test Files  29 passed (29)`, `Tests  89 passed (89)`. *Verify:* run it on the branch.
- [ ] **Fixtures valid and current:** `(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/api/fixtures.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)` → `Tests  15 passed (15)`; re-running the exporter leaves `git status --short web/src/app/core/api/fixtures` empty. *Verify:* run both.
- [ ] **The screen (mock, CFO):** KPI values `58%`, `96.4%`, `7`, `102`, `103%` (pass rate with one decimal, the rest whole numbers); entities E1 Live 100%, E2 On track 89%, E3 At risk 54%, E4 Blocked 19%; banner "4 source systems … Single cloud ERP, one chart of accounts". *Verify:* `(cd web && yarn start)`, open http://localhost:4200.
- [ ] **Percent display (lead's ruling D1):** `grep -c "DISPLAY_DECIMALS = " web/src/app/core/format/format.ts` → `2` (`PERCENT_DISPLAY_DECIMALS = 0`, `PASS_RATE_DISPLAY_DECIMALS = 1`); `(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/format/format.spec.ts 2>&1 | grep -E "Tests ")` → `Tests  5 passed (5)`. *Verify:* run both on the branch.
- [ ] **The screen (mock, E4 entity lead):** one entity row (Entity 4, 19%); pass rate 95.2%; 3 open blockers. *Verify:* Switch user → Entity lead.
- [ ] **Old script gone:** `ls web/scripts/build-fixtures.mjs` fails; `(cd web && yarn fixtures)` prints `error Command "fixtures" not found.`
- [ ] **Docs:** `web/README.md` "Data" names `scripts/export_summary.py`; `HANDOFF.md` has the "Local mock data" bullet; `DEMO.md` has the 58 % pre-flight line. *Verify:* `grep` each.
- [ ] **PR:** open to `develop` titled "Front end: the one screen on the API contract, with exported fixtures (F1b)"; [[Build order]] row F1 updated. *Verify:* `gh pr list --head feature/web-dashboard-contract`.

Related: [[F1b - Real fixtures and the dashboard on the contract keys - spec]], [[F1a - Contract types and the 14 artefacts - spec]], [[Build order]], [[How to execute a plan]]
