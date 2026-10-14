---
tags: [build, plan, area/frontend]
id: F3a
owner: Clement
spec: "[[F3a - Cognito sign-in - spec]]"
status: ready
updated: 2026-10-14
---
# F3a: Cognito sign-in (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[F3a - Cognito sign-in - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger as a `Ruling:` line.
3. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Clement - front end]].
4. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
5. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
6. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

**Goal:** in cognito mode, the portal signs the user in through managed login (code + PKCE), shows what their ID token allows, sends the ID token to the API, and signs them out cleanly.

**Architecture:** `main.ts` → `loadPortalConfig()` → in cognito mode `provideCognitoAuth(settings)` → app initializer `CognitoSession.start()` (`checkAuth`: handles `?code=`) → `SessionStore` (ID token + displayed scope) → `bearerTokenInterceptor` adds `Authorization: Bearer <ID token>` to `/api/*` → API Gateway JWT authorizer → Linus's `scope_from_claims`.

**Tech stack:** Angular 22, `angular-auth-oidc-client` 22.0.1, TypeScript 6, Vitest through `ng test`.

**Dry-run:** Tasks 1–4 were run on 2026-10-14 in a throwaway worktree with C1, F1a, F1b, F2, F4a, F3b and F5 applied; counts and messages are real (the library was installed with `yarn add`; its flows were faked in tests). **Task 5 needs Cognito: verify in AWS** (no AWS calls were made).

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your own clone). Branch **`feature/web-cognito-sign-in`** from an up-to-date `develop`, after every dependency in [[Build order]] is merged. Never commit to, or push, `develop` or `main`; PR to `develop`; Patrick merges.
- **Start state:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` on `develop` with C1, F1a, F1b and F2 merged. Dry-run order (with F4a, F3b, F5): `Test Files  35 passed (35)`, `Tests  107 passed (107)`. What must match is the increase per task (+3, +4, +3, +4). Write your start count in the ledger.
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
- **Stay in your files** (Clement's list in the brief). This item touches `web/package.json`, `web/yarn.lock`, `web/src/app/core/session/`, `web/src/app/core/api/bearer-token-interceptor.ts` (+ spec), `web/src/app/features/auth/`, `web/src/app/shared/layout/app-header/`, and Mildred's files below.
- **Cross-owner edits:** **Mildred's** `web/src/app/core/config/portal-config.ts` (+ spec: the `cognito` block), `web/src/main.ts` (the provider) and `web/src/app/app.routes.ts` (the guard): exactly the edits in Tasks 1–3; she agrees first (her brief: "Clement asks you before changing `authMode` handling").
- **Commits:** small, one per task, with the message given. **No `Co-Authored-By` and no "Generated with" lines** in commits or the PR.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **No token in a log, a URL or `localStorage`:** `grep -rn "console\.\(log\|info\|debug\)" web/src/app` prints nothing new; live, DevTools → Application → Local Storage is empty; the address bar never shows a token (only `?code=…&state=…` once, on the way back).
2. **PKCE is on:** live, the managed login request URL contains `code_challenge=` and `code_challenge_method=S256`.
3. **The ID token, not the access token, goes to the API:** live, decode the `Authorization` header's middle part (paste it into a local `base64 -d`, never into a website): it has `aud` = the client ID and `custom:entity_ids`.
4. **Renewal:** leave the portal open past the ID token's lifetime (Cognito default 60 minutes, or ask Michael for a 5-minute test client): the next `/api` call still succeeds (the library renewed it) or, if renewal fails, the user lands on sign-in with "Your session has expired". Never an error page.
5. **`AUTH_MODE=none` unchanged:** with no `portal-config.json`, `yarn start` shows the role switcher and no "Sign out", and the browser makes no request to `cognito-idp`.

---

### Task 1: The library, the settings and the claims

**Files:**
- Modify: `web/package.json`, `web/yarn.lock` (via `yarn add`), Mildred's `web/src/app/core/config/portal-config.ts` and `portal-config.spec.ts` *(new)*
- Create: `web/src/app/core/session/id-token-claims.ts` *(new)*, `id-token-claims.spec.ts` *(new)* *(new)*

**Produces:** `CognitoSettings`, `PortalConfig.cognito?`, `scopeFromIdTokenClaims(claims)`.

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
git switch -c feature/web-cognito-sign-in
mkdir -p .superpowers && printf '# Ledger: F3a Cognito sign-in\n' > .superpowers/ledger-F3a.md
(cd web && yarn install --frozen-lockfile)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
```
Expected: the start state (dry-run order: `Test Files  35 passed (35)`, `Tests  107 passed (107)`).

- [ ] **Step 2: Add the library**
```bash
(cd web && yarn add angular-auth-oidc-client@22.0.1 2>&1 | tail -1)
git diff --stat web/package.json web/yarn.lock
```
Expected: `Done in …`; `web/package.json | 1 +` and `web/yarn.lock | 13 +++++++++++++` (the library and its one dependency, `rfc4648`).

- [ ] **Step 3: The failing tests.** Replace `web/src/app/core/config/portal-config.spec.ts` *(new)*:
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

  it('needs the three Cognito settings in cognito mode', () => {
    expect(() => mergePortalConfig(PORTAL_CONFIG_VALUES, { authMode: 'cognito', cognito: { clientId: 'example-client-id' } })).toThrow(
      'portal-config.json: authMode cognito needs cognito.authority, cognito.domain',
    );
    const cognito = {
      authority: 'https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_example',
      clientId: 'example-client-id',
      domain: 'https://erp-portal-example.auth.eu-west-1.amazoncognito.com',
    };
    expect(mergePortalConfig(PORTAL_CONFIG_VALUES, { authMode: 'cognito', cognito }).cognito).toEqual(cognito);
  });
});
```
Create `web/src/app/core/session/id-token-claims.spec.ts` *(new)*:
```ts
import { scopeFromIdTokenClaims } from './id-token-claims';

const E4_LEAD_CLAIMS = {
  sub: '0f4c-e4-lead',
  'cognito:groups': ['entity_lead'],
  'custom:tenant_id': 't-01',
  'custom:entity_ids': 'E4',
};

