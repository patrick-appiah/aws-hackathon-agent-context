---
tags: [build, plan, area/frontend]
id: F5
owner: Clement
spec: "[[F5 - Publish and approve on the real API - spec]]"
status: ready
updated: 2026-10-14
---
# F5: publish and approve on the real API (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[F5 - Publish and approve on the real API - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger as a `Ruling:` line.
3. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Clement - front end]].
4. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
5. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
6. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

**Goal:** publish and approve speak C1's contract (keyed by `run_id`), show the API's status, and work end to end against the live API.

**Architecture:** `AnswerCard (publish)` → `/publish/:runId` → `PublishStore.publish` → `PortalApi.publish` → link `/approve/:runId` → `approverGuard` → `ApprovePage` → `PublishStore.decide` → `PortalApi.approve` → badge from `ApproveResponse.status`.

**Tech stack:** Angular 22, TypeScript 6, Vitest through `ng test`.

**Dry-run:** Task 1 was run on 2026-10-14 in a throwaway worktree with C1, F1a, F1b, F2, F4a and F3b applied; counts and messages are real. **Task 2 needs the deployed API and, for approve, Cognito (F3a) or the `AUTH_MODE=none` + `DEMO_ROLE=delivery_lead` fallback (L1): verify in AWS.**

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your own clone). Branch **`feature/web-publish-approve`** from an up-to-date `develop`, after every dependency in [[Build order]] is merged. Never commit to, or push, `develop` or `main`; PR to `develop`; Patrick merges.
- **Start state:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` on `develop` with C1, F1a and F1b merged. Dry-run order (with F2, F4a, F3b): `Test Files  34 passed (34)`, `Tests  104 passed (104)`. What must match is the increase: **+1 file, +3 tests**. Write your start count in the ledger.
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
- **Stay in your files** (Clement's list in the brief). This item touches `web/src/app/core/models/publish.ts`, `web/src/app/features/publish/`, `web/src/app/app.routes.ts` (the approve route), and Mildred's files below.
- **Cross-owner edits:** **Mildred's** `web/src/app/core/api/fixtures/publish.json`, `approve.json`, `core/api/mock-portal-api.ts` (publish and approve methods), `mock-portal-api.spec.ts` (one test) and `http-portal-api.spec.ts` (the approve body): exactly the edits in Task 1; ask her first.
- **Commits:** small, one per task, with the message given. **No `Co-Authored-By` and no "Generated with" lines** in commits or the PR.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **The badge is the API's status:** read `approve-page.ts`: `outcome` reads `store.approved().status`, never the button.
2. **No `execution_arn` left in a link or a route:** `grep -rn "executionArn\|execution_arn" web/src/app --include=*.ts --include=*.html | grep -v "models/publish.ts\|spec.ts\|publish-page.html"` prints nothing (the publish page may still show the execution for reference).
3. **Mock walk-through** (`yarn start`): CFO asks the entity 4 question → "Publish as status pack" → "Send for approval" → "Awaiting approval" → "Open the approval" → sign-in page "Only a delivery lead can approve". Switch user → Delivery lead → open `/approve/run-mock-e4-0001` → Send back with a note → "Sent back".
4. **The note is sent as typed, trimmed, and capped by the API** (C1: `note` ≤ 1,000 characters): a 1,200-character note gets the API's 400 `invalid_input` detail on screen, live.
5. **Live:** after Approve, `aws s3 ls s3://<bucket>/status-packs/ --profile hackathon --region eu-west-1` lists one new object for the run; after Send back, none.

---

### Task 1: Publish and approve on the contract

