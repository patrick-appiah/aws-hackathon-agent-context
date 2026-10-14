---
tags: [build, spec, area/flow]
id: H2b
owner: Huvison
status: awaiting review
updated: 2026-10-14
---
# H2b: The agent-calling states, the in-process spine and the Lambda handlers (spec)
> **Split of H2** (see [[H2a - Budget and ledger states - spec]]). H2b adds the three states that call agents (`run_orchestrator`, `judge_claim`, `write_answer`), `infra/functions/spine.py` (the whole ask spine in-process, in the state machine's order) and `infra/functions/states.py` (one JSON Lambda entry point per state, for Yaw's FlowStack). After H2b, `/ask` runs end to end locally with stub agents, and Step Functions can call every state. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` once H2a, H3 and H5 are merged. The repo is the source of truth for code; the vault is the source of context.

## 0. Context: read the vault first
The team vault is the shared context space for this project. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Workstreams]] §2 (the ask spine), §4 and §7.
3. [[Huvison - trust and flow]] §3 "The step functions": the owner's brief.
4. [[Build order]]: H2b needs **H2a, H3 (the writer) and H5 (cost)** merged, and P1 (`agents/agent_support.py` *(new)*, via H3). It does **not** need P2: the orchestrator is imported only when it runs, and the tests use a stand-in.
5. [[H2a - Budget and ledger states - spec]], [[H3 - Writer agent - spec]], [[H5 - Cost per run - spec]], [[H1 - Ledger extensions - spec]].
6. Patrick's [[P2 - Orchestrator agent - spec]] (`orchestrate`, `replan`, A4) and [[P3 - Local ask runner - spec]] (B2, B4, B7, and "if H2 ships a function that already runs the whole sequence"). Linus's [[L3 - Ask, publish and approve entry points - spec]] (how `/ask` starts the machine).
7. `01 Decisions/`: [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]] (D-007), [[2026-10-13 Artefact text is untrusted, critic fails closed]] (D-009), [[2026-10-13 Scope from the token, enforced twice]] (D-010); the repo's `DECISIONS.md` D-012, D-021; the repo's `docs/DEVOPS_HANDOVER.md`.
8. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` ([[Hackathon guideline]] §02: the critic never sees the plan or the attempt count; the rejected edge is a guard, not an agent), `03 Sessions/`, `Open follow-ups.md` (the critic's prompt provenance item). If the vault doesn't answer it, stop and ask Huvison. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. In `infra/functions/steps.py` *(new)*:
   - `run_orchestrator(question, *, ledger, repository, rejected_claim=None, verdict=None, orchestrator=None) -> OrchestratorResult`: P2's `orchestrate` for the first plan, `replan` with the critic's last verdict for a rejected claim; a re-plan keeps at most one claim, **only under the rejected claim's ID**; records the cost (`record_usage`) and a trace step with the orchestrator's prompt version;
   - `judge_claim(run_id, claim, scope, *, ledger, repository, critic_agent=None) -> dict`: the blind critic (`agents.critic.judge`) on **the ledger's copy** of the claim, under **the run's scope** (another scope raises `OutOfScope`); records the verdict (the attempt count rises), the critic's token usage and a trace step with the critic's prompt version from the verdict;
   - `write_answer(run_id, question, passed_claims, *, ledger, repository=None, writer=None, partial=None) -> AskResponse`: the writer (H3) on the claims **the ledger marks passed**; `rejected` from the rejected records, `cost_usd` from the run, `trace` from the steps, `partial` / `partial_reason`; a partial run with nothing passed has no answer and calls no writer;
   - `OrchestratorAgent` (Protocol), `Writer`, `prompt_ref`, `real_orchestrator`, `real_writer`.
2. `infra/functions/spine.py` *(new)*: `run_spine(question, *, ledger, repository, agents=SpineAgents()) -> AskResponse` and `settle_claim(...)`: the states in the Express machine's order, every loop bounded by `retry_decision`.
3. `infra/functions/states.py` *(new)*: `check_budget`, `run_orchestrator`, `store_claims`, `judge_claim`, `retry_decision`, `record_rejection`, `write_answer`, each `(event: dict, context) -> dict`, with strict event models; ledger and repository built once per container from settings.
4. `docs/DEVOPS_HANDOVER.md`: the ask-machine rows point at `infra.functions.states.<state>`, with each state's event and result; the ASL outline for Yaw.

**Why:** the brief's §3 sequence, D-007's fixed order, and the D1 16:00 milestone "the full `/ask` sequence runs locally with stubs, including one retry and one rejection". Yaw's FlowStack (Y2) needs one entry point per state; Patrick's `scripts/ask.py` *(new)* (P3) and the eval asker (H6) need the same sequence in-process.

**Success means:**
- With stub agents: a supported claim reaches the answer with its citations; a rejected claim is re-planned under its own ID and passes; a claim the critic never passes is rejected after **2 attempts with 2 verdicts** (the lead's limit, H2a) and appears in `AskResponse.rejected`; a re-plan that brings back no claim ends in the rejected records; an unknown entity answers partial with no critic and no writer call; claims gathered before the budget ran out are judged and the answer is partial; a budget spent at the start answers partial without any agent.
- The critic judges the stored claim, never a caller's edited copy, and never runs under a scope other than the run's.
- Every model call's tokens and cost land on the run (orchestrator, critic, writer), and `AskResponse.cost_usd` equals the ledger's.
- The seven handlers chain through JSON to a rejected record, and refuse unknown keys.
- `uv run --locked pytest`: start + **23 passed**; coverage not lower; `uv run python -c "import infra.functions.steps"` works without P2.

**Assumptions about other items (the reviewer reconciles these):**
- **P2** exposes `agents.orchestrator.orchestrate(question, repository, ledger, ...) -> OrchestratorResult` and `replan(question, rejected_claim, verdict, repository, ledger, ...) -> OrchestratorResult` ([[P2 - Orchestrator agent - plan]] Task 2–3), numbers claim IDs in code and returns the rejected ID on a re-plan. `run_orchestrator` imports the module on first use (`real_orchestrator()`), so H2b merges and runs its tests before P2.
- **P1/H3:** `agents.agent_support.usage_of(reply, model_id)`; `agents.writer.write`, `verbatim_answer`, `WRITER_AGENT_NAME`.
- **Yaw (Y2)** writes the ASL from §3's state table and carries `run_id` and `claim_id` between states. The execution input is the bare Question JSON (L3). The ASL passes $$.Execution.Input as question to run_orchestrator and write_answer. The WriteAnswer result is the execution output, with no wrapper key (L3 validates it with AskResponse.model_validate_json).
- **Linus (L3)** builds its own `Question` (a lead decision), starts the Express machine with it and returns the machine's output, the `write_answer` result, as the `/ask` body.

**Alignment with Patrick's assumed signatures (P3 B2, B4, B7; P2 A4):**
| Patrick assumed | H2b ships | Difference and why |
|---|---|---|
| B2 `run_orchestrator(question, *, ledger, repository, rejected_claim=None, verdict=None)` | same, plus `orchestrator=` (a stand-in for tests and H6) | When `verdict` is omitted on a re-plan, the critic's last verdict is read from the ledger. A re-plan's claims under any other ID are **dropped and logged** (D-012: a fresh ID would start a fresh counter) |
| B4 `judge_claim(run_id, claim, scope, *, ledger, repository) -> verdict dict` | same, plus `critic_agent=` | It judges **the ledger's copy** of `claim.claim_id`, and refuses a `scope` other than the run's (`OutOfScope`), so what the critic sees is exactly what was stored under the run's own scope |
| B7 `write_answer(run_id, question, passed_claims, *, ledger, repository) -> AskResponse` | same; `repository` optional (unused: the writer needs no rows); plus `writer=` and `partial=` | Only claims the **ledger** marks passed reach the writer (others dropped and logged); with `partial`, the response is marked partial and, if nothing passed, has no answer and no writer call (P3 builds that response itself today; it may pass `partial=` instead) |
| A4: the trace step carries `load_prompt("orchestrator").provenance()` | `prompt_ref("orchestrator")`: the provenance, or `None` while no prompt file exists | lets H2b's tests run before P2's prompt is merged |
| P3: "if H2 ships a function that already runs the whole sequence, `run_spine` calls it" | `infra.functions.spine.run_spine(question, *, ledger, repository, agents)` | P3 may call it (a Ruling on P3's side); its order matches P3 §1 "Success means", including "a re-plan with no new claim records the rejection" and "claims gathered before the budget ran out are judged" |

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Where the orchestrator comes from | `orchestrator=` if given, else `importlib.import_module("agents.orchestrator")` on first use | A top-level import (P2 imports `tools.budget`; also H2b would need P2 merged) |
| A re-plan returning other IDs | Keep only the first claim under the rejected ID; drop the rest and log | Storing them as new claims (dodges the retry limit: a fresh counter) |
| What the critic judges | `ledger.claim(run_id, claim.claim_id)` | The caller's copy (Step Functions JSON could carry an edited claim) |
| The critic's scope | Must equal the run's stored scope, else `OutOfScope` before any model call | Trusting the caller's scope |
| Critic token usage | The critic agent is wrapped in a recorder; every reply goes through `agent_support.usage_of` | Changing `critic.judge`'s return (the tested, fail-closed security path) |
| Writer input | The ledger's passed claims among those given, in the ledger's copy | Whatever the caller passes |
| A re-plan with no claim | `record_rejection` for that claim (P3's decision) | Judging the old content again (same verdict, wasted call) |
| A partial from the orchestrator with claims | Judge the claims gathered; answer marked partial (P3's decision) | Dropping verified evidence |
| Spine order of claims | One claim at a time to a verdict (pass or rejected record), in plan order | Judging all, then re-planning all (harder to bound and to trace) |
| Lambda events | Strict models (`extra="forbid"`); claims, verdicts and the scope for the critic are read from the ledger by `run_id` and `claim_id`, never taken from the event | Passing whole claims and scopes through the event (tamperable, and large) |
| Lambda dependencies | `make_ledger()`, `make_repository()` cached per container (`lru_cache`), from `ledger_from_settings()` / `repository_from_settings()` | Building them per call (slower), module globals (untestable) |
| `check_budget` handler output | `{run_id, remaining_usd, partial}`: one shape for the machine's Choice | Returning a bare float or a `PartialAnswer` (two shapes for one state) |

## 3. Shapes and behaviour
**`infra/functions/steps.py` additions:** constants `STEP_RUN_ORCHESTRATOR`, `STEP_JUDGE_CLAIM`, `STEP_WRITE_ANSWER`, `ORCHESTRATOR_AGENT_NAME = "orchestrator"`, `ORCHESTRATOR_MODULE = "agents.orchestrator"`; `logger`; `OrchestratorAgent(Protocol)` with `orchestrate(question, repository, ledger)` and `replan(question, rejected_claim, verdict, repository, ledger)`; `Writer(Protocol)` with `__call__(writer_input: WriterInput) -> WriterResult`; `prompt_ref(agent_name) -> PromptRef | None`; `real_orchestrator() -> OrchestratorAgent`; `real_writer() -> Writer`; the three states in §1.

**Trace steps** (`AskResponse.trace`): `check_budget`, `run_orchestrator` (agent `orchestrator`, its prompt), `store_claims`, `judge_claim` (agent `critic`, the verdict's prompt; `None` when code rejected it before any model call), `retry_decision`, `record_rejection`, `write_answer` (agent `writer` when an answer was written, its prompt when claims passed).

**`infra/functions/spine.py`:** `SpineAgents(orchestrator=None, writer=None, critic_agent=None)` (frozen dataclass; `None` = the real one); `settle_claim(question, claim, *, ledger, repository, agents) -> tuple[BlockerClaim | None, PartialAnswer | None]`; `run_spine(question, *, ledger, repository, agents=SpineAgents()) -> AskResponse`. Raises `OutOfScope` (from `check_budget`) before anything is written.

**`infra/functions/states.py` (the ask machine's Lambdas, `infra.functions.states.<state>`):**
| State | Event | Result |
|---|---|---|
| `check_budget` | `Question` | `{run_id, remaining_usd, partial}` |
| `run_orchestrator` | `{question, claim_id?}` (`claim_id`: re-plan that claim; claim and last verdict read from the ledger) | `OrchestratorResult` |
| `store_claims` | `{run_id, claims}` | `{claims}` |
| `judge_claim` | `{run_id, claim_id}` (claim and scope from the ledger) | `{run_id, claim_id, passed}` |
| `retry_decision` | `{run_id, claim_id, max_attempts?}` | `{run_id, claim_id, decision}` |
| `record_rejection` | `{run_id, claim_id}` | `RejectedClaim` (verdicts with the key `pass`) |
| `write_answer` | `{question, partial?}` (passed claims from the ledger) | `AskResponse` (by alias) |

**ASL outline for Yaw (Y2), not code in this repo:** `CheckBudget` → Choice on `$.budget.partial` (not null → `WriteAnswer` with `partial`) → `RunOrchestrator` → `StoreClaims` → Map over `$.claims` (MaxConcurrency 1): `JudgeClaim` → Choice `passed` → end of iteration; else `RetryDecision` → Choice `decision == "retry"` → `RunOrchestrator` with `claim_id` → `StoreClaims` → `JudgeClaim` (loop); `"reject"` → `RecordRejection` → end of iteration → after the Map, `WriteAnswer`. The loop is bounded by `retry_decision` (2 attempts).

## 4. Tests (new)
- `tests/infra/functions/test_steps.py` *(new)* (appended, 12): `run_orchestrator` records cost and a trace step; a re-plan gets the claim and the critic's last verdict from the ledger; a re-plan keeps only a claim under the rejected ID (and logs the rest); `judge_claim` records a passing verdict with the critic's prompt and token usage; counts a rejection; judges the ledger's copy, not the caller's; refuses another scope without a model call; rejects an out-of-scope citation without a model call; `write_answer` words only ledger-passed claims (cost and trace included), reports rejected claims and their count, has no answer for a partial with nothing passed; the real writer is the default.
- `tests/infra/functions/test_spine.py` *(new)*, 7: the scenarios in §1 "Success means".
- `tests/infra/functions/test_states.py` *(new)*, 4: the seven handlers chained through JSON to a rejected record (with `write_answer` reporting it); a spent budget comes back as a partial; unknown event keys are refused; dependencies come from settings and are cached.

## 5. Out of scope
- The ASL and the FlowStack (Yaw, Y2); the API entry point (Linus, L3); `scripts/ask.py` (Patrick, P3).
- The orchestrator itself (P2) and its prompt.
- Publish and approve (H4), the eval asker and `inject` (H6).
- Async `/ask`: the 29-second check and the async decision are [[H7 - Guardrail settings and ask latency - spec]].

Related: [[H2b - Agent states, local spine and Lambda handlers - plan]], [[H2a - Budget and ledger states - spec]], [[Huvison - trust and flow]], [[Build order]]
