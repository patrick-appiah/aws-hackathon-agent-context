---
tags: [build, plan, area/frontend]
id: F3b
owner: Clement
spec: "[[F3b - Role views and the 403 refusal - spec]]"
status: ready
updated: 2026-10-14
---
# F3b: role views and the 403 refusal (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[F3b - Role views and the 403 refusal - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger as a `Ruling:` line.
3. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Clement - front end]].
4. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
5. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
6. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

**Goal:** a 403 from `/ask` reads as a refusal that names what the user may see; the E4 lead can ask about E2 and see it (Q11).

**Architecture:** `AskPanel.pickSuggestion` → `AskStore.ask` → `PortalApi.ask` → 403 `ApiError` → `refusalMessage(SessionStore.scope(), entity)` → `<p class="refusal" role="status">`.

**Tech stack:** Angular 22, TypeScript 6, Vitest through `ng test`.

**Dry-run:** Tasks 1–2 were run on 2026-10-14 in a throwaway worktree with C1, F1a, F1b, F2 and F4a applied; counts and messages are real. **Task 3's live step needs Cognito (F3a) and L3: verify in AWS.**

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your own clone). Branch **`feature/web-role-views-refusal`** from an up-to-date `develop`, after every dependency in [[Build order]] is merged. Never commit to, or push, `develop` or `main`; PR to `develop`; Patrick merges.
- **Start state:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` on `develop` with C1, F1a and F1b merged. The dry-run order also had F2 and F4a: `Test Files  33 passed (33)`, `Tests  101 passed (101)`. Without them the counts are lower; what must match is the **increase** each task states (+2, then +1). Write your start count in the ledger.
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
- **Stay in your files** (Clement's list in the brief). This item touches `web/src/app/core/session/permissions.ts` (+ spec) and `web/src/app/features/ask/` (store, panel, suggestions).
- **Cross-owner edits:** none.
- **Commits:** small, one per task, with the message given. **No `Co-Authored-By` and no "Generated with" lines** in commits or the PR.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **No scope in the request:** the E2 question sends exactly `{"entity_id": "E2", "question": "What is blocking cutover for entity 2?"}` (DevTools → Network in `http` mode, or read `pickSuggestion`): nothing about role or entities.
2. **The UI is not the gate:** nothing in `features/ask/` checks scope before calling the API (`grep -n "scopeAllows" web/src/app/features/ask -r` prints nothing).
3. **Mock walk-through:** CFO: the E2 suggestion gives the mock's partial answer (the CFO may ask about E2). Entity lead: the refusal. Delivery lead: `/approve/run-1` opens; CFO: `/approve/run-1` goes to sign-in with "Only a delivery lead can approve".
4. **Screen reader:** the refusal is announced (`role="status"`), and the asked question stays visible above it.
5. **Live Q11 (after F3a):** no E2 rows in the ledger for the refused run (Abdul's manual check; ask him for the result). Without Cognito the live API runs `AUTH_MODE=none`, whose demo user (L1's `DEMO_ROLE`, every entity) is never refused: the refusal is then mock-only, and Task 3 Step 3 records that.

---

### Task 1: The refusal wording and the store

**Files:** Modify `web/src/app/core/session/permissions.ts`, `permissions.spec.ts`, `web/src/app/features/ask/ask-store.ts`, `ask-store.spec.ts`.

**Produces:** `refusalMessage(scope: Scope, requestedEntityId: string): string`; `AskStore.refusal: Signal<string | undefined>`. **Consumes:** `ApiError.status` (F2), `SessionStore.scope()`, `scopeCoversAllEntities`.

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
git switch -c feature/web-role-views-refusal
mkdir -p .superpowers && printf '# Ledger: F3b role views and refusal\n' > .superpowers/ledger-F3b.md
(cd web && yarn install --frozen-lockfile)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
```
Expected: the start state (dry-run order: `Test Files  33 passed (33)`, `Tests  101 passed (101)`). Write it in the ledger.

