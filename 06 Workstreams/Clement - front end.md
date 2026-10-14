---
tags: [workstream, area/team]
owner: Clement
updated: 2026-10-14
---
# Clement: front end, sign-in, ask, publish and approve
> The repo is the source of truth. Read [[Workstreams]] first. Your row: `docs/TEAM_PLAN.md` §2, workstream 6 (with Mildred, [[Mildred - front end]]).
> **Proposal: confirm this split with Mildred at the first stand-up.** You take **sign-in, roles, ask, publish and approve, and the demo run**; Mildred takes the data layer and the one screen. File ownership is listed below so you never edit the same files.

## Your job in one paragraph
You make the portal's **trust story visible**:
- **real Cognito sign-in**, so the token decides what each role can see (an E4 entity lead is refused E2);
- the **ask panel** on the real `/ask`: the cited answer, the agent trace with prompt versions, the "could not verify" list for rejected claims, and partial answers;
- **publish and approve**, where nothing is written until the delivery lead approves.

You also own the **demo run**: the cold-start rehearsal and the **2-minute backup video**. The organisers require the video, and relying on it caps one demo criterion, so the live run must work.

## Shared front-end context (same in Mildred's brief)
- **Setup:** Node 22 (`web/.nvmrc`), yarn 1.22.22 via `corepack enable`, the read-only npm token in your **home** `~/.npmrc` (`web/README.md`). Then `cd web && yarn install --frozen-lockfile && yarn start`; `yarn test`; `yarn build` → `web/dist/web/browser`.
- **Switches:** `web/src/app/core/config/portal-config.ts`: `dataSource` (`mock` | `http`), `authMode` (`none` | `cognito`), `apiBaseUrl` (`/api`, same origin through Michael's CloudFront `/api/*` behaviour). Mildred owns the file; agree changes with her.
- **The API contract** is Patrick's `tools/api_schema.py` *(new)*, exported as JSON Schema. The front end adopts the back end's keys.
- **`/ask` response:** `{run_id, answer{headline, bullets[{text, citations[]}]}, rejected[{claim_id, statement, reason, verdicts[]}], cost_usd, partial, partial_reason, trace[{step, agent, prompt{agent, version, sha256}}]}`.
- **`/publish`:** `{run_id, execution_arn, status: "awaiting_approval"}`.
- **`/approve`:** request `{run_id, decision: "approve"|"send_back", note}`, response `{run_id, status: "approved"|"sent_back"}`.
- **Errors:** `{error, detail}`; 401 without a token, 403 out of scope.
- **Roles:** `cfo`, `sponsor`, `delivery_lead`, `entity_lead`. **One Cognito group per user.** Entity claims are `custom:entity_ids` (`"E4"`, `"E2,E4"` or `"*"`).

## What you own
| Path | Notes |
|---|---|
| `web/src/app/core/api/bearer-token-interceptor.ts` | sends the **ID token** (custom claims are only in the ID token) |
| `web/src/app/core/session/` (`session-store.ts`, `permissions.ts`) | who is signed in, role, entities |
| `web/src/app/core/models/ask.ts`, `publish.ts` | ask and publish models |
| `web/src/app/features/auth/` | sign-in page, role switcher (mock), approver guard |
| `web/src/app/features/ask/` | ask panel, answer card, could-not-verify list, suggested questions, ask store |
| `web/src/app/features/publish/` | publish and approve pages, publish store |
| `web/src/app/shared/layout/app-header/` | header (signed-in user, role, sign-out) |
| `DEMO.md` (with Patrick) | the demo script and pre-flight |

## What you build
1. **Cognito sign-in** (`authMode: 'cognito'`). Use Cognito's **managed login with authorization code + PKCE**, redirecting to the CloudFront URL. A small OIDC library such as `angular-auth-oidc-client` is fine; agree it with Mildred, and add it with `yarn add`.
   - Store the session in `session-store.ts`; the interceptor sends the ID token as `Authorization: Bearer`.
   - Michael's AuthStack provides the pool ID, client ID and domain; settings go into `portal-config.ts` (Mildred's file).
   - Acceptance: signing in as the E4 lead shows only E4.
