---
tags: [build, plan, area/frontend]
id: F4a
owner: Clement
spec: "[[F4a - Ask panel on the real ask contract - spec]]"
status: ready
updated: 2026-10-14
---
# F4a: ask panel on the real ask contract (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[F4a - Ask panel on the real ask contract - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger as a `Ruling:` line.
3. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Clement - front end]].
4. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
5. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
6. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

**Goal:** `ask.ts` and the ask fixtures match C1's `AskResponse`, and the panel shows the trace with prompt versions, the cost, partial answers and the could-not-verify list.

**Architecture:** `PortalApi.ask()` → `AskStore` → `buildAnswerView()` (pure: wording only) → `AnswerCard` → `CouldNotVerifyList`, `AgentTrace` *(new)*, `CitationChip` → Mildred's `CitationViewer` / row viewer.

**Tech stack:** Angular 22, TypeScript 6, Vitest through `ng test`.

**Dry-run:** Task 1 was run on 2026-10-14 in a throwaway worktree with C1, F1a, F1b and F2 applied; counts and messages are real. **Task 2 needs the deployed `/ask`: verify in AWS** (not dry-run; no AWS calls were made).

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your own clone). Branch **`feature/web-ask-panel-contract`** from an up-to-date `develop`, after every dependency in [[Build order]] is merged. Never commit to, or push, `develop` or `main`; PR to `develop`; Patrick merges.
- **Start state:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` on `develop` with C1, F1a and F1b merged. In the dry-run F2 was merged too: `Test Files  32 passed (32)`, `Tests  95 passed (95)`. Without F2 you will see 29 files and 88 tests: then every count below is 3 files and 7 tests lower. Any other number: stop.
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
- **Stay in your files** (Clement's list in the brief). This item touches `web/src/app/core/models/ask.ts`, `web/src/app/features/ask/`, and (see below) two fixtures and one spec line in Mildred's folders.
- **Cross-owner edits:** **Mildred's** `web/src/app/core/api/fixtures/ask-E4.json` and `ask-partial.json` (handed to you for this change; ask her first) and one line of `web/src/app/core/api/mock-portal-api.spec.ts` (Task 1 Step 6). Nothing else of hers.
- **Commits:** small, one per task, with the message given. **No `Co-Authored-By` and no "Generated with" lines** in commits or the PR.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **Bullet text is shown as text, never HTML:** the bullets render with `{{ }}` interpolation (Angular escapes it). `grep -rn "innerHTML" web/src/app/features/ask` prints nothing (D-009: artefact text is untrusted).
2. **The panel in mock mode** (`yarn start`, CFO, the entity 4 suggestion): the headline, 3 bullets, 5 chips (each opens its row in the drawer), "Could not verify" with the DEF-0398 statement and "Rejected after 2 checks", the trace collapsed by default and showing 8 steps when opened, the cost line.
3. **Partial with no answer** (mock: pick Entity 2, ask anything): the warning alert with the reason, the fallback headline, no "Publish as status pack" button.
4. **Cost wording:** `$0.042` is the API's `cost_usd` with three decimals; nothing sums or estimates cost in the browser.
5. **Live** (after Task 2): the trace's prompt versions match `agents/prompts/prompts.lock` on `develop` (for example the critic's `1.0.0` and `01d4c3b8`).

---

### Task 1: The ask contract, the fixtures and the panel

**Files:**
- Modify: `web/src/app/core/models/ask.ts`, `web/src/app/features/ask/answer-view.ts`, `…/answer-view.spec.ts`, `…/answer-card/answer-card.ts`, `…/answer-card/answer-card.html`, `…/answer-card/answer-card.spec.ts`, `…/could-not-verify-list/could-not-verify-list.ts`
- Modify (Mildred's, agreed): `web/src/app/core/api/fixtures/ask-E4.json`, `ask-partial.json`, one line of `web/src/app/core/api/mock-portal-api.spec.ts`
- Create: `web/src/app/features/ask/ask-fixtures.spec.ts` *(new)*, `web/src/app/features/ask/agent-trace/agent-trace.ts` *(new)*

**Produces:** the `ask.ts` types above; `AnswerView.trace: readonly TraceStepView[]`, `AnswerView.rejected: readonly RejectedClaimView[]`, `RejectedClaimView`, `TraceStepView`; `<app-agent-trace [steps]>`. **Consumes:** F1a's `contractErrors`; F1b's `rows.json` (`RowsResponse`).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
git switch -c feature/web-ask-panel-contract
mkdir -p .superpowers && printf '# Ledger: F4a ask panel on the contract\n' > .superpowers/ledger-F4a.md
(cd web && yarn install --frozen-lockfile)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
```
Expected: `Test Files  32 passed (32)`, `Tests  95 passed (95)` (see Start state).