- [ ] **Step 2: The failing tests.** Replace:
- `web/src/app/core/session/permissions.spec.ts`:
```ts
import { ROLES, Scope } from '../models';
import { canApprove, canPublish, refusalMessage } from './permissions';

const ENTITY_4_LEAD: Scope = { user_id: 'u-e4', role: 'entity_lead', tenant_id: 't-01', entity_ids: ['E4'] };
const ENTITY_2_AND_4_LEAD: Scope = { user_id: 'u-e2-e4', role: 'entity_lead', tenant_id: 't-01', entity_ids: ['E2', 'E4'] };
const CFO: Scope = { user_id: 'u-cfo', role: 'cfo', tenant_id: 't-01', entity_ids: ['*'] };

describe('permissions', () => {
  it('lets every signed-in role publish', () => {
    expect(ROLES.every(canPublish)).toBe(true);
  });

  it('lets only the delivery lead approve', () => {
    expect(ROLES.filter(canApprove)).toEqual(['delivery_lead']);
  });

  it('words a refusal by what the user may see (EVALS Q11)', () => {
    expect(refusalMessage(ENTITY_4_LEAD, 'E2')).toBe('You can see E4 only. E2 is outside your access.');
    expect(refusalMessage(ENTITY_2_AND_4_LEAD, 'E1')).toBe('You can see E2 and E4 only. E1 is outside your access.');
    expect(refusalMessage(CFO, 'E2')).toBe('E2 is outside your access.');
  });
});
```
- `web/src/app/features/ask/ask-store.spec.ts`:
```ts
import { TestBed } from '@angular/core/testing';

import { ApiError } from '../../core/api/api-error';
import { PortalApi } from '../../core/api/portal-api';
import askEntity4Fixture from '../../core/api/fixtures/ask-E4.json';
import { AskRequest, AskResponse, Scope } from '../../core/models';
import { SessionStore } from '../../core/session/session-store';
import { AskStore } from './ask-store';

const REQUEST: AskRequest = { entity_id: 'E4', question: 'What is blocking cutover for entity 4?' };
const ENTITY_4_LEAD: Scope = { user_id: 'u-e4', role: 'entity_lead', tenant_id: 't-01', entity_ids: ['E4'] };

function storeWith(ask: (request: AskRequest) => Promise<AskResponse>): AskStore {
  TestBed.configureTestingModule({ providers: [AskStore, { provide: PortalApi, useValue: { ask } }] });
  return TestBed.inject(AskStore);
}

describe('AskStore', () => {
  it('sends {entity_id, question} and holds the cited answer', async () => {
    const sent: AskRequest[] = [];
    const store = storeWith((request) => {
      sent.push(request);
      return Promise.resolve(askEntity4Fixture as unknown as AskResponse);
    });
    const asking = store.ask(REQUEST);
    expect(store.asking()).toBe(true);
    await asking;
    expect(sent).toEqual([REQUEST]);
    expect(store.asking()).toBe(false);
    expect(store.answer()?.bullets).toHaveLength(3);
    expect(store.lastRequest()).toEqual(REQUEST);
  });

  it('turns a 403 into a refusal that names what the user may see, not an error', async () => {
    const store = storeWith(() => Promise.reject(new ApiError(403, 'Entity E2 is outside your access.', 'out_of_scope')));
    TestBed.inject(SessionStore).setScope(ENTITY_4_LEAD);
    await store.ask({ entity_id: 'E2', question: 'What is blocking cutover for entity 2?' });
    expect(store.refusal()).toBe('You can see E4 only. E2 is outside your access.');
    expect(store.errorMessage()).toBeUndefined();
    expect(store.answer()).toBeUndefined();
  });

  it('shows other failures as an error and asks again on retry', async () => {
    let calls = 0;
    const store = storeWith(() =>
      ++calls === 1
        ? Promise.reject(new ApiError(502, 'The agent loop timed out.'))
        : Promise.resolve(askEntity4Fixture as unknown as AskResponse),
    );
    await store.ask(REQUEST);
    expect(store.errorMessage()).toBe('The agent loop timed out.');
    await store.retry();
    expect(calls).toBe(2);
    expect(store.errorMessage()).toBeUndefined();
    expect(store.answer()).toBeDefined();
  });
});
```

