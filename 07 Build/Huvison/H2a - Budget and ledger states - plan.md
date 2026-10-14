---
tags: [build, plan, area/flow]
id: H2a
owner: Huvison
spec: "[[H2a - Budget and ledger states - spec]]"
status: ready
updated: 2026-10-14
---
# H2a: The budget check and the ledger-only ask-spine states (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[H2a - Budget and ledger states - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; ledger the conflict.
3. [[Huvison - trust and flow]] §2–§3; [[H1 - Ledger extensions - spec]]; [[P2 - Orchestrator agent - spec]] (A1, A2) and [[P3 - Local ask runner - spec]] (B1, B3, B5, B6).
4. `01 Decisions/` D-007, D-010 and the repo's D-012; [[Working with AI assistants]].
5. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Huvison.

**Goal:** the budget rule and the four ask-spine states that need no agent, as tested functions on the ledger.

**Architecture:** `infra/functions/` *(new)* is outside the core: it may import `config` and the ports. Each state takes its input plus `ledger=` (keyword-only) and appends a trace step. `infra/__init__.py` *(new)* and `infra/functions/__init__.py` *(new)* (create if missing; H5 usually made them) stay docstring-only (P2 imports `tools.budget`). The tests under `tests/infra/functions/` need `"infra"` out of pytest's `norecursedirs` in `pyproject.toml` (C2 §3): check it, and drop only that entry if it is still there.

**Tech stack:** Python 3.11, pydantic 2, pytest, uv.

**Dry-run status:** both code tasks ran in a throwaway worktree of C1 + H1 + H5 (+ H3 and P1's `agent_support`, which this item doesn't use); counts and messages are real.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: `feature/ask-spine-ledger-states` from an up-to-date `develop` after **C1, H1 and H5** are merged.
- **Start state:** the dry-run's start was **255 passed**, `TOTAL` 96%. Your count depends on what else is merged: write it in the ledger file; the **deltas** must match (+4, +15).
- **Rules:** `eu-west-1`; synthetic data; no secrets. Settings only in `config.py` (read with `get_settings()`); domain constants only in `tools/constants.py`; descriptive names, no single-character names, no magic numbers. The core (`tools/`) imports no boto3, Strands, adapters, `config`, `os`. **The retry is decided only by the ledger counter**, never by a model; never let a model see the counter. Never weaken a security rule (create-once ledger, scope gate). Tests in `tests/` mirroring the code; coverage must not drop; no layout or meta guard tests. Stay in your folders: `tools/budget.py`, `infra/functions/steps.py`, `tests/infra/functions/` *(new)*, and the doc lines in Task 3.
- **The retry limit is decided:** at most 2 attempts per claim (one retry); `config.py` keeps `max_claim_attempts = 2`. Don't change it.
- **Commits:** one per task, the given messages, **no attribution lines**. Never push to `develop` or `main`.

## Review Focus
1. **Nothing is written for an out-of-scope entity:** `check_budget` calls `scope.require` before `start_run`. Read it.
2. **`retry_decision` reads only `ledger.attempts`** and the limit: no claim content, no verdict, no model.
3. **`store_claims` can't reset a counter:** a known ID goes to `revise_claim` (keeps attempts), never `put_claim`; a duplicate ID in one call is refused before any write.
4. **`record_rejection` can't hide a passed claim** in the rejected records (status check).
5. **`infra/__init__.py` and `infra/functions/__init__.py` still import nothing:** `uv run python -c "import tools.budget"` must not import `infra.functions.steps` (P2 A2).

---

### Task 1: `tools/budget.py`, the one budget rule

**Files:** Create `tools/budget.py` *(new)*, `tests/tools/test_budget.py` *(new)*

