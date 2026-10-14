---
tags: [build, plan, area/contracts]
id: C1
owner: Patrick
spec: "[[C1 - API and spine contracts - spec]]"
status: ready
updated: 2026-10-14
---
# C1: API and ask-spine contracts (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

> **Note (C2, 2026-10-14):** C1 is merged. [[C2 - Repo layout - spec]] updated the DEVOPS_HANDOVER entry points to `infra.functions.<module>.<function>`; the plan below is C1's original wording with its entry-point paths brought in line.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]]: the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[C1 - API and spine contracts - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger (see [[How to execute a plan]]).
3. [[Workstreams]] §3 (code already built) and §7 (rules), and [[Patrick - contracts, orchestrator, retriever]].
4. `01 Decisions/` (D-001, D-011, D-012, D-014, D-019) and [[Working with AI assistants]].

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Patrick.

**Goal:** the API and ask-spine contracts exist as tested code: `tools/api_schema.py` *(new)*, the step models in `tools/models.py`, the new `config.py` settings, exported JSON Schemas for the front end, and the DevOps handover. Every later build item quotes these names.

**Architecture:** all new code is in the core (`tools/`) plus `config.py` and one script. No AWS, no Strands. `tests/test_architecture.py` must keep passing.

**Tech stack:** Python 3.11, pydantic 2, pytest, uv. Run the tests with `uv run --locked pytest` from the repo root.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your own clone of it). Branch: `feature/api-and-spine-contracts` from an up-to-date `develop`.
- **Start state:** `uv run --locked pytest` → **160 passed**, `TOTAL` coverage 95%. If yours differs, stop: you are not on the expected `develop`.
- **Clean code (enforced by tests):**
  - no single-character names, anywhere (comprehensions and lambdas included);
  - no magic numbers or strings, so every limit and code is a named constant;
  - settings only in `config.py`; domain constants only in `tools/constants.py`.
- **The core (`tools/`) must not import** boto3, Strands, `adapters`, `config` or `os`.
- **Every model in `tools/api_schema.py` and every new step model** uses `ConfigDict(extra="forbid", frozen=True)`.
- **Don't change the output of `tools/metrics.py`.** The models describe it.
- **Commits:** small, one per task (the messages are given). No `Co-Authored-By` and no "Generated with" lines.
- **Never push to `develop` or `main`.** The PR is Task 7, after Patrick's OK.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. `SummaryResponse` must accept the CFO summary **and** an entity-lead summary in which `final_cutover` is `None`. A scope over live E1 only has no pending cutover.
2. `rows_response` must never return a row the scope can't see, including roster rows with `primary_entity = All` (visible) and rows with a blank entity (hidden). It reuses `queries.in_entity_view`, so don't reimplement it.
3. Verdicts inside `RejectedClaim` serialise with the key `pass` (alias). Handlers must dump with `by_alias=True`; the JSON Schema shows `pass`.
4. `AUTH_MODE` typos must fail loudly, never fall back to `none`.
5. The JSON Schema export is deterministic (sorted keys), so the drift test isn't flaky.

---

### Task 1: Step models and `Usage` in `tools/models.py`

**Files:**
- Modify: `tools/constants.py` (add 2 constants)
- Modify: `tools/models.py` (add the shared markup check, `EntityId`, the step models, `total_tokens`)
- Create: `tests/tools/test_step_models.py` *(new)*

**Produces:** `EntityId`, `Usage`, `total_tokens`, `Question`, `PlanStep`, `Plan`, `Lead`, `RetrieveRequest`, `Evidence`, `AnalystResult`, `PartialAnswer`, `OrchestratorResult`, `Bullet`, `Answer`, `WriterInput`, `WriterResult` (all in `tools.models`); `QUESTION_MAX_CHARACTERS`, `NOTE_MAX_CHARACTERS` (in `tools.constants`).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)"
git switch -c feature/api-and-spine-contracts
```
Expected: `160 passed`.

- [ ] **Step 2: Write the failing test.** Create `tests/tools/test_step_models.py`:
```python
"""The ask-spine step models (tools/models.py, D-021): valid examples pass, drift and bad values fail."""
import pytest
from pydantic import ValidationError

from config import DEFAULT_TENANT_ID
from tools.constants import QUESTION_MAX_CHARACTERS
from tools.models import (AnalystResult, Answer, Bullet, Citation, Evidence, Lead, OrchestratorResult, PartialAnswer,
                          Plan, PlanStep, Question, RetrieveRequest, Scope, Usage, WriterInput, WriterResult,
                          total_tokens)

CFO_SCOPE = Scope(user_id="user-cfo", role="cfo", tenant_id=DEFAULT_TENANT_ID, entity_ids=("*",))
RUN_ID = "run-0001"
SONNET = "eu.anthropic.claude-sonnet-4-6"
CLAIM = {"claim_id": "claim-1", "statement": "E4 is blocked by DEF-0412",
         "chain": [{"artefact": "defect_log", "row_id": "DEF-0412", "role_in_chain": "cause"}]}
CITATION = {"artefact": "defect_log", "row_id": "DEF-0412"}


def test_question_accepts_a_valid_request():
    question = Question(run_id=RUN_ID, scope=CFO_SCOPE, entity_id="E4", question="What is blocking cutover for E4?",
                        budget_usd=0.5, max_attempts=2)
    assert question.entity_id == "E4"


@pytest.mark.parametrize("bad_field", [{"entity_id": "E-4"}, {"question": ""},
                                       {"question": "x" * (QUESTION_MAX_CHARACTERS + 1)}, {"budget_usd": 0},
                                       {"max_attempts": 0}, {"unexpected": True}])
def test_question_rejects_bad_values_and_extra_fields(bad_field):
    valid = {"run_id": RUN_ID, "scope": CFO_SCOPE, "entity_id": "E4", "question": "What blocks E4?",
             "budget_usd": 0.5, "max_attempts": 2}
    with pytest.raises(ValidationError):
        Question(**{**valid, **bad_field})


def test_plan_steps_name_only_the_planned_agents():
    plan = Plan(run_id=RUN_ID, steps=[PlanStep(agent="retriever", tool_hint="failing_reconciliations",
                                               reason="find failing objects")])
    assert plan.steps[0].agent == "retriever"
    with pytest.raises(ValidationError):
        PlanStep(agent="critic", tool_hint="judge", reason="the orchestrator may not call the critic")


def test_retrieve_request_and_evidence():
    request = RetrieveRequest(scope=CFO_SCOPE, entity_id="E4", lead=Lead(kind="defect", id="DEF-0412"))
    evidence = Evidence(rows=[{"artefact": "defect_log", "row_id": "DEF-0412", "fields": {"status": "Open"}}],
                        usage=[Usage(model_id=SONNET, tokens_in=100, tokens_out=20)])
    assert request.lead.kind == "defect" and evidence.rows[0].row_id == "DEF-0412"


