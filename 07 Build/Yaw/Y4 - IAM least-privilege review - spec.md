---
tags: [build, spec, area/devops]
id: Y4
owner: Yaw
status: ready
updated: 2026-10-14
---
# Y4: IAM least-privilege review (spec)
> The check that every workload role is least privilege, run as a test over every synthesized template and reviewed by Patrick before clean-deploy check 1 (D1 18:00). Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` once every stack is merged (Y1, Y2a, Y2b, Y3a, Y3b, and Michael's M2, M3a, M3b, M4a, M4b).

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] (`06 Workstreams/`): the architecture with owners, the code already built, the contracts and the rules (§7).
3. [[Yaw - DevOps]]: the owner's brief; and [[Michael - DevOps]] (the other half of DevOps).
4. [[Build order]]: what this item depends on and unblocks.
5. [[M2 - App, DataStack and LedgerStack - spec]]: the CDK app, `build_stacks`, the prefix, the test fixtures and the patterns every DevOps item follows.
6. Every stack's spec: [[Y1 - ApiStack - spec]], [[Y2a - Express ask spine - spec]], [[Y2b - Standard publish flow - spec]], [[Y3a - AgentCore runtime - spec]], [[Y3b - Agent shim and host switch - spec]], [[M3a - GuardrailStack - spec]], [[M3b - AuthStack - spec]], [[M4a - WebStack - spec]], [[M4b - Observability - spec]], [[M5 - Clean-deploy runbook - spec]].
7. `docs/DEVOPS_HANDOVER.md` in the repo (the IAM column) and `ARCHITECTURE.md` §7.
8. `01 Decisions/`: [[2026-10-13 Team are admins, workload roles least-privilege]]; `05 Workflow/`: [[Handling security findings]].

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Yaw (owner) or Patrick (reviewer). Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. **`tests/infra/test_least_privilege.py` *(new)*** *(new)*: synthesizes the whole app for **both agent hosts** (`agentcore`, `lambda`) through the `stacks_with_context` fixture (Y1), walks every `AWS::IAM::Policy` and every role's inline policies, and fails on: a **wildcard in an action** (`s3:*`, `s3:GetObject*`); a **bare `*` resource** unless every action in the statement is one AWS offers no resource-level permission for (X-Ray, Step Functions log delivery, `cloudwatch:PutMetricData`); an **AWS managed policy** on a role. Exceptions, each with its reason in the test's docstring: CDK's framework constructs by logical-ID fragment (`CustomCDKBucketDeployment`, `CustomS3AutoDeleteObjectsCustomResourceProvider`, `ProviderframeworkonEvent`, `AWS679f53fac002430cb0da5b7982bd2287`) and statements whose every resource is the CDK bootstrap asset bucket. Self-tests prove each kind of violation is caught.
2. **The roles table** in `infra/README.md` ("Workload roles"): every role, its actions and resources, the allowed `*` actions and the CDK framework roles.
3. **Patrick's review** before clean-deploy check 1: the table against the synthesized templates and the deployed roles (read-only).

**Why:** the brief's least-privilege rule ("no `*`") and gate 1 (clean deploy) are checked by humans under time pressure; a test over the templates keeps every later change honest, and the table is what reviewers and judges read.

**Success means:**
- `uv run --locked pytest` → **S + 6 passed** (dry-run 284 → **290**), `TOTAL` 96%; the test reports nothing for any stack on `develop`.
- `infra/README.md` has the "Workload roles" section matching the templates.
- Patrick's OK is recorded in the PR before clean-deploy check 1.

**Assumptions / known findings to reconcile:**
- **Michael (M4a):** as planned, WebStack's `PortalCallbackHandler` is a plain `lambda_.Function`, so CDK attaches `AWSLambdaBasicExecutionRole` (logs actions on `*`). The test reports it. The fix (Michael's file) is to build that handler with `PortalFunction` (Y1) — see the plan, Task 1 Step 4. The Provider framework's own function is a CDK framework role (exempt).
- Michael's other stacks (Guardrail, Auth, Observability) create no IAM roles of their own; the DataStack and WebStack `BucketDeployment` roles are CDK framework roles.
- `states:SendTaskSuccess` / `SendTaskFailure` accept the state machine ARN as a resource (verify on the first real `/approve`, Y2b Review Focus 3).

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| How to check | A pytest over the synthesized templates, both hosts, one test that lists every violation by stack | A manual checklist only (drifts); checkov or cfn-nag in CI (new tools; D-018 deferred IaC scanning) |
| CDK framework roles | Exempt by logical-ID fragment, listed with reasons | Rewriting CDK's providers (not ours to maintain); exempting by stack (too broad) |
| `*` resources | Only for actions with no resource-level permission, listed by name | Allowing `*` with a comment |
| Managed policies | None on our roles | `AWSLambdaBasicExecutionRole` (its logs actions are on `*`) |

## 3. Tests (new, in `tests/`)
- `tests/infra/test_least_privilege.py`: `test_no_stack_grants_wildcards` (every template, both hosts, violations listed by `host/stack`); `test_the_check_catches_each_kind_of_wildcard` (4 cases); `test_the_check_allows_scoped_statements_and_unscopable_actions`.

## 4. Out of scope
- Human (team) IAM: the team are admins in the sandbox (D-005). Resource policies (bucket policies, the X-Ray and Logs resource policies) beyond reading them in the review. Rewriting CDK's framework roles.

Related: [[Build order]], [[Yaw - DevOps]], [[Workstreams]]
