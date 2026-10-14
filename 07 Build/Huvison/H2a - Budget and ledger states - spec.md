---
tags: [build, spec, area/flow]
id: H2a
owner: Huvison
status: awaiting review
updated: 2026-10-14
---
# H2a: The budget check and the ask-spine states that only touch the ledger (spec)
> **Split of H2.** H2 (`flow/budget.py` + `flow/steps.py`, the ask-spine states) is too big for one session, so it is two items: **H2a** (this note: `require_budget`, `check_budget`, `store_claims`, `retry_decision`, `record_rejection`, which need no agent) and [[H2b - Agent states, local spine and Lambda handlers - spec]] (`run_orchestrator`, `judge_claim`, `write_answer`, the in-process spine and the Lambda entry points). Each is testable and mergeable on its own. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` once C1, H1 and H5 are merged. The repo is the source of truth for code; the vault is the source of context.

## 0. Context: read the vault first
The team vault is the shared context space for this project. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Workstreams]] §2 (the ask spine), §4 (the budget-check contract) and §7.
3. [[Huvison - trust and flow]] §2 "The budget check" and §3 "The step functions": the owner's brief.
4. [[Build order]]: H2 depends on C1 and H1; this split also needs **H5** (`flow/` exists; H2b records cost). Check all three are `merged`.
5. [[H1 - Ledger extensions - spec]] (the ledger methods used here), [[C1 - API and spine contracts - spec]] §3–§4 (`Question`, `PartialAnswer`, `RejectedClaim`, `TraceStep`, `AskRequest`).
6. Patrick's [[P2 - Orchestrator agent - spec]] (assumptions A1, A2: `require_budget`, `flow/__init__.py` *(new)*) and [[P3 - Local ask runner - spec]] §1 (assumed signatures B1, B3, B5, B6), which call these functions.
7. `01 Decisions/`: [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]] (D-007), [[2026-10-13 Scope from the token, enforced twice]] (D-010); the repo's `DECISIONS.md` D-012. `05 Workflow/`: [[Dev loop]].

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` ([[Hackathon guideline]] §02 "the reject loop", non-negotiable 2 "every loop has a bound"), `03 Sessions/`, `Open follow-ups.md`. If the vault doesn't answer it, stop and ask Huvison. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. `flow/budget.py` *(new)*: `require_budget(ledger, run_id) -> float | PartialAnswer`, the one budget rule. Two callers: the `check_budget` state and Patrick's orchestrator before each step and re-plan (P2, A1).
2. `flow/steps.py` *(new)*, the ledger-only states and their helpers:
   - `question_for(scope, request, settings=None) -> Question`: a fresh `run_id`, `budget_usd = run_budget_usd`, `max_attempts = max_claim_attempts` (for Linus's `/ask`, Patrick's `scripts/ask.py` *(new)* and H6);
   - `record_step(ledger, run_id, step, agent=None, prompt=None)`: one `TraceStep` in the ledger;
   - `check_budget(question, *, ledger) -> float | PartialAnswer`: refuse an out-of-scope entity **before anything is written**, start the run, record the step, `require_budget`;
   - `store_claims(run_id, claims, *, ledger) -> list[BlockerClaim]`: `put_claim` for a new claim ID, `revise_claim` for one the run already has;
   - `retry_decision(run_id, claim_id, *, ledger, max_attempts=None) -> "retry" | "reject"`: the ledger's counter against the limit;
   - `record_rejection(run_id, claim_id, *, ledger) -> RejectedClaim`: `put_rejected` with all the claim's verdicts;
   - `stored_claim(...)`, `rejected_claim(record) -> RejectedClaim` (shared with H2b and H4).

**Why:** the ask spine's order is fixed (D-007); only the agents are agentic. The retry bound and the budget ceiling are the guideline's non-negotiables 2 and 5, and the rubric scores them ("a blind critic that actually rejects, a ledger-bounded retry, … a budget ceiling", brief). Putting them in code on the ledger means no model can see, decide or reset them (D-012).

**The retry limit (decided by the lead; not open):** a claim gets **at most 2 attempts in total, one retry**. `config.py` keeps `max_claim_attempts = 2`; `retry_decision` returns `"retry"` while the ledger's attempt count is below 2, otherwise `"reject"`. A claim the critic rejects twice lands in the rejected records with exactly **2 verdicts** (EVALS Q09; the lead's session corrects `EVALS.md` and `evals/expected/Q09.json`, which said 3).

**Success means:**
- `require_budget` returns the remaining USD while it's above 0, else a `PartialAnswer` whose reason names the budget; an unknown run raises `LedgerConflict`.
- `check_budget` with an out-of-scope entity raises `OutOfScope` and **no run exists afterwards** (EVALS Q11: no E2 rows reach the ledger); a second `check_budget` for the same run raises (create-once).
- `store_claims` puts new IDs, revises known IDs (attempts kept), refuses two claims with one ID in a call.
- `retry_decision` gives `retry` after 1 verdict and `reject` at 2 (the configured limit), reading only the counter.
- `record_rejection` copies the claim with every verdict, and refuses an unknown claim or one whose last verdict passed.
- `uv run --locked pytest`: start + **19 passed**; coverage not lower; `uv run python -c "import flow.steps"` works.

