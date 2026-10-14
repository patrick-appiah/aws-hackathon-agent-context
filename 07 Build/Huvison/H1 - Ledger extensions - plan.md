---
tags: [build, plan, area/flow]
id: H1
owner: Huvison
spec: "[[H1 - Ledger extensions - spec]]"
status: ready
updated: 2026-10-14
---
# H1: Ledger extensions on both adapters (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]]: the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[H1 - Ledger extensions - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger file (see [[How to execute a plan]]).
3. [[Workstreams]] §3 and §7, and [[Huvison - trust and flow]] §1.
4. [[C1 - API and spine contracts - spec]] §3 and §5; the repo's `DECISIONS.md` D-012 and D-013; [[Working with AI assistants]].

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Huvison.

**Goal:** the `Ledger` port and both adapters read back runs and claims, keep rejected records in their own table, keep the trace, the publish task token and the publish decisions, all under the create-once rule, and the shared suite proves the two adapters behave the same.

**Architecture:** port in the core (`tools/ports.py`, a `Protocol`, no AWS), two adapters (`adapters/`). The DynamoDB adapter gains a second table and number conversion; the in-memory adapter is the reference. One test file runs every test on both.

**Tech stack:** Python 3.11, boto3 (adapter only), moto 5 (tests), pytest, uv. Run the tests with `uv run --locked pytest` from the repo root.

**Dry-run status:** every step below was run in a throwaway worktree of `feature/api-and-spine-contracts` (C1); the counts and messages are the real ones.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your clone). Branch: `feature/ledger-extensions` from an up-to-date `develop` **after C1 is merged**.
- **Start state:** `uv run --locked pytest` → **204 passed**, `TOTAL` 96% (C1 merged, nothing else). If another item merged first, your count is higher by its tests: write the real number in your ledger file; every task's **delta** (+8, +6, …) must still match.
- **Rules (enforced by tests or review):**
  - `eu-west-1` only; Bedrock `eu.*` inference profiles only; synthetic data only; no secrets anywhere (tests use moto and the fake credential `testing`).
  - Settings only in `config.py`; domain constants only in `tools/constants.py`; descriptive names; **no single-character names** (`tests/test_code_style.py`); no magic numbers.
  - The core (`tools/`) imports no boto3, Strands, adapters, `config` or `os` (`tests/test_architecture.py`). `tools/ports.py` stays a `Protocol`.
  - **Never weaken a security rule** (create-once ledger, scope gate, fail-closed critic, escaping) to make a test pass.
  - Every new ledger test goes in the **shared** suite and runs on both adapters (brief: "never to one adapter only").
  - Tests in `tests/`, mirroring the code; coverage must not drop.
  - No layout or "meta" guard tests: test behaviour, not file placement.
  - Stay in your folders: `tools/ports.py` (the `Ledger` port only), `adapters/memory_ledger.py`, `adapters/dynamo_ledger.py`, `adapters/__init__.py` (one line), `tests/adapters/test_ledgers.py`, and the doc lines in Task 6.
