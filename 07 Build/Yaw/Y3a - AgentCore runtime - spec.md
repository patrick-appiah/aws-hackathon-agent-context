---
tags: [build, spec, area/devops]
id: Y3a
owner: Yaw
status: ready
updated: 2026-10-14
---
# Y3a: AgentStack, the AgentCore Runtime that hosts the agents (spec)
> **Split from Y3.** Y3a is the AgentCore Runtime itself (deployable and invocable on its own); [[Y3b - Agent shim and host switch - spec]] is the shim Lambda Step Functions calls and the `agent_host` switch with the Lambda fallback. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after [[Y2a - Express ask spine - spec]] and Huvison's H2 (`infra/functions/steps.py` *(new)*) are merged.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] (`06 Workstreams/`): the architecture with owners, the code already built, the contracts and the rules (§7).
3. [[Yaw - DevOps]]: the owner's brief; and [[Michael - DevOps]] (the other half of DevOps).
4. [[Build order]]: what this item depends on and unblocks.
5. [[M2 - App, DataStack and LedgerStack - spec]]: the CDK app, `build_stacks`, the prefix, the test fixtures and the patterns every DevOps item follows.
6. [[Y2a - Express ask spine - spec]] (the agent steps and their JSON, §3) and [[Y1 - ApiStack - spec]] (the bundler); [[M3a - GuardrailStack - spec]]; [[M4b - Observability - spec]] (Transaction Search, which AgentCore's traces need).
7. [[Patrick - contracts, orchestrator, retriever]] and [[Huvison - trust and flow]] (the agents and the steps that call them).
8. `01 Decisions/`: [[2026-10-13 No LiteLLM, native Strands BedrockModel]], [[2026-10-13 EU-only Bedrock inference profiles]], [[2026-10-13 Prompts as versioned locked files]], [[2026-10-13 Team are admins, workload roles least-privilege]].
9. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Yaw (owner) or Patrick (agents). Never invent a name, a shape or a rule.

## 1. Intent
**What:** an `AgentStack` *(new)* with one **AgentCore Runtime** (`aws_bedrockagentcore.Runtime`, the L2 in `aws-cdk-lib` 2.273):
1. **Code zip, not a container:** `AgentRuntimeArtifact.from_code_asset(path=<bundle>, runtime=PYTHON_3_11, entrypoint=["server.py"])`. The bundle is built by Y1's bundler for **ARM64** (`aarch64-manylinux2014`): our code (`tools/`, `adapters/`, `agents/` with the locked prompts, `config.py`, `infra/functions/`) plus the runtime dependencies, with `infra/agent_runtime/server.py` *(new)* copied to the bundle root. **No Docker** at build or deploy time.
2. **`server.py`:** the AgentCore HTTP contract on `0.0.0.0:8080` using only the standard library: `GET /ping` → `{"status": "Healthy"}`; `POST /invocations` with `{"step", "input"}` runs **one** of `infra.functions.steps.run_orchestrator | judge_claim | write_answer` and returns its JSON unchanged; anything else → 400 `invalid_input`; a failing step → 500 `step_failed` with the exception type only.
3. **Environment:** `LEDGER_BACKEND=dynamo`, `LEDGER_TABLE`, `REJECTED_TABLE`, `ARTEFACT_BACKEND=csv`, `ARTEFACTS_URI`, `GUARDRAIL_ID`, `GUARDRAIL_VERSION` (the same as the agent-step Lambdas in Y2a).
4. **Role:** the L2's execution role plus exactly the agent steps' statements: ledger actions on both tables, Bedrock invoke on the two `eu.*` profiles and their EU models (`infra/bedrock_access.py` *(new)*), `bedrock:ApplyGuardrail` on the Guardrail, `s3:GetObject` on `artefacts/*`. Tracing on (X-Ray delivery, named per copy).
5. **Name per copy:** `runtime_name(prefix)` → `demo_erp_portal_agents` (`-` becomes `_`: runtime names allow letters, digits and underscores).
6. **Output** `AgentRuntimeArn`; `.runtime`; `.invoke_statement()`: `bedrock-agentcore:InvokeAgentRuntime` on this runtime and its `DEFAULT` endpoint only (for Y3b's shim).

**Why:** the brief's "agents hosted on AgentCore Runtime (Strands)" (TEAM_PLAN §5, ARCHITECTURE §3). A code zip avoids Docker and an ECR repository on every laptop; a stdlib server avoids a new dependency (`bedrock-agentcore` SDK) and keeps the payload exactly the step contract, so the state machine sees the same JSON through either host.

**Success means:**
- `uv run --locked pytest` → **S + 12 passed** (dry-run 265 → **277**), `TOTAL` 96%.
- `npx cdk synth -q` with no credentials (and `infra/functions/` present) writes `AgentStack.template.json` with an `AWS::BedrockAgentCore::Runtime` whose code configuration is `PYTHON_3_11`, entry point `server.py`; `infra/cdk.out/bundles/agent-runtime/` *(new)* holds `server.py`, `agents/prompts/prompts.lock` and ARM64 wheels (`_cffi_backend.cpython-311-aarch64-linux-gnu.so`).
- **Verify in AWS:** `aws bedrock-agentcore invoke-agent-runtime` with `{"step": "judge_claim", "input": ...}` returns the step's JSON.

**Assumptions** (reconcile before the PR):
- **AgentCore in eu-west-1** supports direct code deployment for `PYTHON_3_11` with an entry-point file that serves `/invocations` and `/ping` on port 8080 (the documented runtime contract). If AgentCore isn't available or the code-zip path fails in eu-west-1, the Lambda fallback (Y3b `-c agent_host=lambda`, Y2a's path) is the documented answer, stated in `HANDOFF.md`.
- **Huvison (H2):** `infra.functions.steps.run_orchestrator`, `judge_claim`, `write_answer` are importable inside the runtime and take/return the Y2a §3 JSON; their settings come only from the environment above through `config.get_settings()`.
- **Patrick (P2) / Huvison:** prompts load from `agents/prompts/` relative to the package (the bundle keeps that layout) and `prompts.lock` matches.
- **Michael (M4b):** Transaction Search is on in the account, so the runtime's traces show in CloudWatch.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Artefact | Code zip (`from_code_asset`), ARM64 Python 3.11, built by the uv bundler | A container image (`from_asset` with Docker, an ECR repo, ARM64 cross-builds on x86 laptops) |
| Server | Standard library `ThreadingHTTPServer` with the AgentCore contract | The `bedrock-agentcore` SDK app (a new runtime dependency for two routes) |
| What the runtime runs | The three agent steps of `infra/functions/steps.py`, chosen by `step` | Each agent separately (a second contract next to the step contract) |
| Role | L2 role + the same statements as the agent-step Lambdas | A shared role with the Lambdas (one role per runtime, ARCHITECTURE §7) |
| Naming | `<prefix>_erp_portal_agents` | A fixed name (the second copy would collide) |

## 3. Tests (new, in `tests/`)
- `tests/infra/agent_runtime/test_server.py` *(new)*: a known step runs with its input; bad JSON, a missing key, an unknown step and a non-object input are refused (400); a failing step is a 500 with the type only; `/ping` over real HTTP on a local port is healthy and a bad `/invocations` body is 400.
- `tests/infra/stacks/test_agent_stack.py` *(new)*: the runtime (name, `PYTHON_3_11`, `server.py`, environment); the bundle spec (ARM64, server at the root, `infra/functions` *(new)* included); the role has ledger, model, Guardrail and artefacts actions and no `s3:PutObject` or `dynamodb:Scan`; `runtime_name`; the output.

## 4. Out of scope
- The shim, the switch and the Lambda fallback in the state machine (Y3b). The agents (Patrick, Linus, Huvison).
- AgentCore Memory, Gateway, Identity, VPC networking (public network mode is the default).

Related: [[Build order]], [[Yaw - DevOps]], [[Workstreams]]