2. **Role-based views:**
   - an entity lead sees only their entities;
   - a 403 shows a clear refusal ("You can see E4 only"), not an error page;
   - only a `delivery_lead` can approve (`approver-guard.ts`).
   - Keep the mock role switcher for `authMode: 'none'`.
   - Acceptance (EVALS Q11): as the E4 lead, asking about E2 shows the refusal.
3. **The ask panel on the real `/ask`:**
   - the answer card with clickable citations, through Mildred's row viewer;
   - the **trace** (each step, its agent and prompt version);
   - **cost per question**;
   - **partial answers** with `partial_reason` (Q07: unknown entity);
   - the **"could not verify" list** from `rejected[]` with each reason (Q08/Q09).
   - If Huvison and Yaw switch `/ask` to async (start + poll `GET /ask/{run_id}`, because of API Gateway's 29-second limit), the panel polls with a progress state.
4. **Publish and approve on the real API:**
   - publish shows "awaiting approval";
   - the approve page (delivery lead only) sends `approve` or `send_back` with a note, by `run_id`;
   - the status updates.
5. **The demo** (`DEMO.md`, with Patrick):
   - the 3-minute script on the real portal: 58% headline, E4 Blocked, ask "What is blocking cutover for entity 4?", then the critic catches the decoy (`DEF-0398` closed while `RC-C3-E4-customers` still fails), then publish → approve;
   - **rehearse twice from cold;**
   - **record the 2-minute backup video** and keep it on the laptop, not just in the cloud;
   - the pre-flight checklist (region `eu-west-1`, a warm-up question, latency known).

## Interfaces
| You consume | From |
|---|---|
| `PortalApi` port, http adapter, row viewer, models | Mildred |
| Schema | Patrick |
| `/ask`, `/publish`, `/approve` live | Linus (entry points), Huvison (flow), Yaw (API, state machines) |
| User pool, client, domain, test users | Michael, Abdul |

| You produce | For |
|---|---|
| Signed-in session and ID token | every API call |
| Ask, publish and approve screens | the demo |
| Backup video, rehearsal | the submission |

## Dependencies
- **You wait on:** Michael's AuthStack for sign-in. Until then, keep `authMode: 'none'` and the role switcher. Also the live `/ask` (D1 18:00, critic stubbed; the real critic D2). Build on `ask-E4.json` and `ask-partial.json` fixtures meanwhile.
- **Waiting on you:** the demo and the Cognito go/no-go at D2 12:00.

## Your milestones
| When | Milestone |
|---|---|
| D1 16:00 | Ask panel shows trace, cost, partial and could-not-verify from fixtures |
| D1 18:00 | Ask panel on the live `/ask` (walking skeleton) |
| D2 12:00 | Cognito sign-in end to end; E4 lead refused E2 (go/no-go) |
| D2 14:00 | Publish → approve live |
| D2 16:00–17:00 | Two cold-start rehearsals; backup video recorded |

## Definition of done
- [ ] Real Cognito sign-in; the ID token sent; role-based views; a clean refusal on 403.
- [ ] Ask panel shows the cited answer, trace with prompt versions, cost, partial reason and could-not-verify.
- [ ] Publish waits for approval; only the delivery lead can approve; send-back works.
- [ ] Demo rehearsed twice from cold; 2-minute backup video on the laptop.
- [ ] `yarn test` and `yarn build` green; your `HANDOFF.md` and `DEMO.md` lines.

## Rules and pitfalls specific to you
- **Never trust the client for scope.** The UI hides what a role can't see, but the API is the real gate. Never send scope in a request.
- **Never store tokens in `localStorage` beyond what the OIDC library needs;** never log them.
- **No real names** in the demo or UI copy; synthetic data only.
- **One lock file;** never commit the npm token.

## Getting started
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
cd web && corepack enable && yarn install --frozen-lockfile && yarn test
git switch -c feature/web-cognito-sign-in
```
Then give your assistant `06 Workstreams/prompts/clement.txt`.

## Who to ask
| Topic | Person |
|---|---|
| Cognito | Michael |
| Test users | Abdul |
| `/ask` shape, trace, demo | Patrick |
| Flow, async decision | Huvison |
| Entry points | Linus |
| Shared front-end files | Mildred |

Related: [[Workstreams]], [[Team plan]]