- [ ] **Step 2: The fixtures.** Replace both files (Mildred agreed):
- `web/src/app/core/api/fixtures/ask-E4.json`:
```json
{
  "_mock": "Mock response for UI development; not produced by the agent loop or Step Functions.",
  "run_id": "run-mock-e4-0001",
  "answer": {
    "headline": "Three things block entity 4 from cutover",
    "bullets": [
      {
        "text": "Customer master reconciliation is at 91.2%. The target is 98%. 212 records fail tax ID mapping, and the defect has been open for 18 days.",
        "citations": [
          {
            "artefact": "reconciliation_results",
            "row_id": "RC-C3-E4-customers"
          },
          {
            "artefact": "defect_log",
            "row_id": "DEF-0412"
          }
        ]
      },
      {
        "text": "Mock run 2 has no booked environment. The rehearsal is planned for 5 and 6 Dec and must pass before cutover readiness can be signed off.",
        "citations": [
          {
            "artefact": "workplan",
            "row_id": "WP-022"
          }
        ]
      },
      {
        "text": "Two interface steps have no owner. Steps 14 and 15 of the 31 cutover steps are unassigned.",
        "citations": [
          {
            "artefact": "cutover_runbook",
            "row_id": "E4#RB-014"
          },
          {
            "artefact": "cutover_runbook",
            "row_id": "E4#RB-015"
          }
        ]
      }
    ],
    "rejected_count": 1
  },
  "rejected": [
    {
      "claim_id": "claim-4",
      "statement": "Duplicate customer records (DEF-0398) still block cutover for entity 4.",
      "reason": "The cited defect DEF-0398 is closed, so it does not support an open blocker.",
      "verdicts": [
        {
          "claim_id": "claim-4",
          "pass": false,
          "reason": "The cited defect DEF-0398 is closed, so it does not support an open blocker.",
          "missing_evidence": [],
          "prompt": {
            "agent": "critic",
            "version": "1.0.0",
            "sha256": "01d4c3b8ad16f3360dd21487c74dd018c73ae57fd0c8c36157ba204de470aea3"
          }
        },
        {
          "claim_id": "claim-4",
          "pass": false,
          "reason": "The cited defect DEF-0398 is closed, so it does not support an open blocker.",
          "missing_evidence": [],
          "prompt": {
            "agent": "critic",
            "version": "1.0.0",
            "sha256": "01d4c3b8ad16f3360dd21487c74dd018c73ae57fd0c8c36157ba204de470aea3"
          }
        }
      ]
    }
  ],
  "cost_usd": 0.042,
  "partial": false,
  "partial_reason": null,
  "trace": [
    {
      "step": "check_budget",
      "agent": null,
      "prompt": null
    },
    {
      "step": "run_orchestrator",
      "agent": "orchestrator",
      "prompt": {
        "agent": "orchestrator",
        "version": "0.0.0-mock",
        "sha256": "mock"
      }
    },
    {
      "step": "retriever",
      "agent": "retriever",
      "prompt": {
        "agent": "retriever",
        "version": "0.0.0-mock",
        "sha256": "mock"
      }
    },
    {
      "step": "blocker_analyst",
      "agent": "blocker_analyst",
      "prompt": {
        "agent": "blocker_analyst",
        "version": "0.0.0-mock",
        "sha256": "mock"
      }
    },
    {
      "step": "store_claims",
      "agent": null,
      "prompt": null
    },
    {
      "step": "judge_claim",
      "agent": "critic",
      "prompt": {
        "agent": "critic",
        "version": "1.0.0",
        "sha256": "01d4c3b8ad16f3360dd21487c74dd018c73ae57fd0c8c36157ba204de470aea3"
      }
    },
    {
      "step": "retry_decision",
      "agent": null,
      "prompt": null
    },
    {
      "step": "write_answer",
      "agent": "writer",
      "prompt": {
        "agent": "writer",
        "version": "0.0.0-mock",
        "sha256": "mock"
      }
    }
  ]
}
```
- `web/src/app/core/api/fixtures/ask-partial.json`:
```json
{
  "_mock": "Mock response for UI development; not produced by the agent loop or Step Functions.",
  "run_id": "run-mock-partial-0001",
  "answer": null,
  "rejected": [],
  "cost_usd": 0.5,
  "partial": true,
  "partial_reason": "No claim about this entity passed the critic within the run budget.",
  "trace": [
    {
      "step": "check_budget",
      "agent": null,
      "prompt": null
    },
    {
      "step": "run_orchestrator",
      "agent": "orchestrator",
      "prompt": {
        "agent": "orchestrator",
        "version": "0.0.0-mock",
        "sha256": "mock"
      }
    }
  ]
}
```

