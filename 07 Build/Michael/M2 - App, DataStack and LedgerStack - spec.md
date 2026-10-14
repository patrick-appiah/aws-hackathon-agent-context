---
tags: [build, spec, area/devops]
id: M2
owner: Michael
status: ready
updated: 2026-10-14
---
# M2: the CDK app, DataStack and LedgerStack (spec)
> **The first infrastructure code in the repo.** It sets the patterns every later stack follows (Michael's M3a, M3b, M4a, M4b and Yaw's Y1–Y4): CDK in Python, one `build_stacks` function, a stack prefix for a second copy, stack outputs instead of hardcoded names, `RemovalPolicy.DESTROY`, and CDK unit tests with `aws_cdk.assertions`. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after C1 and M1 are merged.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] (`06 Workstreams/`): the architecture with owners, the code already built, the contracts, and the rules (§7).
3. [[Michael - DevOps]] (the owner's brief: steps 2 and 3) and [[Yaw - DevOps]] (who consumes these stacks).
4. [[Huvison - trust and flow]] §1 (the ledger and rejected-records key layout).
5. [[Build order]]: M2 depends on C1 (the handover and settings) and M1 (the Jenkinsfile this item extends).
6. [[C1 - API and spine contracts - spec]] §5 (settings) and §7 (`docs/DEVOPS_HANDOVER.md`).
7. `01 Decisions/`: [[2026-10-13 Team are admins, workload roles least-privilege]], [[2026-10-14 ERP-layer dataset is the single source]], [[2026-10-14 Two apps in one repo]]; `05 Workflow/`: [[Deploy and demo checks]], [[Dev loop]], [[Working with AI assistants]].

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[AWS sandbox]] for the account); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Michael (owner) or Patrick (settings, handover). Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. **CDK for Python as a dependency**, in a new `infra` dependency group that the `dev` group includes, so `uv sync` installs it for tests and CI while `uv export --no-dev` (every Lambda bundle, D-017) never contains it.
2. **The CDK app:** `infra/app.py` *(new)* with `build_stacks(app) -> PortalStacks` *(new)*, `infra/constants.py` *(new)*, `infra/naming.py` *(new)*, `infra/cdk.json` *(new)*, and `infra/package.json` *(new)* + `package-lock.json` *(new)* pinning the CDK CLI.
3. **`DataStack`** *(new)*: one private S3 bucket; `artefacts/` is a `BucketDeployment` of `demo/data/erp/output/migration/` (14 CSVs + `programme.json`); `status-packs/` is the prefix Huvison's publish flow writes after approval. Exposes the bucket and two scoped IAM statements for Yaw.
4. **`LedgerStack`** *(new)*: the run ledger and the rejected-records table, both `pk`/`sk` strings, on demand. Exposes the tables and a scoped IAM statement for Yaw.
5. **CDK unit tests** in `tests/infra/` *(new)* with `aws_cdk.assertions.Template`, run by the normal `uv run --locked pytest`.
6. **CI runs them:** the Jenkins Python stage installs a pinned, checksum-verified Node (jsii needs it) and treats `infra/` changes as Python changes.
7. **Deployed (verify in AWS):** `npx cdk deploy --all` creates both stacks; the bucket holds the 15 files; Huvison's `DynamoLedger` works against the real table.

**Why:**
- Hard gate 1: "deploys from a clean account". "If it isn't in CDK, it doesn't exist" ([[Michael - DevOps]]).
- The lead's clean-deploy check deploys a **fresh second copy** (`-c prefix=demo2`) into the same account. Every physical name that must be unique (tables, the Cognito domain later) therefore carries the prefix, and nothing else hardcodes a name: other stacks take resources as Python attributes, and humans read stack outputs.
- `RemovalPolicy.DESTROY` and `auto_delete_objects` let a copy be destroyed and redeployed without leftovers.
- CDK tests make the stacks reviewable and keep regressions out without an AWS account; synth needs no credentials.