**Files:**
- Modify: `web/src/app/core/models/publish.ts`, `web/src/app/features/publish/publish-store.ts`, `…/publish-store.spec.ts`, `…/publish-pages.spec.ts`, `…/approve-page.ts`, `…/approve-page.html`, `…/publish-page.html`, `web/src/app/app.routes.ts`
- Modify (Mildred's, agreed): `web/src/app/core/api/fixtures/publish.json`, `approve.json`, `core/api/mock-portal-api.ts`, `mock-portal-api.spec.ts`, `http-portal-api.spec.ts`
- Create: `web/src/app/features/publish/publish-fixtures.spec.ts` *(new)*

**Produces:** `PublishResponse`, `ApproveRequest`, `ApproveResponse`, `ApprovalStatus`, `APPROVAL_STATUS_BY_DECISION`; `PublishStore.decide(runId: string, decision: ApprovalDecision, note: string): Promise<void>`; `ApprovePage.runId` input; route `approve/:runId`.

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
git switch -c feature/web-publish-approve
mkdir -p .superpowers && printf '# Ledger: F5 publish and approve\n' > .superpowers/ledger-F5.md
(cd web && yarn install --frozen-lockfile)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
```
Expected: the start state (dry-run order: `Test Files  34 passed (34)`, `Tests  104 passed (104)`).

- [ ] **Step 2: The fixtures.** Replace:
- `web/src/app/core/api/fixtures/publish.json`:
```json
{
  "_mock": "Mock response for UI development; not produced by the agent loop or Step Functions.",
  "run_id": "run-mock-e4-0001",
  "execution_arn": "arn:aws:states:eu-west-1:000000000000:execution:mock-status-pack:run-mock-e4-0001",
  "status": "awaiting_approval"
}
```
- `web/src/app/core/api/fixtures/approve.json`:
```json
{
  "_mock": "Mock response for UI development; not produced by the agent loop or Step Functions.",
  "run_id": "run-mock-e4-0001",
  "status": "approved"
}
```

- [ ] **Step 3: The failing tests.** Create or replace:
- `web/src/app/features/publish/publish-fixtures.spec.ts`:
```ts
import approveFixture from '../../core/api/fixtures/approve.json';
import publishFixture from '../../core/api/fixtures/publish.json';
import { contractErrors } from '../../core/api/testing/contract-validator';

/** The fixtures' `_mock` note is the only key the API would never send. */
function withoutMockNote(fixture: object): object {
  return Object.fromEntries(Object.entries(fixture).filter(([key]) => key !== '_mock'));
}

describe('publish and approve fixtures', () => {
  it('match the POST /publish and POST /approve response contracts', () => {
    expect(contractErrors('publish_response', withoutMockNote(publishFixture))).toEqual([]);
    expect(contractErrors('approve_response', withoutMockNote(approveFixture))).toEqual([]);
  });

  it('the requests the portal sends match their contracts', () => {
    expect(contractErrors('publish_request', { run_id: 'run-mock-e4-0001' })).toEqual([]);
    expect(contractErrors('approve_request', { run_id: 'run-mock-e4-0001', decision: 'send_back', note: 'Recheck E4' })).toEqual([]);
  });
});
```
- `web/src/app/features/publish/publish-store.spec.ts`:
```ts
import { TestBed } from '@angular/core/testing';

import { ApiError } from '../../core/api/api-error';
import { PortalApi } from '../../core/api/portal-api';
import { ApproveRequest, PublishRequest } from '../../core/models';
import { PublishStore } from './publish-store';

const RUN_ID = 'run-1';
const EXECUTION_ARN = 'arn:aws:states:eu-west-1:000000000000:execution:publish:run-1';

describe('PublishStore', () => {
  const published: PublishRequest[] = [];
  const decided: ApproveRequest[] = [];

  function storeWith(api: Partial<PortalApi>): PublishStore {
    TestBed.configureTestingModule({ providers: [PublishStore, { provide: PortalApi, useValue: api }] });
    return TestBed.inject(PublishStore);
  }

  it('sends the run for approval and holds its run ID and execution', async () => {
    const store = storeWith({
      publish: (request) => {
        published.push(request);
        return Promise.resolve({ run_id: request.run_id, execution_arn: EXECUTION_ARN, status: 'awaiting_approval' });
      },
    });
    await store.publish(RUN_ID);
    expect(published).toEqual([{ run_id: RUN_ID }]);
    expect(store.published()).toEqual({ run_id: RUN_ID, execution_arn: EXECUTION_ARN, status: 'awaiting_approval' });
  });

  it('records a decision by run ID, with its note, and holds the status the API returns', async () => {
    const store = storeWith({
      approve: (request) => {
        decided.push(request);
        return Promise.resolve({ run_id: request.run_id, status: 'sent_back' });
      },
    });
    await store.decide(RUN_ID, 'send_back', 'Recheck the E4 customer figures');
    expect(decided).toEqual([{ run_id: RUN_ID, decision: 'send_back', note: 'Recheck the E4 customer figures' }]);
    expect(store.decision()).toBe('send_back');
    expect(store.approved()).toEqual({ run_id: RUN_ID, status: 'sent_back' });
  });

  it('shows the API refusal message', async () => {
    const store = storeWith({ publish: () => Promise.reject(new ApiError(403, 'Not allowed to publish.', 'forbidden')) });
    await store.publish(RUN_ID);
    expect(store.publishError()).toBe('Not allowed to publish.');
  });
});
```
- `web/src/app/features/publish/publish-pages.spec.ts`:
```ts
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { PortalApi } from '../../core/api/portal-api';
import { ApproveRequest, PublishRequest, Role, Scope } from '../../core/models';
import { SessionStore } from '../../core/session/session-store';
import { ApprovePage } from './approve-page';
import { PublishPage } from './publish-page';

/** Rendering pulls in the ADS wrapper, which can be slow on a busy machine. */
const PAGE_TIMEOUT_MS = 30_000;
const RUN_ID = 'run-mock-e4-0001';

/** The ADS badge draws its text in its shadow root; its `text` property is what it shows. */
function badgeTexts(element: HTMLElement): (string | undefined)[] {
  return [...element.querySelectorAll('app-tone-badge at-badge')].map((badge) => (badge as HTMLElement & { text?: string }).text);
}

function signInAs(role: Role): void {
  const scope: Scope = { user_id: `u-${role}`, role, tenant_id: 't-01', entity_ids: ['*'] };
  TestBed.inject(SessionStore).setScope(scope);
}

describe('publish and approve pages', () => {
  const api = {
    publish: (request: PublishRequest) =>
      Promise.resolve({ run_id: request.run_id, execution_arn: 'arn-mock', status: 'awaiting_approval' as const }),
    approve: (request: ApproveRequest) =>
      Promise.resolve({ run_id: request.run_id, status: request.decision === 'approve' ? ('approved' as const) : ('sent_back' as const) }),
  };

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideRouter([]), { provide: PortalApi, useValue: api }] });
  });

  it('sends a run for approval, then shows "Awaiting approval" and links the approval by run ID', async () => {
    signInAs('entity_lead');
    const fixture = TestBed.createComponent(PublishPage);
    fixture.componentRef.setInput('runId', RUN_ID);
    await fixture.whenStable();
    const element = fixture.nativeElement as HTMLElement;
    expect(element.textContent).toContain('Send for approval');

    element.querySelector<HTMLElement>('.portal-actions at-button')?.dispatchEvent(new CustomEvent('atClick'));
    await fixture.whenStable();
    expect(badgeTexts(element)).toEqual(['Awaiting approval']);
    expect(element.querySelector('a[href="/approve/run-mock-e4-0001"]')).not.toBeNull();
  }, PAGE_TIMEOUT_MS);

  it('shows the approve controls to the delivery lead only', async () => {
    signInAs('cfo');
    const cfoView = TestBed.createComponent(ApprovePage);
    cfoView.componentRef.setInput('runId', RUN_ID);
    await cfoView.whenStable();
    expect((cfoView.nativeElement as HTMLElement).textContent).toContain('Only a delivery lead can approve');
    expect((cfoView.nativeElement as HTMLElement).querySelector('at-textarea')).toBeNull();

    signInAs('delivery_lead');
    const leadView = TestBed.createComponent(ApprovePage);
    leadView.componentRef.setInput('runId', RUN_ID);
    await leadView.whenStable();
    expect((leadView.nativeElement as HTMLElement).querySelector('at-textarea')).not.toBeNull();
    expect((leadView.nativeElement as HTMLElement).textContent).toContain('Send back');
  }, PAGE_TIMEOUT_MS);

  it('shows the status the API returns after the delivery lead sends a pack back', async () => {
    signInAs('delivery_lead');
    const fixture = TestBed.createComponent(ApprovePage);
    fixture.componentRef.setInput('runId', RUN_ID);
    await fixture.whenStable();
    const element = fixture.nativeElement as HTMLElement;
    const sendBack = [...element.querySelectorAll<HTMLElement>('.portal-actions at-button')].find((button) =>
      button.textContent?.includes('Send back'),
    );
    sendBack?.dispatchEvent(new CustomEvent('atClick'));
    await fixture.whenStable();
    expect(badgeTexts(element)).toEqual(['Sent back']);
    expect(element.textContent).toContain('Status from the API: sent_back');
  }, PAGE_TIMEOUT_MS);
});
```
- In `web/src/app/core/api/mock-portal-api.spec.ts`, replace
```ts
  it('publishes and approves', async () => {
    expect((await api.publish({ run_id: 'run-mock-e4-0001' })).status).toBe('awaiting_approval');
    expect((await api.approve({ execution_arn: 'arn', decision: 'approve', note: '' })).status).toBe('approved');
  });
