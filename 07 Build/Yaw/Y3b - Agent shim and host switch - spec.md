---
tags: [build, spec, area/devops]
id: Y3b
owner: Yaw
status: ready
updated: 2026-10-14
---
# Y3b: the agent shim and the `agent_host` switch (spec)
> **Split from Y3.** [[Y3a - AgentCore runtime - spec]] deploys the runtime; Y3b makes the ask spine use it through a **shim Lambda** (Step Functions can't call AgentCore directly), with the **Lambda fallback behind a switch**: `-c agent_host=lambda`. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after Y3a and [[Y2b - Standard publish flow - spec]] are merged.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] (`06 Workstreams/`): the architecture with owners, the code already built, the contracts and the rules (§7).
3. [[Yaw - DevOps]]: the owner's brief; and [[Michael - DevOps]] (the other half of DevOps).
4. [[Build order]]: what this item depends on and unblocks.
5. [[M2 - App, DataStack and LedgerStack - spec]]: the CDK app, `build_stacks`, the prefix, the test fixtures and the patterns every DevOps item follows.
6. [[Y3a - AgentCore runtime - spec]], [[Y2a - Express ask spine - spec]] (§3, the step contract) and [[Y2b - Standard publish flow - spec]].
7. [[Patrick - contracts, orchestrator, retriever]] (the agents) and TEAM_PLAN §5 in the repo (the AgentCore risk and its fallback).
8. `01 Decisions/`: [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]], [[2026-10-13 Team are admins, workload roles least-privilege]].
9. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Yaw (owner) or Patrick. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. **Shim** `infra/functions/agent_shim.py` *(new)*: `handler(event, context)` takes `{"runtime_arn", "step", "input"}`, calls `bedrock-agentcore:InvokeAgentRuntime` with payload `{"step", "input"}`, and returns the runtime's JSON unchanged. Session ID = SHA-256 of the run ID (64 characters; AgentCore needs ≥ 33), so a run's steps share a warm session. A non-200 from the runtime raises `AgentRuntimeError` (the state fails; nothing passes silently). Bundled by Y1's bundler (`AGENT_SHIM_BUNDLE`, root file only) so it carries a `boto3` that knows `bedrock-agentcore`.
2. **Switch** `-c agent_host=agentcore|lambda` (default **`agentcore`**; a typo fails the synth):
   - `agentcore`: the three agent steps (`run_orchestrator`, `judge_claim`, `write_answer`) have **no Lambda of their own**; their states invoke the shim with `{"runtime_arn": <AgentStack's ARN>, "step": <name>, "input": <the same payload as Y2a>}`. The shim's role may **only** `InvokeAgentRuntime` on that runtime.
   - `lambda`: exactly Y2a's graph (each agent step in its own Lambda): the documented fallback (TEAM_PLAN §5 risk).
3. The critic stays blind on both paths: `JudgeClaim`'s `input` is `{run_id, claim, scope}` only.

**Why:** "Agents hosted on AgentCore Runtime; same code runnable as a Lambda (fallback)" (Workstreams §2). The runtime ARN travels in the payload so the shim needs no new setting in `config.py` (Patrick's file) and stays a pure function of its event; IAM still limits it to the one runtime.

**Success means:**
- `uv run --locked pytest` → **S + 7 passed** (dry-run 277 → **284**), `TOTAL` 96%.
- `npx cdk synth -q` (default) shows `agent_shim.handler` and no agent-step Lambdas in `FlowStack`; `npx cdk synth -q -c agent_host=lambda` shows the seven step Lambdas and no shim.
- **Verify in AWS:** the same E4 question gives the same claim IDs and citations through both hosts (deploy one, ask, switch, deploy, ask).

**Assumptions:**
- The Lambda Python runtime's `boto3` might predate `bedrock-agentcore`; the shim bundle ships the locked `boto3` (verify the shim's first call works).
- Y3a's runtime and server are deployed and answer `judge_claim` (Y3a Task 3).
- Step Functions passes the shim's return value through `payload_response_only`, exactly like a step Lambda's.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| How Step Functions reaches AgentCore | One shim Lambda for the three agent steps, the step name in the payload | One shim per step (three identical functions); the AWS SDK integration from Step Functions (not available for `InvokeAgentRuntime` at the time of writing) |
| Where the runtime ARN comes from | The state's payload (a CDK token) | A new `AGENT_RUNTIME_ARN` setting in `config.py` (Patrick's file, for one value only the shim reads) |
| Fallback switch | CDK context `agent_host`, default `agentcore` | A runtime feature flag (both paths deployed, more roles); editing code at the go/no-go |
| Unused Lambdas in `agentcore` mode | Not created | Created but idle (Bedrock permissions on functions nobody calls) |

## 3. Tests (new, in `tests/`)
- `tests/infra/functions/test_agent_shim.py` *(new)*: the step and input reach the runtime and the output comes back; every step of a run shares one ≥ 33-character session; a runtime failure fails the step.
- `tests/infra/stacks/test_agent_host.py` *(new)*: AgentCore is the default and the agent steps have no Lambda; the shim payload carries `step` and the same blind critic input; only the shim may invoke the runtime and it has no Bedrock model rights; a typo fails.
- `tests/infra/stacks/test_flow_stack.py` *(new)* (changed): its fixture builds with `-c agent_host=lambda`, so Y2a's assertions keep describing the Lambda path.

## 4. Out of scope
- The runtime itself (Y3a). Changing the step contract. AgentCore for the publish flow (no agents there).

Related: [[Build order]], [[Yaw - DevOps]], [[Workstreams]]
