---
tags: [build, plan, area/devops]
id: M3b
owner: Michael
spec: "[[M3b - AuthStack - spec]]"
status: ready
updated: 2026-10-14
---
# M3b: AuthStack (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it. Deploying, setting passwords (Task 2) and pushing are outward-facing: ask Michael first. **This item touches security (sign-in and scope claims): any deviation from the spec is a stop-and-ask.**

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]]: the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[M3b - AuthStack - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger.
3. [[M2 - App, DataStack and LedgerStack - spec]] (the CDK patterns), [[Michael - DevOps]], [[Abdul - evals, Cognito, docs]] §5, [[Linus - API, identity, blocker-analyst]] §1.
4. [[2026-10-13 Scope from the token, enforced twice]] and [[Working with AI assistants]].

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Michael (or Abdul for users, Linus for claims).

**Goal:** an `AuthStack` with the Cognito pool, the four role groups, a public PKCE client for managed login that can't write its own claims, the managed login domain and the five demo users, unit-tested, synthesised without credentials, deployed, and checked with a real token.

**Architecture:** one new stack module, `infra/stacks/auth_stack.py` *(new)*, built by `build_stacks` after `GuardrailStack`. Groups come from `tools.models.Role`; the tenant from `config.DEFAULT_TENANT_ID`; the wildcard from `tools.constants.ALL_ENTITIES_WILDCARD`; deploy-time values from `infra/constants.py` *(new)*. Yaw's ApiStack and Michael's WebStack read the pool, client and domain as attributes.

**Tech stack:** Python 3.11, `aws-cdk-lib` 2.273+ (`aws_cognito`), CDK CLI 2.1144.0, pytest, uv; the AWS CLI for the out-of-band passwords and the token check.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your clone). **Branch:** `feature/infra-auth` from an up-to-date `develop`, **after M2 (and preferably M3a) is merged** ([[Build order]]).
- **Start state:** `uv run --locked pytest` → **230 passed**, `TOTAL` 96% (C1, M1, M2, M3a merged). Without M3a: **226 passed**; then every count below is 4 lower. Any other number: stop. (Dry-run: counts measured on `feature/api-and-spine-contracts` + M2 + M3a with this plan applied.)
- `eu-west-1` only (`config.DEFAULT_REGION`); Bedrock `eu.*` inference profiles only; synthetic data only (the demo users are role names, no person names); **no secrets anywhere: no passwords in code, the repo, the vault, Slack or your shell history.**
- Settings only in `config.py`; domain constants only in `tools/constants.py`; deploy-time constants only in `infra/constants.py`; descriptive names; **no single-character names**; no magic numbers or strings. The core (`tools/`) imports no boto3, Strands, adapters, config or os, and never imports `infra`.
- **`RemovalPolicy.DESTROY` on the pool** (users, groups, client and domain go with it). Outputs or attributes for every name another stack or person needs.
- Agents reach data only through `tools/agent_tools.py`; scope is never a tool argument; prompts only in `agents/prompts/<agent>.txt` (nothing here touches them).
- Never weaken a security rule (scope gate, create-once ledger, fail-closed critic, escaping) to pass a test. **Never widen the client's write attributes.**
- Tests in `tests/`, mirroring the code; `uv run --locked pytest` from the repo root; coverage must not drop (96%).
- Deploys are manual (D-018); CI builds and tests only. `export AWS_PROFILE=hackathon AWS_REGION=eu-west-1` before any `aws` or `cdk deploy` command.
- PR to `develop`; Patrick merges; never push to `develop` or `main`; **no `Co-Authored-By` and no "Generated with" lines**.
- Stay in DevOps's files: `infra/`, `tests/infra/` *(new)*.
- No layout or "meta" guard tests.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **A user can't widen their own scope (verify in AWS):** Task 2 Step 6 fails with `NotAuthorizedException`. This is the reason `WriteAttributes` is `["name"]`.
2. **The claims Linus reads are in the ID token:** `cognito:groups`, `custom:tenant_id`, `custom:entity_ids` (Task 2 Step 5). The access token does **not** carry the custom claims; tell Clement the portal sends the ID token.
3. **Abdul's list matches `COGNITO_DEMO_USERS`** (usernames, groups, entities). Write his OK in the ledger.
4. **No password in the template:** `grep -ci password infra/cdk.out/AuthStack.template.json` → `0` after synth (the pool's default `PasswordPolicy` keys don't count; if the count isn't 0, look at each hit: none may be a value).
5. **Managed login works for the localhost client before M4a (verify in AWS):** Task 2 Step 7 returns `200`. M4a later adds the CloudFront URL without changing anything else.

---

### Task 1: `AuthStack`: pool, groups, client, domain, demo users

**Files:**
- Modify: `infra/constants.py`, `infra/app.py` *(new)*
- Create: `infra/stacks/auth_stack.py`, `tests/infra/stacks/test_auth_stack.py` *(new)*

**Produces:** `infra.stacks.auth_stack.AuthStack(scope, construct_id, *, prefix: str, **kwargs)` with `.user_pool`, `.user_pool_client`, `.managed_login_domain`, `.issuer_url`; outputs `UserPoolId`, `UserPoolClientId`, `IssuerUrl`, `ManagedLoginUrl`; `PortalStacks.auth`; constants `USER_POOL_BASE_NAME`, `MANAGED_LOGIN_DOMAIN_BASE`, `TENANT_ID_ATTRIBUTE`, `ENTITY_IDS_ATTRIBUTE`, `CUSTOM_ATTRIBUTE_PREFIX`, `LOCAL_PORTAL_URL`, `ID_TOKEN_VALIDITY_HOURS`, `DemoUser`, `COGNITO_DEMO_USERS`. **Consumes:** `tools.models.Role`, `tools.constants.ALL_ENTITIES_WILDCARD`, `config.DEFAULT_TENANT_ID`, `infra.naming.physical_name`, `build_stacks` / `PortalStacks`, the `portal_stacks` fixture (M2). **Consumed by:** Yaw (Y1: `auth.issuer_url`, `auth.user_pool_client.user_pool_client_id`), Michael (M4a: `auth.user_pool`, `auth.user_pool_client`, `auth.managed_login_domain`), Clement (F3: the outputs).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync --locked && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/infra-auth
mkdir -p .superpowers && printf '# Ledger: M3b AuthStack\n' > .superpowers/ledger-M3b.md
cd infra && npm ci && cd ..
```
Expected: `230 passed`, `TOTAL ... 96%`.

- [ ] **Step 2: Write the failing tests.** Create `tests/infra/stacks/test_auth_stack.py`:
```python
"""AuthStack: a Cognito pool whose groups are the four roles, whose tokens carry tenant and entity claims that
users can't change, a public PKCE client for managed login, and the demo users (no passwords in code)."""
from typing import get_args

from aws_cdk.assertions import Match, Template

from infra.constants import COGNITO_DEMO_USERS, LOCAL_PORTAL_URL
from tools.models import Role


def _template(portal_stacks) -> Template:
    return Template.from_stack(portal_stacks.auth)


def test_the_pool_is_admin_only_essentials_and_destroyed_with_the_stack(portal_stacks):
    _template(portal_stacks).has_resource("AWS::Cognito::UserPool", {
        "DeletionPolicy": "Delete",
        "Properties": {
            "AdminCreateUserConfig": {"AllowAdminCreateUserOnly": True},
            "UserPoolTier": "ESSENTIALS",
            "Schema": Match.array_with([
                {"AttributeDataType": "String", "Mutable": True, "Name": "tenant_id"},
                {"AttributeDataType": "String", "Mutable": True, "Name": "entity_ids"}]),
        },
    })


def test_there_is_one_group_per_role(portal_stacks):
    template = _template(portal_stacks)
    roles = get_args(Role)
    template.resource_count_is("AWS::Cognito::UserPoolGroup", len(roles))
    for role in roles:
        template.has_resource_properties("AWS::Cognito::UserPoolGroup", {"GroupName": role})


def test_the_portal_client_is_public_code_flow_only_and_cannot_write_its_own_claims(portal_stacks):
    _template(portal_stacks).has_resource_properties("AWS::Cognito::UserPoolClient", {
        "GenerateSecret": False,
        "AllowedOAuthFlows": ["code"],
        "AllowedOAuthFlowsUserPoolClient": True,
        "AllowedOAuthScopes": ["openid", "profile"],
        "CallbackURLs": [LOCAL_PORTAL_URL],
        "LogoutURLs": [LOCAL_PORTAL_URL],
        "SupportedIdentityProviders": ["COGNITO"],
        "PreventUserExistenceErrors": "ENABLED",
        "WriteAttributes": ["name"],
        "ExplicitAuthFlows": ["ALLOW_ADMIN_USER_PASSWORD_AUTH", "ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"],
    })


def test_managed_login_is_the_new_version_with_cognito_branding(portal_stacks):
    template = _template(portal_stacks)
    template.has_resource_properties("AWS::Cognito::UserPoolDomain", {"ManagedLoginVersion": 2})
    template.has_resource_properties("AWS::Cognito::ManagedLoginBranding", {"UseCognitoProvidedValues": True})


def test_every_demo_user_exists_with_its_claims_and_one_group_and_no_password(portal_stacks):
    template = _template(portal_stacks)
    template.resource_count_is("AWS::Cognito::UserPoolUser", len(COGNITO_DEMO_USERS))
    template.resource_count_is("AWS::Cognito::UserPoolUserToGroupAttachment", len(COGNITO_DEMO_USERS))
    for demo_user in COGNITO_DEMO_USERS:
        template.has_resource_properties("AWS::Cognito::UserPoolUser", {
            "Username": demo_user.username,
            "MessageAction": "SUPPRESS",
            "UserAttributes": Match.array_with([{"Name": "custom:tenant_id", "Value": "t-01"},
                                                {"Name": "custom:entity_ids", "Value": demo_user.entity_ids}]),
        })
        template.has_resource_properties("AWS::Cognito::UserPoolUserToGroupAttachment",
                                         {"Username": demo_user.username, "GroupName": demo_user.group})
    assert "Password" not in str(template.find_resources("AWS::Cognito::UserPoolUser"))


def test_the_demo_users_cover_every_role_and_a_second_entity_lead():
    assert {demo_user.group for demo_user in COGNITO_DEMO_USERS} == set(get_args(Role))
    assert sorted(demo_user.entity_ids for demo_user in COGNITO_DEMO_USERS if demo_user.group == "entity_lead") == \
        ["E2", "E4"]


def test_the_ids_the_api_and_portal_need_are_outputs(portal_stacks):
    assert {"UserPoolId", "UserPoolClientId", "IssuerUrl", "ManagedLoginUrl"} <= \
        set(_template(portal_stacks).find_outputs("*"))
```

- [ ] **Step 3: Run them and watch them fail**
```bash
uv run --locked pytest tests/infra/stacks/test_auth_stack.py --no-cov 2>&1 | grep -E "^E |error"
```
Expected: `E   ImportError: cannot import name 'COGNITO_DEMO_USERS' from 'infra.constants'` and `1 error`.

- [ ] **Step 4: Add the constants.** In `infra/constants.py`:
  - change the imports at the top to:
    ```python
    from dataclasses import dataclass
    from pathlib import Path

    from aws_cdk import aws_logs as logs

    from config import DEFAULT_ARTEFACTS_URI
    from tools.constants import ALL_ENTITIES_WILDCARD
    ```
  - append:
    ```python

    # Cognito (AuthStack): the one target slice, sign-in with role and entity claims (D-015).
    USER_POOL_BASE_NAME = "erp-portal-users"
    MANAGED_LOGIN_DOMAIN_BASE = "erp-portal"          # + "-<account id>": Cognito domain prefixes are unique per region
    TENANT_ID_ATTRIBUTE = "tenant_id"                 # in tokens as custom:tenant_id (auth/scope.py, Linus)
    ENTITY_IDS_ATTRIBUTE = "entity_ids"               # in tokens as custom:entity_ids, comma-separated, "*" = all
    CUSTOM_ATTRIBUTE_PREFIX = "custom:"
    LOCAL_PORTAL_URL = "http://localhost:4200"        # `yarn start`; WebStack adds the CloudFront URL (M4a)
    ID_TOKEN_VALIDITY_HOURS = 1


    @dataclass(frozen=True)
    class DemoUser:
        """One synthetic sign-in per role (Abdul's list, HANDOFF.md). The password is set out of band, never here."""
        username: str
        group: str
        entity_ids: str


    COGNITO_DEMO_USERS = (
        DemoUser(username="cfo-user", group="cfo", entity_ids=ALL_ENTITIES_WILDCARD),
        DemoUser(username="sponsor-user", group="sponsor", entity_ids=ALL_ENTITIES_WILDCARD),
        DemoUser(username="delivery-lead-user", group="delivery_lead", entity_ids=ALL_ENTITIES_WILDCARD),
        DemoUser(username="e4-lead-user", group="entity_lead", entity_ids="E4"),
        DemoUser(username="e2-lead-user", group="entity_lead", entity_ids="E2"),
    )
    ```
  `infra/constants.py` may import `tools.constants` (the rule forbids the reverse: the core never imports `infra`).

- [ ] **Step 5: Implement the stack.** Create `infra/stacks/auth_stack.py`:
```python
"""AuthStack: Cognito sign-in. Groups are the roles; custom:tenant_id and custom:entity_ids become the Scope
(auth/scope.py). The portal signs in through managed login with the authorization code flow and PKCE."""
from typing import get_args

from aws_cdk import Aws, CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_cognito as cognito
from constructs import Construct

from config import DEFAULT_TENANT_ID
from infra.constants import (COGNITO_DEMO_USERS, CUSTOM_ATTRIBUTE_PREFIX, ENTITY_IDS_ATTRIBUTE, ID_TOKEN_VALIDITY_HOURS,
                             LOCAL_PORTAL_URL, MANAGED_LOGIN_DOMAIN_BASE, TENANT_ID_ATTRIBUTE, USER_POOL_BASE_NAME,
                             DemoUser)
from infra.naming import physical_name
from tools.models import Role

SUPPRESS_INVITATION = "SUPPRESS"   # no e-mail goes out; the password is set with admin-set-user-password


class AuthStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, prefix: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name=physical_name(prefix, USER_POOL_BASE_NAME),
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(username=True),
            custom_attributes={TENANT_ID_ATTRIBUTE: cognito.StringAttribute(mutable=True),
                               ENTITY_IDS_ATTRIBUTE: cognito.StringAttribute(mutable=True)},
            account_recovery=cognito.AccountRecovery.NONE,
            feature_plan=cognito.FeaturePlan.ESSENTIALS,   # managed login (the new version) needs Essentials
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.user_pool_client = self.user_pool.add_client(
            "PortalClient",
            generate_secret=False,   # a browser app is a public client: PKCE instead of a secret
            auth_flows=cognito.AuthFlow(user_srp=True, admin_user_password=True),   # SRP for sign-in; admin: checks
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[cognito.OAuthScope.OPENID, cognito.OAuthScope.PROFILE],
                callback_urls=[LOCAL_PORTAL_URL],
                logout_urls=[LOCAL_PORTAL_URL],
            ),
            supported_identity_providers=[cognito.UserPoolClientIdentityProvider.COGNITO],
            # By default a client may write every attribute, so a user could set their own custom:entity_ids="*".
            write_attributes=cognito.ClientAttributes().with_standard_attributes(fullname=True),
            id_token_validity=Duration.hours(ID_TOKEN_VALIDITY_HOURS),
            prevent_user_existence_errors=True,
        )
        self.managed_login_domain = self.user_pool.add_domain(
            "ManagedLoginDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"{physical_name(prefix, MANAGED_LOGIN_DOMAIN_BASE)}-{Aws.ACCOUNT_ID}"),
            managed_login_version=cognito.ManagedLoginVersion.NEWER_MANAGED_LOGIN,
        )
        cognito.CfnManagedLoginBranding(self, "ManagedLoginBranding", user_pool_id=self.user_pool.user_pool_id,
                                        client_id=self.user_pool_client.user_pool_client_id,
                                        use_cognito_provided_values=True)
        groups = {role: cognito.CfnUserPoolGroup(self, f"Group-{role}", user_pool_id=self.user_pool.user_pool_id,
                                                 group_name=role)
                  for role in get_args(Role)}
        for demo_user in COGNITO_DEMO_USERS:
            self._add_demo_user(demo_user, groups[demo_user.group])
        self.issuer_url = self.user_pool.user_pool_provider_url
        CfnOutput(self, "UserPoolId", value=self.user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=self.user_pool_client.user_pool_client_id)
        CfnOutput(self, "IssuerUrl", value=self.issuer_url)
        CfnOutput(self, "ManagedLoginUrl", value=self.managed_login_domain.base_url())

    def _add_demo_user(self, demo_user: DemoUser, group: cognito.CfnUserPoolGroup) -> None:
        user = cognito.CfnUserPoolUser(
            self, f"User-{demo_user.username}",
            user_pool_id=self.user_pool.user_pool_id,
            username=demo_user.username,
            message_action=SUPPRESS_INVITATION,
            user_attributes=[
                cognito.CfnUserPoolUser.AttributeTypeProperty(
                    name=f"{CUSTOM_ATTRIBUTE_PREFIX}{TENANT_ID_ATTRIBUTE}", value=DEFAULT_TENANT_ID),
                cognito.CfnUserPoolUser.AttributeTypeProperty(
                    name=f"{CUSTOM_ATTRIBUTE_PREFIX}{ENTITY_IDS_ATTRIBUTE}", value=demo_user.entity_ids),
            ],
        )
        attachment = cognito.CfnUserPoolUserToGroupAttachment(
            self, f"Membership-{demo_user.username}", user_pool_id=self.user_pool.user_pool_id,
            username=demo_user.username, group_name=demo_user.group)
        attachment.add_dependency(user)
        attachment.add_dependency(group)
