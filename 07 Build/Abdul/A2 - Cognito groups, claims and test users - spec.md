---
tags: [build, spec, area/identity]
id: A2
owner: Abdul
status: awaiting review
updated: 2026-10-14
---
# A2: Cognito groups, claims and test users (spec)
> **No Python, no console clicks.** You define the groups, the two custom attributes and the test users; **Michael creates them in CDK** (AuthStack, item M3\*); you write the list into `HANDOFF.md` without passwords and check, read-only, that what's deployed matches. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop`.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before you start, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure. For you, every command is run by Linus or Michael.
2. [[Workstreams]] §2 (sign-in: "Cognito: groups = roles, claims tenant_id + entity_ids") and §7 (rules: scope comes from the token; no console-clicked resources; no secrets).
3. [[Abdul - evals, Cognito, docs]] §5 (your brief for this item).
4. [[Michael - DevOps]] "What you build" item 5 (AuthStack and its acceptance), [[Linus - API, identity, blocker-analyst]] §1 (`auth/scope.py` reads the claims), [[Clement - front end]] (sign-in, the E4 lead sees only E4).
5. [[Build order]]: A2 feeds M3\* (GuardrailStack + AuthStack), which feeds Y1 (the JWT authorizer), F3 (sign-in) and L6 (the deployed-API asker uses one ID token per scope).
6. `01 Decisions/`: [[2026-10-13 Scope from the token, enforced twice]], [[2026-10-13 POC plus one target slice, target as 90-day roadmap]] (Cognito sign-in with entity scope is the one target slice). `05 Workflow/`: [[Deploy and demo checks]] (the D2 12:00 Cognito go/no-go).

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief and rubrics; `03 Sessions/`; `Open follow-ups.md`. If it's still unclear, stop and ask Michael (Cognito) or Linus (claims → scope). Never invent a claim name or a group.

## 1. Intent
**What:** one agreed list, used by AuthStack, `auth/scope.py`, the front end and the evals:
1. **Four groups:** `cfo`, `sponsor`, `delivery_lead`, `entity_lead` (exactly the `Role` values in `tools/models.py`).
2. **Two custom attributes (strings):** `tenant_id` and `entity_ids`, read from the ID token as `custom:tenant_id` and `custom:entity_ids`.
3. **Five test users:** one per role, plus a second entity lead (E2) for the scope demo and Q11.
4. **A `HANDOFF.md` section** "Test users (Cognito)" listing them (usernames, group, attributes, purpose), **no passwords**.
5. **A read-only check** after Michael deploys, and an end-to-end sign-in check at the D2 12:00 go/no-go.

**Why:**
- The token's claims become the scope every query and agent tool is filtered by (`ARCHITECTURE.md` §4). A wrong group name or a list-typed attribute breaks sign-in for everyone.
- Q11 ("as E4 entity lead, what is blocking cutover for E2?") and the 403 demo need a real E4 lead; the scope demo needs a second entity lead (E2) to show the other side.
- `HANDOFF.md` is graded ("README, cost and handoff", 8 points). The next team needs to know who to sign in as.

**Success means:**
- Michael's AuthStack (M3\*) creates exactly the groups, attributes and users of §3, from code.
- `HANDOFF.md` on `develop` has the §4 section verbatim, with no password, token or real email.
- In the AWS console (read-only), the user pool shows 4 groups and 5 users, each in exactly one group, with the attribute values of §3.
- At D2 12:00, each of the five users signs in to the portal; the E4 lead sees only E4 and gets a refusal on E2.

