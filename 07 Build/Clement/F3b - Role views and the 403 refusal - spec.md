---
tags: [build, spec, area/frontend]
id: F3b
owner: Clement
status: ready
updated: 2026-10-14
---
# F3b: role-based views and a clear 403 refusal (spec)
> **"As the E4 lead, asking about E2 shows the refusal" (EVALS Q11).** F3 in [[Build order]] is split: **F3a** ([[F3a - Cognito sign-in - spec]]) is Cognito sign-in; **F3b** (this) is what each role sees and how a refusal looks. F3b works in `AUTH_MODE=none` with the role switcher, so it does not wait for Cognito. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after F1b is merged.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Clement - front end]].
3. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
4. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
5. [[F1b - Real fixtures and the dashboard on the contract keys - spec]] (Mildred): the mock returns the server's own E4-lead summary.
6. [[L3 - Ask, publish and approve entry points - spec]] (Linus): `/ask` refuses an out-of-scope entity with 403 before any run starts.
7. `EVALS.md` (repo) Q11; `01 Decisions/` [[2026-10-13 Scope from the token, enforced twice]].
8. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. **A refusal, not an error.** When `/ask` answers 403, the ask panel shows a calm notice that says what the user may see: **"You can see E4 only. E2 is outside your access."**, no red error box and no Retry. Other failures keep the error box with Retry.
2. **A way to ask about another entity** (so the refusal can be shown and demoed): the suggested question "What is blocking cutover for entity 2?" asks about E2 even when E2 is not in the user's picker. **The API decides;** the UI never filters what may be asked.
3. **Role views, confirmed:** an entity lead sees only their entities (the API's summary; the mock serves the server's E4-lead export, F1b); only a `delivery_lead` reaches the approve page (`approverGuard`, unchanged); the mock role switcher stays for `AUTH_MODE=none`. In `AUTH_MODE=none` the switcher is **display only**: the server serves L1's demo user, whose role is the `DEMO_ROLE` setting (default `cfo`) over every entity, whatever the switcher shows.

**Why:** EVALS Q11 and the brief's "a 403 shows a clear refusal ('You can see E4 only'), not an error page". The refusal is evidence of the scope gate (D-010); the rubric's security line is pass/fail.

**Success means:**
- `refusalMessage({entity_ids: ['E4']}, 'E2')` → `You can see E4 only. E2 is outside your access.`; two entities → `You can see E2 and E4 only. …`; `*` → `E2 is outside your access.`
- Mock mode, Switch user → Entity lead (E4), click "What is blocking cutover for entity 2?": the panel shows the refusal in a `role="status"` notice; no `app-load-error`.
- A 502 still shows the error box, and Retry asks again.
- `yarn test`: +3 tests on the start state.
- **In AWS with Cognito (verify there, after F3a):** signed in as the E4 lead, the same click returns 403 from `/api/ask` and shows the same refusal; the ledger has no E2 rows (Abdul's Q11 manual check).

**Assumptions:** L3 answers an out-of-scope `/ask` with **403** (`ErrorResponse`, `out_of_scope`); F2's `ApiError` carries the status. **The `AUTH_MODE=none` demo path (lead decision D2, L1):** with `AUTH_MODE=none` the server ignores tokens and serves one demo user, `Scope(user_id="demo-<DEMO_ROLE>", role=DEMO_ROLE, entity_ids=("*",))`, from L1's `DEMO_ROLE` setting (default `cfo`). AUTH_MODE=none with DEMO_ROLE=delivery_lead is a demo-only fallback for the approval step if the Cognito slice is off. Because the demo user sees every entity, a live API in `AUTH_MODE=none` never refuses E2: if the Cognito go/no-go is no-go, the refusal is demonstrated in mock mode, and the live approve beat uses `DEMO_ROLE=delivery_lead` (F5). The refusal wording uses the **displayed** scope (from the role switcher or, after F3a, the ID token claims), never anything the API must trust.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Wording | Built from the shown scope: "You can see E4 only." + "E2 is outside your access." (`refusalMessage` in `core/session/permissions.ts`, beside the other who-may-do-what rules) | The API's `detail` alone (doesn't say what the user *can* see); a generic "Access denied" |
| How it looks | `<p class="refusal" role="status">` with a calm left border; no Retry | The red `app-load-error` (reads as a crash); the ADS alert (its text sits in a shadow root, so screen-reader and test checks can't read it reliably) |
| Asking about an entity outside the picker | Only through the suggested question, which carries its own `entityId`; the request goes to the API, which refuses | Adding hidden entities to the picker; checking scope in the browser before asking (the UI would be the gate) |
| 403 detection | `ApiError.status === 403` (named `HTTP_FORBIDDEN`) | Matching message text |

## 3. The shapes
- `refusalMessage(scope: Scope, requestedEntityId: string): string` *(new)* in `core/session/permissions.ts`.
- `AskStore`: state status `'refused'`, `refusal = computed<string | undefined>` *(new)*.
- `SUGGESTED_QUESTIONS` gains `{ text: 'What is blocking cutover for entity 2?', entityId: 'E2' }`. `AskPanel.pickSuggestion` asks `{entity_id: suggestion.entityId ?? picked entity, question}`.

## 4. Tests
- `core/session/permissions.spec.ts` +1 (the three wordings). `features/ask/ask-store.spec.ts`: the 403 test becomes "a refusal, not an error"; a new 502 retry test (+1). `features/ask/ask-panel/ask-panel.spec.ts` *(new)*, 1: the E4 lead clicks the E2 suggestion in mock mode and sees the refusal.

## 5. Out of scope
- Cognito sign-in and the ID token: **F3a**. The approve page's own role check exists (`approverGuard`, `ApprovePage.allowed`).
- A 403 on `/summary` (a user with no group): shown by the dashboard's error box with the API's `detail` (F2).

Related: [[F3b - Role views and the 403 refusal - plan]], [[F3a - Cognito sign-in - spec]], [[Build order]], [[Clement - front end]]