- [ ] **Step 3: The failing tests.** Create or replace:
- `web/src/app/features/ask/ask-fixtures.spec.ts`:
```ts
import askEntity4Fixture from '../../core/api/fixtures/ask-E4.json';
import askPartialFixture from '../../core/api/fixtures/ask-partial.json';
import rowsFixture from '../../core/api/fixtures/rows.json';
import { contractErrors } from '../../core/api/testing/contract-validator';

/** The fixtures' `_mock` note is the only key the API would never send. */
function withoutMockNote(fixture: object): object {
  return Object.fromEntries(Object.entries(fixture).filter(([key]) => key !== '_mock'));
}

describe('ask fixtures', () => {
  it('ask-E4.json and ask-partial.json match the POST /ask response contract', () => {
    expect(contractErrors('ask_response', withoutMockNote(askEntity4Fixture))).toEqual([]);
    expect(contractErrors('ask_response', withoutMockNote(askPartialFixture))).toEqual([]);
  });

  it('every citation in ask-E4.json opens a row in rows.json', () => {
    const rowKeys = new Set(rowsFixture.rows.map((row) => `${row.artefact}:${row.row_id}`));
    const cited = askEntity4Fixture.answer.bullets.flatMap((bullet) => bullet.citations);
    expect(cited.filter((citation) => !rowKeys.has(`${citation.artefact}:${citation.row_id}`))).toEqual([]);
  });

  it('ask-E4.json carries a trace with prompt versions and a rejected claim with its verdicts', () => {
    expect(askEntity4Fixture.trace.filter((step) => step.prompt).map((step) => step.prompt?.agent)).toEqual([
      'orchestrator',
      'retriever',
      'blocker_analyst',
      'critic',
      'writer',
    ]);
    expect(askEntity4Fixture.rejected[0].verdicts.map((verdict) => verdict.pass)).toEqual([false, false]);
  });

  it('ask-partial.json is a partial answer with no answer card and its reason', () => {
    expect([askPartialFixture.partial, askPartialFixture.answer]).toEqual([true, null]);
    expect(askPartialFixture.partial_reason).toBe('No claim about this entity passed the critic within the run budget.');
  });
});
```
- `web/src/app/features/ask/answer-view.spec.ts`:
```ts
import askEntity4Fixture from '../../core/api/fixtures/ask-E4.json';
import askPartialFixture from '../../core/api/fixtures/ask-partial.json';
import { AskResponse } from '../../core/models';
import { buildAnswerView } from './answer-view';

describe('buildAnswerView', () => {
  it('numbers the bullets, keeps their citations and lists the artefacts checked', () => {
    const view = buildAnswerView(askEntity4Fixture as unknown as AskResponse);
    expect(view.headline).toBe('Three things block entity 4 from cutover');
    expect(view.bullets.map((bullet) => bullet.number)).toEqual([1, 2, 3]);
    expect(view.bullets.every((bullet) => bullet.citations.length > 0)).toBe(true);
    expect(view.checkedLine).toBe('Checked against 4 artefacts: reconciliation results, defect log, workplan, cutover runbook.');
    expect(view.partial).toBe(false);
    expect(view.runLine).toBe('Run run-mock-e4-0001 · cost $0.042');
  });

  it('lists each rejected claim with its reason and how many times the critic checked it', () => {
    const [rejected] = buildAnswerView(askEntity4Fixture as unknown as AskResponse).rejected;
    expect(rejected.statement).toBe('Duplicate customer records (DEF-0398) still block cutover for entity 4.');
    expect(rejected.reason).toBe('The cited defect DEF-0398 is closed, so it does not support an open blocker.');
    expect(rejected.checksLine).toBe('Rejected after 2 checks');
  });

  it('shows the agent trace with each prompt version', () => {
    const { trace } = buildAnswerView(askEntity4Fixture as unknown as AskResponse);
    expect(trace.map((step) => step.text)).toEqual([
      'Budget check',
      'Orchestrator: planned the retrieval (prompt orchestrator 0.0.0-mock)',
      'Retriever: fetched the cited rows (prompt retriever 0.0.0-mock)',
      'Blocker-analyst: drafted the claims (prompt blocker_analyst 0.0.0-mock)',
      'Stored the claims in the run ledger',
      'Critic: judged each claim against its rows (prompt critic 1.0.0, 01d4c3b8)',
      'Retry decision',
      'Writer: wrote the cited answer (prompt writer 0.0.0-mock)',
    ]);
  });

  it('shows a partial answer with its reason, a fallback headline and no checked line', () => {
    const view = buildAnswerView(askPartialFixture as unknown as AskResponse);
    expect(view.partial).toBe(true);
    expect(view.headline).toBe('This question could not be answered in full');
    expect(view.partialReason).toBe('No claim about this entity passed the critic within the run budget.');
    expect(view.bullets).toEqual([]);
    expect(view.checkedLine).toBeUndefined();
  });
});
```
- `web/src/app/features/ask/answer-card/answer-card.spec.ts`:
```ts
import { TestBed } from '@angular/core/testing';

import askEntity4Fixture from '../../../core/api/fixtures/ask-E4.json';
import { AskResponse } from '../../../core/models';
import { CitationRequest } from '../../../shared/citations/citation-viewer';
import { buildAnswerView } from '../answer-view';
import { AnswerCard } from './answer-card';

describe('AnswerCard', () => {
  async function render() {
    const fixture = TestBed.createComponent(AnswerCard);
    fixture.componentRef.setInput('answer', buildAnswerView(askEntity4Fixture as unknown as AskResponse));
    await fixture.whenStable();
    return fixture;
  }

  it('shows each bullet with its citation chips, the could-not-verify list and the trace', async () => {
    const element = (await render()).nativeElement as HTMLElement;
    expect(element.querySelectorAll('.bullet')).toHaveLength(3);
    expect(element.querySelectorAll('app-citation-chip')).toHaveLength(5);
    expect(element.textContent).toContain('Defect log, DEF-0412');
    expect(element.textContent).toContain('Could not verify');
    expect(element.textContent).toContain('Duplicate customer records (DEF-0398) still block cutover for entity 4.');
    expect(element.textContent).toContain('Rejected after 2 checks');
    expect(element.querySelectorAll('app-agent-trace li')).toHaveLength(8);
    expect(element.textContent).toContain('prompt critic 1.0.0, 01d4c3b8');
  });

  it('opens a cited row when its chip is clicked', async () => {
    const fixture = await render();
    let request: CitationRequest | undefined;
    fixture.componentInstance.showSources.subscribe((emitted) => (request = emitted));
    (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>('app-citation-chip button')?.click();
    expect(request?.citations).toEqual([{ artefact: 'reconciliation_results', row_id: 'RC-C3-E4-customers' }]);
  });
});
```

