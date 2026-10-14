---
tags: [build, spec, area/frontend]
id: F4a
owner: Clement
status: ready
updated: 2026-10-14
---
# F4a: the ask panel on the real `/ask` contract (spec)
> **The trust story, visible:** the cited answer, the agent trace with prompt versions, the cost per question, partial answers with their reason, and the "could not verify" list with each rejected claim's reason. F4 in [[Build order]] is split: **F4a** (this: the contract and the panel, synchronous `/ask`) and **F4b** ([[F4b - Async ask polling - spec]], only if `/ask` becomes asynchronous). Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after F1b is merged; the live check needs L3.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Clement - front end]].
3. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
4. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
5. [[F1b - Real fixtures and the dashboard on the contract keys - spec]] (Mildred): the fixtures folder and `rows.json` this item relies on.
6. [[L3 - Ask, publish and approve entry points - spec]] (Linus) and [[Huvison - trust and flow]] (§ the writer, the ask spine, the trace).
7. `EVALS.md` (repo) Q01, Q02, Q07, Q08, Q09: what the panel must make visible.
8. `01 Decisions/`: [[2026-10-13 Artefact text is untrusted, critic fails closed]], [[2026-10-13 Prompts as versioned locked files]].
9. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. **`core/models/ask.ts` on the contract** (C1 `AskResponse`): `answer: Answer | null` (`headline`, `bullets[{text, citations}]`, `rejected_count`), `rejected: RejectedClaim[]` with `{claim_id, statement, reason, verdicts: Verdict[]}` (`Verdict` sent with the key `pass`), `cost_usd`, `partial`, `partial_reason: string | null`, `trace: TraceStep[]` (`{step, agent, prompt: {agent, version, sha256} | null}`).
2. **The mock agent fixtures on the contract:** `ask-E4.json` (3 cited bullets, the decoy `DEF-0398` rejected after 2 critic verdicts, an 8-step trace with prompt versions, cost $0.042) and `ask-partial.json` (`answer: null`, `partial: true`, a reason).
3. **The panel shows it all:** numbered bullets with clickable citation chips (Mildred's row viewer), **"How this answer was checked (8 steps)"** with each step and its prompt (`critic 1.0.0, 01d4c3b8`), **"Run … · cost $0.042"**, a **partial answer** with its reason and a fallback headline, and **"Could not verify"** with each statement, its reason and "Rejected after 2 checks".
4. **Live:** the panel on the deployed `/ask` (verify in AWS).

**Why:** Q01/Q02 (cited answer, decoy flagged), Q07 (partial, not a guess), Q08/Q09 (rejected claims shown with reasons), and the rubric's 2.1/2.2 (grounding, evidence of quality). The C1 spec notes the old fixture's `rejected[{claim, reason}]` is superseded by `{claim_id, statement, reason, verdicts}`.

**Success means:**
- Both ask fixtures (without `_mock`) validate against `ask_response.schema.json`; every citation in `ask-E4.json` opens a row in `rows.json`.
- Mock mode, CFO, "What is blocking cutover for entity 4?": headline "Three things block entity 4 from cutover", 3 bullets with 5 chips, "Could not verify" with "Duplicate customer records (DEF-0398) still block cutover for entity 4." and "Rejected after 2 checks", the trace (8 steps), "Run run-mock-e4-0001 · cost $0.042".
- Another entity (mock): the partial answer: headline "This question could not be answered in full", the reason "No claim about this entity passed the critic within the run budget.", no bullets.
- `yarn test`: +6 tests on the start state (101 in the dry-run order).
- **In AWS (verify there):** the same panel on the live answer; a partial for E9 through the API.

**Assumptions (reconcile with the owners):**
- **Trace step names** are the ask-machine state names of `docs/DEVOPS_HANDOVER.md` (`check_budget`, `run_orchestrator`, `store_claims`, `judge_claim`, `retry_decision`, `record_rejection`, `write_answer`) plus one step per sub-agent named after it (`retriever`, `blocker_analyst`). Unknown names are shown as they come, so a different naming only changes the wording. *Confirm with Huvison (H2) and Patrick (P2).*
- **`/ask` stays synchronous** for F4a. If Huvison and Yaw switch to start + poll (the 29-second limit), F4b applies.
- **The fixtures folder is Mildred's;** `ask-E4.json` and `ask-partial.json` are handed to Clement for this change (their shape only compiles with `ask.ts`, which is his). C1 §9 said Mildred aligns `ask-E4.json` in F1; this split moves that line here. *Mildred agrees before Task 1.* L4 will not write these files ([[L4 - Front-end fixtures from the real summary - spec]]).

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Where the trace shows | A collapsed `<details>` "How this answer was checked (N steps)" inside the answer card, one line per step, prompt as `agent version, first 8 of sha256` | Always open (crowds the panel); a separate page (the judges look at one screen) |
| Step wording | A label map in `answer-view.ts` (`STEP_LABELS`); unknown steps show their raw name | Inventing steps the API didn't send |
| "Rejected after N checks" | `verdicts.length`, the count the API sent (display, not a KPI) | Hiding the verdicts |
| Answer `null` | Headline "This question could not be answered in full", no bullets, the `partial_reason` alert | Crashing on `answer.bullets` |
| Mock prompt versions | `0.0.0-mock` with sha256 `mock` (hash not shown) for agents without a locked prompt yet; the critic's real `1.0.0` / `01d4c3b8…` from `agents/prompts/prompts.lock` | Made-up hashes that look real |
| Decoy row `WP-032` in the old fixture | Dropped from bullet 2: it is not a row any exported fixture cites, so the chip would open nothing in mock mode | Adding it to `rows.json` by hand (fixtures are exported, never hand-edited) |

## 3. The shapes
`core/models/ask.ts`: `AskRequest`, `Bullet`, `Answer`, `Verdict`, `RejectedClaim`, `PromptRef`, `TraceStep`, `AskResponse` as in §1 (replaces `AnswerBullet` and the old `RejectedClaim`). `features/ask/answer-view.ts`: `AnswerView` gains `trace: TraceStepView[]` (`{number, text}`) and `rejected: RejectedClaimView[]` (`{claimId, statement, reason, checksLine}`); `headline` falls back when `answer` is null. `features/ask/agent-trace/agent-trace.ts` *(new)*: `<app-agent-trace [steps]>`.

## 4. Tests
- `features/ask/ask-fixtures.spec.ts` *(new)*, 4: both fixtures vs the contract; ask-E4 citations resolve in `rows.json`; the trace's prompt agents and the rejected claim's two `pass: false` verdicts; the partial fixture.
- `features/ask/answer-view.spec.ts`, 4 (was 2): bullets and checked line; rejected with reason and "Rejected after 2 checks"; the 8 trace lines; the partial view.
- `features/ask/answer-card/answer-card.spec.ts`, 2: chips (5), could-not-verify text, 8 trace items and the critic's prompt line; a chip opens its row.

## 5. Out of scope
- The 403 refusal and role views: **F3b**. Polling an async `/ask`: **F4b**. Publish/approve: **F5**.
- What the agents put in the trace (Huvison, Patrick); the eval runner.

Related: [[F4a - Ask panel on the real ask contract - plan]], [[Build order]], [[Clement - front end]]