**Success means:**
- `uv run --locked pytest` → **226 passed** (206 on C1 + 20 new), `TOTAL` 96% (infra isn't in the coverage set, so the figure can't drop).
- `uv export --no-dev --format requirements-txt --no-hashes` contains no `aws-cdk-lib`, `constructs` or `jsii`.
- `cd infra && npm ci && npx cdk synth -q` succeeds **with no AWS credentials** and writes `DataStack.template.json` and `LedgerStack.template.json`.
- The Jenkins Python stage runs the infra tests (Node `v22.23.2` installed in the container).
- Verify in AWS: `aws s3 ls s3://<BucketName>/artefacts/` lists 15 objects; `demo-erp-portal-run-ledger` and `demo-erp-portal-rejected-records` exist with `pk`/`sk` string keys, on demand; a `DynamoLedger` smoke run reads back what it wrote.

**Assumptions:**
- C1 is merged: `config.DEFAULT_REJECTED_TABLE`, `config.DEFAULT_STATUS_PACK_PREFIX` and `docs/DEVOPS_HANDOVER.md` exist on `develop` (names quoted from `feature/api-and-spine-contracts`).
- M1 is merged: the `Jenkinsfile` *(new)* with `BANDIT_CANDIDATES` is on `develop`.
- **Huvison's H1 uses the attribute names `pk` and `sk` in the rejected-records table too**, with `pk = run_id` and `sk = claim_id` as values (his brief: "`pk=run_id, sk=claim_id`"). `LedgerStack` keys both tables with `adapters.dynamo_ledger.PARTITION_KEY` / `SORT_KEY` (`"pk"`, `"sk"`). If H1 picks other attribute names, H1 changes `LedgerStack` with Michael.
- Every Lambda gets the real table names through environment variables set by Yaw's stacks from `ledger.ledger_table.table_name`; nothing relies on the `config.py` default name (`erp-portal-run-ledger`) in AWS.
- The AWS profile `hackathon` points at account `486128667962`, and the account is bootstrapped once with `npx cdk bootstrap aws://486128667962/eu-west-1`.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Where CDK goes in `pyproject.toml` | A separate **`infra`** group (`aws-cdk-lib>=2.273.0`, `constructs>=10.8.1`), pulled into `dev` with `{include-group = "infra"}` (PEP 735). One `uv sync` installs it; `uv export --no-dev` (the bundle command in `docs/DEVOPS_HANDOVER.md`) excludes it (dry-run: 0 lines). `tests/test_dependencies.py` learns to follow `include-group`, so the "every declared dependency is locked" check covers CDK too | Runtime `[project]` dependencies (CDK would ship in every Lambda: 100+ MB); listing CDK straight in `dev` (works, but mixes deploy tooling with test tooling); `[tool.uv] default-groups = ["dev", "infra"]` (dry-run: `uv export --no-dev` then **includes** CDK, 16 lines, so every bundle would bloat); a separate `infra/requirements.txt` *(new)* (retired by D-017) |
| Where CDK tests live | `tests/infra/` (D-016, mirroring `infra/`), so `"infra"` leaves pytest's `norecursedirs` (it was there before `infra/` had code; with `testpaths = ["tests"]`, nothing outside `tests/` is collected anyway) | Tests next to the stacks (D-016 guard) |
| How the CLI runs the app | `infra/cdk.json` `"app": "uv run --locked python app.py"`; `app.py` puts the repo root on `sys.path` (the stacks import `config`, `adapters`, `tools`) | `npx cdk` with a global Python (wrong deps); a root-level `cdk.json` (the README says `cd infra`) |
| CDK CLI version | Pinned in `infra/package.json` (`aws-cdk` `2.1144.0`) + committed `package-lock.json`; `npm ci` then `npx cdk ...` | A global install (each laptop differs); `npx aws-cdk@latest` (unpinned) |
| Deploy-time constants | `infra/constants.py` *(new)*: values that only shape stacks (stack prefix, `artefacts/`, log retention, the `api` base path). Runtime settings stay in `config.py`, and infra **imports** them (`DEFAULT_REGION`, `DEFAULT_LEDGER_TABLE`, `DEFAULT_REJECTED_TABLE`, `DEFAULT_STATUS_PACK_PREFIX`, `DEFAULT_ARTEFACTS_URI`) rather than repeating them | Infra constants in `config.py` (Patrick's file; they're not read from the environment); literals in each stack (magic values) |
| Account | Not in code: `cdk.Environment(region=DEFAULT_REGION)` only; the account comes from `AWS_PROFILE=hackathon` | Hardcoding `486128667962` (a different clean account would break); reading `CDK_DEFAULT_ACCOUNT` in code (only `config.py` reads the environment) |
| Prefix | Context `-c prefix=<p>`, default `demo`, must match `[a-z][a-z0-9-]{1,19}` (it goes into table names and, in M3b, the Cognito domain); stack names `<p>-DataStack`, `<p>-LedgerStack` | No prefix (a second copy collides); free-form prefix (an upper-case one fails late, in Cognito) |
| Physical names | Tables: `<prefix>-<config default>` (`demo-erp-portal-run-ledger`, `demo-erp-portal-rejected-records`): readable, unique per copy. Bucket: CloudFormation-generated (bucket names are global) | The bare `config.py` default (the second copy fails on "already exists"); generated table names (hard to find in the console during the demo) |
| How other stacks get names | Python attributes (`data.bucket`, `ledger.ledger_table`, ...) passed into later stacks by `build_stacks`; CDK turns them into cross-stack exports. Humans read `CfnOutput`s | Hardcoded names; SSM parameters (another moving part) |
| IAM helpers | The owning stack builds the narrowest statement for its resource: `artefacts_read_statement()` (`s3:GetObject` on `artefacts/*`), `status_pack_write_statement()` (`s3:PutObject` on `status-packs/*`), `ledger_statement(actions, include_rejected=...)` (named DynamoDB actions on named tables). Yaw attaches them to his roles | CDK `grant_read` / `grant_read_write` (they add `s3:GetObject*`, `s3:List*`, `dynamodb:BatchWriteItem` ...: wildcard actions that fail Y4's "no `*`" review) |
| Data upload | `BucketDeployment` from `config.DEFAULT_ARTEFACTS_URI` (the committed `demo/data/erp/output/migration/`) to `artefacts/` | A hand `aws s3 sync` (not in CDK: fails the clean-deploy gate); Athena/Glue (roadmap, D-015) |
| Bucket settings | Block all public access, S3-managed encryption, enforce SSL, `DESTROY` + `auto_delete_objects` | Versioning (a two-day demo; makes destroy slower); KMS CMK (cost, more IAM) |
| Tables | On demand, `DESTROY`, no streams, no point-in-time recovery | Provisioned capacity; PITR (adds cost and slows a clean redeploy) |
| CI | The Python stage downloads Node `v22.23.2` (checksum-checked against `SHASUMS256.txt`) into `$HOME/node`; `^infra/` joins `PYTHON_PATHS` | Skipping the CDK tests when Node is missing (a silent green); a third-party Python+Node image |

## 3. Exact shapes
**`infra/constants.py`** *(new)*: `STACK_PREFIX_CONTEXT_KEY = "prefix"`, `DEFAULT_STACK_PREFIX = "demo"`, `STACK_PREFIX_PATTERN = r"[a-z][a-z0-9-]{1,19}"`, `NAME_SEPARATOR = "-"`, `ARTEFACTS_PREFIX = "artefacts/"`, `ARTEFACTS_SOURCE_DIRECTORY = Path(DEFAULT_ARTEFACTS_URI)`, `S3_URI_SCHEME = "s3://"`, `API_BASE_PATH = "api"` (used by Y1's stage and M4a's `/api/*` behaviour), `LOG_RETENTION = logs.RetentionDays.TWO_WEEKS` (every log group later stacks create).

**`infra/naming.py`** *(new)*: `stack_prefix(context_value: object) -> str` (default when `None`; `ValueError("stack prefix must match ...")` otherwise); `physical_name(prefix: str, base_name: str) -> str` (`"demo2"`, `"erp-portal-run-ledger"` → `"demo2-erp-portal-run-ledger"`).

**`infra/app.py`** *(new)*: `REPO_ROOT`; `PortalStacks` (frozen dataclass: `prefix: str`, `data: DataStack`, `ledger: LedgerStack`; later items add one field each, in deploy order: `guardrail`, `auth`, `agent`, `flow`, `api`, `web`, `observability`); `build_stacks(app: cdk.App) -> PortalStacks`; `__main__` builds and `synth()`s.

**`DataStack(scope, construct_id, **kwargs)`** *(new)*:
| Member | Shape |
|---|---|
| `bucket` | `s3.Bucket` (private, SSE-S3, SSL only, DESTROY, auto-delete) |
| `artefacts_uri` (property) | `s3://<bucket>/artefacts/`, the `ARTEFACTS_URI` value in `docs/DEVOPS_HANDOVER.md` |
| `artefacts_read_statement()` | `iam.PolicyStatement(actions=["s3:GetObject"], resources=["<bucket arn>/artefacts/*"])` |
| `status_pack_write_statement()` | `iam.PolicyStatement(actions=["s3:PutObject"], resources=["<bucket arn>/status-packs/*"])` |
| Outputs | `BucketName`, `ArtefactsUri`, `StatusPackPrefix` (`status-packs/`) |

**`LedgerStack(scope, construct_id, *, prefix, **kwargs)`** *(new)*:
| Member | Shape |
|---|---|
| `ledger_table` | `dynamodb.Table` `<prefix>-erp-portal-run-ledger`, `pk` (S, hash) + `sk` (S, range), on demand, DESTROY |
| `rejected_table` | `dynamodb.Table` `<prefix>-erp-portal-rejected-records`, same keys |
| `LEDGER_ACTIONS` (module) | `("dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Query")`, the handover's list |
| `ledger_statement(actions=LEDGER_ACTIONS, *, include_rejected=True)` | those actions on the ledger table (and the rejected table unless `include_rejected=False`, e.g. `/publish`'s `dynamodb:GetItem` on the ledger only) |
| Outputs | `LedgerTableName`, `RejectedTableName` |

## 4. Tests (new, in `tests/`)
- `tests/test_dependencies.py`: `test_included_dependency_groups_are_followed` (a `dev` group that includes `infra` yields both groups' requirements); the existing lock checks then cover CDK.
- `tests/infra/test_naming.py` *(new)*: default prefix; a given prefix kept; `Demo`, `2demo`, `demo_2`, `d`, a 29-character prefix and `""` refused; `physical_name`.
- `tests/infra/conftest.py` *(new)*: `portal_stacks` (module-scoped), the app built with `prefix=test` and **CDK's `aws:cdk:bundling-stacks: []`**, so later stacks' Lambda assets are never bundled in tests.
- `tests/infra/test_app.py` *(new)*: every stack in `PortalStacks` is named `<prefix>-...` and is in `eu-west-1` (later stacks are covered automatically); a bad prefix stops the synth.
- `tests/infra/stacks/test_data_stack.py` *(new)*: the bucket is private, encrypted, `DeletionPolicy: Delete`, with one auto-delete custom resource; the deployment targets `artefacts/` from the 15-file folder; the outputs; the two statements name one action each on their prefix.
- `tests/infra/stacks/test_ledger_stack.py` *(new)*: two tables with `pk`/`sk` strings, on demand, prefixed names, `Delete`; outputs; `ledger_statement` names its four actions on both tables and no `*`; the read-only form covers the ledger only.

## 5. Out of scope
- GuardrailStack, AuthStack (M3a, M3b), WebStack, observability (M4a, M4b), the runbook (M5), and every Yaw stack (Y1–Y4).
- Changing `config.py` or the ledger adapters (Patrick's and Huvison's).
- Lifecycle rules, replication, backups.

Related: [[Build order]], [[Michael - DevOps]], [[Workstreams]]