describe('scopeFromIdTokenClaims', () => {
  it('reads the role, tenant and entities the API will enforce (display only)', () => {
    expect(scopeFromIdTokenClaims(E4_LEAD_CLAIMS)).toEqual({
      user_id: '0f4c-e4-lead',
      role: 'entity_lead',
      tenant_id: 't-01',
      entity_ids: ['E4'],
    });
    expect(scopeFromIdTokenClaims({ ...E4_LEAD_CLAIMS, 'custom:entity_ids': 'E2, E4' })?.entity_ids).toEqual(['E2', 'E4']);
    expect(scopeFromIdTokenClaims({ ...E4_LEAD_CLAIMS, 'cognito:groups': ['cfo'], 'custom:entity_ids': '*' })?.entity_ids).toEqual(['*']);
  });

  it('gives no scope unless the user is in exactly one known group, with a tenant and entities', () => {
    expect(scopeFromIdTokenClaims({ ...E4_LEAD_CLAIMS, 'cognito:groups': [] })).toBeUndefined();
    expect(scopeFromIdTokenClaims({ ...E4_LEAD_CLAIMS, 'cognito:groups': ['cfo', 'sponsor'] })).toBeUndefined();
    expect(scopeFromIdTokenClaims({ ...E4_LEAD_CLAIMS, 'cognito:groups': ['admin'] })).toBeUndefined();
    expect(scopeFromIdTokenClaims({ ...E4_LEAD_CLAIMS, 'custom:tenant_id': undefined })).toBeUndefined();
    expect(scopeFromIdTokenClaims({ ...E4_LEAD_CLAIMS, 'custom:entity_ids': '' })).toBeUndefined();
  });
});
```

- [ ] **Step 4: Run them**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/config --include src/app/core/session/id-token-claims.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: `✘ [ERROR] TS2307: Cannot find module './id-token-claims' or its corresponding type declarations.`

- [ ] **Step 5: Implement.** Create `web/src/app/core/session/id-token-claims.ts`:
```ts
/**
 * The scope the portal SHOWS for a Cognito ID token: the same rules as Linus's auth/scope.py `scope_from_claims`
 * (exactly one group = the role; custom:entity_ids is a comma-separated string). Display only: the API builds
 * and enforces the real scope from the same token. The client never sends scope.
 */
import { ROLES, Role, Scope } from '../models';

const GROUPS_CLAIM = 'cognito:groups';
const TENANT_CLAIM = 'custom:tenant_id';
const ENTITIES_CLAIM = 'custom:entity_ids';
const SUBJECT_CLAIM = 'sub';
const ENTITY_SEPARATOR = ',';

export function scopeFromIdTokenClaims(claims: Record<string, unknown>): Scope | undefined {
  const groups = claims[GROUPS_CLAIM];
  const tenantId = claims[TENANT_CLAIM];
  const entities = claims[ENTITIES_CLAIM];
  const userId = claims[SUBJECT_CLAIM];
  if (!Array.isArray(groups) || groups.length !== 1 || !ROLES.includes(groups[0] as Role)) return undefined;
  if (typeof tenantId !== 'string' || !tenantId || typeof entities !== 'string' || typeof userId !== 'string') return undefined;
  const entityIds = entities.split(ENTITY_SEPARATOR).map((entityId) => entityId.trim()).filter(Boolean);
  if (!entityIds.length) return undefined;
  return { user_id: userId, role: groups[0] as Role, tenant_id: tenantId, entity_ids: entityIds };
}
```
Then (Mildred's file, agreed):
- In `web/src/app/core/config/portal-config.ts`, replace
```ts
export interface PortalConfig {
```
  with
```ts
/** Cognito managed login (Michael's AuthStack outputs). None of these is a secret: a SPA client has no secret. */
export interface CognitoSettings {
  /** The OIDC issuer: https://cognito-idp.eu-west-1.amazonaws.com/<user pool ID> */
  authority: string;
  /** The app client ID, which is also the API's JWT authorizer audience. */
  clientId: string;
  /** The managed login domain, for sign-out: https://<prefix>.auth.eu-west-1.amazoncognito.com */
  domain: string;
}

const COGNITO_SETTING_NAMES: readonly (keyof CognitoSettings)[] = ['authority', 'clientId', 'domain'];

export interface PortalConfig {
```
- In `web/src/app/core/config/portal-config.ts`, replace
```ts
  mockLatencyMs: number;
}
```
  with
```ts
  mockLatencyMs: number;
  /** Required when authMode is 'cognito'. */
  cognito?: CognitoSettings;
}
```
- In `web/src/app/core/config/portal-config.ts`, replace
```ts
  requireOneOf('authMode', merged.authMode, AUTH_MODES);
  return merged;
```
  with
```ts
  requireOneOf('authMode', merged.authMode, AUTH_MODES);
  if (merged.authMode === 'cognito') {
    const missing = COGNITO_SETTING_NAMES.filter((name) => typeof merged.cognito?.[name] !== 'string' || !merged.cognito[name]);
    if (missing.length) throw new Error(`${RUNTIME_CONFIG_NAME}: authMode cognito needs cognito.${missing.join(', cognito.')}`);
  }
  return merged;
```

- [ ] **Step 6: Run, suite, commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/config --include src/app/core/session/id-token-claims.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
git add web/package.json web/yarn.lock web/src/app/core/config web/src/app/core/session/id-token-claims.ts web/src/app/core/session/id-token-claims.spec.ts
git commit -m "Cognito settings in the deployed config, and the scope an ID token shows (display only)"
```
Expected: `Test Files  2 passed (2)`, `Tests  7 passed (7)`; the suite at **start + 1 file, + 3 tests** (dry-run: 36 files, 110 tests).

**Task done when:** the suite is at start + 3 and `git show --stat HEAD` includes `web/yarn.lock`.

### Task 2: The Cognito session

**Files:** Create `web/src/app/core/session/cognito-session.ts` *(new)*, `cognito-session.spec.ts` *(new)* *(new)*. Modify `web/src/app/core/session/session-store.ts`, Mildred's `web/src/main.ts`.

**Produces:** `cognitoOidcConfig(settings: CognitoSettings, origin: string): OpenIdConfiguration`, `cognitoLogoutUrl(settings, origin): string`, `CognitoSession.start(): Promise<void>`, `.signIn(): void`, `.signOut(leave?, origin?): void`, `provideCognitoAuth(settings): EnvironmentProviders`, `SessionStore.signedIn`, `SessionStore.clear()`. **Consumes:** `OidcSecurityService` (`checkAuth`, `isAuthenticated$`, `getIdToken`, `getPayloadFromIdToken`, `authorize`, `logoffLocal`), `StsConfigStaticLoader`, `provideAuth`, `LogLevel`.