- [ ] **Step 3: Run them**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/session --include src/app/features/ask/ask-store.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: the build fails with `✘ [ERROR] TS2305: Module '"./permissions"' has no exported member 'refusalMessage'.` and `✘ [ERROR] TS2339: Property 'refusal' does not exist on type 'AskStore'.`

- [ ] **Step 4: Implement.** Replace:
- `web/src/app/core/session/permissions.ts`:
```ts
/**
 * Who may do what in the portal. The only place these rules live.
 * The server enforces them again; the UI uses them to hide what it would refuse.
 */
import { Role, Scope, scopeCoversAllEntities } from '../models';

/** Publishing a status pack only starts the approval flow; nothing is written until a delivery lead approves. */
const PUBLISHER_ROLES: readonly Role[] = ['cfo', 'sponsor', 'delivery_lead', 'entity_lead'];

/** Only the delivery lead approves or sends back a status pack (ARCHITECTURE.md §2). */
const APPROVER_ROLES: readonly Role[] = ['delivery_lead'];

export function canPublish(role: Role): boolean {
  return PUBLISHER_ROLES.includes(role);
}

export function canApprove(role: Role): boolean {
  return APPROVER_ROLES.includes(role);
}

/** How the UI words a 403 (EVALS Q11): what the user may see, then what they asked for. The API already refused it. */
export function refusalMessage(scope: Scope, requestedEntityId: string): string {
  const refused = `${requestedEntityId} is outside your access.`;
  if (scopeCoversAllEntities(scope)) return refused;
  const visible = scope.entity_ids.length === 1
    ? scope.entity_ids[0]
    : `${scope.entity_ids.slice(0, -1).join(', ')} and ${scope.entity_ids[scope.entity_ids.length - 1]}`;
  return `You can see ${visible} only. ${refused}`;
}
```
- `web/src/app/features/ask/ask-store.ts`:
```ts
import { Injectable, computed, inject, signal } from '@angular/core';

import { ApiError } from '../../core/api/api-error';
import { PortalApi } from '../../core/api/portal-api';
import { AskRequest, AskResponse } from '../../core/models';
import { refusalMessage } from '../../core/session/permissions';
import { SessionStore } from '../../core/session/session-store';
import { buildAnswerView } from './answer-view';

type AskStatus = 'idle' | 'asking' | 'answered' | 'refused' | 'failed';

interface AskState {
  status: AskStatus;
  request?: AskRequest;
  response?: AskResponse;
  errorMessage?: string;
  refusal?: string;
}

const ASK_ERROR_MESSAGE = 'The question could not be answered. Try again in a moment.';
const HTTP_FORBIDDEN = 403;

/** One question at a time to POST /ask, and its answer, refusal (403) or error. */
@Injectable()
export class AskStore {
  private readonly api = inject(PortalApi);
  private readonly session = inject(SessionStore);
  private readonly state = signal<AskState>({ status: 'idle' });

  readonly asking = computed(() => this.state().status === 'asking');
  readonly lastRequest = computed(() => this.state().request);
  readonly answer = computed(() => {
    const response = this.state().response;
    return response ? buildAnswerView(response) : undefined;
  });
  readonly errorMessage = computed(() => this.state().errorMessage);
  readonly refusal = computed(() => this.state().refusal);

  async ask(request: AskRequest): Promise<void> {
    this.state.set({ status: 'asking', request });
    try {
      const response = await this.api.ask(request);
      this.state.set({ status: 'answered', request, response });
    } catch (error) {
      if (error instanceof ApiError && error.status === HTTP_FORBIDDEN) {
        this.state.set({ status: 'refused', request, refusal: refusalMessage(this.session.scope(), request.entity_id) });
        return;
      }
      const errorMessage = error instanceof ApiError ? error.message : ASK_ERROR_MESSAGE;
      this.state.set({ status: 'failed', request, errorMessage });
    }
  }

  retry(): Promise<void> {
    const request = this.state().request;
    return request ? this.ask(request) : Promise.resolve();
  }
}
```

