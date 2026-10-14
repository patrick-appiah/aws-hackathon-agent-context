---
tags: [build, spec, area/evals]
id: H6
owner: Huvison
status: awaiting review
updated: 2026-10-14
---
# H6: The local eval asker, `infra/functions/local.py` (spec)
> **The eval runner's way into the agent loop:** `uv run python -m evals.run --asker infra.functions.local:ask` asks all 14 questions through the real ask spine in-process, and plants the two faults Q08 and Q09 need. Only this asker can plant them. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` once H2b and **P2** are merged. The repo is the source of truth for code; the vault is the source of context.

## 0. Context: read the vault first
The team vault is the shared context space for this project. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Workstreams]] §4 (the eval runner contract) and §7.
3. [[Huvison - trust and flow]] §7 "The local asker": the owner's brief.
4. [[Build order]]: H6 depends on H2 (H2a and H2b) and P2. Check they are `merged`.
5. [[H2b - Agent states, local spine and Lambda handlers - spec]] (`run_spine`, `SpineAgents`, `real_orchestrator`, `real_writer`), [[H2a - Budget and ledger states - spec]] (`question_for`, the retry limit), [[P2 - Orchestrator agent - spec]] (claim IDs `claim-1`, … via `tools.constants.CLAIM_ID_PREFIX`).
6. The repo's `evals/run.py` (the asker contract in its docstring), `EVALS.md`, `evals/inputs/Q08.json`, `Q09.json`, `Q11.json`, `evals/expected/`.
7. Abdul's [[A1 - Eval set review and manual checks - spec]] and [[A5a - EVALS results write-up - spec]] (who reads the results). `01 Decisions/`: [[2026-10-13 Artefact text is untrusted, critic fails closed]], [[2026-10-13 Scope from the token, enforced twice]].
8. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` ([[Hackathon guideline]]: "keep a deliberately weak input in the demo set and let it get rejected"), `03 Sessions/`, `Open follow-ups.md`. If the vault doesn't answer it, stop and ask Huvison. Never invent a name, a shape or a rule.

## 1. Intent
**What:** `infra/functions/local.py` *(new)*:
- `ask(case_input, scope, repository) -> dict`: the asker contract of `evals/run.py`. Builds the `Question` with `question_for`, runs `infra.functions.spine.run_spine` on a fresh `InMemoryLedger` with the real agents (P2's orchestrator, the Bedrock critic, H3's writer), and returns the `AskResponse` as a dict (`by_alias=True`). An entity outside the asker's scope returns `{"refused": true, "status_code": 403}` **before anything is written** (Q11).
- `inject` applied here, and only here:
  - **`strip_citations` (Q08):** `CitationStrippingLedger` stores `claim-1` with an empty chain on the first plan and on every re-plan, as if the analyst had sent it uncited. The critic's pre-check rejects it **in code, without a model call**, until the retry guard moves it to the rejected records.
  - **`force_unsupportable_claim` (Q09):** `WithUnsupportableClaim` wraps the orchestrator: the real orchestrator still plans (and costs); its plan gains one more claim under the next free ID, *"E4 customer master reconciled at 100 % in cycle C3 and is ready for cutover"*, citing `RC-C3-E4-customers` (which says FAIL at 91.2 %); its re-plan returns that claim unchanged. The real critic must reject it; after **2 attempts (one retry)** it lands in the rejected records with **exactly 2 verdicts**.
  - an unknown `inject` raises `ValueError`.
- `make_orchestrator()`, `make_critic_agent()`, `make_writer()`, `ledger_for(inject)`: the seams the tests replace.

**The Q09 verdict count (decided by the lead; not open):** a claim gets at most 2 attempts in total (one retry). `config.py` keeps `max_claim_attempts = 2`; `retry_decision` returns `"retry"` while the ledger's attempts are below 2. Q09's forced claim ends with **2 verdicts**. The lead's session corrects `EVALS.md` and `evals/expected/Q09.json` (they said 3); this item doesn't touch them.

**Why:** Q08 and Q09 are the evals that prove the critic rejects and the retry guard bounds the loop (rubric: "a blind critic that actually rejects, a ledger-bounded retry"); they need a planted fault, and no fault switch may exist in the API, the state machine or `config.py` (brief). The same asker is how Abdul's results (A5a) and the worked examples (A5b) are produced.

**Success means:**
- With stand-in agents, the eval runner scores Q01, Q07, Q08, Q09 and Q11 as `pass` through `infra.functions.local:ask`.
- Q08: `claim-1` is rejected and the critic model is never asked.
- Q09: exactly one rejected record for the forced claim, with **2 verdicts**, after exactly one re-plan of it.
- Q11: `{"refused": true, "status_code": 403}`, and no run in the ledger.
- No `inject`: the plain spine (Q01's claim passes and is the answer's one bullet).
- `uv run --locked pytest`: start + **11 passed**; coverage not lower.
- With AWS credentials (verify in AWS): `uv run python -m evals.run --asker infra.functions.local:ask` runs all 14, writes `evals/results/run-*.json`, and Q08, Q09, Q12 pass (or their failures are recorded honestly for A5a).

**Assumptions:**
- P2 is merged: `tools.constants.CLAIM_ID_PREFIX = "claim-"`, `agents.orchestrator.orchestrate` / `replan` with the signatures in [[H2b - Agent states, local spine and Lambda handlers - spec]] §1, and claim IDs numbered from `claim-1`.
- The live run needs `AWS_PROFILE=hackathon`, `AWS_REGION=eu-west-1`, Bedrock access for your sign-in, and P1, L5 (the analyst) and H3 merged. No unit test calls Bedrock.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Where Q08's fault is planted | In the ledger the asker builds: `claim-1` stored with no citations, on every write | Building an uncited `BlockerClaim` (the model refuses an empty chain, `min_length=1`, so the fault couldn't reach the critic); a flag in the API or config (forbidden) |
| Which claim Q08 strips | `claim-1` (the analyst's first, P2's numbering) | A random claim (non-reproducible) |
| Q09's forced claim | Added under the next free ID, after the real claims; cites a real, in-scope row that contradicts it, so the pre-check passes and the **real critic** must judge it | Citing a missing row (the pre-check would reject it without the critic: that's Q08's test) |
| Q09's re-plan | The real `replan` runs (cost, trace) and its claims are replaced by the forced claim | Skipping the re-plan (the run wouldn't be the real loop) |
| Q09 verdict count | **2** (the lead's ruling: 2 attempts, one retry; `max_claim_attempts = 2`) | 3 (the earlier EVALS text) |
| Refusal | `OutOfScope` from `check_budget` (before `start_run`) → `{"refused": true, "status_code": 403}` | Checking the scope again in the asker (one rule, in the spine) |
| Ledger | A fresh `InMemoryLedger` per question | One shared ledger (run IDs are unique anyway; a fresh one keeps cases independent) |

## 3. Shapes (`infra/functions/local.py`)
Constants: `INJECT_STRIP_CITATIONS`, `INJECT_FORCE_UNSUPPORTABLE_CLAIM`, `KNOWN_INJECTS`, `FIRST_CLAIM_ID = f"{CLAIM_ID_PREFIX}1"`, `REFUSED_STATUS_CODE = 403`, `UNSUPPORTABLE_STATEMENT`, `UNSUPPORTABLE_CHAIN`.
| Name | Signature |
|---|---|
| `CitationStrippingLedger(InMemoryLedger)` | `put_claim`, `revise_claim` strip `claim-1`'s chain |
| `WithUnsupportableClaim(orchestrator)` | `orchestrate(question, repository, ledger)`, `replan(question, rejected_claim, verdict, repository, ledger)`; `forced_claim_id` |
| `make_orchestrator() -> OrchestratorAgent` | `infra.functions.steps.real_orchestrator()` |
| `make_critic_agent() -> Callable \| None` | `None` (the real critic) |
| `make_writer() -> Writer` | `infra.functions.steps.real_writer()` |
| `ledger_for(inject: str \| None) -> InMemoryLedger` | refuses an unknown inject |
| `ask(case_input, scope: Scope, repository: ArtefactRepository) -> dict` | §1 |

## 4. Tests (`tests/infra/functions/test_local.py` *(new)*, 11; stand-in agents, no Bedrock)
- The eval runner (`evals.run.run_case`) scores Q01, Q07, Q08, Q09, Q11 as `pass` with `infra.functions.local:ask` (×5).
- Q08 strips `claim-1`'s citations, and the critic stand-in is never called.
- Q11 is refused and no ledger the asker built has a run.
- No inject: the plain spine.
- An unknown inject is refused; the real agents are the defaults.
- The forced claim leaves re-plans of other claims alone.
- Q09: the forced claim is rejected after one retry with 2 verdicts (`max_claim_attempts`).

## 5. Out of scope
- `EVALS.md`, `evals/inputs/`, `evals/expected/` (the lead corrects Q09's text; Abdul writes results, A5a).
- The deployed-API asker (Linus, L6).
- `scripts/ask.py` *(new)* (Patrick, P3), which may call `run_spine` or this asker.

Related: [[H6 - Local eval asker - plan]], [[Huvison - trust and flow]], [[Build order]]
