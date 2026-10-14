---
tags: [build, spec, area/agents]
id: L5
owner: Linus
status: ready
updated: 2026-10-14
---
# L5: the blocker-analyst agent (spec)
> **The agent that turns evidence into cited, figure-checked claims.** Every claim it hands on has passed `tools/claims.py` in code. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after C1 and P1 are merged.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Workstreams]] §2–§3 and §7; [[Linus - API, identity, blocker-analyst]] §5 (this item).
3. The repo's `AGENTS.md` (the blocker-analyst row is the contract) and `EVALS.md` (Q01, Q02, Q03, Q06, Q12).
4. [[C1 - API and spine contracts - spec]] §4: `Evidence`, `AnalystResult`, `Usage`.
5. [[Patrick - contracts, orchestrator, retriever]]: the orchestrator calls this agent as an agent-tool (P2); [[P1 - Retriever agent - spec]]: `agents/agent_support.py` *(new)* (`bedrock_model`, `tagged`, `usage_of`), which this agent reuses. **P1 must be merged.**
6. [[Huvison - trust and flow]]: the critic you mirror (`agents/critic.py`), and the ledger the claims go to.
7. `01 Decisions/`: [[2026-10-13 Metrics are code, only the blocker Q&A is agentic]] (D-001), [[2026-10-13 Artefact text is untrusted, critic fails closed]] (D-009), [[2026-10-13 Prompts as versioned locked files]] (D-014), [[2026-10-13 EU-only Bedrock inference profiles]] (D-002), [[2026-10-13 No LiteLLM, native Strands BedrockModel]] (D-003); `05 Workflow/`: [[Changing a prompt]], [[Working with AI assistants]].

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[Problem statement]], [[Judging rubric]], [[Pitch track grading rubric]], [[Hackathon guideline]]); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Linus. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. `agents/prompts/blocker_analyst.txt` *(new)*, v1.0.0, locked in `agents/prompts/prompts.lock`.
2. `agents/blocker_analyst.py` *(new)*: `analyse(scope, entity_id, evidence, repository, agent=None) -> AnalystResult`.
   - `scope.require(entity_id)` before anything else (no model call for an out-of-scope entity).
   - The model (Strands `Agent` on P1's `bedrock_model(get_settings().analyst_model_id)`, so the Guardrail is attached when `GUARDRAIL_ID` is set, with `callback_handler=None`) gets `Entity: <id>` and the rows inside an escaped `<evidence>` block (P1's `tagged("evidence", ...)`), and the five analyst tools from `make_analyst_tools(scope, repository)`.
   - Its reply must be `{"claims": [...]}`. Every claim goes through `tools.claims.validate_claim(raw_claim, repository, scope, analyst_tools)`; failures are dropped and logged; a repeated `claim_id` keeps the first.
   - `usage`: P1's `usage_of(reply, analyst_model_id)`, one `Usage` per model call (each Strands event-loop cycle) of the invocation.
3. `AGENTS.md`'s blocker-analyst row, the owner in `agents/README.md` (`TODO` → `Linus`) and a `HANDOFF.md` line made true.

**Why:**
- D-001: a model never computes a number. The analyst may only state figures its tools returned, and `validate_claim` re-runs every one.
- Q01 (the E4 chain), Q02 (the decoy: a **conflict claim**, never a silent pick), Q03 (E1: zero invented blockers) and Q06 (102 days, 6 behind) are scored on this agent's output.
- Cost per run needs `usage` on every agent result (C1).

