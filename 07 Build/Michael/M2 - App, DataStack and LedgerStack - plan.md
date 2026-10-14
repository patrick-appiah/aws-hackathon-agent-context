---
tags: [build, plan, area/devops]
id: M2
owner: Michael
spec: "[[M2 - App, DataStack and LedgerStack - spec]]"
status: ready
updated: 2026-10-14
---
# M2: the CDK app, DataStack and LedgerStack (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it. Deploying (Task 7) and pushing are outward-facing: ask Michael first.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]]: the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[M2 - App, DataStack and LedgerStack - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger.
3. [[Workstreams]] §3 (code already built) and §7 (rules), [[Michael - DevOps]] and [[Yaw - DevOps]].
4. [[C1 - API and spine contracts - spec]] §5 and §7; `docs/DEVOPS_HANDOVER.md` in the repo.
5. [[2026-10-13 Team are admins, workload roles least-privilege]] and [[Working with AI assistants]].
6. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Michael (or Patrick for settings and the handover).

**Goal:** the CDK app exists with `DataStack` and `LedgerStack`, unit-tested with `aws_cdk.assertions`, synthesisable with no credentials, run by CI, and deployed to `eu-west-1` (bucket with the 15 synthetic files; the two tables).

**Architecture:** `infra/app.py` builds every stack in deploy order through `build_stacks(app) -> PortalStacks`. Stacks receive earlier stacks' resources as Python attributes and expose scoped IAM statements; names that must be unique carry the `-c prefix=` value. The stacks import settings from `config.py` and key names from `adapters/dynamo_ledger.py`; nothing imports `infra/`. CDK tests live in `tests/infra/` *(new)*.

**Tech stack:** Python 3.11, `aws-cdk-lib` 2.273+ and `constructs` 10.8+ (uv `infra` group), the CDK CLI `aws-cdk` 2.1144.0 via `infra/package.json` *(new)*, Node 22, pytest, uv.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your clone). **Branch:** `feature/infra-data-and-ledger` from an up-to-date `develop`, **after C1 and M1 are merged** ([[Build order]]).
- **Start state:** `uv run --locked pytest` → **206 passed**, `TOTAL` 96% (C1 merged). If yours differs, stop: you are not on the expected `develop`. (Dry-run: every count below was measured on `feature/api-and-spine-contracts` with this plan applied.)
- `eu-west-1` only (`config.DEFAULT_REGION`); Bedrock `eu.*` inference profiles only; synthetic data only; **no secrets anywhere** (no keys, no tokens, no passwords in CDK code, the repo or the vault).
- Settings only in `config.py` (infra **imports** them, never repeats them); domain constants only in `tools/constants.py`; deploy-time constants only in `infra/constants.py` *(new)*; descriptive names; **no single-character names** (the style test scans `infra/` too); no magic numbers or strings. The core (`tools/`) imports no boto3, Strands, adapters, config or os, and never imports `infra`.
- **`RemovalPolicy.DESTROY` on every resource; buckets also `auto_delete_objects=True`.** Stack outputs or Python attributes for every name another stack or person needs, never a hardcoded name.
- Agents reach data only through `tools/agent_tools.py`; scope is never a tool argument; prompts only in `agents/prompts/<agent>.txt` (nothing here touches them).
- Never weaken a security rule (scope gate, create-once ledger, fail-closed critic, escaping) to pass a test.
- Tests in `tests/`, mirroring the code (`tests/infra/` for `infra/`); `uv run --locked pytest` from the repo root; coverage must not drop (96%).
- Deploys are manual from the README (D-018); CI builds and tests only. `export AWS_PROFILE=hackathon AWS_REGION=eu-west-1` before any `aws` or `cdk deploy` command.
- PR to `develop`; Patrick merges; never push to `develop` or `main`; **no `Co-Authored-By` and no "Generated with" lines**.
- Stay in DevOps's files: `infra/` (not Linus's `api.py` and `scope.py` or Huvison's `steps`, `spine`, `local`, `states` and `publish` modules in `infra/functions/` *(new)*), `tests/infra/` (not `tests/infra/functions/` *(new)*), `Jenkinsfile` *(new)*; plus the shared `pyproject.toml`/`uv.lock` (the dependency) and the one helper in `tests/test_dependencies.py` (Task 1: tell Patrick in the PR body).
- No layout or "meta" guard tests: the tests below check what the stacks synthesise, not where files sit.

## Review Focus (what the tests don't fully cover; check by hand at the end)
1. `uv export --no-dev --format requirements-txt --no-hashes | grep -ci "cdk\|jsii\|constructs"` prints `0`: the bundles stay lean. `[tool.uv] default-groups` would silently break this (dry-run: 16 lines).
2. No `grant_*` helper is used anywhere in `infra/` (`grep -rn "grant_" infra/` is empty): they add wildcard actions (`s3:GetObject*`, `s3:List*`) that Y4's review rejects.
3. The second copy really is separate: `cd infra && npx cdk synth -q -c prefix=demo2` and `grep -h '"TableName"' cdk.out/LedgerStack.template.json` shows `demo2-...` names.
4. The rejected-records table's key attribute names (`pk`, `sk`) match what Huvison's H1 writes. Ask him before the PR; if they differ, stop.
5. `infra/package-lock.json` is committed and `infra/node_modules/` *(new)* and `infra/cdk.out/` are not (`git status --short infra/`).

---

### Task 1: CDK as an `infra` dependency group that `dev` includes

**Files:**
- Modify: `tests/test_dependencies.py` (one helper, one test, two constants)
- Modify: `pyproject.toml`, `uv.lock`

