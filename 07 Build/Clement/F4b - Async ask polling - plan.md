---
tags: [build, plan, area/frontend]
id: F4b
owner: Clement
spec: "[[F4b - Async ask polling - spec]]"
status: ready (conditional)
updated: 2026-10-14
---
# F4b: async ask polling (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[F4b - Async ask polling - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger as a `Ruling:` line.
3. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Clement - front end]].
4. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
5. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
6. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

**Goal:** the ask panel polls an asynchronous run with a visible progress state and a clear timeout.

**Architecture:** `AskStore.ask` → `PortalApi.ask` → `AskPending`? → `pollUntilAnswered` (`ASK_POLLING.wait(intervalMs)` → `PortalApi.askResult(runId)`, up to `maxAttempts`) → the answer, or the timeout message. `AskPanel` shows `store.progress()`.

**Tech stack:** Angular 22 (signals, `InjectionToken`), TypeScript 6, Vitest through `ng test`.

**Dry-run:** Tasks 1–2 were run on 2026-10-14 in a throwaway worktree with C1, F1a, F1b, F2, F4a, F3b, F5 and F3a applied; counts and messages are real. **Task 3 needs the async API: verify in AWS.**

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your own clone). Branch **`feature/web-ask-polling`** from an up-to-date `develop`, after every dependency in [[Build order]] is merged. Never commit to, or push, `develop` or `main`; PR to `develop`; Patrick merges.
- **Start state:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` on `develop` with F4a merged. Dry-run order (everything above): `Test Files  38 passed (38)`, `Tests  121 passed (121)`. What must match is the increase (+1, then +1 file and +2). **Gate:** the async decision is recorded (`DECISIONS.md` or the vault) with the shapes in the spec; otherwise stop.
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
- **Stay in your files** (Clement's list in the brief). This item touches `web/src/app/core/models/ask.ts`, `web/src/app/features/ask/` (store, panel, new spec), and Mildred's port and adapters below.
- **Cross-owner edits:** **Mildred's** `web/src/app/core/api/portal-api.ts`, `http-portal-api.ts`, `mock-portal-api.ts` and `http-portal-api.spec.ts`: exactly the edits in Task 1; she agrees first.
- **Commits:** small, one per task, with the message given. **No `Co-Authored-By` and no "Generated with" lines** in commits or the PR.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **The decided shape equals the assumed one** (`status: "running"`, `GET /ask/{run_id}`); if Patrick exported an `AskPending` schema, add `contractErrors('ask_pending', …)` checks (ask Patrick for the schema name).
2. **No overlapping polls:** a second question while polling is impossible (the panel disables asking while `store.asking()`).
3. **The timer stops:** after the answer or the timeout, no more `/ask/{run_id}` requests in Network.
4. **A synchronous answer still works** (the mock, and the API if it answers fast).
5. **Live:** a slow question shows the progress line, then the answer; total polls × 2 s ≈ the run's time.

---

### Task 1: The port and the adapters can fetch a run

**Files:** Modify `web/src/app/core/models/ask.ts`; Mildred's `core/api/portal-api.ts`, `http-portal-api.ts`, `mock-portal-api.ts`, `http-portal-api.spec.ts`.

**Produces:** `AskPending`, `isAskPending(body)`, `PortalApi.askResult(runId: string): Promise<AskResponse | AskPending>`; `PortalApi.ask` returns `Promise<AskResponse | AskPending>`.

- [ ] **Step 0: The gate.** Find the recorded async decision; compare its shapes with the spec's assumptions. Different: stop and ask Patrick.
- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
git switch -c feature/web-ask-polling
mkdir -p .superpowers && printf '# Ledger: F4b ask polling\n' > .superpowers/ledger-F4b.md
(cd web && yarn install --frozen-lockfile)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
```
Expected: the start state (dry-run: `Test Files  38 passed (38)`, `Tests  121 passed (121)`).
- [ ] **Step 2: The failing test.** In `web/src/app/core/api/http-portal-api.spec.ts`, add before the final `});` of the `describe`:
```ts

  it('GETs /ask/{run_id} for an asynchronous run', async () => {
    const response = api.askResult('run-async-1');
    http.expectOne({ method: 'GET', url: `${BASE_URL}/ask/run-async-1` }).flush({ run_id: 'run-async-1', status: 'running' });
    expect(await response).toEqual({ run_id: 'run-async-1', status: 'running' });
  });
```
- [ ] **Step 3: Run it**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/api/http-portal-api.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: `✘ [ERROR] TS2339: Property 'askResult' does not exist on type 'HttpPortalApi'.`
- [ ] **Step 4: Implement.** Append to `web/src/app/core/models/ask.ts`:
```ts
/**
 * ASSUMED (F4b): the asynchronous /ask, if Huvison and Yaw switch to it because of API Gateway's 29-second limit.
 * POST /ask and GET /ask/{run_id} answer with this while the run is still working, and with AskResponse when done.
 */
export interface AskPending {
  run_id: string;
  status: 'running';
}

export function isAskPending(body: AskResponse | AskPending): body is AskPending {
  return 'status' in body && body.status === 'running';
}
```
Then:
- In `web/src/app/core/api/portal-api.ts`, replace
```ts
  AskRequest,
```
  with
