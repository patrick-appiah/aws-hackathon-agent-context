---
tags: [build, spec, area/frontend]
id: F2
owner: Mildred
status: ready
updated: 2026-10-14
---
# F2: click a number → its source rows, and the portal on the live API (spec)
> **"Click a number to see its source rows" on the real `/rows`, and the deployed portal on the real API.** Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after F1b is merged; the live steps need L2 (handlers), Y1 (API) and M4 (CloudFront) deployed.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Mildred - front end]].
3. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
4. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
5. [[F1b - Real fixtures and the dashboard on the contract keys - spec]]: the screen and fixtures this item builds on.
6. [[L2 - Entity and rows handlers - spec]] (Linus): `/rows` and the error body; [[L1 - Scope from the token and the summary handler - spec]]: `/summary`.
7. `docs/DEVOPS_HANDOVER.md` (repo) and [[Michael - DevOps]] (WebStack: CloudFront, `/api/*`) and [[Yaw - DevOps]] (ApiStack).
8. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. **The error body.** `HttpPortalApi` turns a contract error (`{error, detail}`, 400/401/403/404) into `ApiError(status, detail, code)`, so every screen shows the API's own words ("Entity E2 is outside your access."). Other failures keep today's behaviour.
2. **Click a number, see its rows.** Already wired in PR #12 (`CitedNumber` → `CitationViewer` → `PortalApi.rows` → `RowViewer`). F2 pins it with two tests on the contract fixtures: 58% opens its 49 reconciliation rows; the drawer lists `missing` citations separately under "Not available to you".
3. **The deployed config without a rebuild.** `main.ts` reads `/portal-config.json` (written by the WebStack) before the app starts and merges it over the defaults; local runs and tests keep `mock`. A typo fails loudly.
4. **Switch the deployed portal to `http`** against the live API (D1 18:00 walking skeleton, with Linus, Yaw and Michael): verify in AWS.

**Why:** the brief's acceptance "clicking 58% shows the passing reconciliation rows" and "the one screen on the live `/summary`". A config baked into the build would need a rebuild per stack; the clean-deploy check deploys a second copy with a new prefix (new CloudFront domain, new Cognito IDs), so the settings must come from the stack.

**Success means:**
- A 403 body `{"error": "out_of_scope", "detail": "Entity E2 is outside your access."}` rejects with `{status: 403, code: 'out_of_scope', message: 'Entity E2 is outside your access.'}`.
- In the dashboard (mock), clicking **58%** opens the drawer with **"49 source rows"**, starting at `Reconciliation results, RC-PROD-E1-E1-company_codes`.
- `loadPortalConfig` returns the defaults with no file or an HTML fallback, merges a JSON file, and throws `portal-config.json: dataSource must be one of mock, http, not "htpp"` on a typo.
- **In AWS (verify there):** `https://<CloudFront domain>/portal-config.json` returns the JSON above; the portal shows the same figures as mock mode; clicking 58% sends `GET /api/rows?cite=reconciliation_results:RC-PROD-E1-E1-company_codes,…` and shows 49 rows.
- `yarn test`: 95 passed (F1b's 88 + 7).

**Assumptions (reconcile with the owners):**
- **M4 (Michael, WebStack)** deploys `/portal-config.json` at the site root (for example `s3_deployment.Source.json_data`), served as `application/json` with `Cache-Control: no-cache`, containing `{"dataSource": "http", "authMode": "none", "apiBaseUrl": "/api"}` until the Cognito go/no-go (F3a adds the `cognito` block). Its SPA error responses map 403/404 to `/index.html` (the loader tolerates that).
- **L2 (Linus)** answers `GET /rows?cite=artefact:row_id,…` with `RowsResponse` and errors with `ErrorResponse` (C1). The longest `cite` the screen sends is the 58% card's 49 citations (about 2.3 KB of URL), well under CloudFront's 8,192-byte limit.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Where deployed settings come from | `/portal-config.json` read in `main.ts` before bootstrap, merged over `PORTAL_CONFIG_VALUES`, provided as `PORTAL_CONFIG` | Angular `fileReplacements` per environment (a rebuild per stack; the clean deploy changes the IDs); `environment.ts` with hardcoded IDs |
| A missing or odd config | Missing / non-JSON (the SPA fallback) → defaults; unknown `dataSource` / `authMode` → throw (console error, blank app) | Silently falling back to mock (a typo would show mock data on the live demo) |
| The error message | The API's `detail` (it is written for people: "Entity E2 is outside your access.") | Our own messages per status (two sources of wording) |
| Click-a-number tests | Characterisation tests on the contract fixtures (the behaviour exists; the tests pin it) | Rewriting the viewer |

## 3. The shapes
- `class ApiError extends Error { constructor(status: number, message: string, code?: ErrorCode) }`; `ApiError.outOfScope(entityId)` has code `out_of_scope`, `ApiError.notFound(what)` has `not_found`; `isErrorResponse(body: unknown): body is ErrorResponse` *(new)* in `core/api/api-error.ts`.
- `core/config/portal-config.ts`: `DATA_SOURCES`, `AUTH_MODES` (as const), `RUNTIME_CONFIG_URL = '/portal-config.json'`, `mergePortalConfig(defaults: PortalConfig, overrides: unknown): PortalConfig`, `loadPortalConfig(fetchConfig?: (url: string) => Promise<Response>): Promise<PortalConfig>` *(all new)*.
- `src/main.ts`: `loadPortalConfig().then((portalConfig) => bootstrapApplication(App, {...appConfig, providers: [...appConfig.providers, { provide: PORTAL_CONFIG, useValue: portalConfig }]}))`.

## 4. Tests
- `core/api/http-portal-api.spec.ts`: +1 (the contract error body; validated with `contractErrors('error', …)` first).
- `features/dashboard/dashboard-page.spec.ts` *(new)*, 1: click 58% → "49 source rows".
- `shared/citations/row-viewer/row-viewer.spec.ts` *(new)*, 1: rows and `missing` from a fake `PortalApi`.
- `core/config/portal-config.spec.ts` *(new)*, 4: no file, HTML fallback, the deployed file, typos.

## 5. Out of scope
- Cognito settings in the config and sign-in: **F3a** (Clement adds the `cognito` block to `PortalConfig`).
- The WebStack itself (M4), the handlers (L1, L2), the API (Y1).

Related: [[F2 - Click a number and the live API - plan]], [[Build order]], [[Mildred - front end]]