```

- [ ] **Step 6: Wire it into the app.** In `infra/app.py`:
  - add `from infra.stacks.auth_stack import AuthStack` before the `DataStack` import;
  - add the field `auth: AuthStack` after `guardrail: GuardrailStack` in `PortalStacks`;
  - in `build_stacks`, after the `guardrail = ...` line, add
    `auth = AuthStack(app, "AuthStack", prefix=prefix, **stack_options("AuthStack"))`
    and add `auth=auth` to the `PortalStacks(...)` call in the `return`.

- [ ] **Step 7: Run them**
```bash
uv run --locked pytest tests/infra/stacks/test_auth_stack.py --no-cov 2>&1 | tail -1
```
Expected: `7 passed`.

- [ ] **Step 8: Synth with no credentials and look at the client**
```bash
cd infra && env -u AWS_PROFILE AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q 2>&1 | grep -E "Successfully|rror"
python3 -c "import json; template = json.load(open('cdk.out/AuthStack.template.json')); print([resource['Properties']['Domain'] for resource in template['Resources'].values() if resource['Type'] == 'AWS::Cognito::UserPoolDomain'])"
cd ..
```
Expected: `Successfully synthesized to .../infra/cdk.out`, then `[{'Fn::Join': ['', ['demo-erp-portal-', {'Ref': 'AWS::AccountId'}]]}]`.

- [ ] **Step 9: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/constants.py infra/app.py infra/stacks/auth_stack.py tests/infra/stacks/test_auth_stack.py
git commit -m "infra: AuthStack, Cognito pool with role groups, claim attributes users can't write, PKCE client, demo users (M3b)"
```
Expected: `237 passed`, `TOTAL ... 96%`.

