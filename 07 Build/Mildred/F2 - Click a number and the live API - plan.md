---
tags: [build, plan, area/frontend]
id: F2
owner: Mildred
spec: "[[F2 - Click a number and the live API - spec]]"
status: ready
updated: 2026-10-14
---
# F2: click a number and the live API (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[F2 - Click a number and the live API - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger as a `Ruling:` line.
3. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Mildred - front end]].
4. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
5. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
6. [[F1b - Real fixtures and the dashboard on the contract keys - spec]]: what is already in place.
7. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

**Goal:** contract errors read as the API's words; click-a-number pinned by tests; the deployed portal configured by `/portal-config.json`, and switched to the live API.

**Architecture:** `main.ts` → `loadPortalConfig()` → `PORTAL_CONFIG` → `providePortalApi()` picks `HttpPortalApi` when `dataSource` is `http`. `HttpPortalApi.call()` maps errors. No change to components.

**Tech stack:** Angular 22, TypeScript 6, Vitest through `ng test`; the deployed check uses a browser and `curl`.

**Dry-run:** Tasks 1–3 were run on 2026-10-14 in a throwaway worktree with C1, F1a and F1b applied; the counts and messages are the real output. **Task 4 needs the deployed stacks: verify in AWS** (not dry-run; no AWS calls were made).

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your own clone). Branch **`feature/web-rows-and-live-api`** from an up-to-date `develop`, after every dependency in [[Build order]] is merged. Never commit to, or push, `develop` or `main`; PR to `develop`; Patrick merges.
- **Start state:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` → `Test Files  29 passed (29)`, `Tests  88 passed (88)` (C1, F1a, F1b merged). If yours differs, stop.
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
- **Stay in your files** (Mildred's list in the brief). This item touches `web/src/app/core/api/`, `web/src/app/core/config/`, `web/src/main.ts`, two new spec files, and `web/README.md`.
- **Cross-owner edits:** none. (`main.ts` and `portal-config.ts` are yours; Clement extends both in F3a.)
- **Commits:** small, one per task, with the message given. **No `Co-Authored-By` and no "Generated with" lines** in commits or the PR.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **`main.ts` really waits for the config:** in `yarn start` (no file) the app loads in mock mode; with a `web/public/portal-config.json` *(new, temporary)* containing `{"dataSource": "htpp"}` the page stays blank and the console shows `portal-config.json: dataSource must be one of mock, http, not "htpp"`. Delete the file afterwards (never commit one).
2. **The deep-link case:** open http://localhost:4200/publish/run-1 directly: the config request in the Network tab goes to `/portal-config.json`, not `/publish/portal-config.json`.
3. **The live `cite` URL:** in AWS, the 58% click's request URL is under 8,192 bytes and returns 200 (Network tab).
4. **Error wording on screen:** in AWS with `AUTH_MODE=none` the API never 403s; check one error by hand instead: `curl -s https://<CloudFront domain>/api/entity/E9` returns `{"error": "not_found", …}`, and the screen would show its `detail`.
5. **No token or scope in any request** the portal sends (Network tab: `/api/summary`, `/api/rows` carry no `scope`, `role` or `entity_ids` parameter).

---

### Task 1: The contract error body becomes the message

**Files:** Modify `web/src/app/core/api/api-error.ts`, `web/src/app/core/api/http-portal-api.ts`, `web/src/app/core/api/http-portal-api.spec.ts`.