```ts
  AskPending,
  AskRequest,
```
- In `web/src/app/core/api/portal-api.ts`, replace
```ts
  abstract ask(request: AskRequest): Promise<AskResponse>;
```
  with
```ts
  /** The answer, or AskPending when the API runs the question asynchronously (then poll askResult). */
  abstract ask(request: AskRequest): Promise<AskResponse | AskPending>;
  /** GET /ask/{run_id}: the answer of an asynchronous run, or AskPending while it is still working. */
  abstract askResult(runId: string): Promise<AskResponse | AskPending>;
```
- In `web/src/app/core/api/http-portal-api.ts`, replace
```ts
  AskRequest,
```
  with
```ts
  AskPending,
  AskRequest,
```
- In `web/src/app/core/api/http-portal-api.ts`, replace
```ts
  override ask(request: AskRequest): Promise<AskResponse> {
    return this.call(this.http.post<AskResponse>(`${this.baseUrl}/ask`, request));
  }
```
  with
```ts
  override ask(request: AskRequest): Promise<AskResponse | AskPending> {
    return this.call(this.http.post<AskResponse | AskPending>(`${this.baseUrl}/ask`, request));
  }

  override askResult(runId: string): Promise<AskResponse | AskPending> {
    return this.call(this.http.get<AskResponse | AskPending>(`${this.baseUrl}/ask/${encodeURIComponent(runId)}`));
  }
```
- In `web/src/app/core/api/mock-portal-api.ts`, replace
```ts
    return withoutFixtureNotes<AskResponse>(fixture);
  }
```
  with