- [ ] **Step 1: The failing test.** Create `web/src/app/core/session/cognito-session.spec.ts` *(new)*:
```ts
import { TestBed } from '@angular/core/testing';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { of } from 'rxjs';

import { CognitoSettings, PORTAL_CONFIG, PORTAL_CONFIG_VALUES } from '../config/portal-config';
import { CognitoSession, cognitoLogoutUrl, cognitoOidcConfig } from './cognito-session';
import { SessionStore } from './session-store';

const SETTINGS: CognitoSettings = {
  authority: 'https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_example',
  clientId: 'example-client-id',
  domain: 'https://erp-portal-example.auth.eu-west-1.amazoncognito.com',
};
const ORIGIN = 'https://d111111abcdef8.cloudfront.net';
const ID_TOKEN = 'header.payload.signature';
const E4_LEAD_CLAIMS = { sub: 'u-e4', 'cognito:groups': ['entity_lead'], 'custom:tenant_id': 't-01', 'custom:entity_ids': 'E4' };

function fakeOidc(isAuthenticated: boolean) {
  return {
    checkAuth: vi.fn(() => of({ isAuthenticated, idToken: isAuthenticated ? ID_TOKEN : '', accessToken: '', userData: null })),
    isAuthenticated$: of({ isAuthenticated, allConfigsAuthenticated: [] }),
    getIdToken: vi.fn(() => of(ID_TOKEN)),
    getPayloadFromIdToken: vi.fn(() => of(E4_LEAD_CLAIMS)),
    authorize: vi.fn(),
    logoffLocal: vi.fn(),
  };
}

function sessionWith(oidc: ReturnType<typeof fakeOidc>): CognitoSession {
  TestBed.configureTestingModule({
    providers: [
      CognitoSession,
      { provide: OidcSecurityService, useValue: oidc },
      { provide: PORTAL_CONFIG, useValue: { ...PORTAL_CONFIG_VALUES, authMode: 'cognito', cognito: SETTINGS } },
    ],
  });
  return TestBed.inject(CognitoSession);
}

describe('CognitoSession', () => {
  it('configures managed login with the authorization code flow, PKCE and refresh tokens', () => {
    expect(cognitoOidcConfig(SETTINGS, ORIGIN)).toMatchObject({
      authority: SETTINGS.authority,
      clientId: SETTINGS.clientId,
      redirectUrl: `${ORIGIN}/`,
      postLogoutRedirectUri: `${ORIGIN}/`,
      responseType: 'code',
      scope: 'openid email profile',
      useRefreshToken: true,
      silentRenew: true,
      ignoreNonceAfterRefresh: true,
    });
    expect(cognitoLogoutUrl(SETTINGS, ORIGIN)).toBe(
      'https://erp-portal-example.auth.eu-west-1.amazoncognito.com/logout?client_id=example-client-id&logout_uri=https%3A%2F%2Fd111111abcdef8.cloudfront.net%2F',
    );
  });

  it('after the redirect back, puts the ID token and its role and entities into the session', async () => {
    const oidc = fakeOidc(true);
    await sessionWith(oidc).start();
    const store = TestBed.inject(SessionStore);
    expect(oidc.checkAuth).toHaveBeenCalledTimes(1);
    expect(store.idToken()).toBe(ID_TOKEN);
    expect(store.scope()).toEqual({ user_id: 'u-e4', role: 'entity_lead', tenant_id: 't-01', entity_ids: ['E4'] });
    expect(store.signedIn()).toBe(true);
  });

  it('stays signed out when Cognito has no session, and sends the user to managed login on sign-in', async () => {
    const oidc = fakeOidc(false);
    const session = sessionWith(oidc);
    await session.start();
    expect(TestBed.inject(SessionStore).signedIn()).toBe(false);
    session.signIn();
    expect(oidc.authorize).toHaveBeenCalledTimes(1);
  });

  it('signs out locally, forgets the token and leaves through the Cognito logout endpoint', async () => {
    const oidc = fakeOidc(true);
    const session = sessionWith(oidc);
    await session.start();
    const leave = vi.fn();
    session.signOut(leave, ORIGIN);
    expect(oidc.logoffLocal).toHaveBeenCalledTimes(1);
    expect(TestBed.inject(SessionStore).idToken()).toBeUndefined();
    expect(leave).toHaveBeenCalledWith(cognitoLogoutUrl(SETTINGS, ORIGIN));
  });
});
```
- [ ] **Step 2: Run it**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/session/cognito-session.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: `✘ [ERROR] TS2307: Cannot find module './cognito-session' or its corresponding type declarations.` and `✘ [ERROR] TS2339: Property 'signedIn' does not exist on type 'SessionStore'.`
- [ ] **Step 3: Implement.** Create `web/src/app/core/session/cognito-session.ts`:
```ts
import { EnvironmentProviders, Injectable, inject, makeEnvironmentProviders, provideAppInitializer } from '@angular/core';
import { LogLevel, OidcSecurityService, OpenIdConfiguration, StsConfigLoader, StsConfigStaticLoader, provideAuth } from 'angular-auth-oidc-client';
import { firstValueFrom } from 'rxjs';

import { CognitoSettings, PORTAL_CONFIG } from '../config/portal-config';
import { scopeFromIdTokenClaims } from './id-token-claims';
import { SessionStore } from './session-store';

/** Custom claims (role group, tenant, entities) are only in the ID token, so that is what the API receives. */
const OIDC_SCOPES = 'openid email profile';
const AUTHORIZATION_CODE_RESPONSE = 'code';
/** Renew a minute before the ID token expires, so a request never goes out with an expired one. */
const RENEW_SECONDS_BEFORE_EXPIRY = 60;

/**
 * angular-auth-oidc-client settings for Cognito managed login: authorization code + PKCE (the library always uses
 * PKCE with the code flow), refresh tokens for renewal, and warnings only in the console (it never logs tokens then).
 */
export function cognitoOidcConfig(settings: CognitoSettings, origin: string): OpenIdConfiguration {
  return {
    authority: settings.authority,
    clientId: settings.clientId,
    redirectUrl: `${origin}/`,
    postLogoutRedirectUri: `${origin}/`,
    responseType: AUTHORIZATION_CODE_RESPONSE,
    scope: OIDC_SCOPES,
    useRefreshToken: true,
    silentRenew: true,
    renewTimeBeforeTokenExpiresInSeconds: RENEW_SECONDS_BEFORE_EXPIRY,
    // Cognito's refreshed ID tokens carry no nonce.
    ignoreNonceAfterRefresh: true,
    logLevel: LogLevel.Warn,
  };
}

/** Cognito publishes no end_session_endpoint; its managed login signs out at /logout. */
export function cognitoLogoutUrl(settings: CognitoSettings, origin: string): string {
  const query = new URLSearchParams({ client_id: settings.clientId, logout_uri: `${origin}/` });
  return `${settings.domain}/logout?${query.toString()}`;
}

/** Bridges the OIDC library and the SessionStore: who is signed in, with which ID token. */
@Injectable({ providedIn: 'root' })
export class CognitoSession {
  private readonly oidc = inject(OidcSecurityService);
  private readonly session = inject(SessionStore);
  private readonly settings = inject(PORTAL_CONFIG).cognito;

  /** Runs once before the first route: handles the ?code= redirect from managed login, or an existing session. */
  async start(): Promise<void> {
    const result = await firstValueFrom(this.oidc.checkAuth());
    if (result.isAuthenticated) await this.refreshSession();
    // A silent renewal brings a new ID token: keep the bearer token current.
    this.oidc.isAuthenticated$.subscribe(({ isAuthenticated }) => {
      if (isAuthenticated) void this.refreshSession();
    });
  }

  signIn(): void {
    this.oidc.authorize();
  }

  signOut(leave: (url: string) => void = (url) => window.location.assign(url), origin = window.location.origin): void {
    this.oidc.logoffLocal();
    this.session.clear();
    if (this.settings) leave(cognitoLogoutUrl(this.settings, origin));
  }

  private async refreshSession(): Promise<void> {
    const [idToken, claims] = await Promise.all([
      firstValueFrom(this.oidc.getIdToken()),
      firstValueFrom(this.oidc.getPayloadFromIdToken()),
    ]);
    const scope = scopeFromIdTokenClaims(claims ?? {});
    if (scope) this.session.setScope(scope);
    this.session.setIdToken(idToken || undefined);
  }
}

/** Only for authMode 'cognito' (main.ts adds it): the OIDC library, and the session check before the first route. */
export function provideCognitoAuth(settings: CognitoSettings): EnvironmentProviders {
  return makeEnvironmentProviders([
    provideAuth({
      loader: {
        provide: StsConfigLoader,
        useFactory: () => new StsConfigStaticLoader(cognitoOidcConfig(settings, window.location.origin)),
      },
    }),
    provideAppInitializer(() => inject(CognitoSession).start()),
  ]);
}
```
Then:
- In `web/src/app/core/session/session-store.ts`, replace
```ts
  readonly idToken = this.currentIdToken.asReadonly();
```
  with
