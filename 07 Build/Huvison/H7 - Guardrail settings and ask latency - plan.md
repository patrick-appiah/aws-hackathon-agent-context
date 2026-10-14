---
tags: [build, plan, area/flow]
id: H7
owner: Huvison
spec: "[[H7 - Guardrail settings and ask latency - spec]]"
status: ready
updated: 2026-10-14
---
# H7: Guardrail settings and the `/ask` latency check (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[H7 - Guardrail settings and ask latency - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; ledger the conflict.
3. [[Huvison - trust and flow]] §8 and §9; [[P1 - Retriever agent - spec]] (`bedrock_model`); [[M3a - GuardrailStack - spec]]; [[Y2a - Express ask spine - spec]] §6; [[H6 - Local eval asker - spec]].
4. `01 Decisions/`: [[2026-10-13 Artefact text is untrusted, critic fails closed]], [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]]; `05 Workflow/`: [[Deploy and demo checks]].
5. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Huvison.

**Goal:** the Guardrail on every agent's model calls, proven by a test; the Guardrail settings written down once; the `/ask` time measured and the sync-or-async decision recorded as D-023.

**Architecture:** one place attaches the Guardrail: `agents.agent_support.bedrock_model` (P1). The critic, which predates it, switches to it. A test discovers every `make_agent` in `agents/` and checks its model. The latency part adds no code: it uses the eval runner's per-question timing (`evals/run.py` records `seconds`) and `aws stepfunctions start-sync-execution`'s billed duration.

**Tech stack:** Python 3.11, Strands Agents 1.x (`BedrockModel`), pytest, uv; AWS CLI v2 for the deployed check.

