---
tags: [build, spec, area/frontend]
id: F4b
owner: Clement
status: ready (conditional)
updated: 2026-10-14
---
# F4b: the ask panel polls an asynchronous `/ask` (spec)
> **Only if `/ask` becomes asynchronous.** Huvison times a full `/ask` with one retry against API Gateway's 29-second limit by D1 18:00; if it is too slow, he proposes to Patrick an async start (`POST /ask` returns `run_id`) plus polling (`GET /ask/{run_id}`), and Yaw builds it. **If that decision is not recorded, do not start this item.** Second part of F4 (after [[F4a - Ask panel on the real ask contract - spec]]). Repo: `Amali-Tech/cloud-9-hackathon`.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Clement - front end]].
3. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
4. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
5. [[F4a - Ask panel on the real ask contract - spec]]: the panel and the `AskResponse` types.
6. [[Huvison - trust and flow]] (the 29-second check) and [[Yaw - DevOps]] (§ the async fallback); `DECISIONS.md` (repo) for the recorded async decision.
7. [[Mildred - front end]]: the `PortalApi` port and adapters are hers.
8. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

## 1. Intent
**What:** when `POST /ask` answers "still running", the panel polls `GET /ask/{run_id}` every 2 seconds, shows **"Still checking the evidence (run <id>)"**, and shows the answer when it arrives; after 30 polls (a minute) it stops with **"The answer is taking longer than expected. Run <id> is still working; try again in a minute."** A synchronous `/ask` keeps working unchanged.

**Why:** the brief (Clement, item 3): "if Huvison and Yaw switch `/ask` to async …, the panel polls with a progress state". A live demo question must never die on a 504.

**Success means:** with a fake API that answers pending, pending, then the E4 answer: two polls 2,000 ms apart, the progress line during both, then the answer; with an API that never finishes: exactly 3 polls (test setting) and the timeout message. `GET /ask/run-async-1` is the URL. `yarn test`: +3. **In AWS (verify there):** a slow question shows the progress line, then the answer.

**Assumptions (the decided shape must match; if it doesn't, stop and ask Patrick):**
- `POST /ask` answers either the full `AskResponse` (fast path) or **`{"run_id": "<id>", "status": "running"}`** (HTTP 200 or 202).
- `GET /ask/{run_id}` answers `{"run_id", "status": "running"}` while working, and the full `AskResponse` when done (`AskResponse` has no `status` key, which is how the two are told apart). Errors use `ErrorResponse`; a run the caller may not see is 403/404.
- Neither shape is in C1 yet: Patrick adds `AskPending` to `tools/api_schema.py` with the decision; then this item's type is checked against the exported schema.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Interval and limit | 2,000 ms × 30 polls (`ASK_POLL_INTERVAL_MS`, `ASK_POLL_MAX_ATTEMPTS` in `ask-store.ts`), injectable as `ASK_POLLING` so tests don't wait | Hardcoded `setTimeout` (slow, flaky tests); WebSockets (a new API for one screen) |
| Telling pending from done | `isAskPending(body)`: `status === 'running'` | The HTTP status (202) alone (Angular's `HttpClient` hides it unless `observe: 'response'`; the body is enough) |
| Port change | `PortalApi.askResult(runId)` (new); `ask()` may return `AskPending`. The mock never returns pending | A second store for async runs |

## 3. Tests
`core/api/http-portal-api.spec.ts` +1 (`GET /ask/{run_id}`); `features/ask/ask-polling.spec.ts` *(new)* 2 (polls until answered with progress; gives up after the last attempt).

## 4. Out of scope
The async API itself (Huvison, Yaw, Linus); cancelling a run; resuming a run after a page reload.

Related: [[F4b - Async ask polling - plan]], [[F4a - Ask panel on the real ask contract - spec]], [[Build order]]