```ts
  readonly idToken = this.currentIdToken.asReadonly();
  /** Signed in with Cognito: an ID token is held. In AUTH_MODE=none nobody is, and nobody needs to be. */
  readonly signedIn = computed(() => this.currentIdToken() !== undefined);
```
- In `web/src/app/core/session/session-store.ts`, replace
```ts
  setIdToken(idToken: string | undefined): void {
    this.currentIdToken.set(idToken);
  }
```
  with
```ts
  setIdToken(idToken: string | undefined): void {
    this.currentIdToken.set(idToken);
  }

  /** Forget the token and fall back to the demo scope (sign-out, or an expired token). */
  clear(): void {
    this.currentIdToken.set(undefined);
    this.currentScope.set(DEMO_SCOPE);
  }
```
Replace Mildred's `web/src/main.ts`:
```ts
import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';
import { PORTAL_CONFIG, loadPortalConfig } from './app/core/config/portal-config';
import { provideCognitoAuth } from './app/core/session/cognito-session';

loadPortalConfig()
  .then((portalConfig) =>
    bootstrapApplication(App, {
      ...appConfig,
      providers: [
        ...appConfig.providers,
        { provide: PORTAL_CONFIG, useValue: portalConfig },
        // Sign-in only when the deployment asks for it; mergePortalConfig guarantees the settings are there.
        ...(portalConfig.authMode === 'cognito' && portalConfig.cognito ? [provideCognitoAuth(portalConfig.cognito)] : []),
      ],
    }),
  )
  .catch((error: unknown) => console.error(error));
```
- [ ] **Step 4: Run, suite, build, commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/session/cognito-session.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
(cd web && yarn build 2>&1 | grep -E "ERROR|bundle generation complete")
git add web/src/app/core/session web/src/main.ts
git commit -m "Cognito managed login with code + PKCE: the ID token and its displayed scope fill the session"
```
Expected: `Tests  4 passed (4)`; the suite at **start + 2 files, + 7 tests** (dry-run: 37 files, 114 tests); the build prints `Application bundle generation complete.`

**Task done when:** the 4 session tests pass; `grep -n "provideCognitoAuth" web/src/main.ts` prints two lines (import and use).

### Task 3: Every page needs a signed-in user (cognito mode)

**Files:** Create `web/src/app/features/auth/signed-in-guard.ts` *(new)*, `signed-in-guard.spec.ts` *(new)* *(new)*. Modify Mildred's `web/src/app/app.routes.ts`.

**Produces:** `signedInGuard: CanActivateFn`.

- [ ] **Step 1: The failing test.** Create `web/src/app/features/auth/signed-in-guard.spec.ts` *(new)*:
```ts
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, UrlTree, provideRouter } from '@angular/router';

import { AuthMode, PORTAL_CONFIG, PORTAL_CONFIG_VALUES } from '../../core/config/portal-config';
import { SessionStore } from '../../core/session/session-store';
import { signedInGuard } from './signed-in-guard';

function runGuard(authMode: AuthMode, idToken?: string): boolean | UrlTree {
  TestBed.configureTestingModule({
    providers: [provideRouter([]), { provide: PORTAL_CONFIG, useValue: { ...PORTAL_CONFIG_VALUES, authMode } }],
  });
  TestBed.inject(SessionStore).setIdToken(idToken);
  return TestBed.runInInjectionContext(() =>
    signedInGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
  ) as boolean | UrlTree;
}

describe('signedInGuard', () => {
  it('lets everyone through in AUTH_MODE=none (the demo user)', () => {
    expect(runGuard('none')).toBe(true);
  });

  it('lets a signed-in user through in cognito mode', () => {
    expect(runGuard('cognito', 'header.payload.signature')).toBe(true);
  });

  it('sends a signed-out user to the sign-in page in cognito mode', () => {
    const result = runGuard('cognito');
    expect(result).toBeInstanceOf(UrlTree);
    expect(TestBed.inject(Router).serializeUrl(result as UrlTree)).toBe('/sign-in');
  });
});
```
- [ ] **Step 2: Run it**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/features/auth/signed-in-guard.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: `✘ [ERROR] TS2307: Cannot find module './signed-in-guard' or its corresponding type declarations.`
- [ ] **Step 3: Implement.** Create `web/src/app/features/auth/signed-in-guard.ts`:
```ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { PORTAL_CONFIG } from '../../core/config/portal-config';
import { SessionStore } from '../../core/session/session-store';

/** In cognito mode, every page but sign-in needs a signed-in user. In AUTH_MODE=none the demo user is enough. */
export const signedInGuard: CanActivateFn = () => {
  if (inject(PORTAL_CONFIG).authMode !== 'cognito' || inject(SessionStore).signedIn()) return true;
  return inject(Router).createUrlTree(['/sign-in']);
};
```
Then (Mildred's routes, agreed):
- In `web/src/app/app.routes.ts`, replace
```ts
import { approverGuard } from './features/auth/approver-guard';
```
  with
```ts
import { approverGuard } from './features/auth/approver-guard';
import { signedInGuard } from './features/auth/signed-in-guard';
```
- In `web/src/app/app.routes.ts`, replace
```ts
    title: 'ERP migration progress',
    loadComponent