**Dry-run status:** re-run on C1 at `94970fd` (C1 alone: `213 passed`, 96%); the counts below are from that run. Task 1 ran in a throwaway worktree of C1 + P1 (P1's dry-run files). Start `232 passed`; the failing run and the passing run below are real (`236 passed`, `TOTAL` 97%). Re-run with C1 + P1 + H1 + H5 + H3 + H2a + H2b: `323 passed`, the wiring test then checks the writer too (6 tests). Task 2's insertion point was checked against `docs/DEVOPS_HANDOVER.md` on the C1 branch. The two p95 calculations in Task 4 ran on sample files; the AWS commands were **not run** (no AWS calls from the planning session): **verify in AWS**.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch for Tasks 1–3: `feature/guardrail-wiring` from an up-to-date `develop` after **C1 and P1** are merged. Branch for Tasks 4–5: `docs/ask-latency-decision`, after M3a and Y2a are deployed (and H6 merged for the one-retry run).
- **Start state:** `uv run --locked pytest` → **232 passed**, `TOTAL` 96% (C1 + P1). If other items merged first, write your real number in the ledger file; the deltas must match (each agent module already merged adds 2 to this item's test count).
- **Rules:** `eu-west-1` only; Bedrock `eu.*` inference profiles only; synthetic data only; no secrets. Settings only in `config.py`, domain constants only in `tools/constants.py`; descriptive names, no single-character names, no magic numbers. The core (`tools/`) imports no boto3, Strands, adapters, `config` or `os`. Agents reach data only through `tools/agent_tools.py`. Never weaken a security rule (scope gate, create-once ledger, fail-closed critic, escaping) to pass a test; **never lower a Guardrail filter to make an eval pass**. Tests in `tests/`, mirroring the code; `uv run --locked pytest` from the repo root; coverage must not drop. No layout or meta guard tests. Stay in your folders: `agents/critic.py`, `tests/agents/`, the named section of `docs/DEVOPS_HANDOVER.md`, and one entry in `DECISIONS.md`.
- **AWS:** profile `hackathon`, region `eu-west-1`, account `796973512193`. Every AWS step is marked **verify in AWS**; ask Huvison before running it.
- **Commits:** one per task, the given message, **no `Co-Authored-By` and no "Generated with" lines**. PR to `develop`; Patrick merges; never push to `develop` or `main`.

## Review Focus
1. **The critic's behaviour is unchanged:** same model ID (`critic_model_id`), same region, same guardrail options, `tools=[]`. Only the place that builds the model moved. `tests/agents/test_critic.py` passes untouched.
2. **The discovery can't silently check nothing:** run the wiring test with `-v` and read the IDs. It must list `agents.critic` and `agents.retriever` (and every agent merged since). An empty parametrisation would show `skipped`.
3. **Q12 under the Guardrail:** the filter sees the `<evidence>` rows. If a run citing `DEF-0462` is blocked, the critic fails closed (safe). Record the outcome in D-023, and don't lower the filter.
4. **The numbers in D-023 are measured, not estimated:** each figure has its N, the date and the commit, and the raw files are in `.superpowers/` (ignored by git).
5. **The async decision goes through Patrick:** it changes the API contract (`AskPending`, a seventh route). Don't change `tools/api_schema.py` here.

---

### Task 1: Every agent's model goes through `bedrock_model`

**Files:**
- Create: `tests/agents/test_guardrail_wiring.py` *(new)*
- Modify: `agents/critic.py` (`make_agent` and one import)

**Produces:** `agents.critic.make_agent(prompt: Prompt) -> Callable`, now built with `agents.agent_support.bedrock_model`; the test helpers `agent_module_names() -> list[str]`, `build_agent(module_name: str)`. **Consumes:** `agents.agent_support.bedrock_model(model_id: str)` (P1); `agents.prompt_loader.load_prompt` (exists); `config.get_settings` (`critic_model_id`, `guardrail_id`, `guardrail_version`; exist). **Consumed by:** every later agent (P2, L5, H3): their `make_agent` is checked by this test as soon as they merge.

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL|agents/critic"
git switch -c feature/guardrail-wiring
mkdir -p .superpowers && printf '# Ledger: H7 Guardrail settings and ask latency\n' > .superpowers/ledger-H7.md
```
Expected: `232 passed`, `TOTAL ... 96%`, and `agents/critic.py ... 88%   73-80` (the critic's `make_agent` is the miss).

- [ ] **Step 2: Write the failing test.** Create `tests/agents/test_guardrail_wiring.py`:
```python
"""Every agent builds its model through agents/agent_support.bedrock_model, so the Bedrock Guardrail is on every
model call once GUARDRAIL_ID is set (ARCHITECTURE.md §7, H7). Building a Strands Agent calls no AWS service."""
import importlib
import inspect
import pkgutil

import pytest

import agents
import config
from agents import agent_support
from agents.prompt_loader import load_prompt

AGENT_FACTORY_NAME = "make_agent"
MODEL_BUILDER_NAME = "bedrock_model"
SAMPLE_PROMPT_AGENT = "critic"   # any locked prompt will do: make_agent only uses its text
EU_PROFILE_PREFIX = "eu."
GUARDRAIL_ID = "guardrail-test"
GUARDRAIL_VERSION = "3"


def agent_module_names() -> list[str]:
    """Every module in agents/ that builds a model (defines make_agent): the critic and each agent merged since."""
    module_names = [f"{agents.__name__}.{module_info.name}" for module_info in pkgutil.iter_modules(agents.__path__)]
    return sorted(name for name in module_names if hasattr(importlib.import_module(name), AGENT_FACTORY_NAME))


def build_agent(module_name: str):
    """Call the module's make_agent with a real prompt and no tools (every argument after the prompt is a tool map)."""
    make_agent = getattr(importlib.import_module(module_name), AGENT_FACTORY_NAME)
    tool_maps = [{} for _parameter in list(inspect.signature(make_agent).parameters)[1:]]
    return make_agent(load_prompt(SAMPLE_PROMPT_AGENT), *tool_maps)


@pytest.fixture
def fresh_settings(monkeypatch):
    for variable in ("GUARDRAIL_ID", "GUARDRAIL_VERSION"):
        monkeypatch.delenv(variable, raising=False)
    config.get_settings.cache_clear()
    yield monkeypatch
    config.get_settings.cache_clear()


@pytest.mark.parametrize("module_name", agent_module_names())
def test_every_agent_builds_its_model_through_bedrock_model(module_name, fresh_settings):
    model_ids = []

    def recording_bedrock_model(model_id: str):
        model_ids.append(model_id)
        return agent_support.bedrock_model(model_id)

    fresh_settings.setattr(importlib.import_module(module_name), MODEL_BUILDER_NAME, recording_bedrock_model)
    build_agent(module_name)
    assert len(model_ids) == 1 and model_ids[0].startswith(EU_PROFILE_PREFIX)


@pytest.mark.parametrize("module_name", agent_module_names())
def test_every_agent_model_carries_the_guardrail_only_when_one_is_set(module_name, fresh_settings):
    assert "guardrail_id" not in build_agent(module_name).model.config
    fresh_settings.setenv("GUARDRAIL_ID", GUARDRAIL_ID)
    fresh_settings.setenv("GUARDRAIL_VERSION", GUARDRAIL_VERSION)
    config.get_settings.cache_clear()
    model_config = build_agent(module_name).model.config
    assert (model_config["guardrail_id"], model_config["guardrail_version"]) == (GUARDRAIL_ID, GUARDRAIL_VERSION)
```

- [ ] **Step 3: Run it and watch it fail**
```bash
uv run --locked pytest tests/agents/test_guardrail_wiring.py --no-cov 2>&1 | grep -E "^E  |^FAILED|[0-9]+ (passed|failed)"
```
Expected (C1 + P1; each other agent already merged adds 2 to `passed`):
```
E       AttributeError: <module 'agents.critic' from '.../agents/critic.py'> has no attribute 'bedrock_model'
FAILED tests/agents/test_guardrail_wiring.py::test_every_agent_builds_its_model_through_bedrock_model[agents.critic]
1 failed, 3 passed in ...s
```
The critic already attaches the Guardrail (its guardrail test passes); it just builds the model itself.

- [ ] **Step 4: Implement.** In `agents/critic.py`:
  - directly above the line `from agents.prompt_loader import Prompt, load_prompt`, add `from agents.agent_support import bedrock_model`;
  - replace the whole `make_agent` function with:
```python
def make_agent(prompt: Prompt) -> Callable:
    from strands import Agent  # imported lazily so the core and tests run without Strands

    # bedrock_model attaches the Guardrail when GUARDRAIL_ID is set, the same way for every agent (H7)
    return Agent(model=bedrock_model(get_settings().critic_model_id), system_prompt=prompt.text, tools=[])
```

- [ ] **Step 5: Run it and watch it pass**
```bash
uv run --locked pytest tests/agents/test_guardrail_wiring.py --no-cov -v 2>&1 | grep -E "PASSED|FAILED|[0-9]+ passed"
```
Expected: four `PASSED` lines, for `[agents.critic]` and `[agents.retriever]` in each test (plus two per agent merged since), then `4 passed in ...s`.

- [ ] **Step 6: The full suite and lint**
```bash
uv run --locked pytest tests/agents/test_critic.py --no-cov 2>&1 | tail -1
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL|agents/critic"
uv run ruff check agents tests
```
Expected: the critic tests pass unchanged (`... passed`, none failed); full suite **`236 passed`** (start + 4), `TOTAL ... 97%`, **no** `agents/critic.py` line (fully covered now); `All checks passed!`.

- [ ] **Step 7: Commit**
```bash
git add agents/critic.py tests/agents/test_guardrail_wiring.py
git commit -m "Every agent builds its model through bedrock_model; test the Guardrail is on each"
```
Expected: `2 files changed`.

**Task done when:** `uv run --locked pytest tests/agents/test_guardrail_wiring.py --no-cov 2>&1 | tail -1` prints `4 passed` (or more, 2 per agent module), and `grep -c "BedrockModel" agents/critic.py` prints `0`.

---

### Task 2: The Guardrail settings in the DevOps handover

**Files:** Modify `docs/DEVOPS_HANDOVER.md` (a new section directly before `## Rules`)

**Produces:** the section "Guardrail settings". **Consumes:** M3a's constants (`infra/constants.py` *(new)* once M3a is merged; [[M3a - GuardrailStack - spec]] §3 until then). **Consumed by:** Michael (M3a reads it as the agreed filter set), Yaw (environment), Abdul (A4c, the prompt review).

- [ ] **Step 1: Check M3a's values.** If M3a is merged: `grep -n "^GUARDRAIL_" infra/constants.py`. Expected: `GUARDRAIL_PROMPT_ATTACK_STRENGTH = "HIGH"`, `GUARDRAIL_BLOCKED_PII_TYPES = ("AWS_ACCESS_KEY", "AWS_SECRET_KEY", "PASSWORD")`, `GUARDRAIL_MASKED_PII_TYPES = ("EMAIL", "PHONE", "NAME")`, and the two messages, exactly as in the spec §3 table. If M3a isn't merged, use the spec's table and note "M3a not merged; values from its spec" in the ledger. If a value differs, stop and agree it with Michael first; the spec's table is the proposal.
- [ ] **Step 2: Write the section.** In `docs/DEVOPS_HANDOVER.md`, directly before the line `## Rules`, insert:
```markdown
## Guardrail settings
Owner: Huvison (settings), Michael (GuardrailStack). Every agent's model is built by `agents.agent_support.bedrock_model`, which attaches the Guardrail when `GUARDRAIL_ID` is set; `tests/agents/test_guardrail_wiring.py` checks every agent.

| Filter | Input | Output | Why |
|---|---|---|---|
| Prompt attack | `HIGH` | `NONE` (the only value Bedrock allows) | Artefact text is untrusted (D-009); the planted row `DEF-0462` is EVALS Q12 |
| PII `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `PASSWORD` | `BLOCK` | `BLOCK` | A credential never enters or leaves a model |
| PII `EMAIL`, `PHONE`, `NAME` | off | `ANONYMIZE` | The critic must see the exact rows; readers never see raw personal details |

- Messages: input "This request was blocked by the portal's safety filter."; output "The answer was blocked by the portal's safety filter."
- `GUARDRAIL_VERSION` is the published version number (GuardrailStack output `GuardrailVersion`), never `DRAFT`.
- A filter change is a new published version; never lower a filter to make an eval pass.

```
- [ ] **Step 3: Check and commit**
```bash
grep -c "^## Guardrail settings" docs/DEVOPS_HANDOVER.md
grep -n "^## " docs/DEVOPS_HANDOVER.md
git add docs/DEVOPS_HANDOVER.md
git commit -m "DEVOPS_HANDOVER: the Guardrail settings every agent runs under"
```
Expected: `1`; the headings in order end `## Bundling`, `## Guardrail settings`, `## Rules`; `1 file changed`.

**Task done when:** `grep -A3 "^| Prompt attack" docs/DEVOPS_HANDOVER.md` shows the `HIGH` / `NONE` row, and the three PII types of each kind appear in the table.

---

### Task 3: Review and the first PR

- [ ] **Step 1:** Review Focus 1–2 by hand; write the results in `.superpowers/ledger-H7.md`.
- [ ] **Step 2:** `git diff develop --stat`. Expected: `agents/critic.py`, `docs/DEVOPS_HANDOVER.md`, `tests/agents/test_guardrail_wiring.py` (3 files).
- [ ] **Step 3:** Get a fresh review of the diff against [[H7 - Guardrail settings and ask latency - spec]] (another person, or an agent with no prior context). Fix critical and important findings test-first; list the minors in the PR.
- [ ] **Step 4: With Huvison's OK only:** `git push -u origin feature/guardrail-wiring`, then open the PR to `develop` titled "Guardrail on every agent: critic through bedrock_model, wiring test, settings (H7)". Body: what changed, the test count (`236 passed` or your start + 4), the four (or more) wiring test IDs, the ledger's `Ruling:` lines. No attribution lines.
- [ ] **Step 5:** [[Build order]] row H7 → `in review (PR #nn)`. Tell Michael (the settings are in the handover; M3a's constants must match) and Patrick, Linus (their `make_agent` is now checked by the wiring test).

**Task done when:** the PR is open to `develop` with the test count in its body, and the [[Build order]] row says `in review (PR #nn)`.

---

### Task 4: Time `/ask` with one retry (verify in AWS)

**Files:** none in the repo; raw results in `.superpowers/latency-local/` and `.superpowers/latency-deployed/` (ignored by git).

**Consumes:** `evals/run.py` (`--asker`, `--results-dir`, per-case `seconds`; exists), `infra.functions.local.ask` (H6), the deployed ask machine (Y2a output `AskStateMachineArn` on `demo-FlowStack`), the Guardrail (M3a). **Produces:** the figures for D-023.

- [ ] **Step 1: Local runs, with the Guardrail on (verify in AWS: calls Bedrock).** Ask Huvison first; three eval passes cost about three times one eval run (COST.md). From the repo root on an up-to-date `develop`:
```bash
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
export GUARDRAIL_ID=$(aws cloudformation describe-stacks --stack-name demo-GuardrailStack --query "Stacks[0].Outputs[?OutputKey=='GuardrailId'].OutputValue" --output text)
export GUARDRAIL_VERSION=$(aws cloudformation describe-stacks --stack-name demo-GuardrailStack --query "Stacks[0].Outputs[?OutputKey=='GuardrailVersion'].OutputValue" --output text)
for pass_number in 1 2 3; do uv run python -m evals.run --asker infra.functions.local.ask --results-dir .superpowers/latency-local; done
```
Expected: three reports, each ending `Results written to .superpowers/latency-local/run-<timestamp>.json`; every asked question shows its time (`  12.3 s`). Q12's line reads `PASS`. If Q12 fails with a guardrail block, **don't change the filter**; write "Q12 blocked by the Guardrail; critic failed closed" in the ledger for D-023 and tell Patrick (Review Focus 3).

- [ ] **Step 2: The local figures.**
```bash
LATENCY_DIR=.superpowers/latency-local uv run python - <<'EOF'
import json
import math
import os
from pathlib import Path

PERCENTILE = 0.95
results = [json.loads(path.read_text()) for path in sorted(Path(os.environ["LATENCY_DIR"]).glob("run-*.json"))]
seconds = sorted(case["seconds"] for result in results for case in result["cases"] if case["seconds"] is not None)
retry_runs = [case["seconds"] for result in results for case in result["cases"] if case["id"] == "Q09"]
rank = math.ceil(PERCENTILE * len(seconds))
print(f"local: {len(seconds)} runs, p95 {seconds[rank - 1]} s, max {seconds[-1]} s; Q09 (one retry): {retry_runs} s")
EOF
```
Expected: one line of the form `local: 36 runs, p95 16.7 s, max 17.4 s; Q09 (one retry): [12.3, 13.8, 15.3] s` (these are the dry-run's **sample** values; yours are the measurement). Copy the line into the ledger. If H6 isn't merged, run `time uv run python scripts/ask.py --entity E4 "What is blocking cutover for E4?"` five times instead, write the five `real` times in the ledger, and note "no retry forced".

- [ ] **Step 3: Deployed runs (verify in AWS: once M3a and Y2a are deployed).**
```bash
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
ASK_ARN=$(aws cloudformation describe-stacks --stack-name demo-FlowStack --query "Stacks[0].Outputs[?OutputKey=='AskStateMachineArn'].OutputValue" --output text)
mkdir -p .superpowers/latency-deployed && : > .superpowers/latency-deployed/durations.txt
for attempt in $(seq 1 10); do
  run_id="run-latency-$(date +%s)-$attempt"
  printf '{"run_id":"%s","scope":{"user_id":"demo-cfo","role":"cfo","tenant_id":"t-01","entity_ids":["*"]},"entity_id":"E4","question":"What is blocking cutover for E4?","budget_usd":0.5,"max_attempts":2}' "$run_id" > .superpowers/latency-deployed/question.json
  aws stepfunctions start-sync-execution --state-machine-arn "$ASK_ARN" --input file://.superpowers/latency-deployed/question.json \
    --query "[status, billingDetails.billedDurationInMilliseconds]" --output text | tee -a .superpowers/latency-deployed/durations.txt
done
```
Expected: ten lines `SUCCEEDED	<milliseconds>`. The input is the bare `Question` JSON, as L3 sends it ([[H2b - Agent states, local spine and Lambda handlers - spec]]). A `FAILED` line is a finding: open the execution in the Step Functions console, write the failing state in the ledger, and tell Yaw.

- [ ] **Step 4: The deployed figures.**
```bash
LATENCY_FILE=.superpowers/latency-deployed/durations.txt uv run python - <<'EOF'
import math
import os
from pathlib import Path

PERCENTILE = 0.95
MILLISECONDS_PER_SECOND = 1000
lines = [line.split("\t") for line in Path(os.environ["LATENCY_FILE"]).read_text().splitlines() if line.strip()]
statuses = sorted({status for status, _milliseconds in lines})
seconds = sorted(int(milliseconds) / MILLISECONDS_PER_SECOND for _status, milliseconds in lines)
rank = math.ceil(PERCENTILE * len(seconds))
print(f"deployed: {len(seconds)} runs, statuses {statuses}, p95 {seconds[rank - 1]} s, max {seconds[-1]} s")
EOF
```
Expected: one line of the form `deployed: 10 runs, statuses ['SUCCEEDED'], p95 15.1 s, max 15.1 s` (dry-run sample values). Copy it into the ledger.

- [ ] **Step 5: Apply the rule** (spec §2). **Async** if the local p95 > 20 s, or the deployed p95 > 20 s, or any deployed run > 25 s. Otherwise **sync stays**. Write `Ruling: /ask <sync|async>, local p95 <x> s, deployed p95 <y> s` in the ledger, then tell Patrick before Task 5, because async changes the API contract.

**Task done when:** the ledger holds both figure lines, and the ruling has Patrick's agreement (his name and the time in the ledger).

---

### Task 5: Record D-023 and the second PR

**Files:** Modify `DECISIONS.md` (one entry at the end)

- [ ] **Step 1: Branch.**
```bash
git switch develop && git pull && git switch -c docs/ask-latency-decision
grep -c "^### D-023" DECISIONS.md
```
Expected: `0`. If it prints `1`, the number is taken: use the next free one, and write it in the ledger and in every message below.

- [ ] **Step 2: Write the entry.** Append to `DECISIONS.md`, using **one** of the two blocks, with your measured figures in place of the sample figures:
  - **If sync stays:**
```markdown

### D-023 · /ask stays synchronous
- **What:** `POST /ask` keeps waiting for the Express execution and returns the `AskResponse` in the same request. The threshold for switching is a p95 above 20 s, or any deployed run above 25 s.
- **Why:** Measured on 2026-10-14 at commit abc1234: local, 36 runs over three eval passes with the Guardrail on, p95 16.7 s, max 17.4 s; Q09 (one retry) 12.3 to 15.3 s. Deployed Express, 10 runs, p95 15.1 s, max 15.1 s. That is under API Gateway's 29-second limit with margin for cold starts.
- **Rejected:** Async start plus polling (a new route, a new response model and a polling panel, for no measured need).
```
  - **If async:**
```markdown

### D-023 · /ask is asynchronous: start, then poll
- **What:** `POST /ask` starts the run (`states:StartExecution`) and returns `{run_id, status: "running"}` (`AskPending`, added to `tools/api_schema.py` by Patrick); `GET /ask/{run_id}` returns the `AskResponse` when the run is done, else `AskPending`. `write_answer` stores the `AskResponse` on the run in the ledger, and `GET` reads it from there. Follow-ups: Patrick (`AskPending`), Linus (`infra.functions.api.ask_result`), Yaw (the route and the start permission, Y2a §6), Clement (F4b, polling), Huvison (storing the response).
- **Why:** Measured on 2026-10-14 at commit abc1234: local p95 21.8 s; deployed Express p95 23.4 s, max 26.0 s, over 10 runs. Too close to API Gateway's 29-second limit.
- **Rejected:** Keeping sync (a slow run times out mid-demo). A Standard ask machine read with `DescribeExecution` (reverses D-007; asynchronous Express runs have no `DescribeExecution`). WebSockets (a second API type for one panel).
```
  Replace the date, `abc1234` (`git rev-parse --short HEAD` at the measurement) and every figure with the ledger's.

- [ ] **Step 3: Check and commit**
```bash
grep -n "^### D-023" DECISIONS.md
git add DECISIONS.md
git commit -m "D-023: /ask sync or async, decided from the measured p95"
```
Expected: one line, `### D-023 · /ask stays synchronous` or `### D-023 · /ask is asynchronous: start, then poll`; `1 file changed`.

- [ ] **Step 4: With Huvison's OK only:** push `docs/ask-latency-decision` and open the PR to `develop` titled "D-023: the /ask latency decision (H7)", with the two figure lines from the ledger in the body. No attribution lines.
- [ ] **Step 5:** If async: add one line per follow-up to the vault's `Open follow-ups.md` (Patrick `AskPending`; Linus `ask_result`; Yaw Y2a §6; Clement [[F4b - Async ask polling - spec]]; Huvison: store the response on the run), and tell each owner at stand-up. If sync: tell Clement that F4b is not needed.
- [ ] **Step 6:** [[Build order]] row H7 → `merged` once both PRs are merged.

**Task done when:** `grep -c "^### D-023" DECISIONS.md` prints `1` on the branch, and the PR is open with both figure lines in its body.

## Done means
- [ ] **Every agent's model goes through `bedrock_model`.** *Verify:* on `develop`, `uv run --locked pytest tests/agents/test_guardrail_wiring.py --no-cov -v 2>&1 | grep -c PASSED` prints twice the number of agent modules (`4` with the critic and the retriever; `10` once the orchestrator, the analyst and the writer are merged), and `grep -c "BedrockModel" agents/critic.py` prints `0`.
- [ ] **The critic is unchanged in behaviour.** *Verify:* `uv run --locked pytest tests/agents/test_critic.py --no-cov 2>&1 | tail -1` shows only `passed`.
- [ ] **Nothing broke, coverage held.** *Verify:* `uv run --locked pytest 2>&1 | grep -E "passed|TOTAL"` prints start + 4 passed and `TOTAL` ≥ 96%, with no `agents/critic.py` line.
- [ ] **The settings are written down and match the stack.** *Verify:* `grep -A5 "^## Guardrail settings" docs/DEVOPS_HANDOVER.md` shows the section, and its values equal `grep "^GUARDRAIL_" infra/constants.py` (once M3a is merged).
- [ ] **The latency is measured and decided (verify in AWS).** *Verify:* `grep -A3 "^### D-023" DECISIONS.md` shows the decision with local and deployed p95 figures, the number of runs, the date and a commit.
- [ ] **The follow-ups are assigned.** *Verify:* if D-023 says async, `Open follow-ups.md` in the vault has the five follow-up lines; if sync, Clement's F4b row in [[Build order]] is marked not needed.
- [ ] **Merged.** *Verify:* both PRs merged into `develop`; [[Build order]] row H7 `merged`.

## Never
- Lower or remove a Guardrail filter to make an eval pass; change the filter values without Michael and a new published version.
- Build a `BedrockModel` directly in an agent; attach the Guardrail anywhere but `bedrock_model`.
- Point `GUARDRAIL_VERSION` at `DRAFT`.
- Add `AskPending` or a route yourself (Patrick and Linus own them); decide async without Patrick.
- Commit the raw timing files, a token or a credential.
- Push to `develop` or `main`, or add attribution lines.

Related: [[H7 - Guardrail settings and ask latency - spec]], [[Huvison - trust and flow]], [[Build order]], [[How to execute a plan]]