**Produces:** the `infra` group (`aws-cdk-lib`, `constructs`); `tests/test_dependencies.py` `_group_requirements(groups, group_name)`, `DEV_GROUP`, `INCLUDE_GROUP_KEY`. **Consumed by:** every later task and every DevOps item.

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/infra-data-and-ledger
mkdir -p .superpowers && printf '# Ledger: M2 App, DataStack and LedgerStack\n' > .superpowers/ledger-M2.md
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
```
Expected: `206 passed`, `TOTAL ... 96%`.

- [ ] **Step 2: Write the failing test.** In `tests/test_dependencies.py`, after `UV_EXECUTABLE = "uv"`, add:
```python
DEV_GROUP = "dev"
INCLUDE_GROUP_KEY = "include-group"
```
and directly before `def test_every_declared_dependency_is_locked():` add:
```python
def test_included_dependency_groups_are_followed():
    groups = {"dev": ["pytest>=8.0", {"include-group": "infra"}], "infra": ["aws-cdk-lib>=2.273.0"]}
    assert _group_requirements(groups, DEV_GROUP) == ["pytest>=8.0", "aws-cdk-lib>=2.273.0"]


```

- [ ] **Step 3: Run it and watch it fail**
```bash
uv run --locked pytest tests/test_dependencies.py --no-cov 2>&1 | grep -E "NameError|passed|failed"
```
Expected: `E       NameError: name '_group_requirements' is not defined`, then `1 failed, 4 passed`.

- [ ] **Step 4: Implement the helper.** In `tests/test_dependencies.py`, replace the whole `_declared_dependency_names` function with:
```python
def _group_requirements(groups: dict, group_name: str) -> list[str]:
    """A dependency group's requirement strings, following its {include-group = "..."} entries (PEP 735)."""
    requirements = []
    for entry in groups[group_name]:
        if isinstance(entry, dict):
            requirements.extend(_group_requirements(groups, entry[INCLUDE_GROUP_KEY]))
        else:
            requirements.append(entry)
    return requirements


def _declared_dependency_names() -> set[str]:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    requirements = [*project["project"]["dependencies"],
                    *_group_requirements(project["dependency-groups"], DEV_GROUP)]
    return {_normalised(DEPENDENCY_NAME.match(requirement).group(0)) for requirement in requirements}
```
Run: `uv run --locked pytest tests/test_dependencies.py --no-cov 2>&1 | tail -1`. Expected: `5 passed`.

- [ ] **Step 5: Add CDK in its own group, included by `dev`**
```bash
uv add --group infra "aws-cdk-lib>=2.273.0" "constructs>=10.8.1"
```
Expected: ends with lines like `+ aws-cdk-lib==2.273.0`, `+ constructs==10.8.1`, `+ jsii==...`. (A newer `aws-cdk-lib` 2.x is fine; the lock records it.)

Then edit `pyproject.toml` by hand:
- in `[dependency-groups]`, make `dev` read:
  ```toml
  dev = [
      "pytest>=8.0",
      "pytest-cov>=5",
      "moto[dynamodb]>=5",
      {include-group = "infra"},   # CDK for the infra tests; --no-dev keeps it out of Lambda bundles
  ]
  ```
  (leave the `infra = [...]` group `uv add` wrote, directly below `dev`);
- in `[tool.pytest.ini_options]`, change `norecursedirs` to:
  ```toml
  norecursedirs = [".venv", ".git", "node_modules", "cdk.out", "demo", "docs"]
  ```
  (`"infra"` goes: the CDK tests are in `tests/infra/`, and with `testpaths = ["tests"]` nothing in `infra/` itself is collected; this edit also lets Linus's and Huvison's `tests/infra/functions/` run). `--cov=infra/functions` in `addopts` is added by whichever of L1 and H5 lands first: this item only checks it, and does not add it (the folder may not exist yet).

```bash
uv lock && uv sync
uv export --no-dev --format requirements-txt --no-hashes | grep -ci "cdk\|jsii\|constructs"
uv run --locked python -c "import aws_cdk, constructs; print('cdk ok')"
```
Expected: `Resolved 77 packages`; the export count is `0`; `cdk ok`.

- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add pyproject.toml uv.lock tests/test_dependencies.py
git commit -m "Add CDK for Python as an infra dependency group, included in dev and kept out of Lambda bundles"
```
Expected: `207 passed`, `TOTAL ... 96%`.

**Task done when:**
- `uv export --no-dev ... | grep -ci "cdk\|jsii\|constructs"` prints `0` and `uv run --locked python -c "import aws_cdk"` succeeds.
- `uv run --locked pytest` → `207 passed`, coverage 96%.

### Task 2: Stack prefix and deploy-time constants

**Files:**
- Create: `infra/__init__.py` *(new)*, `infra/constants.py`, `infra/naming.py` *(new)*
- Create: `tests/infra/test_naming.py` *(new)*

**Produces:** `infra.constants` (`STACK_PREFIX_CONTEXT_KEY`, `DEFAULT_STACK_PREFIX`, `STACK_PREFIX_PATTERN`, `NAME_SEPARATOR`, `ARTEFACTS_PREFIX`, `ARTEFACTS_SOURCE_DIRECTORY`, `S3_URI_SCHEME`, `API_BASE_PATH`, `LOG_RETENTION`); `infra.naming.stack_prefix(context_value: object) -> str`, `infra.naming.physical_name(prefix: str, base_name: str) -> str`. **Consumed by:** Tasks 3–5, M3a, M3b, M4a, M4b, Y1–Y4.

- [ ] **Step 1: Write the failing test.** Create `tests/infra/test_naming.py`:
```python
"""Stack prefixes (infra/naming.py): a second copy of the app gets its own names, and bad prefixes are refused."""
import pytest

from infra.constants import DEFAULT_STACK_PREFIX
from infra.naming import physical_name, stack_prefix


def test_the_default_prefix_is_used_when_none_is_given():
    assert stack_prefix(None) == DEFAULT_STACK_PREFIX


def test_a_given_prefix_is_kept():
    assert stack_prefix("demo2") == "demo2"


@pytest.mark.parametrize("bad_prefix", ["Demo", "2demo", "demo_2", "d", "a-very-long-prefix-for-a-copy", ""])
def test_prefixes_that_cannot_name_a_table_or_domain_are_refused(bad_prefix):
    with pytest.raises(ValueError, match="stack prefix"):
        stack_prefix(bad_prefix)


def test_physical_names_carry_the_prefix():
    assert physical_name("demo2", "erp-portal-run-ledger") == "demo2-erp-portal-run-ledger"
```