- [ ] **Step 4: Run them and watch the build fail**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/features/ask 2>&1 | grep -E "ERROR\\]" | sort -u)
```
Expected:
```text
✘ [ERROR] TS2339: Property 'checksLine' does not exist on type 'RejectedClaim'.
✘ [ERROR] TS2339: Property 'statement' does not exist on type 'RejectedClaim'.
✘ [ERROR] TS2339: Property 'trace' does not exist on type 'AnswerView'.
✘ [ERROR] TS7006: Parameter 'step' implicitly has an 'any' type.
```

- [ ] **Step 5: Implement.** Replace or create:
- `web/src/app/core/models/ask.ts`:
```ts
import { Citation } from './citation';

/** POST /ask and its response (tools/api_schema.py `AskRequest`, `AskResponse`, D-021). */
export interface AskRequest {
  entity_id: string;
  question: string;
}

export interface Bullet {
  text: string;
  citations: Citation[];
}

/** The writer's answer card (tools/models.py `Answer`). */
export interface Answer {
  headline: string;
  bullets: Bullet[];
  rejected_count: number;
}

/** One critic verdict (tools/models.py `Verdict`, sent with the key `pass`). */
export interface Verdict {
  claim_id: string;
  pass: boolean;
  reason: string;
  missing_evidence?: string[];
  prompt?: Record<string, unknown> | null;
}

