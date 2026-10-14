---
tags: [build, plan, area/flow]
id: H2b
owner: Huvison
spec: "[[H2b - Agent states, local spine and Lambda handlers - spec]]"
status: ready
updated: 2026-10-14
---
# H2b: Agent-calling states, the in-process spine and the Lambda handlers (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[H2b - Agent states, local spine and Lambda handlers - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; ledger the conflict.
3. [[H2a - Budget and ledger states - spec]], [[H3 - Writer agent - spec]], [[H5 - Cost per run - spec]]; Patrick's [[P2 - Orchestrator agent - spec]] and [[P3 - Local ask runner - spec]].
4. `01 Decisions/` D-007, D-009, D-010 and the repo's D-012; [[Working with AI assistants]].
5. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Huvison.

**Goal:** the three agent-calling states, the whole ask spine in-process, and one JSON Lambda entry point per state, all tested with stub agents.

**Architecture:** the states take `ledger=` and `repository=` keyword ports and optional agent stand-ins (`orchestrator=`, `critic_agent=`, `writer=`); `None` means the real agent (P2's module imported on first use; the Bedrock critic; H3's writer). The ledger is the only state: claims, verdicts and the run's scope are read from it. `infra/functions/spine.py` sequences the states; `infra/functions/states.py` wraps each for Step Functions.

**Tech stack:** Python 3.11, pydantic 2, pytest, uv. No Bedrock and no AWS in any test.

**Dry-run status:** re-run on C1 at `94970fd` (C1 alone: `213 passed`, 96%); the counts below are from that run. Every step ran in a throwaway worktree of C1 + H1 + H5 + H3 + H2a, with P1's `agents/agent_support.py` *(new)* copied verbatim from [[P1 - Retriever agent - plan]] as its stand-in. P2 isn't needed: the tests pass an orchestrator stand-in, and nothing imports `agents.orchestrator` at load. Counts and messages are real.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: `feature/ask-spine-agent-states` from an up-to-date `develop` after **H2a, H3 and H5** (and so C1, H1, P1) are merged.
- **Start state:** the dry-run's start was **283 passed**, `TOTAL` 97%. Write your real number in the ledger file; the **deltas** must match (+3, +5, +4, +7, +4).
- **Rules:** `eu-west-1`, `eu.*` models only; synthetic data; no secrets. Settings only in `config.py`; domain constants only in `tools/constants.py`; descriptive names, no single-character names, no magic numbers. The core imports no boto3, Strands, adapters, `config`, `os`. Agents reach data only through `tools/agent_tools.py`; **scope is never a tool argument**. **The critic stays blind and fails closed:** it sees only the stored claim and its cited rows, never the plan, the question, the attempt count or the orchestrator's reasoning; never catch a critic failure as a pass. **The retry is decided only by `retry_decision`** (2 attempts per claim, the lead's ruling). Never weaken a security rule. Tests in `tests/` mirroring the code; coverage must not drop; no layout or meta guard tests. Stay in your folders: `infra/functions/` *(new)*, `tests/infra/functions/` *(new)*, and the doc lines in Task 6.
- **Commits:** one per task, the given messages, **no attribution lines**. Never push to `develop` or `main`.

## Review Focus
1. **Critic blindness:** in `judge_claim`, the critic gets only `ledger.claim(...)` and the rows its citations point to (inside `critic.judge`). No question, plan, verdict history or attempt count reaches it. Read the function.
2. **No fresh counter through a re-plan:** `run_orchestrator` drops re-plan claims under any other ID; `settle_claim` stores the re-planned claim under the same ID; `store_claims` revises. Trace one retry by hand.
3. **Bounded loop:** `settle_claim`'s `while True` exits on pass, on `REJECT`, or on an empty re-plan; each turn records one verdict, so `retry_decision` ends it at 2 attempts.
4. **Only ledger-passed claims are written,** in the ledger's copy (`write_answer`), and handlers never take claims, verdicts or scope for the critic from the event.
5. **Partial runs:** an unknown entity calls no critic and no writer; a spent budget at the start calls no agent at all.

---

### Task 1: `run_orchestrator`

**Files:** Modify `infra/functions/steps.py` *(new)*, `tests/infra/functions/test_steps.py` *(new)*

**Produces:** in `infra.functions.steps`: `STEP_RUN_ORCHESTRATOR`, `STEP_JUDGE_CLAIM`, `STEP_WRITE_ANSWER`, `ORCHESTRATOR_AGENT_NAME`, `ORCHESTRATOR_MODULE`, `logger`, `OrchestratorAgent`, `Writer`, `prompt_ref(agent_name: str) -> PromptRef | None`, `real_orchestrator() -> OrchestratorAgent`, `run_orchestrator(question: Question, *, ledger: Ledger, repository: ArtefactRepository, rejected_claim: BlockerClaim | None = None, verdict: dict | None = None, orchestrator: OrchestratorAgent | None = None) -> OrchestratorResult`. **Consumes:** `tools.cost.record_usage` (H5); `agents.prompt_loader` (exists); P2's `orchestrate` / `replan` (at run time only). **Consumed by:** Task 4, H6, P3.

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/ask-spine-agent-states
mkdir -p .superpowers && printf '# Ledger: H2b Agent states, spine, handlers\n' > .superpowers/ledger-H2b.md
```
Expected: your start count, `TOTAL ... 97%` (or 96%).
- [ ] **Step 2: Failing tests.** In `tests/infra/functions/test_steps.py`:
  - change the first line (the module docstring) to `"""The ask-spine states (infra/functions/steps.py): budget, claims, retry guard, rejections, and the states that call agents."""`;
  - replace the import block (from `import pytest` to `from tools.ports import LedgerConflict`) with:
```python
import json
import logging
from types import SimpleNamespace

import pytest

from adapters.memory_ledger import InMemoryLedger
from agents.prompt_loader import load_prompt
from agents.writer import verbatim_answer
from config import get_settings
from infra.functions import steps
from tools.cost import cost_usd
from infra.functions.steps import (REJECT, RETRY, check_budget, question_for, record_rejection, retry_decision,
                        store_claims)
from tools.api_schema import AskRequest
from tools.models import (BlockerClaim, OrchestratorResult, OutOfScope, PartialAnswer, Plan, Question, Usage,
                          WriterInput, WriterResult)
from tools.ports import LedgerConflict
```
  - append:
```python


# ---- the states that call agents -------------------------------------------------------------------------------
REASONING_MODEL = get_settings().orchestrator_model_id
ORCHESTRATOR_USAGE = [Usage(model_id=REASONING_MODEL, tokens_in=1000, tokens_out=200)]
CRITIC_TOKENS_IN = 700
CRITIC_TOKENS_OUT = 60
VALID_E4_CLAIM = BlockerClaim(
    claim_id="claim-1",
    statement="212 customer records were rejected in load cycle 3, tied to open High defect DEF-0412",
    chain=[{"artefact": "reconciliation_results", "row_id": "RC-C3-E4-customers", "role_in_chain": "failed check"},
           {"artefact": "defect_log", "row_id": "DEF-0412", "role_in_chain": "cause"}])