**Assumptions (to reconcile with the owners):**
- **A2-1:** Linus's `auth/scope.py` *(new)* `scope_from_claims(claims, settings)` maps `cognito:groups` (exactly one) → `Scope.role`, `custom:tenant_id` → `tenant_id`, `custom:entity_ids` (comma-separated, or `*`) → `entity_ids`, `sub` → `user_id` (his brief §1).
- **A2-2:** Michael's AuthStack creates the users in CDK (for example `CfnUserPoolUser` and `CfnUserPoolUserToGroupAttachment`) with **no password in code**; Patrick sets the passwords out of band and shares them privately (your brief §5; Michael's "passwords set out of band, never in code").
- **A2-3:** the front end (Clement, F3) sends the **ID token** to the API (custom claims are only in the ID token), and the portal is reached at the CloudFront URL Michael's WebStack outputs.
- **A2-4:** sign-in is by **username**. If AuthStack requires an email attribute, Michael uses `<username>@example.com` (`example.com` is reserved for documentation, so it's never a real address), and that's still listed in `HANDOFF.md` as "email: `<username>@example.com` (not a real mailbox)".

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Group names | `cfo`, `sponsor`, `delivery_lead`, `entity_lead`, exactly `tools/models.py` `Role` | Display names ("Delivery lead"): the scope builder compares the group string to `Role` |
| Groups per user | **Exactly one.** `scope_from_claims` refuses none or several with 403 `forbidden` | Several groups (ambiguous role) |
| `custom:entity_ids` type | **A comma-separated string**: `*` for all entities, `E4` for one, `E2,E4` for several (no spaces) | A list or JSON array (Cognito custom attributes are strings) |
| `custom:tenant_id` | `t-01` for every user (`config.py` `DEFAULT_TENANT_ID`) | A second tenant user for Q13 (Q13 is `kind: target`, roadmap only) |
| Users | 5: `demo-cfo`, `demo-sponsor`, `demo-delivery-lead`, `demo-entity-lead-e4`, `demo-entity-lead-e2` (people named by role, `demo-` prefix; the front end's mock users are `u-demo-…`) | Real people's names or emails (synthetic data rule) |
| Where the list lives | `HANDOFF.md` section "Test users (Cognito)" (your brief §5); Michael's CDK reads its own copy in code | A separate users file (two sources of truth) |
| Passwords | Never written anywhere by you. Patrick shares them privately | In `HANDOFF.md`, the vault, Slack, CDK or Postman |
| Who creates | Michael, in CDK. You only **look** in the console | Creating users in the console (fails the clean-deploy gate) |

## 3. The exact list (hand this to Michael)
**User pool:** groups `cfo`, `sponsor`, `delivery_lead`, `entity_lead`. Custom attributes (type String, mutable): `tenant_id`, `entity_ids`.

| Username | Group | `custom:tenant_id` | `custom:entity_ids` | Used for |
|---|---|---|---|---|
| `demo-cfo` | `cfo` | `t-01` | `*` | The demo driver; Q01–Q10, Q12 as the CFO |
| `demo-sponsor` | `sponsor` | `t-01` | `*` | Sponsor view (all entities, can't approve) |
| `demo-delivery-lead` | `delivery_lead` | `t-01` | `*` | Approves the status pack (the only approver role) |
| `demo-entity-lead-e4` | `entity_lead` | `t-01` | `E4` | Q11; the 403 on E2; sees only E4 |
| `demo-entity-lead-e2` | `entity_lead` | `t-01` | `E2` | Second entity lead for the scope demo; sees only E2 |

**What the E4 lead's ID token must contain** (Michael's acceptance): `cognito:groups` = `["entity_lead"]`, `custom:tenant_id` = `t-01`, `custom:entity_ids` = `E4`.

## 4. The `HANDOFF.md` section (verbatim)
Inserted after the "What's faked / stubbed" section and before "What breaks first":
```markdown
## Test users (Cognito)
The one target slice that is built (D-015): sign-in with role and entity scope. AuthStack creates these users in CDK; there are no hand-made users. **Passwords are not in the repo**: ask the team lead.

| Username | Group (role) | `custom:tenant_id` | `custom:entity_ids` | Used for |
|---|---|---|---|---|
| `demo-cfo` | `cfo` | `t-01` | `*` | The demo driver; eval questions as the CFO |
| `demo-sponsor` | `sponsor` | `t-01` | `*` | Sponsor view: all entities, can't approve |
| `demo-delivery-lead` | `delivery_lead` | `t-01` | `*` | Approves the status pack (the only approver) |
| `demo-entity-lead-e4` | `entity_lead` | `t-01` | `E4` | EVALS Q11: refused on E2 (403); sees only E4 |
| `demo-entity-lead-e2` | `entity_lead` | `t-01` | `E2` | The scope demo's second entity lead; sees only E2 |

- Each user is in **exactly one** group; the group is the role. `custom:entity_ids` is a comma-separated string (`*` = all entities).
- The API reads the claims from the **ID token** (`cognito:groups`, `custom:tenant_id`, `custom:entity_ids`, `sub`) and builds the scope server-side (`ARCHITECTURE.md` §4). The client never sends scope.
- If the Cognito slice is switched off (`AUTH_MODE=none`), every request runs as a demo CFO user.
```
(The section names no command, so the doc guard tests are unaffected. Dry-run: this exact text added to `HANDOFF.md` on the C1 branch → `204 passed`, 96%.)

## 5. Tests
No code. The checks are:
- **Doc guards:** Linus runs `uv run --locked pytest` on your branch → the baseline count, 0 failed.
- **Deployed matches the list:** AWS console (read-only) → Cognito → the user pool → Groups (4, names exact) and Users (5; each user's Groups tab shows one group; Attributes show `custom:tenant_id` and `custom:entity_ids` as in §3).
- **The claims:** Michael's acceptance (E4 lead's token claims as in §3); optionally your own Postman check (plan Task 4).
- **End to end (D2 12:00):** each user signs in; E4 lead sees only E4 and is refused E2; E2 lead sees only E2.

## 6. Out of scope
- AuthStack code (Michael, M3\*), the JWT authorizer (Yaw, Y1), `auth/scope.py` (Linus, L1), the sign-in UI (Clement, F3).
- Passwords (Patrick, out of band).
- Federation with a client identity provider, Verified Permissions, a second tenant (roadmap Phase 1 and 3).

Related: [[Build order]], [[Abdul - evals, Cognito, docs]], [[A2 - Cognito groups, claims and test users - plan]]
