---
tags: [workstream, area/team]
owner: Michael
updated: 2026-10-14
---
# Michael: DevOps (CI, data, ledger, guardrail, Cognito, web hosting, observability)
> The repo is the source of truth. Read [[Workstreams]] first. Your row: `docs/TEAM_PLAN.md` §2, workstream 5 (with Yaw, [[Yaw - DevOps]]). You also co-own [[Business case and pitch]] with Patrick.
> **Proposal: confirm this split with Yaw at the first stand-up.** You take CI and the *stateful and edge* stacks; Yaw takes the *compute and orchestration* stacks. No stack is in both briefs.

## Your job in one paragraph
You make the system **deploy from a clean AWS account**: hard gate 1, checked twice, D1 18:00 and D2 13:00.
- **CI:** keep the Jenkins pipeline green on every PR.
- **Stacks you own:** the S3 data bucket with the synthetic dataset; the DynamoDB run ledger and rejected records; the Bedrock Guardrail; Cognito (the one target slice: sign-in with role and entity claims); the portal's S3 + CloudFront hosting; logs, traces and a dashboard.
- **Rule:** everything in CDK. If it isn't in CDK, it doesn't exist.

## Shared DevOps context (same in Yaw's brief)
- **CDK in Python:** `infra/app.py` *(new)* defines every stack; the stack list and resources are in `infra/README.md`.
- **Bootstrap once:** `npx cdk bootstrap aws://486128667962/eu-west-1`. **`eu-west-1` only** (organiser rule). Profile `AWS_PROFILE=hackathon`; your IAM user is `michael.lamptey`.
- **Stack names take a prefix** (a context value, e.g. `-c prefix=demo2`), so the lead can deploy a second, fresh copy for the clean-deploy check.
- **Deploys are manual from the README** (`cd infra && npx cdk deploy --all`). CI builds and tests only, never deploys (D-018).
- **Least privilege** (`ARCHITECTURE.md` §7): one role per Lambda / runtime / state machine, scoped to its S3 prefix, its table and **specific** Bedrock model ARNs. No `*`.
- **Python bundles:** generated at build time with `uv export --no-dev --format requirements-txt --no-hashes`; `agents/prompts/` and `prompts.lock` must ship with any code that loads prompts (D-014, D-017).
- **Your input from the back end:** `docs/DEVOPS_HANDOVER.md` *(new, Patrick)*. Each Lambda's entry point, environment variables and IAM. Settings names come from `config.py` (`get_settings()`), which is the only code that reads environment variables.
- **No console-clicked resources;** no secrets in the repo or the vault.