/** A claim the critic rejected at the retry limit, shown as "could not verify". */
export interface RejectedClaim {
  claim_id: string;
  statement: string;
  reason: string;
  verdicts: Verdict[];
}

/** Which prompt an agent ran with (agents/prompt_loader.py `Prompt.provenance()`). */
export interface PromptRef {
  agent: string;
  version: string;
  sha256: string;
}

/** One state of the ask spine, in the order it ran. */
export interface TraceStep {
  step: string;
  agent: string | null;
  prompt: PromptRef | null;
}

export interface AskResponse {
  run_id: string;
  /** null when the run stopped before the writer: then `partial` is true and `partial_reason` says why. */
  answer: Answer | null;
  rejected: RejectedClaim[];
  cost_usd: number;
  partial: boolean;
  partial_reason: string | null;
  trace: TraceStep[];
}
```
- `web/src/app/features/ask/answer-view.ts`:
```ts
import { artefactLabel } from '../../core/format/format';
import { AskResponse, Citation, TraceStep } from '../../core/models';

export interface AnswerBulletView {
  number: number;
  text: string;
  citations: readonly Citation[];
}

export interface RejectedClaimView {
  claimId: string;
  statement: string;
  reason: string;
  /** "Rejected after 2 checks": one per critic verdict the API returned. */
  checksLine: string;
}

export interface TraceStepView {
  number: number;
  text: string;
}

export interface AnswerView {
  runId: string;
  headline: string;
  bullets: AnswerBulletView[];
  /** "Checked against 4 artefacts: workplan, …" (which artefacts the bullets cite). */
  checkedLine?: string;
  rejected: readonly RejectedClaimView[];
  trace: readonly TraceStepView[];
  partial: boolean;
  partialReason: string;
  runLine: string;
}

const PARTIAL_HEADLINE = 'This question could not be answered in full';
const PARTIAL_FALLBACK_REASON = 'The answer is incomplete. The API did not say why.';
const COST_DECIMALS = 3;
/** How much of a prompt's sha256 the trace shows: enough to tell two versions apart. */
const PROMPT_HASH_SHOWN_CHARACTERS = 8;
const MOCK_PROMPT_HASH = 'mock';

/**
 * What each step did, in the user's words: the ask-machine states of docs/DEVOPS_HANDOVER.md, and the two sub-agents
 * the orchestrator calls. A step not listed here shows its own name, so a new state never breaks the trace.
 */
const STEP_LABELS: Record<string, string> = {
  check_budget: 'Budget check',
  run_orchestrator: 'Orchestrator: planned the retrieval',
  retriever: 'Retriever: fetched the cited rows',
  blocker_analyst: 'Blocker-analyst: drafted the claims',
  store_claims: 'Stored the claims in the run ledger',
  judge_claim: 'Critic: judged each claim against its rows',
  retry_decision: 'Retry decision',
  record_rejection: 'Recorded the rejected claims',
  write_answer: 'Writer: wrote the cited answer',
};