**Produces:** `ApiError.code?: ErrorCode`, `isErrorResponse(body: unknown): body is ErrorResponse`. **Consumes:** F1a's `ErrorResponse`, `ERROR_CODES`, `contractErrors`.

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
git switch -c feature/web-rows-and-live-api
mkdir -p .superpowers && printf '# Ledger: F2 click a number and the live API\n' > .superpowers/ledger-F2.md
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
```
Expected: `Test Files  29 passed (29)`, `Tests  88 passed (88)`.

- [ ] **Step 2: Failing test.** In `web/src/app/core/api/http-portal-api.spec.ts`, replace
```ts
import { ApiError } from './api-error';
import { HttpPortalApi } from './http-portal-api';
```
with
```ts
import { ErrorResponse } from '../models';
import { ApiError } from './api-error';
import { HttpPortalApi } from './http-portal-api';
import { contractErrors } from './testing/contract-validator';
```
and replace the line
```ts
  it('turns an HTTP failure into an ApiError with the status', async () => {
```
with
```ts
  it("turns the contract's error body into an ApiError with its status, code and detail", async () => {
    const body: ErrorResponse = { error: 'out_of_scope', detail: 'Entity E2 is outside your access.' };
    expect(contractErrors('error', body)).toEqual([]);
    const response = api.entity('E2');
    http.expectOne(`${BASE_URL}/entity/E2`).flush(body, { status: 403, statusText: 'Forbidden' });
    await expect(response).rejects.toMatchObject({
      name: 'ApiError',
      status: 403,
      code: 'out_of_scope',
      message: 'Entity E2 is outside your access.',
    } satisfies Partial<ApiError>);
  });

  it('turns an HTTP failure without the error body into an ApiError with the status', async () => {
```

- [ ] **Step 3: Run it**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/api/http-portal-api.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: `✘ [ERROR] TS2353: Object literal may only specify known properties, and 'code' does not exist in type 'Partial<ApiError>'.`

- [ ] **Step 4: Implement.** Replace `web/src/app/core/api/api-error.ts` with:
```ts
import { ERROR_CODES, ErrorCode, ErrorResponse } from '../models';

/** A failed API call, whichever data source made it. `code` is the contract's `error` when the API sent its body. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly code?: ErrorCode,
  ) {
    super(message);
    this.name = 'ApiError';
  }

  static outOfScope(entityId: string): ApiError {
    return new ApiError(403, `Entity ${entityId} is outside your access.`, 'out_of_scope');
  }

  static notFound(what: string): ApiError {
    return new ApiError(404, `${what} was not found.`, 'not_found');
  }
}

/** True when `body` is the contract's `{error, detail}` (tools/api_schema.py `ErrorResponse`). */
export function isErrorResponse(body: unknown): body is ErrorResponse {
  if (body === null || typeof body !== 'object') return false;
  const { error, detail } = body as Record<string, unknown>;
  return ERROR_CODES.includes(error as ErrorCode) && typeof detail === 'string';
}
```
In `web/src/app/core/api/http-portal-api.ts`, change `import { ApiError } from './api-error';` to `import { ApiError, isErrorResponse } from './api-error';`, and in `call()` replace
```ts
      if (error instanceof HttpErrorResponse) throw new ApiError(error.status, error.message);
```
with
```ts
      if (error instanceof HttpErrorResponse) {
        throw isErrorResponse(error.error)
          ? new ApiError(error.status, error.error.detail, error.error.error)
          : new ApiError(error.status, error.message);
      }
```

- [ ] **Step 5: Run it, then the suite, then commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/api/http-portal-api.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
git add web/src/app/core/api
git commit -m "Show the API's own error detail: map the contract error body to ApiError with its code"
```
Expected: `Tests  6 passed (6)`; then `Test Files  29 passed (29)` and `Tests  89 passed (89)`.

**Task done when:** the new test passes, `yarn test` reports 89 passed, and `ApiError.outOfScope('E2').code` is `'out_of_scope'` (read the file).

### Task 2: Pin "click a number → its source rows"

**Files:** Create `web/src/app/features/dashboard/dashboard-page.spec.ts` *(new)*, `web/src/app/shared/citations/row-viewer/row-viewer.spec.ts` *(new)*.

**Consumes:** `DashboardPage`, `KpiRow`, `CitedNumber`, `CitationViewer.open(request: CitationRequest)`, `RowViewer`, `PortalApi.rows(citations)`, the F1b fixtures.

These are **characterisation tests**: the behaviour exists since PR #12 and F1b moved it onto the contract. They are expected to **pass at once**; this is the one declared exception to "watch it fail". If one fails, F1b broke the behaviour: fix the code, never the test, and ledger it.

- [ ] **Step 1: Write the tests.** `web/src/app/features/dashboard/dashboard-page.spec.ts`:
```ts
import { ApplicationRef } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { providePortalApi } from '../../core/api/provide-portal-api';
import { PORTAL_CONFIG, PORTAL_CONFIG_VALUES } from '../../core/config/portal-config';
import { DashboardPage } from './dashboard-page';

/** The page pulls in the ADS wrapper, which can be slow on a busy machine. */
const PAGE_TIMEOUT_MS = 30_000;

async function renderDashboard() {
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      providePortalApi(),
      { provide: PORTAL_CONFIG, useValue: { ...PORTAL_CONFIG_VALUES, dataSource: 'mock', mockLatencyMs: 0 } },
    ],
  });
  const fixture = TestBed.createComponent(DashboardPage);
  await settle(fixture);
  return fixture;
}

async function settle(fixture: { whenStable: () => Promise<unknown> }): Promise<void> {
  await fixture.whenStable();
  await TestBed.inject(ApplicationRef).whenStable();
  await fixture.whenStable();
}

function rowViewerText(element: HTMLElement): string {
  return element.querySelector('app-row-viewer')?.textContent ?? '';
}

describe('DashboardPage: click a number to see its source rows', () => {
  it('opens the 49 reconciliation rows behind 58%', async () => {
    const fixture = await renderDashboard();
    const element = fixture.nativeElement as HTMLElement;
    const headline = element.querySelector<HTMLButtonElement>('app-kpi-row app-cited-number button');
    expect(headline?.textContent?.trim()).toBe('58%');

    headline?.click();
    await settle(fixture);

    expect(rowViewerText(element)).toContain('49 source rows');
    expect(rowViewerText(element)).toContain('Reconciliation results, RC-PROD-E1-E1-company_codes');
  }, PAGE_TIMEOUT_MS);
});
```
`web/src/app/shared/citations/row-viewer/row-viewer.spec.ts`:
```ts
import { ApplicationRef } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { PortalApi } from '../../../core/api/portal-api';
import { Citation, RowsResponse } from '../../../core/models';
import { CitationViewer } from '../citation-viewer';
import { RowViewer } from './row-viewer';

/** Rendering pulls in the ADS drawer, which can be slow on a busy machine. */
const RENDER_TIMEOUT_MS = 30_000;
const VISIBLE: Citation = { artefact: 'defect_log', row_id: 'DEF-0412' };
const NOT_VISIBLE: Citation = { artefact: 'defect_log', row_id: 'DEF-0447' };
const ROWS: RowsResponse = {
  rows: [{ ...VISIBLE, fields: { defect_id: 'DEF-0412', status: 'Open' } }],
  missing: [NOT_VISIBLE],
};

describe('RowViewer', () => {
  it('shows the rows from GET /rows and lists `missing` separately', async () => {
    const asked: (readonly Citation[])[] = [];
    const rows = (citations: readonly Citation[]): Promise<RowsResponse> => {
      asked.push(citations);
      return Promise.resolve(ROWS);
    };
    TestBed.configureTestingModule({ providers: [CitationViewer, { provide: PortalApi, useValue: { rows } }] });
    const fixture = TestBed.createComponent(RowViewer);
    TestBed.inject(CitationViewer).open({ title: 'Open blockers', citations: [VISIBLE, NOT_VISIBLE] });
    await fixture.whenStable();
    await TestBed.inject(ApplicationRef).whenStable();
    await fixture.whenStable();

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(asked).toEqual([ [VISIBLE, NOT_VISIBLE] ]);
    expect(text).toContain('1 source row');
    expect(text).toContain('Defect log, DEF-0412');
    expect(text).toContain('Not available to you');
    expect(text).toContain('Defect log, DEF-0447');
  }, RENDER_TIMEOUT_MS);
});
```

- [ ] **Step 2: Run them**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/features/dashboard/dashboard-page.spec.ts --include src/app/shared/citations 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: `Test Files  2 passed (2)`, `Tests  2 passed (2)`. (They render the ADS drawer; on a slow machine one may take 5–10 s.)

- [ ] **Step 3: Prove the first test can fail** (it must not be vacuous): temporarily change `'49 source rows'` to `'48 source rows'`, run Step 2 again, and see `AssertionError: expected '…' to contain '48 source rows'`. Undo the change.

- [ ] **Step 4: Full suite and commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
git add web/src/app/features/dashboard/dashboard-page.spec.ts web/src/app/shared/citations/row-viewer/row-viewer.spec.ts
git commit -m "Pin click-a-number: 58% opens its 49 reconciliation rows; missing rows listed apart"
```
Expected: `Test Files  31 passed (31)` and `Tests  91 passed (91)`.

**Task done when:** both tests pass, the deliberate break in Step 3 failed as described, and `yarn test` reports 91 passed.

### Task 3: The deployed config, read at start-up

**Files:** Modify `web/src/app/core/config/portal-config.ts`, `web/src/main.ts`, `web/README.md`. Create `web/src/app/core/config/portal-config.spec.ts` *(new)*.

**Produces:** `DATA_SOURCES`, `AUTH_MODES`, `RUNTIME_CONFIG_URL`, `mergePortalConfig(defaults, overrides)`, `loadPortalConfig(fetchConfig?)`. **Consumed by:** `main.ts`; Clement's F3a (adds `cognito`).

- [ ] **Step 1: Failing test.** Create `web/src/app/core/config/portal-config.spec.ts`:
```ts
import { PORTAL_CONFIG_VALUES, RUNTIME_CONFIG_URL, loadPortalConfig, mergePortalConfig } from './portal-config';

const DEPLOYED = { dataSource: 'http', authMode: 'none', apiBaseUrl: '/api' };

function respondWith(body: string, contentType: string, status = 200): (url: string) => Promise<Response> {
  return () => Promise.resolve(new Response(body, { status, headers: { 'content-type': contentType } }));
}

describe('portal config', () => {
  it('keeps the defaults (mock data, no sign-in) when no portal-config.json is deployed', async () => {
    expect(await loadPortalConfig(respondWith('Not found', 'text/plain', 404))).toEqual(PORTAL_CONFIG_VALUES);
    expect(PORTAL_CONFIG_VALUES.dataSource).toBe('mock');
  });

  it("ignores the SPA fallback page that a host serves instead of a missing file", async () => {
    expect(await loadPortalConfig(respondWith('<!doctype html>', 'text/html'))).toEqual(PORTAL_CONFIG_VALUES);
  });

  it('reads the deployed /portal-config.json over the defaults', async () => {
    const requested: string[] = [];
    const config = await loadPortalConfig((url) => {
      requested.push(url);
      return respondWith(JSON.stringify(DEPLOYED), 'application/json')(url);
    });
    expect(requested).toEqual([RUNTIME_CONFIG_URL]);
    expect(config).toEqual({ ...PORTAL_CONFIG_VALUES, ...DEPLOYED });
  });

  it('refuses a mistyped dataSource or authMode instead of falling back', () => {
    expect(() => mergePortalConfig(PORTAL_CONFIG_VALUES, { dataSource: 'htpp' })).toThrow(
      'portal-config.json: dataSource must be one of mock, http, not "htpp"',
    );
    expect(() => mergePortalConfig(PORTAL_CONFIG_VALUES, { authMode: 'cognitoo' })).toThrow(
      'portal-config.json: authMode must be one of none, cognito, not "cognitoo"',
    );
    expect(() => mergePortalConfig(PORTAL_CONFIG_VALUES, ['http'])).toThrow('portal-config.json: must be a JSON object');
  });

});
```

- [ ] **Step 2: Run it**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/config/portal-config.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: `✘ [ERROR] No matching export in "src/app/core/config/portal-config.ts" for import "RUNTIME_CONFIG_URL"` (and the same for `loadPortalConfig`, `mergePortalConfig`).

- [ ] **Step 3: Implement.** Replace `web/src/app/core/config/portal-config.ts` with:
```ts
import { InjectionToken } from '@angular/core';

export const DATA_SOURCES = ['mock', 'http'] as const;
export type DataSource = (typeof DATA_SOURCES)[number];

/** TEAM_PLAN §3 AUTH_MODE: 'none' runs as a demo user; 'cognito' signs in and sends the JWT. */
export const AUTH_MODES = ['none', 'cognito'] as const;
export type AuthMode = (typeof AUTH_MODES)[number];

export interface PortalConfig {
  /** The one switch between the mock fixtures and the real API. */
  dataSource: DataSource;
  authMode: AuthMode;
  /** API Gateway base URL, used when dataSource is 'http'. */
  apiBaseUrl: string;
  /** Simulated network delay for the mock, so loading states are visible. */
  mockLatencyMs: number;
}

/**
 * The defaults: local development and the tests run on the mock fixtures with no sign-in. A deployment overrides
 * them with /portal-config.json, which the WebStack writes next to index.html (see web/README.md, "Deployed config").
 */
export const PORTAL_CONFIG_VALUES: PortalConfig = {
  dataSource: 'mock',
  authMode: 'none',
  apiBaseUrl: '/api',
  mockLatencyMs: 400,
};

export const PORTAL_CONFIG = new InjectionToken<PortalConfig>('PORTAL_CONFIG', {
  providedIn: 'root',
  factory: () => PORTAL_CONFIG_VALUES,
});

/** Absolute, so a deep link such as /publish/run-1 still finds it at the site root. */
export const RUNTIME_CONFIG_URL = '/portal-config.json';
const RUNTIME_CONFIG_NAME = 'portal-config.json';
const JSON_CONTENT_TYPE = 'application/json';

function requireOneOf<T extends string>(field: string, value: unknown, allowed: readonly T[]): void {
  if (!allowed.includes(value as T)) {
    throw new Error(`${RUNTIME_CONFIG_NAME}: ${field} must be one of ${allowed.join(', ')}, not ${JSON.stringify(value)}`);
  }
}

/** The deployment's settings over the defaults. A typo fails loudly: it must never silently mean mock data. */
export function mergePortalConfig(defaults: PortalConfig, overrides: unknown): PortalConfig {
  if (overrides === null || typeof overrides !== 'object' || Array.isArray(overrides)) {
    throw new Error(`${RUNTIME_CONFIG_NAME}: must be a JSON object`);
  }
  const merged = { ...defaults, ...(overrides as Partial<PortalConfig>) };
  requireOneOf('dataSource', merged.dataSource, DATA_SOURCES);
  requireOneOf('authMode', merged.authMode, AUTH_MODES);
  return merged;
}

/**
 * Reads /portal-config.json before the app starts. When there is none (yarn start, yarn test), or the host answers
 * with its index.html fallback instead, the defaults apply.
 */
export async function loadPortalConfig(
  fetchConfig: (url: string) => Promise<Response> = (url) => fetch(url),
): Promise<PortalConfig> {
  const response = await fetchConfig(RUNTIME_CONFIG_URL);
  const isJson = response.ok && (response.headers.get('content-type') ?? '').includes(JSON_CONTENT_TYPE);
  return isJson ? mergePortalConfig(PORTAL_CONFIG_VALUES, await response.json()) : PORTAL_CONFIG_VALUES;
}
```
Replace `web/src/main.ts` with:
```ts
import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';
import { PORTAL_CONFIG, loadPortalConfig } from './app/core/config/portal-config';

loadPortalConfig()
  .then((portalConfig) =>
    bootstrapApplication(App, {
      ...appConfig,
      providers: [...appConfig.providers, { provide: PORTAL_CONFIG, useValue: portalConfig }],
    }),
  )
  .catch((error: unknown) => console.error(error));
```

- [ ] **Step 4: README.** In `web/README.md`, add after the `### Data` section (before `### Troubleshooting`):
```markdown
### Deployed config

`yarn start` and `yarn test` run on the defaults in `src/app/core/config/portal-config.ts`: mock data, no sign-in. A deployment changes them **without a rebuild**: before the app starts, `main.ts` reads `/portal-config.json` from the site root. The WebStack (Michael) writes that file next to `index.html`:

```json
{ "dataSource": "http", "authMode": "none", "apiBaseUrl": "/api" }
```

- Missing file, or the host's `index.html` fallback instead of JSON → the defaults.
- A mistyped `dataSource` or `authMode` stops the app with an error in the browser console; it never falls back to mock data silently.
- `apiBaseUrl` stays `/api`: CloudFront forwards `/api/*` to API Gateway on the same origin, so there is no CORS.
```

- [ ] **Step 5: Run it, the suite and the build; commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/config/portal-config.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
(cd web && yarn build 2>&1 | grep -E "ERROR|bundle generation complete")
git add web/src/app/core/config web/src/main.ts web/README.md
git commit -m "Read the deployment's /portal-config.json before start-up; typos fail loudly"
```
Expected: `Tests  4 passed (4)`; `Test Files  32 passed (32)` and `Tests  95 passed (95)`. The build prints `Application bundle generation complete.`

- [ ] **Step 6: Check it in the browser.** `(cd web && yarn start)`; http://localhost:4200 shows the mock dashboard (58%). Then create `web/public/portal-config.json` with `{"dataSource": "htpp"}`, reload: blank page, console `Error: portal-config.json: dataSource must be one of mock, http, not "htpp"`. **Delete the file** (`rm web/public/portal-config.json`) and confirm `git status --short web/public` prints nothing.

**Task done when:** 4 config tests pass; `yarn test` reports 95 passed; the typo check in Step 6 behaved as written and no `portal-config.json` is committed.

### Task 4: The deployed portal on the live API (verify in AWS; not dry-run)
Needs: L1 and L2 merged and deployed, Y1's ApiStack, M4's WebStack writing `/portal-config.json`. Do it with Linus and Yaw at the D1 18:00 walking skeleton. Replace `<cf>` with the CloudFront domain from Michael's stack outputs.

- [ ] **Step 1: The config is deployed**
```bash
curl -s https://<cf>/portal-config.json
```
Expected: `{"dataSource": "http", "authMode": "none", "apiBaseUrl": "/api"}` (keys in any order). Anything else: stop and ask Michael (M4).
- [ ] **Step 2: The API answers through CloudFront**
```bash
curl -s -o /dev/null -w "%{http_code}\n" https://<cf>/api/summary
curl -s https://<cf>/api/summary | python3 -c "import json,sys; body = json.load(sys.stdin); print(body['overall']['pct'], body['open_blockers']['count'], body['final_cutover']['days_remaining'])"
```
Expected: `200`, then `58.1 7 102`.
- [ ] **Step 3: The screen.** Open `https://<cf>/` in a private window. Expected: the same KPI values as mock mode: 58%, 96%, 7, 102, 103%; four entity rows. DevTools → Network shows `portal-config.json` 200 and `summary` 200 from `/api/summary`.
- [ ] **Step 4: Click a number.** Click **58%**. Expected: the drawer says "49 source rows"; Network shows one `rows?cite=reconciliation_results:RC-PROD-E1-E1-company_codes,…` request (Angular leaves `:` and `,` unencoded) with status 200.
- [ ] **Step 5: Record it.** Ledger line: `Task 4: live — <cf> — summary 58.1/7/102 — rows 49 — <date time>`. If any step fails, the fallback for the demo is unchanged: `portal-config.json` with `"dataSource": "mock"` (Michael changes it; no rebuild).

**Task done when:** Steps 1–4 match their `Expected:` lines and the ledger line exists.

### Task 5: Review, then PR (after Mildred's OK)
- [ ] **Step 1:** Work through the Review Focus by hand (1–2 locally, 3–5 in AWS once Task 4 is done); write each result in the ledger.
- [ ] **Step 2:** `git diff develop --stat` lists only the files in Tasks 1–3 (8 files).
- [ ] **Step 3:** Fresh review against [[F2 - Click a number and the live API - spec]]; fix critical and important findings test-first.
- [ ] **Step 4 (with Mildred's OK only):** `git push -u origin feature/web-rows-and-live-api`; PR to `develop` titled "Front end: API error body, click-a-number tests, deployed config (F2)". Body: what changed, `yarn test` 95 passed, Task 4's ledger line (or "live check pending M4"), the rulings. No attribution lines. Tell Michael the `portal-config.json` contract (§1 Assumptions).
- [ ] **Step 5:** [[Build order]] row F2: `in review (PR #nn)`, then `merged`.

**Task done when:** the PR is open to `develop` with a green Jenkins front-end build.

## Never
- Compute a KPI, a status or a date in the browser; show what the API returns.
- Send scope (role, entities, tenant) in a request body, query string or header.
- Log, print or store a token yourself.
- Add a `package-lock.json`, or change `yarn.lock` other than with `yarn add`.
- Commit the npm token, a password or any secret.
- Push to `develop` or `main`, or add attribution lines.
- Commit a `portal-config.json` (the stack writes it; a committed one would override every deployment).
- Hardcode a CloudFront domain, API URL, pool ID or client ID in the source.
- Fall back to mock data when the deployed config is wrong.

## Done means
- [ ] **Tests:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` → `Test Files  32 passed (32)`, `Tests  95 passed (95)`. *Verify:* run it.
- [ ] **Error body:** `(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/api/http-portal-api.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)` → `Tests  6 passed (6)`. *Verify:* run it.
- [ ] **Click a number (mock):** `yarn start`, click 58% → drawer "49 source rows". *Verify:* by hand.
- [ ] **Config:** no file → mock dashboard; `{"dataSource": "htpp"}` → blank page and the console error quoted in Task 3 Step 6. *Verify:* by hand, then delete the file.
- [ ] **Live (verify in AWS):** `curl -s https://<cf>/portal-config.json` shows `"dataSource": "http"`; the portal at `https://<cf>/` shows 58%, 96%, 7, 102, 103%; 58% opens 49 rows from `/api/rows`. *Verify:* Task 4 Steps 1–4, ledger line.
- [ ] **PR:** open to `develop` titled "Front end: API error body, click-a-number tests, deployed config (F2)"; [[Build order]] row F2 updated. *Verify:* `gh pr list --head feature/web-rows-and-live-api`.

Related: [[F2 - Click a number and the live API - spec]], [[F1b - Real fixtures and the dashboard on the contract keys - spec]], [[Build order]], [[How to execute a plan]]