```
  with
```ts
  it('publishes and approves by run ID, answering with the status each decision leads to', async () => {
    expect(await api.publish({ run_id: 'run-7' })).toMatchObject({ run_id: 'run-7', status: 'awaiting_approval' });
    expect(await api.approve({ run_id: 'run-7', decision: 'approve', note: '' })).toEqual({ run_id: 'run-7', status: 'approved' });
    expect(await api.approve({ run_id: 'run-7', decision: 'send_back', note: 'Recheck E4' })).toEqual({ run_id: 'run-7', status: 'sent_back' });
  });
```
- In `web/src/app/core/api/http-portal-api.spec.ts`, replace
```ts
    const approved = api.approve({ execution_arn: 'arn-1', decision: 'send_back', note: 'Recheck E4' });
    const approveRequest = http.expectOne({ method: 'POST', url: `${BASE_URL}/approve` });
    expect(approveRequest.request.body).toEqual({ execution_arn: 'arn-1', decision: 'send_back', note: 'Recheck E4' });
```
  with
```ts
    const approved = api.approve({ run_id: 'run-1', decision: 'send_back', note: 'Recheck E4' });
    const approveRequest = http.expectOne({ method: 'POST', url: `${BASE_URL}/approve` });
    expect(approveRequest.request.body).toEqual({ run_id: 'run-1', decision: 'send_back', note: 'Recheck E4' });