function traceText(step: TraceStep): string {
  const label = STEP_LABELS[step.step] ?? step.step;
  if (!step.prompt) return label;
  const { agent, version, sha256 } = step.prompt;
  const hash = sha256 === MOCK_PROMPT_HASH ? '' : `, ${sha256.slice(0, PROMPT_HASH_SHOWN_CHARACTERS)}`;
  return `${label} (prompt ${agent} ${version}${hash})`;
}

/** Shapes a POST /ask response for the answer card. Every bullet keeps its citations; nothing is computed. */
export function buildAnswerView(response: AskResponse): AnswerView {
  const bullets = (response.answer?.bullets ?? []).map((bullet, index) => ({
    number: index + 1,
    text: bullet.text,
    citations: bullet.citations,
  }));
  const artefacts = [...new Set(bullets.flatMap((bullet) => bullet.citations.map((citation) => citation.artefact)))];
  const artefactList = artefacts.map((artefact) => artefactLabel(artefact).toLowerCase()).join(', ');
  return {
    runId: response.run_id,
    headline: response.answer?.headline ?? PARTIAL_HEADLINE,
    bullets,
    checkedLine: artefacts.length
      ? `Checked against ${artefacts.length} ${artefacts.length === 1 ? 'artefact' : 'artefacts'}: ${artefactList}.`
      : undefined,
    rejected: response.rejected.map((claim) => ({
      claimId: claim.claim_id,
      statement: claim.statement,
      reason: claim.reason,
      checksLine: `Rejected after ${claim.verdicts.length} ${claim.verdicts.length === 1 ? 'check' : 'checks'}`,
    })),
    trace: response.trace.map((step, index) => ({ number: index + 1, text: traceText(step) })),
    partial: response.partial,
    partialReason: response.partial_reason ?? PARTIAL_FALLBACK_REASON,
    runLine: `Run ${response.run_id} · cost $${response.cost_usd.toFixed(COST_DECIMALS)}`,
  };
}
```
- `web/src/app/features/ask/agent-trace/agent-trace.ts`:
```ts
import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { TraceStepView } from '../answer-view';

