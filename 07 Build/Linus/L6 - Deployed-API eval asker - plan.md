---
tags: [build, plan, area/evals]
id: L6
owner: Linus
spec: "[[L6 - Deployed-API eval asker - spec]]"
status: ready
updated: 2026-10-14
---
# L6: the deployed-API eval asker (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[L6 - Deployed-API eval asker - spec]]: **the authority**, including the token and refusal rules.
3. The repo's `evals/run.py` docstring (the asker contract) and `tests/evals/test_run.py` (how askers are tested).
4. [[Abdul - evals, Cognito, docs]] (users, results write-up), [[Deploy and demo checks]], [[Handling security findings]].
5. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[Problem statement]], [[Judging rubric]], [[Pitch track grading rubric]], [[Hackathon guideline]]); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Linus. Never invent a name, a shape or a rule.

**Goal:** `uv run python -m evals.run --asker evals.api_asker:ask` asks the 14 questions of the deployed API as the right users and records honest results.

**Architecture:** one asker module at the edge of the eval runner. It reads settings through `config.get_settings()`, builds the body with C1's `AskRequest`, and talks HTTP with the standard library. The runner (`evals/run.py`) is unchanged.

**Tech stack:** Python 3.11, `urllib.request`, pydantic 2, pytest, uv. Tests fake `urllib.request.urlopen`; no network. **Dry-run status:** Tasks 1–2 ran on a develop with only C1 (counts below are real); Task 3 needs AWS (L3, Y1, M3* deployed): "verify in AWS".

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: **`feature/eval-api-asker`** from an up-to-date `develop`. Tasks 1–2 need only C1 merged; Task 3 needs L3, Y1 and M3* **deployed**.
- **Start state:** `uv run --locked pytest` → START. With only C1 merged it's **213 passed**, `TOTAL` **96%** (the dry-run base); by Day 2 more items will have merged: write your count in the ledger as START, and read each `N passed` below as START + the same increase.
- **AWS:** `eu-west-1` only; Bedrock `eu.*` inference profiles only, never `global.*` (D-002). Synthetic data only. **No secrets** anywhere: code, tests, fixtures, the repo, the vault, Slack, commit messages.
- **Clean code (enforced by tests):** no single-character names anywhere (comprehensions, lambdas and `except ... as` included); no magic numbers or strings, so every limit, code and key is a named constant; settings only in `config.py`; domain constants only in `tools/constants.py`; descriptive names.
- **The core (`tools/`) never imports** boto3, Strands, `adapters`, `config` or `os` (`tests/test_architecture.py`).
- **Agents reach data only through `tools/agent_tools.py`.** Scope is never a tool argument and never comes from a request body, a query string or a model. Prompts live only in `agents/prompts/<agent>.txt`, versioned and locked (`uv run python scripts/lock_prompts.py`).
- **Never weaken a security rule** (the scope gate, the create-once ledger, the fail-closed critic, the `<evidence>` escaping) to make a test pass.
- **Tests** live in `tests/`, mirroring the code; run `uv run --locked pytest` from the repo root. Coverage must not drop below the start state. **No layout or "meta" guard tests**: test behaviour, not where files sit.
- **Git:** small commits, one per task, with the messages given. **No `Co-Authored-By` and no "Generated with" lines.** Never push to `develop` or `main`; the PR goes to `develop` after the owner's OK, and Patrick merges.
- **Stay in your folders** (`docs/TEAM_PLAN.md` §2, workstream 3: `infra/functions/api.py` *(new)*, `infra/functions/scope.py` *(new)*, `tests/infra/functions/` *(new)*, `tools/metrics.py`, `tools/queries.py`, `tools/agent_tools.py`, `tools/claims.py`, `agents/blocker_analyst.py` *(new)*, `agents/prompts/blocker_analyst.txt` *(new)*, `scripts/export_summary.py` *(new)*, the eval runner). Any other file this plan touches is named in its task, with the owner who must review it.
- **Tokens are secrets for an hour.** The tokens file lives outside the repo (for example `~/eval-id-tokens.json`), is never committed, never pasted into Slack or the vault, and deleted after the run. Check `git status` before every commit.
- **Shared files touched:** `config.py` and `tests/test_config.py` (Patrick's: two settings; he reviews), `EVALS.md` (one paragraph; tell Abdul).

## Review Focus (check by hand at the end)
1. **No token in any file the run writes.** After the Task 3 run, `grep -c "eyJ" evals/results/run-*.json` (JWTs start with `eyJ`) prints `0` for the new file.
2. **Only `out_of_scope` is a refusal.** Read the last lines of `ask`: a 403 `forbidden` raises `AskFailed`.
3. **https only.** The base URL check runs before any request; `file://` and `http://` are refused (tested). The `# nosec B310` comment says why.
4. **Honest failures.** Q05, Q08 and Q09 show `fail` with `InjectNeedsTheLocalAsker` / `NoEntityToAsk` in the results; that's expected and must be written up as such in `EVALS.md` (Abdul), never hidden.
5. **Timeout vs the gateway.** A question that takes longer than 29 s comes back as a 504 → `AskFailed`; note in the results write-up which questions did.

---

### Task 1: The two settings

**Files:**
- Modify: `config.py`, `tests/test_config.py`

**Produces:** `Settings.eval_api_base_url: str | None` (`EVAL_API_BASE_URL`), `Settings.eval_id_tokens_file: str | None` (`EVAL_ID_TOKENS_FILE`), both default `None`. **Consumes:** C1's `config.py`. **Consumed by:** Task 2.

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/eval-api-asker
mkdir -p .superpowers && printf '# Ledger: L6 deployed-API eval asker\n' > .superpowers/ledger-L6.md
```
Expected: START (`213 passed` on the dry-run base), `TOTAL ... 96%`.

- [ ] **Step 2: Write the failing tests.** In `tests/test_config.py`:
  - in `NEW_SETTING_DEFAULTS`, replace `"user_pool_id": None, "user_pool_client_id": None,` with `"user_pool_id": None, "user_pool_client_id": None, "eval_api_base_url": None, "eval_id_tokens_file": None,`;
  - in `ENVIRONMENT_VARIABLES`, after the `"user_pool_id": ...` line, add:
    ```python
        "eval_api_base_url": ("EVAL_API_BASE_URL", "https://example.cloudfront.net/api"),
        "eval_id_tokens_file": ("EVAL_ID_TOKENS_FILE", "/home/someone/eval-id-tokens.json"),
    ```
- [ ] **Step 3: Run them and watch them fail**
```bash
uv run --locked pytest tests/test_config.py --no-cov 2>&1 | tail -1
uv run --locked pytest tests/test_config.py --no-cov 2>&1 | grep -E "^E  " | sort -u
```
Expected: `3 failed, 11 passed` (L1 added the two `DEMO_ROLE` tests; `3 failed, 9 passed` on C1 alone); the errors are `AttributeError: 'Settings' object has no attribute 'eval_api_base_url'` (and `... 'eval_id_tokens_file'`).
- [ ] **Step 4: Implement.** In `config.py`:
  - in the `Settings` dataclass, after `user_pool_client_id: str | None`, add:
```python
    eval_api_base_url: str | None
    eval_id_tokens_file: str | None
```
  - in `get_settings()`, after `user_pool_client_id=os.environ.get("USER_POOL_CLIENT_ID"),`, add:
```python
        eval_api_base_url=os.environ.get("EVAL_API_BASE_URL"),        # the deployed-API eval asker (evals/api_asker.py)
        eval_id_tokens_file=os.environ.get("EVAL_ID_TOKENS_FILE"),    # a local file outside the repo; never committed
```
- [ ] **Step 5: Run them and watch them pass**
```bash
uv run --locked pytest tests/test_config.py --no-cov 2>&1 | tail -1
```
Expected: `14 passed` (`12 passed` on C1 alone).
- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add config.py tests/test_config.py
git commit -m "Settings for the deployed-API eval asker: the API base URL and a local ID-token file"
```
Expected: START + 2 (`215 passed`), `TOTAL ... 96%`.

**Task done when:** `uv run --locked pytest tests/test_config.py --no-cov` prints `14 passed` (`12 passed` on C1 alone); `git show --stat HEAD` lists only `config.py` and `tests/test_config.py`.

### Task 2: `evals/api_asker.py` *(new)*

**Files:**
- Create: `evals/api_asker.py`, `tests/evals/test_api_asker.py` *(new)*
- Modify: `EVALS.md` (one paragraph)

**Produces:** `evals.api_asker.ask(case_input: EvalInput, scope: Scope, _repository) -> dict`; `post_ask(url: str, body: bytes, id_token: str | None) -> tuple[int, dict]`; `id_token_for(scope: Scope, tokens_file: str | None) -> str | None`; `scope_key(scope: Scope) -> str`; exceptions `DeployedApiCannotAsk`, `InjectNeedsTheLocalAsker`, `NoEntityToAsk`, `NoTokenForScope`, `AskFailed`. **Consumes:** Task 1; `evals.run.EvalInput`, `REFUSED_STATUS_CODE`, `load_cases`, `scope_for`, `run_case`; `tools.api_schema.AskRequest` (C1); `tools.agent_tools.ERROR_OUT_OF_SCOPE`. **Consumed by:** the Day 2 eval run (Task 3), Abdul (A5).

- [ ] **Step 1: Write the failing test.** Create `tests/evals/test_api_asker.py`:
```python
"""The deployed-API eval asker (evals/api_asker.py) against a fake HTTP layer: what it sends and how it maps replies."""
import io
import json
import urllib.error
import urllib.request

import pytest

from config import DEFAULT_TENANT_ID, get_settings
from evals import api_asker
from evals import run as runner

API_BASE_URL = "https://portal.example.cloudfront.net/api"
ENTITY_FOUR_LEAD_TOKEN = "id-token-e4-lead"
CFO_TOKEN = "id-token-cfo"
E4_BLOCKER_BULLETS = [
    {"text": "Customer master reconciles at 91.2 % against the 98 % target.",
     "citations": [{"artefact": "reconciliation_results", "row_id": "RC-C3-E4-customers"}]},
    {"text": "212 customers are rejected for invalid tax IDs.",
     "citations": [{"artefact": "defect_log", "row_id": "DEF-0412"}]},
    {"text": "Runbook step RB-010 needs that reconciliation to pass.",
     "citations": [{"artefact": "cutover_runbook", "row_id": "E4#RB-010"}]},
]
ANSWER_BODY = {"run_id": "run-1", "answer": {"headline": "E4 is blocked", "bullets": E4_BLOCKER_BULLETS,
                                             "rejected_count": 0},
               "rejected": [], "cost_usd": 0.05, "partial": False, "partial_reason": None, "trace": []}
OUT_OF_SCOPE_BODY = {"error": "out_of_scope", "detail": "entity E2 is outside this user's scope"}
FORBIDDEN_BODY = {"error": "forbidden", "detail": "a user needs exactly one group"}
HTTP_OK, HTTP_FORBIDDEN, HTTP_SERVER_ERROR = 200, 403, 500


class FakeResponse(io.BytesIO):
    def __init__(self, status: int, body: dict):
        super().__init__(json.dumps(body).encode())
        self.status = status


class FakeApi:
    """Stands in for urllib.request.urlopen: records each request and replies with one status and body."""

    def __init__(self, status: int, body: dict):
        self.status, self.body, self.requests = status, body, []

    def __call__(self, request, timeout):
        self.requests.append(request)
        if self.status == HTTP_OK:
            return FakeResponse(self.status, self.body)
        error_body = io.BytesIO(json.dumps(self.body).encode())
        raise urllib.error.HTTPError(request.full_url, self.status, "error", {}, error_body)


@pytest.fixture
def cases_by_id():
    return {case.input.id: case for case in runner.load_cases()}


@pytest.fixture
def deployed_api(monkeypatch, tmp_path):
    """The asker's settings: the API's base URL and a tokens file outside the repo, one ID token per eval scope."""
    tokens_file = tmp_path / "eval-id-tokens.json"
    tokens_file.write_text(json.dumps({"cfo:*": CFO_TOKEN, "entity_lead:E4": ENTITY_FOUR_LEAD_TOKEN}), encoding="utf-8")
    monkeypatch.setenv("EVAL_API_BASE_URL", API_BASE_URL)
    monkeypatch.setenv("EVAL_ID_TOKENS_FILE", str(tokens_file))
    get_settings.cache_clear()
    yield monkeypatch
    get_settings.cache_clear()


def replying(monkeypatch, status: int, body: dict) -> FakeApi:
    fake_api = FakeApi(status, body)
    monkeypatch.setattr(urllib.request, "urlopen", fake_api)
    return fake_api


def ask(case):
    return api_asker.ask(case.input, runner.scope_for(case.input, DEFAULT_TENANT_ID), None)


def test_a_question_is_posted_to_ask_with_the_scopes_id_token(deployed_api, cases_by_id):
    fake_api = replying(deployed_api, HTTP_OK, ANSWER_BODY)
    assert ask(cases_by_id["Q01"]) == ANSWER_BODY
    [request] = fake_api.requests
    assert (request.full_url, request.get_method()) == (f"{API_BASE_URL}/ask", "POST")
    assert request.get_header("Authorization") == f"Bearer {CFO_TOKEN}"
    assert json.loads(request.data) == {"entity_id": "E4", "question": cases_by_id["Q01"].input.question}


def test_an_out_of_scope_403_is_a_refusal(deployed_api, cases_by_id):
    fake_api = replying(deployed_api, HTTP_FORBIDDEN, OUT_OF_SCOPE_BODY)
    response = ask(cases_by_id["Q11"])
    assert (response["refused"], response["status_code"], response["error"]) == (True, HTTP_FORBIDDEN, "out_of_scope")
    assert fake_api.requests[0].get_header("Authorization") == f"Bearer {ENTITY_FOUR_LEAD_TOKEN}"


@pytest.mark.parametrize("status, body", [(HTTP_FORBIDDEN, FORBIDDEN_BODY),
                                          (HTTP_SERVER_ERROR, {"message": "Internal Server Error"})],
                         ids=["forbidden_is_not_a_scope_refusal", "server_error"])
def test_any_other_error_fails_the_question(deployed_api, cases_by_id, status, body):
    replying(deployed_api, status, body)
    with pytest.raises(api_asker.AskFailed, match=str(status)):
        ask(cases_by_id["Q11"])


@pytest.mark.parametrize("case_id, error_type", [("Q08", api_asker.InjectNeedsTheLocalAsker),
                                                 ("Q09", api_asker.InjectNeedsTheLocalAsker),
                                                 ("Q05", api_asker.NoEntityToAsk)])
def test_questions_the_deployed_api_cannot_ask_raise_before_sending(deployed_api, cases_by_id, case_id, error_type):
    fake_api = replying(deployed_api, HTTP_OK, ANSWER_BODY)
    with pytest.raises(error_type):
        ask(cases_by_id[case_id])
    assert fake_api.requests == []


@pytest.mark.parametrize("base_url", ["", "http://portal.example.cloudfront.net/api", "file:///etc/passwd"],
                         ids=["unset", "plain_http", "file"])
def test_the_base_url_must_be_https(deployed_api, cases_by_id, base_url):
    deployed_api.setenv("EVAL_API_BASE_URL", base_url)
    get_settings.cache_clear()
    with pytest.raises(api_asker.DeployedApiCannotAsk, match="https"):
        ask(cases_by_id["Q01"])


def test_a_scope_without_a_token_in_the_file_is_refused(deployed_api, cases_by_id, tmp_path):
    other_tokens = tmp_path / "cfo-only.json"
    other_tokens.write_text(json.dumps({"cfo:*": CFO_TOKEN}), encoding="utf-8")
    deployed_api.setenv("EVAL_ID_TOKENS_FILE", str(other_tokens))
    get_settings.cache_clear()
    with pytest.raises(api_asker.NoTokenForScope, match="entity_lead:E4"):
        ask(cases_by_id["Q11"])


def test_without_a_tokens_file_no_token_is_sent(deployed_api, cases_by_id):
    deployed_api.delenv("EVAL_ID_TOKENS_FILE")
    get_settings.cache_clear()
    fake_api = replying(deployed_api, HTTP_OK, ANSWER_BODY)
    ask(cases_by_id["Q01"])
    assert fake_api.requests[0].get_header("Authorization") is None


def test_the_runner_scores_the_deployed_answers(deployed_api, cases_by_id, repository):
    replying(deployed_api, HTTP_FORBIDDEN, OUT_OF_SCOPE_BODY)
    assert runner.run_case(cases_by_id["Q11"], repository, api_asker.ask, DEFAULT_TENANT_ID)["status"] == "pass"
    replying(deployed_api, HTTP_OK, ANSWER_BODY)
    assert runner.run_case(cases_by_id["Q01"], repository, api_asker.ask, DEFAULT_TENANT_ID)["status"] == "pass"
    q08 = runner.run_case(cases_by_id["Q08"], repository, api_asker.ask, DEFAULT_TENANT_ID)
    assert q08["status"] == "fail" and "agent loop answered" in q08["detail"]
```
- [ ] **Step 2: Run it and watch it fail**
```bash
uv run --locked pytest tests/evals/test_api_asker.py --no-cov 2>&1 | grep -E "^E  "
```
Expected: `E   ImportError: cannot import name 'api_asker' from 'evals' (unknown location)`.
- [ ] **Step 3: Implement.** Create `evals/api_asker.py`:
```python
"""Eval asker for the deployed API: sends each eval question to POST /ask on AWS (the asker contract in evals/run.py).

    EVAL_API_BASE_URL=https://<portal domain>/api EVAL_ID_TOKENS_FILE=~/eval-id-tokens.json \\
        uv run python -m evals.run --asker evals.api_asker:ask

EVAL_ID_TOKENS_FILE is a JSON file OUTSIDE the repo, never committed: one Cognito ID token per eval scope, keyed
role:entity_ids, e.g. {"cfo:*": "<ID token>", "entity_lead:E4": "<ID token>"}. Without it, no token is sent, and only
an AUTH_MODE=none deployment answers. ID tokens expire after an hour: fetch fresh ones before each run.

Replies: 200 → the AskResponse body. 403 out_of_scope → that body plus "refused": true and "status_code": 403 (Q11).
Any other status raises AskFailed. Questions this asker can't send raise before anything is sent, so the runner records
them as failed: an `inject` condition (Q08, Q09; the API has no fault switch, by design: use infra.functions.local:ask) and a
question without an entity (POST /ask needs one).
"""
import json
import urllib.error
import urllib.request
from pathlib import Path

from config import get_settings
from evals.run import REFUSED_STATUS_CODE, EvalInput
from tools.agent_tools import ERROR_OUT_OF_SCOPE
from tools.api_schema import AskRequest
from tools.models import Scope

ASK_PATH = "/ask"
HTTPS_SCHEME = "https://"
HTTP_OK = 200
REQUEST_TIMEOUT_SECONDS = 35   # API Gateway ends synchronous calls at 29 s; wait a little longer so its 504 arrives
SCOPE_KEY_SEPARATOR = ":"
ENTITY_IDS_SEPARATOR = ","
JSON_CONTENT_TYPE = "application/json"
BEARER_PREFIX = "Bearer "
TEXT_ENCODING = "utf-8"
ERROR_FIELD = "error"


class DeployedApiCannotAsk(ValueError):
    """This question or this configuration can't be sent to the deployed API."""


class InjectNeedsTheLocalAsker(DeployedApiCannotAsk):
    """Q08 and Q09 plant a fault; only the local asker (infra.functions.local:ask) can, because the API has no fault switch."""


class NoEntityToAsk(DeployedApiCannotAsk):
    """POST /ask needs an entity_id, and this question has none."""


class NoTokenForScope(DeployedApiCannotAsk):
    """The tokens file has no ID token for this eval scope."""


class AskFailed(RuntimeError):
    """POST /ask answered with a status that is neither an answer nor a scope refusal."""


def scope_key(scope: Scope) -> str:
    return f"{scope.role}{SCOPE_KEY_SEPARATOR}{ENTITY_IDS_SEPARATOR.join(scope.entity_ids)}"


def id_token_for(scope: Scope, tokens_file: str | None) -> str | None:
    if not tokens_file:
        return None
    tokens = json.loads(Path(tokens_file).expanduser().read_text(encoding=TEXT_ENCODING))
    if scope_key(scope) not in tokens:
        raise NoTokenForScope(f"no ID token for {scope_key(scope)} in EVAL_ID_TOKENS_FILE")
    return tokens[scope_key(scope)]


def post_ask(url: str, body: bytes, id_token: str | None) -> tuple[int, dict]:
    """POST the body; the status code and the JSON reply, for error statuses too."""
    headers = {"Content-Type": JSON_CONTENT_TYPE}
    if id_token:
        headers["Authorization"] = f"{BEARER_PREFIX}{id_token}"
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:  # nosec B310: https only
            return response.status, json.loads(response.read().decode(TEXT_ENCODING))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode(TEXT_ENCODING))


def ask(case_input: EvalInput, scope: Scope, _repository) -> dict:
    """The asker contract (evals/run.py): the /ask response, or "refused": true when the scope gate refused it."""
    if case_input.inject:
        raise InjectNeedsTheLocalAsker(f"{case_input.id} plants '{case_input.inject}': run it with infra.functions.local:ask")
    if case_input.entity_id is None:
        raise NoEntityToAsk(f"{case_input.id} names no entity, and POST /ask needs one")
    base_url = get_settings().eval_api_base_url or ""
    if not base_url.startswith(HTTPS_SCHEME):
        raise DeployedApiCannotAsk(f"EVAL_API_BASE_URL must be an {HTTPS_SCHEME} URL, not {base_url!r}")
    body = AskRequest(entity_id=case_input.entity_id, question=case_input.question).model_dump_json()
    status, reply = post_ask(base_url.rstrip("/") + ASK_PATH, body.encode(TEXT_ENCODING),
                             id_token_for(scope, get_settings().eval_id_tokens_file))
    if status == HTTP_OK:
        return reply
    if status == REFUSED_STATUS_CODE and reply.get(ERROR_FIELD) == ERROR_OUT_OF_SCOPE:
        return {**reply, "refused": True, "status_code": status}
    raise AskFailed(f"POST /ask for {case_input.id} returned {status}: {reply}")
```
- [ ] **Step 4: Run it and watch it pass**
```bash
uv run --locked pytest tests/evals/test_api_asker.py tests/evals/test_run.py --no-cov 2>&1 | tail -1
```
Expected: `33 passed` (13 new, plus the runner's 20, unchanged).
- [ ] **Step 5: `EVALS.md`.** Directly after the paragraph that ends `Commit the results file of every run you record below.`, add a blank line and:
```markdown
**Against the deployed API (`evals/api_asker.py`, Linus):** the same 14 questions through `POST /ask` on AWS. Put one Cognito ID token per eval scope in a JSON file **outside the repo** (`{"cfo:*": "<ID token>", "entity_lead:E4": "<ID token>"}`; tokens expire after an hour, so fetch fresh ones per run), then run `EVAL_API_BASE_URL=https://<portal domain>/api EVAL_ID_TOKENS_FILE=<that file> uv run python -m evals.run --asker evals.api_asker:ask`. A 403 `out_of_scope` counts as a refusal (Q11); any other error fails the question. Q08 and Q09 fail by design here (the API has no fault switch: run them with the local asker), and so does Q05 (no entity, and `POST /ask` needs one). Record both runs.
```
- [ ] **Step 6: Guards, full suite and commit**
```bash
uv run --locked pytest tests/test_dependencies.py tests/test_code_style.py --no-cov 2>&1 | tail -1
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add evals/api_asker.py tests/evals/test_api_asker.py EVALS.md
git commit -m "Eval asker for the deployed API: POST /ask per eval user, 403 out_of_scope as a refusal (Q11)"
```
Expected: `15 passed`; then START + 15 (`228 passed`), `TOTAL ... 96%`.

**Task done when:** `uv run --locked pytest tests/evals --no-cov` prints `33 passed`; `grep -c "evals.api_asker:ask" EVALS.md` prints `1`.

### Task 3: Run it against AWS and hand over the results (Day 2, verify in AWS)
Only after L3 is deployed behind Y1's authorizer with `AUTH_MODE=cognito`, and Abdul's CFO and E4-lead test users exist.

- [ ] **Step 1: Fetch fresh ID tokens** for the CFO and the E4 lead (sign in to the portal as each and copy the ID token from the browser's session storage, or the Cognito CLI if Michael enabled a password flow on the test client). Write them to `~/eval-id-tokens.json` (outside the repo):
```json
{"cfo:*": "<the CFO's ID token>", "entity_lead:E4": "<the E4 lead's ID token>"}
```
Expected: `git status --short` in the repo shows nothing new.
- [ ] **Step 2: Run**
```bash
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
EVAL_API_BASE_URL=https://<portal domain>/api EVAL_ID_TOKENS_FILE=~/eval-id-tokens.json \
  uv run python -m evals.run --asker evals.api_asker:ask
```
Expected: one line per question and `Results written to evals/results/run-<stamp>.json`. Q11 shows `PASS`; Q05, Q08 and Q09 show `FAIL` with `agent loop answered` (by design); Q10 `MANUAL`; Q13, Q14 `NOT APPLICABLE`. The rest are whatever the system really does: **record them as they are**.
- [ ] **Step 3: Check, clean up, commit the results**
```bash
grep -c "eyJ" evals/results/run-*.json | tail -1
rm ~/eval-id-tokens.json
git add evals/results/run-<stamp>.json
git commit -m "Eval run against the deployed API (evals.api_asker), failures included"
```
Expected: `...:0` for the new file (no token in it); the file is committed. Hand the file name to Abdul for the `EVALS.md` Results row.

**Task done when:** an `evals/results/run-*.json` with `"asker": "evals.api_asker:ask"` is committed, and Abdul has it.

### Task 4: Review, then PR (after Linus's OK)
- [ ] **Step 1:** Work through the Review Focus; write each result in the ledger.
- [ ] **Step 2:** `git diff develop --stat` lists only `config.py`, `tests/test_config.py`, `evals/api_asker.py`, `tests/evals/test_api_asker.py`, `EVALS.md` and (after Task 3) one `evals/results/run-*.json`.
- [ ] **Step 3:** Fresh review against the spec, with the security focus on tokens; fix critical and important findings test-first.
- [ ] **Step 4: With the OK only:** `git push -u origin feature/eval-api-asker`; PR to `develop`, titled "Deployed-API eval asker (L6)". The body: how to run it, which questions fail by design and why, the counts, and "Michael: please add `evals` to the bandit paths". No attribution lines. (Tasks 1–2 can go in a first PR before Task 3 if Day 2 is tight; the results file then follows in its own small PR.)
- [ ] **Step 5:** L6's [[Build order]] row → `in review (PR #nn)`.

**Task done when:** the PR is open to `develop` and L6's [[Build order]] row says `in review (PR #nn)`.

## Done means (checklist)
- [ ] `uv run --locked pytest` prints START + 15 passed (228 on the dry-run base). *Verify:* run it.
- [ ] `uv run --locked pytest tests/evals/test_api_asker.py -k "refusal or runner" --no-cov` prints `3 passed`. *Verify:* run it.
- [ ] A results file from the deployed API is committed: `grep -l '"asker": "evals.api_asker:ask"' evals/results/*.json` prints a file name, and in it Q11's `"status"` is `"pass"`. *Verify (in AWS run):* open the file.
- [ ] That file contains no token. *Verify:* `grep -c "eyJ" <that file>` prints `0`.
- [ ] `EVALS.md` explains the asker and the by-design failures. *Verify:* `grep -n "api_asker" EVALS.md`.
- [ ] PR open or merged, no attribution lines; [[Build order]] row L6 updated. *Verify:* `gh pr view <nn> --json state`; open the note.

## Never
- Commit, paste or log an ID token; keep the tokens file anywhere inside the repo.
- Count a 403 that isn't `out_of_scope` as a refusal.
- Skip or hide a failing question; add a fault switch to the API to make Q08/Q09 pass.
- Edit `evals/run.py`'s scoring to fit this asker.
- Push to `develop` or `main`, or add attribution lines.

Related: [[L6 - Deployed-API eval asker - spec]], [[L3 - Ask, publish and approve entry points - spec]], [[Abdul - evals, Cognito, docs]], [[Build order]], [[How to execute a plan]]
