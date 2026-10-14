---
tags: [build, spec, area/frontend]
id: F5
owner: Clement
status: ready
updated: 2026-10-14
---
# F5: publish and approve on the real API (spec)
> **Nothing is written until the delivery lead approves.** The publish and approve pages move onto C1's contract (`run_id` is the key) and run against the live `/publish` and `/approve`. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after F1b is merged; the live steps need L3 and H4.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Clement - front end]].
3. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
4. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
5. [[L3 - Ask, publish and approve entry points - spec]] (Linus) and [[Huvison - trust and flow]] (H4: `flow/publish.py` *(new)*, the task token, the status-pack write).
6. `01 Decisions/` [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]].
7. `DEMO.md` (repo): the 2:15–2:35 publish → approve beat.
8. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. `core/models/publish.ts` on the contract: `PublishResponse {run_id, execution_arn, status: 'awaiting_approval'}`, `ApproveRequest {run_id, decision: 'approve' | 'send_back', note}`, `ApproveResponse {run_id, status: 'approved' | 'sent_back'}`, `ApprovalStatus`, `APPROVAL_STATUS_BY_DECISION`.
2. **The approval is keyed by run:** route `approve/:runId` (was `:executionArn`); the publish page links "Open the approval" to `/approve/<run_id>`; `PublishStore.decide(runId, decision, note)`.
3. **The status comes from the API:** the approve page shows the badge for the `status` the API returned ("Approved" / "Sent back") and "Status from the API: sent_back".
4. **Mock and fixtures on the contract:** `publish.json`, `approve.json` carry `run_id`; the mock answers `publish` with the requested `run_id` and `approve` with the status the decision leads to.
5. **Live** publish → approve → status (verify in AWS).

**Why:** hard gate "human approval before the only write"; `DEMO.md` 2:15–2:35; C1 decided `/approve` takes `run_id` (the task token is stored by run).

**Success means:**
- Publish page (any role): "Send for approval" → badge "Awaiting approval", link `/approve/<run_id>`.
- Approve page: CFO sees "Only a delivery lead can approve…", no note box; delivery lead sees the note box, Approve and Send back; Send back → badge "Sent back" and "Status from the API: sent_back".
- Requests: `POST /publish {"run_id"}`, `POST /approve {"run_id", "decision", "note"}`, each matching its schema.
- `yarn test`: +3 on the start state.
- **In AWS (verify there):** a real run published shows "Awaiting approval"; the delivery lead's approve returns `approved` and a status pack appears under `status-packs/`; send-back returns `sent_back` and writes nothing. This works with Cognito (F3a) or, if the Cognito slice is off, with `AUTH_MODE=none` and `DEMO_ROLE=delivery_lead` (L1).

**Assumptions (reconcile with the owners):**
- **L3/H4:** `/approve` answers 403 `forbidden` to anyone but a `delivery_lead`, using the **token's** scope, and `/publish` only lets the user who asked the run publish it. With Cognito (F3a) the delivery lead signs in as Abdul's test user.
- **The `AUTH_MODE=none` demo path (lead decision D2, L1):** with `AUTH_MODE=none` the server ignores tokens and serves one demo user, `Scope(user_id="demo-<DEMO_ROLE>", role=DEMO_ROLE, entity_ids=("*",))`, from L1's `DEMO_ROLE` setting (default `cfo`). AUTH_MODE=none with DEMO_ROLE=delivery_lead is a demo-only fallback for the approval step if the Cognito slice is off. If the Cognito go/no-go (D2 12:00) is no-go, Yaw sets `AUTH_MODE=none` and `DEMO_ROLE=delivery_lead` on **every** API Lambda (`summary`, `entity`, `rows`, `ask`, `publish`, `approve`), so one demo user, `demo-delivery_lead`, asks, publishes (same user as the asker) and approves. In the browser, the role switcher is set to Delivery lead so `approverGuard` opens the approve page; the switcher is display only and the API never trusts it. With Cognito on, `DEMO_ROLE` is ignored.
- The fixtures `publish.json` and `approve.json` are in Mildred's folder; they are handed to Clement for this change (their shape follows `publish.ts`, his file). Two tests of hers change with them (`http-portal-api.spec.ts`, `mock-portal-api.spec.ts`: the approve body). *Mildred agrees before Task 1.*
- There is no status route (`GET /publish/{run_id}`) in the contract: the publish page shows "Awaiting approval" from the publish response; the decided status shows on the approve page.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Route key | `/approve/:runId` | `execution_arn` (C1 rejected it; ARNs are long and leak the account ID into links) |
| Badge after a decision | From `ApproveResponse.status` (`STATUS_LABELS`) | From the button pressed (shows "Approved" even if the API said otherwise) |
| Mock approve | `{run_id, status: APPROVAL_STATUS_BY_DECISION[decision]}` | Always `approved` (send-back could never be rehearsed in mock mode) |
| Who sees the approve controls | `canApprove(role)` (unchanged, delivery lead only) and the `approverGuard` route guard; the API decides again | Showing the controls to everyone and relying on a 403 |
| Live approve without Cognito | `AUTH_MODE=none` + `DEMO_ROLE=delivery_lead` on the API (L1, lead decision D2); no front-end change | Blocking the live approve beat on F3a; a front-end role header the API would trust (scope must come from the token) |

## 3. Tests
- `features/publish/publish-fixtures.spec.ts` *(new)*, 2: both fixtures and both request bodies against their schemas.
- `features/publish/publish-store.spec.ts`, 3: publish holds `run_id` and the execution; decide sends `{run_id, decision, note}` and holds the API's status; the API's refusal message.
- `features/publish/publish-pages.spec.ts`, 3 (was 2): publish → "Awaiting approval" + link `/approve/run-mock-e4-0001`; approve controls for the delivery lead only; send back → "Sent back" from the API.
- Mildred's specs: the approve body in `http-portal-api.spec.ts`; the mock publish/approve test in `mock-portal-api.spec.ts`.

## 4. Out of scope
- The publish flow, the task token and the status-pack write (H4, Y2); sign-in (F3a).
- Who may publish (decided in `flow.publish`); the UI lets every signed-in role press "Send for approval".

Related: [[F5 - Publish and approve on the real API - plan]], [[Build order]], [[Clement - front end]]
