---
tags: [workstream, area/team]
owner: Yaw
updated: 2026-10-14
---
# Yaw: DevOps (API, Lambdas, Step Functions, AgentCore, IAM)
> The repo is the source of truth. Read [[Workstreams]] first. Your row: `docs/TEAM_PLAN.md` §2, workstream 5 (with Michael, [[Michael - DevOps]]).
> **Proposal: confirm this split with Michael at the first stand-up.** You take the *compute and orchestration* stacks; Michael takes CI and the *stateful and edge* stacks. No stack is in both briefs.

## Your job in one paragraph
You put the back end's code into AWS:
- **API Gateway** with the JWT authorizer and the six routes, onto Linus's Lambda handlers;
- the two **Step Functions** state machines: the Express "ask spine" that runs every question, and the Standard publish flow that waits for a human approval;
- **AgentCore Runtime**, which hosts the Strands agents, with a plain-Lambda fallback;
- a least-privilege **IAM role** for every function.

The ask spine is what makes the agent loop "genuinely run" in AWS, which is what judges weigh most.

## Shared DevOps context (same in Michael's brief)
- **CDK in Python:** `infra/app.py` *(new)* defines every stack; the stack list and resources are in `infra/README.md`.
- **Bootstrap once:** `npx cdk bootstrap aws://486128667962/eu-west-1`. **`eu-west-1` only.** Profile `AWS_PROFILE=hackathon`; your IAM user is `yaw.mintah`.
- **Stack names take a prefix** for the clean-deploy check (`-c prefix=demo2`).
- **Deploys are manual from the README** (`cd infra && npx cdk deploy --all`). CI builds and tests only (D-018, which lands with PR #8).
- **Least privilege** (`ARCHITECTURE.md` §7): one role per Lambda / runtime / state machine, scoped to its S3 prefix, its table and **specific** Bedrock model ARNs (`eu.anthropic.claude-sonnet-4-6`, `eu.amazon.nova-lite-v1:0`). No `*`.
- **Python bundles:** `uv export --no-dev --format requirements-txt --no-hashes > build/requirements.txt` at build time; `agents/prompts/` and `prompts.lock` ship with every bundle that loads prompts (the loader refuses unlocked prompts).
- **Your input:** `docs/DEVOPS_HANDOVER.md` *(new, Patrick)*, plus the step-model contract in `tools/models.py` (Patrick). Settings reach code only through `config.py` environment variables.
- **No console-clicked resources;** no secrets in the repo or the vault.

## Where you sit in the architecture
```
 CloudFront /api/* (Michael) ─▶ ★API Gateway HTTP API (v2) + JWT authorizer★ (issuer: Michael's pool, audience: app client ID)
   ├─ GET /summary · /entity/{id} · /rows ─▶ ★Lambda★ api.handlers:summary|entity|rows (Linus)
   ├─ POST /ask ─▶ ★Lambda★ api.handlers:ask ─▶ ★Express state machine★ (StartSyncExecution)
   │      check_budget ─▶ run_orchestrator ─▶ store_claims ─▶ judge_claim ─▶ retry Choice ─▶ write_answer | record_rejection
   │      (each state = one ★Lambda★ from Huvison's flow/steps.py; agents run on ★AgentCore★ or in the Lambda)
   └─ POST /publish · /approve ─▶ ★Lambda★ api.handlers:publish|approve ─▶ ★Standard state machine★ (waitForTaskToken)
```

## What you own
| Stack | Resources |
|---|---|
| `ApiStack` | API Gateway **HTTP API (v2)** (its JWT authorizer reads Cognito ID tokens natively); routes `GET /summary`, `GET /entity/{id}`, `GET /rows`, `POST /ask`, `POST /publish`, `POST /approve`, mapped under `/api` so Michael's CloudFront `/api/*` behaviour reaches them; one Lambda per route (entry points from the handover) |
| `FlowStack` | **Express** ask spine (synchronous; the `retry` `Choice` reads the attempt count the `retry_decision` Lambda returns from the ledger; limit `MAX_CLAIM_ATTEMPTS=2`); **Standard** publish (first state stores the task token via Huvison's function, `waitForTaskToken`, then the status-pack write) |
| `AgentStack` | AgentCore Runtime for the Strands agents (orchestrator, retriever, blocker-analyst, critic, writer), plus the **Lambda fallback**: the same code run in a Lambda (TEAM_PLAN §5 risk). Step Functions can't call AgentCore directly, so `run_orchestrator` and the agent states use a **shim Lambda** that invokes the runtime |
| IAM | one role per function and state machine; Bedrock `InvokeModel` only on the specific model ARNs and the Guardrail ARN; S3 read on `artefacts/`, write only on `status-packs/` for the publish writer; DynamoDB only on the ledger and rejected tables; `states:StartSyncExecution` only on the ask machine for the `ask` Lambda |

## What you build
1. **`ApiStack` with a stub `/summary` Lambda, deploying empty** (D1 12:00). Then the real handlers from `api/handlers.py` *(new, Linus)*. Acceptance: `curl` with an ID token on `/api/summary` returns the summary JSON; without a token it returns 401.
2. **JWT authorizer:** issuer `https://cognito-idp.eu-west-1.amazonaws.com/<pool id>`, audience = the app client ID (Michael's outputs). Acceptance: the E4 lead's token reaches the Lambda with `cognito:groups` and `custom:entity_ids` in `event.requestContext.authorizer.jwt.claims`.
3. **`FlowStack` Express ask spine** from Patrick's step contract and Huvison's `flow/steps.py` *(new)*. One Lambda per state; pass JSON matching the step models; the `Choice` on `retry_decision`'s result. Acceptance: one E4 question runs end to end in AWS (D1 18:00, critic stubbed to pass).
4. **The 29-second limit:** API Gateway cuts synchronous integrations at 29 s. Work with Huvison's timing (D1 18:00). If a run with retries is too slow, implement the agreed async fallback: `POST /ask` starts the execution and returns `run_id`; `GET /ask/{run_id}` polls.
5. **`FlowStack` Standard publish** with `waitForTaskToken` (Huvison's `start_publish` / `decide`). Acceptance: publish waits until `/approve` as the delivery lead, then the status pack appears in `s3://<bucket>/status-packs/`.
6. **`AgentStack`:** AgentCore Runtime + shim, and the Lambda fallback behind a config switch. Acceptance: the same question gives the same claims through both paths.
7. **IAM review:** no `*` actions or resources; one role each. Acceptance: Patrick reviews the roles before clean-deploy check 1.

## Interfaces
| You consume | From |
|---|---|
| `docs/DEVOPS_HANDOVER.md` (entry points, environment, IAM), step models | Patrick |
| `api/handlers.py` entry points | Linus |
| `flow/steps.py`, `flow/publish.py` *(new)* functions | Huvison |
| Bucket, ledger and rejected tables, guardrail ID, user pool + client IDs, CloudFront | Michael (stack outputs) |

| You produce | For |
|---|---|
| API base path `/api` | Mildred, Clement, Linus (deployed-API asker) |
| State machine ARNs (`ASK_STATE_MACHINE_ARN`, `PUBLISH_STATE_MACHINE_ARN`) | Linus, Huvison (environment) |
| The deployed loop | Patrick (walking skeleton, clean deploys) |

## Dependencies
- **You wait on:** the handover and step models (Patrick); the handlers (Linus); the flow functions (Huvison); Michael's outputs. **Deploy stubs first** (a hello-world Lambda per route, a two-state machine), then swap in the real code.
- **Waiting on you:** everyone, for anything running in AWS.

## Your milestones
| When | Milestone |
|---|---|
| D1 12:00 | `ApiStack`, `FlowStack` and `AgentStack` deploy empty, with stubs |
| D1 18:00 | Walking skeleton in AWS: `/api/summary` real; `/ask` runs the Express spine (critic stubbed); clean-deploy check 1 |
| D2 12:00 | JWT authorizer with Cognito end to end; publish + approve live |
| D2 13:00 | Clean-deploy check 2 |

## Definition of done
- [ ] Six routes behind the JWT authorizer; 401 without a token, 403 from the handler out of scope.
- [ ] The Express spine runs the real loop; the retry `Choice` reads the ledger count; publish waits for approval.
- [ ] Agents run on AgentCore (or the documented Lambda fallback, stated in `HANDOFF.md`).
- [ ] Least-privilege roles, reviewed; bundles built with `uv export`, prompts included.
- [ ] Clean-deploy check passed twice; your `HANDOFF.md` lines and `DECISIONS.md` entries.

## Rules and pitfalls specific to you
- **Bedrock `eu.*` inference profiles only;** IAM on those exact ARNs (no `global.*`).
- **The retry decision is a `Choice` on a ledger value,** never a model output.
- **The critic's Lambda must not receive attempts or the plan** in its input (D-007): pass only the claim and scope.
- **Missing prompts in a bundle** makes `load_prompt` refuse to run. Test a deployed bundle.
- **HTTP API (v2), not REST API (v1):** the event shape differs, and Linus's handler tests use v2.

## Getting started
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
git switch -c feature/infra-api-and-flow
```
Then give your assistant `06 Workstreams/prompts/yaw.txt`.

## Who to ask
| Topic | Person |
|---|---|
| Handover, step models, deploys | Patrick |
| Handlers | Linus |
| Flow functions, timing | Huvison |
| Shared outputs, CloudFront | Michael |

Related: [[Workstreams]], [[Team plan]]