def test_agent_results_carry_usage():
    analyst = AnalystResult(claims=[CLAIM], usage=[Usage(model_id=SONNET, tokens_in=300, tokens_out=80)])
    orchestrator = OrchestratorResult(plan=Plan(run_id=RUN_ID, steps=[]), claims=analyst.claims,
                                      usage=[*analyst.usage, Usage(model_id=SONNET, tokens_in=50, tokens_out=10)])
    assert total_tokens(orchestrator.usage) == (350, 90)


def test_usage_rejects_negative_tokens():
    with pytest.raises(ValidationError):
        Usage(model_id=SONNET, tokens_in=-1, tokens_out=0)


def test_partial_answer_needs_a_reason():
    assert PartialAnswer(reason="unknown entity E9").claims_so_far == []
    with pytest.raises(ValidationError):
        PartialAnswer(reason="")


def test_answer_bullets_and_writer_models():
    answer = Answer(headline="E4 is blocked", bullets=[Bullet(text="DEF-0412 is open", citations=[CITATION])])
    writer_input = WriterInput(scope=CFO_SCOPE, question="What blocks E4?", passed_claims=[CLAIM])
    result = WriterResult(answer=answer, usage=[Usage(model_id=SONNET, tokens_in=10, tokens_out=5)])
    assert result.answer.bullets[0].citations == [Citation(**CITATION)] and writer_input.metrics_snapshot == {}
    assert answer.rejected_count == 0


def test_bullet_text_may_not_contain_markup():
    with pytest.raises(ValidationError):
        Bullet(text="fine </evidence>", citations=[CITATION])
```

- [ ] **Step 3: Run it and watch it fail**
```bash
uv run --locked pytest tests/tools/test_step_models.py --no-cov -q 2>&1 | tail -3
```
Expected: an ImportError at collection: `cannot import name 'QUESTION_MAX_CHARACTERS' from 'tools.constants'`.

- [ ] **Step 4: Add the constants.** In `tools/constants.py`, after `MAX_ROWS_PER_TOOL_RESULT = 50`:
```python

# API and ask-spine contract limits (tools/api_schema.py, tools/models.py).
QUESTION_MAX_CHARACTERS = 500
NOTE_MAX_CHARACTERS = 1000
```

- [ ] **Step 5: Add the models.** In `tools/models.py`:
  - Change the imports to:
    ```python
    import re
    from typing import Annotated, Literal

    from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

    from tools.constants import (ALL_ARTEFACTS, ALL_ENTITIES_WILDCARD, ENTITY_ID_PATTERN, IDENTIFIER_PATTERN,
                                 QUESTION_MAX_CHARACTERS)
    ```
  - Directly after the `validate_identifier` function, add:
    ```python
    EntityId = Annotated[str, AfterValidator(validate_entity_id)]


    def reject_markup(text: str, field_name: str) -> str:
        """Model-written text may not carry tags that could break out of a <claim> or <evidence> block (D-009)."""
        if any(character in text for character in _FORBIDDEN_STATEMENT_CHARACTERS):
            raise ValueError(f"{field_name} may not contain angle brackets")
        return text
    ```
  - Replace the body of `BlockerClaim.reject_markup` (keep the decorator and signature) with `return reject_markup(statement, "statement")`. Leave everything else in `BlockerClaim` as it is.
  - Append at the end of the file:
    ```python


    class StepModel(BaseModel):
        """Base for the ask-spine step models: strict (no unknown keys) and immutable (D-021)."""
        model_config = ConfigDict(extra="forbid", frozen=True)


    class Usage(StepModel):
        """Token usage of one model call. Every agent result carries a list of these, so cost can be measured."""
        model_id: str = Field(min_length=1)
        tokens_in: int = Field(ge=0)
        tokens_out: int = Field(ge=0)


    def total_tokens(usages: list[Usage]) -> tuple[int, int]:
        """Input and output tokens summed over a list of model calls."""
        return sum(usage.tokens_in for usage in usages), sum(usage.tokens_out for usage in usages)


    class Question(StepModel):
        """The ask spine's input: who asks, about which entity, within which budget."""
        run_id: str = Field(min_length=1)
        scope: Scope
        entity_id: EntityId
        question: str = Field(min_length=1, max_length=QUESTION_MAX_CHARACTERS)
        budget_usd: float = Field(gt=0)
        max_attempts: int = Field(ge=1)


    class PlanStep(StepModel):
        """One step the orchestrator plans. It may only call the retriever or the blocker-analyst (D-007)."""
        agent: Literal["retriever", "blocker_analyst"]
        tool_hint: str
        reason: str


    class Plan(StepModel):
        run_id: str = Field(min_length=1)
        steps: list[PlanStep]


    class Lead(StepModel):
        """What the retriever should look into for an entity."""
        kind: Literal["entity", "object", "defect", "runbook_step", "task"]
        id: str | None = None


    class RetrieveRequest(StepModel):
        scope: Scope
        entity_id: EntityId
        lead: Lead


    class Evidence(StepModel):
        """The retriever's output: rows with citations, never paraphrased."""
        rows: list[Row]
        usage: list[Usage] = []


    class AnalystResult(StepModel):
        """The blocker-analyst's output: claims (checked by tools/claims.py) and the model calls behind them."""
        claims: list[BlockerClaim]
        usage: list[Usage] = []


    class PartialAnswer(StepModel):
        """Returned instead of a guess: unknown or out-of-scope entity, or the budget is spent."""
        reason: str = Field(min_length=1)
        claims_so_far: list[BlockerClaim] = []


    class OrchestratorResult(StepModel):
        """The orchestrator's output, with its own and its sub-agents' model calls."""
        plan: Plan
        claims: list[BlockerClaim] = []
        partial: PartialAnswer | None = None
        usage: list[Usage] = []


    class Bullet(StepModel):
        text: str = Field(min_length=1)
        citations: list[Citation] = []

        @field_validator("text")
        @classmethod
        def reject_markup_in_text(cls, text: str) -> str:
            return reject_markup(text, "bullet text")


    class Answer(StepModel):
        """The writer's answer card. AskResponse.answer reuses it (tools/api_schema.py)."""
        headline: str = Field(min_length=1)
        bullets: list[Bullet] = []
        rejected_count: int = Field(default=0, ge=0)


    class WriterInput(StepModel):
        scope: Scope
        question: str = Field(min_length=1, max_length=QUESTION_MAX_CHARACTERS)
        passed_claims: list[BlockerClaim]
        metrics_snapshot: dict = {}


    class WriterResult(StepModel):
        answer: Answer
        usage: list[Usage] = []
    ```
  - `Row`, `Citation`, `Scope` and `BlockerClaim` are defined above these in the same file, so no forward references are needed.

- [ ] **Step 6: Run the new tests and the claim tests**
```bash
uv run --locked pytest tests/tools/test_step_models.py tests/tools/test_claims.py --no-cov -q 2>&1 | tail -2
```
Expected: `22 passed` (14 new: 8 functions, one of them parametrised ×6; plus the 8 existing claim tests).

- [ ] **Step 7: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add tools/constants.py tools/models.py tests/tools/test_step_models.py
git commit -m "Add the ask-spine step models with token usage on every agent result (D-021)"
```
Expected: `174 passed`, coverage not below 95%.