class StubOrchestrator:
    """Stands in for agents/orchestrator.py (P2): fixed claims, and a record of what it was asked."""

    def __init__(self, *claims, replan_claims=None):
        self.claims = list(claims)
        self.replan_claims = self.claims if replan_claims is None else list(replan_claims)
        self.calls = []

    def orchestrate(self, question, repository, ledger):
        self.calls.append(("orchestrate", None, None))
        return OrchestratorResult(plan=Plan(run_id=question.run_id, steps=[]), claims=self.claims,
                                  usage=ORCHESTRATOR_USAGE)

    def replan(self, question, rejected_claim, verdict, repository, ledger):
        self.calls.append(("replan", rejected_claim.claim_id, verdict["reason"]))
        return OrchestratorResult(plan=Plan(run_id=question.run_id, steps=[]), claims=self.replan_claims,
                                  usage=ORCHESTRATOR_USAGE)


class StrandsLikeReply:
    """The parts of a Strands AgentResult the flow reads: the text, and the token usage of each model call."""

    def __init__(self, text: str):
        self.text = text
        cycle = SimpleNamespace(usage={"inputTokens": CRITIC_TOKENS_IN, "outputTokens": CRITIC_TOKENS_OUT})
        self.metrics = SimpleNamespace(latest_agent_invocation=SimpleNamespace(cycles=[cycle]))

    def __str__(self) -> str:
        return self.text


class StubCritic:
    """Stands in for the Strands critic agent: a fixed verdict, and a record of its prompts."""

    def __init__(self, passed: bool):
        self.passed = passed
        self.prompts = []

    def __call__(self, prompt: str) -> StrandsLikeReply:
        self.prompts.append(prompt)
        claim_id = json.loads(prompt.split("<claim>")[1].split("</claim>")[0])["claim_id"]
        return StrandsLikeReply(json.dumps({"claim_id": claim_id, "pass": self.passed, "reason": "stub",
                                            "missing_evidence": []}))


def stub_writer(writer_input: WriterInput) -> WriterResult:
    return WriterResult(answer=verbatim_answer(writer_input.passed_claims),
                        usage=[Usage(model_id=REASONING_MODEL, tokens_in=500, tokens_out=100)])


def test_run_orchestrator_records_its_cost_and_a_trace_step(started, repository, cfo_scope):
    result = steps.run_orchestrator(question(cfo_scope), ledger=started, repository=repository,
                                    orchestrator=StubOrchestrator(VALID_E4_CLAIM))
    assert result.claims == [VALID_E4_CLAIM]
    run = started.run(RUN_ID)
    assert (run["tokens_in"], run["tokens_out"]) == (1000, 200)
    assert run["cost_usd"] == pytest.approx(cost_usd(ORCHESTRATOR_USAGE))
    orchestrator_prompt = steps.prompt_ref("orchestrator")  # None until P2's orchestrator prompt is merged
    expected_prompt = orchestrator_prompt.model_dump() if orchestrator_prompt else None
    assert started.steps(RUN_ID)[-1] == {"step": "run_orchestrator", "agent": "orchestrator", "prompt": expected_prompt}


def test_a_re_plan_gets_the_claim_and_the_critics_last_verdict_from_the_ledger(started, repository, cfo_scope):
    store_claims(RUN_ID, [VALID_E4_CLAIM], ledger=started)
    started.record_verdict(RUN_ID, "claim-1", REJECTION)
    orchestrator = StubOrchestrator(VALID_E4_CLAIM)
    steps.run_orchestrator(question(cfo_scope), ledger=started, repository=repository,
                           rejected_claim=VALID_E4_CLAIM, orchestrator=orchestrator)
    assert orchestrator.calls == [("replan", "claim-1", REJECTION["reason"])]


def test_a_re_plan_keeps_only_a_claim_under_the_rejected_id(started, repository, cfo_scope, caplog):
    fresh = VALID_E4_CLAIM.model_copy(update={"claim_id": "claim-7"})
    orchestrator = StubOrchestrator(VALID_E4_CLAIM, replan_claims=[fresh, VALID_E4_CLAIM, VALID_E4_CLAIM])
    with caplog.at_level(logging.WARNING, logger="infra.functions.steps"):
        result = steps.run_orchestrator(question(cfo_scope), ledger=started, repository=repository,
                                        rejected_claim=VALID_E4_CLAIM, verdict=REJECTION, orchestrator=orchestrator)
    assert result.claims == [VALID_E4_CLAIM] and "claim-7" in caplog.text