```
  with
```ts
    title: 'ERP migration progress',
    canActivate: [signedInGuard],
    loadComponent
```
- In `web/src/app/app.routes.ts`, replace
```ts
    title: 'Publish status pack',
    loadComponent
```
  with
```ts
    title: 'Publish status pack',
    canActivate: [signedInGuard],
    loadComponent
```
- In `web/src/app/app.routes.ts`, replace
```ts
canActivate: [approverGuard],
```
  with
```ts
canActivate: [signedInGuard, approverGuard],
```
- [ ] **Step 4: Run, suite, commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/features/auth/signed-in-guard.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
git add web/src/app/features/auth/signed-in-guard.ts web/src/app/features/auth/signed-in-guard.spec.ts web/src/app/app.routes.ts
git commit -m "In cognito mode every page but sign-in needs a signed-in user"
```
Expected: `Tests  3 passed (3)`; the suite at **start + 3 files, + 10 tests** (dry-run: 38 files, 117 tests).

**Task done when:** `grep -c signedInGuard web/src/app/app.routes.ts` prints `4`.

### Task 4: Sign-in page, sign-out, and an expired token

**Files:** Modify `web/src/app/features/auth/sign-in-page.ts`, `sign-in-page.html`, `sign-in-page.spec.ts`, `web/src/app/shared/layout/app-header/app-header.ts`, `.html`, `.scss`, `.spec.ts`, `web/src/app/core/api/bearer-token-interceptor.ts`, `.spec.ts`.

**Produces:** `SESSION_EXPIRED_REASON`; the header's "Sign out" (`button.sign-out`); the interceptor's 401 handling.