```

- [ ] **Step 4: Run them**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "ERROR\\]" | sort | uniq -c)
```
Expected: the build fails (no test runs). The errors include `✘ [ERROR] TS2339: Property 'run_id' does not exist on type 'ApproveRequest'.` and `✘ [ERROR] TS2353: Object literal may only specify known properties, and 'run_id' does not exist in type 'ApproveRequest'.` (and the same `TS2353` for `PublishResponse` and `ApproveResponse`). Every error names `run_id`; any other error: stop.

- [ ] **Step 5: Implement.** Replace `web/src/app/core/models/publish.ts`:
```ts
/** POST /publish and POST /approve (tools/api_schema.py, D-021). Approvals are keyed by `run_id`. */

export interface PublishRequest {
  run_id: string;
}

export interface PublishResponse {
  run_id: string;
  execution_arn: string;
  status: 'awaiting_approval';
}

export type ApprovalDecision = 'approve' | 'send_back';

export type ApprovalStatus = 'approved' | 'sent_back';

/** The status each decision leads to (the mock API answers with it; the real API returns it). */
export const APPROVAL_STATUS_BY_DECISION: Record<ApprovalDecision, ApprovalStatus> = {
  approve: 'approved',
  send_back: 'sent_back',
};

export interface ApproveRequest {
  run_id: string;
  decision: ApprovalDecision;
  note: string;
}

export interface ApproveResponse {
  run_id: string;
  status: ApprovalStatus;
}
```
Then:
- In `web/src/app/features/publish/publish-store.ts`, replace
```ts
  async decide(executionArn: string, decision: ApprovalDecision, note: string): Promise<void> {
```
  with
```ts
  async decide(runId: string, decision: ApprovalDecision, note: string): Promise<void> {
```
- In `web/src/app/features/publish/publish-store.ts`, replace
```ts
await this.api.approve({ execution_arn: executionArn, decision, note });
```
  with
```ts
await this.api.approve({ run_id: runId, decision, note });
```
- In `web/src/app/features/publish/approve-page.ts`, replace
```ts
import { ApprovalDecision } from '../../core/models';
```
  with
```ts
import { ApprovalDecision, ApprovalStatus } from '../../core/models';
```
- In `web/src/app/features/publish/approve-page.ts`, replace
```ts
const DECISION_LABELS: Record<ApprovalDecision, { text: string; tone: Tone }> = {
  approve: { text: 'Approved', tone: 'success' },
  send_back: { text: 'Sent back', tone: 'warning' },
};
```
  with
```ts
/** How each status the API returns is shown. */
const STATUS_LABELS: Record<ApprovalStatus, { text: string; tone: Tone }> = {
  approved: { text: 'Approved', tone: 'success' },
  sent_back: { text: 'Sent back', tone: 'warning' },
};
```
- In `web/src/app/features/publish/approve-page.ts`, replace
```ts
  /** From the route: /approve/:executionArn */
  readonly executionArn = input.required<string>();
```
  with