```
- [ ] **Step 3: Run:** `uv run --locked pytest tests/infra/functions/test_steps.py --no-cov 2>&1 | tail -1` and `... 2>&1 | grep -E "^E  " | sort -u | head -1`. Expected: `3 failed, 15 passed`; `E       AttributeError: module 'infra.functions.steps' has no attribute 'run_orchestrator'`.
- [ ] **Step 4: Implement.** In `infra/functions/steps.py`:
  - replace everything from `from uuid import uuid4` down to (not including) `def question_for(` with:
```python
import importlib
import logging
from typing import Callable, Protocol
from uuid import uuid4

from agents import critic
from agents.agent_support import usage_of
from agents.prompt_loader import PROMPT_FILE_SUFFIX, PROMPTS_DIR, load_prompt
from agents.writer import WRITER_AGENT_NAME
from config import Settings, get_settings
from tools.budget import require_budget
from tools.cost import record_usage
from tools.api_schema import AskRequest, AskResponse, PromptRef, RejectedClaim, TraceStep
from tools.constants import ClaimStatus
from tools.models import (BlockerClaim, OrchestratorResult, OutOfScope, PartialAnswer, Question, Scope, Verdict,
                          WriterInput, WriterResult)
from tools.ports import ArtefactRepository, Ledger, LedgerConflict

RUN_ID_PREFIX = "run-"
RETRY = "retry"
REJECT = "reject"
STEP_CHECK_BUDGET = "check_budget"
STEP_STORE_CLAIMS = "store_claims"
STEP_RETRY_DECISION = "retry_decision"
STEP_RECORD_REJECTION = "record_rejection"
STEP_RUN_ORCHESTRATOR = "run_orchestrator"
STEP_JUDGE_CLAIM = "judge_claim"
STEP_WRITE_ANSWER = "write_answer"
ORCHESTRATOR_AGENT_NAME = "orchestrator"
ORCHESTRATOR_MODULE = "agents.orchestrator"   # Patrick's P2: orchestrate() and replan()

logger = logging.getLogger(__name__)


class OrchestratorAgent(Protocol):
    """What run_orchestrator needs from the orchestrator (agents/orchestrator.py, P2). Tests pass a stand-in."""

    def orchestrate(self, question: Question, repository: ArtefactRepository,
                    ledger: Ledger) -> OrchestratorResult: ...

    def replan(self, question: Question, rejected_claim: BlockerClaim, verdict: dict,
               repository: ArtefactRepository, ledger: Ledger) -> OrchestratorResult: ...


class Writer(Protocol):
    """What write_answer needs from the writer (agents/writer.py, H3). Tests pass a stand-in."""

    def __call__(self, writer_input: WriterInput) -> WriterResult: ...


```
  - append at the end:
```python


# ---- the states that call agents -------------------------------------------------------------------------------
def prompt_ref(agent_name: str) -> PromptRef | None:
    """The agent's prompt version for the trace; None while the agent has no prompt file yet (a stub)."""
    if not (PROMPTS_DIR / f"{agent_name}{PROMPT_FILE_SUFFIX}").is_file():
        return None
    return PromptRef(**load_prompt(agent_name).provenance())


def real_orchestrator() -> OrchestratorAgent:
    """agents/orchestrator.py, imported on first use: it imports tools.budget, so infra/functions/steps.py must not import it at load."""
    return importlib.import_module(ORCHESTRATOR_MODULE)


def run_orchestrator(question: Question, *, ledger: Ledger, repository: ArtefactRepository,
                     rejected_claim: BlockerClaim | None = None, verdict: dict | None = None,
                     orchestrator: OrchestratorAgent | None = None) -> OrchestratorResult:
    """The first plan (orchestrate), or the re-plan of one rejected claim (replan) with the critic's last verdict.
    Records the cost of every model call behind it and a trace step.

    A re-plan keeps at most one claim, and only under the rejected claim's ID: a claim under any other ID is dropped
    and logged, so a re-plan can never start a fresh attempt counter (D-012).
    """
    agent = orchestrator or real_orchestrator()
    if rejected_claim is None:
        result = agent.orchestrate(question, repository, ledger)
    else:
        last_verdict = verdict or stored_claim(ledger, question.run_id, rejected_claim.claim_id)["verdicts"][-1]
        result = agent.replan(question, rejected_claim, last_verdict, repository, ledger)
        kept = [claim for claim in result.claims if claim.claim_id == rejected_claim.claim_id][:1]
        if len(kept) != len(result.claims):
            logger.warning("re-plan of %s returned claims %s: kept %s", rejected_claim.claim_id,
                           [claim.claim_id for claim in result.claims], [claim.claim_id for claim in kept])
            result = result.model_copy(update={"claims": kept})
    record_usage(ledger, question.run_id, result.usage)
    record_step(ledger, question.run_id, STEP_RUN_ORCHESTRATOR, agent=ORCHESTRATOR_AGENT_NAME,
                prompt=prompt_ref(ORCHESTRATOR_AGENT_NAME))
    return result
```
- [ ] **Step 5: Run:** `uv run --locked pytest tests/infra/functions/test_steps.py --no-cov 2>&1 | tail -1`. Expected: `18 passed in …s`.
- [ ] **Step 6: Full suite, no cycle, commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
uv run python -c "import infra.functions.steps, sys; print('agents.orchestrator' in sys.modules)"
git add infra/functions/steps.py tests/infra/functions/test_steps.py
git commit -m "run_orchestrator state: first plan or re-plan of one claim under its own ID, cost and trace recorded"
```
Expected: start + 3 (dry-run `286 passed`); `False` (the orchestrator isn't imported at load).

**Task done when:** `uv run --locked pytest tests/infra/functions/test_steps.py --no-cov -k re_plan 2>&1 | tail -1 | cut -d, -f1` prints `2 passed`.

### Task 2: `judge_claim`

**Files:** Modify `infra/functions/steps.py`, `tests/infra/functions/test_steps.py`

**Produces:** `infra.functions.steps.judge_claim(run_id: str, claim: BlockerClaim, scope: Scope, *, ledger: Ledger, repository: ArtefactRepository, critic_agent: Callable | None = None) -> dict`. **Consumes:** `agents.critic.judge`, `make_agent`, `CRITIC_AGENT_NAME` (exist); `agents.agent_support.usage_of` (P1); `Ledger.claim`, `run`, `record_verdict` (H1). **Consumed by:** Task 4, H6, P3.

- [ ] **Step 1: Failing tests.** Append to `tests/infra/functions/test_steps.py`:
```python


def test_judge_claim_records_a_passing_verdict_its_prompt_and_its_cost(started, repository, cfo_scope):
    store_claims(RUN_ID, [VALID_E4_CLAIM], ledger=started)
    verdict = steps.judge_claim(RUN_ID, VALID_E4_CLAIM, cfo_scope, ledger=started, repository=repository,
                                critic_agent=StubCritic(passed=True))
    assert verdict["pass"] is True and started.claims(RUN_ID)[0]["status"] == "passed"
    assert started.steps(RUN_ID)[-1]["prompt"] == load_prompt("critic").provenance()
    assert (started.run(RUN_ID)["tokens_in"], started.run(RUN_ID)["tokens_out"]) == (CRITIC_TOKENS_IN,
                                                                                      CRITIC_TOKENS_OUT)


def test_judge_claim_counts_a_rejection(started, repository, cfo_scope):
    store_claims(RUN_ID, [VALID_E4_CLAIM], ledger=started)
    verdict = steps.judge_claim(RUN_ID, VALID_E4_CLAIM, cfo_scope, ledger=started, repository=repository,
                                critic_agent=StubCritic(passed=False))
    assert verdict["pass"] is False and started.attempts(RUN_ID, "claim-1") == 1


def test_judge_claim_judges_the_ledgers_copy_not_the_callers(started, repository, cfo_scope):
    store_claims(RUN_ID, [VALID_E4_CLAIM], ledger=started)
    tampered = VALID_E4_CLAIM.model_copy(update={"statement": "E4 is ready for cutover"})
    critic = StubCritic(passed=True)
    steps.judge_claim(RUN_ID, tampered, cfo_scope, ledger=started, repository=repository, critic_agent=critic)
    assert VALID_E4_CLAIM.statement in critic.prompts[0] and "ready for cutover" not in critic.prompts[0]


def test_judge_claim_refuses_a_scope_other_than_the_runs(started, repository, entity_four_lead_scope):
    store_claims(RUN_ID, [VALID_E4_CLAIM], ledger=started)
    critic = StubCritic(passed=True)
    with pytest.raises(OutOfScope):
        steps.judge_claim(RUN_ID, VALID_E4_CLAIM, entity_four_lead_scope, ledger=started, repository=repository,
                          critic_agent=critic)
    assert not critic.prompts and started.attempts(RUN_ID, "claim-1") == 0


def test_an_out_of_scope_citation_is_rejected_without_a_model_call(ledger, repository, entity_four_lead_scope):
    check_budget(question(entity_four_lead_scope), ledger=ledger)
    e2_claim = BlockerClaim(claim_id="claim-1", statement="E2 is blocked by DEF-0447",
                            chain=[{"artefact": "defect_log", "row_id": "DEF-0447"}])
    store_claims(RUN_ID, [e2_claim], ledger=ledger)
    critic = StubCritic(passed=True)
    verdict = steps.judge_claim(RUN_ID, e2_claim, entity_four_lead_scope, ledger=ledger, repository=repository,
                                critic_agent=critic)
    assert verdict["pass"] is False and not critic.prompts and ledger.steps(RUN_ID)[-1]["prompt"] is None
```
- [ ] **Step 2: Run:** `uv run --locked pytest tests/infra/functions/test_steps.py --no-cov 2>&1 | tail -1`. Expected: `5 failed, 18 passed`, with `AttributeError: module 'infra.functions.steps' has no attribute 'judge_claim'`.
- [ ] **Step 3: Implement.** Append to `infra/functions/steps.py`:
```python


def judge_claim(run_id: str, claim: BlockerClaim, scope: Scope, *, ledger: Ledger, repository: ArtefactRepository,
                critic_agent: Callable | None = None) -> dict:
    """Judge one claim with the blind critic (agents/critic.py) and record the verdict, which raises the attempt
    count the retry guard reads. Returns the verdict (`pass`, `reason`, ...).

    The critic judges the ledger's copy of the claim (what was stored is what is judged), under the run's own scope:
    a different scope raises OutOfScope. It sees only the claim and its cited rows, and fails closed.
    """
    if scope.model_dump(mode="json") != ledger.run(run_id)["scope"]:
        raise OutOfScope(f"run {run_id} was started under another scope")
    stored = ledger.claim(run_id, claim.claim_id)
    agent = critic_agent or critic.make_agent(load_prompt(critic.CRITIC_AGENT_NAME))
    replies = []

    def recording_agent(model_input: str):
        reply = agent(model_input)
        replies.append(reply)
        return reply
    verdict = critic.judge(stored, repository, scope, agent=recording_agent)
    ledger.record_verdict(run_id, claim.claim_id, verdict)
    critic_model_id = get_settings().critic_model_id
    record_usage(ledger, run_id, [usage for reply in replies for usage in usage_of(reply, critic_model_id)])
    verdict_prompt = verdict.get("prompt")
    record_step(ledger, run_id, STEP_JUDGE_CLAIM, agent=critic.CRITIC_AGENT_NAME,
                prompt=PromptRef(**verdict_prompt) if verdict_prompt else None)
    return verdict
```
- [ ] **Step 4: Run:** `uv run --locked pytest tests/infra/functions/test_steps.py --no-cov 2>&1 | tail -1`. Expected: `23 passed in …s`.
- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/functions/steps.py tests/infra/functions/test_steps.py
git commit -m "judge_claim state: the blind critic on the ledger's copy under the run's scope; verdict, cost and trace recorded"
```
Expected: start + 8 (dry-run `291 passed`).

**Task done when:** `uv run --locked pytest tests/infra/functions/test_steps.py --no-cov -k judge_claim 2>&1 | tail -1 | cut -d, -f1` prints `4 passed`.

### Task 3: `write_answer`

**Files:** Modify `infra/functions/steps.py`, `tests/infra/functions/test_steps.py`

**Produces:** `infra.functions.steps.real_writer() -> Writer`, `write_answer(run_id: str, question: Question, passed_claims: list[BlockerClaim], *, ledger: Ledger, repository: ArtefactRepository | None = None, writer: Writer | None = None, partial: PartialAnswer | None = None) -> AskResponse`. **Consumes:** `agents.writer.write`, `WRITER_AGENT_NAME` (H3); `Ledger.claims`, `rejected`, `run`, `steps` (H1); `rejected_claim` (H2a). **Consumed by:** Task 4, Task 5, H6, P3, the `/ask` response (L3 returns the machine's output).

- [ ] **Step 1: Failing tests.** Append to `tests/infra/functions/test_steps.py`:
```python


def test_write_answer_words_only_claims_the_ledger_marks_passed(started, repository, cfo_scope):
    store_claims(RUN_ID, [VALID_E4_CLAIM, SECOND_CLAIM], ledger=started)
    steps.judge_claim(RUN_ID, VALID_E4_CLAIM, cfo_scope, ledger=started, repository=repository,
                      critic_agent=StubCritic(passed=True))
    response = steps.write_answer(RUN_ID, question(cfo_scope), [VALID_E4_CLAIM, SECOND_CLAIM], ledger=started,
                                  repository=repository, writer=stub_writer)
    assert [bullet.text for bullet in response.answer.bullets] == [VALID_E4_CLAIM.statement]
    assert (response.partial, response.partial_reason, response.rejected) == (False, None, [])
    assert response.cost_usd == pytest.approx(started.run(RUN_ID)["cost_usd"]) and response.cost_usd > 0
    assert [step.step for step in response.trace] == ["check_budget", "store_claims", "judge_claim", "write_answer"]


def test_write_answer_reports_rejected_claims_and_their_count(started, repository, cfo_scope):
    store_claims(RUN_ID, [VALID_E4_CLAIM], ledger=started)
    steps.judge_claim(RUN_ID, VALID_E4_CLAIM, cfo_scope, ledger=started, repository=repository,
                      critic_agent=StubCritic(passed=False))
    record_rejection(RUN_ID, "claim-1", ledger=started)
    response = steps.write_answer(RUN_ID, question(cfo_scope), [], ledger=started, writer=stub_writer)
    assert [rejected.claim_id for rejected in response.rejected] == ["claim-1"]
    assert response.answer.rejected_count == 1 and response.answer.bullets == []


def test_write_answer_with_a_partial_and_nothing_passed_has_no_answer(started, cfo_scope):
    calls = []
    response = steps.write_answer(RUN_ID, question(cfo_scope), [], ledger=started, writer=calls.append,
                                  partial=PartialAnswer(reason="unknown entity E9"))
    assert (response.answer, response.partial, response.partial_reason) == (None, True, "unknown entity E9")
    assert not calls


def test_the_real_writer_is_the_default():
    from agents.writer import write
    assert steps.real_writer() is write
```
- [ ] **Step 2: Run:** `uv run --locked pytest tests/infra/functions/test_steps.py --no-cov 2>&1 | tail -1`. Expected: `4 failed, 23 passed`, with `AttributeError: module 'infra.functions.steps' has no attribute 'write_answer'` (and `'real_writer'`).
- [ ] **Step 3: Implement.** Append to `infra/functions/steps.py`:
```python


def real_writer() -> Writer:
    from agents.writer import write
    return write


def write_answer(run_id: str, question: Question, passed_claims: list[BlockerClaim], *, ledger: Ledger,
                 repository: ArtefactRepository | None = None, writer: Writer | None = None,
                 partial: PartialAnswer | None = None) -> AskResponse:
    """Last state: the writer words the passed claims, and the response carries the rejected claims, the run's cost
    and its trace.

    Only claims the ledger marks passed reach the writer, in the ledger's copy (anything else is dropped and logged).
    A partial run with nothing passed has no answer and calls no writer. `repository` is accepted so every state has
    the same ports; the writer needs no rows.
    """
    passed_in_ledger = {stored["claim_id"]: stored["claim"] for stored in ledger.claims(run_id)
                        if stored["status"] == ClaimStatus.PASSED}
    verified = [BlockerClaim.model_validate(passed_in_ledger[claim.claim_id]) for claim in passed_claims
                if claim.claim_id in passed_in_ledger]
    if len(verified) != len(passed_claims):
        logger.warning("write_answer dropped claims the ledger does not mark passed: %s",
                       [claim.claim_id for claim in passed_claims if claim.claim_id not in passed_in_ledger])
    rejected = [rejected_claim(record) for record in ledger.rejected(run_id)]
    answer = None
    if verified or partial is None:
        result = (writer or real_writer())(WriterInput(scope=question.scope, question=question.question,
                                                       passed_claims=verified))
        record_usage(ledger, run_id, result.usage)
        answer = result.answer.model_copy(update={"rejected_count": len(rejected)})
    record_step(ledger, run_id, STEP_WRITE_ANSWER, agent=WRITER_AGENT_NAME if answer else None,
                prompt=prompt_ref(WRITER_AGENT_NAME) if verified else None)
    return AskResponse(run_id=run_id, answer=answer, rejected=rejected, cost_usd=ledger.run(run_id)["cost_usd"],
                       partial=partial is not None, partial_reason=partial.reason if partial else None,
                       trace=[TraceStep.model_validate(step) for step in ledger.steps(run_id)])
```
- [ ] **Step 4: Run:** `uv run --locked pytest tests/infra/functions/test_steps.py --no-cov 2>&1 | tail -1`. Expected: `27 passed in …s`.
- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL|infra/functions/steps"
git add infra/functions/steps.py tests/infra/functions/test_steps.py
git commit -m "write_answer state: the writer on ledger-passed claims; rejected, cost and trace from the ledger"
```
Expected: start + 12 (dry-run `295 passed`); `infra/functions/steps.py ... 99%` with line 152 (`real_orchestrator`'s import, covered once P2 runs) the only miss.

**Task done when:** `uv run --locked pytest tests/infra/functions/test_steps.py --no-cov -k write_answer 2>&1 | tail -1 | cut -d, -f1` prints `3 passed`.

### Task 4: `infra/functions/spine.py`, the whole ask spine in-process

**Files:** Create `infra/functions/spine.py` *(new)*, `tests/infra/functions/test_spine.py` *(new)*

**Produces:** `infra.functions.spine.SpineAgents(orchestrator: OrchestratorAgent | None = None, writer: Writer | None = None, critic_agent: Callable | None = None)`, `settle_claim(question, claim, *, ledger, repository, agents) -> tuple[BlockerClaim | None, PartialAnswer | None]`, `run_spine(question: Question, *, ledger: Ledger, repository: ArtefactRepository, agents: SpineAgents = SpineAgents()) -> AskResponse`. **Consumes:** Tasks 1–3 and H2a. **Consumed by:** H6 (`infra/functions/local.py` *(new)*), P3 (may call `run_spine`).

- [ ] **Step 1: Failing tests.** Create `tests/infra/functions/test_spine.py`:
```python
"""The whole ask spine in-process (infra/functions/spine.py), in the order the Step Functions machine runs it, with stubs."""
import json

from adapters.memory_ledger import InMemoryLedger
from agents.writer import verbatim_answer
from infra.functions.spine import SpineAgents, run_spine
from tools.models import (BlockerClaim, OrchestratorResult, PartialAnswer, Plan, Question, WriterInput,
                          WriterResult)

RUN_ID = "run-spine"
BUDGET_USD = 0.50
MAX_ATTEMPTS = 2   # at most 2 attempts per claim, one retry (the lead's ruling on Q09)
E4_CLAIM = BlockerClaim(
    claim_id="claim-1",
    statement="212 customer records were rejected in load cycle 3, tied to open High defect DEF-0412",
    chain=[{"artefact": "reconciliation_results", "row_id": "RC-C3-E4-customers", "role_in_chain": "failed check"},
           {"artefact": "defect_log", "row_id": "DEF-0412", "role_in_chain": "cause"},
           {"artefact": "cutover_runbook", "row_id": "E4#RB-010", "role_in_chain": "blocked step"}])


def question(scope) -> Question:
    return Question(run_id=RUN_ID, scope=scope, entity_id="E4", question="What is blocking cutover for E4?",
                    budget_usd=BUDGET_USD, max_attempts=MAX_ATTEMPTS)


class StubOrchestrator:
    """Stands in for P2: the first plan and each re-plan return the given results; calls are recorded."""

    def __init__(self, plan_claims, replan_claims=None, plan_partial=None, replan_partial=None):
        self.plan_claims, self.plan_partial = plan_claims, plan_partial
        self.replan_claims = plan_claims if replan_claims is None else replan_claims
        self.replan_partial = replan_partial
        self.calls = []

    def orchestrate(self, question, repository, ledger):
        self.calls.append(None)
        return OrchestratorResult(plan=Plan(run_id=question.run_id, steps=[]), claims=self.plan_claims,
                                  partial=self.plan_partial)

    def replan(self, question, rejected_claim, verdict, repository, ledger):
        self.calls.append(rejected_claim.claim_id)
        return OrchestratorResult(plan=Plan(run_id=question.run_id, steps=[]), claims=self.replan_claims,
                                  partial=self.replan_partial)


def critic_replying(*passes):
    """A stub critic that gives these verdicts in turn (and the last one from then on)."""
    remaining = list(passes)

    def judge(prompt):
        claim_id = json.loads(prompt.split("<claim>")[1].split("</claim>")[0])["claim_id"]
        passed = remaining.pop(0) if len(remaining) > 1 else remaining[0]
        return json.dumps({"claim_id": claim_id, "pass": passed, "reason": "stub", "missing_evidence": []})
    return judge


def stub_writer(writer_input: WriterInput) -> WriterResult:
    return WriterResult(answer=verbatim_answer(writer_input.passed_claims))


def run(cfo_scope, repository, orchestrator, critic, ledger=None):
    agents = SpineAgents(orchestrator=orchestrator, writer=stub_writer, critic_agent=critic)
    return run_spine(question(cfo_scope), ledger=ledger or InMemoryLedger(), repository=repository, agents=agents)


def test_a_supported_claim_reaches_the_answer_with_its_citations(repository, cfo_scope):
    response = run(cfo_scope, repository, StubOrchestrator([E4_CLAIM]), critic_replying(True))
    cited = {citation.label() for bullet in response.answer.bullets for citation in bullet.citations}
    assert {"reconciliation_results:RC-C3-E4-customers", "defect_log:DEF-0412", "cutover_runbook:E4#RB-010"} <= cited
    assert response.rejected == [] and response.partial is False


def test_a_rejected_claim_is_re_planned_under_the_same_id_then_passes(repository, cfo_scope):
    ledger = InMemoryLedger()
    orchestrator = StubOrchestrator([E4_CLAIM])
    response = run(cfo_scope, repository, orchestrator, critic_replying(False, True), ledger)
    assert orchestrator.calls == [None, "claim-1"]
    assert ledger.attempts(RUN_ID, "claim-1") == 2 and len(response.answer.bullets) == 1


def test_a_claim_the_critic_never_passes_stops_at_the_retry_limit(repository, cfo_scope):
    ledger = InMemoryLedger()
    orchestrator = StubOrchestrator([E4_CLAIM])
    response = run(cfo_scope, repository, orchestrator, critic_replying(False), ledger)
    assert [rejected.claim_id for rejected in response.rejected] == ["claim-1"]
    assert len(response.rejected[0].verdicts) == MAX_ATTEMPTS == len(ledger.rejected(RUN_ID)[0]["verdicts"])
    assert orchestrator.calls == [None] + ["claim-1"] * (MAX_ATTEMPTS - 1)
    assert response.answer.bullets == [] and response.answer.rejected_count == 1


def test_a_re_plan_without_a_claim_ends_in_the_rejected_records(repository, cfo_scope):
    ledger = InMemoryLedger()
    response = run(cfo_scope, repository, StubOrchestrator([E4_CLAIM], replan_claims=[]), critic_replying(False),
                   ledger)
    assert [rejected.claim_id for rejected in response.rejected] == ["claim-1"]
    assert ledger.attempts(RUN_ID, "claim-1") == 1


def test_an_unknown_entity_answers_partial_without_the_writer_or_the_critic(repository, cfo_scope):
    critic_prompts = []
    orchestrator = StubOrchestrator([], plan_partial=PartialAnswer(reason="unknown entity E9"))
    response = run(cfo_scope, repository, orchestrator, critic_prompts.append)
    assert (response.answer, response.partial, response.partial_reason) == (None, True, "unknown entity E9")
    assert not critic_prompts and "judge_claim" not in [step.step for step in response.trace]


def test_claims_gathered_before_the_budget_ran_out_are_judged_and_the_answer_is_partial(repository, cfo_scope):
    orchestrator = StubOrchestrator([E4_CLAIM], plan_partial=PartialAnswer(reason="the run's budget is spent"))
    response = run(cfo_scope, repository, orchestrator, critic_replying(True))
    assert response.partial is True and len(response.answer.bullets) == 1


class LedgerWithNothingLeft(InMemoryLedger):
    """A ledger whose budget is spent from the start."""

    def budget_remaining(self, run_id: str) -> float:
        return 0.0


def test_a_spent_budget_at_the_start_answers_partial_without_any_agent(repository, cfo_scope):
    orchestrator = StubOrchestrator([E4_CLAIM])
    response = run(cfo_scope, repository, orchestrator, critic_replying(True), LedgerWithNothingLeft())
    assert response.partial is True and "budget" in response.partial_reason and orchestrator.calls == []
```
- [ ] **Step 2: Run:** `uv run --locked pytest tests/infra/functions/test_spine.py --no-cov 2>&1 | grep -E "^E  " | head -1`. Expected: `E   ModuleNotFoundError: No module named 'infra.functions.spine'`.
- [ ] **Step 3: Implement.** Create `infra/functions/spine.py`:
```python
"""The ask spine in-process, in the order the Step Functions Express machine runs the states (infra/functions/steps.py).

Local runs (scripts/ask.py), the eval runner's local asker (infra/functions/local.py) and the tests use run_spine; in AWS the
state machine runs the same functions through infra/functions/states.py. Every loop is bounded by the ledger's attempt
counter (retry_decision), never by a model.
"""
from dataclasses import dataclass
from typing import Callable

from infra.functions.steps import (REJECT, OrchestratorAgent, Writer, check_budget, judge_claim, record_rejection,
                        retry_decision, run_orchestrator, store_claims, write_answer)
from tools.api_schema import AskResponse
from tools.models import BlockerClaim, PartialAnswer, Question
from tools.ports import ArtefactRepository, Ledger


@dataclass(frozen=True)
class SpineAgents:
    """The agents the spine calls. None means the real one: P2's orchestrator, the Bedrock critic, H3's writer."""
    orchestrator: OrchestratorAgent | None = None
    writer: Writer | None = None
    critic_agent: Callable | None = None


def settle_claim(question: Question, claim: BlockerClaim, *, ledger: Ledger, repository: ArtefactRepository,
                 agents: SpineAgents) -> tuple[BlockerClaim | None, PartialAnswer | None]:
    """Judge one claim until it passes or the retry guard rejects it. Returns the passed claim (or None) and any
    PartialAnswer a re-plan returned. A re-plan that brings back no claim ends in the rejected records."""
    run_id = question.run_id
    partial = None
    while True:
        verdict = judge_claim(run_id, claim, question.scope, ledger=ledger, repository=repository,
                              critic_agent=agents.critic_agent)
        if verdict.get("pass") is True:
            return claim, partial
        if retry_decision(run_id, claim.claim_id, ledger=ledger, max_attempts=question.max_attempts) == REJECT:
            record_rejection(run_id, claim.claim_id, ledger=ledger)
            return None, partial
        replanned = run_orchestrator(question, ledger=ledger, repository=repository, rejected_claim=claim,
                                     verdict=verdict, orchestrator=agents.orchestrator)
        partial = partial or replanned.partial
        if not replanned.claims:
            record_rejection(run_id, claim.claim_id, ledger=ledger)
            return None, partial
        claim = store_claims(run_id, replanned.claims, ledger=ledger)[0]


def run_spine(question: Question, *, ledger: Ledger, repository: ArtefactRepository,
              agents: SpineAgents = SpineAgents()) -> AskResponse:
    """One /ask, start to finish. Raises OutOfScope, before anything is written, for an entity outside the scope.

    A spent budget at the start answers partial without any agent. Claims the orchestrator gathered before it ran
    out are still judged, and the answer is marked partial.
    """
    run_id = question.run_id
    remaining = check_budget(question, ledger=ledger)
    if isinstance(remaining, PartialAnswer):
        return write_answer(run_id, question, [], ledger=ledger, repository=repository, writer=agents.writer,
                            partial=remaining)
    planned = run_orchestrator(question, ledger=ledger, repository=repository, orchestrator=agents.orchestrator)
    partial = planned.partial
    passed = []
    for claim in store_claims(run_id, planned.claims, ledger=ledger):
        settled, replan_partial = settle_claim(question, claim, ledger=ledger, repository=repository, agents=agents)
        passed += [settled] if settled else []
        partial = partial or replan_partial
    return write_answer(run_id, question, passed, ledger=ledger, repository=repository, writer=agents.writer,
                        partial=partial)
```
- [ ] **Step 4: Run:** `uv run --locked pytest tests/infra/functions/test_spine.py --no-cov 2>&1 | tail -1`. Expected: `7 passed in …s`.
- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/functions/spine.py tests/infra/functions/test_spine.py
git commit -m "The ask spine in-process: states in the machine's order, every loop bounded by the retry guard"
```
Expected: start + 19 (dry-run `302 passed`), no `infra/functions/spine.py` line (100%).

**Task done when:** `uv run --locked pytest tests/infra/functions/test_spine.py --no-cov -k retry_limit 2>&1 | tail -1 | cut -d, -f1` prints `1 passed` (the claim the critic never passes ends with 2 verdicts).

### Task 5: `infra/functions/states.py`, the ask machine's Lambda entry points

**Files:** Create `infra/functions/states.py` *(new)*, `tests/infra/functions/test_states.py` *(new)*

**Produces:** `infra.functions.states.check_budget`, `run_orchestrator`, `store_claims`, `judge_claim`, `retry_decision`, `record_rejection`, `write_answer` (each `(event: dict, context) -> dict`); `StateIO`, `BudgetCheck`, `OrchestratorEvent`, `StoreClaimsEvent`, `ClaimEvent`, `RetryEvent`, `WriteAnswerEvent`; `make_ledger()`, `make_repository()`. **Consumes:** Tasks 1–3, H2a; `adapters.ledger_from_settings`, `repository_from_settings`. **Consumed by:** Yaw's FlowStack (Y2), H4 (adds the publish Lambdas here).

- [ ] **Step 1: Failing tests.** Create `tests/infra/functions/test_states.py`:
```python
"""The Lambda entry points (infra/functions/states.py): JSON in, JSON out, one per state, driven as the machine would."""
import json

import pytest
from pydantic import ValidationError

from adapters.memory_ledger import InMemoryLedger
from agents.writer import verbatim_answer
from infra.functions import states, steps
from tools.models import BlockerClaim, OrchestratorResult, Plan, Question, WriterResult

RUN_ID = "run-handlers"
MAX_ATTEMPTS = 2   # at most 2 attempts per claim, one retry (the lead's ruling on Q09)
E4_CLAIM = BlockerClaim(
    claim_id="claim-1", statement="212 customer records were rejected, tied to open defect DEF-0412",
    chain=[{"artefact": "reconciliation_results", "row_id": "RC-C3-E4-customers", "role_in_chain": "failed check"},
           {"artefact": "defect_log", "row_id": "DEF-0412", "role_in_chain": "cause"}])


def as_state_machine_json(output: dict) -> dict:
    """What the next state receives: Step Functions passes JSON, nothing else."""
    return json.loads(json.dumps(output))


class StubOrchestrator:
    def orchestrate(self, question, repository, ledger):
        return OrchestratorResult(plan=Plan(run_id=question.run_id, steps=[]), claims=[E4_CLAIM])

    def replan(self, question, rejected_claim, verdict, repository, ledger):
        return OrchestratorResult(plan=Plan(run_id=question.run_id, steps=[]), claims=[rejected_claim])


def rejecting_critic(prompt):
    claim_id = json.loads(prompt.split("<claim>")[1].split("</claim>")[0])["claim_id"]
    return json.dumps({"claim_id": claim_id, "pass": False, "reason": "stub", "missing_evidence": []})


@pytest.fixture
def ledger(monkeypatch, repository):
    ledger = InMemoryLedger()
    monkeypatch.setattr(states, "make_ledger", lambda: ledger)
    monkeypatch.setattr(states, "make_repository", lambda: repository)
    monkeypatch.setattr(steps, "real_orchestrator", StubOrchestrator)
    monkeypatch.setattr(steps.critic, "make_agent", lambda prompt: rejecting_critic)
    monkeypatch.setattr(steps, "real_writer", lambda: lambda writer_input: WriterResult(
        answer=verbatim_answer(writer_input.passed_claims)))
    return ledger


def question_event(cfo_scope) -> dict:
    return as_state_machine_json(Question(
        run_id=RUN_ID, scope=cfo_scope, entity_id="E4", question="What is blocking cutover for E4?",
        budget_usd=0.5, max_attempts=MAX_ATTEMPTS).model_dump(mode="json"))


def test_the_states_chain_through_json_to_a_rejected_record(ledger, cfo_scope):
    question = question_event(cfo_scope)
    assert as_state_machine_json(states.check_budget(question, None))["remaining_usd"] == 0.5
    planned = as_state_machine_json(states.run_orchestrator({"question": question}, None))
    stored = as_state_machine_json(states.store_claims({"run_id": RUN_ID, "claims": planned["claims"]}, None))
    claim_id = stored["claims"][0]["claim_id"]
    decision = None
    while decision != "reject":
        judged = as_state_machine_json(states.judge_claim({"run_id": RUN_ID, "claim_id": claim_id}, None))
        assert judged["passed"] is False
        decision = as_state_machine_json(states.retry_decision(
            {"run_id": RUN_ID, "claim_id": claim_id, "max_attempts": MAX_ATTEMPTS}, None))["decision"]
        if decision == "retry":
            replanned = states.run_orchestrator({"question": question, "claim_id": claim_id}, None)
            states.store_claims({"run_id": RUN_ID, "claims": replanned["claims"]}, None)
    rejected = as_state_machine_json(states.record_rejection({"run_id": RUN_ID, "claim_id": claim_id}, None))
    assert len(rejected["verdicts"]) == MAX_ATTEMPTS and rejected["verdicts"][0]["pass"] is False
    response = as_state_machine_json(states.write_answer({"question": question}, None))
    assert response["rejected"][0]["claim_id"] == claim_id and response["answer"]["rejected_count"] == 1


def test_a_spent_budget_comes_back_as_a_partial(ledger, monkeypatch, cfo_scope):
    monkeypatch.setattr(ledger, "budget_remaining", lambda run_id: 0.0)
    checked = states.check_budget(question_event(cfo_scope), None)
    assert checked["remaining_usd"] is None and "budget" in checked["partial"]["reason"]


def test_an_event_with_unknown_keys_is_refused(ledger, cfo_scope):
    with pytest.raises(ValidationError):
        states.judge_claim({"run_id": RUN_ID, "claim_id": "claim-1", "attempts": 0}, None)
    with pytest.raises(ValidationError):
        states.check_budget({**question_event(cfo_scope), "max_attempts": 0}, None)


def test_dependencies_come_from_settings():
    states.make_ledger.cache_clear()
    assert isinstance(states.make_ledger(), InMemoryLedger)   # LEDGER_BACKEND defaults to memory
    assert states.make_ledger() is states.make_ledger()     # one per Lambda container
    assert states.make_repository().load("entities")
    states.make_ledger.cache_clear()
```
- [ ] **Step 2: Run:** `uv run --locked pytest tests/infra/functions/test_states.py --no-cov 2>&1 | grep -E "^E  " | head -1`. Expected: `E   ImportError: cannot import name 'states' from 'infra.functions' (...)`.
- [ ] **Step 3: Implement.** Create `infra/functions/states.py`:
```python
"""Lambda entry points for the ask spine's states: `infra.functions.states.<state>` (docs/DEVOPS_HANDOVER.md).

Each handler validates the state's JSON input against a strict model, reads what the state needs from the ledger
(never from the event: claims, verdicts and the scope are the ledger's), calls its infra/functions/steps.py function with the
ledger, repository and agents built from config.py, and returns JSON for the next state:

  check_budget      Question                        -> {run_id, remaining_usd, partial}
  run_orchestrator  {question, claim_id?}           -> OrchestratorResult   (claim_id: re-plan that claim)
  store_claims      {run_id, claims}                -> {claims}
  judge_claim       {run_id, claim_id}              -> {run_id, claim_id, passed}
  retry_decision    {run_id, claim_id, max_attempts?} -> {run_id, claim_id, decision}
  record_rejection  {run_id, claim_id}              -> RejectedClaim
  write_answer      {question, partial?}            -> AskResponse (the claims the ledger marks passed)
"""
from functools import lru_cache

from pydantic import BaseModel, Field

from adapters import ledger_from_settings, repository_from_settings
from infra.functions import steps
from tools.constants import ClaimStatus
from tools.models import BlockerClaim, PartialAnswer, Question, Scope, StrictModel


class StateIO(StrictModel):
    """Base for the states' JSON inputs and outputs: unknown keys are refused, so a renamed field fails loudly."""


class BudgetCheck(StateIO):
    run_id: str
    remaining_usd: float | None = None
    partial: PartialAnswer | None = None


class OrchestratorEvent(StateIO):
    question: Question
    claim_id: str | None = None


class StoreClaimsEvent(StateIO):
    run_id: str = Field(min_length=1)
    claims: list[BlockerClaim]


class ClaimEvent(StateIO):
    run_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)


class RetryEvent(ClaimEvent):
    max_attempts: int | None = Field(default=None, ge=1)


class WriteAnswerEvent(StateIO):
    question: Question
    partial: PartialAnswer | None = None


# ---- dependencies, built once per Lambda container from config.py (the tests replace these) ----------------------
@lru_cache(maxsize=1)
def make_ledger():
    return ledger_from_settings()


@lru_cache(maxsize=1)
def make_repository():
    return repository_from_settings()


def _as_json(model: BaseModel) -> dict:
    return model.model_dump(mode="json", by_alias=True)


def _ledger_claim(run_id: str, claim_id: str) -> BlockerClaim:
    return BlockerClaim.model_validate(make_ledger().claim(run_id, claim_id))


# ---- the handlers ----------------------------------------------------------------------------------------------
def check_budget(event: dict, context) -> dict:
    question = Question.model_validate(event)
    remaining = steps.check_budget(question, ledger=make_ledger())
    if isinstance(remaining, PartialAnswer):
        return _as_json(BudgetCheck(run_id=question.run_id, partial=remaining))
    return _as_json(BudgetCheck(run_id=question.run_id, remaining_usd=remaining))


def run_orchestrator(event: dict, context) -> dict:
    request = OrchestratorEvent.model_validate(event)
    run_id = request.question.run_id
    rejected = _ledger_claim(run_id, request.claim_id) if request.claim_id else None
    return _as_json(steps.run_orchestrator(request.question, ledger=make_ledger(), repository=make_repository(),
                                           rejected_claim=rejected))


def store_claims(event: dict, context) -> dict:
    request = StoreClaimsEvent.model_validate(event)
    stored = steps.store_claims(request.run_id, request.claims, ledger=make_ledger())
    return {"claims": [_as_json(claim) for claim in stored]}


def judge_claim(event: dict, context) -> dict:
    request = ClaimEvent.model_validate(event)
    ledger = make_ledger()
    scope = Scope.model_validate(ledger.run(request.run_id)["scope"])
    verdict = steps.judge_claim(request.run_id, _ledger_claim(request.run_id, request.claim_id), scope,
                                ledger=ledger, repository=make_repository())
    return {"run_id": request.run_id, "claim_id": request.claim_id, "passed": verdict.get("pass") is True}


def retry_decision(event: dict, context) -> dict:
    request = RetryEvent.model_validate(event)
    decision = steps.retry_decision(request.run_id, request.claim_id, ledger=make_ledger(),
                                    max_attempts=request.max_attempts)
    return {"run_id": request.run_id, "claim_id": request.claim_id, "decision": decision}


def record_rejection(event: dict, context) -> dict:
    request = ClaimEvent.model_validate(event)
    return _as_json(steps.record_rejection(request.run_id, request.claim_id, ledger=make_ledger()))


def write_answer(event: dict, context) -> dict:
    request = WriteAnswerEvent.model_validate(event)
    ledger = make_ledger()
    run_id = request.question.run_id
    passed = [BlockerClaim.model_validate(stored["claim"]) for stored in ledger.claims(run_id)
              if stored["status"] == ClaimStatus.PASSED]
    return _as_json(steps.write_answer(run_id, request.question, passed, ledger=ledger,
                                       repository=make_repository(), partial=request.partial))
```
- [ ] **Step 4: Run:** `uv run --locked pytest tests/infra/functions/test_states.py --no-cov 2>&1 | tail -1`. Expected: `4 passed in …s`.
- [ ] **Step 5: Guards, full suite and commit**
```bash
uv run --locked pytest tests/test_architecture.py tests/test_code_style.py --no-cov 2>&1 | tail -1
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/functions/states.py tests/infra/functions/test_states.py
git commit -m "Lambda entry points for the ask machine's states: strict JSON events, ledger-read claims and scope"
```
Expected: guards pass; start + 23 (dry-run `306 passed`), `TOTAL ... 98%`.

**Task done when:** `uv run --locked pytest tests/infra/functions/test_states.py --no-cov -k chain 2>&1 | tail -1 | cut -d, -f1` prints `1 passed`.

### Task 6: Handover, docs, review and PR
- [ ] **Step 1: `docs/DEVOPS_HANDOVER.md`.** In the two rows whose entry point is `` `infra.functions.steps.<name>` *(planned)* ``, change the entry point to `` `infra.functions.states.<name>` `` (built), and add below the table a section:
```markdown
### Ask machine states (Huvison, `infra/functions/states.py`)
| State | Event | Result |
|---|---|---|
| `check_budget` | the `Question` | `{run_id, remaining_usd, partial}`: go to `write_answer` with `partial` when it isn't null |
| `run_orchestrator` | `{question, claim_id?}` (with `claim_id`: re-plan that claim) | `OrchestratorResult` |
| `store_claims` | `{run_id, claims}` | `{claims}` |
| `judge_claim` | `{run_id, claim_id}` | `{run_id, claim_id, passed}` |
| `retry_decision` | `{run_id, claim_id, max_attempts?}` | `{run_id, claim_id, decision: "retry" \| "reject"}` (2 attempts per claim) |
| `record_rejection` | `{run_id, claim_id}` | `RejectedClaim` |
| `write_answer` | `{question, partial?}` | `AskResponse`: the `/ask` body |

Order: `check_budget` → `run_orchestrator` → `store_claims` → Map over the claims (one at a time): `judge_claim` → passed: done; else `retry_decision` → `retry`: `run_orchestrator` with `claim_id` → `store_claims` → `judge_claim`; `reject`: `record_rejection` → after the Map, `write_answer`. Claims, verdicts and the scope are read from the ledger by `run_id` and `claim_id`, never taken from the event.
```
  (`docs/DEVOPS_HANDOVER.md` is Patrick's: say so in the PR body.)
- [ ] **Step 2: `HANDOFF.md`.** Under `## What's real`, add: `- The ask spine end to end in-process (\`infra/functions/spine.py\`) and as one Lambda per Step Functions state (\`infra/functions/states.py\`): the blind critic judges the stored claim under the run's scope; a rejected claim is re-planned under its own ID; after 2 attempts it lands in the rejected records; only ledger-passed claims reach the writer; every model call's cost is on the run.`
- [ ] **Step 3: Commit:** `git add docs/DEVOPS_HANDOVER.md HANDOFF.md && git commit -m "Handover: the ask machine's states, events and order; HANDOFF line"`; then `uv run --locked pytest tests/test_dependencies.py --no-cov 2>&1 | tail -1`. Expected: `4 passed`.
- [ ] **Step 4:** Review Focus by hand; results in `.superpowers/ledger-H2b.md`.
- [ ] **Step 5:** `git diff develop --stat`. Expected: `HANDOFF.md`, `docs/DEVOPS_HANDOVER.md`, `infra/functions/states.py`, `infra/functions/spine.py`, `infra/functions/steps.py`, `tests/infra/functions/test_states.py`, `tests/infra/functions/test_spine.py`, `tests/infra/functions/test_steps.py` (8 files).
- [ ] **Step 6: With Huvison's OK only:** push `feature/ask-spine-agent-states`, PR to `develop` ("Ask spine: agent states, in-process spine and Lambda handlers (H2b)"), body with the count, the alignment table from the spec (for Patrick's P3), the handover change (for Yaw) and the rulings. No attribution lines.
- [ ] **Step 7:** [[Build order]]: H2 → `in review (PR #nn)` (H2a merged, H2b in review), then `merged`. Tell Yaw (the state table is in the handover), Patrick (`run_spine` and the signature differences), Linus (`/ask` returns the `write_answer` output).

**Task done when:** the PR is open with the alignment table in its body, and Yaw has the handover link.

## Done means
- [ ] **The three agent states are tested.** *Verify:* on `develop`, `uv run --locked pytest tests/infra/functions/test_steps.py --no-cov 2>&1 | tail -1` prints `27 passed`.
- [ ] **The local sequence passes a claim and handles a rejection after one retry.** *Verify:* `uv run --locked pytest tests/infra/functions/test_spine.py --no-cov 2>&1 | tail -1` prints `7 passed`.
- [ ] **Every state has a Lambda entry point.** *Verify:* `uv run python -c "from infra.functions import states; print([name for name in ('check_budget','run_orchestrator','store_claims','judge_claim','retry_decision','record_rejection','write_answer') if callable(getattr(states, name))])"` prints all seven names.
- [ ] **No import cycle, and P2 isn't loaded at import.** *Verify:* `uv run python -c "import infra.functions.steps, sys; print('agents.orchestrator' in sys.modules)"` prints `False`.
- [ ] **The handover is current.** *Verify:* `grep -c "infra.functions.states:" docs/DEVOPS_HANDOVER.md` prints at least `2`, and the "Ask machine states" table is there.
- [ ] **Nothing broke.** *Verify:* full suite after merge: start + 23, `TOTAL` ≥ 97%.
- [ ] **Merged.** *Verify:* PR merged into `develop`; [[Build order]] row H2 `merged`.

## Never
- Pass the question, the plan, verdicts or the attempt count to the critic.
- Store a re-planned claim under a new ID, or let anything but `retry_decision` end the loop.
- Treat a critic error as a pass.
- Read a claim, a verdict or the critic's scope from a Step Functions event.
- Call Bedrock or AWS in a test.
- Push to `develop` or `main`, or add attribution lines.

Related: [[H2b - Agent states, local spine and Lambda handlers - spec]], [[H2a - Budget and ledger states - plan]], [[Build order]], [[How to execute a plan]]