```ts
    return withoutFixtureNotes<AskResponse>(fixture);
  }

  /** The mock answers synchronously, so there is never a run to poll. */
  override async askResult(runId: string): Promise<AskResponse> {
    throw ApiError.notFound(`Run ${runId}`);
  }
```
- [ ] **Step 5: Run, suite, commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/core/api/http-portal-api.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
git add web/src/app/core
git commit -m "The API port can fetch an asynchronous ask run (GET /ask/{run_id})"
```
Expected: `Tests  7 passed (7)`; the suite at **start + 1** (dry-run: 38 files, 122 tests).

**Task done when:** `grep -n "askResult" web/src/app/core/api/*.ts` shows the port, both adapters and the spec.

### Task 2: The store polls; the panel shows progress

**Files:** Modify `web/src/app/features/ask/ask-store.ts`, `ask-panel/ask-panel.html`, `ask-panel/ask-panel.scss`. Create `web/src/app/features/ask/ask-polling.spec.ts` *(new)*.

**Produces:** `ASK_POLLING: InjectionToken<AskPolling>`, `AskPolling {intervalMs, maxAttempts, wait}`, `AskStore.progress: Signal<string | undefined>`.

- [ ] **Step 1: The failing test.** Create `web/src/app/features/ask/ask-polling.spec.ts`:
```ts
import { TestBed } from '@angular/core/testing';

import askEntity4Fixture from '../../core/api/fixtures/ask-E4.json';
import { PortalApi } from '../../core/api/portal-api';
import { AskPending, AskResponse } from '../../core/models';
import { ASK_POLLING, AskStore } from './ask-store';

const REQUEST = { entity_id: 'E4', question: 'What is blocking cutover for entity 4?' };
const PENDING: AskPending = { run_id: 'run-async-1', status: 'running' };
const ANSWER = askEntity4Fixture as unknown as AskResponse;
const POLL_INTERVAL_MS = 2000;

/** A store whose API starts the run, then answers each poll from `results` (still running once they run out). */
function storeWith(results: (AskResponse | AskPending)[], maxAttempts = 3) {
  const polled: string[] = [];
  const progressWhileWaiting: (string | undefined)[] = [];
  const api = {
    ask: () => Promise.resolve(PENDING),
    askResult: (runId: string) => {
      polled.push(runId);
      return Promise.resolve(results.shift() ?? PENDING);
    },
  };
  const wait = (milliseconds: number): Promise<void> => {
    expect(milliseconds).toBe(POLL_INTERVAL_MS);
    progressWhileWaiting.push(TestBed.inject(AskStore).progress());
    return Promise.resolve();
  };
  TestBed.configureTestingModule({
    providers: [
      AskStore,
      { provide: PortalApi, useValue: api },
      { provide: ASK_POLLING, useValue: { intervalMs: POLL_INTERVAL_MS, maxAttempts, wait } },
    ],
  });
  return { store: TestBed.inject(AskStore), polled, progressWhileWaiting };
}