- [ ] **Step 1: The failing tests.** Replace:
- `web/src/app/features/auth/sign-in-page.spec.ts`:
```ts
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';

import { AuthMode, PORTAL_CONFIG, PORTAL_CONFIG_VALUES } from '../../core/config/portal-config';
import { CognitoSession } from '../../core/session/cognito-session';
import { SessionStore } from '../../core/session/session-store';
import { SignInPage } from './sign-in-page';

const PAGE_TIMEOUT_MS = 30_000;

const cognitoSession = { signIn: vi.fn() };

async function render(authMode: AuthMode, reason?: string) {
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      { provide: PORTAL_CONFIG, useValue: { ...PORTAL_CONFIG_VALUES, authMode } },
      { provide: CognitoSession, useValue: cognitoSession },
    ],
  });
  const fixture = TestBed.createComponent(SignInPage);
  if (reason) fixture.componentRef.setInput('reason', reason);
  await fixture.whenStable();
  return fixture;
}

describe('SignInPage', () => {
  it('offers the demo users in AUTH_MODE=none and signs in as the one picked', async () => {
    const fixture = await render('none');
    const element = fixture.nativeElement as HTMLElement;
    const buttons = [...element.querySelectorAll<HTMLButtonElement>('app-role-switcher button')];
    expect(buttons.map((button) => button.querySelector('.role')?.textContent)).toEqual([
      'CFO',
      'Sponsor',
      'Delivery lead',
      'Entity lead',
    ]);
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    buttons[3].click();
    expect(TestBed.inject(SessionStore).scope().entity_ids).toEqual(['E4']);
    expect(navigate).toHaveBeenCalledWith('/');
  }, PAGE_TIMEOUT_MS);

  it('explains why when the approver guard sent the user here', async () => {
    const element = (await render('none', 'approver')).nativeElement as HTMLElement;
    expect(element.textContent).toContain('Only a delivery lead can approve');
  }, PAGE_TIMEOUT_MS);

  it('sends the user to Cognito managed login in AUTH_MODE=cognito, with no role switcher', async () => {
    const element = (await render('cognito')).nativeElement as HTMLElement;
    expect(element.querySelector('app-role-switcher')).toBeNull();
    const signIn = element.querySelector<HTMLElement>('.portal-actions at-button');
    expect(signIn?.textContent?.trim()).toBe('Sign in');
    signIn?.dispatchEvent(new CustomEvent('atClick'));
    expect(cognitoSession.signIn).toHaveBeenCalledTimes(1);
  }, PAGE_TIMEOUT_MS);

  it('says why when an expired session sent the user here', async () => {
    const element = (await render('cognito', 'expired')).nativeElement as HTMLElement;
    expect(element.textContent).toContain('Your session has expired. Sign in again to continue.');
  }, PAGE_TIMEOUT_MS);
});
```
- `web/src/app/shared/layout/app-header/app-header.spec.ts`:
```ts
import { TestBed } from '@angular/core/testing';

import { PORTAL_CONFIG, PORTAL_CONFIG_VALUES } from '../../../core/config/portal-config';
import { CognitoSession } from '../../../core/session/cognito-session';
import { SessionStore } from '../../../core/session/session-store';
import { AppHeader } from './app-header';

describe('AppHeader', () => {
  it('shows the heading, the programme line and who is signed in', async () => {
    const fixture = TestBed.createComponent(AppHeader);
    fixture.componentRef.setInput('heading', 'ERP migration progress');
    fixture.componentRef.setInput('subheading', 'Group ERP consolidation, four entities moving onto one platform');
    fixture.componentRef.setInput('signedInAs', 'CFO');
    await fixture.whenStable();

    const element = fixture.nativeElement as HTMLElement;
    expect(element.querySelector('h1')?.textContent).toBe('ERP migration progress');
    expect(element.textContent).toContain('Group ERP consolidation');
    expect(element.textContent).toContain('Signed in as CFO');
    expect(element.textContent).toContain('Synthetic data');
  });

  it('leaves out the programme line when the API has none', async () => {
    const fixture = TestBed.createComponent(AppHeader);
    fixture.componentRef.setInput('heading', 'ERP migration progress');
    await fixture.whenStable();
    expect((fixture.nativeElement as HTMLElement).querySelector('.subheading')).toBeNull();
  });

  it('offers "Sign out" only to a user signed in with Cognito', async () => {
    const cognitoSession = { signOut: vi.fn() };
    TestBed.configureTestingModule({
      providers: [
        { provide: PORTAL_CONFIG, useValue: { ...PORTAL_CONFIG_VALUES, authMode: 'cognito' } },
        { provide: CognitoSession, useValue: cognitoSession },
      ],
    });
    TestBed.inject(SessionStore).setIdToken('header.payload.signature');
    const fixture = TestBed.createComponent(AppHeader);
    fixture.componentRef.setInput('heading', 'ERP migration progress');
    await fixture.whenStable();
    const signOut = (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>('button.sign-out');
    expect(signOut?.textContent?.trim()).toBe('Sign out');
    signOut?.click();
    expect(cognitoSession.signOut).toHaveBeenCalledTimes(1);
  });

  it('has no "Sign out" in AUTH_MODE=none', async () => {
    const fixture = TestBed.createComponent(AppHeader);
    fixture.componentRef.setInput('heading', 'ERP migration progress');
    await fixture.whenStable();
    expect((fixture.nativeElement as HTMLElement).querySelector('button.sign-out')).toBeNull();
  });
});
```
- `web/src/app/core/api/bearer-token-interceptor.spec.ts`:
```ts
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';

import { AuthMode, PORTAL_CONFIG, PORTAL_CONFIG_VALUES } from '../config/portal-config';
import { Router, provideRouter } from '@angular/router';

import { SessionStore } from '../session/session-store';
import { bearerTokenInterceptor } from './bearer-token-interceptor';

const API = 'https://api.example.test';

function setUp(authMode: AuthMode, idToken?: string): { http: HttpClient; controller: HttpTestingController } {
  TestBed.configureTestingModule({
    providers: [
      provideHttpClient(withInterceptors([bearerTokenInterceptor])),
      provideHttpClientTesting(),
      provideRouter([]),
      { provide: PORTAL_CONFIG, useValue: { ...PORTAL_CONFIG_VALUES, authMode, apiBaseUrl: API } },
    ],
  });
  TestBed.inject(SessionStore).setIdToken(idToken);
  return { http: TestBed.inject(HttpClient), controller: TestBed.inject(HttpTestingController) };
}

describe('bearerTokenInterceptor', () => {
  it('sends the ID token to our API in cognito mode', async () => {
    const { http, controller } = setUp('cognito', 'header.payload.signature');
    const response = firstValueFrom(http.get(`${API}/summary`));
    const request = controller.expectOne(`${API}/summary`);
    expect(request.request.headers.get('Authorization')).toBe('Bearer header.payload.signature');
    request.flush({});
    await response;
  });

  it('sends no token in AUTH_MODE=none, with no token, or to another host', () => {
    const { http, controller } = setUp('none', 'header.payload.signature');
    http.get(`${API}/summary`).subscribe();
    expect(controller.expectOne(`${API}/summary`).request.headers.has('Authorization')).toBe(false);

    TestBed.resetTestingModule();
    const cognitoNoToken = setUp('cognito');
    cognitoNoToken.http.get(`${API}/summary`).subscribe();
    expect(cognitoNoToken.controller.expectOne(`${API}/summary`).request.headers.has('Authorization')).toBe(false);

    TestBed.resetTestingModule();
    const otherHost = setUp('cognito', 'header.payload.signature');
    otherHost.http.get('https://elsewhere.example.test/data').subscribe();
    expect(otherHost.controller.expectOne('https://elsewhere.example.test/data').request.headers.has('Authorization')).toBe(false);
  });

  it('on a 401 in cognito mode, forgets the token and sends the user to sign in again', async () => {
    const { http, controller } = setUp('cognito', 'header.payload.signature');
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    const response = firstValueFrom(http.get(`${API}/summary`));
    controller.expectOne(`${API}/summary`).flush({ error: 'unauthorized', detail: 'Token expired.' }, { status: 401, statusText: 'Unauthorized' });
    await expect(response).rejects.toMatchObject({ status: 401 });
    expect(TestBed.inject(SessionStore).idToken()).toBeUndefined();
    expect(navigate).toHaveBeenCalledWith(['/sign-in'], { queryParams: { reason: 'expired' } });
  });
});
```
- [ ] **Step 2: Run them**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/features/auth/sign-in-page.spec.ts --include src/app/shared/layout --include src/app/core/api/bearer-token-interceptor.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: `Tests  4 failed | 7 passed (11)`, with `AssertionError: expected 'header.payload.signature' to be undefined`, `AssertionError: expected undefined to be 'Sign in' // Object.is equality`, `AssertionError: expected 'ERP migration progressSign inSyntheti…' to contain 'Your session has expired. Sign in aga…'` and `AssertionError: expected undefined to be 'Sign out' // Object.is equality`.
- [ ] **Step 3: Implement.** Replace:
- `web/src/app/features/auth/sign-in-page.ts`:
```ts
import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AtButton } from '@amalitechnpm/at-design-system/angular';

import { PORTAL_CONFIG } from '../../core/config/portal-config';
import { roleLabel } from '../../core/format/format';
import { Scope } from '../../core/models';
import { CognitoSession } from '../../core/session/cognito-session';
import { DEMO_SCOPES, SessionStore } from '../../core/session/session-store';
import { AppHeader } from '../../shared/layout/app-header/app-header';
import { APPROVER_REQUIRED_REASON } from './approver-guard';

/** Set by the bearer-token interceptor when the API answers 401. */
export const SESSION_EXPIRED_REASON = 'expired';
import { RoleSwitcher } from './role-switcher/role-switcher';

/**
 * Sign-in. AUTH_MODE=none: choose a demo user (mock role switcher).
 * AUTH_MODE=cognito: Cognito managed login (authorization code + PKCE); the role and entities come from the ID token.
 */
@Component({
  selector: 'app-sign-in-page',
  imports: [RouterLink, AtButton, AppHeader, RoleSwitcher],
  templateUrl: './sign-in-page.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SignInPage {
  /** From the query string, e.g. ?reason=approver when the approver guard sent the user here. */
  readonly reason = input<string>();

  private readonly session = inject(SessionStore);
  private readonly router = inject(Router);

  protected readonly demoMode = inject(PORTAL_CONFIG).authMode === 'none';
  /** Only in cognito mode: the OIDC library is not provided in AUTH_MODE=none. */
  private readonly cognitoSession = this.demoMode ? undefined : inject(CognitoSession);
  protected readonly demoScopes = DEMO_SCOPES;
  protected readonly currentUserId = computed(() => this.session.scope().user_id);
  protected readonly signedInAs = computed(() => roleLabel(this.session.role()));
  protected readonly approverRequired = computed(() => this.reason() === APPROVER_REQUIRED_REASON);
  protected readonly sessionExpired = computed(() => this.reason() === SESSION_EXPIRED_REASON);

  protected signInWithCognito(): void {
    this.cognitoSession?.signIn();
  }

  protected signInAs(scope: Scope): void {
    this.session.setScope(scope);
    void this.router.navigateByUrl('/');
  }
}
```
- `web/src/app/features/auth/sign-in-page.html`:
```html
<app-header heading="ERP migration progress" subheading="Sign in" [signedInAs]="signedInAs()" [showShare]="false" />

<main class="portal-page">
  <a class="portal-back-link" routerLink="/">Back to the dashboard</a>

  <section class="portal-card" aria-labelledby="sign-in-heading">
    <h2 id="sign-in-heading">Sign in</h2>

    @if (approverRequired()) {
      <p role="alert">Only a delivery lead can approve a status pack. Sign in as a delivery lead to continue.</p>
    }

    @if (sessionExpired()) {
      <p role="alert">Your session has expired. Sign in again to continue.</p>
    }

    @if (demoMode) {
      <p>Demo mode (AUTH_MODE=none): choose who the portal acts as. The mock API filters what each user sees by their scope.</p>
      <app-role-switcher [scopes]="demoScopes" [currentUserId]="currentUserId()" (pick)="signInAs($event)" />
    } @else {
      <p>Sign in with your portal account. What you can see is set by your role and entities, from your sign-in.</p>
      <div class="portal-actions">
        <at-button variant="solid" color="brand-dark-blue" (atClick)="signInWithCognito()">Sign in</at-button>
      </div>
    }
  </section>
</main>
```
- `web/src/app/shared/layout/app-header/app-header.ts`:
```ts
import { ChangeDetectionStrategy, Component, computed, inject, input, output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AtButton } from '@amalitechnpm/at-design-system/angular';

import { PORTAL_CONFIG } from '../../../core/config/portal-config';
import { CognitoSession } from '../../../core/session/cognito-session';
import { SessionStore } from '../../../core/session/session-store';

@Component({
  selector: 'app-header',
  imports: [RouterLink, AtButton],
  templateUrl: './app-header.html',
  styleUrl: './app-header.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppHeader {
  readonly heading = input.required<string>();
  readonly subheading = input<string>();
  readonly dataNotice = input<string>();
  readonly signedInAs = input<string>();
  readonly shareStatus = input<string>();
  readonly showShare = input(true);
  /** Where "Switch user" goes; no link when undefined. */
  readonly switchUserLink = input<string>();
  readonly share = output<void>();

  private readonly cognitoMode = inject(PORTAL_CONFIG).authMode === 'cognito';
  /** Only in cognito mode: the OIDC library is not provided in AUTH_MODE=none. */
  private readonly cognitoSession = this.cognitoMode ? inject(CognitoSession) : undefined;
  private readonly session = inject(SessionStore);
  protected readonly canSignOut = computed(() => this.cognitoMode && this.session.signedIn());

  protected signOut(): void {
    this.cognitoSession?.signOut();
  }
}
```
- `web/src/app/shared/layout/app-header/app-header.html`:
```html
<header class="header">
  <div class="identity">
    <svg class="logo" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <rect x="2" y="4" width="20" height="3.5" rx="1" />
      <rect x="2" y="10.25" width="20" height="3.5" rx="1" />
      <rect x="2" y="16.5" width="20" height="3.5" rx="1" />
    </svg>
    <div class="titles">
      <h1 class="heading">{{ heading() }}</h1>
      @if (subheading()) {
        <p class="subheading">{{ subheading() }}</p>
      }
    </div>
  </div>

  <div class="actions">
    <span class="data-pill" [attr.title]="dataNotice()">Synthetic data</span>
    <p class="notice">Every figure is derived from the programme artefacts</p>
    @if (signedInAs()) {
      <p class="signed-in">Signed in as <strong>{{ signedInAs() }}</strong></p>
    }
    @if (canSignOut()) {
      <button type="button" class="sign-out" (click)="signOut()">Sign out</button>
    } @else if (switchUserLink(); as link) {
      <a class="switch-user" [routerLink]="link">Switch user</a>
    }
    @if (showShare()) {
      <at-button variant="solid" color="brand-dark-blue" (atClick)="share.emit()">Share this view</at-button>
      <span class="visually-hidden" aria-live="polite">{{ shareStatus() }}</span>
    }
  </div>
</header>
```
- `web/src/app/shared/layout/app-header/app-header.scss`:
```scss
:host {
  display: block;
  background: var(--portal-color-surface);
  border-bottom: 1px solid var(--portal-color-border);
}

.header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--portal-space-3) var(--portal-space-5);
  max-width: var(--portal-page-max-width);
  margin: 0 auto;
  padding: var(--portal-space-4) var(--portal-space-6);
}

.identity {
  display: flex;
  align-items: center;
  gap: var(--portal-space-4);
  min-width: 0;
}

.logo {
  flex: none;
  width: 1.75rem;
  height: 1.75rem;
  fill: var(--portal-color-brand);
}

.titles {
  min-width: 0;
}

.heading {
  color: var(--portal-color-primary);
  font-size: var(--portal-font-size-xl);
  font-weight: 600;
  line-height: 1.2;
}

.subheading {
  color: var(--portal-color-text-muted);
  font-size: var(--portal-font-size-sm);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--portal-space-2) var(--portal-space-4);
  min-width: 0;
}

.data-pill {
  padding: var(--portal-space-1) var(--portal-space-2);
  border-radius: var(--portal-radius-pill);
  background: var(--portal-tone-info-bg);
  color: var(--portal-tone-info-text);
  font-size: var(--portal-font-size-xs);
  font-weight: 500;
}

.notice,
.signed-in {
  color: var(--portal-color-text-muted);
  font-size: var(--portal-font-size-sm);
}

.switch-user,
.sign-out {
  display: inline-flex;
  align-items: center;
  min-height: var(--portal-control-min-height);
  color: var(--portal-color-primary);
  font-size: var(--portal-font-size-sm);
  font-weight: 500;
}

at-button {
  min-height: var(--portal-control-min-height);
}

@media (max-width: 48rem) {
  .header {
    padding: var(--portal-space-3) var(--portal-space-4);
  }

  .notice {
    display: none;
  }
}

.sign-out {
  padding: 0;
  border: 0;
  background: none;
  cursor: pointer;
}
```
- `web/src/app/core/api/bearer-token-interceptor.ts`:
```ts
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { PORTAL_CONFIG } from '../config/portal-config';
import { SessionStore } from '../session/session-store';

const HTTP_UNAUTHORIZED = 401;
/** Must match SESSION_EXPIRED_REASON in features/auth/sign-in-page.ts. */
const SESSION_EXPIRED_REASON = 'expired';

/**
 * Adds `Authorization: Bearer <ID token>` to calls to our API when AUTH_MODE is 'cognito' and a token exists.
 * API Gateway's JWT authorizer checks it; the server builds the scope from it (the client never sends scope).
 * A 401 means the token is gone or expired: forget it and send the user to sign in again. Never logs the token.
 */
export const bearerTokenInterceptor: HttpInterceptorFn = (request, next) => {
  const config = inject(PORTAL_CONFIG);
  const session = inject(SessionStore);
  const router = inject(Router);
  const idToken = session.idToken();
  const toOurApi = request.url.startsWith(config.apiBaseUrl);
  if (config.authMode !== 'cognito' || !toOurApi) return next(request);
  const sent = idToken ? request.clone({ setHeaders: { Authorization: `Bearer ${idToken}` } }) : request;
  return next(sent).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse && error.status === HTTP_UNAUTHORIZED) {
        session.clear();
        void router.navigate(['/sign-in'], { queryParams: { reason: SESSION_EXPIRED_REASON } });
      }
      return throwError(() => error);
    }),
  );
};
```
- [ ] **Step 4: Run, suite, build, commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/features/auth/sign-in-page.spec.ts --include src/app/shared/layout --include src/app/core/api/bearer-token-interceptor.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
(cd web && yarn build 2>&1 | grep -E "ERROR|WARN|bundle generation complete")
git add web/src/app/features/auth web/src/app/shared/layout web/src/app/core/api/bearer-token-interceptor.ts web/src/app/core/api/bearer-token-interceptor.spec.ts
git commit -m "Sign in and out with Cognito; an expired token returns the user to sign-in"
```
Expected: `Test Files  3 passed (3)`, `Tests  11 passed (11)`; the suite at **start + 3 files, + 14 tests** (dry-run: `Test Files  38 passed (38)`, `Tests  121 passed (121)`); the build prints `Application bundle generation complete.` and no `WARN`.

**Task done when:** the suite is at start + 14; `yarn start` (no config file) still shows the role switcher and no "Sign out".

### Task 5: Sign-in end to end (verify in AWS; not dry-run)
Needs: M3* (AuthStack) and A2 (test users) deployed, Y1's JWT authorizer, M4 writing the `cognito` block (spec §1). The **D2 12:00 go/no-go** is decided on this task. Passwords come from Abdul out of band; never write them anywhere.

- [ ] **Step 1: Config.** `curl -s https://<cf>/portal-config.json` → `"authMode": "cognito"` and a `cognito` block with `authority`, `clientId`, `domain`.
- [ ] **Step 2: Signed out.** Open `https://<cf>/` in a private window. Expected: redirected to `/sign-in`, one "Sign in" button.
- [ ] **Step 3: Sign in as the E4 entity lead** (`demo-entity-lead-e4`, A2). Click Sign in → the managed login page (URL on `<prefix>.auth.eu-west-1.amazoncognito.com`, with `code_challenge_method=S256`) → sign in. Expected: back on the dashboard; header "Signed in as Entity lead" and "Sign out"; **one entity row, Entity 4**; KPI 19%; Network: `GET /api/summary` has `Authorization: Bearer eyJ…` and answers 200.
- [ ] **Step 4: Q11.** Click "What is blocking cutover for entity 2?". Expected: `POST /api/ask` → 403; "You can see E4 only. E2 is outside your access." (F3b).
- [ ] **Step 5: Sign out.** Click Sign out. Expected: a short visit to Cognito's `/logout`, then the portal's sign-in page; DevTools → Application: Local Storage empty, Session Storage without tokens.
- [ ] **Step 6: The CFO and the delivery lead.** Sign in as `demo-cfo`: four entity rows, 58%. As `demo-delivery-lead`: `/approve/<run>` shows the approve controls (F5).
- [ ] **Step 7: Record the go/no-go.** Ledger: `Task 5: Cognito go — <date time> — E4 lead sees E4 only, Q11 refused` or `no-go — <what failed>`. On no-go, Michael sets `"authMode": "none"` in `portal-config.json` (no rebuild) and [[Deploy and demo checks]] applies (say so in `HANDOFF.md`).