## What you own
| Stack / file | Resources |
|---|---|
| `Jenkinsfile` (PR #8, open) | path-aware CI: gitleaks, the Python suite (`uv run --locked pytest`), bandit, pip-audit, the front-end build |
| `DataStack` | S3 bucket; `artefacts/` = upload of `demo/data/erp/output/migration/` (all 14 CSVs + `programme.json`); `status-packs/` prefix (written by Huvison's publish flow after approval) |
| `LedgerStack` | DynamoDB run ledger (name from `LEDGER_TABLE`, default `erp-portal-run-ledger`; `pk` string + `sk` string, on-demand); the rejected-records table (`REJECTED_TABLE`, Patrick's new setting). Huvison's approval token is an item `sk=TASK` in the ledger, so nothing extra |
| `GuardrailStack` | Bedrock Guardrail: PII filter + prompt-attack filter, settings from Huvison; outputs `guardrail_id` / version for `GUARDRAIL_ID` / `GUARDRAIL_VERSION` |
| `AuthStack` | Cognito user pool; groups `cfo`, `sponsor`, `delivery_lead`, `entity_lead`; custom attributes `tenant_id` and `entity_ids` (strings); an app client for **managed login, authorization code + PKCE**, callback URL = the CloudFront domain; the test users from Abdul's list (passwords set out of band, never in code) |
| `WebStack` | S3 + CloudFront for the Angular build output **`web/dist/web/browser`**. A **`/api/*` behaviour** forwards to Yaw's API Gateway, so the portal's `apiBaseUrl: '/api'` is same-origin (no CORS) |
| Observability | log groups with retention; X-Ray / AgentCore Observability on; one CloudWatch dashboard (`/ask` latency, errors, tokens and cost per run from the ledger) |
| Clean-deploy runbook | the exact commands, in `README.md` "Run it in 5 commands" with Patrick, including the private npm token for `yarn install` (`web/README.md`) |

## What you build
1. **Get PR #8 reviewed and merged** (Patrick merges).
   - Add the new back-end folders to bandit's `-r` list: today it's `tools adapters agents scripts config.py`; add `api auth flow evals` as they land.
   - Make sure the Jenkins credential `cloud9-npm-token` exists, so the front-end build passes.
   - Acceptance: a PR shows a green Jenkins status check.
2. **`infra/app.py` and `DataStack` deploying empty**, then with the upload (`aws_s3_deployment.BucketDeployment` from `demo/data/erp/output/migration`). Acceptance: `aws s3 ls s3://<bucket>/artefacts/` lists 14 CSVs and `programme.json`.
3. **`LedgerStack`**: keys and names exactly as above. Acceptance: Huvison's DynamoDB adapter works against it (`LEDGER_BACKEND=dynamo`).
4. **`GuardrailStack`** with Huvison's settings. Acceptance: a test call with the guardrail blocks a prompt-attack string.
5. **`AuthStack`** with Abdul's groups and users.
   - The front end sends the **ID token**, because custom claims are only in the ID token. Yaw's JWT authorizer audience is your app client ID; export the pool ID and client ID.
   - Acceptance: signing in as the E4 lead gives a token whose claims include `cognito:groups=[entity_lead]` and `custom:entity_ids=E4`.
6. **`WebStack`** with the `/api/*` behaviour. Acceptance: the portal loads from CloudFront, and `GET /api/summary` reaches the API.
7. **Observability:** the dashboard and log retention. Acceptance: one `/ask` run is visible end to end (trace) with its cost.
8. **The clean-deploy check with Patrick** (D1 18:00, D2 13:00) using a fresh prefix. Acceptance: `npx cdk deploy --all` from clean works twice, with no manual steps.

## Interfaces
| You consume | From |
|---|---|
| `docs/DEVOPS_HANDOVER.md` *(new)*, settings names in `config.py` | Patrick |
| Guardrail settings, ledger key layout | Huvison |
| Cognito users and groups list | Abdul |
| Angular build (`cd web && yarn build` → `web/dist/web/browser`) | Mildred, Clement |

| You produce | For |
|---|---|
| Bucket name, ledger and rejected table names, guardrail ID/version, user pool + client IDs (stack outputs) | Yaw (environment for the Lambdas), Linus, Clement |
| CloudFront URL | everyone |

## Dependencies
- **You wait on:** the handover doc (Patrick) and the Guardrail settings (Huvison). Deploy empty stacks first; the D1 10:30–12:00 target is **every stack deploys empty**.
- **Waiting on you:** Yaw (bucket, tables and pool IDs for his stacks), Clement (Cognito for sign-in), Huvison (the real ledger), Patrick (clean deploys).

## Your milestones
| When | Milestone |
|---|---|
| D1 12:00 | CI merged; DataStack, LedgerStack, GuardrailStack, AuthStack, WebStack deploy empty |
| D1 18:00 | Data uploaded; ledger live; the portal on CloudFront; clean-deploy check 1 |
| D2 12:00 | Cognito end to end (go/no-go); guardrail on |
| D2 13:00 | Clean-deploy check 2 |

## Business case and pitch (co-owned with Patrick)
See [[Business case and pitch]]. You already wrote `business/business-case.md` and `business/product-spec.md`. Plan your time: DevOps is critical on D1, the business documents on D2 afternoon.

## Definition of done
- [ ] PR #8 merged; CI green on PRs.
- [ ] Your five stacks deploy from a clean account with a prefix; no console-made resources.
- [ ] IAM least privilege (no `*`), log retention set, dashboard shows one `/ask` run.
- [ ] Clean-deploy check passed twice; the README commands work as written.
- [ ] Your `HANDOFF.md` lines (what's real, what breaks first) and `DECISIONS.md` entries for infra choices.

## Rules and pitfalls specific to you
- **`eu-west-1` only;** Bedrock model ARNs only for `eu.*` inference profiles.
- **Never put the npm token, Cognito passwords or any secret** in CDK code, the repo or the vault. Use Jenkins credentials and set passwords out of band.
- **`RemovalPolicy.DESTROY` for the demo stacks,** so clean redeploys don't collide with leftovers (S3 needs `auto_delete_objects`).
- **Use CDK outputs** for names other stacks need. Never hardcode them.

## Getting started
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
git switch -c feature/infra-data-and-ledger
```
Then give your assistant `06 Workstreams/prompts/michael.txt`.

## Who to ask
| Topic | Person |
|---|---|
| Handover, settings, deploys | Patrick |
| Ledger layout, guardrail | Huvison |
| API, Flow, Agent stacks | Yaw |
| Users | Abdul |
| Sign-in | Clement |
| Build output | Mildred |

Related: [[Workstreams]], [[Team plan]]