- **Commits:** one per task with the given message. **No `Co-Authored-By` and no "Generated with" lines.**
- **Never push to `develop` or `main`.** PR to `develop` after Huvison's OK; Patrick merges.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. **Create-once can't be bypassed through the new writes.** `put_rejected` and `put_task_token` use `ITEM_IS_NEW`; `add_step`'s counter uses `ITEM_EXISTS`; `record_decision` uses `ITEM_EXISTS`. Read every `_write` call.
2. **`put_rejected` copies the stored claim,** never something the caller passed (there's no content parameter).
3. **Number round trip:** `_to_item` is applied to every dict a write stores (`claim`, `verdicts`, `step`, `decision`), `_from_item` to every read. A missed one fails only on DynamoDB with a decimal value.
4. **Step order beyond 9999 steps** isn't handled (four digits). A run has at most a few dozen steps; check the ask spine can't loop past that (it is bounded by the retry limit and `MAX_PLAN_STEPS`).
5. **The real tables:** moto doesn't check IAM. Before the walking skeleton, confirm in AWS that the ask functions can `Query` the rejected-records table (verify in AWS with Michael and Yaw).

---

### Task 1: `DynamoLedger` gets the rejected-records table

**Files:**
- Modify: `adapters/dynamo_ledger.py` (docstring, constructor), `adapters/__init__.py` (`ledger_from_settings`), `tests/adapters/test_ledgers.py` (the fixture)

**Produces:** `DynamoLedger(table_name: str, region: str, rejected_table_name: str)` with `self.rejected_table`; `ledger_from_settings()` passing `settings.rejected_table`; test helper `create_table(boto3, table_name)`, constant `TEST_REJECTED_TABLE`. **Consumes:** `config.Settings.rejected_table` (C1).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/ledger-extensions
mkdir -p .superpowers && printf '# Ledger: H1 Ledger extensions\n' > .superpowers/ledger-H1.md
```
Expected: `TOTAL ... 96%` and `204 passed` (or your recorded start count).

- [ ] **Step 2: Write the failing test.** In `tests/adapters/test_ledgers.py`, replace everything from `TEST_TABLE = "test-run-ledger"` down to (not including) the line `@pytest.fixture` above `def started_run` with:
```python
TEST_TABLE = "test-run-ledger"
TEST_REJECTED_TABLE = "test-rejected-records"
RUN_BUDGET_USD = 0.50
FIRST_CALL_COST_USD = 0.12
LARGE_CALL_COST_USD = 0.40
TOKENS_IN = 1000
TOKENS_OUT = 200
MONEY_DECIMALS = 2
LEDGERS = ("memory", "dynamo")


def create_table(boto3, table_name):
    boto3.client("dynamodb", region_name=DEFAULT_REGION).create_table(
        TableName=table_name, BillingMode="PAY_PER_REQUEST",
        KeySchema=[{"AttributeName": PARTITION_KEY, "KeyType": "HASH"},
                   {"AttributeName": SORT_KEY, "KeyType": "RANGE"}],
        AttributeDefinitions=[{"AttributeName": PARTITION_KEY, "AttributeType": "S"},
                              {"AttributeName": SORT_KEY, "AttributeType": "S"}])


@pytest.fixture(params=LEDGERS)
def ledger(request, monkeypatch):
    if request.param == "memory":
        from adapters.memory_ledger import InMemoryLedger
        yield InMemoryLedger()
        return
    moto = pytest.importorskip("moto")
    boto3 = pytest.importorskip("boto3")
    for variable in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.setenv(variable, "testing")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    with moto.mock_aws():
        create_table(boto3, TEST_TABLE)
        create_table(boto3, TEST_REJECTED_TABLE)
        from adapters.dynamo_ledger import DynamoLedger
        yield DynamoLedger(TEST_TABLE, DEFAULT_REGION, TEST_REJECTED_TABLE)


```
- [ ] **Step 3: Run it and watch it fail**
```bash
uv run --locked pytest tests/adapters/test_ledgers.py --no-cov 2>&1 | grep -E "^E  " | sort | uniq -c
```
Expected: `5 E           TypeError: DynamoLedger.__init__() takes 3 positional arguments but 4 were given` (the five dynamo cases error; the five memory cases pass).

- [ ] **Step 4: Implement.**
  - In `adapters/dynamo_ledger.py`, replace the first line of the module docstring with these two lines:
    ```python
    """DynamoDB Ledger (target). Run ledger table: pk = run_id, sk = RUN | CLAIM#<id> | STEP#<n> | TASK.
    Rejected-records table (a separate table, REJECTED_TABLE): pk = run_id, sk = claim_id.
    ```
  - Replace the constructor's first three lines with:
    ```python
        def __init__(self, table_name: str, region: str, rejected_table_name: str):
            import boto3  # adapter-only dependency
            dynamodb = boto3.resource("dynamodb", region_name=region)
            self.table = dynamodb.Table(table_name)
            self.rejected_table = dynamodb.Table(rejected_table_name)
    ```
    (keep the `self._conditional_check_failed = ...` line after them).
  - In `adapters/__init__.py`, change `return DynamoLedger(settings.ledger_table, settings.aws_region)` to `return DynamoLedger(settings.ledger_table, settings.aws_region, settings.rejected_table)`.
- [ ] **Step 5: Run it:** `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov 2>&1 | tail -1`. Expected: `10 passed in …s`.
- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add adapters/dynamo_ledger.py adapters/__init__.py tests/adapters/test_ledgers.py
git commit -m "DynamoLedger takes the rejected-records table; ledger_from_settings passes REJECTED_TABLE"
```
Expected: `204 passed` (start + 0), `TOTAL ... 96%`.

**Task done when:** `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov 2>&1 | tail -1` prints `10 passed`; `git show --stat HEAD` lists exactly the three files.

### Task 2: Read back the run and the claims; numbers survive DynamoDB

**Files:**
- Modify: `tools/ports.py` (two methods), `adapters/memory_ledger.py` (whole file), `adapters/dynamo_ledger.py`, `tests/adapters/test_ledgers.py` (append)

**Produces:** `Ledger.claims(run_id) -> list[dict]`, `Ledger.run(run_id) -> dict` on both adapters; `InMemoryLedger.stored_claims` (renamed from `claims`); `adapters.dynamo_ledger._to_item`, `_from_item`, `DynamoLedger._query(table, run_id, sort_key_prefix=None)`. **Consumed by:** H2a (`store_claims`, `record_rejection`), H2b (`write_answer`), H4, H5 (the tests read `run()`).

- [ ] **Step 1: Failing tests.** Append to `tests/adapters/test_ledgers.py`:
```python


CLAIM_WITH_FIGURES = {"claim_id": "claim-1", "statement": "E4 is 102 days from cutover at 91.2 % reconciled",
                      "chain": [{"artefact": "reconciliation_results", "row_id": "RC-C3-E4-customers"}],
                      "figures": {"days": {"value": 102, "tool": "days_to_cutover", "field": "days_remaining"},
                                  "match_rate": {"value": 91.2, "tool": "records_reconciled", "field": "pct"}}}


def test_run_reads_back_scope_budget_cost_and_tokens(ledger, started_run, cfo_scope):
    ledger.add_cost(started_run, TOKENS_IN, TOKENS_OUT, FIRST_CALL_COST_USD)
    ledger.add_cost(started_run, TOKENS_IN, TOKENS_OUT, FIRST_CALL_COST_USD)
    run = ledger.run(started_run)
    assert run["run_id"] == started_run and run["scope"] == cfo_scope.model_dump(mode="json")
    assert (run["budget_usd"], run["tokens_in"], run["tokens_out"]) == (RUN_BUDGET_USD, 2 * TOKENS_IN, 2 * TOKENS_OUT)
    assert round(run["cost_usd"], MONEY_DECIMALS) == 2 * FIRST_CALL_COST_USD
    assert run["decisions"] == []


def test_claims_lists_every_claim_with_attempts_verdicts_and_status(ledger, started_run):
    ledger.put_claim(started_run, CLAIM_WITH_FIGURES)
    ledger.put_claim(started_run, {"claim_id": "claim-2", "statement": "second"})
    ledger.record_verdict(started_run, "claim-1", {"claim_id": "claim-1", "pass": False, "reason": "no row"})
    claims = ledger.claims(started_run)
    assert [stored["claim_id"] for stored in claims] == ["claim-1", "claim-2"]
    assert claims[0] == {"claim_id": "claim-1", "claim": CLAIM_WITH_FIGURES, "attempts": 1, "status": "rejected",
                         "verdicts": [{"claim_id": "claim-1", "pass": False, "reason": "no row"}]}
    assert (claims[1]["attempts"], claims[1]["verdicts"], claims[1]["status"]) == (0, [], "pending")


def test_claims_keep_their_numbers_exactly(ledger, started_run):
    ledger.put_claim(started_run, CLAIM_WITH_FIGURES)
    assert ledger.claim(started_run, "claim-1") == CLAIM_WITH_FIGURES
    figures = ledger.claims(started_run)[0]["claim"]["figures"]
    assert isinstance(figures["days"]["value"], int) and isinstance(figures["match_rate"]["value"], float)


def test_reading_an_unknown_run_raises(ledger):
    with pytest.raises(LedgerConflict):
        ledger.run("missing-run")
    with pytest.raises(LedgerConflict):
        ledger.claims("missing-run")
```
- [ ] **Step 2: Run them:** `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov 2>&1 | grep -E "^E  " | sort | uniq -c`. Expected, among the lines: `AttributeError: 'InMemoryLedger' object has no attribute 'run'`, `AttributeError: 'DynamoLedger' object has no attribute 'run'`, `TypeError: 'dict' object is not callable` (the in-memory `claims` attribute) and **`TypeError: Float types are not supported. Use Decimal types instead.`** (the DynamoDB bug this task fixes). Then `... 2>&1 | tail -1` shows `8 failed, 10 passed`.
- [ ] **Step 3: Implement the port.** In `tools/ports.py`, in `class Ledger`, insert before `def add_cost`:
```python
    def claims(self, run_id: str) -> list[dict]:
        """Every claim of the run in claim-ID order: {claim_id, claim, attempts, verdicts, status}."""
        ...

    def run(self, run_id: str) -> dict:
        """The run: {run_id, scope, budget_usd, cost_usd, tokens_in, tokens_out, decisions}."""
        ...

```
- [ ] **Step 4: Implement the in-memory adapter.** Replace the whole of `adapters/memory_ledger.py` with:
```python
"""In-memory Ledger for tests and local runs. The reference behaviour DynamoLedger must match.

Reads return deep copies, as DynamoDB does, so a caller can never change the ledger by editing what it read.
"""
from copy import deepcopy

from tools.constants import ClaimStatus
from tools.models import Scope
from tools.ports import LedgerConflict, claim_status_after, revised_claim


class InMemoryLedger:
    def __init__(self):
        self.runs: dict[str, dict] = {}
        self.stored_claims: dict[tuple[str, str], dict] = {}

    def start_run(self, run_id: str, scope: Scope, budget_usd: float) -> None:
        if run_id in self.runs:
            raise LedgerConflict(f"run {run_id} already exists")
        self.runs[run_id] = {"scope": scope.model_dump(mode="json"), "budget_usd": budget_usd, "cost_usd": 0.0,
                             "tokens_in": 0, "tokens_out": 0, "decisions": []}

    def put_claim(self, run_id: str, claim: dict) -> None:
        self._run(run_id)
        claim_key = (run_id, claim["claim_id"])
        if claim_key in self.stored_claims:
            raise LedgerConflict(f"claim {claim['claim_id']} already exists in run {run_id}")
        self.stored_claims[claim_key] = {"claim": deepcopy(claim), "attempts": 0, "verdicts": [],
                                         "status": ClaimStatus.PENDING}

    def revise_claim(self, run_id: str, claim_id: str, claim: dict) -> None:
        stored = self._claim(run_id, claim_id)
        stored["claim"] = revised_claim(claim_id, deepcopy(claim))
        stored["status"] = ClaimStatus.PENDING

    def record_verdict(self, run_id: str, claim_id: str, verdict: dict) -> int:
        stored = self._claim(run_id, claim_id)
        stored["attempts"] += 1
        stored["verdicts"].append(deepcopy(verdict))
        stored["status"] = claim_status_after(verdict)
        return stored["attempts"]

    def attempts(self, run_id: str, claim_id: str) -> int:
        return self._claim(run_id, claim_id)["attempts"]

    def claim(self, run_id: str, claim_id: str) -> dict:
        return deepcopy(self._claim(run_id, claim_id)["claim"])

    def claims(self, run_id: str) -> list[dict]:
        self._run(run_id)
        return [{"claim_id": claim_id, **deepcopy(stored)}
                for (stored_run_id, claim_id), stored in sorted(self.stored_claims.items())
                if stored_run_id == run_id]

    def run(self, run_id: str) -> dict:
        return {"run_id": run_id, **deepcopy(self._run(run_id))}

    def add_cost(self, run_id: str, tokens_in: int, tokens_out: int, cost_usd: float) -> None:
        run = self._run(run_id)
        run["tokens_in"] += tokens_in
        run["tokens_out"] += tokens_out
        run["cost_usd"] += cost_usd

    def budget_remaining(self, run_id: str) -> float:
        run = self._run(run_id)
        return run["budget_usd"] - run["cost_usd"]

    def _run(self, run_id: str) -> dict:
        if run_id not in self.runs:
            raise LedgerConflict.missing_run(run_id)
        return self.runs[run_id]

    def _claim(self, run_id: str, claim_id: str) -> dict:
        if (run_id, claim_id) not in self.stored_claims:
            raise LedgerConflict.missing_claim(run_id, claim_id)
        return self.stored_claims[(run_id, claim_id)]
```
- [ ] **Step 5: Implement the DynamoDB adapter.** In `adapters/dynamo_ledger.py`:
  - After the `_as_decimal` function, add:
    ```python


    def _to_item(value):
        """A value DynamoDB accepts: floats become Decimals (boto3 refuses floats), tuples become lists."""
        if isinstance(value, float):
            return _as_decimal(value)
        if isinstance(value, dict):
            return {key: _to_item(nested) for key, nested in value.items()}
        if isinstance(value, (list, tuple)):
            return [_to_item(nested) for nested in value]
        return value


    def _from_item(value):
        """The value as it was written: whole Decimals back to int, the others back to float."""
        if isinstance(value, Decimal):
            return int(value) if value.as_tuple().exponent >= 0 else float(value)
        if isinstance(value, dict):
            return {key: _from_item(nested) for key, nested in value.items()}
        if isinstance(value, list):
            return [_from_item(nested) for nested in value]
        return value
    ```
  - Directly before `def _run(self, run_id: str) -> dict:` (inside the class), add:
    ```python
        def _query(self, table, run_id: str, sort_key_prefix: str | None = None) -> list[dict]:
            """Every item of one run (optionally only sort keys with a prefix), in sort-key order, across pages."""
            from boto3.dynamodb.conditions import Key  # adapter-only dependency
            condition = Key(PARTITION_KEY).eq(run_id)
            if sort_key_prefix:
                condition = condition & Key(SORT_KEY).begins_with(sort_key_prefix)
            request = {"KeyConditionExpression": condition}
            items = []
            while True:
                page = table.query(**request)
                items += [_from_item(item) for item in page.get("Items", [])]
                if "LastEvaluatedKey" not in page:
                    return items
                request["ExclusiveStartKey"] = page["LastEvaluatedKey"]

    ```
  - In `start_run`, change `"tokens_in": 0, "tokens_out": 0, "created_at": int(time.time())})` to `"tokens_in": 0, "tokens_out": 0, "decisions": [], "created_at": int(time.time())})`.
  - In `put_claim`, change `"claim": claim,` to `"claim": _to_item(claim),`.
  - In `revise_claim`, change `{":claim": revised_claim(claim_id, claim),` to `{":claim": _to_item(revised_claim(claim_id, claim)),`.
  - In `record_verdict`, replace the `ExpressionAttributeValues=...` line with:
    ```python
                ExpressionAttributeValues={":one": 1, ":verdict": [_to_item(verdict)],
                                           ":status": claim_status_after(verdict)},
    ```
  - Replace the `claim` method with:
    ```python
        def claim(self, run_id: str, claim_id: str) -> dict:
            return _from_item(self._claim(run_id, claim_id)["claim"])

        def claims(self, run_id: str) -> list[dict]:
            self._run(run_id)
            return [{"claim_id": item[SORT_KEY].removeprefix(CLAIM_SORT_KEY_PREFIX), "claim": item["claim"],
                     "attempts": item["attempts"], "verdicts": item["verdicts"], "status": item["status"]}
                    for item in self._query(self.table, run_id, CLAIM_SORT_KEY_PREFIX)]

        def run(self, run_id: str) -> dict:
            run = _from_item(self._run(run_id))
            return {"run_id": run_id, "scope": run["scope"], "budget_usd": float(run["budget_usd"]),
                    "cost_usd": float(run["cost_usd"]), "tokens_in": int(run["tokens_in"]),
                    "tokens_out": int(run["tokens_out"]), "decisions": run.get("decisions", [])}
    ```
- [ ] **Step 6: Run:** `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov 2>&1 | tail -1`. Expected: `18 passed in …s`.
- [ ] **Step 7: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add tools/ports.py adapters/memory_ledger.py adapters/dynamo_ledger.py tests/adapters/test_ledgers.py
git commit -m "Ledger reads back runs and claims; DynamoDB keeps decimal figures (floats were refused)"
```
Expected: `212 passed` (start + 8), `TOTAL ... 96%`.

**Task done when:** `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov -k "numbers_exactly" 2>&1 | tail -1 | cut -d, -f1` prints `2 passed`; the full suite shows start + 8.

### Task 3: Rejected records, create-once, in their own table

**Files:** Modify `tools/ports.py`, `adapters/memory_ledger.py`, `adapters/dynamo_ledger.py`, `tests/adapters/test_ledgers.py` (append)

**Produces:** `Ledger.put_rejected(run_id: str, claim_id: str, verdicts: list[dict]) -> None`, `Ledger.rejected(run_id: str) -> list[dict]`; `InMemoryLedger.rejected_records`. **Consumed by:** H2a (`record_rejection`), H2b (`write_answer`), H4 (status pack).

- [ ] **Step 1: Failing tests.** Append:
```python


FIRST_REJECTION = {"claim_id": "claim-1", "pass": False, "reason": "no row supports it"}
SECOND_REJECTION = {"claim_id": "claim-1", "pass": False, "reason": "still unsupported",
                    "prompt": {"agent": "critic", "version": "1.0.0", "sha256": "abc"}}


def test_a_rejected_claim_keeps_its_content_and_every_verdict(ledger, started_run):
    ledger.put_claim(started_run, CLAIM_WITH_FIGURES)
    assert ledger.rejected(started_run) == []
    ledger.put_rejected(started_run, "claim-1", [FIRST_REJECTION, SECOND_REJECTION])
    assert ledger.rejected(started_run) == [{"claim_id": "claim-1", "claim": CLAIM_WITH_FIGURES,
                                             "verdicts": [FIRST_REJECTION, SECOND_REJECTION]}]


def test_a_rejection_is_create_once(ledger, started_run):
    ledger.put_claim(started_run, CLAIM_WITH_FIGURES)
    ledger.put_rejected(started_run, "claim-1", [FIRST_REJECTION])
    with pytest.raises(LedgerConflict):
        ledger.put_rejected(started_run, "claim-1", [])
    assert ledger.rejected(started_run)[0]["verdicts"] == [FIRST_REJECTION]


def test_only_a_stored_claim_can_be_rejected(ledger, started_run):
    with pytest.raises(LedgerConflict):
        ledger.put_rejected(started_run, "claim-never-stored", [FIRST_REJECTION])
    with pytest.raises(LedgerConflict):
        ledger.rejected("missing-run")
```
- [ ] **Step 2: Run:** `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov 2>&1 | tail -1`. Expected: `6 failed, 18 passed`, with `AttributeError: 'InMemoryLedger' object has no attribute 'put_rejected'` (and `'rejected'`, and the same for `DynamoLedger`).
- [ ] **Step 3: Port.** In `tools/ports.py`, insert before `def run(self, run_id: str) -> dict:`:
```python
    def put_rejected(self, run_id: str, claim_id: str, verdicts: list[dict]) -> None:
        """Create-once: copy a claim that reached the retry limit, with all its verdicts, to the rejected records."""
        ...

    def rejected(self, run_id: str) -> list[dict]:
        """The run's rejected records in claim-ID order: {claim_id, claim, verdicts}."""
        ...

```
- [ ] **Step 4: In-memory.** In `adapters/memory_ledger.py`, add `self.rejected_records: dict[tuple[str, str], dict] = {}` as the last line of `__init__`, and insert before `def run(self, run_id: str) -> dict:`:
```python
    def put_rejected(self, run_id: str, claim_id: str, verdicts: list[dict]) -> None:
        stored = self._claim(run_id, claim_id)
        if (run_id, claim_id) in self.rejected_records:
            raise LedgerConflict(f"claim {claim_id} is already in the rejected records of run {run_id}")
        self.rejected_records[(run_id, claim_id)] = {"claim": deepcopy(stored["claim"]), "verdicts": deepcopy(verdicts)}

    def rejected(self, run_id: str) -> list[dict]:
        self._run(run_id)
        return [{"claim_id": claim_id, **deepcopy(record)}
                for (record_run_id, claim_id), record in sorted(self.rejected_records.items())
                if record_run_id == run_id]

```
- [ ] **Step 5: DynamoDB.** In `adapters/dynamo_ledger.py`, insert before `def run(self, run_id: str) -> dict:`:
```python
    def put_rejected(self, run_id: str, claim_id: str, verdicts: list[dict]) -> None:
        stored = self._claim(run_id, claim_id)
        self._write(self.rejected_table.put_item, ConditionExpression=ITEM_IS_NEW,
                    Item={PARTITION_KEY: run_id, SORT_KEY: claim_id, "claim": stored["claim"],
                          "verdicts": _to_item(verdicts), "created_at": int(time.time())})

    def rejected(self, run_id: str) -> list[dict]:
        self._run(run_id)
        return [{"claim_id": item[SORT_KEY], "claim": item["claim"], "verdicts": item["verdicts"]}
                for item in self._query(self.rejected_table, run_id)]

```
- [ ] **Step 6: Run:** `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov 2>&1 | tail -1`. Expected: `24 passed in …s`.
- [ ] **Step 7: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add tools/ports.py adapters/memory_ledger.py adapters/dynamo_ledger.py tests/adapters/test_ledgers.py
git commit -m "Rejected records: create-once, the claim's stored content and every verdict, in their own table"
```
Expected: `218 passed` (start + 14), `TOTAL ... 96%`.

**Task done when:** `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov -k "rejected or rejection" 2>&1 | tail -1 | cut -d, -f1` prints `6 passed`.

### Task 4: The trace, `STEP#<n>`

**Files:** Modify `tools/ports.py`, `adapters/memory_ledger.py`, `adapters/dynamo_ledger.py`, `tests/adapters/test_ledgers.py` (append)

**Produces:** `Ledger.add_step(run_id: str, step: dict) -> int`, `Ledger.steps(run_id: str) -> list[dict]`; `adapters.dynamo_ledger.STEP_SORT_KEY_PREFIX = "STEP#"`, `STEP_NUMBER_DIGITS = 4`, `_step_key(run_id, step_number)`; `InMemoryLedger.trace_steps`. **Consumed by:** H2a (`record_step`), H2b (`write_answer` builds `AskResponse.trace`).

- [ ] **Step 1: Failing tests.** Append:
```python


ORCHESTRATOR_STEP = {"step": "run_orchestrator", "agent": "orchestrator",
                     "prompt": {"agent": "orchestrator", "version": "1.0.0", "sha256": "abc"}}
STORE_STEP = {"step": "store_claims", "agent": None, "prompt": None}
MORE_STEPS_THAN_ONE_DIGIT = 12


def test_steps_are_numbered_and_read_back_in_order(ledger, started_run):
    assert ledger.steps(started_run) == []
    assert ledger.add_step(started_run, ORCHESTRATOR_STEP) == 1
    assert ledger.add_step(started_run, STORE_STEP) == 2
    assert ledger.steps(started_run) == [ORCHESTRATOR_STEP, STORE_STEP]


def test_step_order_survives_more_than_nine_steps(ledger, started_run):
    for step_number in range(1, MORE_STEPS_THAN_ONE_DIGIT + 1):
        ledger.add_step(started_run, {"step": f"step-{step_number}", "agent": None, "prompt": None})
    assert [step["step"] for step in ledger.steps(started_run)] == [
        f"step-{step_number}" for step_number in range(1, MORE_STEPS_THAN_ONE_DIGIT + 1)]


def test_steps_need_an_existing_run(ledger):
    with pytest.raises(LedgerConflict):
        ledger.add_step("missing-run", STORE_STEP)
    with pytest.raises(LedgerConflict):
        ledger.steps("missing-run")
```
- [ ] **Step 2: Run:** `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov 2>&1 | tail -1`. Expected: `6 failed, 24 passed`, with `AttributeError: 'InMemoryLedger' object has no attribute 'steps'` / `'add_step'` (and `DynamoLedger`).
- [ ] **Step 3: Port.** In `tools/ports.py`, insert before `def run(self, run_id: str) -> dict:`:
```python
    def add_step(self, run_id: str, step: dict) -> int:
        """Append a trace step {step, agent, prompt}; return its number (1, 2, ...)."""
        ...

    def steps(self, run_id: str) -> list[dict]:
        """The run's trace steps in the order they were added."""
        ...

```
- [ ] **Step 4: In-memory.** In `adapters/memory_ledger.py`: add `self.trace_steps: dict[str, list[dict]] = {}` as the last line of `__init__`; add `self.trace_steps[run_id] = []` as the last line of `start_run`; insert before `def run(self, run_id: str) -> dict:`:
```python
    def add_step(self, run_id: str, step: dict) -> int:
        self._run(run_id)
        self.trace_steps[run_id].append(deepcopy(step))
        return len(self.trace_steps[run_id])

    def steps(self, run_id: str) -> list[dict]:
        self._run(run_id)
        return deepcopy(self.trace_steps[run_id])

```
- [ ] **Step 5: DynamoDB.** In `adapters/dynamo_ledger.py`:
  - After `CLAIM_SORT_KEY_PREFIX = "CLAIM#"` add:
    ```python
    STEP_SORT_KEY_PREFIX = "STEP#"
    STEP_NUMBER_DIGITS = 4   # STEP#0001: zero-padded so the sort key orders steps by number
    ```
  - Before `def _run_key(` add:
    ```python
    def _step_key(run_id: str, step_number: int) -> dict:
        return {PARTITION_KEY: run_id, SORT_KEY: f"{STEP_SORT_KEY_PREFIX}{step_number:0{STEP_NUMBER_DIGITS}d}"}


    ```
  - In `start_run`, replace `"tokens_in": 0, "tokens_out": 0, "decisions": [], "created_at": int(time.time())})` with:
    ```python
                              "tokens_in": 0, "tokens_out": 0, "decisions": [], "step_count": 0,
                              "created_at": int(time.time())})
    ```
  - Insert before `def run(self, run_id: str) -> dict:`:
    ```python
        def add_step(self, run_id: str, step: dict) -> int:
            response = self._write(self.table.update_item, ConditionExpression=ITEM_EXISTS, Key=_run_key(run_id),
                                   UpdateExpression="ADD step_count :one", ExpressionAttributeValues={":one": 1},
                                   ReturnValues="UPDATED_NEW")
            step_number = int(response["Attributes"]["step_count"])
            self._write(self.table.put_item, ConditionExpression=ITEM_IS_NEW,
                        Item={**_step_key(run_id, step_number), "step": _to_item(step), "created_at": int(time.time())})
            return step_number

        def steps(self, run_id: str) -> list[dict]:
            self._run(run_id)
            return [item["step"] for item in self._query(self.table, run_id, STEP_SORT_KEY_PREFIX)]

    ```
- [ ] **Step 6: Run:** `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov 2>&1 | tail -1`. Expected: `30 passed in …s`.
- [ ] **Step 7: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add tools/ports.py adapters/memory_ledger.py adapters/dynamo_ledger.py tests/adapters/test_ledgers.py
git commit -m "Ledger keeps the trace: numbered STEP#nnnn items, read back in order"
```
Expected: `224 passed` (start + 20), `TOTAL ... 96%`.

**Task done when:** `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov -k steps 2>&1 | tail -1 | cut -d, -f1` prints `6 passed`.

### Task 5: The publish task token and the publish decisions

**Files:** Modify `tools/ports.py`, `adapters/memory_ledger.py`, `adapters/dynamo_ledger.py`, `tests/adapters/test_ledgers.py` (append)

**Produces:** `Ledger.put_task_token(run_id: str, task_token: str) -> None`, `Ledger.task_token(run_id: str) -> str | None`, `Ledger.record_decision(run_id: str, decision: dict) -> None`; `adapters.dynamo_ledger.TASK_SORT_KEY = "TASK"`, `_task_key(run_id)`; `InMemoryLedger.task_tokens`. **Consumed by:** H4 (`store_task_token`, `decide`, `write_status_pack`).

- [ ] **Step 1: Failing tests.** Append:
```python


TASK_TOKEN = "AQB8AAAAKgAAAAMAAAAAAAAAAexample-task-token"
SEND_BACK = {"decision": "send_back", "note": "cite the runbook step", "user_id": "user-delivery-lead",
             "decided_at": "2026-10-14T15:00:00+00:00"}
APPROVE = {"decision": "approve", "note": "", "user_id": "user-delivery-lead",
           "decided_at": "2026-10-14T15:05:00+00:00"}


def test_the_task_token_is_stored_once_by_run_id(ledger, started_run):
    assert ledger.task_token(started_run) is None
    ledger.put_task_token(started_run, TASK_TOKEN)
    assert ledger.task_token(started_run) == TASK_TOKEN
    with pytest.raises(LedgerConflict):
        ledger.put_task_token(started_run, "a-second-token")
    assert ledger.task_token(started_run) == TASK_TOKEN


def test_task_tokens_need_an_existing_run(ledger):
    with pytest.raises(LedgerConflict):
        ledger.put_task_token("missing-run", TASK_TOKEN)
    with pytest.raises(LedgerConflict):
        ledger.task_token("missing-run")


def test_publish_decisions_are_appended_to_the_run(ledger, started_run):
    ledger.record_decision(started_run, SEND_BACK)
    ledger.record_decision(started_run, APPROVE)
    assert ledger.run(started_run)["decisions"] == [SEND_BACK, APPROVE]
    with pytest.raises(LedgerConflict):
        ledger.record_decision("missing-run", APPROVE)
```
- [ ] **Step 2: Run:** `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov 2>&1 | tail -1`. Expected: `6 failed, 30 passed`, with `AttributeError: ... object has no attribute 'task_token'` / `'put_task_token'` / `'record_decision'`.
- [ ] **Step 3: Port.** In `tools/ports.py`, insert before `def run(self, run_id: str) -> dict:`:
```python
    def put_task_token(self, run_id: str, task_token: str) -> None:
        """Create-once: the publish machine's approval task token, keyed by run ID (/approve takes run_id)."""
        ...

    def task_token(self, run_id: str) -> str | None:
        """The run's publish task token, or None while no publish is waiting for approval."""
        ...

    def record_decision(self, run_id: str, decision: dict) -> None:
        """Append a publish decision {decision, note, user_id, decided_at} to the run (approvals and send-backs)."""
        ...

```
  And replace the first lines of the `Ledger` docstring, from `"""The run ledger: claims, verdicts, the per-claim attempt counter and per-run cost.` to `Integrity rule: runs and claims are create-once. Re-creating one raises LedgerConflict, so`, with:
```python
    """The run ledger: claims, verdicts, the per-claim attempt counter, per-run cost, the trace, rejected records,
    the publish task token and the publish decisions.

    Implementations: adapters.memory_ledger.InMemoryLedger, adapters.dynamo_ledger.DynamoLedger.

    Integrity rule: runs, claims, rejected records and task tokens are create-once. Re-creating one raises
    LedgerConflict, so
```
  (the docstring continues unchanged with `neither the attempt counter nor the spent cost can be reset. ...`).
- [ ] **Step 4: In-memory.** Add `self.task_tokens: dict[str, str] = {}` as the last line of `__init__`, and insert before `def run(self, run_id: str) -> dict:`:
```python
    def put_task_token(self, run_id: str, task_token: str) -> None:
        self._run(run_id)
        if run_id in self.task_tokens:
            raise LedgerConflict(f"run {run_id} already has a publish task token")
        self.task_tokens[run_id] = task_token

    def task_token(self, run_id: str) -> str | None:
        self._run(run_id)
        return self.task_tokens.get(run_id)

    def record_decision(self, run_id: str, decision: dict) -> None:
        self._run(run_id)["decisions"].append(deepcopy(decision))

```
- [ ] **Step 5: DynamoDB.** After `RUN_SORT_KEY = "RUN"` add `TASK_SORT_KEY = "TASK"`; before `def _run_key(` add:
```python
def _task_key(run_id: str) -> dict:
    return {PARTITION_KEY: run_id, SORT_KEY: TASK_SORT_KEY}


```
and insert before `def run(self, run_id: str) -> dict:`:
```python
    def put_task_token(self, run_id: str, task_token: str) -> None:
        self._run(run_id)
        self._write(self.table.put_item, ConditionExpression=ITEM_IS_NEW,
                    Item={**_task_key(run_id), "task_token": task_token, "created_at": int(time.time())})

    def task_token(self, run_id: str) -> str | None:
        self._run(run_id)
        return self._get(_task_key(run_id)).get("task_token")

    def record_decision(self, run_id: str, decision: dict) -> None:
        self._write(self.table.update_item, ConditionExpression=ITEM_EXISTS, Key=_run_key(run_id),
                    UpdateExpression="SET decisions = list_append(if_not_exists(decisions, :none), :decision)",
                    ExpressionAttributeValues={":none": [], ":decision": [_to_item(decision)]})

```
- [ ] **Step 6: Run:** `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov 2>&1 | tail -1`. Expected: `36 passed in …s`.
- [ ] **Step 7: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
uv run --locked pytest tests/test_architecture.py tests/test_code_style.py --no-cov 2>&1 | tail -1
git add tools/ports.py adapters/memory_ledger.py adapters/dynamo_ledger.py tests/adapters/test_ledgers.py
git commit -m "Ledger stores the publish task token once by run ID and appends each publish decision to the run"
```
Expected: `230 passed` (start + 26), `TOTAL ... 96%`; the guards line ends in `passed`.

**Task done when:** `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov 2>&1 | tail -1` prints `36 passed`; `grep -c "def " tools/ports.py` is 9 higher than on `develop`.

### Task 6: Docs, then review and PR
- [ ] **Step 1: `HANDOFF.md`.** Under `## What's real`, replace the line `- TODO: agent loop, critic, ledger, approval flow, as each lands.` with:
```markdown
- The run ledger (`tools/ports.py` `Ledger`; in-memory and DynamoDB adapters, one shared test suite on moto): create-once runs, claims, rejected records (their own table) and publish task tokens; the attempt counter and the spent cost can't be reset; the trace (`STEP#n`) and every publish decision are kept per run.
- TODO: agent loop, critic, approval flow, as each lands.
```
- [ ] **Step 2: `docs/TEAM_PLAN.md` §3.** Replace the line that starts `**Run ledger (DynamoDB):**` with:
```markdown
**Run ledger (DynamoDB):** `pk=run_id`, `sk=RUN | CLAIM#<id> | STEP#<nnnn> | TASK`; claim items hold `claim`, `verdicts[]`, `attempts`, `status`; the RUN item holds `scope`, `budget_usd`, `cost_usd`, `tokens_in`, `tokens_out`, `step_count`, `decisions[]`; `TASK` holds the publish task token. **Rejected records** are a second table (`REJECTED_TABLE`): `pk=run_id`, `sk=claim_id`, `claim`, `verdicts[]`.
```
  (`docs/TEAM_PLAN.md` is Patrick's: say so in the PR body.)
- [ ] **Step 3: Doc guard and commit**
```bash
uv run --locked pytest tests/test_dependencies.py --no-cov 2>&1 | tail -1
git add HANDOFF.md docs/TEAM_PLAN.md
git commit -m "Document the ledger item layout and the rejected-records table"
```
Expected: `4 passed`.
- [ ] **Step 4: Review Focus** by hand; write each result in `.superpowers/ledger-H1.md`.
- [ ] **Step 5:** `git diff develop --stat`. Expected: exactly `HANDOFF.md`, `adapters/__init__.py`, `adapters/dynamo_ledger.py`, `adapters/memory_ledger.py`, `docs/TEAM_PLAN.md`, `tests/adapters/test_ledgers.py`, `tools/ports.py` (7 files).
- [ ] **Step 6: With Huvison's OK only:** `git push -u origin feature/ledger-extensions`; open the PR to `develop`, titled "Ledger extensions: read-backs, rejected records, trace, task tokens, decisions (H1)", body: what changed, `230 passed` (or start + 26), the rulings, and "Michael: the rejected-records table uses `pk`/`sk` strings like the ledger; Yaw: `Query` on both tables". No attribution lines.
- [ ] **Step 7:** Update [[Build order]]: H1 → `in review (PR #nn)`; after the merge, `merged`. Tell Michael (LedgerStack: second table, same key schema) and Yaw (IAM: `Query` on both tables).

**Task done when:** the PR is open to `develop` with the test count in its body, and the [[Build order]] row says `in review (PR #nn)`.

## Done means
- [ ] **Both adapters implement the nine new methods.** *Verify:* on `develop`, `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov 2>&1 | tail -1` prints `36 passed`.
- [ ] **Decimal figures survive DynamoDB.** *Verify:* `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov -k numbers_exactly 2>&1 | tail -1 | cut -d, -f1` prints `2 passed`.
- [ ] **Create-once holds for rejected records and task tokens.** *Verify:* `uv run --locked pytest tests/adapters/test_ledgers.py --no-cov -k "create_once or stored_once" 2>&1 | tail -1 | cut -d, -f1` prints `4 passed`.
- [ ] **The settings wire the second table.** *Verify:* `grep -n "settings.rejected_table" adapters/__init__.py` prints one line.
- [ ] **Nothing else broke.** *Verify:* `uv run --locked pytest` on `develop` right after the merge: start + 26 passed, `TOTAL` ≥ 96%.
- [ ] **The layout is documented.** *Verify:* `grep -n "STEP#<nnnn>" docs/TEAM_PLAN.md` and `grep -n "rejected records (their own table)" HANDOFF.md` each print one line.
- [ ] **Merged.** *Verify:* the PR shows "merged" into `develop`, and [[Build order]] row H1 says `merged`.

## Never
- Add a ledger test that runs on one adapter only.
- Allow an overwrite of a run, claim, rejected record or task token, or reset `attempts` or `cost_usd`.
- Pass claim content into `put_rejected` (it copies the stored claim).
- Import boto3 in `tools/`.
- Push to `develop` or `main`, or add attribution lines.

Related: [[H1 - Ledger extensions - spec]], [[Build order]], [[How to execute a plan]]