- [ ] **Step 5: Run, suite, commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/session --include src/app/features/ask/ask-store.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
git add web/src/app/core/session web/src/app/features/ask/ask-store.ts web/src/app/features/ask/ask-store.spec.ts
git commit -m "A 403 from /ask is a refusal that says what the user may see (EVALS Q11)"
```
Expected: `Test Files  2 passed (2)`, `Tests  6 passed (6)`; then the suite at **start + 2** (dry-run: `Test Files  33 passed (33)`, `Tests  103 passed (103)`).

**Task done when:** `refusalMessage` returns the three wordings of the spec; the suite is at start + 2.

### Task 2: Ask about E2 from the panel, and show the refusal

**Files:** Modify `web/src/app/features/ask/suggested-questions/suggested-questions.ts`, `ask-panel/ask-panel.ts`, `ask-panel/ask-panel.html`, `ask-panel/ask-panel.scss`. Create `web/src/app/features/ask/ask-panel/ask-panel.spec.ts` *(new)*.

**Consumes:** F1b's `summary-entity-lead-E4.json`, `providePortalApi()`, `DEMO_SCOPES`.

- [ ] **Step 1: The failing test.** Create `web/src/app/features/ask/ask-panel/ask-panel.spec.ts`:
```ts
import { ApplicationRef } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import entity4LeadSummary from '../../../core/api/fixtures/summary-entity-lead-E4.json';
import { providePortalApi } from '../../../core/api/provide-portal-api';
import { PORTAL_CONFIG, PORTAL_CONFIG_VALUES } from '../../../core/config/portal-config';
import { SummaryResponse } from '../../../core/models';
import { DEMO_SCOPES, SessionStore } from '../../../core/session/session-store';
import { AskPanel } from './ask-panel';

/** Rendering pulls in the ADS wrapper, which can be slow on a busy machine. */
const PAGE_TIMEOUT_MS = 30_000;

describe('AskPanel as the E4 entity lead (EVALS Q11)', () => {
  it('asks about E2 and shows a clear refusal instead of an error', async () => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        providePortalApi(),
        { provide: PORTAL_CONFIG, useValue: { ...PORTAL_CONFIG_VALUES, dataSource: 'mock', mockLatencyMs: 0 } },
      ],
    });
    TestBed.inject(SessionStore).setScope(DEMO_SCOPES.find((scope) => scope.role === 'entity_lead')!);
    const fixture = TestBed.createComponent(AskPanel);
    fixture.componentRef.setInput('entities', (entity4LeadSummary as unknown as SummaryResponse).entities);
    await fixture.whenStable();

    const element = fixture.nativeElement as HTMLElement;
    const suggestion = [...element.querySelectorAll<HTMLButtonElement>('app-suggested-questions button')].find(
      (button) => button.textContent?.trim() === 'What is blocking cutover for entity 2?',
    );
    suggestion?.click();
    await fixture.whenStable();
    await TestBed.inject(ApplicationRef).whenStable();
    await fixture.whenStable();

    expect(element.querySelector('[role="status"].refusal')?.textContent?.trim()).toBe(
      'You can see E4 only. E2 is outside your access.',
    );
    expect(element.querySelector('app-load-error')).toBeNull();
  }, PAGE_TIMEOUT_MS);
});
```

- [ ] **Step 2: Run it**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/features/ask/ask-panel 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: `Tests  1 failed (1)` with `AssertionError: expected undefined to be 'You can see E4 only. E2 is outside yo…' // Object.is equality` (Vitest truncates the string) (there is no E2 suggestion yet).