describe('AskStore with an asynchronous /ask (start, then poll GET /ask/{run_id})', () => {
  it('polls the run until the answer arrives, showing progress meanwhile', async () => {
    const { store, polled, progressWhileWaiting } = storeWith([PENDING, ANSWER]);
    const asking = store.ask(REQUEST);
    expect(store.asking()).toBe(true);
    await asking;
    expect(polled).toEqual(['run-async-1', 'run-async-1']);
    expect(progressWhileWaiting).toEqual([
      'Still checking the evidence (run run-async-1)',
      'Still checking the evidence (run run-async-1)',
    ]);
    expect(store.answer()?.bullets).toHaveLength(3);
    expect([store.asking(), store.progress()]).toEqual([false, undefined]);
  });

  it('gives up with a clear message after the last attempt', async () => {
    const { store, polled } = storeWith([], 3);
    await store.ask(REQUEST);
    expect(polled).toHaveLength(3);
    expect(store.errorMessage()).toBe(
      'The answer is taking longer than expected. Run run-async-1 is still working; try again in a minute.',
    );
  });
});
```
- [ ] **Step 2: Run it**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/features/ask/ask-polling.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
```
Expected: `✘ [ERROR] TS2305: Module '"./ask-store"' has no exported member 'ASK_POLLING'.` and `✘ [ERROR] TS2339: Property 'progress' does not exist on type 'AskStore'.` (esbuild also prints `No matching export in "src/app/features/ask/ask-store.ts" for import "ASK_POLLING"`)
- [ ] **Step 3: Implement.** Replace `web/src/app/features/ask/ask-store.ts`:
```ts
import { Injectable, InjectionToken, computed, inject, signal } from '@angular/core';

import { ApiError } from '../../core/api/api-error';
import { PortalApi } from '../../core/api/portal-api';
import { AskPending, AskRequest, AskResponse, isAskPending } from '../../core/models';
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
  /** Set while an asynchronous run is being polled. */
  pendingRunId?: string;
}

/** How the panel polls an asynchronous /ask. */
export interface AskPolling {
  intervalMs: number;
  maxAttempts: number;
  wait: (milliseconds: number) => Promise<void>;
}

const ASK_POLL_INTERVAL_MS = 2_000;
/** 30 polls 2 s apart: a minute, twice the ask spine's expected worst case with one retry. */
const ASK_POLL_MAX_ATTEMPTS = 30;

export const ASK_POLLING = new InjectionToken<AskPolling>('ASK_POLLING', {
  providedIn: 'root',
  factory: () => ({
    intervalMs: ASK_POLL_INTERVAL_MS,
    maxAttempts: ASK_POLL_MAX_ATTEMPTS,
    wait: (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds)),
  }),
});

const ASK_ERROR_MESSAGE = 'The question could not be answered. Try again in a moment.';
const HTTP_FORBIDDEN = 403;

/** One question at a time to POST /ask, and its answer, refusal (403) or error. */
@Injectable()
export class AskStore {
  private readonly api = inject(PortalApi);
  private readonly session = inject(SessionStore);
  private readonly polling = inject(ASK_POLLING);
  private readonly state = signal<AskState>({ status: 'idle' });

  readonly asking = computed(() => this.state().status === 'asking');
  readonly lastRequest = computed(() => this.state().request);
  readonly answer = computed(() => {
    const response = this.state().response;
    return response ? buildAnswerView(response) : undefined;
  });
  readonly errorMessage = computed(() => this.state().errorMessage);
  readonly refusal = computed(() => this.state().refusal);
  readonly progress = computed(() => {
    const runId = this.state().pendingRunId;
    return runId ? `Still checking the evidence (run ${runId})` : undefined;
  });

  async ask(request: AskRequest): Promise<void> {
    this.state.set({ status: 'asking', request });
    try {
      const started = await this.api.ask(request);
      const response = isAskPending(started) ? await this.pollUntilAnswered(request, started) : started;
      if (response) this.state.set({ status: 'answered', request, response });
    } catch (error) {
      if (error instanceof ApiError && error.status === HTTP_FORBIDDEN) {
        this.state.set({ status: 'refused', request, refusal: refusalMessage(this.session.scope(), request.entity_id) });
        return;
      }
      const errorMessage = error instanceof ApiError ? error.message : ASK_ERROR_MESSAGE;
      this.state.set({ status: 'failed', request, errorMessage });
    }
  }

  /** Polls GET /ask/{run_id}; undefined (with the error set) when the run is still working after the last attempt. */
  private async pollUntilAnswered(request: AskRequest, pending: AskPending): Promise<AskResponse | undefined> {
    this.state.set({ status: 'asking', request, pendingRunId: pending.run_id });
    for (let attempt = 0; attempt < this.polling.maxAttempts; attempt++) {
      await this.polling.wait(this.polling.intervalMs);
      const result = await this.api.askResult(pending.run_id);
      if (!isAskPending(result)) return result;
    }
    const errorMessage = `The answer is taking longer than expected. Run ${pending.run_id} is still working; try again in a minute.`;
    this.state.set({ status: 'failed', request, errorMessage });
    return undefined;
  }

  retry(): Promise<void> {
    const request = this.state().request;
    return request ? this.ask(request) : Promise.resolve();
  }
}
```
Then:
- In `web/src/app/features/ask/ask-panel/ask-panel.html`, replace
```html
    <app-loading-block label="Checking the evidence" [lines]="4" />
```
  with
