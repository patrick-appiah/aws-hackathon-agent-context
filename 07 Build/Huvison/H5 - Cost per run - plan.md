---
tags: [build, plan, area/flow]
id: H5
owner: Huvison
spec: "[[H5 - Cost per run - spec]]"
status: ready
updated: 2026-10-14
---
# H5: Cost per run (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[H5 - Cost per run - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; ledger the conflict.
3. [[Huvison - trust and flow]] §6, [[A3a - Bedrock unit prices - spec]], [[Workstreams]] §7.

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Huvison.

**Goal:** a price table and two functions that turn every agent's `usage` into USD on the run's ledger entry.

**Architecture:** the table is a domain constant in the core (`tools/constants.py`); the functions live in the new `flow/` package (not the core: `flow` may use adapters and config later). `flow/__init__.py` holds only a docstring.

**Tech stack:** Python 3.11, pydantic 2, pytest, uv.

**Dry-run status:** re-run on C1 at `94970fd` (C1 alone: `213 passed`, 96%); the counts below are from that run. Tasks 1–2 ran in a throwaway worktree of C1 + H1; counts and messages are real. Task 3 needs A3a's values (not available): its test step is the same suite, which doesn't depend on the values.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: `feature/cost-per-run` from an up-to-date `develop` after **C1 and H1** are merged.
- **Start state:** `uv run --locked pytest` → **239 passed**, `TOTAL` 96% (C1 + H1). If other items merged first, write your real number in the ledger file; the deltas must match.
- **Rules:** `eu-west-1`, `eu.*` model IDs only; synthetic data; no secrets. Settings only in `config.py`, domain constants only in `tools/constants.py`; descriptive names, no single-character names, no magic numbers. The core imports no boto3, Strands, adapters, `config`, `os`. Never weaken a security rule. Tests in `tests/` mirroring the code; coverage must not drop. No layout or meta guard tests. Stay in your folders: `flow/`, `tests/flow/` *(new)*, and the named lines of `tools/constants.py` and `pyproject.toml`.
- **Commits:** one per task, the given message, **no attribution lines**. Never push to `develop` or `main`.