**Assumptions:**
- C1, H1 and H5 are merged (H5 created `flow/__init__.py`, docstring only, and `--cov=flow`).
- P2's orchestrator numbers claim IDs in code (`claim-1`, `claim-2`, …) and a re-plan returns the rejected claim's ID ([[P2 - Orchestrator agent - spec]], "Claim IDs"). H2b's `run_orchestrator` enforces the second rule; `store_claims` relies on both.
- Linus's `/ask` (L3) builds the `Question` itself or with `question_for`; both are fine.

**Alignment with Patrick's assumed signatures (P3 B1, B3, B5, B6; P2 A1, A2):**
| Patrick assumed | H2a ships | Difference and why |
|---|---|---|
| A1 `require_budget(ledger, run_id) -> float \| PartialAnswer` | same | none |
| A2 `flow/__init__.py` doesn't import `flow.steps` | same (H5's docstring-only file) | none |
| B1 `check_budget(question, *, ledger) -> float \| PartialAnswer` | same | also refuses an out-of-scope entity before `start_run` (D-010's second check; L3 refuses first) |
| B3 `store_claims(run_id, claims, *, ledger) -> None` | returns the stored claims | a return value the caller may ignore (the Lambda handler passes it to the next state); also refuses duplicate IDs in one call |
| B5 `retry_decision(run_id, claim_id, *, ledger) -> "retry" \| "reject"` | same, plus optional `max_attempts=` | default is `max_claim_attempts`; the spine passes `question.max_attempts` (same value) |
| B6 `record_rejection(run_id, claim_id, *, ledger) -> None` | returns the `RejectedClaim` | a return value the caller may ignore; refuses a claim that isn't rejected |

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Ports | Keyword-only `ledger=` (and `repository=` in H2b), so one in-memory ledger is shared locally and the Lambda handlers build them from settings | Module-level ledger (untestable, shared across tests) |
| Budget threshold | Spent when `budget_remaining ≤ 0` (`BUDGET_SPENT_AT_USD = 0.0`); one call may overshoot, the next is refused | A reserve per step (a guess at the next call's cost) |
| Who refuses an out-of-scope entity | L3 first (403 before any execution); `check_budget` again before `start_run` (scope enforced twice, D-010) | Only the API (a direct state call or the local runner would start a run) |
| Claim IDs | The orchestrator's code numbers them (P2); `store_claims` puts new IDs and revises known ones (B3) | Renumbering again in `store_claims` (two numbering rules; P3 expects P2's IDs) |
| Duplicate IDs in one call | `ValueError`, nothing written | Last one wins (silently overwrites a claim) |
| Retry limit source | `get_settings().max_claim_attempts` (2) unless `max_attempts` is given | Reading it from the claim or the event only (a caller could raise it) |
| Rejecting a non-rejected claim | `LedgerConflict` | Allowing it (a passed claim could be hidden in "could not verify") |
| Rejected reason shown | The last verdict's reason | A separate field (second copy) |
| `question_for` here | Yes: one place that applies the budget and the retry limit from `config.py` | Each caller building `Question` (three copies of the defaults) |

## 3. Shapes
`flow/budget.py`: `BUDGET_SPENT_AT_USD = 0.0`, `USD_FORMAT = ".2f"`, `require_budget(ledger: Ledger, run_id: str) -> float | PartialAnswer` (reason: `the run's budget of 0.50 USD is spent (0.50 USD used)`).

`flow/steps.py`: constants `RUN_ID_PREFIX = "run-"`, `RETRY = "retry"`, `REJECT = "reject"`, `STEP_CHECK_BUDGET`, `STEP_STORE_CLAIMS`, `STEP_RETRY_DECISION`, `STEP_RECORD_REJECTION` (the state names, used as trace step names); the functions in §1. Every state appends a trace step `{step: <state name>, agent: null, prompt: null}`.

## 4. Tests
- `tests/flow/test_budget.py` *(new)*, 4: remaining amount; spent (exactly and over) → `PartialAnswer`; unknown run raises.
- `tests/flow/test_steps.py` *(new)*, 15: `question_for` uses the settings and fresh run IDs; `check_budget` starts the run and returns the budget, refuses out of scope with no run written, can't restart a run, returns a `PartialAnswer` when nothing is left; `store_claims` puts, revises keeping attempts, refuses duplicate IDs, needs a started run; `retry_decision` (1 → retry, 2 → reject, 3 → reject) and its default limit; `record_rejection` moves every verdict, and refuses unknown or not-rejected claims.

## 5. Out of scope
- `run_orchestrator`, `judge_claim`, `write_answer`, the in-process spine, the Lambda handlers (H2b).
- The Step Functions definition (Yaw, Y2) and the API entry point (Linus, L3).

Related: [[H2a - Budget and ledger states - plan]], [[H2b - Agent states, local spine and Lambda handlers - spec]], [[Huvison - trust and flow]], [[Build order]]