```html
    @if (store.progress(); as progress) {
      <p class="progress" aria-live="polite">{{ progress }}</p>
    }
    <app-loading-block label="Checking the evidence" [lines]="4" />
```
- Append to `web/src/app/features/ask/ask-panel/ask-panel.scss`:
```scss

.progress {
  color: var(--portal-color-text-muted);
  font-size: var(--portal-font-size-sm);
}
```
- [ ] **Step 4: Run, suite, build, commit**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/features/ask 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
(cd web && yarn build 2>&1 | grep -E "ERROR|WARN|bundle generation complete")
git add web/src/app/features/ask
git commit -m "Ask panel polls an asynchronous run with a progress line and a one-minute limit"
```
Expected: the ask folder passes; the suite at **start + 1 file, + 3 tests** (dry-run: `Test Files  39 passed (39)`, `Tests  124 passed (124)`); the build prints `Application bundle generation complete.`

**Task done when:** both polling tests pass and the suite is at start + 3.

### Task 3: Live (verify in AWS; not dry-run)
- [ ] **Step 1:** `curl -s -X POST https://<cf>/api/ask -H 'content-type: application/json' -d '{"entity_id": "E4", "question": "What is blocking cutover for entity 4?"}'` (add the ID token header in cognito mode). Expected: `{"run_id": "…", "status": "running"}` or the full answer.
- [ ] **Step 2:** `curl -s https://<cf>/api/ask/<run_id>` until it returns the answer. Expected: `{"run_id": …, "status": "running"}` then a body with `answer` and `trace`.
- [ ] **Step 3:** In the portal, ask the same question. Expected: "Still checking the evidence (run <id>)" under the question, then the answer card; Network shows `GET /api/ask/<run_id>` every ~2 s, stopping when the answer arrives. Ledger: `Task 3: live async — <polls> polls — <seconds> s — <date time>`.

**Task done when:** Steps 1–3 match and the ledger line exists.

### Task 4: Review, then PR (after Clement's OK)
- [ ] **Step 1:** Work through the Review Focus by hand; write each result in the ledger.
- [ ] **Step 2:** `git diff develop --stat` lists only the files this plan names.
- [ ] **Step 3:** Fresh review of the diff against [[F4b - Async ask polling - spec]] (another person, or an agent with no prior context); fix critical and important findings test-first; list minor ones in the PR.
- [ ] **Step 4 (with Clement's OK only):** `git push -u origin feature/web-ask-polling`; open the PR to `develop` titled "Front end: poll an asynchronous /ask (F4b)". Body: what changed, the suite count (start + 3), the `Ruling:` lines, deferred minors. Link the recorded async decision. No attribution lines.
- [ ] **Step 5:** [[Build order]] row F4: `in review (PR #nn)`, then `merged` when Patrick merges.

**Task done when:** the PR is open to `develop`, Jenkins' front-end build is green, and [[Build order]] shows `in review (PR #nn)`.

## Never
- Compute a KPI, a status or a date in the browser; show what the API returns.
- Send scope (role, entities, tenant) in a request body, query string or header.
- Log, print or store a token yourself.
- Add a `package-lock.json`, or change `yarn.lock` other than with `yarn add`.
- Commit the npm token, a password or any secret.
- Push to `develop` or `main`, or add attribution lines.
- Start this item before the async decision is recorded.
- Poll without a limit, or faster than every 2 seconds.

## Done means
- [ ] **Gate:** the PR body links the recorded async decision. *Verify:* read the PR.
- [ ] **Tests:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` → start + 3 (dry-run: `Tests  124 passed (124)`). *Verify:* run it.
- [ ] **Polling unit:** `(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/features/ask/ask-polling.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)` → `Tests  2 passed (2)`. *Verify:* run it.
- [ ] **Live (verify in AWS):** Task 3's ledger line; Network shows polls stop after the answer.
- [ ] **PR:** open to `develop` titled "Front end: poll an asynchronous /ask (F4b)"; [[Build order]] row F4 updated. *Verify:* `gh pr list --head feature/web-ask-polling`.

Related: [[F4b - Async ask polling - spec]], [[F4a - Ask panel on the real ask contract - spec]], [[Build order]], [[How to execute a plan]]
