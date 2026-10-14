---
tags: [build, spec, area/flow]
id: H7
owner: Huvison
status: awaiting review
updated: 2026-10-14
---
# H7: Guardrail settings and the `/ask` latency check (spec)
> **Two of Huvison's brief items that nobody else owns: the Bedrock Guardrail settings (brief §8) and the 29-second `/ask` check (brief §9).** Part 1 writes down the filter set Michael's GuardrailStack deploys and proves in a test that every agent's model goes through `agents/agent_support.bedrock_model`, so the Guardrail is on every model call once `GUARDRAIL_ID` is set. Part 2 times a full ask with one retry, locally and (once deployed) on the Express machine, and records the sync-or-async decision. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` once P1 is merged; the deployed checks need M3a (and Y2a) deployed. The repo is the source of truth for code; the vault is the source of context.

## 0. Context: read the vault first
The team vault is the shared context space for this project. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] §2 (the ask spine) and §7 (the rules).
3. [[Huvison - trust and flow]] §8 "Guardrail settings" and §9 "Latency": the owner's brief for this item.
4. [[Build order]]: H7 depends on P1 (code); the deployed checks need M3a and Y2a deployed; the local timing with one retry needs H6.
5. [[P1 - Retriever agent - spec]] (`agents/agent_support.py` *(new)*: `bedrock_model`), [[M3a - GuardrailStack - spec]] (the filter set as deployed constants), [[Y2a - Express ask spine - spec]] §6 (the async fallback DevOps agreed), [[H6 - Local eval asker - spec]] (Q09: one retry).
6. `01 Decisions/`: [[2026-10-13 Artefact text is untrusted, critic fails closed]] (D-009), [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]] (D-007), [[2026-10-13 EU-only Bedrock inference profiles]]; the repo's `ARCHITECTURE.md` §7, `DECISIONS.md`, `docs/DEVOPS_HANDOVER.md`.
7. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` ([[Hackathon guideline]], [[Judging rubric]]: trust and guardrails), `03 Sessions/`, `Open follow-ups.md`. If the vault doesn't answer it, stop and ask Huvison. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. **The Guardrail settings**, written once in `docs/DEVOPS_HANDOVER.md` (a new section "Guardrail settings"), matching the constants M3a deploys (§3 table).
2. **Every agent's model through `bedrock_model`:** `agents/critic.py` `make_agent` builds its model with `agents.agent_support.bedrock_model(settings.critic_model_id)` instead of its own `BedrockModel` call (same behaviour, one place). A new test, `tests/agents/test_guardrail_wiring.py` *(new)*, finds every module in `agents/` that defines `make_agent` and checks that it builds its model through `bedrock_model`, and that the model carries `guardrail_id` and `guardrail_version` when `GUARDRAIL_ID` is set and none when it isn't.
3. **The latency check:** time a full ask with one retry locally (the eval runner with `infra.functions.local:ask`, Q09 is the one-retry run) and, once deployed, the Express execution; apply the decision rule (§2); record the decision in `DECISIONS.md` as D-023.

**Why:**
- `ARCHITECTURE.md` §7 lists the Guardrail's prompt-attack filter as defence 2 of 5 against prompt injection; EVALS Q12 (`DEF-0462`) tests that artefact text stays data. A Guardrail that one agent forgets to attach protects nothing on that agent's calls.
- API Gateway ends a synchronous `/ask` at 29 seconds (the brief; HTTP API's hard integration cap is 30 s). A demo answer that times out is a failed demo; the async path changes the API contract, so it must be decided early (D1 18:00) and through Patrick.

**Success means:**
- `uv run --locked pytest tests/agents/test_guardrail_wiring.py --no-cov` passes with **2 tests per agent module** (critic and retriever after P1: `4 passed`; each later agent adds 2).
- Full suite: start + 4 (dry-run on C1 + P1: `236 passed`, `TOTAL` 97%); `agents/critic.py` no longer has missed lines.
- `docs/DEVOPS_HANDOVER.md` has the "Guardrail settings" table, and its values equal `infra/constants.py` *(new)*'s `GUARDRAIL_*` (M3a).
- `DECISIONS.md` has D-023 with the measured p95 figures and the decision (sync kept, or async).
- **Verify in AWS:** the deployed ask machine's p95 over 10 runs and the local Q09 time are in the D-023 entry; Q12 still passes with `GUARDRAIL_ID` set.

**Assumptions** (reconcile with the named owner before the PR):
- **P1** ships `agents.agent_support.bedrock_model(model_id: str)` that adds `guardrail_id` and `guardrail_version` from `config.get_settings()` when `guardrail_id` is set ([[P1 - Retriever agent - plan]] Task 1). P2 (orchestrator), L5 (analyst) and H3 (writer) build their models with it; the test checks them automatically as they merge.
- Every agent's `make_agent` takes the prompt first and, after it, only tool maps (`dict[str, Callable]`): true for the critic and the writer (prompt only), the retriever, the orchestrator and the analyst (prompt, tools). An agent whose `make_agent` breaks this fails the test loudly; fix the test's `build_agent`, not the agent.
- **Michael (M3a)** deploys exactly the values in §3 (his constants `GUARDRAIL_PROMPT_ATTACK_STRENGTH`, `GUARDRAIL_BLOCKED_PII_TYPES`, `GUARDRAIL_MASKED_PII_TYPES`). M3a's spec calls this item "H8 Guardrail settings"; it is H7.
- **Yaw (Y2a)** §6 describes the async DevOps change (ask Lambda `states:StartExecution`, route `GET /ask/{run_id}`, `write_answer` storing the response). Y2a names the decision "D-022" and a ~25 s threshold; D-022 is already the Q09 verdict-count decision, so this one is **D-023**, and the lead set the threshold at **20 s**.
- **H6** is merged for the local one-retry timing (`infra.functions.local:ask` plants Q09's forced claim). Without H6, time `scripts/ask.py` *(new)* only and note that no retry was forced.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Where the Guardrail is attached | Only in `agents.agent_support.bedrock_model`; every `make_agent` calls it (the critic too, after this item) | Each agent building its own `BedrockModel` with the guardrail options (the critic today: five copies of the same `if`) |
| How the test finds the agents | Every module in `agents/` that defines `make_agent` (`pkgutil.iter_modules`), so a new agent is checked the day it merges | A hand-kept list of agents (forgotten when an agent is added) |
| What the test proves | Behaviour: `make_agent` calls the module's `bedrock_model` once with an `eu.*` model ID, and the built model's config has the guardrail only when it is set | Reading the source for the string `bedrock_model` (a layout check, not behaviour) |
| PII on input | Credentials (`AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `PASSWORD`) blocked; personal details not filtered on input | Masking names and e-mails on input (rewrites evidence rows, so the critic would judge altered data and fail) |
| PII on output | `EMAIL`, `PHONE`, `NAME` masked (`ANONYMIZE`); credentials blocked | Blocking every PII type on output (one name in an owner field would lose the whole answer) |
| Prompt attack | `HIGH` on input; `NONE` on output (Bedrock allows only `NONE` there) | `MEDIUM` (DEF-0462 is planted to test exactly this); off (fails ARCHITECTURE §7) |
| Which version the Lambdas use | The published version number from M3a's output | `DRAFT` (changes under running code) |
| Latency measure | p95, nearest rank, over ≥ 10 deployed Express runs plus the local runs of three eval passes; Q09's time is reported on its own (the one-retry case) | A single run (a lucky run hides cold starts); the mean (hides the slow tail that times out) |
| Decision rule | **p95 > 20 s** on either measurement, or any single deployed run > 25 s → async; otherwise keep the synchronous `/ask` | Waiting until runs reach 29 s (no margin for cold starts and a busy Bedrock) |
| The async shape, if chosen | `POST /ask` returns `{run_id, status: "running"}` (a new `AskPending` model in `tools/api_schema.py`, a C1 follow-up for Patrick); `GET /ask/{run_id}` returns the `AskResponse` when done, else `AskPending` again; the ask machine starts with `states:StartExecution`, and `write_answer` stores the `AskResponse` on the run in the ledger (Y2a §6) | A Standard ask machine read with `DescribeExecution` (Express executions started asynchronously have no `DescribeExecution`, and switching type reverses D-007); WebSockets (a second API type for one panel) |
| Where the decision goes | `DECISIONS.md` D-023 with the figures, the date and the commit | Only in the PR body (lost after merge) |

