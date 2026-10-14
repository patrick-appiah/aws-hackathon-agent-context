---
tags: [build, spec, area/devops]
id: M3b
owner: Michael
status: ready
updated: 2026-10-14
---
# M3b: AuthStack, Cognito sign-in with role and entity claims (spec)
> **Split from M3** (the lead's rule). M3b is Cognito, the one target slice (D-015); [[M3a - GuardrailStack - spec]] is the Guardrail. Each is deployable and mergeable on its own. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after [[M2 - App, DataStack and LedgerStack - spec]] (and ideally M3a) is merged.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] (`06 Workstreams/`): the architecture, the code already built, the contracts and the rules (§7).
3. [[Michael - DevOps]] (step 5, `AuthStack`), [[Abdul - evals, Cognito, docs]] §5 (groups, attributes, test users), [[Linus - API, identity, blocker-analyst]] §1 (how `auth/scope.py` *(new)* reads the claims), [[Clement - front end]] (managed login + PKCE) and [[Yaw - DevOps]] (the JWT authorizer).
4. [[M2 - App, DataStack and LedgerStack - spec]]: the CDK patterns this item follows.
5. [[Build order]]: M3b depends on M2 and A2 (Abdul's users list).
6. `01 Decisions/`: [[2026-10-13 Scope from the token, enforced twice]], [[2026-10-13 POC plus one target slice, target as 90-day roadmap]], [[2026-10-13 Team are admins, workload roles least-privilege]]; `05 Workflow/`: [[Deploy and demo checks]], [[Synthetic data rules]].

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Michael (owner), Abdul (users) or Linus (claims). Never invent a name, a shape or a rule.

## 1. Intent
**What:** an `AuthStack` *(new)* with:
1. A **Cognito user pool**: admin-created users only, username sign-in, custom string attributes `tenant_id` and `entity_ids`, no account recovery (no e-mail), Essentials feature plan (managed login, new version), destroyed with the stack.
2. **Four groups**, one per role, taken from `tools.models.Role` (`cfo`, `sponsor`, `delivery_lead`, `entity_lead`).
3. A **portal app client**: public (no secret, PKCE), authorization-code flow only, scopes `openid` + `profile`, callback and logout `http://localhost:4200` (WebStack adds the CloudFront URL, M4a), ID token valid one hour, user-existence errors hidden, and **users may not write their own custom attributes**.
4. A **managed login domain** `<prefix>-erp-portal-<account id>` (new managed login, with Cognito's default branding).
5. The **demo users** from Abdul's list: one per role plus a second entity lead (E2), each in exactly one group, with `custom:tenant_id = t-01` and `custom:entity_ids` (`*`, `E4` or `E2`). No passwords in code: they are set out of band.
6. **Outputs** `UserPoolId`, `UserPoolClientId`, `IssuerUrl`, `ManagedLoginUrl`; attributes `user_pool`, `user_pool_client`, `issuer_url`, `managed_login_domain` for Yaw's JWT authorizer and Michael's WebStack.

**Why:**
- D-015: Cognito sign-in with entity scope is the one target slice. D-010: scope comes from the token; `auth/scope.py` (Linus) turns `cognito:groups`, `custom:tenant_id` and `custom:entity_ids` into a `Scope`.
- **The ID token** carries the custom claims (the access token doesn't), so the portal sends it and Yaw's authorizer uses the app client ID as audience.
- **The write restriction is a security control:** by default a Cognito app client may write every attribute, so a signed-in E4 lead could call `UpdateUserAttributes` and set `custom:entity_ids` to `*`. Restricting the client's write attributes to `name` closes that.

**Success means:**
- `uv run --locked pytest` → **237 passed** (230 after M3a + 7 new), `TOTAL` 96%. If M3a isn't merged yet: 231.
- `cd infra && npx cdk synth -q` succeeds with no AWS credentials.
- **Verify in AWS:** the E4 lead's ID token has `cognito:groups = ["entity_lead"]`, `custom:entity_ids = "E4"`, `custom:tenant_id = "t-01"`, `aud = <UserPoolClientId>`; writing `custom:entity_ids` with that user's access token fails with `NotAuthorizedException`; the managed login page answers `200`.

**Assumptions** (reconcile with the named owner before the PR):
- **Abdul (A2):** the usernames `cfo-user`, `sponsor-user`, `delivery-lead-user`, `e4-lead-user`, `e2-lead-user` match his `HANDOFF.md` list. If his list differs, change only `COGNITO_DEMO_USERS` in `infra/constants.py` *(new)*.
- **Linus (L1):** `scope_from_claims` reads `cognito:groups` (exactly one), `custom:tenant_id` and `custom:entity_ids` (comma-separated, `*` = all), as his brief says.
- **Yaw (Y1):** builds the JWT authorizer from `auth.issuer_url` and `auth.user_pool_client.user_pool_client_id` ([[Y1 - ApiStack - spec]]).
- **Clement (F3):** signs in with managed login + PKCE using `UserPoolClientId` and `ManagedLoginUrl`, and sends the ID token.
- **Patrick:** shares the demo passwords privately; they never appear in the repo, the vault or Slack.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Group names | `typing.get_args(tools.models.Role)`: the same four strings `Scope.role` accepts | A second list in `infra/` (drifts from the model) |
| Custom attributes | `tenant_id`, `entity_ids`, both `StringAttribute(mutable=True)`; users can't write them (client `WriteAttributes = ["name"]`); admins can | Immutable attributes (an entity change would need a new user); the default client (users could widen their own scope) |
| Feature plan / login UI | `FeaturePlan.ESSENTIALS` + `ManagedLoginVersion.NEWER_MANAGED_LOGIN` + `CfnManagedLoginBranding(use_cognito_provided_values=True)` | Lite + classic hosted UI (the brief says managed login); custom branding (time) |
| Client type | Public client, no secret, authorization code only (PKCE is enforced by the portal's OIDC library) | Implicit flow (tokens in the URL); a secret in a browser app |
| Auth flows | `ALLOW_USER_SRP_AUTH` (password sign-in), `ALLOW_ADMIN_USER_PASSWORD_AUTH` (lets an admin with IAM rights fetch a token for the claims check), refresh | `ALLOW_USER_PASSWORD_AUTH` (lets anyone holding a password skip SRP without IAM) |
| Callback URLs | `http://localhost:4200` here; the CloudFront URL is added by M4a's custom resource | Adding CloudFront here (AuthStack would need WebStack, which needs the API, which needs AuthStack: a cycle) |
| Domain prefix | `<prefix>-erp-portal-<account id>` | A fixed prefix (Cognito domain prefixes are unique across all accounts in a region) |
| Users in CDK | `CfnUserPoolUser` (`MessageAction: SUPPRESS`) + `CfnUserPoolUserToGroupAttachment` | Creating users by hand (clean-deploy gate); passwords in CDK (a secret in the template) |
| Passwords | `aws cognito-idp admin-set-user-password --permanent`, typed at a hidden prompt | Temporary passwords by e-mail (no e-mail for synthetic users) |
| Token lifetime | ID token 1 hour (`ID_TOKEN_VALIDITY_HOURS`) | The 1-hour default left implicit (a magic default) |

## 3. Exact shapes
**`infra/constants.py` additions:** `from dataclasses import dataclass`, `from tools.constants import ALL_ENTITIES_WILDCARD`, and:
| Name | Value |
|---|---|
| `USER_POOL_BASE_NAME` | `"erp-portal-users"` |
| `MANAGED_LOGIN_DOMAIN_BASE` | `"erp-portal"` |
| `TENANT_ID_ATTRIBUTE` / `ENTITY_IDS_ATTRIBUTE` | `"tenant_id"` / `"entity_ids"` |
| `CUSTOM_ATTRIBUTE_PREFIX` | `"custom:"` |
| `LOCAL_PORTAL_URL` | `"http://localhost:4200"` |
| `ID_TOKEN_VALIDITY_HOURS` | `1` |
| `DemoUser` | frozen dataclass `username: str`, `group: str`, `entity_ids: str` |
| `COGNITO_DEMO_USERS` | `cfo-user`/`cfo`/`*`, `sponsor-user`/`sponsor`/`*`, `delivery-lead-user`/`delivery_lead`/`*`, `e4-lead-user`/`entity_lead`/`E4`, `e2-lead-user`/`entity_lead`/`E2` |

**`infra/stacks/auth_stack.py` *(new)*:** `AuthStack(scope, construct_id, *, prefix: str, **kwargs)`.
- Attributes: `user_pool: cognito.UserPool`, `user_pool_client: cognito.UserPoolClient`, `managed_login_domain: cognito.UserPoolDomain`, `issuer_url: str` (`https://cognito-idp.eu-west-1.amazonaws.com/<pool id>`).
- Outputs: `UserPoolId`, `UserPoolClientId`, `IssuerUrl`, `ManagedLoginUrl` (`https://<prefix>-erp-portal-<account>.auth.eu-west-1.amazoncognito.com`).
- Synthesised client (dry-run): `AllowedOAuthFlows: ["code"]`, `AllowedOAuthFlowsUserPoolClient: true`, `AllowedOAuthScopes: ["openid", "profile"]`, `CallbackURLs` / `LogoutURLs: ["http://localhost:4200"]`, `ExplicitAuthFlows: ["ALLOW_ADMIN_USER_PASSWORD_AUTH", "ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]`, `GenerateSecret: false`, `IdTokenValidity: 60` (minutes), `PreventUserExistenceErrors: "ENABLED"`, `SupportedIdentityProviders: ["COGNITO"]`, `WriteAttributes: ["name"]`.

**`infra/app.py` *(new)*:** `PortalStacks.auth: AuthStack`, built fourth (after `guardrail`), stack name `<prefix>-AuthStack`.

## 4. Tests (`tests/infra/stacks/test_auth_stack.py` *(new)*, 7 tests)
- The pool: admin-only creation, `ESSENTIALS` tier, both custom string attributes, `DeletionPolicy: Delete`.
- One group per `Role` value.
- The portal client exactly as §3 (public, code flow, scopes, localhost URLs, `WriteAttributes: ["name"]`, auth flows).
- Managed login version 2 and Cognito-provided branding.
- Every demo user exists with `MessageAction: SUPPRESS`, `custom:tenant_id = t-01`, its `custom:entity_ids`, one group attachment, and **no password property**.
- The demo users cover every role, and the entity leads are exactly E2 and E4.
- The four outputs exist.

## 5. Out of scope
- The CloudFront callback URL and the portal's runtime config (M4a).
- `auth/scope.py` (Linus, L1), the JWT authorizer (Yaw, Y1), the sign-in UI (Clement, F3).
- MFA, federation and Verified Permissions (the 90-day roadmap, `docs/ROADMAP.md`).
- Writing the users list into `HANDOFF.md` (Abdul).

Related: [[M3b - AuthStack - plan]], [[Build order]], [[Michael - DevOps]]