- [ ] **Step 2: Run it and watch it fail**
```bash
uv run --locked pytest tests/infra/test_naming.py --no-cov 2>&1 | grep -E "ModuleNotFoundError|error"
```
Expected: `E   ModuleNotFoundError: No module named 'infra.constants'` and `Interrupted: 1 error during collection`.

- [ ] **Step 3: Implement.** Create `infra/__init__.py`:
```python
"""The CDK app (D-018: deployed by hand from the README, never by CI). Stacks live in infra/stacks/, Lambda glue in infra/functions/.

This file must not import CDK: Lambda bundles include it (C2 §3), and a handler import must never pull aws_cdk."""
```
Create `infra/constants.py`:
```python
"""Deploy-time constants for the CDK app. Runtime settings stay in config.py; these only shape the stacks."""
from pathlib import Path

from aws_cdk import aws_logs as logs

from config import DEFAULT_ARTEFACTS_URI

STACK_PREFIX_CONTEXT_KEY = "prefix"               # npx cdk deploy --all -c prefix=demo2 (a fresh second copy)
DEFAULT_STACK_PREFIX = "demo"
STACK_PREFIX_PATTERN = r"[a-z][a-z0-9-]{1,19}"    # lower case: it goes into table names and the Cognito domain
NAME_SEPARATOR = "-"

ARTEFACTS_PREFIX = "artefacts/"                   # ARTEFACTS_URI = s3://<bucket>/artefacts/ (docs/DEVOPS_HANDOVER.md)
ARTEFACTS_SOURCE_DIRECTORY = Path(DEFAULT_ARTEFACTS_URI)   # demo/data/erp/output/migration (D-019)
S3_URI_SCHEME = "s3://"

API_BASE_PATH = "api"                             # CloudFront /api/* → the HTTP API stage named "api" (Y1, M4a)

LOG_RETENTION = logs.RetentionDays.TWO_WEEKS      # every log group we create; a two-day event needs no more
```
Create `infra/naming.py`:
```python
"""Names that must differ between two copies of the app in one account (the clean-deploy check)."""
import re

from infra.constants import DEFAULT_STACK_PREFIX, NAME_SEPARATOR, STACK_PREFIX_PATTERN


def stack_prefix(context_value: object) -> str:
    """The `-c prefix=...` context value, or the default. Anything that can't go into a table name is refused."""
    prefix = DEFAULT_STACK_PREFIX if context_value is None else str(context_value)
    if not re.fullmatch(STACK_PREFIX_PATTERN, prefix):
        raise ValueError(f"stack prefix must match {STACK_PREFIX_PATTERN}, not {prefix!r}")
    return prefix


def physical_name(prefix: str, base_name: str) -> str:
    """`demo` + `erp-portal-run-ledger` → `demo-erp-portal-run-ledger`, so a second copy never collides."""
    return f"{prefix}{NAME_SEPARATOR}{base_name}"
```

- [ ] **Step 4: Run it:** `uv run --locked pytest tests/infra/test_naming.py --no-cov 2>&1 | tail -1`. Expected: `9 passed`.

- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/__init__.py infra/constants.py infra/naming.py tests/infra/test_naming.py
git commit -m "infra: stack prefix for a fresh second copy, and the deploy-time constants"
```
Expected: `216 passed`, `TOTAL ... 96%` (the style test now also scans `infra/`: no single-character names).

**Task done when:**
- `uv run --locked pytest tests/infra --no-cov` → `9 passed`.
- `uv run --locked python -c "from infra.naming import stack_prefix; stack_prefix('Demo')"` raises `ValueError: stack prefix must match ...`.

### Task 3: `infra/app.py` and `DataStack` (bucket + artefacts upload)

**Files:**
- Create: `infra/stacks/__init__.py` *(new)*, `infra/stacks/data_stack.py` *(new)*, `infra/app.py` *(new)*
- Create: `tests/infra/conftest.py` *(new)*, `tests/infra/test_app.py` *(new)*, `tests/infra/stacks/test_data_stack.py` *(new)*

**Produces:** `infra.app.REPO_ROOT`, `infra.app.PortalStacks(prefix, data)`, `infra.app.build_stacks(app: cdk.App) -> PortalStacks`; `infra.stacks.data_stack.DataStack` with `.bucket`, `.artefacts_uri`, `.artefacts_read_statement()`, `.status_pack_write_statement()`; outputs `BucketName`, `ArtefactsUri`, `StatusPackPrefix`; the test fixture `portal_stacks` and `SKIP_ALL_BUNDLING`. **Consumes:** `config.DEFAULT_REGION`, `config.DEFAULT_STATUS_PACK_PREFIX`, Task 2.

- [ ] **Step 1: Write the failing tests.** Create `tests/infra/conftest.py`:
```python
"""Synthesise the CDK app once per test module. No AWS credentials are needed: nothing here looks anything up."""
import aws_cdk as cdk
import pytest

from infra.app import build_stacks
from infra.constants import STACK_PREFIX_CONTEXT_KEY

TEST_PREFIX = "test"
# CDK's own context key: bundle no stack's Lambda code during tests (assets get a placeholder), so tests stay fast
# and offline. A real `npx cdk synth` / `deploy` still bundles.
SKIP_ALL_BUNDLING = {"aws:cdk:bundling-stacks": []}


@pytest.fixture(scope="module")
def portal_stacks():
    return build_stacks(cdk.App(context={STACK_PREFIX_CONTEXT_KEY: TEST_PREFIX, **SKIP_ALL_BUNDLING}))
```
Create `tests/infra/test_app.py`:
```python
"""The CDK app (infra/app.py): every stack carries the prefix and deploys to eu-west-1 only."""
import aws_cdk as cdk
import pytest

from config import DEFAULT_REGION
from infra.app import build_stacks
from infra.constants import STACK_PREFIX_CONTEXT_KEY


def _all_stacks(portal_stacks) -> list[cdk.Stack]:
    return [value for value in vars(portal_stacks).values() if isinstance(value, cdk.Stack)]


def test_every_stack_is_named_with_the_prefix_and_deploys_to_eu_west_1(portal_stacks):
    stacks = _all_stacks(portal_stacks)
    assert stacks, "build_stacks returned no stacks"
    for stack in stacks:
        assert stack.stack_name.startswith(f"{portal_stacks.prefix}-")
        assert stack.region == DEFAULT_REGION