**Produces:** `tools.budget.require_budget(ledger: Ledger, run_id: str) -> float | PartialAnswer`, `BUDGET_SPENT_AT_USD`, `USD_FORMAT`. **Consumes:** `Ledger.budget_remaining`, `Ledger.run` (H1); `tools.models.PartialAnswer` (C1). **Consumed by:** Task 2 (`check_budget`), P2 (`agents/orchestrator.py` *(new)*).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/ask-spine-ledger-states
mkdir -p .superpowers && printf '# Ledger: H2a Budget and ledger states\n' > .superpowers/ledger-H2a.md
```
Expected: your start count, `TOTAL ... 96%`.
- [ ] **Step 2: Failing test.** Create `tests/tools/test_budget.py`:
```python
"""The budget check (tools/budget.py): one function, called by the check_budget state and by the orchestrator."""
import pytest

from adapters.memory_ledger import InMemoryLedger
from tools.budget import require_budget
from tools.models import PartialAnswer
from tools.ports import LedgerConflict

RUN_ID = "run-budget"
BUDGET_USD = 0.50
SMALL_SPEND_USD = 0.10


@pytest.fixture
def ledger(cfo_scope):
    ledger = InMemoryLedger()
    ledger.start_run(RUN_ID, cfo_scope, budget_usd=BUDGET_USD)
    return ledger


def test_a_run_with_budget_left_gets_the_remaining_amount(ledger):
    ledger.add_cost(RUN_ID, 0, 0, SMALL_SPEND_USD)
    assert require_budget(ledger, RUN_ID) == pytest.approx(BUDGET_USD - SMALL_SPEND_USD)


@pytest.mark.parametrize("spent_usd", [BUDGET_USD, BUDGET_USD + SMALL_SPEND_USD])
def test_a_spent_budget_returns_a_partial_answer_instead(ledger, spent_usd):
    ledger.add_cost(RUN_ID, 0, 0, spent_usd)
    partial = require_budget(ledger, RUN_ID)
    assert isinstance(partial, PartialAnswer) and "budget" in partial.reason and partial.claims_so_far == []


def test_an_unknown_run_is_not_a_budget_question(ledger):
    with pytest.raises(LedgerConflict):
        require_budget(ledger, "run-never-started")
```
- [ ] **Step 3: Run:** `uv run --locked pytest tests/tools/test_budget.py --no-cov 2>&1 | grep -E "^E  " | head -1`. Expected: `E   ModuleNotFoundError: No module named 'tools.budget'`.
- [ ] **Step 4: Implement.** Create `tools/budget.py`:
```python
"""The budget ceiling, checked in code (AGENTS.md orchestrator row; guideline: "budget ceiling enforced in the
orchestrator"). One function, two callers: the check_budget state (infra/functions/steps.py) and the orchestrator, before
each step and each re-plan. The spent cost comes from the ledger, which only real model calls increase
(tools/cost.py), and which can't be reset (D-012).
"""
from tools.models import PartialAnswer
from tools.ports import Ledger

BUDGET_SPENT_AT_USD = 0.0
USD_FORMAT = ".2f"


def require_budget(ledger: Ledger, run_id: str) -> float | PartialAnswer:
    """The run's remaining budget in USD, or a PartialAnswer once it is spent. Raises LedgerConflict if unknown."""
    remaining_usd = ledger.budget_remaining(run_id)
    if remaining_usd > BUDGET_SPENT_AT_USD:
        return remaining_usd
    run = ledger.run(run_id)
    return PartialAnswer(reason=f"the run's budget of {run['budget_usd']:{USD_FORMAT}} USD is spent "
                                f"({run['cost_usd']:{USD_FORMAT}} USD used)")
```
- [ ] **Step 5: Run:** `uv run --locked pytest tests/tools/test_budget.py --no-cov 2>&1 | tail -1`. Expected: `4 passed in …s`.
- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add tools/budget.py tests/tools/test_budget.py
git commit -m "require_budget: the one budget rule for the check_budget state and the orchestrator"
```
Expected: start + 4 (dry-run `259 passed`), `TOTAL ... 96%`.

**Task done when:** `uv run python -c "import inspect; from tools.budget import require_budget; print(inspect.signature(require_budget))"` prints `(ledger: tools.ports.Ledger, run_id: str) -> float | tools.models.PartialAnswer`.

### Task 2: `infra/functions/steps.py`: `question_for`, `check_budget`, `store_claims`, `retry_decision`, `record_rejection`