- [ ] **Step 3: Implement.**
- In `web/src/app/features/ask/suggested-questions/suggested-questions.ts`, replace
```ts
/** The design's starter questions. EVALS Q01 is the entity 4 one. */
export const SUGGESTED_QUESTIONS: readonly SuggestedQuestion[] = [
  { text: 'Are we on track for the final cutover?' },
  { text: 'How much is left to reconcile?' },
  { text: 'What is blocking cutover for entity 4?', entityId: 'E4' },
];
```
  with
```ts
/** The design's starter questions. EVALS Q01 is the entity 4 one; the entity 2 one shows the Q11 refusal to the E4 lead. */
export const SUGGESTED_QUESTIONS: readonly SuggestedQuestion[] = [
  { text: 'Are we on track for the final cutover?' },
  { text: 'How much is left to reconcile?' },
  { text: 'What is blocking cutover for entity 4?', entityId: 'E4' },
  { text: 'What is blocking cutover for entity 2?', entityId: 'E2' },
];
```
- In `web/src/app/features/ask/ask-panel/ask-panel.ts`, replace
```ts
  protected pickSuggestion(suggestion: SuggestedQuestion): void {
    const knownEntity = this.entities().some((entity) => entity.entity_id === suggestion.entityId);
    this.form.patchValue({
      question: suggestion.text,
      ...(suggestion.entityId && knownEntity ? { entity: suggestion.entityId } : {}),
    });
    this.submit();
  }
```
  with
```ts
  /**
   * Asks the suggestion about its own entity even when that entity is not in the picker: the API is the gate, and
   * its 403 shows as a refusal (EVALS Q11). The UI never decides what the user may ask.
   */
  protected pickSuggestion(suggestion: SuggestedQuestion): void {
    const entityId = suggestion.entityId ?? this.entityId();
    const visible = this.entities().some((entity) => entity.entity_id === entityId);
    this.form.patchValue({ question: suggestion.text, ...(visible ? { entity: entityId } : {}) });
    if (this.store.asking() || entityId === '') return;
    void this.store.ask({ entity_id: entityId, question: suggestion.text });
  }
```
- In `web/src/app/features/ask/ask-panel/ask-panel.html`, replace
```html
  } @else if (store.errorMessage(); as message) {
```
  with
```html
  } @else if (store.refusal(); as refusal) {
    <p class="refusal" role="status">{{ refusal }}</p>
  } @else if (store.errorMessage(); as message) {
```
- Append to `web/src/app/features/ask/ask-panel/ask-panel.scss`:
```scss

// A 403 is an answer, not a failure: a calm notice, no Retry (EVALS Q11).
.refusal {
  padding: var(--portal-space-3) var(--portal-space-4);
  border-left: 3px solid var(--portal-color-primary);
  border-radius: var(--portal-radius-control);
  background: var(--portal-color-surface-muted);
  color: var(--portal-color-primary);
  font-size: var(--portal-font-size-sm);
}
```