def test_a_bad_prefix_stops_the_synth():
    with pytest.raises(ValueError, match="stack prefix"):
        build_stacks(cdk.App(context={STACK_PREFIX_CONTEXT_KEY: "Bad_Prefix"}))
```
Create `tests/infra/stacks/test_data_stack.py`:
```python
"""DataStack: a private bucket that is emptied on destroy, with the 15 synthetic files uploaded under artefacts/."""
from aws_cdk.assertions import Template

from infra.constants import ARTEFACTS_SOURCE_DIRECTORY

SYNTHETIC_FILE_COUNT = 15   # 14 artefact CSVs + programme.json (D-019)


def _template(portal_stacks) -> Template:
    return Template.from_stack(portal_stacks.data)


def test_the_bucket_is_private_encrypted_and_destroyed_with_the_stack(portal_stacks):
    template = _template(portal_stacks)
    template.has_resource("AWS::S3::Bucket", {
        "DeletionPolicy": "Delete",
        "Properties": {
            "PublicAccessBlockConfiguration": {"BlockPublicAcls": True, "BlockPublicPolicy": True,
                                               "IgnorePublicAcls": True, "RestrictPublicBuckets": True},
            "BucketEncryption": {"ServerSideEncryptionConfiguration": [
                {"ServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]},
        },
    })
    template.resource_count_is("Custom::S3AutoDeleteObjects", 1)


def test_the_synthetic_dataset_is_uploaded_under_artefacts(portal_stacks):
    _template(portal_stacks).has_resource_properties("Custom::CDKBucketDeployment",
                                                     {"DestinationBucketKeyPrefix": "artefacts/"})
    assert len(list(ARTEFACTS_SOURCE_DIRECTORY.iterdir())) == SYNTHETIC_FILE_COUNT


def test_the_bucket_name_and_artefacts_uri_are_outputs(portal_stacks):
    outputs = _template(portal_stacks).find_outputs("*")
    assert {"BucketName", "ArtefactsUri", "StatusPackPrefix"} <= set(outputs)
    assert outputs["StatusPackPrefix"]["Value"] == "status-packs/"


def test_the_read_and_write_statements_are_limited_to_their_prefix(portal_stacks):
    stack = portal_stacks.data
    read = stack.resolve(stack.artefacts_read_statement().to_statement_json())
    write = stack.resolve(stack.status_pack_write_statement().to_statement_json())
    assert read["Action"] == "s3:GetObject" and write["Action"] == "s3:PutObject"
    assert read["Resource"]["Fn::Join"][1][-1] == "/artefacts/*"
    assert write["Resource"]["Fn::Join"][1][-1] == "/status-packs/*"
```

- [ ] **Step 2: Run them and watch them fail**
```bash
uv run --locked pytest tests/infra --no-cov 2>&1 | grep -E "ModuleNotFoundError|ImportError"
```
Expected: `ImportError while loading conftest '.../tests/infra/conftest.py'.` and `E   ModuleNotFoundError: No module named 'infra.app'`.

- [ ] **Step 3: Implement the stack.** Create `infra/stacks/__init__.py`:
```python
"""One module per stack. Each stack exposes the resources other stacks need as attributes, never as names."""
```
Create `infra/stacks/data_stack.py`:
```python
"""DataStack: one private bucket. artefacts/ holds the synthetic dataset; status-packs/ the approved packs."""
from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3_deployment
from constructs import Construct

from config import DEFAULT_STATUS_PACK_PREFIX
from infra.constants import ARTEFACTS_PREFIX, ARTEFACTS_SOURCE_DIRECTORY, S3_URI_SCHEME

ALL_KEYS_UNDER = "*"


class DataStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.bucket = s3.Bucket(
            self, "DataBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        s3_deployment.BucketDeployment(
            self, "ArtefactsUpload",
            sources=[s3_deployment.Source.asset(str(ARTEFACTS_SOURCE_DIRECTORY))],
            destination_bucket=self.bucket,
            destination_key_prefix=ARTEFACTS_PREFIX,
        )
        CfnOutput(self, "BucketName", value=self.bucket.bucket_name)
        CfnOutput(self, "ArtefactsUri", value=self.artefacts_uri)
        CfnOutput(self, "StatusPackPrefix", value=DEFAULT_STATUS_PACK_PREFIX)

    @property
    def artefacts_uri(self) -> str:
        """The ARTEFACTS_URI every Lambda that reads data gets (docs/DEVOPS_HANDOVER.md)."""
        return f"{S3_URI_SCHEME}{self.bucket.bucket_name}/{ARTEFACTS_PREFIX}"

    def artefacts_read_statement(self) -> iam.PolicyStatement:
        """s3:GetObject on artefacts/ only: what the API, step and agent roles get (no List, no other prefix)."""
        return iam.PolicyStatement(actions=["s3:GetObject"],
                                   resources=[self.bucket.arn_for_objects(f"{ARTEFACTS_PREFIX}{ALL_KEYS_UNDER}")])

    def status_pack_write_statement(self) -> iam.PolicyStatement:
        """s3:PutObject on status-packs/ only: for the publish writer, the system's one write (after approval)."""
        return iam.PolicyStatement(
            actions=["s3:PutObject"],
            resources=[self.bucket.arn_for_objects(f"{DEFAULT_STATUS_PACK_PREFIX}{ALL_KEYS_UNDER}")])
```

- [ ] **Step 4: Implement the app.** Create `infra/app.py`:
```python
"""The CDK app: every stack, in deploy order. `cd infra && npx cdk deploy --all [-c prefix=demo2]` (README)."""
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:   # `cdk` runs this file from infra/; the stacks import config, adapters, tools
    sys.path.insert(0, str(REPO_ROOT))

import aws_cdk as cdk

from config import DEFAULT_REGION
from infra.constants import STACK_PREFIX_CONTEXT_KEY
from infra.naming import physical_name, stack_prefix
from infra.stacks.data_stack import DataStack


@dataclass(frozen=True)
class PortalStacks:
    """Every stack of one copy of the app. Later stacks take earlier ones' resources from here."""
    prefix: str
    data: DataStack


def build_stacks(app: cdk.App) -> PortalStacks:
    prefix = stack_prefix(app.node.try_get_context(STACK_PREFIX_CONTEXT_KEY))
    environment = cdk.Environment(region=DEFAULT_REGION)   # the account comes from AWS_PROFILE=hackathon

    def stack_options(stack_id: str) -> dict:
        return {"stack_name": physical_name(prefix, stack_id), "env": environment}

    data = DataStack(app, "DataStack", **stack_options("DataStack"))
    return PortalStacks(prefix=prefix, data=data)


if __name__ == "__main__":
    portal_app = cdk.App()
    build_stacks(portal_app)
    portal_app.synth()
```
`config` can't supply `REPO_ROOT` here: it isn't importable until the path is set.

- [ ] **Step 5: Run them:** `uv run --locked pytest tests/infra --no-cov 2>&1 | tail -1`. Expected: `15 passed` (9 naming + 2 app + 4 data).

- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/app.py infra/stacks/__init__.py infra/stacks/data_stack.py tests/infra/conftest.py tests/infra/test_app.py tests/infra/stacks/test_data_stack.py
git commit -m "infra: the CDK app and DataStack, a private bucket with the synthetic artefacts uploaded under artefacts/"
```
Expected: `222 passed`, `TOTAL ... 96%`.

**Task done when:**
- `uv run --locked pytest tests/infra --no-cov` → `15 passed`.
- `grep -rn "grant_" infra/` prints nothing.

### Task 4: `LedgerStack` (run ledger + rejected records)

**Files:**
- Create: `infra/stacks/ledger_stack.py` *(new)*, `tests/infra/stacks/test_ledger_stack.py` *(new)*
- Modify: `infra/app.py`

**Produces:** `infra.stacks.ledger_stack.LedgerStack(scope, construct_id, *, prefix, **kwargs)` with `.ledger_table`, `.rejected_table`, `.ledger_statement(actions=LEDGER_ACTIONS, *, include_rejected=True)`; `LEDGER_ACTIONS`; outputs `LedgerTableName`, `RejectedTableName`; `PortalStacks.ledger`. **Consumes:** `adapters.dynamo_ledger.PARTITION_KEY`, `SORT_KEY`; `config.DEFAULT_LEDGER_TABLE`, `config.DEFAULT_REJECTED_TABLE`; `infra.naming.physical_name`.

- [ ] **Step 1: Write the failing tests.** Create `tests/infra/stacks/test_ledger_stack.py`:
```python
"""LedgerStack: two on-demand tables keyed pk/sk (strings), named with the stack prefix, destroyed with the stack."""
from aws_cdk.assertions import Template

KEY_SCHEMA = [{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}]
KEY_TYPES = [{"AttributeName": "pk", "AttributeType": "S"}, {"AttributeName": "sk", "AttributeType": "S"}]


def test_both_tables_have_string_keys_on_demand_and_prefixed_names(portal_stacks):
    template = Template.from_stack(portal_stacks.ledger)
    template.resource_count_is("AWS::DynamoDB::Table", 2)
    for table_name in ("test-erp-portal-run-ledger", "test-erp-portal-rejected-records"):
        template.has_resource("AWS::DynamoDB::Table", {
            "DeletionPolicy": "Delete",
            "Properties": {"TableName": table_name, "KeySchema": KEY_SCHEMA, "AttributeDefinitions": KEY_TYPES,
                           "BillingMode": "PAY_PER_REQUEST"},
        })


def test_the_table_names_are_outputs(portal_stacks):
    assert {"LedgerTableName", "RejectedTableName"} <= set(Template.from_stack(portal_stacks.ledger).find_outputs("*"))


def test_the_ledger_statement_names_its_actions_and_both_tables_only(portal_stacks):
    stack = portal_stacks.ledger
    statement = stack.resolve(stack.ledger_statement().to_statement_json())
    assert statement["Action"] == ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Query"]
    assert len(statement["Resource"]) == 2 and "*" not in str(statement["Resource"])


def test_a_role_that_only_reads_the_ledger_gets_neither_writes_nor_the_rejected_table(portal_stacks):
    stack = portal_stacks.ledger
    statement = stack.resolve(stack.ledger_statement(("dynamodb:GetItem",), include_rejected=False).to_statement_json())
    assert statement["Action"] == "dynamodb:GetItem"
    assert statement["Resource"] == stack.resolve(stack.ledger_table.table_arn)
```

- [ ] **Step 2: Run them and watch them fail**
```bash
uv run --locked pytest tests/infra/stacks/test_ledger_stack.py --no-cov 2>&1 | grep -E "^E |passed|failed"
```
Expected: four lines `E       AttributeError: 'PortalStacks' object has no attribute 'ledger'`, then `4 failed`.

- [ ] **Step 3: Implement the stack.** Create `infra/stacks/ledger_stack.py`:
```python
"""LedgerStack: the run ledger (runs, claims, steps, task tokens) and the rejected-records table (H1)."""
from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from constructs import Construct

from adapters.dynamo_ledger import PARTITION_KEY, SORT_KEY
from config import DEFAULT_LEDGER_TABLE, DEFAULT_REJECTED_TABLE
from infra.naming import physical_name

# Exactly what infra/functions/ and adapters/dynamo_ledger.py call (docs/DEVOPS_HANDOVER.md). No Scan, no Delete.
LEDGER_ACTIONS = ("dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Query")


def _string_key(name: str) -> dynamodb.Attribute:
    return dynamodb.Attribute(name=name, type=dynamodb.AttributeType.STRING)


class LedgerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, prefix: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.ledger_table = self._table("RunLedger", physical_name(prefix, DEFAULT_LEDGER_TABLE))
        self.rejected_table = self._table("RejectedRecords", physical_name(prefix, DEFAULT_REJECTED_TABLE))
        CfnOutput(self, "LedgerTableName", value=self.ledger_table.table_name)
        CfnOutput(self, "RejectedTableName", value=self.rejected_table.table_name)

    def _table(self, construct_id: str, table_name: str) -> dynamodb.Table:
        return dynamodb.Table(
            self, construct_id,
            table_name=table_name,
            partition_key=_string_key(PARTITION_KEY),
            sort_key=_string_key(SORT_KEY),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

    def ledger_statement(self, actions: tuple[str, ...] = LEDGER_ACTIONS, *,
                         include_rejected: bool = True) -> iam.PolicyStatement:
        """The given actions on the ledger (and the rejected-records table unless told not to), nothing else."""
        tables = [self.ledger_table, self.rejected_table] if include_rejected else [self.ledger_table]
        return iam.PolicyStatement(actions=list(actions), resources=[table.table_arn for table in tables])
```
`adapters/dynamo_ledger.py` imports boto3 only inside `DynamoLedger.__init__`, so importing its key names costs nothing.

- [ ] **Step 4: Wire it into the app.** In `infra/app.py`:
  - add `from infra.stacks.ledger_stack import LedgerStack` after the `DataStack` import;
  - add the field `ledger: LedgerStack` after `data: DataStack` in `PortalStacks`;
  - in `build_stacks`, after the `data = ...` line, add
    `ledger = LedgerStack(app, "LedgerStack", prefix=prefix, **stack_options("LedgerStack"))`
    and change the return to `return PortalStacks(prefix=prefix, data=data, ledger=ledger)`.

- [ ] **Step 5: Run them:** `uv run --locked pytest tests/infra --no-cov 2>&1 | tail -1`. Expected: `19 passed`.

- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/stacks/ledger_stack.py infra/app.py tests/infra/stacks/test_ledger_stack.py
git commit -m "infra: LedgerStack, the run ledger and rejected-records tables (pk/sk strings, on demand, prefixed names)"
```
Expected: `226 passed`, `TOTAL ... 96%`.

**Task done when:**
- `uv run --locked pytest` → `226 passed`, 96%.
- `test_app.py` covers `LedgerStack` without being edited (it iterates every stack in `PortalStacks`).

### Task 5: The CLI: `cdk.json`, the pinned CDK CLI, synth with no credentials, and the README

**Files:**
- Create: `infra/cdk.json` *(new)*, `infra/package.json`, `infra/package-lock.json` *(new)*
- Modify: `infra/README.md`

**Produces:** `cd infra && npm ci && npx cdk synth -q`. **Consumes:** Tasks 3–4.

- [ ] **Step 1: Create `infra/cdk.json`:**
```json
{
  "app": "uv run --locked python app.py",
  "watch": {"exclude": ["cdk.out", "node_modules"]}
}
```
- [ ] **Step 2: Create `infra/package.json`:**
```json
{
  "name": "erp-portal-infra",
  "private": true,
  "description": "Pins the CDK CLI for infra/ (npm ci, then npx cdk ...). The CDK library itself is Python (pyproject.toml, infra group).",
  "engines": {"node": ">=22"},
  "devDependencies": {
    "aws-cdk": "2.1144.0"
  }
}
```
Then generate the lock and install:
```bash
cd infra && npm install --no-audit --no-fund && cd ..
git status --short infra/
```
Expected: `added 1 package`; `git status` shows `?? infra/cdk.json`, `?? infra/package.json`, `?? infra/package-lock.json` and **not** `node_modules/` (ignored by the root `.gitignore`). `aws-cdk` is public, so no npm token is needed.

- [ ] **Step 3: Synth with no AWS credentials** (proves no lookups and no account in code):
```bash
cd infra && env -u AWS_PROFILE AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q; cd ..
ls infra/cdk.out/*.template.json
cd infra && npx cdk synth -q -c prefix=demo2 && grep -h '"TableName"' cdk.out/LedgerStack.template.json; cd ..
```
Expected: `Successfully synthesized to .../infra/cdk.out` (plus a note about unconfigured feature flags, which is fine); `infra/cdk.out/DataStack.template.json` *(new)* and `infra/cdk.out/LedgerStack.template.json` *(new)*; then `"TableName": "demo2-erp-portal-run-ledger",` and `"TableName": "demo2-erp-portal-rejected-records",`. `cdk.out/` is git-ignored.

- [ ] **Step 4: Document the commands.** In `infra/README.md`, replace the line `Bootstrap once: \`npx cdk bootstrap aws://796973512193/eu-west-1\`` with:
```markdown
## Commands
Run from the repo root unless a line starts with `cd infra`. Set `export AWS_PROFILE=hackathon AWS_REGION=eu-west-1` before anything that talks to AWS.

| What | Command |
|---|---|
| Install (once) | `uv sync` (the CDK library comes in the `infra` group, included by `dev`) and `cd infra && npm ci` (the pinned CDK CLI) |
| Unit tests (no AWS needed) | `uv run --locked pytest tests/infra` |
| Synth (no AWS needed) | `cd infra && npx cdk synth -q` |
| Bootstrap (once per account) | `cd infra && npx cdk bootstrap aws://796973512193/eu-west-1` |
| Deploy (manual, D-018) | `cd infra && npx cdk deploy --all` |
| A fresh second copy | `cd infra && npx cdk deploy --all -c prefix=demo2` (every stack, table and domain gets the prefix) |
| Remove a copy | `cd infra && npx cdk destroy --all -c prefix=demo2` (every resource is `DESTROY`; buckets empty themselves) |
| Read outputs | `aws cloudformation describe-stacks --stack-name demo-DataStack --query "Stacks[0].Outputs"` |

Stacks are built in `infra/app.py` (`build_stacks`, in deploy order). Each stack exposes what others need as attributes and as `CfnOutput`s; nothing hardcodes a name. IAM statements come from the stack that owns the resource (`DataStack.artefacts_read_statement()`, `LedgerStack.ledger_statement(...)`), never from `grant_*` helpers, which add wildcard actions.
```
Then run the doc checks (they read Markdown commands):
```bash
uv run --locked pytest tests/test_dependencies.py tests/test_code_style.py --no-cov 2>&1 | tail -1
```
Expected: `16 passed` (dry-run), 0 failed.

- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add infra/cdk.json infra/package.json infra/package-lock.json infra/README.md
git commit -m "infra: pin the CDK CLI, run the app through uv, and document synth and deploy commands"
```
Expected: `226 passed`, `TOTAL ... 96%`.

**Task done when:**
- `cd infra && npm ci && npx cdk synth -q` succeeds with no credentials and writes the two templates.
- `-c prefix=demo2` gives `demo2-` table names.

### Task 6: CI runs the CDK tests (Node in the Python container)

**Files:**
- Modify: `Jenkinsfile`

**Produces:** the `NODE_VERSION` environment variable; Node on the Python stage's `PATH`; `^infra/` in `PYTHON_PATHS`. **Consumes:** M1's Jenkinsfile.

- [ ] **Step 1: Show the failure CI would hit.** jsii (under `aws_cdk`) needs Node, and `python:3.11-bookworm` has none:
```bash
docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -e UV_PYTHON_DOWNLOADS=never -e UV_PROJECT_ENVIRONMENT=/tmp/venv \
  -v "$PWD:/work" -w /work python:3.11-bookworm bash -euo pipefail -c '
    pip install --quiet --user "uv==0.13.0"; export PATH="$HOME/.local/bin:$PATH"
    uv sync --locked -q
    uv run --locked pytest tests/infra/stacks/test_ledger_stack.py --no-cov 2>&1 | tail -2'
```
Expected: a jsii traceback ending `AttributeError: '_NodeProcess' object has no attribute '_process'` (Node could not be started).

- [ ] **Step 2: Edit the Jenkinsfile.**
  - In `environment { ... }`, change `PYTHON_PATHS` to add `|^infra/` before `|^Jenkinsfile$`:
    ```groovy
    PYTHON_PATHS = '^ALL$|\\.py$|\\.md$|^pyproject\\.toml$|^uv\\.lock$|^\\.python-version$|^agents/prompts/|^demo/data/|^infra/|^Jenkinsfile$'
    ```
  - In `environment { ... }`, after `BANDIT_CANDIDATES`, add:
    ```groovy
    // jsii (behind the CDK tests in tests/infra/) needs Node; python:3.11-bookworm has none.
    NODE_VERSION = 'v22.23.2'
    ```
  - In the Python stage's `docker run` line, change `-e UV_VERSION -e BANDIT_CANDIDATES` to `-e UV_VERSION -e BANDIT_CANDIDATES -e NODE_VERSION`.
  - Directly after the line `export PATH="$HOME/.local/bin:$PATH"` in that stage, add:
    ```bash
              node_archive="node-${NODE_VERSION}-linux-x64.tar.xz"
              cd "$HOME"
              curl -fsSLO "https://nodejs.org/dist/${NODE_VERSION}/${node_archive}"
              curl -fsSL "https://nodejs.org/dist/${NODE_VERSION}/SHASUMS256.txt" | grep -F "  ${node_archive}" | sha256sum -c -
              mkdir -p node && tar -xJf "${node_archive}" -C node --strip-components=1 && rm "${node_archive}"
              export PATH="$HOME/node/bin:$PATH"
              cd /work
    ```
    (No single quotes inside: the block is within `bash -c '...'`. `sha256sum -c` fails the stage if the download was tampered with.)

- [ ] **Step 3: Dry-run the new stage locally:**
```bash
docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -e UV_PYTHON_DOWNLOADS=never -e UV_PROJECT_ENVIRONMENT=/tmp/venv \
  -e NODE_VERSION=v22.23.2 -v "$PWD:/work" -w /work python:3.11-bookworm bash -euo pipefail -c '
    pip install --quiet --user "uv==0.13.0"; export PATH="$HOME/.local/bin:$PATH"
    node_archive="node-${NODE_VERSION}-linux-x64.tar.xz"
    cd "$HOME"
    curl -fsSLO "https://nodejs.org/dist/${NODE_VERSION}/${node_archive}"
    curl -fsSL "https://nodejs.org/dist/${NODE_VERSION}/SHASUMS256.txt" | grep -F "  ${node_archive}" | sha256sum -c -
    mkdir -p node && tar -xJf "${node_archive}" -C node --strip-components=1 && rm "${node_archive}"
    export PATH="$HOME/node/bin:$PATH"
    cd /work
    node --version
    uv sync --locked -q
    uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"'
```
Expected: `node-v22.23.2-linux-x64.tar.xz: OK`, `v22.23.2`, `226 passed`, `TOTAL ... 96%`.

- [ ] **Step 4: Commit**
```bash
git add Jenkinsfile
git commit -m "CI: install a checksum-verified Node in the Python stage so the CDK tests run, and treat infra/ as Python"
```
Expected: the commit is created; `git diff develop --stat` lists only the files of Tasks 1–6.

**Task done when:**
- The local container run prints `226 passed`.
- `grep -n "NODE_VERSION\|\^infra/" Jenkinsfile` shows the new lines.

### Task 7: Deploy, check, and open the PR (verify in AWS; ask Michael first)

**Files:** none (deploy and checks). **Produces:** the deployed `demo-DataStack` and `demo-LedgerStack` and their outputs, for Huvison, Yaw and Linus.

- [ ] **Step 1: Bootstrap once (verify in AWS)** — skip if `aws cloudformation describe-stacks --stack-name CDKToolkit` already succeeds:
```bash
cd infra && npx cdk bootstrap aws://796973512193/eu-west-1; cd ..
```
Expected: `Environment aws://796973512193/eu-west-1 bootstrapped`.

- [ ] **Step 2: Deploy (verify in AWS)**
```bash
cd infra && npx cdk deploy --all --require-approval never; cd ..
```
Expected: `demo-DataStack` and `demo-LedgerStack` end with `✅`; the outputs print `DataStack.BucketName = demo-datastack-databucket...`, `DataStack.ArtefactsUri = s3://.../artefacts/`, `DataStack.StatusPackPrefix = status-packs/`, `LedgerStack.LedgerTableName = demo-erp-portal-run-ledger`, `LedgerStack.RejectedTableName = demo-erp-portal-rejected-records`.

- [ ] **Step 3: The bucket holds the dataset (verify in AWS)**
```bash
BUCKET=$(aws cloudformation describe-stacks --stack-name demo-DataStack --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text)
aws s3 ls "s3://$BUCKET/artefacts/" | wc -l
ARTEFACTS_URI="s3://$BUCKET/artefacts/" uv run --locked python -c "
from adapters import repository_from_settings
from config import DEFAULT_TENANT_ID
from tools import metrics
from tools.models import Scope
scope = Scope(user_id='smoke-cfo', role='cfo', tenant_id=DEFAULT_TENANT_ID, entity_ids=('*',))
print(metrics.portfolio_summary(repository_from_settings(), scope)['overall']['records_reconciled'])"
```
Expected: `15`; then `18420` (the dashboard figure, read from S3 through `CsvRepository`).

- [ ] **Step 4: The ledger works with Huvison's adapter (verify in AWS)**
```bash
aws dynamodb describe-table --table-name demo-erp-portal-run-ledger --query "Table.[KeySchema, BillingModeSummary.BillingMode]" --output json
uv run --locked python -c "
from adapters.dynamo_ledger import DynamoLedger
from config import DEFAULT_REGION, DEFAULT_TENANT_ID
from tools.models import Scope
ledger = DynamoLedger('demo-erp-portal-run-ledger', DEFAULT_REGION)
ledger.start_run('smoke-m2', Scope(user_id='smoke-cfo', role='cfo', tenant_id=DEFAULT_TENANT_ID, entity_ids=('*',)), 0.5)
print(ledger.budget_remaining('smoke-m2'))"
aws dynamodb delete-item --table-name demo-erp-portal-run-ledger --key '{"pk": {"S": "smoke-m2"}, "sk": {"S": "RUN"}}'
```
Expected: the key schema `pk` HASH, `sk` RANGE and `PAY_PER_REQUEST`; then `0.5`; the delete returns nothing (the smoke item is removed so the create-once rule doesn't block a re-run; you are an admin user, D-005; workload roles never get `DeleteItem`).

- [ ] **Step 5: Review Focus, then the PR (with Michael's OK).** Work through the Review Focus by hand and write each result in the ledger. Then:
```bash
git diff develop --stat
git push -u origin feature/infra-data-and-ledger
gh pr create --repo Amali-Tech/cloud-9-hackathon --base develop --title "infra: CDK app, DataStack and LedgerStack (M2)" --body-file .superpowers/pr-M2.md
```
Write `.superpowers/pr-M2.md` first: what changed (the `infra` group and why it's in `dev`; the stacks, their outputs and IAM helpers; the CI Node step), the test count (`226 passed`, 96%), the deployed outputs from Step 2, the `tests/test_dependencies.py` helper (for Patrick), and the ledger's `Ruling:` lines. No attribution lines.
Expected: the PR opens against `develop`; the Jenkins check runs the Python stage (it sees `infra/` and `.py` changes) and goes green.

- [ ] **Step 6: Tell the team:** post the five output values (not secrets) for Yaw (Lambda environment), Huvison (`LEDGER_BACKEND=dynamo`, `LEDGER_TABLE`, `REJECTED_TABLE`) and Linus (`ARTEFACTS_URI`). Update [[Build order]]: M2 `in review (PR #nn)`.

**Task done when:**
- `aws s3 ls s3://<bucket>/artefacts/ | wc -l` → `15` and the smoke run printed `18420` and `0.5`.
- The PR is open with a green Jenkins check.

## Done means
- [ ] **The suite is green with the CDK tests.** Verify: `uv run --locked pytest 2>&1 | grep -E "passed|TOTAL"` on the branch → `226 passed`, `TOTAL ... 96%`.
- [ ] **Bundles stay lean.** Verify: `uv export --no-dev --format requirements-txt --no-hashes | grep -ci "cdk\|jsii\|constructs"` → `0`.
- [ ] **Synth needs no credentials, and a second copy is separate.** Verify: `cd infra && npm ci && env -u AWS_PROFILE AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null npx cdk synth -q -c prefix=demo2 && grep -h '"TableName"' cdk.out/LedgerStack.template.json` → `Successfully synthesized` and two `demo2-erp-portal-...` names.
- [ ] **No wildcard grants.** Verify: `grep -rn "grant_" infra/` → nothing; `grep -h '"Action"' infra/cdk.out/*.template.json` shows no `"*"` action in a role we wrote (the BucketDeployment and auto-delete roles are CDK's own; Y4 lists them).
- [ ] **CI runs the infra tests.** Verify: the PR's Jenkins log shows `node-v22.23.2-linux-x64.tar.xz: OK` and the pytest line `226 passed`.
- [ ] **The data is in S3 (verify in AWS).** Verify: `aws s3 ls s3://$(aws cloudformation describe-stacks --stack-name demo-DataStack --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text)/artefacts/ | wc -l` → `15`.
- [ ] **The tables exist as specified (verify in AWS).** Verify: `aws dynamodb describe-table --table-name demo-erp-portal-rejected-records --query "Table.KeySchema"` → `pk` HASH, `sk` RANGE; `aws dynamodb describe-table --table-name demo-erp-portal-run-ledger --query "Table.BillingModeSummary.BillingMode"` → `"PAY_PER_REQUEST"`.
- [ ] **Huvison's adapter works against AWS.** Verify: Task 7 Step 4's smoke run prints `0.5` (re-runnable after its delete).
- [ ] **PR open to `develop`, green, and [[Build order]] says `in review (PR #nn)`.** Verify: `gh pr checks <nn> --repo Amali-Tech/cloud-9-hackathon` → the Jenkins check `pass`.

## Never
- Use `grant_read`, `grant_read_write` or any `grant_*` helper (wildcard actions).
- Hardcode the account ID, a bucket name or a table name outside `infra/naming.py`'s prefix rule.
- Put `aws-cdk-lib` in the runtime dependencies or make `infra` a default group.
- Create or change anything in the console.
- Deploy from CI; push to `develop` or `main`; add attribution lines.

Related: [[M2 - App, DataStack and LedgerStack - spec]], [[Build order]], [[Michael - DevOps]], [[How to execute a plan]]