```ts
  /** From the route: /approve/:runId */
  readonly runId = input.required<string>();
```
- In `web/src/app/features/publish/approve-page.ts`, replace
```ts
  protected readonly outcome = computed(() => {
    const decision = this.store.decision();
    return this.store.approved() && decision ? DECISION_LABELS[decision] : undefined;
  });
```
  with
```ts
  protected readonly outcome = computed(() => {
    const approved = this.store.approved();
    return approved ? STATUS_LABELS[approved.status] : undefined;
  });
```
- In `web/src/app/features/publish/approve-page.ts`, replace
```ts
void this.store.decide(this.executionArn(), decision, adsFieldValue(this.note.value).trim());
```
  with
```ts
void this.store.decide(this.runId(), decision, adsFieldValue(this.note.value).trim());
```
- In `web/src/app/features/publish/approve-page.html`, replace
```html
<p>Execution <code>{{ executionArn() }}</code></p>
```
  with
```html
<p>Run <code>{{ runId() }}</code></p>
```
- In `web/src/app/features/publish/publish-page.html`, replace
```html
<a class="portal-back-link" [routerLink]="['/approve', published.execution_arn]">Open the approval</a>
```
  with
```html
<a class="portal-back-link" [routerLink]="['/approve', published.run_id]">Open the approval</a>
```
- In `web/src/app/app.routes.ts`, replace
```ts
path: 'approve/:executionArn',
```
  with
```ts
path: 'approve/:runId',
```
- In `web/src/app/core/api/mock-portal-api.ts`, replace
```ts
  ApproveRequest,
  ApproveResponse,
```
  with
```ts
  APPROVAL_STATUS_BY_DECISION,
  ApproveRequest,
  ApproveResponse,
```
- In `web/src/app/core/api/mock-portal-api.ts`, replace
```ts
  override async publish(_request: PublishRequest): Promise<PublishResponse> {
    return withoutFixtureNotes<PublishResponse>(await this.load(() => import('./fixtures/publish.json')));
  }

  override async approve(_request: ApproveRequest): Promise<ApproveResponse> {
    return withoutFixtureNotes<ApproveResponse>(await this.load(() => import('./fixtures/approve.json')));
  }
```
  with
```ts
  /** The fixture's shape, for the run that was published. */
  override async publish(request: PublishRequest): Promise<PublishResponse> {
    const fixture = withoutFixtureNotes<PublishResponse>(await this.load(() => import('./fixtures/publish.json')));
    return { ...fixture, run_id: request.run_id };
  }

  /** The fixture's shape, with the status the decision leads to. */
  override async approve(request: ApproveRequest): Promise<ApproveResponse> {
    await this.load(() => import('./fixtures/approve.json'));
    return { run_id: request.run_id, status: APPROVAL_STATUS_BY_DECISION[request.decision] };
  }
```

- [ ] **Step 6: Run, suite, build, commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/features/publish 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
(cd web && yarn build 2>&1 | grep -E "ERROR|bundle generation complete")
git add web/src/app/core/models/publish.ts web/src/app/features/publish web/src/app/app.routes.ts web/src/app/core/api
git commit -m "Publish and approve on the contract: keyed by run_id, the badge shows the API's status"
```
Expected: `Test Files  3 passed (3)`, `Tests  8 passed (8)`; the suite at **start + 1 file, + 3 tests** (dry-run: `Test Files  35 passed (35)`, `Tests  107 passed (107)`); the build prints `Application bundle generation complete.`

**Task done when:** the suite is at start + 3; the mock walk-through in Review Focus 3 works.

### Task 2: Publish → approve live (verify in AWS; not dry-run)
Needs: L3 and H4 merged and deployed, Y2's publish machine, F2's `"dataSource": "http"`, and for the approve step **either** F3a with `authMode: cognito` (Steps 1–4, Abdul's test users; passwords are given out of band, never written down) **or**, if the Cognito go/no-go was no-go, the demo-only fallback of the spec's assumption: Yaw sets `AUTH_MODE=none` and `DEMO_ROLE=delivery_lead` on every API Lambda (L1's `DEMO_ROLE` setting), and you do Step 5 instead of Steps 2–4.

- [ ] **Step 1: Publish as any user.** Ask the entity 4 question, press "Publish as status pack", then "Send for approval". Expected: Network `POST /api/publish` → 200 `{"run_id": "<run>", "execution_arn": "arn:aws:states:eu-west-1:796973512193:execution:…", "status": "awaiting_approval"}`; the page shows "Awaiting approval".
- [ ] **Step 2: Approve as the delivery lead.** Sign out, sign in as `demo-delivery-lead` (A2), open `https://<cf>/approve/<run>`, write a note, press Approve. Expected: `POST /api/approve` → 200 `{"run_id": "<run>", "status": "approved"}`; badge "Approved"; `aws s3 ls s3://<bucket>/status-packs/ --profile hackathon --region eu-west-1` lists one new object for `<run>`.
- [ ] **Step 3: Send back** (a second published run): Send back with a note. Expected: `{"status": "sent_back"}`, badge "Sent back", no new object under `status-packs/`.
- [ ] **Step 4: Refused approver:** as `demo-cfo`, `POST /api/approve` from the page's URL is never reached (the guard sends the CFO to sign-in); with `curl` and the CFO's ID token it returns 403 `forbidden`. Record all four results in the ledger with the run IDs.
- [ ] **Step 5 (only if Cognito is off: `AUTH_MODE=none`, `DEMO_ROLE=delivery_lead`):** in the app, Switch user → Delivery lead (display only; the API serves `demo-delivery_lead` whatever the switcher says). Ask the entity 4 question, publish it (Step 1), open "Open the approval", write a note, press Approve. Expected: `POST /api/approve` → 200 `{"run_id": "<run>", "status": "approved"}`; badge "Approved"; one new object for `<run>` under `status-packs/` (same `aws s3 ls` as Step 2). Then publish a second run and Send back: `{"status": "sent_back"}`, no new object. Record both in the ledger as `Task 2 (AUTH_MODE=none, DEMO_ROLE=delivery_lead): <run> approved; <run> sent_back`. The refused-approver check (Step 4) needs Cognito: write "Step 4 pending F3a".

