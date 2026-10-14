---
tags: [build, spec, area/frontend]
id: F3a
owner: Clement
status: ready
updated: 2026-10-14
---
# F3a: Cognito sign-in with managed login, authorization code + PKCE (spec)
> **The one target slice that is built (D-015): the token decides what each role sees.** F3 in [[Build order]] is split: **F3a** (this) signs the user in and sends the ID token; **F3b** ([[F3b - Role views and the 403 refusal - spec]]) shows role views and the 403 refusal. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after F2 is merged (it extends F2's runtime config); the live steps need M3* (AuthStack), A2 (test users) and Y1 (JWT authorizer).

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Clement - front end]].
3. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
4. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
5. [[F2 - Click a number and the live API - spec]] (Mildred): `/portal-config.json` and `loadPortalConfig`, which this item extends with a `cognito` block.
6. [[A2 - Cognito groups, claims and test users - spec]] (Abdul) and [[Michael - DevOps]] (AuthStack): groups, claims, the app client, the domain.
7. [[L1 - Scope from the token and the summary handler - spec]] (Linus): the same claim rules on the server (`scope_from_claims`).
8. `01 Decisions/` [[2026-10-13 Scope from the token, enforced twice]] (D-010), [[2026-10-13 POC plus one target slice, target as 90-day roadmap]] (D-015); [[Deploy and demo checks]] (the D2 12:00 Cognito go/no-go).
9. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. **Sign-in** with Cognito **managed login, authorization code + PKCE**, through `angular-auth-oidc-client` **22.0.1** (supports Angular ≥ 20; added with `yarn add`). Only when the deployment's `portal-config.json` says `"authMode": "cognito"`; `AUTH_MODE=none` keeps the role switcher.
2. **The session:** after the redirect back, the ID token and the role and entities it carries (`cognito:groups`, `custom:tenant_id`, `custom:entity_ids`, `sub`) go into `SessionStore`; the existing `bearerTokenInterceptor` sends the **ID token** as `Authorization: Bearer` to `/api/*` (custom claims are only in the ID token). Silent renewal with refresh tokens keeps it current.
3. **Guards and pages:** every page but sign-in needs a signed-in user in cognito mode (`signedInGuard`); the sign-in page has one "Sign in" button; the header has "Sign out" (local sign-out + Cognito's `/logout`).
4. **An expired token** (any `/api` 401) clears the session and returns to sign-in with "Your session has expired. Sign in again to continue."
5. **Settings** come from `portal-config.json` (`cognito.authority`, `cognito.clientId`, `cognito.domain`); `authMode: cognito` without them fails at start-up.

**Why:** the brief ("real Cognito sign-in, so the token decides what each role can see"), EVALS Q11 end to end, D-015's one target slice, and the D2 12:00 go/no-go. The scope stays server-side (D-010): the UI only displays what the token says.

**Success means:**
- Unit: the OIDC settings are code flow + PKCE + refresh tokens with the right redirect and logout URLs; claims → scope with exactly one group; the session fills after `checkAuth`; the guard sends a signed-out user to `/sign-in`; a 401 clears the token and navigates to `/sign-in?reason=expired`; the header offers "Sign out" only when signed in with Cognito.
- `yarn test`: +14 tests on the start state; `yarn build` green; `yarn.lock` changed only by the library and its one dependency (`rfc4648`).
- **In AWS (verify there):** signing in as the E4 lead shows only E4; requests to `/api/*` carry the ID token; asking about E2 is refused (F3b); signing out lands on the managed login sign-out and back at the portal signed out; nothing in `localStorage`.

**Assumptions (reconcile with the owners):**
- **M3* (Michael, AuthStack):** the app client is public (no secret), allows the **authorization code** grant with scopes `openid email profile`, issues refresh tokens, and lists the callback URL **and** the sign-out URL `https://<CloudFront domain>/` (with the trailing slash). The managed login domain is a stack output.
- **M4 (Michael, WebStack)** writes the `cognito` block into `/portal-config.json`:
```json
{
  "dataSource": "http",
  "authMode": "cognito",
  "apiBaseUrl": "/api",
  "cognito": {
    "authority": "https://cognito-idp.eu-west-1.amazonaws.com/<user pool ID>",
    "clientId": "<app client ID>",
    "domain": "https://<prefix>.auth.eu-west-1.amazoncognito.com"
  }
}
```
- **A2 (Abdul):** one Cognito group per user (`cfo`, `sponsor`, `delivery_lead`, `entity_lead`); `custom:entity_ids` like `E4`, `E2,E4` or `*`; `custom:tenant_id` `t-01`.
- **Y1 (Yaw):** the JWT authorizer's audience is the app client ID, so the **ID token** (whose `aud` is the client ID) is accepted.
- **Mildred** agrees the `cognito` block in her `portal-config.ts` and the guard on her routes (`app.routes.ts`).

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Library or hand-rolled | **`angular-auth-oidc-client` 22.0.1**: certified OIDC client, code flow + PKCE by default, `state`/`nonce` checks, token validation against the pool's JWKS, refresh-token renewal; one small dependency (`rfc4648`) | Hand-rolling PKCE, state, token exchange, JWKS validation and renewal (about 300 lines of security code to own and test in two days); Amplify (large, pulls in much more than auth) |
| Token storage | The library's default, **`sessionStorage`** (per tab, gone when the tab closes); our code keeps the ID token only in memory (`SessionStore`) | `localStorage` (the brief forbids it beyond what the library needs); memory only (every reload would bounce through managed login) |
| Which token goes to the API | The **ID token** (custom claims live only there; the authorizer's audience is the client ID) | The access token (no `custom:` claims) |
| Where settings come from | `portal-config.json` `cognito` block, validated at start-up | Hardcoded IDs (the clean-deploy check creates a new pool) |
| When the library loads | Only in cognito mode: `main.ts` adds `provideCognitoAuth(...)`; components inject `CognitoSession` only in cognito mode | Always providing it (would need dummy settings in `AUTH_MODE=none`) |
| Logout | `logoffLocal()`, clear the session, then Cognito's `/logout?client_id&logout_uri` (Cognito has no `end_session_endpoint` in its discovery document) | `logoff()` (fails without `end_session_endpoint`) |
| Library log level | `LogLevel.Warn`, so tokens never reach the console | Debug |
| A 401 | Clear and re-sign-in with a reason (`?reason=expired`) | Silent retry (could loop) |

## 3. The shapes
- `CognitoSettings {authority, clientId, domain}` and `PortalConfig.cognito?` in `core/config/portal-config.ts`.
- `scopeFromIdTokenClaims(claims: Record<string, unknown>): Scope | undefined` in `core/session/id-token-claims.ts` *(new)*.
- `cognitoOidcConfig(settings, origin): OpenIdConfiguration`, `cognitoLogoutUrl(settings, origin): string`, `class CognitoSession { start(); signIn(); signOut(leave?, origin?) }`, `provideCognitoAuth(settings): EnvironmentProviders` in `core/session/cognito-session.ts` *(new)*.
- `SessionStore.signedIn` (computed) and `SessionStore.clear()`.
- `signedInGuard: CanActivateFn` in `features/auth/signed-in-guard.ts` *(new)*, on `''`, `publish/:runId` and `approve/:runId`.
- `SESSION_EXPIRED_REASON = 'expired'` in `features/auth/sign-in-page.ts`.

## 4. Tests
`core/config/portal-config.spec.ts` +1; `core/session/id-token-claims.spec.ts` *(new)* 2; `core/session/cognito-session.spec.ts` *(new)* 4 (with a fake `OidcSecurityService`); `features/auth/signed-in-guard.spec.ts` *(new)* 3; `features/auth/sign-in-page.spec.ts` +1 (the placeholder test becomes the Sign in button); `shared/layout/app-header/app-header.spec.ts` +2; `core/api/bearer-token-interceptor.spec.ts` +1. Total +14. The real redirect, token exchange and renewal are the library's and are checked live (Task 5).

## 5. Out of scope
- The AuthStack, the users and the authorizer (M3*, A2, Y1). Federation with a client IdP (roadmap).
- The refusal wording and the role switcher (F3b).

Related: [[F3a - Cognito sign-in - plan]], [[F3b - Role views and the 403 refusal - spec]], [[Build order]], [[Clement - front end]]