**Files:** Create `infra/functions/steps.py` *(new)*, `tests/infra/functions/test_steps.py` *(new)*

**Produces:** in `infra.functions.steps`: `RUN_ID_PREFIX`, `RETRY`, `REJECT`, `STEP_CHECK_BUDGET`, `STEP_STORE_CLAIMS`, `STEP_RETRY_DECISION`, `STEP_RECORD_REJECTION`;
- `question_for(scope: Scope, request: AskRequest, settings: Settings | None = None) -> Question`;
- `record_step(ledger: Ledger, run_id: str, step: str, agent: str | None = None, prompt: PromptRef | None = None) -> None`;
- `check_budget(question: Question, *, ledger: Ledger) -> float | PartialAnswer`;
- `store_claims(run_id: str, claims: list[BlockerClaim], *, ledger: Ledger) -> list[BlockerClaim]`;
- `retry_decision(run_id: str, claim_id: str, *, ledger: Ledger, max_attempts: int | None = None) -> str`;
- `stored_claim(ledger: Ledger, run_id: str, claim_id: str) -> dict`; `rejected_claim(record: dict) -> RejectedClaim`;
- `record_rejection(run_id: str, claim_id: str, *, ledger: Ledger) -> RejectedClaim`.

**Consumes:** Task 1; `Ledger.start_run`, `add_step`, `claims`, `put_claim`, `revise_claim`, `attempts`, `put_rejected` (H1); `config.get_settings` (`run_budget_usd`, `max_claim_attempts`); C1's `AskRequest`, `PromptRef`, `RejectedClaim`, `TraceStep`, `Question`, `BlockerClaim`, `PartialAnswer`, `Verdict`. **Consumed by:** H2b, H6, P3 (`scripts/ask.py` *(new)*), L3 (`question_for`, optional).