**Task done when:**
- `uv run --locked pytest` → `237 passed`, 96%.
- `AuthStack.template.json` synthesises with no credentials and its client has `"WriteAttributes": ["name"]`.

### Task 2: Deploy, set the passwords out of band, check a real token, open the PR (verify in AWS; ask Michael first)

**Files:** none (deploy, checks and PR only).

**Produces:** a deployed `demo-AuthStack`; the four outputs for Yaw, Clement and Linus; the PR.

- [ ] **Step 1: Deploy (with Michael's OK).**
```bash
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
cd infra && npx cdk deploy AuthStack --require-approval never 2>&1 | tail -6; cd ..
```
Expected (verify in AWS): `✅  demo-AuthStack` and four outputs: `UserPoolId = eu-west-1_<...>`, `UserPoolClientId = <26 characters>`, `IssuerUrl = https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_<...>`, `ManagedLoginUrl = https://demo-erp-portal-486128667962.auth.eu-west-1.amazoncognito.com`.

- [ ] **Step 2: Read the outputs into the shell**
```bash
stack_output() { aws cloudformation describe-stacks --stack-name "$1" --query "Stacks[0].Outputs[?OutputKey=='$2'].OutputValue" --output text; }
USER_POOL_ID=$(stack_output demo-AuthStack UserPoolId)
USER_POOL_CLIENT_ID=$(stack_output demo-AuthStack UserPoolClientId)
MANAGED_LOGIN_URL=$(stack_output demo-AuthStack ManagedLoginUrl)
aws cognito-idp list-users-in-group --user-pool-id "$USER_POOL_ID" --group-name entity_lead --query "Users[].Username" --output text
```
Expected: `e2-lead-user	e4-lead-user` (tab-separated, either order).

- [ ] **Step 3: Set each demo user's password out of band.** Patrick gives you the passwords privately. Type each one at a hidden prompt; it never lands in the history or a file:
```bash
for demo_username in cfo-user sponsor-user delivery-lead-user e4-lead-user e2-lead-user; do
  read -rsp "Password for ${demo_username}: " demo_password && echo
  aws cognito-idp admin-set-user-password --user-pool-id "$USER_POOL_ID" --username "$demo_username" \
    --password "$demo_password" --permanent
done
unset demo_password
aws cognito-idp list-users --user-pool-id "$USER_POOL_ID" --query "Users[].UserStatus" --output text
```
Expected: five prompts, no output from `admin-set-user-password`, then `CONFIRMED` five times. (The pool's default policy needs 8+ characters with upper case, lower case, a digit and a symbol; an `InvalidPasswordException` means the password is too weak: ask Patrick for another.)

- [ ] **Step 4: Get the E4 lead's tokens (verify in AWS).**
```bash
read -rsp "Password for e4-lead-user: " demo_password && echo
read -r E4_ID_TOKEN E4_ACCESS_TOKEN < <(aws cognito-idp admin-initiate-auth --user-pool-id "$USER_POOL_ID" \
  --client-id "$USER_POOL_CLIENT_ID" --auth-flow ADMIN_USER_PASSWORD_AUTH \
  --auth-parameters "USERNAME=e4-lead-user,PASSWORD=${demo_password}" \
  --query "[AuthenticationResult.IdToken, AuthenticationResult.AccessToken]" --output text)
unset demo_password
echo "${#E4_ID_TOKEN} ${#E4_ACCESS_TOKEN}"
```
Expected: two numbers above 500 (the token lengths). Never print or save the tokens themselves.

- [ ] **Step 5: The ID token carries the scope claims (verify in AWS).**
```bash
uv run python -c "
import base64, json, sys
payload = sys.argv[1].split('.')[1]
claims = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))
print(json.dumps({claim: claims.get(claim) for claim in ('cognito:groups', 'custom:tenant_id', 'custom:entity_ids', 'aud', 'token_use')}))
" "$E4_ID_TOKEN"
```
Expected: `{"cognito:groups": ["entity_lead"], "custom:tenant_id": "t-01", "custom:entity_ids": "E4", "aud": "<the UserPoolClientId>", "token_use": "id"}`.

- [ ] **Step 6: The user can't widen their own scope (verify in AWS; Review Focus 1).**
```bash
aws cognito-idp update-user-attributes --access-token "$E4_ACCESS_TOKEN" \
  --user-attributes Name=custom:entity_ids,Value='*' 2>&1 | tail -1
aws cognito-idp admin-get-user --user-pool-id "$USER_POOL_ID" --username e4-lead-user \
  --query "UserAttributes[?Name=='custom:entity_ids'].Value" --output text
```
Expected: an error line containing `NotAuthorizedException` (a client may not write `custom:entity_ids`), then `E4`. **If the update succeeds, stop:** reset the attribute with `aws cognito-idp admin-update-user-attributes --user-pool-id "$USER_POOL_ID" --username e4-lead-user --user-attributes Name=custom:entity_ids,Value=E4`, and tell Michael and Patrick; it's a security finding ([[Handling security findings]]).

- [ ] **Step 7: Managed login answers for the localhost client (verify in AWS).**
```bash
curl -s -o /dev/null -w "%{http_code}\n" "${MANAGED_LOGIN_URL}/login?client_id=${USER_POOL_CLIENT_ID}&response_type=code&scope=openid&redirect_uri=http%3A%2F%2Flocalhost%3A4200"
```
Expected: `200`. Optional, in a browser: open the same URL, sign in as `e4-lead-user`, and land on `http://localhost:4200/?code=...`.

- [ ] **Step 8: Review Focus, then the PR (with Michael's OK).** Work through the Review Focus list and write each result in the ledger. Then:
```bash
unset E4_ID_TOKEN E4_ACCESS_TOKEN
git push -u origin feature/infra-auth
gh pr create --repo Amali-Tech/cloud-9-hackathon --base develop --title "infra: AuthStack, Cognito sign-in with role and entity claims (M3b)" --body-file .superpowers/pr-M3b.md
```
Write `.superpowers/pr-M3b.md` first: what changed (pool, groups, the client and why `WriteAttributes` is `name`, the domain, the demo users and that passwords are out of band), the test count (`237 passed`, 96%), the results of Steps 5–7 (claims, `NotAuthorizedException`, `200`; **no tokens**), Abdul's OK, and the ledger's `Ruling:` lines. No attribution lines.
Expected: the PR opens against `develop`; the Jenkins check goes green.

- [ ] **Step 9: Tell the team.** Post `UserPoolId`, `UserPoolClientId`, `IssuerUrl` and `ManagedLoginUrl` (not secrets) for Yaw (JWT authorizer), Clement (sign-in) and Linus (claims). Tell Clement the portal must send the **ID token**. Update [[Build order]]: M3b `in review (PR #nn)`.

**Task done when:**
- Step 5 printed the four expected claims and Step 6 printed `NotAuthorizedException` then `E4`.
- The PR is open with a green Jenkins check.

## Done means
- [ ] **The suite is green with the auth tests.** Verify: `uv run --locked pytest 2>&1 | grep -E "passed|TOTAL"` on the branch → `237 passed`, `TOTAL ... 96%`.
- [ ] **Synth needs no credentials and the client can't write claims.** Verify: `cd infra && env -u AWS_PROFILE AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q && grep -A1 '"WriteAttributes"' cdk.out/AuthStack.template.json` → `Successfully synthesized` and `"name"`.
- [ ] **The pool, groups and users exist (verify in AWS).** Verify: `aws cognito-idp list-groups --user-pool-id "$USER_POOL_ID" --query "Groups[].GroupName" --output text` → the four roles; `aws cognito-idp list-users --user-pool-id "$USER_POOL_ID" --query "length(Users)"` → `5`.
- [ ] **The E4 lead's ID token carries the scope (verify in AWS).** Verify: Task 2 Step 5 → `cognito:groups ["entity_lead"]`, `custom:tenant_id "t-01"`, `custom:entity_ids "E4"`, `aud` = `UserPoolClientId`.
- [ ] **A user can't widen their scope (verify in AWS).** Verify: Task 2 Step 6 → `NotAuthorizedException`, then `E4`.
- [ ] **Managed login is up (verify in AWS).** Verify: Task 2 Step 7 → `200`.
- [ ] **No password anywhere in the repo.** Verify: `git grep -n -iE "password\s*[=:]\s*[\"']" feature/infra-auth -- infra tests/infra` → no output (no quoted password value anywhere).
- [ ] **PR open to `develop`, green, and [[Build order]] says `in review (PR #nn)`.** Verify: `gh pr checks <nn> --repo Amali-Tech/cloud-9-hackathon` → the Jenkins check `pass`.

## Never
- Put a password, a token or a secret in code, the template, the repo, the vault, Slack, the PR or the ledger.
- Widen `write_attributes` or remove it (users could set their own `custom:entity_ids`).
- Add the implicit flow, a client secret or `ALLOW_USER_PASSWORD_AUTH`.
- Create users, groups or clients in the console (clean-deploy gate).
- Deploy from CI; push to `develop` or `main`; add attribution lines.

Related: [[M3b - AuthStack - spec]], [[Build order]], [[Michael - DevOps]], [[How to execute a plan]]