## Review Focus
1. **No price is zero or missing** for a model `config.py` can select (the test covers today's defaults; an env override to another model would raise `UnpricedModel` at the first call: intended).
2. **`flow/__init__.py` imports nothing** (P2 imports `flow.budget`; an import there could loop back through `agents.orchestrator`).
3. **The placeholder comment is gone after Task 3,** replaced by A3a's source and date.
4. **Float sums:** `cost_usd` sums floats; the ledger stores them as `Decimal(str(x))` (H1). Rounding is for display only (COST.md).
5. **`--cov=flow`** is in `addopts` once, and the coverage report lists `flow/` files when they miss lines.

---

### Task 1: The price table and `cost_usd`

**Files:**
- Create: `flow/__init__.py` *(new)*, `flow/cost.py` *(new)*, `tests/flow/test_cost.py` *(new)* (the folder `tests/flow/` is new; no `__init__.py`)
- Modify: `tools/constants.py` (append), `pyproject.toml` (`addopts`)

**Produces:** `tools.constants.TOKENS_PER_PRICE_UNIT`, `MODEL_PRICES_USD_PER_1K_TOKENS`; `flow.cost.UnpricedModel`, `flow.cost.cost_usd(usages: list[Usage]) -> float`. **Consumes:** `tools.models.Usage` (C1). **Consumed by:** Task 2, H2b.

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/cost-per-run
mkdir -p .superpowers && printf '# Ledger: H5 Cost per run\n' > .superpowers/ledger-H5.md
```
Expected: `239 passed`, `TOTAL ... 96%`.
- [ ] **Step 2: Failing test.** Create `tests/flow/test_cost.py`:
```python
"""Cost per run (flow/cost.py): token usage times the price table in tools/constants.py."""
import pytest

from config import DEFAULT_REASONING_MODEL, DEFAULT_RETRIEVAL_MODEL
from flow.cost import UnpricedModel, cost_usd
from tools.constants import MODEL_PRICES_USD_PER_1K_TOKENS, TOKENS_PER_PRICE_UNIT
from tools.models import Usage

REASONING_CALL = Usage(model_id=DEFAULT_REASONING_MODEL, tokens_in=2000, tokens_out=500)
RETRIEVAL_CALL = Usage(model_id=DEFAULT_RETRIEVAL_MODEL, tokens_in=4000, tokens_out=1000)


def expected_cost(usage: Usage) -> float:
    input_price, output_price = MODEL_PRICES_USD_PER_1K_TOKENS[usage.model_id]
    return (usage.tokens_in * input_price + usage.tokens_out * output_price) / TOKENS_PER_PRICE_UNIT


def test_cost_is_tokens_times_the_price_per_thousand():
    assert cost_usd([REASONING_CALL]) == pytest.approx(expected_cost(REASONING_CALL))


def test_cost_sums_every_model_call():
    assert cost_usd([REASONING_CALL, RETRIEVAL_CALL]) == pytest.approx(
        expected_cost(REASONING_CALL) + expected_cost(RETRIEVAL_CALL))
    assert cost_usd([]) == 0


def test_an_unpriced_model_fails_loudly():
    with pytest.raises(UnpricedModel, match="eu.example.unpriced-model"):
        cost_usd([Usage(model_id="eu.example.unpriced-model", tokens_in=1, tokens_out=1)])
```
- [ ] **Step 3: Run it:** `uv run --locked pytest tests/flow/test_cost.py --no-cov 2>&1 | grep -E "^E  " | head -1`. Expected: `E   ModuleNotFoundError: No module named 'flow'`.
- [ ] **Step 4: Implement.**
  - Append to `tools/constants.py`:
    ```python

    # Bedrock on-demand prices in USD per 1,000 tokens, (input, output), by inference profile (flow/cost.py).
    # Placeholder list prices until A3: the values from A3 (Abdul's eu-west-1 research, COST.md) replace these,
    # with the source and the date in this comment. Every model ID config.py can select must be listed here.
    TOKENS_PER_PRICE_UNIT = 1000
    MODEL_PRICES_USD_PER_1K_TOKENS = {
        "eu.anthropic.claude-sonnet-4-6": (0.003, 0.015),
        "eu.amazon.nova-lite-v1:0": (0.00006, 0.00024),
    }
    ```
  - Create `flow/__init__.py`:
    ```python
    """The ask spine and the publish flow (trust and flow, Huvison).

    Each Step Functions state is one function here: flow/steps.py (the ask spine), flow/publish.py (publish and
    approve), flow/budget.py (the budget check), flow/cost.py (cost per run). Not the core: flow may use config and
    the adapters, and the Lambda entry points in flow/handlers.py build them from settings.
    """
    ```
  - Create `flow/cost.py`:
    ```python
    """Cost per run: the model calls' token usage times the price table (tools/constants.py).

    Every state that runs an agent calls record_usage with the agent result's `usage`, so the run's cost in the
    ledger is measured from real calls, and the budget check (flow/budget.py) reads it.
    """
    from tools.constants import MODEL_PRICES_USD_PER_1K_TOKENS, TOKENS_PER_PRICE_UNIT
    from tools.models import Usage


    class UnpricedModel(LookupError):
        """A model call whose model ID has no price: the run's cost can't be measured, so the budget can't hold."""


    def cost_usd(usages: list[Usage]) -> float:
        """The cost of a list of model calls, in USD."""
        total_usd = 0.0
        for usage in usages:
            if usage.model_id not in MODEL_PRICES_USD_PER_1K_TOKENS:
                raise UnpricedModel(f"no price for model {usage.model_id}: add it to MODEL_PRICES_USD_PER_1K_TOKENS "
                                    f"in tools/constants.py")
            input_price, output_price = MODEL_PRICES_USD_PER_1K_TOKENS[usage.model_id]
            total_usd += (usage.tokens_in * input_price + usage.tokens_out * output_price) / TOKENS_PER_PRICE_UNIT
        return total_usd
    ```
  - In `pyproject.toml`, in `addopts`, insert `--cov=flow ` directly before `--cov-report` (L1 inserts `--cov=auth ` the same way; whichever merges second keeps both).
- [ ] **Step 5: Run:** `uv run --locked pytest tests/flow/test_cost.py --no-cov 2>&1 | tail -1`. Expected: `3 passed in …s`.
- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
uv run --locked pytest tests/test_architecture.py tests/test_dependencies.py --no-cov 2>&1 | tail -1
git add tools/constants.py flow/__init__.py flow/cost.py tests/flow/test_cost.py pyproject.toml
git commit -m "Price table per eu.* model and cost_usd: tokens times price, unknown models refused"
```
Expected: `242 passed` (start + 3), `TOTAL ... 96%`; the guards line ends in `passed`.

**Task done when:** `uv run --locked pytest tests/flow/test_cost.py --no-cov 2>&1 | tail -1` prints `3 passed`; `grep -c "cov=flow" pyproject.toml` prints `1`.

### Task 2: `record_usage`, and every configured model is priced

**Files:** Modify `flow/cost.py`, `tests/flow/test_cost.py`

**Produces:** `flow.cost.record_usage(ledger: Ledger, run_id: str, usages: list[Usage]) -> float`. **Consumes:** `Ledger.add_cost`, `Ledger.run` (H1), `tools.models.total_tokens` (C1). **Consumed by:** H2b (`run_orchestrator`, `judge_claim`, `write_answer`).

- [ ] **Step 1: Failing tests.** In `tests/flow/test_cost.py`, replace the import block (from `import pytest` to `from tools.models import Usage`) with:
```python
import pytest

from adapters.memory_ledger import InMemoryLedger
from config import DEFAULT_REASONING_MODEL, DEFAULT_RETRIEVAL_MODEL, get_settings
from flow.cost import UnpricedModel, cost_usd, record_usage
from tools.constants import MODEL_PRICES_USD_PER_1K_TOKENS, TOKENS_PER_PRICE_UNIT
from tools.models import Usage
```
and append:
```python


def test_record_usage_adds_tokens_and_cost_to_the_run(cfo_scope):
    ledger = InMemoryLedger()
    ledger.start_run("run-1", cfo_scope, budget_usd=0.5)
    recorded = record_usage(ledger, "run-1", [REASONING_CALL, RETRIEVAL_CALL])
    run = ledger.run("run-1")
    assert (run["tokens_in"], run["tokens_out"]) == (6000, 1500)
    assert run["cost_usd"] == pytest.approx(recorded) and recorded == pytest.approx(
        cost_usd([REASONING_CALL, RETRIEVAL_CALL]))


def test_configured_models_all_have_a_price():
    settings = get_settings()
    configured = {settings.orchestrator_model_id, settings.retriever_model_id, settings.analyst_model_id,
                  settings.critic_model_id, settings.writer_model_id}
    assert configured <= set(MODEL_PRICES_USD_PER_1K_TOKENS)
```
- [ ] **Step 2: Run:** `uv run --locked pytest tests/flow/test_cost.py --no-cov 2>&1 | grep -E "^E  " | head -1`. Expected: `E   ImportError: cannot import name 'record_usage' from 'flow.cost' (...)`.
- [ ] **Step 3: Implement.** In `flow/cost.py`, replace `from tools.models import Usage` with:
```python
from tools.models import Usage, total_tokens
from tools.ports import Ledger
```
and append:
```python


def record_usage(ledger: Ledger, run_id: str, usages: list[Usage]) -> float:
    """Add a step's model calls to the run in the ledger (tokens and cost); return the step's cost in USD."""
    step_cost_usd = cost_usd(usages)
    tokens_in, tokens_out = total_tokens(usages)
    ledger.add_cost(run_id, tokens_in, tokens_out, step_cost_usd)
    return step_cost_usd
```
- [ ] **Step 4: Run:** `uv run --locked pytest tests/flow/test_cost.py --no-cov 2>&1 | tail -1`. Expected: `5 passed in …s`.
- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add flow/cost.py tests/flow/test_cost.py
git commit -m "record_usage: every agent step adds its tokens and cost to the run in the ledger"
```
Expected: `244 passed` (start + 5), `TOTAL ... 96%`, no `flow/` line in the report (100% covered files are skipped).

**Task done when:** `uv run --locked pytest tests/flow/test_cost.py --no-cov 2>&1 | tail -1` prints `5 passed`.

### Task 3: A3a's prices replace the placeholders (when Abdul's A3a is merged)
**Files:** Modify `tools/constants.py` (the price comment and two tuples)
- [ ] **Step 1:** Open `COST.md` on `develop` and read the two rows A3a filled: the unit prices for `eu.anthropic.claude-sonnet-4-6` and `eu.amazon.nova-lite-v1:0` (per 1K tokens, input and output), the source link and the date. If A3a isn't merged, stop here and do the PR (Task 4) with the placeholders; this task becomes a follow-up PR.
- [ ] **Step 2:** In `tools/constants.py`, replace the comment line `# Placeholder list prices until A3: the values from A3 (Abdul's eu-west-1 research, COST.md) replace these,` and the line after it with: `# Source: <the A3a source link>, Europe (Ireland) EU cross-region row, read <the A3a date> (A3a, COST.md).` and `# Every model ID config.py can select must be listed here.`; put A3a's four numbers in the two tuples.
- [ ] **Step 3: Run and commit**
```bash
uv run --locked pytest tests/flow/test_cost.py --no-cov 2>&1 | tail -1
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add tools/constants.py
git commit -m "Bedrock eu-west-1 prices from A3a, with source and date"
```
Expected: `5 passed`; full suite unchanged from Task 2 (`244 passed` or your start + 5).

**Task done when:** `grep -n "Placeholder" tools/constants.py` prints nothing and `grep -n "Source:" tools/constants.py` prints the A3a line.

### Task 4: Docs, review and PR
- [ ] **Step 1: `HANDOFF.md`.** Under `## What's real`, add the line: `- Cost per run is measured: every agent's token usage times the price table in \`tools/constants.py\` (\`flow/cost.py\`), added to the run in the ledger; the budget check reads it.`
- [ ] **Step 2: Commit:** `git add HANDOFF.md && git commit -m "HANDOFF: cost per run is measured from token usage"`. Expected: one file changed.
- [ ] **Step 3:** Review Focus by hand; results in `.superpowers/ledger-H5.md`.
- [ ] **Step 4:** `git diff develop --stat`. Expected: `HANDOFF.md`, `flow/__init__.py`, `flow/cost.py`, `pyproject.toml`, `tests/flow/test_cost.py`, `tools/constants.py` (6 files).
- [ ] **Step 5: With Huvison's OK only:** push `feature/cost-per-run`, open the PR to `develop` ("Cost per run: price table and record_usage (H5)"), body with the count, whether the prices are A3a's or placeholders, and the rulings. No attribution lines.
- [ ] **Step 6:** [[Build order]] row H5 → `in review (PR #nn)`, then `merged`. Tell Abdul (A3b can measure once H2b runs) and Patrick (H2a can start).

**Task done when:** the PR is open with the test count in its body, and the [[Build order]] row says `in review (PR #nn)`.

## Done means
- [ ] **Cost is computed from usage.** *Verify:* on `develop`, `uv run --locked pytest tests/flow/test_cost.py --no-cov 2>&1 | tail -1` prints `5 passed`.
- [ ] **Every configured model is priced.** *Verify:* `uv run --locked pytest tests/flow/test_cost.py --no-cov -k configured 2>&1 | tail -1 | cut -d, -f1` prints `1 passed`.
- [ ] **The prices are sourced.** *Verify:* `grep -n "Source:" tools/constants.py` shows A3a's link and date (or, if A3a was late, a follow-up PR is open and linked from the H5 PR).
- [ ] **`flow/` is in coverage.** *Verify:* `grep -c "cov=flow" pyproject.toml` prints `1`.
- [ ] **Nothing broke.** *Verify:* full suite on `develop` after merge: start + 5 passed, `TOTAL` ≥ 96%.
- [ ] **Merged.** *Verify:* PR merged into `develop`; [[Build order]] row H5 `merged`.

## Never
- Price an unknown model at zero or skip it.
- Put prices in `config.py` or read them from the environment.
- Import anything in `flow/__init__.py`.
- Push to `develop` or `main`, or add attribution lines.

Related: [[H5 - Cost per run - spec]], [[Build order]], [[How to execute a plan]]
