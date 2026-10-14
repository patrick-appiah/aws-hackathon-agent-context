---
tags: [build, plan, area/agents]
id: P3
owner: Patrick
spec: "[[P3 - Local ask runner - spec]]"
status: ready
updated: 2026-10-14
---
# P3: `scripts/ask.py`, the local ask runner (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]]: the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[P3 - Local ask runner - spec]]: **the authority**. Where this plan and the spec disagree, the spec wins; record the conflict in the ledger.
3. [[Workstreams]] §2 and §7, [[Patrick - contracts, orchestrator, retriever]] §4–§5, [[Huvison - trust and flow]] §3 and §7.
4. [[H2b - Agent states, local spine and Lambda handlers - spec]] (`flow.spine.run_spine`, `SpineAgents`), [[L1 - Scope from the token and the summary handler - spec]] (`auth.scope.demo_scope`), [[P2 - Orchestrator agent - spec]] and [[C1 - API and spine contracts - spec]] §3 (`AskResponse`).
5. `01 Decisions/`: [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]]; `05 Workflow/`: [[Dev loop]], [[Deploy and demo checks]], [[Working with AI assistants]].

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Patrick.

**Goal:** `uv run python scripts/ask.py --entity E4 "What is blocking cutover?"` builds the demo CFO's `Question`, runs Huvison's `flow.spine.run_spine` on a fresh `InMemoryLedger` and the committed CSVs, and prints the cited answer, the could-not-verify claims, the trace and the cost.

**Architecture:** the script holds no spine logic. `main` parses the command line, builds the `Question` (validated before anything runs), calls `run_spine(question, ledger=InMemoryLedger(), repository=CsvRepository(DEFAULT_ARTEFACTS_URI))` and prints `render(response)` or the JSON. The state order, the retry guard and the partial answers are H2b's (`flow/spine.py` *(new)*). `local_scope` is the demo CFO: L1's `auth.scope.demo_scope(settings)` once L1 is merged, until then the same CFO scope built here. Tests monkeypatch `run_spine`, or drive the real one with stub agents: no Bedrock, no AWS.

**Tech stack:** Python 3.11, pydantic 2, argparse, pytest, uv. Run the tests with `uv run --locked pytest` from the repo root.