**ADR: why these Guardrail settings.**
- *Context:* artefact text (defect titles, notes) is untrusted (D-009), and the planted row `DEF-0462` tries to instruct the model. With Strands, the Guardrail sees the whole conversation, including the `<evidence>` rows.
- *Decision:* the prompt-attack filter at `HIGH` on input catches the injection pattern before it reaches any agent. Credentials are blocked both ways, because a key must never enter or leave a model. Personal details are masked on output only, so the critic still sees the exact rows it recomputes figures from, while a reader never sees a raw e-mail or phone number. One published version is pinned.
- *Consequences:* if the filter blocks a run that cites `DEF-0462`, the critic fails closed and Q12 shows a rejection instead of a clean verdict. That is still safe (nothing injected passes), but it changes Q12's expected outcome. This item checks Q12 with the Guardrail on and records what happens. If Q12 breaks, the fix is in the flow (tag only the user's question as guarded content), never a lower filter. Names in synthetic owner fields are masked in answers: acceptable, because answers cite roles and row IDs.

## 3. Exact shapes
**The Guardrail settings** (the "Guardrail settings" section of `docs/DEVOPS_HANDOVER.md`, the same values as M3a's `infra/constants.py`):
| Filter | Setting | Input | Output | M3a constant |
|---|---|---|---|---|
| Prompt attack | strength | `HIGH` | `NONE` | `GUARDRAIL_PROMPT_ATTACK_STRENGTH = "HIGH"` |
| PII `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `PASSWORD` | action | `BLOCK` | `BLOCK` | `GUARDRAIL_BLOCKED_PII_TYPES` |
| PII `EMAIL`, `PHONE`, `NAME` | action | off | `ANONYMIZE` | `GUARDRAIL_MASKED_PII_TYPES` |
| Blocked input message | text | "This request was blocked by the portal's safety filter." | | `GUARDRAIL_BLOCKED_INPUT_MESSAGE` |
| Blocked output message | text | | "The answer was blocked by the portal's safety filter." | `GUARDRAIL_BLOCKED_OUTPUT_MESSAGE` |
| Version | the published number (stack output `GuardrailVersion`) → `GUARDRAIL_VERSION` | | | `GUARDRAIL_VERSION_DESCRIPTION` |

**`agents/critic.py`:** `make_agent(prompt: Prompt) -> Callable` returns `Agent(model=bedrock_model(get_settings().critic_model_id), system_prompt=prompt.text, tools=[])`, with `from agents.agent_support import bedrock_model` at the top. Nothing else in the critic changes.

**`tests/agents/test_guardrail_wiring.py`:** constants `AGENT_FACTORY_NAME = "make_agent"`, `MODEL_BUILDER_NAME = "bedrock_model"`, `SAMPLE_PROMPT_AGENT = "critic"`, `EU_PROFILE_PREFIX = "eu."`, `GUARDRAIL_ID`, `GUARDRAIL_VERSION`; helpers `agent_module_names() -> list[str]`, `build_agent(module_name: str)`; fixture `fresh_settings`.

**The decision entry** (`DECISIONS.md`, after the last entry): `### D-023 · /ask stays synchronous` or `### D-023 · /ask is asynchronous: start, then poll`, in the repo's format: the bullets **What** (the decision and, if async, the follow-ups named in §2), **Why** (the figures: local Q09 seconds, local p95, deployed p95 and max, the number of runs, the date and the commit) and **Rejected** (the option not taken).

**`AskPending`** (only if async; Patrick adds it in a C1 follow-up, not this item): `class AskPending(Contract): run_id: str; status: Literal["running"]`.

## 4. Tests
`tests/agents/test_guardrail_wiring.py` *(new)*, 2 tests, each parametrised over the agent modules:
- `test_every_agent_builds_its_model_through_bedrock_model`: the module's `bedrock_model` is replaced with a recording wrapper around the real one; `make_agent` calls it exactly once, with an `eu.*` model ID. Before Task 1's fix, the critic fails with `AttributeError: ... has no attribute 'bedrock_model'`.
- `test_every_agent_model_carries_the_guardrail_only_when_one_is_set`: without `GUARDRAIL_ID`, the model config has no `guardrail_id`; with `GUARDRAIL_ID=guardrail-test` and `GUARDRAIL_VERSION=3`, it has both.
- The existing critic tests (`tests/agents/test_critic.py`) pass unchanged.

## 5. Out of scope
- Deploying the Guardrail (Michael, M3a) and setting `GUARDRAIL_ID` / `GUARDRAIL_VERSION` on the Lambdas (Yaw).
- Building the async path: `AskPending` (Patrick), `infra.functions.api.ask_result` (Linus), the route and `StartExecution` (Yaw), polling in the ask panel (Clement, [[F4b - Async ask polling - spec]]), storing the response on the run (Huvison, a follow-up item if async is chosen).
- Topic, word and contextual-grounding filters (not in the brief).
- Changing the flow to tag only the question as guarded content (only if Q12 breaks; a follow-up).

Related: [[H7 - Guardrail settings and ask latency - plan]], [[Huvison - trust and flow]], [[M3a - GuardrailStack - spec]], [[Build order]]
