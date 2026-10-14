---
tags: [build, plan, area/evals]
id: H6
owner: Huvison
spec: "[[H6 - Local eval asker - spec]]"
status: ready
updated: 2026-10-14
---
# H6: The local eval asker (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[H6 - Local eval asker - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; ledger the conflict.
3. [[Huvison - trust and flow]] §7; [[H2b - Agent states, local spine and Lambda handlers - spec]]; the repo's `evals/run.py` docstring and `EVALS.md`.
4. [[Working with AI assistants]], [[Deploy and demo checks]].
5. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Huvison.

**Goal:** `infra.functions.local.ask` runs every eval question through the real ask spine in-process and plants Q08's and Q09's faults; the eval runner scores them.

**Architecture:** a thin module over `infra.functions.spine.run_spine`: a fresh in-memory ledger per question (Q08's strips `claim-1`'s citations), and an orchestrator wrapper for Q09. Seams (`make_orchestrator`, `make_critic_agent`, `make_writer`, `ledger_for`) let the tests use stand-ins.

**Tech stack:** Python 3.11, pytest, uv. Bedrock only in the live run (Task 2), never in tests.

**Dry-run status:** Task 1 ran in a throwaway worktree of C1 + H1 + H5 + H3 + H2a + H2b + H4, with P1's `agent_support` and P2's `CLAIM_ID_PREFIX = "claim-"` added as stand-ins (P2's agents aren't needed: the tests replace them). The live eval run (Task 2, Step 4) is **verify in AWS**: it needs P2, L5 and Bedrock.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: `feature/local-eval-asker` from an up-to-date `develop` after **H2b and P2** are merged.
- **Start state:** the dry-run's start was **314 passed**, `TOTAL` 98%. Write your real number in the ledger file; the **delta** must match (+11).
- **The retry limit is decided** (the lead): at most 2 attempts per claim; `config.py` keeps `max_claim_attempts = 2`; Q09 ends with 2 verdicts. Don't change `config.py`, `EVALS.md` or `evals/`.
- **Rules:** `eu-west-1`, `eu.*` models only; synthetic data; no secrets. Settings only in `config.py`; domain constants only in `tools/constants.py`; descriptive names, no single-character names, no magic numbers. **No fault switch in the API, the state machine or `config.py`: only this asker plants faults.** Never weaken a security rule (the critic's pre-check, the scope gate, create-once). Tests in `tests/` mirroring the code; coverage must not drop; no layout or meta guard tests; no Bedrock in tests. Stay in your folders: `infra/functions/local.py`, `tests/infra/functions/test_local.py`, and the doc line in Task 2.
- **Commits:** one per task, the given messages, **no attribution lines**. Never push to `develop` or `main`.

## Review Focus
1. **The faults stay in `infra/functions/local.py`.** `git grep -n "strip_citations\|force_unsupportable_claim" -- ':!evals' ':!EVALS.md'` lists only `infra/functions/local.py` and `tests/infra/functions/test_local.py`.
2. **Q09 reaches the real critic:** the forced claim cites an existing, in-scope row, so the pre-check passes and the model must judge it (check the row: `RC-C3-E4-customers` is FAIL at 91.2 %).
3. **Q08 never reaches the model:** the stripped claim has no citations, so `critic.judge` returns the pre-check's rejection.
4. **Q11 writes nothing:** the refusal comes from `check_budget` before `start_run`.
5. **The live run's honesty:** failures in `evals/results/run-*.json` are recorded as they are (A5a); nothing is re-run until it passes without a code change.

---

### Task 1: `infra/functions/local.py`

**Files:** Create `infra/functions/local.py` *(new)*, `tests/infra/functions/test_local.py` *(new)*

**Produces:** in `infra.functions.local`: the constants of spec §3; `CitationStrippingLedger`, `WithUnsupportableClaim`, `make_orchestrator()`, `make_critic_agent()`, `make_writer()`, `ledger_for(inject)`, `ask(case_input, scope: Scope, repository: ArtefactRepository) -> dict`. **Consumes:** `infra.functions.spine.SpineAgents`, `run_spine`; `infra.functions.steps.OrchestratorAgent`, `Writer`, `question_for`, `real_orchestrator`, `real_writer` (H2a/H2b); `tools.constants.CLAIM_ID_PREFIX` (P2); `evals.run.load_cases`, `run_case`, `Status` (exist, tests only). **Consumed by:** the eval runner (`--asker infra.functions.local.ask`), A5a/A5b (Abdul), P3 (optional).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
uv run python -c "from tools.constants import CLAIM_ID_PREFIX; from config import get_settings; print(CLAIM_ID_PREFIX, get_settings().max_claim_attempts)"
git switch -c feature/local-eval-asker
mkdir -p .superpowers && printf '# Ledger: H6 Local eval asker\n' > .superpowers/ledger-H6.md
```
Expected: your start count, `TOTAL ... 98%`; then `claim- 2` (P2 merged; the limit is 2).
- [ ] **Step 2: Failing tests.** Create `tests/infra/functions/test_local.py`:
```python
"""The eval runner's local asker (infra/functions/local.py): the spine in-process, with the planted faults Q08 and Q09."""
import json
from types import SimpleNamespace

import pytest

from agents.writer import verbatim_answer
from config import get_settings
from evals import run as eval_runner
from infra.functions import local
from tools.models import BlockerClaim, OrchestratorResult, PartialAnswer, Plan, WriterResult

E4_CHAIN_CLAIM = BlockerClaim(
    claim_id="claim-1",
    statement="Customer master reconciles at 91.2 % against 98 % in cycle C3, caused by open defect DEF-0412",
    chain=[{"artefact": "reconciliation_results", "row_id": "RC-C3-E4-customers", "role_in_chain": "failed check"},
           {"artefact": "defect_log", "row_id": "DEF-0412", "role_in_chain": "cause"},
           {"artefact": "cutover_runbook", "row_id": "E4#RB-010", "role_in_chain": "blocked step"}])


class StubOrchestrator:
    """Stands in for P2: the E4 chain claim for E4, a PartialAnswer for the unknown E9; re-plans are recorded."""

    def __init__(self):
        self.replans = []

    def orchestrate(self, question, repository, ledger):
        if question.entity_id == "E9":
            return OrchestratorResult(plan=Plan(run_id=question.run_id, steps=[]),
                                      partial=PartialAnswer(reason="unknown entity E9"))
        return OrchestratorResult(plan=Plan(run_id=question.run_id, steps=[]), claims=[E4_CHAIN_CLAIM])

    def replan(self, question, rejected_claim, verdict, repository, ledger):
        self.replans.append(rejected_claim.claim_id)
        return OrchestratorResult(plan=Plan(run_id=question.run_id, steps=[]), claims=[rejected_claim])


class StubCritic:
    """Passes every claim except the unsupportable one (the real critic must reject it: the row says FAIL, 91.2 %)."""

    def __init__(self):
        self.judged = []

    def __call__(self, prompt):
        claim = json.loads(prompt.split("<claim>")[1].split("</claim>")[0])
        self.judged.append(claim["claim_id"])
        passed = claim["statement"] != local.UNSUPPORTABLE_STATEMENT
        return json.dumps({"claim_id": claim["claim_id"], "pass": passed, "reason": "stub", "missing_evidence": []})


@pytest.fixture
def agents(monkeypatch):
    stubs = {"orchestrator": StubOrchestrator(), "critic": StubCritic()}
    monkeypatch.setattr(local, "make_orchestrator", lambda: stubs["orchestrator"])
    monkeypatch.setattr(local, "make_critic_agent", lambda: stubs["critic"])
    monkeypatch.setattr(local, "make_writer", lambda: lambda writer_input: WriterResult(
        answer=verbatim_answer(writer_input.passed_claims)))
    return stubs


def run_eval(case_id, repository):
    case = {case.input.id: case for case in eval_runner.load_cases()}[case_id]
    return eval_runner.run_case(case, repository, local.ask, get_settings().default_tenant_id)


@pytest.mark.parametrize("case_id", ["Q01", "Q07", "Q08", "Q09", "Q11"])
def test_the_runner_scores_these_cases_as_passed(agents, repository, case_id):
    result = run_eval(case_id, repository)
    assert result["status"] == eval_runner.Status.PASS, result["detail"]


def test_q08_strips_claim_1s_citations_so_the_critic_model_is_never_asked(agents, repository):
    response = run_eval("Q08", repository)["answer"]
    assert [rejected["claim_id"] for rejected in response["rejected"]] == ["claim-1"]
    assert agents["critic"].judged == [] and response["rejected"][0]["verdicts"][0]["pass"] is False


def test_q11_is_refused_before_anything_reaches_a_ledger(agents, repository, monkeypatch):
    ledgers = []
    original = local.ledger_for
    monkeypatch.setattr(local, "ledger_for", lambda inject: ledgers.append(original(inject)) or ledgers[-1])
    assert run_eval("Q11", repository)["answer"] == {"refused": True, "status_code": 403}
    assert all(not ledger.runs for ledger in ledgers)


def test_no_inject_means_the_plain_spine(agents, repository):
    response = run_eval("Q01", repository)["answer"]
    assert response["rejected"] == [] and len(response["answer"]["bullets"]) == 1


def test_an_unknown_inject_is_refused_and_the_real_agents_are_the_default():
    from agents.writer import write
    with pytest.raises(ValueError, match="unknown inject"):
        local.ledger_for("drop_the_critic")
    assert local.make_critic_agent() is None and local.make_writer() is write


def test_the_forced_claim_leaves_re_plans_of_other_claims_alone():
    stub = StubOrchestrator()
    orchestrator = local.WithUnsupportableClaim(stub)
    orchestrator.forced_claim_id = "claim-2"
    question = SimpleNamespace(run_id="run-1")
    assert orchestrator.replan(question, E4_CHAIN_CLAIM, {}, None, None).claims == [E4_CHAIN_CLAIM]
    assert stub.replans == ["claim-1"]


ONE_RETRY = 1   # the lead's ruling on Q09: at most 2 attempts per claim (max_claim_attempts = 2), so one retry


def test_q09_the_forced_claim_is_rejected_after_one_retry_with_two_verdicts(agents, repository):
    response = run_eval("Q09", repository)["answer"]
    forced = [rejected for rejected in response["rejected"] if rejected["statement"] == local.UNSUPPORTABLE_STATEMENT]
    assert len(forced) == 1
    assert len(forced[0]["verdicts"]) == get_settings().max_claim_attempts == ONE_RETRY + 1
    assert agents["orchestrator"].replans == [forced[0]["claim_id"]] * ONE_RETRY
```
- [ ] **Step 3: Run:** `uv run --locked pytest tests/infra/functions/test_local.py --no-cov 2>&1 | grep -E "^E  " | head -1`. Expected: `E   ImportError: cannot import name 'local' from 'infra.functions' (...)`.
- [ ] **Step 4: Implement.** Create `infra/functions/local.py`:
```python
"""The eval runner's local asker: the ask spine in-process with the real agents, plus the planted faults.

    uv run python -m evals.run --asker infra.functions.local.ask

ask() has the asker contract in evals/run.py: (case_input, scope, repository) -> the /ask response as a dict, or
{"refused": true, "status_code": 403} when the scope refuses the entity (nothing is written then). It runs
infra/functions/spine.py on a fresh in-memory ledger and applies the input's `inject` itself. Only this asker can: no fault
switch exists in the API, the state machine or config.py.

  strip_citations (Q08): the first claim (claim-1) reaches the ledger without its citations, on the first plan and
      on every re-plan, as if the analyst had sent it uncited. The critic's pre-check must reject it in code,
      without a model call, until the retry guard moves it to the rejected records.
  force_unsupportable_claim (Q09): the plan gains one more claim, which the row it cites contradicts, and its
      re-plan returns it unchanged. The real critic must reject it on each attempt: max_claim_attempts verdicts
      (2: one retry, the lead's ruling), then the rejected records.
"""
from collections.abc import Callable

from adapters.memory_ledger import InMemoryLedger
from infra.functions.spine import SpineAgents, run_spine
from infra.functions.steps import OrchestratorAgent, Writer, question_for, real_orchestrator, real_writer
from tools.api_schema import AskRequest
from tools.constants import CLAIM_ID_PREFIX
from tools.models import BlockerClaim, OrchestratorResult, OutOfScope, Scope
from tools.ports import ArtefactRepository

INJECT_STRIP_CITATIONS = "strip_citations"
INJECT_FORCE_UNSUPPORTABLE_CLAIM = "force_unsupportable_claim"
KNOWN_INJECTS = (INJECT_STRIP_CITATIONS, INJECT_FORCE_UNSUPPORTABLE_CLAIM)
FIRST_CLAIM_ID = f"{CLAIM_ID_PREFIX}1"   # the orchestrator numbers a plan's claims from claim-1 (P2)
REFUSED_STATUS_CODE = 403
# RC-C3-E4-customers says FAIL at 91.2 %: no reading of that row supports this statement.
UNSUPPORTABLE_STATEMENT = "E4 customer master reconciled at 100 % in cycle C3 and is ready for cutover"
UNSUPPORTABLE_CHAIN = [{"artefact": "reconciliation_results", "row_id": "RC-C3-E4-customers",
                        "role_in_chain": "evidence"}]


class CitationStrippingLedger(InMemoryLedger):
    """Q08: the ledger receives claim-1 without its citations, on the first plan and on every re-plan."""

    def put_claim(self, run_id: str, claim: dict) -> None:
        super().put_claim(run_id, self._stripped(claim["claim_id"], claim))

    def revise_claim(self, run_id: str, claim_id: str, claim: dict) -> None:
        super().revise_claim(run_id, claim_id, self._stripped(claim_id, claim))

    @staticmethod
    def _stripped(claim_id: str, claim: dict) -> dict:
        return {**claim, "chain": []} if claim_id == FIRST_CLAIM_ID else claim


class WithUnsupportableClaim:
    """Q09: the real orchestrator still plans and re-plans (and costs), but its plan gains the unsupportable claim
    under the next free claim ID, and a re-plan of that claim returns it unchanged."""

    def __init__(self, orchestrator: OrchestratorAgent):
        self.orchestrator = orchestrator
        self.forced_claim_id = None

    def orchestrate(self, question, repository, ledger) -> OrchestratorResult:
        result = self.orchestrator.orchestrate(question, repository, ledger)
        self.forced_claim_id = f"{CLAIM_ID_PREFIX}{len(result.claims) + 1}"
        forced = BlockerClaim(claim_id=self.forced_claim_id, statement=UNSUPPORTABLE_STATEMENT,
                              chain=UNSUPPORTABLE_CHAIN)
        return result.model_copy(update={"claims": [*result.claims, forced]})

    def replan(self, question, rejected_claim, verdict, repository, ledger) -> OrchestratorResult:
        result = self.orchestrator.replan(question, rejected_claim, verdict, repository, ledger)
        if rejected_claim.claim_id != self.forced_claim_id:
            return result
        return result.model_copy(update={"claims": [rejected_claim]})


# ---- the real agents (the tests replace these) -----------------------------------------------------------------
def make_orchestrator() -> OrchestratorAgent:
    return real_orchestrator()


def make_critic_agent() -> Callable | None:
    return None  # judge_claim builds the real Bedrock critic


def make_writer() -> Writer:
    return real_writer()


def ledger_for(inject: str | None) -> InMemoryLedger:
    if inject is not None and inject not in KNOWN_INJECTS:
        raise ValueError(f"unknown inject {inject!r}: expected one of {KNOWN_INJECTS}")
    return CitationStrippingLedger() if inject == INJECT_STRIP_CITATIONS else InMemoryLedger()


def ask(case_input, scope: Scope, repository: ArtefactRepository) -> dict:
    """The eval runner's asker (evals/run.py): one question, as its user, with its planted fault applied."""
    ledger = ledger_for(case_input.inject)
    orchestrator = make_orchestrator()
    if case_input.inject == INJECT_FORCE_UNSUPPORTABLE_CLAIM:
        orchestrator = WithUnsupportableClaim(orchestrator)
    agents = SpineAgents(orchestrator=orchestrator, writer=make_writer(), critic_agent=make_critic_agent())
    try:
        question = question_for(scope, AskRequest(entity_id=case_input.entity_id, question=case_input.question))
        response = run_spine(question, ledger=ledger, repository=repository, agents=agents)
    except OutOfScope:
        return {"refused": True, "status_code": REFUSED_STATUS_CODE}
    return response.model_dump(mode="json", by_alias=True)
```
- [ ] **Step 5: Run:** `uv run --locked pytest tests/infra/functions/test_local.py --no-cov 2>&1 | tail -1`. Expected: `11 passed in …s`.
- [ ] **Step 6: Guards, full suite and commit**
```bash
uv run --locked pytest tests/test_architecture.py tests/test_code_style.py tests/evals/test_run.py --no-cov 2>&1 | tail -1
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL|infra/functions/local"
git add infra/functions/local.py tests/infra/functions/test_local.py
git commit -m "Local eval asker: the ask spine in-process with Q08's stripped citations and Q09's unsupportable claim"
```
Expected: all passed; start + 11 (dry-run `325 passed`), `TOTAL ... 98%`, `infra/functions/local.py ... 98%` with only `make_orchestrator`'s body (the real P2 import) missed.

**Task done when:** `uv run --locked pytest tests/infra/functions/test_local.py --no-cov -k q09 2>&1 | tail -1 | cut -d, -f1` prints `2 passed` (the Q09 test and the runner's Q09 case; `-k` ignores case), and `uv run --locked pytest tests/infra/functions/test_local.py --no-cov -k scores 2>&1 | tail -1 | cut -d, -f1` prints `5 passed`.

### Task 2: The live eval run, docs, review and PR
- [ ] **Step 1: `HANDOFF.md`.** Under `## What's real`, add: `- The local eval asker (\`infra/functions/local.py\`): \`uv run python -m evals.run --asker infra.functions.local.ask\` asks the 14 questions through the real ask spine; it alone plants Q08's uncited claim and Q09's unsupportable claim (rejected after 2 attempts, 2 verdicts). No fault switch exists in the API or config.`
- [ ] **Step 2: Commit:** `git add HANDOFF.md && git commit -m "HANDOFF: the local eval asker and its planted faults"`; then `uv run --locked pytest tests/test_dependencies.py --no-cov 2>&1 | tail -1`. Expected: `4 passed`.
- [ ] **Step 3:** Review Focus by hand; results in `.superpowers/ledger-H6.md`.
- [ ] **Step 4: Verify in AWS (the live run).** Needs P1, P2, L5, H3 merged and Bedrock access:
```bash
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
uv run python -m evals.run --asker infra.functions.local.ask; echo "exit $?"
ls -t evals/results/ | head -1
```
Expected: one line per question (`Q01 PASS|FAIL …` with seconds), a summary line, `Results written to evals/results/run-<stamp>.json`, and an exit code (0 if no question failed, 1 otherwise; both are acceptable outcomes to record). In that file, Q09's answer has a rejected claim whose `verdicts` has 2 entries; Q08's rejected claim's verdicts have no `prompt` (code rejected it). Copy the summary line and the Q08, Q09, Q12 lines into the ledger file. Hand the results file to Abdul (A5a); do **not** commit it unless Abdul asks for that run.
- [ ] **Step 5:** `git diff develop --stat`. Expected: `HANDOFF.md`, `infra/functions/local.py`, `tests/infra/functions/test_local.py` (3 files).
- [ ] **Step 6: With Huvison's OK only:** push `feature/local-eval-asker`, PR to `develop` ("Local eval asker with the Q08 and Q09 faults (H6)"), body with the count, the Q09 rule (2 attempts, 2 verdicts), the live-run summary (or "pending AWS"), and the rulings. No attribution lines.
- [ ] **Step 7:** [[Build order]] row H6 → `in review (PR #nn)`, then `merged`. Tell Abdul (A5a and A5b can run `--asker infra.functions.local.ask`; Q09 shows 2 verdicts) and Patrick (P3 may call `infra.functions.local.ask` or `infra.functions.spine.run_spine`).

**Task done when:** the PR is open with the Q09 rule and the live-run summary (or "pending AWS") in its body.

## Done means
- [ ] **The asker exists and the runner scores it.** *Verify:* on `develop`, `uv run --locked pytest tests/infra/functions/test_local.py --no-cov 2>&1 | tail -1` prints `11 passed`.
- [ ] **Q09 ends with 2 verdicts.** *Verify:* `uv run --locked pytest tests/infra/functions/test_local.py --no-cov -k q09 2>&1 | tail -1 | cut -d, -f1` prints `2 passed`; in the live results file, Q09's forced claim's `verdicts` has length 2.
- [ ] **Q08 never reaches the critic model.** *Verify:* `uv run --locked pytest tests/infra/functions/test_local.py --no-cov -k q08 2>&1 | tail -1 | cut -d, -f1` prints `2 passed`.
- [ ] **No fault switch outside the asker.** *Verify:* `git grep -n "force_unsupportable_claim" -- infra/functions config.py` prints only `infra/functions/local.py` lines.
- [ ] **The live run is recorded.** *Verify:* the PR body (or a comment after P2/L5 merge) has the runner's summary line and the Q08, Q09, Q12 lines; Abdul has the results file.
- [ ] **Nothing broke.** *Verify:* full suite after merge: start + 11, `TOTAL` ≥ 98%.
- [ ] **Merged.** *Verify:* PR merged into `develop`; [[Build order]] row H6 `merged`.

## Never
- Add a fault switch to the API, the state machine, `config.py` or any agent.
- Change `max_claim_attempts`, `EVALS.md` or `evals/` in this item.
- Re-run the live evals until they pass without a code change, or hide a failure.
- Call Bedrock in a test.
- Push to `develop` or `main`, or add attribution lines.

Related: [[H6 - Local eval asker - spec]], [[Build order]], [[How to execute a plan]]
