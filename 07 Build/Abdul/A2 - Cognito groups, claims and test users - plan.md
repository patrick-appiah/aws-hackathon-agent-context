---
tags: [build, plan, area/identity]
id: A2
owner: Abdul
spec: "[[A2 - Cognito groups, claims and test users - spec]]"
status: ready
updated: 2026-10-14
---
# A2: Cognito groups, claims and test users (implementation plan)

> **For the executing agent (and Abdul):** follow [[How to execute a plan]] exactly, with one change: **Abdul does not run Python, uv or pytest, and never creates anything in AWS.** Wherever a step needs a command, it says "ask Linus (or Michael) to run X and send you the output", and you compare it with the `Expected:` line. Work the tasks in order. If anything differs from `Expected:`, stop and follow "When output doesn't match" in [[How to execute a plan]].

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]]: the procedure and the PR rules.
2. [[A2 - Cognito groups, claims and test users - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in your ledger.
3. [[Abdul - evals, Cognito, docs]] §5, [[Michael - DevOps]] item 5, [[Linus - API, identity, blocker-analyst]] §1.
4. [[2026-10-13 Scope from the token, enforced twice]] and [[Deploy and demo checks]] (the D2 12:00 go/no-go).

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If it's still unclear, stop and ask Michael (Cognito) or Linus (claims).

**Goal:** the groups, claims and five test users are agreed with Michael, deployed by him in CDK, listed in `HANDOFF.md` without passwords, and checked end to end at D2 12:00.

**Architecture:** Cognito user pool (Michael's AuthStack) → ID token with `cognito:groups`, `custom:tenant_id`, `custom:entity_ids` → API Gateway JWT authorizer (Yaw) → `auth/scope.py` *(new)* `scope_from_claims` (created by Linus's L1) → `Scope` → every query and tool.

**Tech stack:** Slack or GitHub for the agreement, VS Code + Git for `HANDOFF.md`, the AWS console **read-only** (Cognito, eu-west-1), the portal in a browser, optionally Postman (nothing saved or committed).

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: `docs/cognito-test-users` from an up-to-date `develop`.
- **Start state:** `develop` has C1 merged; Linus's `uv run --locked pytest` → **`204 passed`**, 96% (or the higher count once more items merge: that's your baseline). `HANDOFF.md` has the sections "What's real", "What's faked / stubbed", "What breaks first", "Week one / two / three for the next team", "Contacts", and **no** "Test users" section. `config.py` has `DEFAULT_TENANT_ID = "t-01"`.
- **Your ledger:** `.superpowers/ledger-A2.md` (gitignored). One line per task.
- **Rules:**
  - **No passwords or tokens in any file, message, issue, PR or screenshot.** If you paste a token into Postman, close the tab after; never save or export the request.
  - **Never create, change or delete anything in AWS.** If something is missing, ask Michael to add it in CDK.
  - `eu-west-1` only. Synthetic names only (people by role).
  - Markdown guard tests: no bare `` `pytest` ``, no `uv run pytest`, no `python scripts/…` without `uv run `, test files only by `tests/…` path.
  - Commits: the messages given; **no `Co-Authored-By` and no "Generated with" lines.** Never push to `develop` or `main`; PR to `develop`; Linus reviews; Patrick merges.

## Review Focus (what nothing tests; check by hand at the end)
1. Group names in the console are exactly `cfo`, `sponsor`, `delivery_lead`, `entity_lead` (underscore, lower case), the same as `tools/models.py` `Role`.
2. `custom:entity_ids` is a **string** (`E4`, `*`), not a list, in the console and in the token.
3. No user is in two groups (each user's "Group memberships" shows one).
4. `HANDOFF.md`, the PR and every message you sent contain no password, no token, no real email.
5. The users were created by CDK (Michael confirms the AuthStack deploy created them; the console shows them, and nobody clicked "Create user").

---

### Task 1: Agree the list with Michael (D1, by 18:00)

**Files:** none.
**Produces:** Michael's written agreement. **Consumes:** spec §3.

- [ ] **Step 1: Send Michael the list.** In Slack (or as a comment on his AuthStack PR, once it exists), send:
```markdown
A2 Cognito list for AuthStack (spec: 07 Build/Abdul/A2 - Cognito groups, claims and test users - spec.md §3)
Groups: cfo, sponsor, delivery_lead, entity_lead. Custom attributes (String, mutable): tenant_id, entity_ids.
| Username | Group | custom:tenant_id | custom:entity_ids |
|---|---|---|---|
| demo-cfo | cfo | t-01 | * |
| demo-sponsor | sponsor | t-01 | * |
| demo-delivery-lead | delivery_lead | t-01 | * |
| demo-entity-lead-e4 | entity_lead | t-01 | E4 |
| demo-entity-lead-e2 | entity_lead | t-01 | E2 |
Each user in exactly one group. Username sign-in; if the pool needs an email, use <username>@example.com. No passwords in code: Patrick sets them out of band.
Please confirm, or tell me what you need changed.
```
Expected: Michael replies "agreed" (or names a change). Copy his reply into the ledger. If he changes anything (for example a stack prefix in the usernames), update spec §3 with the owner's OK and use his names everywhere after this.

- [ ] **Step 2: Tell Linus the claim names.** Send: *"A2: tokens will carry `cognito:groups` (one of cfo/sponsor/delivery_lead/entity_lead), `custom:tenant_id` = t-01, `custom:entity_ids` = `*`, `E4` or `E2` (comma-separated string). Matches your `scope_from_claims`?"*
Expected: Linus confirms "matches". Ledger line.

- [ ] **Step 3: Ledger:** `Task 1: complete (Michael agreed <date/time>; Linus confirmed claims)`.

**Task done when:**
- Michael's written agreement to the §3 list is in the ledger;
- Linus confirmed the claim names match `auth/scope.py`.

### Task 2: Write the `HANDOFF.md` section (D1 evening)

**Files:** Modify `HANDOFF.md`.
**Produces:** the "Test users (Cognito)" section. **Consumes:** Task 1.

- [ ] **Step 1: Branch.**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
git switch -c docs/cognito-test-users
mkdir -p .superpowers && printf '# Ledger: A2 Cognito users\n' > .superpowers/ledger-A2.md
```
Expected: `Switched to a new branch 'docs/cognito-test-users'`.

- [ ] **Step 2: Insert the section.** Open `HANDOFF.md`. Put the cursor on the empty line just before `## What breaks first`, and paste the whole block from spec §4 (from `## Test users (Cognito)` to the line ending `as a demo CFO user.`), followed by one empty line. If Michael changed a username in Task 1, use his.
Expected: the preview (Ctrl+Shift+V) shows, in order, "What's real", "What's faked / stubbed", **"Test users (Cognito)"** with a 5-row table, "What breaks first". Ctrl+F `password` finds only the sentence "Passwords are not in the repo".

- [ ] **Step 3: Commit and push.**
```bash
git add HANDOFF.md
git commit -m "HANDOFF: list the Cognito test users per role (no passwords)"
git push -u origin docs/cognito-test-users
```
Expected: `1 file changed, 14 insertions(+)` (about; the section is 14 lines with its blank lines), then the tracking line.

- [ ] **Step 4: Ask Linus to run the guards.** *"Please run `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"` on `docs/cognito-test-users` and send me the output."*
Expected: the baseline passed count, no `failed`, coverage not lower (dry-run of this exact section on the C1 branch: `204 passed`, 96%).

- [ ] **Step 5: PR.** Base `develop`, title `HANDOFF: Cognito test users (A2)`, body: "The agreed list (Michael, <date>). No passwords. Linus's run: <paste>." Request review from Linus and Michael.
Expected: the PR page shows base `develop`, one file changed (`HANDOFF.md`), and a green Jenkins check once it runs.

**Task done when:**
- the PR to `develop` is open with only `HANDOFF.md` changed;
- Linus's output on the branch shows 0 failed.

### Task 3: Check the deployed pool, read-only (D2 morning, after Michael deploys AuthStack)

**Files:** none.
**Produces:** a ledger line per check. **Consumes:** Michael's deploy (M3\*).

- [ ] **Step 1: Find the pool.** Sign in to the AWS console with your IAM user, region **Europe (Ireland) eu-west-1** (top right). Search "Cognito" → User pools. Ask Michael which pool is the current one if there are several prefixes.
Expected: one user pool for the current prefix, created by CloudFormation (its tags or Michael's stack output `user pool ID` match).

- [ ] **Step 2: Groups.** Open the pool → "Groups" (under User management).
Expected: exactly four groups: `cfo`, `delivery_lead`, `entity_lead`, `sponsor`.

- [ ] **Step 3: Users.** Open "Users".
Expected: five users: `demo-cfo`, `demo-delivery-lead`, `demo-entity-lead-e2`, `demo-entity-lead-e4`, `demo-sponsor` (status "Confirmed" or "Force change password", depending on how Patrick set passwords).

- [ ] **Step 4: Each user's group and attributes.** Click each user. Under "Group memberships" and "User attributes":
Expected:
  - `demo-cfo`: group `cfo`; `custom:tenant_id` `t-01`; `custom:entity_ids` `*`.
  - `demo-sponsor`: `sponsor`; `t-01`; `*`.
  - `demo-delivery-lead`: `delivery_lead`; `t-01`; `*`.
  - `demo-entity-lead-e4`: `entity_lead`; `t-01`; `E4`.
  - `demo-entity-lead-e2`: `entity_lead`; `t-01`; `E2`.
  - Each user has exactly one group.
  Any difference: don't fix it; send Michael the user, the field, what you see and what §3 says.

- [ ] **Step 5: Ledger:** `Task 3: complete (pool <id from Michael>: 4 groups, 5 users, attributes match / differences sent to Michael: <list>)`.

**Task done when:**
- the console shows 4 groups and 5 users matching spec §3 exactly, or every difference is sent to Michael;
- nothing was changed in the console.

### Task 4: End-to-end sign-in at the go/no-go (D2 11:30–12:00)

**Files:** none (optionally a `HANDOFF.md` line if the slice is off).
**Produces:** the go/no-go evidence. **Consumes:** F3 (Clement's sign-in), F4 (Clement's ask panel), Y1, L1–L2, the passwords from Patrick.

- [ ] **Step 1: Sign in as each user.** Get the passwords from Patrick privately. Open the portal's CloudFront URL in a private browser window. Sign in as each user in turn (sign out between).
Expected:
  - `demo-cfo`, `demo-sponsor`, `demo-delivery-lead`: the dashboard shows all four entities (E1–E4); the header shows the role.
  - `demo-entity-lead-e4`: only E4 appears.
  - `demo-entity-lead-e2`: only E2 appears.
  - Only `demo-delivery-lead` sees an approve action (the front end's `APPROVER_ROLES` is `delivery_lead` only).

- [ ] **Step 2: The refusal.** Signed in as `demo-entity-lead-e4`, use the portal's ask panel (Clement's F4) to ask, for entity E2 if the panel offers an entity choice, `What is blocking cutover for E2?` (EVALS Q11). The portal has no entity page today (`web/src/app/app.routes.ts` has only the dashboard, `publish/:runId`, `approve/:executionArn` and `sign-in`), so the raw `/entity/E2` check is Step 3.
Expected: a refusal message (Clement's 403 refusal card), no answer, no E2 figures. If the panel only offers E4, write "E2 not selectable" in the ledger (that is also a pass: the UI can't ask) and rely on Step 3 for the 403.

- [ ] **Step 3: the raw 403 and 401 in Postman (optional if Linus's deployed-API asker already showed Q11 refused).** Still signed in as the E4 lead, open the browser's DevTools (F12) → Network, reload, click the `summary` request → Headers → Request Headers → copy the value after `Authorization: Bearer `. In Postman (a new, **unsaved** request): `GET https://<CloudFront domain>/api/entity/E2`, Headers `Authorization` = `Bearer <pasted token>` → Send. Then remove the header → Send.
Expected: first **`403`** with a body `{"error": "out_of_scope", "detail": "…"}` (or `"forbidden"`); then **`401`** (no body from our code; API Gateway's `{"message":"Unauthorized"}`). Close the Postman tab without saving; don't screenshot the token.

- [ ] **Step 4: Report the go/no-go.** Post at the 12:00 stand-up: "Cognito: 5 users sign in; E4 lead sees only E4, refused E2 (403); E2 lead sees only E2." or exactly what failed.
Expected: Patrick records go or no-go. If **no-go** (`AUTH_MODE=none`), add this line under "What's faked / stubbed" in `HANDOFF.md` on a branch `docs/cognito-no-go`: `- **Cognito sign-in is switched off for the demo** (\`AUTH_MODE=none\`, D2 12:00 go/no-go): every request runs as a demo CFO user. The users above exist in the pool; <what failed>.` and PR it as in Task 2.

- [ ] **Step 5: Ledger:** `Task 4: complete (go/no-go: <go/no-go>; 5 users checked; 403 seen <yes/no>)`.

**Task done when:**
- all five users were tried and the result per user is in the ledger;
- the E4 lead's refusal on E2 was seen (portal, and optionally the 403 in Postman);
- the go/no-go was reported at the stand-up.

## Never
- Create, edit or delete a user, group or attribute in the console.
- Write, paste or screenshot a password or a token anywhere lasting.
- Save or export a Postman request or collection.
- Use a real person's name or a real email address.
- Push to `develop` or `main`, or add attribution lines.

## Done means
- [ ] **Michael agreed the list in writing.** *Verify:* his Slack message or PR comment quoting the five usernames.
- [ ] **`HANDOFF.md` on `develop` has "## Test users (Cognito)"** with the 5-row table of spec §4, and Ctrl+F `password` finds only "Passwords are not in the repo". *Verify:* open `HANDOFF.md` on GitHub, `develop` branch.
- [ ] **The PR is merged** and its body has Linus's suite output with 0 failed. *Verify:* the PR from `docs/cognito-test-users` shows "Merged".
- [ ] **The deployed pool matches.** *Verify:* AWS console (eu-west-1) → Cognito → the pool shows groups `cfo`, `delivery_lead`, `entity_lead`, `sponsor` and the five users with the attributes in spec §3, each in one group.
- [ ] **End to end works, or the no-go is documented.** *Verify:* signed in as `demo-entity-lead-e4`, the portal shows only E4 and refuses E2; or `HANDOFF.md` on `develop` has the "Cognito sign-in is switched off" line.

Related: [[A2 - Cognito groups, claims and test users - spec]], [[Build order]], [[How to execute a plan]]