- [ ] **Step 1: Failing tests.** Create `tests/infra/functions/test_steps.py`:
```python
"""The ask-spine states that only touch the ledger (infra/functions/steps.py): budget, claims, retry guard, rejections."""
import pytest

from adapters.memory_ledger import InMemoryLedger
from config import get_settings
from infra.functions.steps import (REJECT, RETRY, check_budget, question_for, record_rejection, retry_decision,
                        store_claims)
from tools.api_schema import AskRequest
from tools.models import BlockerClaim, OutOfScope, PartialAnswer, Question
from tools.ports import LedgerConflict

RUN_ID = "run-steps"
BUDGET_USD = 0.50
MAX_ATTEMPTS = 2   # the configured limit: at most 2 attempts per claim, one retry (the lead's ruling on Q09)
E4_CLAIM = BlockerClaim(claim_id="claim-1", statement="E4 is blocked by open DEF-0412",
                        chain=[{"artefact": "defect_log", "row_id": "DEF-0412", "role_in_chain": "cause"}])
SECOND_CLAIM = BlockerClaim(claim_id="claim-2", statement="Runbook step RB-010 waits on the reconciliation",
                            chain=[{"artefact": "cutover_runbook", "row_id": "E4#RB-010"}])
REJECTION = {"claim_id": "claim-1", "pass": False, "reason": "no row supports it", "missing_evidence": []}


def question(scope, entity_id="E4") -> Question:
    return Question(run_id=RUN_ID, scope=scope, entity_id=entity_id, question="What is blocking cutover for E4?",
                    budget_usd=BUDGET_USD, max_attempts=MAX_ATTEMPTS)


@pytest.fixture
def ledger():
    return InMemoryLedger()


@pytest.fixture
def started(ledger, cfo_scope):
    check_budget(question(cfo_scope), ledger=ledger)
    return ledger


def test_question_for_fills_the_budget_and_retry_limit_from_settings(cfo_scope):
    built = question_for(cfo_scope, AskRequest(entity_id="E4", question="What blocks E4?"))
    settings = get_settings()
    assert (built.budget_usd, built.max_attempts) == (settings.run_budget_usd, settings.max_claim_attempts)
    assert built.run_id != question_for(cfo_scope, AskRequest(entity_id="E4", question="What blocks E4?")).run_id


def test_check_budget_starts_the_run_and_returns_what_is_left(ledger, cfo_scope):
    assert check_budget(question(cfo_scope), ledger=ledger) == BUDGET_USD
    assert ledger.run(RUN_ID)["budget_usd"] == BUDGET_USD
    assert [step["step"] for step in ledger.steps(RUN_ID)] == ["check_budget"]


def test_check_budget_refuses_an_out_of_scope_entity_before_anything_is_written(ledger, entity_four_lead_scope):
    with pytest.raises(OutOfScope):
        check_budget(question(entity_four_lead_scope, entity_id="E2"), ledger=ledger)
    with pytest.raises(LedgerConflict):
        ledger.run(RUN_ID)


def test_check_budget_cannot_restart_a_run(started, cfo_scope):
    with pytest.raises(LedgerConflict):
        check_budget(question(cfo_scope), ledger=started)


def test_check_budget_returns_a_partial_answer_when_nothing_is_left(cfo_scope):
    class LedgerWithNothingLeft(InMemoryLedger):
        def budget_remaining(self, run_id: str) -> float:
            return 0.0
    assert isinstance(check_budget(question(cfo_scope), ledger=LedgerWithNothingLeft()), PartialAnswer)


def test_store_claims_puts_new_claims_under_their_ids(started):
    assert store_claims(RUN_ID, [E4_CLAIM, SECOND_CLAIM], ledger=started) == [E4_CLAIM, SECOND_CLAIM]
    assert [entry["claim_id"] for entry in started.claims(RUN_ID)] == ["claim-1", "claim-2"]
    assert started.steps(RUN_ID)[-1]["step"] == "store_claims"


def test_a_known_claim_id_is_revised_and_keeps_its_attempts(started):
    store_claims(RUN_ID, [E4_CLAIM], ledger=started)
    started.record_verdict(RUN_ID, "claim-1", REJECTION)
    replanned = E4_CLAIM.model_copy(update={"statement": "E4 is blocked by DEF-0412, open for 18 days"})
    store_claims(RUN_ID, [replanned], ledger=started)
    assert started.claim(RUN_ID, "claim-1")["statement"] == replanned.statement
    assert started.attempts(RUN_ID, "claim-1") == 1 and len(started.claims(RUN_ID)) == 1


def test_two_claims_with_one_id_in_a_plan_are_refused(started):
    with pytest.raises(ValueError, match="duplicate claim IDs"):
        store_claims(RUN_ID, [E4_CLAIM, E4_CLAIM], ledger=started)
    assert started.claims(RUN_ID) == []


def test_store_claims_needs_a_started_run(ledger):
    with pytest.raises(LedgerConflict):
        store_claims(RUN_ID, [E4_CLAIM], ledger=ledger)


@pytest.mark.parametrize("verdicts_so_far, expected", [(1, RETRY), (MAX_ATTEMPTS, REJECT), (MAX_ATTEMPTS + 1, REJECT)])
def test_retry_decision_reads_only_the_ledger_counter(started, verdicts_so_far, expected):
    store_claims(RUN_ID, [E4_CLAIM], ledger=started)
    for _ in range(verdicts_so_far):
        started.record_verdict(RUN_ID, "claim-1", REJECTION)
    assert retry_decision(RUN_ID, "claim-1", ledger=started, max_attempts=MAX_ATTEMPTS) == expected


def test_retry_decision_defaults_to_the_configured_limit(started):
    store_claims(RUN_ID, [E4_CLAIM], ledger=started)
    for _ in range(get_settings().max_claim_attempts):
        started.record_verdict(RUN_ID, "claim-1", REJECTION)
    assert retry_decision(RUN_ID, "claim-1", ledger=started) == REJECT


def test_record_rejection_moves_the_claim_with_every_verdict(started):
    store_claims(RUN_ID, [E4_CLAIM], ledger=started)
    for _ in range(MAX_ATTEMPTS):
        started.record_verdict(RUN_ID, "claim-1", REJECTION)
    rejected = record_rejection(RUN_ID, "claim-1", ledger=started)
    assert (rejected.claim_id, rejected.statement, rejected.reason) == ("claim-1", E4_CLAIM.statement,
                                                                        REJECTION["reason"])
    assert len(rejected.verdicts) == MAX_ATTEMPTS
    assert [record["claim_id"] for record in started.rejected(RUN_ID)] == ["claim-1"]


def test_record_rejection_refuses_a_claim_that_was_not_rejected(started):
    with pytest.raises(LedgerConflict):
        record_rejection(RUN_ID, "claim-never-stored", ledger=started)
    store_claims(RUN_ID, [E4_CLAIM], ledger=started)
    with pytest.raises(LedgerConflict):
        record_rejection(RUN_ID, "claim-1", ledger=started)
    started.record_verdict(RUN_ID, "claim-1", {**REJECTION, "pass": True})
    with pytest.raises(LedgerConflict):
        record_rejection(RUN_ID, "claim-1", ledger=started)
```
- [ ] **Step 2: Run:** `uv run --locked pytest tests/infra/functions/test_steps.py --no-cov 2>&1 | grep -E "^E  " | head -1`. Expected: `E   ModuleNotFoundError: No module named 'infra.functions.steps'`.
- [ ] **Step 3: Implement.** Create `infra/functions/steps.py`:
```python
"""The ask spine's states, one function per Step Functions state (D-007, D-011, D-012).

    check_budget -> run_orchestrator -> store_claims -> judge_claim (per claim) -> retry_decision
        pass -> write_answer · reject, under the limit -> run_orchestrator (re-plan, same claim ID) -> store_claims
        reject, at the limit -> record_rejection

Each function takes its state's input plus the ports it uses as keyword arguments (`ledger=`, `repository=`), so a
local run shares one ledger across states (infra/functions/spine.py, scripts/ask.py) and the Lambda entry points
(infra/functions/states.py) build them from config.py. Inputs and outputs are the step models (tools/models.py,
tools/api_schema.py). The ledger is the only state: every function reads what it needs from it, and every state
appends a trace step.
"""
from uuid import uuid4

from config import Settings, get_settings
from tools.budget import require_budget
from tools.api_schema import AskRequest, PromptRef, RejectedClaim, TraceStep
from tools.constants import ClaimStatus
from tools.models import BlockerClaim, PartialAnswer, Question, Scope, Verdict
from tools.ports import Ledger, LedgerConflict

RUN_ID_PREFIX = "run-"
RETRY = "retry"
REJECT = "reject"
STEP_CHECK_BUDGET = "check_budget"
STEP_STORE_CLAIMS = "store_claims"
STEP_RETRY_DECISION = "retry_decision"
STEP_RECORD_REJECTION = "record_rejection"


def question_for(scope: Scope, request: AskRequest, settings: Settings | None = None) -> Question:
    """The spine's input for one /ask: a fresh run ID, and the budget and retry limit from config.py."""
    settings = settings or get_settings()
    return Question(run_id=f"{RUN_ID_PREFIX}{uuid4().hex}", scope=scope, entity_id=request.entity_id,
                    question=request.question, budget_usd=settings.run_budget_usd,
                    max_attempts=settings.max_claim_attempts)


def record_step(ledger: Ledger, run_id: str, step: str, agent: str | None = None,
                prompt: PromptRef | None = None) -> None:
    """Append one AskResponse.trace entry to the run."""
    ledger.add_step(run_id, TraceStep(step=step, agent=agent, prompt=prompt).model_dump(mode="json"))


def check_budget(question: Question, *, ledger: Ledger) -> float | PartialAnswer:
    """First state: refuse an out-of-scope entity before anything is written (D-010, Q11), start the run (create-once,
    so neither the spent cost nor the run can be reset), then the budget check."""
    question.scope.require(question.entity_id)
    ledger.start_run(question.run_id, question.scope, question.budget_usd)
    record_step(ledger, question.run_id, STEP_CHECK_BUDGET)
    return require_budget(ledger, question.run_id)


def store_claims(run_id: str, claims: list[BlockerClaim], *, ledger: Ledger) -> list[BlockerClaim]:
    """Write the orchestrator's claims: put_claim for a new claim ID, revise_claim for one the run already has.

    Claim IDs are numbered in code by the orchestrator (claim-1, claim-2, ...), never by a model, and a re-plan keeps
    the rejected claim's ID (run_orchestrator enforces it), so revise_claim keeps the attempt count (D-012).
    Two claims with one ID in a single call would overwrite each other, so that raises ValueError.
    """
    claim_ids = [claim.claim_id for claim in claims]
    if len(set(claim_ids)) != len(claim_ids):
        raise ValueError(f"duplicate claim IDs in one plan: {claim_ids}")
    known_ids = {stored["claim_id"] for stored in ledger.claims(run_id)}
    for claim in claims:
        content = claim.model_dump(mode="json")
        if claim.claim_id in known_ids:
            ledger.revise_claim(run_id, claim.claim_id, content)
        else:
            ledger.put_claim(run_id, content)
    record_step(ledger, run_id, STEP_STORE_CLAIMS)
    return list(claims)


def retry_decision(run_id: str, claim_id: str, *, ledger: Ledger, max_attempts: int | None = None) -> str:
    """The retry guard on the rejected edge: the ledger's counter against the limit (max_claim_attempts unless given).
    It reads only the counter: never the claim, the verdict or a model."""
    limit = max_attempts if max_attempts is not None else get_settings().max_claim_attempts
    decision = RETRY if ledger.attempts(run_id, claim_id) < limit else REJECT
    record_step(ledger, run_id, STEP_RETRY_DECISION)
    return decision


def stored_claim(ledger: Ledger, run_id: str, claim_id: str) -> dict:
    """One claim's ledger entry {claim_id, claim, attempts, verdicts, status}. Raises LedgerConflict if unknown."""
    for stored in ledger.claims(run_id):
        if stored["claim_id"] == claim_id:
            return stored
    raise LedgerConflict.missing_claim(run_id, claim_id)


def rejected_claim(record: dict) -> RejectedClaim:
    """A rejected record (Ledger.rejected) as AskResponse.rejected[] shows it; the reason is the last verdict's."""
    verdicts = [Verdict.model_validate(verdict) for verdict in record["verdicts"]]
    return RejectedClaim(claim_id=record["claim_id"], statement=record["claim"]["statement"],
                         reason=verdicts[-1].reason, verdicts=verdicts)


def record_rejection(run_id: str, claim_id: str, *, ledger: Ledger) -> RejectedClaim:
    """At the retry limit: copy the claim and all its verdicts to the rejected records ("could not verify").
    Only a claim whose last verdict rejected it can be recorded."""
    stored = stored_claim(ledger, run_id, claim_id)
    if stored["status"] != ClaimStatus.REJECTED or not stored["verdicts"]:
        raise LedgerConflict(f"claim {claim_id} in run {run_id} is not rejected (status {stored['status']})")
    ledger.put_rejected(run_id, claim_id, stored["verdicts"])
    record_step(ledger, run_id, STEP_RECORD_REJECTION)
    return rejected_claim({"claim_id": claim_id, "claim": stored["claim"], "verdicts": stored["verdicts"]})
```
- [ ] **Step 4: Run:** `uv run --locked pytest tests/tools/test_cost.py tests/tools/test_budget.py tests/infra/functions/ --no-cov 2>&1 | tail -1`. Expected: `24 passed in …s` (5 cost + 4 budget + 15 steps).
- [ ] **Step 5: Guards, imports, full suite and commit**
```bash
uv run --locked pytest tests/test_architecture.py tests/test_code_style.py --no-cov 2>&1 | tail -1
uv run python -c "import sys, tools.budget; print('infra.functions.steps' in sys.modules)"
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/functions/steps.py tests/infra/functions/test_steps.py
git commit -m "Ask-spine ledger states: check_budget, store_claims, retry_decision, record_rejection"
```
Expected: the guards pass; `False` (importing `tools.budget` doesn't load `infra.functions.steps`); start + 19 (dry-run `274 passed`), `TOTAL ... 97%` or higher.

**Task done when:** `uv run --locked pytest tests/infra/functions/test_steps.py --no-cov 2>&1 | tail -1` prints `15 passed`, and `uv run --locked pytest tests/infra/functions/test_steps.py --no-cov -k "refuses_an_out_of_scope" 2>&1 | tail -1 | cut -d, -f1` prints `1 passed`.

### Task 3: Docs, review and PR
- [ ] **Step 1: `docs/DEVOPS_HANDOVER.md`.** No change yet: the `infra.functions.steps.<name>` rows become `infra.functions.states.<name>` in H2b, which ships the Lambda entry points. Write "handover unchanged (H2b)" in the ledger file.
- [ ] **Step 2: `HANDOFF.md`.** Under `## What's real`, add: `- The ask spine's ledger states (\`infra/functions/steps.py\`): the budget check (\`tools/budget.py\`, also called by the orchestrator), claims to the ledger, the retry guard (at most 2 attempts per claim, read from the ledger counter only) and the rejected records.`
- [ ] **Step 3: Commit:** `git add HANDOFF.md && git commit -m "HANDOFF: the ask spine's ledger states"`; then `uv run --locked pytest tests/test_dependencies.py --no-cov 2>&1 | tail -1`. Expected: `4 passed`.
- [ ] **Step 4:** Review Focus by hand; results in `.superpowers/ledger-H2a.md`.
- [ ] **Step 5:** `git diff develop --stat`. Expected: `HANDOFF.md`, `tools/budget.py`, `infra/functions/steps.py`, `tests/tools/test_budget.py`, `tests/infra/functions/test_steps.py` (5 files).
- [ ] **Step 6: With Huvison's OK only:** push `feature/ask-spine-ledger-states`, PR to `develop` ("Ask spine: budget check and ledger states (H2a)"), body with the count, the signature table from the spec (for Patrick's P2/P3) and the rulings. No attribution lines.
- [ ] **Step 7:** [[Build order]]: H2 → `in progress (H2a in review, PR #nn)`; tell Patrick `require_budget` is on `develop` once merged (P2's A1).

**Task done when:** the PR is open with the count and the signature table in its body.

## Done means
- [ ] **The budget rule exists with Patrick's signature.** *Verify:* on `develop`, the Task 1 "Task done when" command prints that signature.
- [ ] **The four states are tested.** *Verify:* `uv run --locked pytest tests/tools/test_budget.py tests/infra/functions/test_steps.py --no-cov 2>&1 | tail -1` prints `19 passed`.
- [ ] **The retry limit is 2 attempts.** *Verify:* `uv run --locked pytest tests/infra/functions/test_steps.py --no-cov -k retry_decision 2>&1 | tail -1 | cut -d, -f1` prints `4 passed`, and `uv run python -c "from config import get_settings; print(get_settings().max_claim_attempts)"` prints `2`.
- [ ] **Tests under `tests/infra/` *(new)* are collected.** *Verify:* `grep -n norecursedirs pyproject.toml` shows a list without `"infra"`.
- [ ] **No import cycle.** *Verify:* `uv run python -c "import infra.functions.steps"` exits 0.
- [ ] **Nothing broke.** *Verify:* full suite after merge: start + 19, `TOTAL` ≥ 96%.
- [ ] **Merged.** *Verify:* PR merged into `develop`; Patrick told (stand-up note or Slack message).

## Never
- Let anything but the ledger counter decide a retry, or show the counter to a model.
- Start a run before the scope check.
- Change `max_claim_attempts`.
- Import `infra.functions.steps` from `infra/__init__.py`, `infra/functions/__init__.py` or `tools/budget.py`.
- Push to `develop` or `main`, or add attribution lines.

Related: [[H2a - Budget and ledger states - spec]], [[H2b - Agent states, local spine and Lambda handlers - plan]], [[Build order]], [[How to execute a plan]]