**Task done when:** the four ledger lines of Steps 1–4 exist and match, or (Cognito off) Step 1's line and Step 5's line exist and match.

### Task 3: Review, then PR (after Clement's OK)
- [ ] **Step 1:** Work through the Review Focus by hand; write each result in the ledger.
- [ ] **Step 2:** `git diff develop --stat` lists only the files this plan names.
- [ ] **Step 3:** Fresh review of the diff against [[F5 - Publish and approve on the real API - spec]] (another person, or an agent with no prior context); fix critical and important findings test-first; list minor ones in the PR.
- [ ] **Step 4 (with Clement's OK only):** `git push -u origin feature/web-publish-approve`; open the PR to `develop` titled "Front end: publish and approve on the contract (F5)". Body: what changed, the suite count (start + 3), the `Ruling:` lines, deferred minors. Tell Mildred which of her files changed. No attribution lines.
- [ ] **Step 5:** [[Build order]] row F5: `in review (PR #nn)`, then `merged` when Patrick merges.

**Task done when:** the PR is open to `develop`, Jenkins' front-end build is green, and [[Build order]] shows `in review (PR #nn)`.

## Never
- Compute a KPI, a status or a date in the browser; show what the API returns.
- Send scope (role, entities, tenant) in a request body, query string or header.
- Log, print or store a token yourself.
- Add a `package-lock.json`, or change `yarn.lock` other than with `yarn add`.
- Commit the npm token, a password or any secret.
- Push to `develop` or `main`, or add attribution lines.
- Show "Approved" unless the API returned `approved`.
- Put an execution ARN or a task token in a URL.

## Done means
- [ ] **Tests:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` → start + 3 (dry-run: `Tests  107 passed (107)`). *Verify:* run it.
- [ ] **Contract:** `(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/features/publish/publish-fixtures.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)` → `Tests  2 passed (2)`. *Verify:* run it.
- [ ] **Route:** `grep -n "approve/:runId" web/src/app/app.routes.ts` prints one line. *Verify:* run it.
- [ ] **Mock walk-through:** Review Focus 3 ends on the badge "Sent back" and "Status from the API: sent_back". *Verify:* `yarn start`.
- [ ] **Live (verify in AWS):** Task 2's four ledger lines: publish 200 awaiting_approval; approve 200 approved + one `status-packs/` object; send back 200 sent_back + no object; CFO 403. If Cognito is off: Step 1's line and Step 5's line (`AUTH_MODE=none`, `DEMO_ROLE=delivery_lead`: approved + one object; sent_back + no object), and "Step 4 pending F3a".
- [ ] **PR:** open to `develop` titled "Front end: publish and approve on the contract (F5)"; [[Build order]] row F5 updated. *Verify:* `gh pr list --head feature/web-publish-approve`.

Related: [[F5 - Publish and approve on the real API - spec]], [[Build order]], [[How to execute a plan]]