**Success means:**
- With a stub model, the Q01 chain claim (`E4#RB-010` → `RC-C3-E4-customers` → `LE-000418` → `DEF-0412` → `E4#CUSMST#TAXNO`, figures 102 days remaining and 6 behind from `days_to_cutover`) and the Q02 conflict claim (`DEF-0398` Closed, `RC-C3-E4-customers` failing, `E4#RB-010` needing it) come out unchanged.
- A claim with a wrong figure, or citing another entity's row for an E4 lead, is dropped; the others are kept.
- Prose, `{"claims": "none"}`, a JSON list and a non-object claim all give no claims.
- An out-of-scope entity raises `OutOfScope` with no model call. The prompt the model gets has the rows inside `<evidence>`, with `<` and `>` escaped.
- The agent is built with exactly the five analyst tools, the analyst model ID and the Guardrail ID (through `bedrock_model`), and Strands' `null_callback_handler`.
- `blocker_analyst.py` defines no `usage_of` and imports nothing from `agents/critic.py`.
- `uv run --locked pytest`: **245 passed** (P1's 232 + 13), coverage 97%.

**Assumptions:**
- C1 is merged (`Evidence`, `AnalystResult`, `Usage` in `tools/models.py`), and P1 is merged with `agents.agent_support.bedrock_model(model_id: str)`, `tagged(tag: str, value) -> str` and `usage_of(reply, model_id: str) -> list[Usage]` as in [[P1 - Retriever agent - plan]] Task 1.
- **Patrick's orchestrator (P2)** calls `agents.blocker_analyst.analyse(scope, entity_id, evidence, repository)` (wrapped as an agent-tool on its side) and reads `AnalystResult.claims` and `.usage`. If P2 needs a different entry shape, it wraps this one; this signature is the contract offered.
- **Claims dropped here never reach the ledger.** `AnalystResult` has no field for code rejections (C1). If Patrick or Huvison want them recorded, that's a C1 change (for example `AnalystResult.rejected`); until then they're logged.
- Strands 1.x exposes per-call usage as `AgentResult.metrics.latest_agent_invocation.cycles[*].usage` with `inputTokens` and `outputTokens` (true for the locked `strands-agents 1.60.0`); P1's `usage_of` reads it and P1's tests cover it.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| How figures are checked | `tools/claims.validate_claim` on every claim, in the agent, before the result leaves it | Trusting the model; leaving it to the critic (the critic judges support, not arithmetic) |
| What happens to an invalid claim | Dropped and logged with its reason | Raising (one bad claim would lose the good ones); passing it on (it would reach the ledger unverified) |
| Unparseable output | No claims (fail closed), logged; the usage is still reported | Parsing prose; retrying inside the agent (the retry guard and re-plan live in the flow) |
| Model exceptions (throttling, network) | Propagate to the caller (the state machine's retry/catch handles infrastructure errors) | Swallowing them as "no claims" (an outage would look like "nothing is blocking", which is Q03's wrong answer) |
| Conflicting rows | The prompt requires a conflict claim citing every side; Q02 checks the answer, and the stub test proves such a claim validates | A code-side conflict detector (business logic the metrics don't have; not in this item) |
| Escaping the evidence (lead decision D3) | P1's `agents.agent_support.tagged("evidence", ...)`, with this module's own `EVIDENCE_TAG = "evidence"`: one escaper for every agent (D-009) | Importing the critic's private `_tagged` / `EVIDENCE_TAG` (couples to Huvison's internals); a copy (two escapers drift) |
| Model and Guardrail wiring (D3) | P1's `bedrock_model(settings.analyst_model_id)`, `callback_handler=None`, the five tools | Building `BedrockModel` here (a second Guardrail wiring to keep in step) |
| Usage (D3) | P1's `usage_of`: one `Usage` per Strands cycle (= one model call), C1's rule | An own `usage_of` (a copy of P1's); one entry per invocation (loses per-call detail) |
| Repeated `claim_id` | Keep the first, drop the rest (the ledger is create-once, D-012) | Renumbering (changes IDs the critic and the writer refer to) |

## 3. Shapes and behaviour
`agents/blocker_analyst.py`:
| Name | Signature | Behaviour |
|---|---|---|
| `ANALYST_AGENT_NAME` | `"blocker_analyst"` | the prompt file's name |
| `EVIDENCE_TAG` | `"evidence"` | the tag around the rows |
| `build_input` | `(entity_id: str, evidence: Evidence) -> str` | `Entity: <id>` + newline + `tagged(EVIDENCE_TAG, [row.model_dump() ...])` (P1's `agents/agent_support.py`) |
| `make_agent` | `(prompt: Prompt, analyst_tools: dict[str, Callable]) -> Callable` | Strands `Agent(model=bedrock_model(settings.analyst_model_id), system_prompt=prompt.text, tools=as_strands_tools(analyst_tools), callback_handler=None)`; imports Strands lazily |
| `raw_claims` | `(reply_text: str) -> list` | the `claims` list of a JSON object reply, else `[]` (logged) |
| `checked_claims` | `(candidates, repository, scope, analyst_tools) -> list[BlockerClaim]` | `validate_claim` on each; first per `claim_id` |
| `analyse` | `(scope, entity_id, evidence, repository, agent=None) -> AnalystResult` | require → tools → prompt → model → checked claims + `usage_of(reply, analyst_model_id)` (P1's) |

The prompt's output contract: `{"claims": [{"claim_id", "statement", "chain": [{"artefact", "row_id", "role_in_chain"}], "severity", "owner_role", "figures": {name: {"value", "tool", "args", "field"}}}]}`, severity one of critical/high/medium/low. A figure's `field` must be a **top-level** field of the tool's result (for example `days_remaining` from `days_to_cutover`); `blocker_ages` returns a list, so ages are quoted from the cited defect row instead.

## 4. Tests
- `tests/agents/test_prompts.py`: 1 new test, the prompt loads (v1.0.0, output contract `AnalystResult.claims (BlockerClaim[])`) and keeps the injection-defence wording.
- `tests/agents/test_blocker_analyst.py` *(new)*, 12 tests: the Q01 chain claim; the Q02 conflict claim; a wrong figure dropped and the rest kept; another entity's row dropped; a repeated ID; four kinds of non-claim output; an out-of-scope entity refused before the model; the evidence escaped; the agent's tools, model, Guardrail and null callback handler. Usage per model call is P1's `usage_of`, tested in `tests/agents/test_agent_support.py` *(new)*.

## 5. Out of scope
- The orchestrator and how it calls the analyst (Patrick, P2); the critic and the writer (Huvison).
- Real-model runs and the worked example in `evals/expected/blocker_analyst.json` *(new)* (Abdul and Linus, A5, once the loop runs).
- New analyst tools or figures (`tools/agent_tools.py` / `tools/metrics.py` with pinned tests, a separate change).

Related: [[L5 - Blocker-analyst agent - plan]], [[Patrick - contracts, orchestrator, retriever]], [[Build order]]