- [ ] **Step 4: Run, suite, build, commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/features/ask/ask-panel 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
(cd web && yarn build 2>&1 | grep -E "ERROR|WARN|bundle generation complete")
git add web/src/app/features/ask
git commit -m "The E4 lead can ask about E2 and sees a clear refusal, not an error"
```
Expected: `Tests  1 passed (1)`; the suite at **start + 3** (dry-run: `Test Files  34 passed (34)`, `Tests  104 passed (104)`); the build prints `Application bundle generation complete.` and no `WARN` about component style budgets.

**Task done when:** the E4 lead sees the refusal in mock mode (`yarn start` → Switch user → Entity lead → the E2 suggestion); the suite is at start + 3.

### Task 3: Role views, by hand, then live
- [ ] **Step 1 (mock):** `(cd web && yarn start)`. Switch user → Entity lead. Expected: the entities table has one row, "Entity 4"; the KPI row shows 19%, 95%, 3; the ask picker offers only Entity 4. Switch user → CFO: four rows. Open http://localhost:4200/approve/run-1 as the CFO: the sign-in page says "Only a delivery lead can approve a status pack."; as the delivery lead: the approve page with "Approve" and "Send back".
- [ ] **Step 2 (verify in AWS, after F3a is merged and `authMode` is `cognito`):** sign in as `demo-entity-lead-e4` (Abdul's A2 test user); click the E2 suggestion. Expected: Network shows `POST /api/ask` → **403**; the panel shows "You can see E4 only. E2 is outside your access." Record in the ledger: `Task 3: live Q11 refusal — <date time>`; ask Abdul to confirm no E2 ledger rows for that time.

- [ ] **Step 3 (verify in AWS, only if the Cognito go/no-go was no-go, so the API runs `AUTH_MODE=none`):** in the deployed app, Switch user → Entity lead and click the E2 suggestion. Expected: `POST /api/ask` → **200** (the server's demo user is L1's `DEMO_ROLE`, `cfo` by default or `delivery_lead` for the approval demo, over every entity; the switcher is display only), so no refusal live. Record `Task 3: AUTH_MODE=none (DEMO_ROLE=<value>), live refusal not possible; refusal shown in mock mode` in the ledger, and tell Patrick so HANDOFF says the Q11 demo is mock-only.

**Task done when:** Step 1's screens match; Step 2's ledger line exists, or (Cognito go/no-go at D2 12:00 was no-go) Step 3's ledger line exists.

### Task 4: Review, then PR (after Clement's OK)
- [ ] **Step 1:** Work through the Review Focus by hand; write each result in the ledger.
- [ ] **Step 2:** `git diff develop --stat` lists only the files this plan names.
- [ ] **Step 3:** Fresh review of the diff against [[F3b - Role views and the 403 refusal - spec]] (another person, or an agent with no prior context); fix critical and important findings test-first; list minor ones in the PR.
- [ ] **Step 4 (with Clement's OK only):** `git push -u origin feature/web-role-views-refusal`; open the PR to `develop` titled "Front end: role views and a clear 403 refusal (F3b)". Body: what changed, the suite count (start + 3), the `Ruling:` lines, deferred minors. No attribution lines.
- [ ] **Step 5:** [[Build order]] row F3: `in review (PR #nn)`, then `merged` when Patrick merges.

**Task done when:** the PR is open to `develop`, Jenkins' front-end build is green, and [[Build order]] shows `in review (PR #nn)`.

## Never
- Compute a KPI, a status or a date in the browser; show what the API returns.
- Send scope (role, entities, tenant) in a request body, query string or header.
- Log, print or store a token yourself.
- Add a `package-lock.json`, or change `yarn.lock` other than with `yarn add`.
- Commit the npm token, a password or any secret.
- Push to `develop` or `main`, or add attribution lines.
- Decide in the browser whether a user may ask about an entity; the API decides.
- Show a refusal as an error with Retry.

## Done means
- [ ] **Tests:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` → start + 3 (dry-run: `Tests  104 passed (104)`). *Verify:* run it; compare with the ledger's start count.
- [ ] **Refusal unit:** `(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/session/permissions.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)` → `Tests  3 passed (3)`. *Verify:* run it.
- [ ] **Q11 in mock:** Entity lead + E2 suggestion → "You can see E4 only. E2 is outside your access." and no red error box. *Verify:* `yarn start`.
- [ ] **Role views:** Entity lead sees one entity row; CFO is sent to sign-in from `/approve/run-1`. *Verify:* Task 3 Step 1.
- [ ] **Live Q11 (verify in AWS, after F3a):** 403 in Network and the refusal on screen; ledger line. *Verify:* Task 3 Step 2. If Cognito is off: the ledger has Task 3 Step 3's `AUTH_MODE=none (DEMO_ROLE=...)` line instead.
- [ ] **PR:** open to `develop` titled "Front end: role views and a clear 403 refusal (F3b)"; [[Build order]] updated. *Verify:* `gh pr list --head feature/web-role-views-refusal`.

Related: [[F3b - Role views and the 403 refusal - spec]], [[Build order]], [[How to execute a plan]]