**Task done when:** Steps 1–6 match and the go/no-go line is in the ledger and posted to Patrick.

### Task 6: `HANDOFF.md`, then PR (after Clement's OK)
- [ ] **Step 1:** In `HANDOFF.md` under `## What's real`, add:
```markdown
- **Cognito sign-in** (the one target slice, D-015): managed login with authorization code + PKCE (`angular-auth-oidc-client`); the portal sends the ID token, and the API builds the scope from its group and `custom:entity_ids`. Turned on per deployment by `/portal-config.json` (`"authMode": "cognito"`); `"none"` falls back to the demo users.
```
  `git add HANDOFF.md && git commit -m "HANDOFF: Cognito sign-in"`. Expected: `1 file changed`.
- [ ] **Step 1:** Work through the Review Focus by hand; write each result in the ledger.
- [ ] **Step 2:** `git diff develop --stat` lists only the files this plan names.
- [ ] **Step 3:** Fresh review of the diff against [[F3a - Cognito sign-in - spec]] (another person, or an agent with no prior context); fix critical and important findings test-first; list minor ones in the PR.
- [ ] **Step 4 (with Clement's OK only):** `git push -u origin feature/web-cognito-sign-in`; open the PR to `develop` titled "Front end: Cognito sign-in with managed login and PKCE (F3a)". Body: what changed, the suite count (start + 14), the Task 5 go/no-go line, the `Ruling:` lines, deferred minors. Tell Mildred which of her files changed, and Michael the `portal-config.json` `cognito` block. No attribution lines.
- [ ] **Step 5:** [[Build order]] row F3: `in review (PR #nn)`, then `merged` when Patrick merges.

**Task done when:** the PR is open to `develop`, Jenkins' front-end build is green, and [[Build order]] shows `in review (PR #nn)`.

## Never
- Compute a KPI, a status or a date in the browser; show what the API returns.
- Send scope (role, entities, tenant) in a request body, query string or header.
- Log, print or store a token yourself.
- Add a `package-lock.json`, or change `yarn.lock` other than with `yarn add`.
- Commit the npm token, a password or any secret.
- Push to `develop` or `main`, or add attribution lines.
- Put a pool ID, client ID, domain or test password in the source, the repo or the vault.
- Send the access token instead of the ID token, or read scope from anything but the token.
- Raise the library's log level above `Warn` in a commit.

## Done means
- [ ] **Tests:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` → start + 14 (dry-run: `Tests  121 passed (121)`). *Verify:* run it.
- [ ] **One lock file:** `git diff develop --stat -- web/yarn.lock` shows only additions (the library and `rfc4648`); `ls web/package-lock.json` fails. *Verify:* run both.
- [ ] **Build:** `(cd web && yarn build)` ends with `Application bundle generation complete.` *Verify:* run it.
- [ ] **`AUTH_MODE=none` unchanged:** `yarn start` (no config) shows the role switcher, no "Sign out". *Verify:* by hand.
- [ ] **Live (verify in AWS):** Task 5 Steps 1–6 as written; the go/no-go line in the ledger and sent to Patrick.
- [ ] **HANDOFF:** `grep -c "Cognito sign-in" HANDOFF.md` → at least `1`.
- [ ] **PR:** open to `develop` titled "Front end: Cognito sign-in with managed login and PKCE (F3a)"; [[Build order]] row F3 updated. *Verify:* `gh pr list --head feature/web-cognito-sign-in`.

Related: [[F3a - Cognito sign-in - spec]], [[F3b - Role views and the 403 refusal - spec]], [[Build order]], [[How to execute a plan]]