/** "How this answer was checked": each ask-spine step in order, with the agent's prompt version (AskResponse.trace). */
@Component({
  selector: 'app-agent-trace',
  template: `
    <details class="trace">
      <summary class="summary">How this answer was checked ({{ steps().length }} steps)</summary>
      <ol class="steps">
        @for (step of steps(); track step.number) {
          <li>{{ step.text }}</li>
        }
      </ol>
    </details>
  `,
  styles: `
    .trace { color: var(--portal-color-text-muted); font-size: var(--portal-font-size-xs); }
    .summary { color: var(--portal-color-primary); font-weight: 600; cursor: pointer; }
    .steps { display: grid; gap: var(--portal-space-1); margin: var(--portal-space-2) 0 0; padding-left: var(--portal-space-5); }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AgentTrace {
  readonly steps = input.required<readonly TraceStepView[]>();
}
```

- [ ] **Step 6: The edits.**
- In `web/src/app/features/ask/could-not-verify-list/could-not-verify-list.ts`, replace
```ts
import { RejectedClaim } from '../../../core/models';
```
  with
```ts
import { RejectedClaimView } from '../answer-view';
```
- In `web/src/app/features/ask/could-not-verify-list/could-not-verify-list.ts`, replace
```ts
        @for (item of rejected(); track item.claim) {
          <li class="claim">
            <p class="claim-text">{{ item.claim }}</p>
            <p class="reason"><span class="reason-label">Why:</span> {{ item.reason }}</p>
```
  with
```ts
        @for (item of rejected(); track item.claimId) {
          <li class="claim">
            <p class="claim-text">{{ item.statement }}</p>
            <p class="reason"><span class="reason-label">Why:</span> {{ item.reason }}</p>
            <p class="reason">{{ item.checksLine }}</p>
```
- In `web/src/app/features/ask/could-not-verify-list/could-not-verify-list.ts`, replace
```ts
readonly rejected = input.required<readonly RejectedClaim[]>();
```
  with
```ts
readonly rejected = input.required<readonly RejectedClaimView[]>();
```
- In `web/src/app/features/ask/answer-card/answer-card.ts`, replace
```ts
import { AnswerView } from '../answer-view';
```
  with
```ts
import { AgentTrace } from '../agent-trace/agent-trace';
import { AnswerView } from '../answer-view';
```
- In `web/src/app/features/ask/answer-card/answer-card.ts`, replace
```ts
imports: [AtAlert, AtButton, CitationChip, CouldNotVerifyList],
```
  with
```ts
imports: [AtAlert, AtButton, CitationChip, CouldNotVerifyList, AgentTrace],
```
- In `web/src/app/features/ask/answer-card/answer-card.ts`, replace
```ts
/** The cited answer: headline, numbered bullets with citation chips, the could-not-verify list. */
```
  with
```ts
/** The cited answer: headline, numbered bullets with citation chips, the could-not-verify list and the agent trace. */
```
- In `web/src/app/features/ask/answer-card/answer-card.html`, replace
```html
  <footer class="answer-footer">
```
  with
```html
  @if (answer().trace.length) {
    <app-agent-trace [steps]="answer().trace" />
  }

  <footer class="answer-footer">
```
- In `web/src/app/core/api/mock-portal-api.spec.ts`, replace
```ts
expect(answered.answer.bullets.length).toBe(3);
```
  with
```ts
expect(answered.answer?.bullets.length).toBe(3);
```

- [ ] **Step 7: Run the ask tests, then the suite and the build**
```bash
(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/features/ask 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)
(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")
(cd web && yarn build 2>&1 | grep -E "ERROR|bundle generation complete")
```
Expected: `Test Files  4 passed (4)`, `Tests  11 passed (11)`; then `Test Files  33 passed (33)` and `Tests  101 passed (101)`. The build prints `Application bundle generation complete.`

- [ ] **Step 8: Look at it.** `(cd web && yarn start)`, http://localhost:4200, click "What is blocking cutover for entity 4?". Expected: [[F4a - Ask panel on the real ask contract - spec]] §1 "Success means" (mock bullets). Open "How this answer was checked (8 steps)": the 5th line reads "Critic: judged each claim against its rows (prompt critic 1.0.0, 01d4c3b8)".

- [ ] **Step 9: Commit**
```bash
git add web/src/app/core/models/ask.ts web/src/app/features/ask web/src/app/core/api/fixtures/ask-E4.json web/src/app/core/api/fixtures/ask-partial.json web/src/app/core/api/mock-portal-api.spec.ts
git commit -m "Ask panel on the /ask contract: trace with prompt versions, cost, partial reason, could-not-verify with verdicts"
```

**Task done when:** `yarn test` reports 101 passed (95 + 6); the panel in mock mode shows the trace, the cost line and "Rejected after 2 checks".

### Task 2: The panel on the live `/ask` (verify in AWS; not dry-run)
Needs: L3 merged and deployed, the ask spine (H2, P2, Y2) live, F2's `portal-config.json` with `"dataSource": "http"`. `<cf>` is the CloudFront domain.

- [ ] **Step 1: The API answers.**
```bash
curl -s -X POST https://<cf>/api/ask -H 'content-type: application/json' -d '{"entity_id": "E4", "question": "What is blocking cutover for entity 4?"}' | python3 -c "import json,sys; body = json.load(sys.stdin); print(body['partial'], len(body['answer']['bullets']), len(body['trace']), body['cost_usd'] > 0)"
```
Expected: `False 3 <n> True` with `<n>` ≥ 3 (the number of trace steps). With `AUTH_MODE=cognito` add `-H "Authorization: Bearer <ID token>"` (a test user's, from Abdul; never paste it into a file or chat).
- [ ] **Step 2: The panel.** In the portal, ask the same question. Expected: the cited answer; each chip opens its rows; the trace lists the steps the API sent with their prompt versions; "Run run-… · cost $0.0…".
- [ ] **Step 3: A partial answer (Q07) through the API:**
```bash
curl -s -X POST https://<cf>/api/ask -H 'content-type: application/json' -d '{"entity_id": "E9", "question": "What is blocking cutover for E9?"}' | python3 -c "import json,sys; body = json.load(sys.stdin); print(body['partial'], body['answer'], bool(body['partial_reason']))"
```
Expected: `True None True`.
- [ ] **Step 4: Record** in the ledger: `Task 2: live — run_id <id> — <n> trace steps — cost <x> — Q07 partial OK — <date time>`.

**Task done when:** Steps 1–3 match; the ledger line exists. If the live answer has a field the contract lacks (the response would fail `ask_response.schema.json`), stop and tell Patrick and Linus: never loosen the types.

### Task 3: Your `HANDOFF.md` line
- [ ] **Step 1:** In `HANDOFF.md` under `## What's real`, add:
```markdown
- The ask panel shows the live `/ask` answer: cited bullets (each opens its source rows), the agent trace with each prompt's version and hash, the cost of the question, partial answers with their reason, and every claim the critic rejected with its reason and number of checks ("Could not verify").
```
- [ ] **Step 2:** `git add HANDOFF.md && git commit -m "HANDOFF: what the ask panel shows"`. Expected: `1 file changed`.

**Task done when:** `grep -c "Could not verify" HANDOFF.md` prints `1`.

### Task 4: Review, then PR (after Clement's OK)
- [ ] **Step 1:** Work through the Review Focus by hand; write each result in the ledger.
- [ ] **Step 2:** `git diff develop --stat` lists only the files this plan names.
- [ ] **Step 3:** Fresh review of the diff against [[F4a - Ask panel on the real ask contract - spec]] (another person, or an agent with no prior context); fix critical and important findings test-first; list minor ones in the PR.
- [ ] **Step 4 (with Clement's OK only):** `git push -u origin feature/web-ask-panel-contract`; open the PR to `develop` titled "Front end: ask panel on the /ask contract (F4a)". Body: what changed, `yarn test` 101 passed (or start + 6), the `Ruling:` lines, deferred minors. Tell Mildred which fixtures changed. No attribution lines.
- [ ] **Step 5:** [[Build order]] row F4: `in review (PR #nn)`, then `merged` when Patrick merges.

**Task done when:** the PR is open to `develop`, Jenkins' front-end build is green, and [[Build order]] shows `in review (PR #nn)`.

## Never
- Compute a KPI, a status or a date in the browser; show what the API returns.
- Send scope (role, entities, tenant) in a request body, query string or header.
- Log, print or store a token yourself.
- Add a `package-lock.json`, or change `yarn.lock` other than with `yarn add`.
- Commit the npm token, a password or any secret.
- Push to `develop` or `main`, or add attribution lines.
- Render bullet or claim text as HTML (`innerHTML`, `bypassSecurityTrust…`).
- Hide a rejected claim or a partial reason.
- Add a field to `ask.ts` that the contract does not have (ask Patrick to change C1 first).

## Done means
- [ ] **Tests:** `(cd web && NO_COLOR=1 yarn test --watch=false 2>&1 | grep -E "Test Files|Tests ")` → `Tests  101 passed (101)` in the dry-run order (your start count + 6). *Verify:* run it.
- [ ] **Fixtures on the contract:** `(cd web && NO_COLOR=1 yarn test --watch=false --include src/app/features/ask/ask-fixtures.spec.ts 2>&1 | grep -E "ERROR\]|Test Files|Tests |AssertionError" | head)` → `Tests  4 passed (4)`. *Verify:* run it.
- [ ] **The panel (mock):** entity 4 suggestion → 3 bullets, 5 chips, "Could not verify" + "Rejected after 2 checks", trace "(8 steps)", "Run run-mock-e4-0001 · cost $0.042"; Entity 2 → partial alert "No claim about this entity passed the critic within the run budget." *Verify:* `yarn start`.
- [ ] **Live (verify in AWS):** Task 2 Steps 1–3 outputs as written; ledger line present.
- [ ] **HANDOFF:** the ask-panel bullet is in `HANDOFF.md`. *Verify:* `grep -c "Could not verify" HANDOFF.md` → `1`.
- [ ] **PR:** open to `develop` titled "Front end: ask panel on the /ask contract (F4a)"; [[Build order]] row F4 updated. *Verify:* `gh pr list --head feature/web-ask-panel-contract`.

Related: [[F4a - Ask panel on the real ask contract - spec]], [[Build order]], [[How to execute a plan]]