**Dry-run status of this plan:** every step was run on C1 as reviewed (`94970fd`) + P1 + H1 + H5 + H3 + H2a + H2b (Huvison's dry-run code) + P2. The L1 variant of `local_scope` (Task 2, Step 4) was run against a stand-in `auth/scope.py` *(new)* with L1's `demo_scope`. The counts below are **deltas** from your start count; the failure messages are the real ones. The Q01 live run (Task 3, Step 1) needs Bedrock: "verify in AWS".

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (or your clone of `Amali-Tech/cloud-9-hackathon`). Branch: **`feature/local-ask-runner`** from an up-to-date `develop` **after H2b is merged** (and so C1, H1, H2a, H3, H5).
- **Start state:** `uv run --locked pytest` → **`N passed`** (and `1 skipped` if P2 is merged and L5 isn't), where `N` is whatever `develop` gives after H2b; `TOTAL` coverage ≥ 96%. Write `N` in the ledger. Every count below is `N + k`.
- **Region and models:** `eu-west-1` only; `eu.*` inference profiles only, from `config.get_settings()`. Synthetic data only. No secrets anywhere.
- **Clean code (enforced by tests):** settings only in `config.py`; domain constants only in `tools/constants.py`; descriptive names; **no single-character names**; no magic numbers. Scripts run as `uv run python scripts/...` in every doc and docstring (`tests/test_dependencies.py`).
- **No spine logic in the script.** The state order, the retry (the ledger's `retry_decision`) and the partial answers belong to `flow.spine.run_spine` (H2b). The script never loops over claims. When H6 (`flow/local.py` *(new)*) lands, the script **keeps calling `run_spine`**: `flow/local.py` is the eval asker's, not this runner's.
- **The scope is the demo user, built in code** (`local_scope`), never from the command line. `AUTH_MODE` defaults to `cognito` since C1's review; the runner never reads it: `local_scope` builds the demo user itself, or through L1's `demo_scope`, which doesn't check `AUTH_MODE` either. So no `AUTH_MODE=none` is needed in your shell.
- **`AskResponse` carries `partial_reason` exactly when `partial` is true** (C1 validator): never set one without the other, in code or in tests.
- **No Bedrock or AWS calls in tests.** The live run is manual.
- **Never weaken a security rule** (scope gate, create-once ledger, fail-closed critic, escaping) to pass a test.
- **Tests in `tests/`, mirroring the code** (`tests/scripts/test_ask.py`). **No layout or "meta" guard tests.**
- **Stay in your folders:** `scripts/ask.py`, `tests/scripts/test_ask.py`, one line in `HANDOFF.md`. Don't touch `flow/` (Huvison) or `auth/` (Linus).
- **Commits:** one per task, with the messages given. No `Co-Authored-By` and no "Generated with" lines. **Never push to `develop` or `main`;** the PR is Task 4, after Patrick's OK.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **`run_spine`'s signature against the merged `flow/spine.py`.** It must take `ledger=` and `repository=` as keywords and return an `AskResponse` (Task 1, Step 1). A different signature: adapt only the one call in `main` and its test stand-in (`spine_returning`), ledger a Ruling, tell Huvison.
2. **One demo user.** With L1 merged, `local_scope` must be `demo_scope(settings)` (Task 2, Step 4); without it, the CFO scope here must equal L1's (`demo-cfo`, `cfo`, `*`, the default tenant). Note: L1's `demo_scope` follows `DEMO_ROLE`, so `DEMO_ROLE=delivery_lead` in your shell makes the local run ask as a delivery lead. Unset it for the demo rehearsal.
3. **No spine logic crept in.** `grep -nE "while |for claim|retry" scripts/ask.py` prints nothing.
4. **Partial responses carry the cost.** After the E9 run (Task 3, Step 1) the `Cost:` line is `$0.0000` (no model call); after the Q01 run it is above `$0.0000` and below `$0.5000`.
5. **The output hides nothing that matters:** every rejected claim and every trace step is printed; the JSON output has `pass` (alias) in the verdicts.

---

### Task 1: The demo user and the printed answer

**Files:**
- Create: `scripts/ask.py` *(new; Task 2 completes it)*, `tests/scripts/test_ask.py` *(new; Task 2 completes it)*

**Produces:** `scripts.ask.local_scope(settings: Settings) -> Scope`, `render(response: AskResponse) -> str`; constants `DEMO_USER_ID = "demo-cfo"`, `DEMO_ROLE = "cfo"`, `COST_DECIMALS = 4`, `TRACE_SEPARATOR`, `CITATION_SEPARATOR`. **Consumes:** `tools.api_schema.AskResponse`, `TraceStep` (C1); `tools.models.Scope`; `tools.constants.ALL_ENTITIES_WILDCARD`; `config.Settings` (exist).

- [ ] **Step 1: Branch, baseline, and the H2b and L1 checks**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed|skipped)|TOTAL"
uv run python -c "import inspect; from flow.spine import run_spine; print(inspect.signature(run_spine))"
uv run python -c "from auth.scope import demo_scope; print('L1 merged')"
git switch -c feature/local-ask-runner
mkdir -p .superpowers && printf '# Ledger: P3 Local ask runner\n' > .superpowers/ledger-P3.md
```
Expected: `N passed` (write it in the ledger); then `(question: tools.models.Question, *, ledger: tools.ports.Ledger, repository: tools.ports.ArtefactRepository, agents: flow.spine.SpineAgents = SpineAgents(orchestrator=None, writer=None, critic_agent=None)) -> tools.api_schema.AskResponse`. `No module named 'flow'` or `'flow.spine'`: stop, H2b isn't merged. Then either `L1 merged` (write "L1 variant" in the ledger: Task 2, Step 4 applies) or `ModuleNotFoundError: No module named 'auth'` (write "pre-L1 variant"; skip Task 2, Step 4).

- [ ] **Step 2: Write the failing tests.** Create `tests/scripts/test_ask.py`:
```python
"""scripts/ask.py: the local runner builds the demo CFO's question, runs flow.spine.run_spine on a fresh in-memory
ledger and the committed CSVs, and prints what /ask returns. No test calls Bedrock or AWS."""
from config import get_settings
from scripts import ask
from tools.api_schema import AskResponse, PromptRef, RejectedClaim, TraceStep
from tools.models import Answer, Bullet, Citation, Verdict

RUN_ID = "local-test-run"
ANSWER = Answer(headline="E4 is blocked by DEF-0412",
                bullets=[Bullet(text="212 customer records fail on DEF-0412",
                                citations=[Citation(artefact="defect_log", row_id="DEF-0412")])])
SPENT_COST_USD = 0.0123


def test_render_shows_the_answer_citations_rejections_trace_and_cost():
    rejected = RejectedClaim(claim_id="claim-2", statement="E4 is on track", reason="no evidence",
                             verdicts=[Verdict(claim_id="claim-2", passed=False, reason="no evidence")])
    trace = [TraceStep(step="check_budget"),
             TraceStep(step="run_orchestrator", agent="orchestrator",
                       prompt=PromptRef(agent="orchestrator", version="1.0.0", sha256="hash"))]
    text = ask.render(AskResponse(run_id=RUN_ID, answer=ANSWER, rejected=[rejected], cost_usd=SPENT_COST_USD,
                                  trace=trace))
    for expected in ("E4 is blocked by DEF-0412", "[defect_log:DEF-0412]", "Could not verify (1)",
                     "claim-2: E4 is on track (no evidence)", "check_budget -> run_orchestrator (orchestrator 1.0.0)",
                     "Cost: $0.0123"):
        assert expected in text, expected


def test_render_shows_a_partial_answer():
    text = ask.render(AskResponse(run_id=RUN_ID, cost_usd=0, partial=True, partial_reason="unknown entity: E9"))
    assert "Partial answer: unknown entity: E9" in text and "Answer:" not in text.replace("Partial answer:", "")


def test_the_local_scope_is_the_demo_cfo_of_the_default_tenant():
    scope = ask.local_scope(get_settings())
    assert (scope.user_id, scope.role, scope.entity_ids, scope.tenant_id) == (
        "demo-cfo", "cfo", ("*",), get_settings().default_tenant_id)
```

- [ ] **Step 3: Run them and watch them fail**
```bash
uv run --locked pytest tests/scripts/test_ask.py --no-cov 2>&1 | grep -E "^E " | head -1
uv run --locked pytest tests/scripts/test_ask.py --no-cov 2>&1 | tail -1
```
Expected: `E   ImportError: cannot import name 'ask' from 'scripts' (unknown location)`, then `1 error in …s`.

- [ ] **Step 4: Implement.** Create `scripts/ask.py`:
```python
"""Ask the agent loop one question on this machine: the committed CSV data, an in-memory ledger, real Bedrock models.

Usage, from the repo root (AWS_PROFILE=hackathon AWS_REGION=eu-west-1 for the model calls):
  uv run python scripts/ask.py --entity E4 "What is blocking cutover?"
  uv run python scripts/ask.py --entity E4 "What is blocking cutover?" --json   # the AskResponse as JSON
It calls Huvison's flow.spine.run_spine, which runs the ask-spine states (flow/steps.py) in the Express state
machine's order with the real agents. The user is the demo CFO (AUTH_MODE=none). It prints the answer and its
citations, the claims that could not be verified, the trace with prompt versions, and the cost.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from config import Settings  # noqa: E402
from tools.api_schema import AskResponse, TraceStep  # noqa: E402
from tools.constants import ALL_ENTITIES_WILDCARD  # noqa: E402
from tools.models import Scope  # noqa: E402

DEMO_USER_ID = "demo-cfo"
DEMO_ROLE = "cfo"
COST_DECIMALS = 4
TRACE_SEPARATOR = " -> "
CITATION_SEPARATOR = ", "


def local_scope(settings: Settings) -> Scope:
    """The demo user of AUTH_MODE=none: the CFO, every entity of the default tenant (the same user as L1's
    auth.scope.demo_scope)."""
    return Scope(user_id=DEMO_USER_ID, role=DEMO_ROLE, tenant_id=settings.default_tenant_id,
                 entity_ids=(ALL_ENTITIES_WILDCARD,))


def _trace_label(trace_step: TraceStep) -> str:
    if trace_step.prompt is None:
        return trace_step.step
    return f"{trace_step.step} ({trace_step.prompt.agent} {trace_step.prompt.version})"


def render(response: AskResponse) -> str:
    """The response as the text a person reads in a terminal."""
    lines = [f"Run {response.run_id}"]
    if response.partial:
        lines.append(f"Partial answer: {response.partial_reason}")
    if response.answer:
        lines.append(f"Answer: {response.answer.headline}")
        for bullet in response.answer.bullets:
            labels = CITATION_SEPARATOR.join(citation.label() for citation in bullet.citations)
            lines.append(f"  - {bullet.text}  [{labels}]")
    if response.rejected:
        lines.append(f"Could not verify ({len(response.rejected)}):")
        lines.extend(f"  - {rejected.claim_id}: {rejected.statement} ({rejected.reason})"
                     for rejected in response.rejected)
    if response.trace:
        lines.append("Trace: " + TRACE_SEPARATOR.join(_trace_label(trace_step) for trace_step in response.trace))
    lines.append(f"Cost: ${response.cost_usd:.{COST_DECIMALS}f}")
    return "\n".join(lines)
```

- [ ] **Step 5: Run the tests**
```bash
uv run --locked pytest tests/scripts/test_ask.py --no-cov 2>&1 | tail -1
```
Expected: `3 passed in …s`.

- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed|skipped)|TOTAL"
git add scripts/ask.py tests/scripts/test_ask.py
git commit -m "Local ask runner: the demo CFO and the printed answer, citations, could-not-verify claims, trace and cost"
```
Expected: `N+3 passed`, coverage unchanged (`scripts/` is outside the coverage sources).

**Task done when:**
- `uv run --locked pytest tests/scripts/test_ask.py --no-cov` prints `3 passed`.
- `git log -1 --format=%s` prints the commit message above.

### Task 2: The command line on `flow.spine.run_spine`

**Files:**
- Modify: `scripts/ask.py`, `tests/scripts/test_ask.py` (both replaced by the full files below)

**Produces:** `scripts.ask.main(argv: list[str] | None = None) -> int`; constants `LOCAL_RUN_PREFIX = "local-"`, `JSON_INDENT = 2`, `EXIT_OK = 0`. **Consumes:** `flow.spine.run_spine(question, *, ledger, repository, agents=SpineAgents()) -> AskResponse` and `flow.spine.SpineAgents` (H2b); `adapters.csv_repo.CsvRepository`, `adapters.memory_ledger.InMemoryLedger`, `config.DEFAULT_ARTEFACTS_URI`, `get_settings`, `tools.models.Question`, `OrchestratorResult`, `PartialAnswer`, `Plan` (exist); with L1, `auth.scope.demo_scope(settings) -> Scope`.

- [ ] **Step 1: Write the failing tests.** Replace the whole of `tests/scripts/test_ask.py` with:
```python
"""scripts/ask.py: the local runner builds the demo CFO's question, runs flow.spine.run_spine on a fresh in-memory
ledger and the committed CSVs, and prints what /ask returns. No test calls Bedrock or AWS."""
import functools
import json
import subprocess
import sys

import pytest

from adapters.csv_repo import CsvRepository
from adapters.memory_ledger import InMemoryLedger
from config import REPO_ROOT, get_settings
from flow import spine
from scripts import ask
from tools.api_schema import AskResponse, PromptRef, RejectedClaim, TraceStep
from tools.models import Answer, Bullet, Citation, OrchestratorResult, PartialAnswer, Plan, Verdict

ASK_SCRIPT = REPO_ROOT / "scripts" / "ask.py"
RUN_ID = "local-test-run"
EXIT_USAGE_ERROR = 2
QUESTION_TEXT = "What is blocking cutover?"
ANSWER = Answer(headline="E4 is blocked by DEF-0412",
                bullets=[Bullet(text="212 customer records fail on DEF-0412",
                                citations=[Citation(artefact="defect_log", row_id="DEF-0412")])])
SPENT_COST_USD = 0.0123
UNKNOWN_ENTITY_REASON = "unknown entity: E9 is not in this programme"


class UnknownEntityOrchestrator:
    """Stands in for P2's orchestrator on an entity that isn't in the programme: a partial answer, no claims."""

    def orchestrate(self, question, repository, ledger):
        return OrchestratorResult(plan=Plan(run_id=question.run_id, steps=[]),
                                  partial=PartialAnswer(reason=UNKNOWN_ENTITY_REASON))

    def replan(self, question, rejected_claim, verdict, repository, ledger):
        raise AssertionError("an unknown entity has no claim to re-plan")


def writer_that_must_not_run(writer_input):
    raise AssertionError("the writer must not run for a partial answer without claims")


def spine_returning(response: AskResponse, seen: dict):
    """A stand-in for flow.spine.run_spine: records what main passed, returns the response under the run's ID."""
    def fake_run_spine(question, *, ledger, repository):
        seen.update(question=question, ledger=ledger, repository=repository)
        return response.model_copy(update={"run_id": question.run_id})
    return fake_run_spine


def test_render_shows_the_answer_citations_rejections_trace_and_cost():
    rejected = RejectedClaim(claim_id="claim-2", statement="E4 is on track", reason="no evidence",
                             verdicts=[Verdict(claim_id="claim-2", passed=False, reason="no evidence")])
    trace = [TraceStep(step="check_budget"),
             TraceStep(step="run_orchestrator", agent="orchestrator",
                       prompt=PromptRef(agent="orchestrator", version="1.0.0", sha256="hash"))]
    text = ask.render(AskResponse(run_id=RUN_ID, answer=ANSWER, rejected=[rejected], cost_usd=SPENT_COST_USD,
                                  trace=trace))
    for expected in ("E4 is blocked by DEF-0412", "[defect_log:DEF-0412]", "Could not verify (1)",
                     "claim-2: E4 is on track (no evidence)", "check_budget -> run_orchestrator (orchestrator 1.0.0)",
                     "Cost: $0.0123"):
        assert expected in text, expected


def test_render_shows_a_partial_answer():
    text = ask.render(AskResponse(run_id=RUN_ID, cost_usd=0, partial=True, partial_reason="unknown entity: E9"))
    assert "Partial answer: unknown entity: E9" in text and "Answer:" not in text.replace("Partial answer:", "")


def test_the_local_scope_is_the_demo_cfo_of_the_default_tenant():
    scope = ask.local_scope(get_settings())
    assert (scope.user_id, scope.role, scope.entity_ids, scope.tenant_id) == (
        "demo-cfo", "cfo", ("*",), get_settings().default_tenant_id)


def test_main_runs_the_spine_for_the_demo_cfo_on_a_fresh_ledger_and_the_committed_csvs(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr(ask, "run_spine", spine_returning(
        AskResponse(run_id=RUN_ID, answer=ANSWER, cost_usd=SPENT_COST_USD), seen))
    assert ask.main(["--entity", "E4", QUESTION_TEXT]) == ask.EXIT_OK
    settings, question = get_settings(), seen["question"]
    assert question.run_id.startswith(ask.LOCAL_RUN_PREFIX) and question.scope == ask.local_scope(settings)
    assert (question.entity_id, question.question, question.budget_usd, question.max_attempts) == (
        "E4", QUESTION_TEXT, settings.run_budget_usd, settings.max_claim_attempts)
    assert isinstance(seen["ledger"], InMemoryLedger) and isinstance(seen["repository"], CsvRepository)
    assert "Answer: E4 is blocked by DEF-0412" in capsys.readouterr().out


def test_main_prints_the_ask_response_as_json(monkeypatch, capsys):
    monkeypatch.setattr(ask, "run_spine", spine_returning(
        AskResponse(run_id=RUN_ID, answer=ANSWER, cost_usd=SPENT_COST_USD), {}))
    assert ask.main(["--entity", "E4", QUESTION_TEXT, "--json"]) == ask.EXIT_OK
    body = json.loads(capsys.readouterr().out)
    assert body["answer"]["bullets"][0]["citations"] == [{"artefact": "defect_log", "row_id": "DEF-0412"}]
    assert body["run_id"].startswith(ask.LOCAL_RUN_PREFIX)


def test_an_unknown_entity_prints_a_partial_answer_without_calling_the_writer(monkeypatch, capsys):
    agents = spine.SpineAgents(orchestrator=UnknownEntityOrchestrator(), writer=writer_that_must_not_run)
    monkeypatch.setattr(ask, "run_spine", functools.partial(spine.run_spine, agents=agents))
    assert ask.main(["--entity", "E9", "What is blocking cutover for E9?"]) == ask.EXIT_OK
    output = capsys.readouterr().out
    assert f"Partial answer: {UNKNOWN_ENTITY_REASON}" in output and "\nAnswer:" not in output


@pytest.mark.parametrize("arguments", [
    ["--entity", "E-4", QUESTION_TEXT],
    ["--entity", "E4", ""],
], ids=["malformed_entity", "empty_question"])
def test_the_command_refuses_a_bad_question_before_running_anything(arguments):
    completed = subprocess.run([sys.executable, str(ASK_SCRIPT), *arguments], cwd=REPO_ROOT, capture_output=True,
                               text=True, check=False)
    assert completed.returncode == EXIT_USAGE_ERROR and "invalid question" in completed.stderr
```

- [ ] **Step 2: Run them and watch them fail**
```bash
uv run --locked pytest tests/scripts/test_ask.py --no-cov 2>&1 | grep -E "^E  " | head -1
uv run --locked pytest tests/scripts/test_ask.py --no-cov 2>&1 | tail -1
```
Expected: `E       AttributeError: <module 'scripts.ask' from '…/scripts/ask.py'> has no attribute 'run_spine'`, then `5 failed, 3 passed in …s`.

- [ ] **Step 3: Implement.** Replace the whole of `scripts/ask.py` with:
```python
"""Ask the agent loop one question on this machine: the committed CSV data, an in-memory ledger, real Bedrock models.

Usage, from the repo root (AWS_PROFILE=hackathon AWS_REGION=eu-west-1 for the model calls):
  uv run python scripts/ask.py --entity E4 "What is blocking cutover?"
  uv run python scripts/ask.py --entity E4 "What is blocking cutover?" --json   # the AskResponse as JSON
It calls Huvison's flow.spine.run_spine, which runs the ask-spine states (flow/steps.py) in the Express state
machine's order with the real agents. The user is the demo CFO (AUTH_MODE=none). It prints the answer and its
citations, the claims that could not be verified, the trace with prompt versions, and the cost.
"""
import argparse
import json
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from pydantic import ValidationError  # noqa: E402

from adapters.csv_repo import CsvRepository  # noqa: E402
from adapters.memory_ledger import InMemoryLedger  # noqa: E402
from config import DEFAULT_ARTEFACTS_URI, Settings, get_settings  # noqa: E402
from flow.spine import run_spine  # noqa: E402
from tools.api_schema import AskResponse, TraceStep  # noqa: E402
from tools.constants import ALL_ENTITIES_WILDCARD  # noqa: E402
from tools.models import Question, Scope  # noqa: E402

DEMO_USER_ID = "demo-cfo"
DEMO_ROLE = "cfo"
LOCAL_RUN_PREFIX = "local-"
COST_DECIMALS = 4
JSON_INDENT = 2
TRACE_SEPARATOR = " -> "
CITATION_SEPARATOR = ", "
EXIT_OK = 0


def local_scope(settings: Settings) -> Scope:
    """The demo user of AUTH_MODE=none: the CFO, every entity of the default tenant (the same user as L1's
    auth.scope.demo_scope)."""
    return Scope(user_id=DEMO_USER_ID, role=DEMO_ROLE, tenant_id=settings.default_tenant_id,
                 entity_ids=(ALL_ENTITIES_WILDCARD,))


def _trace_label(trace_step: TraceStep) -> str:
    if trace_step.prompt is None:
        return trace_step.step
    return f"{trace_step.step} ({trace_step.prompt.agent} {trace_step.prompt.version})"


def render(response: AskResponse) -> str:
    """The response as the text a person reads in a terminal."""
    lines = [f"Run {response.run_id}"]
    if response.partial:
        lines.append(f"Partial answer: {response.partial_reason}")
    if response.answer:
        lines.append(f"Answer: {response.answer.headline}")
        for bullet in response.answer.bullets:
            labels = CITATION_SEPARATOR.join(citation.label() for citation in bullet.citations)
            lines.append(f"  - {bullet.text}  [{labels}]")
    if response.rejected:
        lines.append(f"Could not verify ({len(response.rejected)}):")
        lines.extend(f"  - {rejected.claim_id}: {rejected.statement} ({rejected.reason})"
                     for rejected in response.rejected)
    if response.trace:
        lines.append("Trace: " + TRACE_SEPARATOR.join(_trace_label(trace_step) for trace_step in response.trace))
    lines.append(f"Cost: ${response.cost_usd:.{COST_DECIMALS}f}")
    return "\n".join(lines)


def _problems(error: ValidationError) -> str:
    return "; ".join(f"{'.'.join(str(part) for part in detail['loc'])}: {detail['msg']}" for detail in error.errors())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ask the agent loop one question locally (CSV data, in-memory ledger).")
    parser.add_argument("--entity", required=True, help="the entity the question is about, e.g. E4")
    parser.add_argument("question", help="the question, in quotes")
    parser.add_argument("--json", action="store_true", help="print the AskResponse as JSON instead of text")
    arguments = parser.parse_args(argv)
    settings = get_settings()
    try:
        question = Question(run_id=f"{LOCAL_RUN_PREFIX}{uuid.uuid4().hex}", scope=local_scope(settings),
                            entity_id=arguments.entity, question=arguments.question,
                            budget_usd=settings.run_budget_usd, max_attempts=settings.max_claim_attempts)
    except ValidationError as error:
        parser.error(f"invalid question: {_problems(error)}")
    response = run_spine(question, ledger=InMemoryLedger(), repository=CsvRepository(DEFAULT_ARTEFACTS_URI))
    if arguments.json:
        print(json.dumps(response.model_dump(mode="json", by_alias=True), indent=JSON_INDENT))
    else:
        print(render(response))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Only if Task 1, Step 1 printed `L1 merged`: use L1's demo user.** In `scripts/ask.py`:
  - directly after `from adapters.memory_ledger import InMemoryLedger  # noqa: E402`, add `from auth.scope import demo_scope  # noqa: E402`;
  - delete the line `from tools.constants import ALL_ENTITIES_WILDCARD  # noqa: E402` and the two lines `DEMO_USER_ID = "demo-cfo"` and `DEMO_ROLE = "cfo"`;
  - replace the whole `local_scope` function with:
```python
def local_scope(settings: Settings) -> Scope:
    """The demo user of AUTH_MODE=none, built by L1's auth.scope.demo_scope, so the API and this runner agree."""
    return demo_scope(settings)
```
  The tests don't change: L1's demo user is the same CFO (`demo-cfo`, `cfo`, `*`, the default tenant).

- [ ] **Step 5: Run the tests and the command's refusal**
```bash
uv run --locked pytest tests/scripts/test_ask.py --no-cov 2>&1 | tail -1
uv run python scripts/ask.py --entity E-4 "What is blocking cutover?"; echo "exit $?"
uv run python scripts/ask.py --help | head -1
```
Expected: `8 passed in …s`; then `usage: ask.py [-h] --entity ENTITY [--json] question`, `ask.py: error: invalid question: entity_id: Value error, not an entity id: 'E-4'` and `exit 2`; then `usage: ask.py [-h] --entity ENTITY [--json] question`.

- [ ] **Step 6: Guards, full suite and commit**
```bash
uv run --locked pytest tests/test_dependencies.py tests/test_code_style.py --no-cov 2>&1 | tail -1
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed|skipped)|TOTAL"
git add scripts/ask.py tests/scripts/test_ask.py
git commit -m "Local ask runner: the command line runs flow.spine.run_spine on an in-memory ledger and the committed CSVs; --json"
```
Expected: `15 passed` (the guards; more if later items added some); then `N+8 passed`, coverage unchanged.

**Task done when:**
- `uv run --locked pytest tests/scripts/test_ask.py --no-cov` prints `8 passed`.
- `uv run python scripts/ask.py --entity E-4 "x"; echo $?` ends with `2`.
- `grep -c "from flow.spine import run_spine" scripts/ask.py` prints `1`.

### Task 3: The local and live runs, and the HANDOFF line

**Files:**
- Modify: `HANDOFF.md` ("What's real")

- [ ] **Step 1: The runs.** The E9 run needs P2 merged but no AWS (the orchestrator refuses an unknown entity in code, before any model call). The E4 runs need P2, L5 and H3 merged and your Bedrock access: **verify in AWS**.
```bash
uv run python scripts/ask.py --entity E9 "What is blocking cutover for E9?"
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
time uv run python scripts/ask.py --entity E4 "What is blocking cutover for E4?"
uv run python scripts/ask.py --entity E4 "What is blocking cutover for E4?" --json > /tmp/ask-E4.json && python3 -m json.tool /tmp/ask-E4.json > /dev/null && echo "valid JSON"
```
Expected:
  - the E9 run prints `Run local-…`, `Partial answer: unknown entity: E9 is not in this programme`, `Trace: check_budget -> run_orchestrator (orchestrator 1.0.0) -> store_claims -> write_answer`, `Cost: $0.0000`, and no `Answer:` line (this is the dry-run's real output);
  - the first E4 run prints `Run local-…`, an `Answer:` line, at least one bullet whose brackets include `defect_log:DEF-0412` and one with `reconciliation_results:RC-C3-E4-customers`, a `Trace:` line containing `run_orchestrator (orchestrator 1.0.0)`, and `Cost: $0.0…` (below `0.5000`); write the `real` time in the ledger (H7 times `/ask` against 29 s);
  - the third prints `valid JSON`.
  Copy the outputs into the ledger. If P2, L5 or H3 isn't merged, write "run deferred: <item> not merged" for the runs that need it and do them after. A missing citation is a finding for the agents (P1, P2, L5), not for this script: note it and go on.
- [ ] **Step 2: `HANDOFF.md`.** Under `## What's real`, directly after the line that starts `- The orchestrator (` (P2; if P2 isn't merged yet, as the last line of that section), add:
```markdown
- `uv run python scripts/ask.py --entity E4 "What is blocking cutover?"` runs the whole ask spine on one machine (`flow.spine.run_spine`: CSV data, in-memory ledger, real Bedrock agents) in the state machine's order, and prints the cited answer, what could not be verified, the trace and the cost.
```
- [ ] **Step 3: Guards, full suite and commit**
```bash
uv run --locked pytest tests/test_dependencies.py tests/test_code_style.py --no-cov 2>&1 | tail -1
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed|skipped)|TOTAL"
git add HANDOFF.md
git commit -m "HANDOFF: the local ask runner is real"
```
Expected: the guards pass (`15 passed` or more, 0 failed); `N+8 passed`.

**Task done when:**
- `grep -c "scripts/ask.py" HANDOFF.md` prints `1`.
- The ledger holds the run outputs, or "run deferred: …".

### Task 4: Review, then PR (after Patrick's OK)
- [ ] **Step 1:** Check each Review Focus line by hand; write the result of each in the ledger.
- [ ] **Step 2:** `git diff develop --stat`. Expected: exactly `HANDOFF.md`, `scripts/ask.py`, `tests/scripts/test_ask.py` (3 files).
- [ ] **Step 3:** Get a fresh review of the diff against [[P3 - Local ask runner - spec]]. Fix critical and important findings test-first; list the minors in the PR.
- [ ] **Step 4: With Patrick's OK only:** `git push -u origin feature/local-ask-runner`, then open the PR to `develop` titled "scripts/ask.py: the README's command 5 runs the ask spine locally (P3)". Body: what changed, the test count, which `local_scope` variant (L1 or pre-L1), the run outputs (or "deferred"), the `Ruling:` lines, the deferred minors. No attribution lines.
- [ ] **Step 5:** Update [[Build order]]: P3 → `in review (PR #nn)`, then `merged`. If the pre-L1 variant was used and L1 merges later, tell Patrick: a one-commit follow-up applies Task 2, Step 4.

**Task done when:**
- `gh pr view --json baseRefName,state` shows `"baseRefName":"develop"` and `"state":"OPEN"` (then `MERGED`).
- [[Build order]] row P3 shows the PR number or `merged`.

## Done means
- [ ] **The runner is tested.** *Verify:* on `develop`, `uv run --locked pytest tests/scripts/test_ask.py --no-cov` prints `8 passed`.
- [ ] **The suite is green.** *Verify:* `uv run --locked pytest 2>&1 | grep -E "passed|TOTAL"` shows 0 failed and `TOTAL` ≥ 96%.
- [ ] **The script runs H2b's spine and holds no spine logic.** *Verify:* `grep -c "from flow.spine import run_spine" scripts/ask.py` prints `1`; `grep -nE "while |for claim|retry" scripts/ask.py` prints nothing.
- [ ] **One demo user.** *Verify:* `uv run --locked pytest tests/scripts/test_ask.py -k local_scope --no-cov` prints `1 passed`; with L1 on `develop`, `grep -n "return demo_scope(settings)" scripts/ask.py` shows one line.
- [ ] **Bad input never starts a run.** *Verify:* `uv run python scripts/ask.py --entity E-4 "What is blocking cutover?"; echo $?` prints `invalid question: entity_id: …` and `2`.
- [ ] **An unknown entity is a partial answer, without a model call.** *Verify:* with P2 merged and no AWS credentials, `uv run python scripts/ask.py --entity E9 "What is blocking cutover for E9?"` prints `Partial answer: unknown entity: E9 is not in this programme` and `Cost: $0.0000`.
- [ ] **README command 5 answers Q01 with citations.** *Verify:* the PR body (or a follow-up comment) has the Task 3 output with `defect_log:DEF-0412` and `reconciliation_results:RC-C3-E4-customers` in the bullets.
- [ ] **HANDOFF is true.** *Verify:* `grep -n "scripts/ask.py" HANDOFF.md` shows the "What's real" line.
- [ ] **Merged.** *Verify:* the PR shows `Merged` into `develop`; [[Build order]] row P3 is `merged`.

## Never
- Sequence the states, decide a retry, or read or reset an attempt count in the script: that is `flow.spine.run_spine` (H2b).
- Switch the script to `flow/local.py` when H6 lands; it keeps calling `run_spine`.
- Take the scope from the command line; build it only in `local_scope` (L1's `demo_scope` once merged, which follows `config.py`'s `demo_role`).
- Call Bedrock or AWS in a test.
- Edit `flow/` or `auth/` to make the script fit; adapt the call in `main` and tell the owner.
- Push to `develop` or `main`; add attribution lines.

Related: [[P3 - Local ask runner - spec]], [[Build order]], [[How to execute a plan]]