### Task 2: `queries.to_row`, one way to turn a loaded row into a `Row`

**Files:**
- Modify: `tools/queries.py`, `tools/agent_tools.py`
- Modify: `tests/tools/test_queries.py` (append one test)

**Produces:** `tools.queries.to_row(raw_row: dict) -> Row`. **Consumed by:** Task 3 (`rows_response`) and `tools/agent_tools.py`.

- [ ] **Step 1: Failing test.** Append to `tests/tools/test_queries.py`:
```python


def test_to_row_keeps_the_citation_and_the_public_columns_as_text():
    from tools.queries import to_row
    raw_row = {ROW_ARTEFACT_KEY: ArtefactName.DEFECT_LOG, "_row_id": "DEF-0412", "defect_id": "DEF-0412",
               "records_affected": 212}
    row = to_row(raw_row)
    assert (row.artefact, row.row_id, row.fields) == ("defect_log", "DEF-0412",
                                                      {"defect_id": "DEF-0412", "records_affected": "212"})
```
- [ ] **Step 2: Run it:** `uv run --locked pytest tests/tools/test_queries.py --no-cov -q 2>&1 | tail -2`. Expected: 1 failed (`ImportError: cannot import name 'to_row'`), 5 passed.
- [ ] **Step 3: Implement.** In `tools/queries.py`, change `from tools.models import Citation, Scope` to `from tools.models import Citation, Row, Scope`, and add after `public_fields`:
```python


def to_row(raw_row: dict) -> Row:
    """A loaded artefact row as a typed Row: its citation plus its own columns as text."""
    return Row(artefact=raw_row[ROW_ARTEFACT_KEY], row_id=raw_row[ROW_ID_KEY],
               fields={key: str(value) for key, value in public_fields(raw_row).items()})
```
- [ ] **Step 4: Use it in `tools/agent_tools.py`.** Replace the first statement of `_as_tool_rows` (the `rows = [Row(...) ... for raw_row in raw_rows]` comprehension) with `rows = [queries.to_row(raw_row) for raw_row in raw_rows]`, and remove `Row` from the `from tools.models import ...` line (it's no longer used there).
- [ ] **Step 5: Run:** `uv run --locked pytest tests/tools --no-cov -q 2>&1 | tail -2`. Expected: all passed, 0 failed.
- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add tools/queries.py tools/agent_tools.py tests/tools/test_queries.py
git commit -m "One way to turn a loaded row into a Row: queries.to_row, reused by the agent tools"
```
Expected: `175 passed`.

### Task 3: `tools/api_schema.py`, the API models and their builders

**Files:**
- Create: `tools/api_schema.py`, `tests/tools/test_api_schema.py` *(new)*

**Produces:**
- `SummaryResponse`, `EntityResponse`, `RowsResponse`, `AskRequest`, `AskResponse`, `RejectedClaim`, `TraceStep`, `PromptRef`, `PublishRequest`, `PublishResponse`, `ApproveRequest`, `ApproveResponse`, `ErrorResponse`, plus the nested models;
- `ERROR_UNAUTHORIZED`, `ERROR_FORBIDDEN`, `ERROR_NOT_FOUND`, `ERROR_STATUS_CODES`;
- `summary_response(repository, scope)`, `entity_response(repository, scope, entity_id)`, `rows_response(repository, scope, citations)`, `citations_from_query(cite)`;
- `API_MODELS`.

**Consumed by:** Linus (L1–L3 handlers), the eval runner, Task 5 (the export).

- [ ] **Step 1: Failing tests.** Create `tests/tools/test_api_schema.py`:
```python
"""The API contract (tools/api_schema.py, D-021) matches what the core really returns, and rejects drift."""
import pytest
from pydantic import ValidationError

from config import DEFAULT_TENANT_ID
from evals import run as eval_runner
from tools import metrics
from tools.api_schema import (API_MODELS, ERROR_STATUS_CODES, ApproveRequest, AskRequest, AskResponse,
                              ErrorResponse, RejectedClaim, SummaryResponse, citations_from_query, entity_response,
                              rows_response, summary_response)
from tools.models import Answer, Bullet, Citation, OutOfScope, Verdict

E4_BLOCKER = "DEF-0412"
E4_FAILING_RECONCILIATION = "RC-C3-E4-customers"
E4_CALENDAR_CLASH = ["CAL-004"]
E2_DEFECT = "DEF-0447"
UNKNOWN_DEFECT = "DEF-9999"
EXPECTED_RECORDS_RECONCILED = 18420
HTTP_STATUS_CODES_USED = {400, 401, 403, 404}


def test_summary_validates_for_the_cfo(repository, cfo_scope):
    summary = summary_response(repository, cfo_scope)
    assert summary.overall.records_reconciled == EXPECTED_RECORDS_RECONCILED
    assert summary.final_cutover is not None and summary.final_cutover.entity_id == "E4"


def test_summary_validates_for_an_entity_lead(repository, entity_four_lead_scope):
    assert [entity.entity_id for entity in summary_response(repository, entity_four_lead_scope).entities] == ["E4"]


def test_summary_without_a_pending_cutover_validates(repository):
    live_only_scope = entity_four_lead_scope_for("E1")
    assert summary_response(repository, live_only_scope).final_cutover is None


def entity_four_lead_scope_for(entity_id):
    from tools.models import Scope
    return Scope(user_id=f"user-{entity_id}-lead", role="entity_lead", tenant_id=DEFAULT_TENANT_ID,
                 entity_ids=(entity_id,))


def test_a_renamed_or_extra_summary_key_fails(repository, cfo_scope):
    raw_summary = metrics.portfolio_summary(repository, cfo_scope)
    renamed = {**raw_summary, "programme": raw_summary["programme_name"]}
    del renamed["programme_name"]
    with pytest.raises(ValidationError):
        SummaryResponse.model_validate(renamed)
    with pytest.raises(ValidationError):
        SummaryResponse.model_validate({**raw_summary, "unexpected": True})


def test_entity_response_for_e4(repository, cfo_scope):
    response = entity_response(repository, cfo_scope, "E4")
    assert response.entity.status == "Blocked"
    assert E4_BLOCKER in {blocker.reference for blocker in response.blockers}
    assert E4_FAILING_RECONCILIATION in {failed.recon_id for failed in response.failing_reconciliations}
    assert [conflict.window_id for conflict in response.calendar_conflicts] == E4_CALENDAR_CLASH


def test_entity_response_refuses_another_entity(repository, entity_four_lead_scope):
    with pytest.raises(OutOfScope):
        entity_response(repository, entity_four_lead_scope, "E2")


def test_entity_response_unknown_entity_is_a_key_error(repository, cfo_scope):
    with pytest.raises(KeyError):
        entity_response(repository, cfo_scope, "E9")


def test_rows_response_returns_only_visible_rows_and_lists_the_rest(repository, entity_four_lead_scope):
    citations = [Citation(artefact="defect_log", row_id=row_id) for row_id in (E4_BLOCKER, E2_DEFECT, UNKNOWN_DEFECT)]
    response = rows_response(repository, entity_four_lead_scope, citations)
    assert [row.row_id for row in response.rows] == [E4_BLOCKER]
    assert [citation.row_id for citation in response.missing] == [E2_DEFECT, UNKNOWN_DEFECT]


def test_citations_from_query_parses_and_rejects_malformed_input():
    assert citations_from_query("defect_log:DEF-0412,cutover_runbook:E4#RB-010") == [
        Citation(artefact="defect_log", row_id="DEF-0412"), Citation(artefact="cutover_runbook", row_id="E4#RB-010")]
    for malformed in ("defect_log", "not_an_artefact:X", ""):
        with pytest.raises(ValueError):
            citations_from_query(malformed)


@pytest.mark.parametrize("model, bad_body", [
    (AskRequest, {"entity_id": "E-4", "question": "What blocks E4?"}),
    (AskRequest, {"entity_id": "E4", "question": ""}),
    (AskRequest, {"entity_id": "E4", "question": "What blocks E4?", "scope": {"role": "cfo"}}),
    (ApproveRequest, {"run_id": "run-1", "decision": "maybe"}),
    (ApproveRequest, {"run_id": "", "decision": "approve"}),
])
def test_request_models_reject_bad_bodies(model, bad_body):
    with pytest.raises(ValidationError):
        model.model_validate(bad_body)


def test_ask_response_passes_the_eval_runners_answer_checks(repository):
    bullets = [Bullet(text="Customer master reconciles at 91.2 % against the 98 % target.",
                      citations=[Citation(artefact="reconciliation_results", row_id=E4_FAILING_RECONCILIATION)]),
               Bullet(text="212 customers are rejected for invalid tax IDs.",
                      citations=[Citation(artefact="defect_log", row_id=E4_BLOCKER)]),
               Bullet(text="Runbook step RB-010 needs that reconciliation to pass.",
                      citations=[Citation(artefact="cutover_runbook", row_id="E4#RB-010")])]
    rejected = RejectedClaim(claim_id="claim-9", statement="E4 is on track", reason="no evidence",
                             verdicts=[Verdict(claim_id="claim-9", passed=False, reason="no evidence")])
    response = AskResponse(run_id="run-1", answer=Answer(headline="E4 is blocked", bullets=bullets),
                           rejected=[rejected], cost_usd=0.05)
    body = response.model_dump(mode="json", by_alias=True)
    assert body["rejected"][0]["verdicts"][0]["pass"] is False
    case = {case.input.id: case for case in eval_runner.load_cases()}["Q01"]
    result = eval_runner.run_case(case, repository, lambda case_input, scope, repo: body, DEFAULT_TENANT_ID)
    assert result["status"] == eval_runner.Status.PASS, result["detail"]


def test_error_codes_map_to_http_status_codes():
    assert set(ERROR_STATUS_CODES.values()) == HTTP_STATUS_CODES_USED
    assert ErrorResponse(error="not_found", detail="no entity E9").error == "not_found"
    with pytest.raises(ValidationError):
        ErrorResponse(error="teapot", detail="")


def test_every_api_model_forbids_unknown_keys():
    assert {name: model.model_config.get("extra") for name, model in API_MODELS.items()} == {
        name: "forbid" for name in API_MODELS}
```
- [ ] **Step 2: Run it:** `uv run --locked pytest tests/tools/test_api_schema.py --no-cov -q 2>&1 | tail -2`. Expected: an ImportError at collection: `No module named 'tools.api_schema'`.
- [ ] **Step 3: Implement.** Create `tools/api_schema.py`:
```python
"""API contracts: the request and response models of the portal's six routes (D-021).

One definition shared by the API handlers (`infra/functions/api.py` *(new)*), the eval runner, the tests and the Angular front end, which gets
these as JSON Schema (scripts/export_api_schema.py). SummaryResponse mirrors tools/metrics.portfolio_summary key for
key, and the front end adopts these keys. Pure core: no AWS.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from tools import metrics, queries
from tools.agent_tools import ERROR_INVALID_INPUT, ERROR_OUT_OF_SCOPE
from tools.constants import NOTE_MAX_CHARACTERS, QUESTION_MAX_CHARACTERS, ROW_ARTEFACT_KEY, ROW_ID_KEY
from tools.models import Answer, Citation, EntityId, Row, Scope, Verdict
from tools.ports import ArtefactRepository

ERROR_UNAUTHORIZED = "unauthorized"
ERROR_FORBIDDEN = "forbidden"
ERROR_NOT_FOUND = "not_found"
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
ERROR_STATUS_CODES = {ERROR_INVALID_INPUT: HTTP_BAD_REQUEST, ERROR_UNAUTHORIZED: HTTP_UNAUTHORIZED,
                      ERROR_FORBIDDEN: HTTP_FORBIDDEN, ERROR_OUT_OF_SCOPE: HTTP_FORBIDDEN,
                      ERROR_NOT_FOUND: HTTP_NOT_FOUND}
CITE_LIST_SEPARATOR = ","
CITE_LABEL_SEPARATOR = ":"


class Contract(BaseModel):
    """Base for every API model: strict (a renamed key fails instead of vanishing) and immutable."""
    model_config = ConfigDict(extra="forbid", frozen=True)


# ---- GET /summary ---------------------------------------------------------------------------------------------
class OverallReconciled(Contract):
    records_reconciled: int
    records_in_scope: int
    pct: float


class CycleTotals(Contract):
    cycle_id: str
    records_matched: int
    records_sent: int
    pct: float
    evidence: list[Citation]


class PassRate(Contract):
    latest: CycleTotals | None
    previous: CycleTotals | None
    target_pct: float


class Blocker(Contract):
    reference: str
    entity_id: str
    blocker: str
    age_days: int
    owner_role: str
    evidence: list[Citation]


class OpenBlockers(Contract):
    count: int
    oldest_days: int
    blockers: list[Blocker]


class Cutover(Contract):
    entity_id: str
    cutover_forecast: str
    cutover_baseline: str
    days_remaining: int
    days_behind_plan: int
    live: bool
    evidence: list[Citation]


class RoleCapacity(Contract):
    role: str
    people_used: int
    people_planned: int
    pct: float
    evidence: list[Citation]


class Capacity(Contract):
    month: str
    people_used: int
    people_planned: int
    pct: float
    by_role: list[RoleCapacity]


class Reconciled(Contract):
    records_reconciled: int
    records_in_scope: int
    pct: float
    evidence: list[Citation]


class EntityRow(Contract):
    entity_id: str
    entity_name: str
    business_role: str
    source_tier: str
    source_description: str
    target_company_code: str
    reconciled: Reconciled
    cutover: Cutover
    open_blockers: int
    status: str


class SummaryResponse(Contract):
    as_of: str
    tenant_id: str
    programme_name: str
    target_platform: str
    currency: str
    overall: OverallReconciled
    pass_rate: PassRate
    open_blockers: OpenBlockers
    final_cutover: Cutover | None
    capacity: Capacity
    entities: list[EntityRow]


# ---- GET /entity/{id} -----------------------------------------------------------------------------------------
class FailedReconciliation(Contract):
    recon_id: str
    cycle_id: str
    entity_id: str
    object_id: str
    records_sent: str
    records_rejected: str
    records_matched: str
    match_rate_pct: str
    target_pct: str
    status: str
    evidence: list[Citation]


class CalendarConflict(Contract):
    window_id: str
    label: str
    type: str
    evidence: list[Citation]


class EntityResponse(Contract):
    entity: EntityRow
    blockers: list[Blocker]
    failing_reconciliations: list[FailedReconciliation]
    calendar_conflicts: list[CalendarConflict]


# ---- GET /rows ------------------------------------------------------------------------------------------------
class RowsResponse(Contract):
    rows: list[Row]
    missing: list[Citation]


# ---- POST /ask ------------------------------------------------------------------------------------------------
class AskRequest(Contract):
    entity_id: EntityId
    question: str = Field(min_length=1, max_length=QUESTION_MAX_CHARACTERS)


class PromptRef(Contract):
    agent: str
    version: str
    sha256: str


class TraceStep(Contract):
    step: str
    agent: str | None = None
    prompt: PromptRef | None = None


class RejectedClaim(Contract):
    claim_id: str
    statement: str
    reason: str
    verdicts: list[Verdict] = []


class AskResponse(Contract):
    run_id: str
    answer: Answer | None = None
    rejected: list[RejectedClaim] = []
    cost_usd: float = Field(ge=0)
    partial: bool = False
    partial_reason: str | None = None
    trace: list[TraceStep] = []


# ---- POST /publish, POST /approve ------------------------------------------------------------------------------
class PublishRequest(Contract):
    run_id: str = Field(min_length=1)


class PublishResponse(Contract):
    run_id: str
    execution_arn: str
    status: Literal["awaiting_approval"]


class ApproveRequest(Contract):
    run_id: str = Field(min_length=1)
    decision: Literal["approve", "send_back"]
    note: str = Field(default="", max_length=NOTE_MAX_CHARACTERS)


class ApproveResponse(Contract):
    run_id: str
    status: Literal["approved", "sent_back"]


# ---- errors ---------------------------------------------------------------------------------------------------
class ErrorResponse(Contract):
    error: Literal[ERROR_INVALID_INPUT, ERROR_UNAUTHORIZED, ERROR_FORBIDDEN, ERROR_OUT_OF_SCOPE, ERROR_NOT_FOUND]
    detail: str


API_MODELS: dict[str, type[Contract]] = {
    "summary": SummaryResponse, "entity": EntityResponse, "rows": RowsResponse,
    "ask_request": AskRequest, "ask_response": AskResponse,
    "publish_request": PublishRequest, "publish_response": PublishResponse,
    "approve_request": ApproveRequest, "approve_response": ApproveResponse,
    "error": ErrorResponse,
}


# ---- builders shared by the handlers and the tests -------------------------------------------------------------
def summary_response(repository: ArtefactRepository, scope: Scope) -> SummaryResponse:
    """GET /summary: the one screen, limited to the scope."""
    return SummaryResponse.model_validate(metrics.portfolio_summary(repository, scope))


def entity_response(repository: ArtefactRepository, scope: Scope, entity_id: str) -> EntityResponse:
    """GET /entity/{id}. Raises OutOfScope (403), ValueError for a malformed ID (400), KeyError if unknown (404)."""
    scope.require(entity_id)
    entity = next((row for row in metrics.portfolio_summary(repository, scope)["entities"]
                   if row["entity_id"] == entity_id), None)
    if entity is None:
        raise KeyError(f"unknown entity: {entity_id}")
    return EntityResponse.model_validate({
        "entity": entity,
        "blockers": metrics.open_blockers(repository, entity_id),
        "failing_reconciliations": metrics.failing_reconciliations(repository, entity_id),
        "calendar_conflicts": metrics.cutover_calendar_conflicts(repository, entity_id),
    })


def rows_response(repository: ArtefactRepository, scope: Scope, citations: list[Citation]) -> RowsResponse:
    """GET /rows: the cited rows the scope may see; everything else (unknown or not visible) goes to `missing`."""
    unique_citations = list(dict.fromkeys(citations))
    visible = [row for row in queries.rows_by_citation(repository, unique_citations)
               if queries.in_entity_view(row, scope)]
    visible_keys = {(row[ROW_ARTEFACT_KEY], row[ROW_ID_KEY]) for row in visible}
    return RowsResponse(rows=[queries.to_row(row) for row in visible],
                        missing=[citation for citation in unique_citations
                                 if (citation.artefact, citation.row_id) not in visible_keys])


def citations_from_query(cite: str) -> list[Citation]:
    """Parse `/rows?cite=artefact:row_id,artefact:row_id`. Raises ValueError (pydantic's included) when malformed."""
    labels = [label for label in cite.split(CITE_LIST_SEPARATOR) if label]
    if not labels:
        raise ValueError("cite needs at least one artefact:row_id")
    citations = []
    for label in labels:
        artefact, separator, row_id = label.partition(CITE_LABEL_SEPARATOR)
        if not separator:
            raise ValueError(f"not artefact:row_id: {label!r}")
        citations.append(Citation(artefact=artefact, row_id=row_id))
    return citations
```
- [ ] **Step 4: Run:** `uv run --locked pytest tests/tools/test_api_schema.py --no-cov -q 2>&1 | tail -2`. Expected: `17 passed`.
  - If `test_summary_validates_*` fails with a ValidationError, the model doesn't match `portfolio_summary`. Fix the **model**, never `metrics.py`, and ledger it.
- [ ] **Step 5: Architecture and style guards, then commit**
```bash
uv run --locked pytest tests/test_architecture.py tests/test_code_style.py --no-cov -q 2>&1 | tail -1
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add tools/api_schema.py tests/tools/test_api_schema.py
git commit -m "API contract in code: response and request models for the six routes, tested against the real KPIs"
```
Expected: the guards pass; `192 passed`; coverage not below 95%.

### Task 4: The new settings in `config.py`

**Files:**
- Modify: `config.py`
- Create: `tests/test_config.py` *(new)*

**Produces:** the `Settings` fields `auth_mode`, `rejected_table`, `artefacts_bucket`, `status_pack_prefix`, `ask_state_machine_arn`, `publish_state_machine_arn`, `user_pool_id` and `user_pool_client_id`; `AUTH_MODE_NONE`, `AUTH_MODE_COGNITO` and `AUTH_MODES` in `config`.

- [ ] **Step 1: Failing tests.** Create `tests/test_config.py`:
```python
"""Deployment settings (config.py): the new D-021 settings have defaults, take environment overrides, and refuse typos."""
import pytest

import config

NEW_SETTING_DEFAULTS = {
    "auth_mode": "none", "rejected_table": "erp-portal-rejected-records", "artefacts_bucket": None,
    "status_pack_prefix": "status-packs/", "ask_state_machine_arn": None, "publish_state_machine_arn": None,
    "user_pool_id": None, "user_pool_client_id": None,
}
ENVIRONMENT_VARIABLES = {
    "auth_mode": ("AUTH_MODE", "cognito"), "rejected_table": ("REJECTED_TABLE", "demo2-rejected"),
    "artefacts_bucket": ("ARTEFACTS_BUCKET", "demo2-artefacts"),
    "status_pack_prefix": ("STATUS_PACK_PREFIX", "packs/"),
    "ask_state_machine_arn": ("ASK_STATE_MACHINE_ARN", "arn:aws:states:eu-west-1:000000000000:stateMachine:ask"),
    "publish_state_machine_arn": ("PUBLISH_STATE_MACHINE_ARN",
                                  "arn:aws:states:eu-west-1:000000000000:stateMachine:publish"),
    "user_pool_id": ("USER_POOL_ID", "eu-west-1_example"), "user_pool_client_id": ("USER_POOL_CLIENT_ID", "client"),
}


@pytest.fixture(autouse=True)
def fresh_settings(monkeypatch):
    for variable, _value in ENVIRONMENT_VARIABLES.values():
        monkeypatch.delenv(variable, raising=False)
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


def test_new_settings_have_defaults():
    settings = config.get_settings()
    assert {field: getattr(settings, field) for field in NEW_SETTING_DEFAULTS} == NEW_SETTING_DEFAULTS


@pytest.mark.parametrize("field", sorted(ENVIRONMENT_VARIABLES))
def test_each_new_setting_takes_its_environment_variable(monkeypatch, field):
    variable, value = ENVIRONMENT_VARIABLES[field]
    monkeypatch.setenv(variable, value)
    assert getattr(config.get_settings(), field) == value


def test_an_unknown_auth_mode_is_refused(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "cognitoo")
    with pytest.raises(ValueError, match="AUTH_MODE"):
        config.get_settings()
```
- [ ] **Step 2: Run it:** `uv run --locked pytest tests/test_config.py --no-cov -q 2>&1 | tail -2`. Expected: failures with `AttributeError: 'Settings' object has no attribute 'auth_mode'`.
- [ ] **Step 3: Implement** in `config.py`:
  - After `DEFAULT_RUN_BUDGET_USD = 0.50` add:
    ```python
    AUTH_MODE_NONE = "none"                           # demo user with CFO scope; local runs and the Cognito fallback
    AUTH_MODE_COGNITO = "cognito"                     # scope from the Cognito ID token (the target slice, D-015)
    AUTH_MODES = (AUTH_MODE_NONE, AUTH_MODE_COGNITO)
    DEFAULT_AUTH_MODE = AUTH_MODE_NONE
    DEFAULT_REJECTED_TABLE = "erp-portal-rejected-records"
    DEFAULT_STATUS_PACK_PREFIX = "status-packs/"
    ```
  - Add to the `Settings` dataclass, after `run_budget_usd: float`:
    ```python
        auth_mode: str
        rejected_table: str
        artefacts_bucket: str | None
        status_pack_prefix: str
        ask_state_machine_arn: str | None
        publish_state_machine_arn: str | None
        user_pool_id: str | None
        user_pool_client_id: str | None
    ```
  - Add after `_env`:
    ```python
    def _auth_mode() -> str:
        auth_mode = _env("AUTH_MODE", DEFAULT_AUTH_MODE)
        if auth_mode not in AUTH_MODES:
            raise ValueError(f"AUTH_MODE must be one of {AUTH_MODES}, not {auth_mode!r}")
        return auth_mode
    ```
  - Add to the `Settings(...)` call in `get_settings()`, after `run_budget_usd=...`:
    ```python
            auth_mode=_auth_mode(),
            rejected_table=_env("REJECTED_TABLE", DEFAULT_REJECTED_TABLE),
            artefacts_bucket=os.environ.get("ARTEFACTS_BUCKET"),
            status_pack_prefix=_env("STATUS_PACK_PREFIX", DEFAULT_STATUS_PACK_PREFIX),
            ask_state_machine_arn=os.environ.get("ASK_STATE_MACHINE_ARN"),
            publish_state_machine_arn=os.environ.get("PUBLISH_STATE_MACHINE_ARN"),
            user_pool_id=os.environ.get("USER_POOL_ID"),
            user_pool_client_id=os.environ.get("USER_POOL_CLIENT_ID"),
    ```
- [ ] **Step 4: Run:** `uv run --locked pytest tests/test_config.py --no-cov -q 2>&1 | tail -2`. Expected: `10 passed`.
- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add config.py tests/test_config.py
git commit -m "Settings for auth mode, rejected records, status packs, state machines and Cognito (D-021)"
```
Expected: `202 passed`.

### Task 5: Export the API contract as JSON Schema for the front end

**Files:**
- Create: `scripts/export_api_schema.py` *(new)*, `tests/scripts/test_export_api_schema.py` *(new)*
- Generated and committed: `web/src/app/core/api/schema/*.schema.json`, `web/src/app/core/api/schema/README.md` *(new)*

- [ ] **Step 1: Failing tests.** Create `tests/scripts/test_export_api_schema.py` (the folder is new; no `__init__.py`):
```python
"""scripts/export_api_schema.py writes one JSON Schema per API model, and the committed schemas are current."""
import subprocess
import sys

from config import REPO_ROOT
from tools.api_schema import API_MODELS

EXPORT_SCRIPT = REPO_ROOT / "scripts" / "export_api_schema.py"
COMMITTED_SCHEMA_FOLDER = REPO_ROOT / "web" / "src" / "app" / "core" / "api" / "schema"
SCHEMA_SUFFIX = ".schema.json"
STALE_HINT = "stale schema: run `uv run python scripts/export_api_schema.py` and commit the result"


def export_to(output_folder):
    subprocess.run([sys.executable, str(EXPORT_SCRIPT), "--out", str(output_folder)], cwd=REPO_ROOT, check=True,
                   capture_output=True, text=True)


def test_export_writes_one_schema_per_api_model(tmp_path):
    export_to(tmp_path)
    assert sorted(schema_file.name for schema_file in tmp_path.glob(f"*{SCHEMA_SUFFIX}")) == sorted(
        f"{name}{SCHEMA_SUFFIX}" for name in API_MODELS)


def test_committed_schemas_match_the_models(tmp_path):
    export_to(tmp_path)
    for fresh_file in tmp_path.iterdir():
        committed_file = COMMITTED_SCHEMA_FOLDER / fresh_file.name
        assert committed_file.exists() and committed_file.read_text(encoding="utf-8") == fresh_file.read_text(
            encoding="utf-8"), STALE_HINT
```
- [ ] **Step 2: Run it:** `uv run --locked pytest tests/scripts/test_export_api_schema.py --no-cov -q 2>&1 | tail -2`. Expected: 2 failed (`CalledProcessError`: the script doesn't exist).
- [ ] **Step 3: Implement.** Create `scripts/export_api_schema.py`:
```python
"""Write the API contract (tools/api_schema.py) as JSON Schema files for the Angular front end (D-021).

Usage, from the repo root:
  uv run python scripts/export_api_schema.py                  # writes web/src/app/core/api/schema/
  uv run python scripts/export_api_schema.py --out <folder>   # somewhere else (the tests do this)
Re-run it after changing a model in tools/api_schema.py. A test fails while the committed files are stale.
"""
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.api_schema import API_MODELS  # noqa: E402

DEFAULT_OUTPUT_FOLDER = REPO_ROOT / "web" / "src" / "app" / "core" / "api" / "schema"
SCHEMA_SUFFIX = ".schema.json"
JSON_INDENT = 2
README_FILE_NAME = "README.md"
README_TEXT = ("# Generated API schemas\n\n"
               "Generated from `tools/api_schema.py` by `uv run python scripts/export_api_schema.py` (D-021). "
               "Don't edit these files by hand: change the models, re-run the script and commit the result.\n")
EXIT_OK = 0


def schema_texts() -> dict[str, str]:
    """File name → JSON Schema text, one per API model, with sorted keys so the output never changes by itself."""
    return {f"{name}{SCHEMA_SUFFIX}": json.dumps(model.model_json_schema(), indent=JSON_INDENT, sort_keys=True) + "\n"
            for name, model in API_MODELS.items()}


def export(output_folder: Path) -> list[Path]:
    output_folder.mkdir(parents=True, exist_ok=True)
    written = []
    for file_name, text in {**schema_texts(), README_FILE_NAME: README_TEXT}.items():
        output_path = output_folder / file_name
        output_path.write_text(text, encoding="utf-8")
        written.append(output_path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the API contract as JSON Schema.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_FOLDER, help="folder to write the schemas to")
    for output_path in export(parser.parse_args().out):
        print(output_path)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
```
- [ ] **Step 4: Generate the committed schemas and run the tests**
```bash
uv run python scripts/export_api_schema.py | wc -l
uv run --locked pytest tests/scripts/test_export_api_schema.py --no-cov -q 2>&1 | tail -1
```
Expected: `11` (10 schemas + README); `2 passed`.
- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add scripts/export_api_schema.py tests/scripts/test_export_api_schema.py web/src/app/core/api/schema
git commit -m "Export the API contract as JSON Schema for the front end, with a test that the committed copy is current"
```
Expected: `204 passed`. (`tests/test_dependencies.py` checks that the script's docstring uses `uv run python scripts/...`.)

### Task 6: The DevOps handover, TEAM_PLAN §3, ARCHITECTURE §3c and D-021

**Files:**
- Create: `docs/DEVOPS_HANDOVER.md` *(new)*
- Modify: `docs/TEAM_PLAN.md` (§3 API table), `ARCHITECTURE.md` (§3c), `DECISIONS.md`

- [ ] **Step 1: `docs/DEVOPS_HANDOVER.md`.** It opens: "What each Lambda and runtime is, the environment it reads (all through `config.get_settings()`), the IAM it needs, and how it is bundled. Owner: Patrick (contracts); entry points marked *planned* are built by the named workstream. DevOps (Michael, Yaw) builds the stacks from this file." Then:
  - **One table**, with columns *Function · Entry point · Trigger · Environment · IAM (actions on resources) · Owner*, one row each for:
    - `summary`, `entity`, `rows`: `infra.functions.api.summary|entity|rows` *(planned, Linus)*, API GET routes. Environment: `ARTEFACT_BACKEND`, `ARTEFACTS_URI` (`s3://<bucket>/artefacts/`), `AUTH_MODE`, `DEFAULT_TENANT_ID`. IAM: `s3:GetObject` on `artefacts/*`.
    - `ask`: `infra.functions.api.ask` *(planned, Linus)*. Environment: the above plus `ASK_STATE_MACHINE_ARN`. IAM: `s3:GetObject` on `artefacts/*`, `states:StartSyncExecution` on the ask machine.
    - `publish`, `approve`: `infra.functions.api.publish|approve` *(planned, Linus)*. Environment: `PUBLISH_STATE_MACHINE_ARN`, `LEDGER_TABLE`. IAM: `states:StartExecution`, `states:SendTaskSuccess`, `states:SendTaskFailure` on the publish machine; DynamoDB `GetItem` on the ledger.
    - `check_budget`, `store_claims`, `retry_decision`, `record_rejection`: `infra.functions.steps.<name>` *(planned, Huvison)*, ask-machine states. Environment: `LEDGER_BACKEND=dynamo`, `LEDGER_TABLE`, `REJECTED_TABLE`, `RUN_BUDGET_USD`, `MAX_CLAIM_ATTEMPTS`. IAM: DynamoDB `GetItem`, `PutItem`, `UpdateItem`, `Query` on the ledger and rejected tables.
    - `run_orchestrator`, `judge_claim`, `write_answer`: `infra.functions.steps.<name>` *(planned, Huvison)*, ask-machine states that call agents. Environment: the ledger settings plus the model IDs (`REASONING_MODEL_ID` / `*_MODEL_ID`), `GUARDRAIL_ID`, `GUARDRAIL_VERSION`, `ARTEFACTS_URI`. IAM: the ledger actions; `bedrock:InvokeModel` on the **specific** inference-profile ARNs `arn:aws:bedrock:eu-west-1:796973512193:inference-profile/eu.anthropic.claude-sonnet-4-6` and `.../eu.amazon.nova-lite-v1:0`, plus the foundation-model ARNs those EU profiles route to; `bedrock:ApplyGuardrail` on the Guardrail ARN; `s3:GetObject` on `artefacts/*`.
    - `start_publish`, `decide`, status-pack writer: `infra.functions.publish.<name>` *(planned, Huvison)*, publish-machine states. Environment: `LEDGER_TABLE`, `ARTEFACTS_BUCKET`, `STATUS_PACK_PREFIX`. IAM: DynamoDB on the ledger; `s3:PutObject` **only** on `status-packs/*`.
    - AgentCore runtime + shim: *(planned, Yaw / Patrick)*. Same environment and Bedrock IAM as `run_orchestrator`.
  - **A "Bundling" section:** `uv export --no-dev --format requirements-txt --no-hashes > build/requirements.txt`; copy `tools/`, `adapters/`, `agents/` (including `agents/prompts/*.txt` and `agents/prompts/prompts.lock`; `load_prompt` refuses to run without them), `config.py` and the handler package; Python 3.11.
  - **A "Rules" section:** `eu-west-1` only; `eu.*` models only; no `*` in actions or resources; one role per function.
- [ ] **Step 2: `docs/TEAM_PLAN.md` §3 API table.** (`web/src/app/core/api/schema/` *(new)* is created in Task 5.) Replace the table (the rows from `| GET /summary |` to `| POST /approve |`) with:
```markdown
| Route | Request | Response (`tools/api_schema.py`, JSON Schema in `web/src/app/core/api/schema/`) |
|---|---|---|
| `GET /summary` | scope from token | `SummaryResponse`: exactly `metrics.portfolio_summary()`, scope-filtered |
| `GET /entity/{id}` | scope | `EntityResponse`: the entity row + its blockers, failing reconciliations and calendar conflicts |
| `GET /rows?cite=artefact:row_id,...` | scope | `RowsResponse {rows, missing}`: rows the scope may see; everything else is listed in `missing` |
| `POST /ask` | `AskRequest {entity_id, question}` | `AskResponse {run_id, answer, rejected[{claim_id, statement, reason, verdicts}], cost_usd, partial, partial_reason, trace}`; out of scope → 403 |
| `POST /publish` | `PublishRequest {run_id}` | `PublishResponse {run_id, execution_arn, status: "awaiting_approval"}` |
| `POST /approve` | `ApproveRequest {run_id, decision: "approve"\|"send_back", note}` | `ApproveResponse {run_id, status: "approved"\|"sent_back"}` |
| any error | | `ErrorResponse {error, detail}`: `invalid_input` 400, `unauthorized` 401, `forbidden`/`out_of_scope` 403, `not_found` 404 |

Step models between the ask-spine states (`Question`, `Plan`, `RetrieveRequest`, `Evidence`, `AnalystResult`, `OrchestratorResult`, `PartialAnswer`, `WriterInput`, `WriterResult`, `Answer`, `Usage`) are in `tools/models.py`. Every agent result carries `usage`. Settings and IAM per function: `docs/DEVOPS_HANDOVER.md`.
```
- [ ] **Step 3: `ARCHITECTURE.md` §3c.** After the paragraph that starts `**Settings and constants.**`, add: `**Contracts.** The API's request and response models are in `tools/api_schema.py` (exported as JSON Schema for the front end by `uv run python scripts/export_api_schema.py`); the ask-spine step models, with token usage on every agent result, are in `tools/models.py` (D-021).`
- [ ] **Step 4: `DECISIONS.md`.** Append:
```markdown
### D-021 · API and ask-spine contracts live in code, in the core
- **What:** The six routes' request and response models, plus the error body, are pydantic models in `tools/api_schema.py`; `SummaryResponse` mirrors `metrics.portfolio_summary` exactly. The ask-spine step models (`Question`, `Plan`, `RetrieveRequest`, `Evidence`, `AnalystResult`, `OrchestratorResult`, `PartialAnswer`, `WriterInput`, `WriterResult`, `Answer`, `Usage`) are in `tools/models.py`, and every agent result carries `usage` for cost. All are strict (`extra="forbid"`). `/approve` takes `run_id`. JSON Schemas for the front end are exported by `scripts/export_api_schema.py`, and a test keeps the committed copy current. New settings (`AUTH_MODE` and others) are in `config.py`; per-function environment and IAM are in `docs/DEVOPS_HANDOVER.md`.
- **Why:** Eight people build against these shapes in parallel. In prose they drift; in code, tests catch a renamed key the day it happens, and every later plan quotes names that exist. Usage on every agent result is the only way to measure cost per run, because the model calls happen in different workstreams.
- **Rejected:** Models in the handlers' module (Linus's file, not shared). Hand-written OpenAPI (a second source of truth). Reshaping the summary to the old front-end types. Lenient models (drift goes unnoticed). Keying approvals by `execution_arn` in a `run_id`-keyed ledger.
```
- [ ] **Step 5: Run the doc guards and the full suite, then commit**
```bash
uv run --locked pytest tests/test_dependencies.py tests/test_code_style.py --no-cov -q 2>&1 | tail -1
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add docs/DEVOPS_HANDOVER.md docs/TEAM_PLAN.md ARCHITECTURE.md DECISIONS.md
git commit -m "Document the contracts: DevOps handover, TEAM_PLAN API table, ARCHITECTURE and D-021"
```
Expected: the guards pass; `204 passed`; coverage not below 95%.

### Task 7: Review, then PR (after Patrick's OK)
- [ ] **Step 1:** Check each line of the Review Focus by hand, and note the result in the ledger.
- [ ] **Step 2:** Self-check: `git diff develop --stat` touches only the files named in Tasks 1–6.
- [ ] **Step 3: With Patrick's OK only:**
  - push: `git push -u origin feature/api-and-spine-contracts`;
  - open the PR to `develop`, titled "API and ask-spine contracts in code (D-021)". The body lists what each workstream can now import, and the test count;
  - no attribution lines.
- [ ] **Step 4: Tell the team** (Patrick posts it):
  - the contracts are on `develop`;
  - Mildred: the JSON Schemas are in `web/src/app/core/api/schema/`, `ARTEFACT_NAMES` needs all 14, and `rejected[]` is now `{claim_id, statement, reason, verdicts}`;
  - DevOps: `docs/DEVOPS_HANDOVER.md`.

## Done checklist
- [ ] `tools/api_schema.py`, the step models, the settings, the export script, the committed schemas and the handover exist, all tested.
- [ ] `uv run --locked pytest`: all passed, coverage ≥ 95%, architecture and style guards green.
- [ ] TEAM_PLAN §3, ARCHITECTURE §3c and D-021 updated.
- [ ] PR open to `develop` (after OK); the team told.

## Never
- Change `tools/metrics.py` output to fit a model.
- Loosen `extra="forbid"` to make a test pass.
- Import `config` or `os` in `tools/`.
- Push to `develop` or `main`.
- Add attribution lines.

Related: [[C1 - API and spine contracts - spec]], [[Build order]], [[How to execute a plan]]
