---
tags: [build, spec, area/repo]
id: C2
owner: Patrick
status: approved (Patrick, 2026-10-14)
updated: 2026-10-14
---
# C2: Repo layout, the brief's five folders (spec)
> **No new top-level folders.** The code the plans put in **api/**, **auth/** and **flow/** goes into the folders the brief prescribes: pure logic in `tools/`, Lambda and Step Functions glue in `infra/functions/` *(new)*. Nothing moves in the repo today, because those three folders were never created. Only plan text changes.

## 0. Context: read the vault first
Read, in order:
1. [[Hackathon guideline]] §04 "Delivery guidelines": the repo shape every team uses, and why ("a judge can navigate any team's work in two minutes").
2. [[Pitch track grading rubric]]: "README runs in 5 commands; **brief's layout followed**" is part of an 8-point criterion.
3. [[Workstreams]] and [[Build order]]: who owns which item.
4. [[C1 - API and spine contracts - spec]]: the contracts these files implement.

When this spec is silent, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If it's still unclear, ask Patrick.

## 1. Intent
- **What:** every planned module under **api/**, **auth/** and **flow/** moves to a path inside the brief's folders. The test files and coverage flags move with them.
- **Why:** the brief fixes the repo shape for all ten teams, and the rubric scores whether it is followed. Three extra top-level folders are three things a judge has to work out.
- **Success means:**
  - no plan or doc creates **api/**, **auth/** or **flow/**;
  - the release checker passes on every `07 Build` folder;
  - `docs/TEAM_PLAN.md` §2, `docs/DEVOPS_HANDOVER.md` and `ARCHITECTURE.md` name the new paths;
  - `README.md` has a short repo map.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Where pure logic goes | `tools/`, flat (no subfolders), only for modules that import nothing but `tools` and the standard library. The architecture test forbids `config`, `adapters`, `boto3`, `strands` and `os` in `tools/` | A **tools/flow/** subpackage (breaks the flat "deterministic code" folder for two files) |
| Where handlers and glue go | `infra/functions/`: everything that reads `config`, uses `adapters`, or is a Lambda or Step Functions entry point | Keeping **api/**, **auth/** and **flow/** with a README map (three extra top-level folders) |
| Subfolders in the five | Only where a folder holds different kinds of things: `agents/prompts/` (exists), `evals/inputs/` and `evals/expected/` (exist), `demo/data/` (exists), and `infra/stacks/` *(new)*, `infra/functions/`, `infra/agent_runtime/` *(new)* (planned by M and Y) | Subfolders in `tools/` or `agents/` |
| Existing extra folders | `adapters/`, `tests/`, `scripts/`, `docs/`, `business/` and `web/` stay; the README map explains each in one line | Moving `adapters/` (the architecture test enforces that boundary; merged code imports it) |
| Scope from the token | `infra/functions/scope.py` *(new)*: it reads `AUTH_MODE` and `DEMO_ROLE` from `config` | **tools/scope.py** (the core may not import `config`) |

## 3. The mapping (exact)
| Planned path (old) | New path | Import (old → new) | Owner |
|---|---|---|---|
| **flow/budget.py** | `tools/budget.py` *(new)* | `flow.budget` → `tools.budget` | Huvison (H2a) |
| **flow/cost.py** | `tools/cost.py` *(new)* | `flow.cost` → `tools.cost` | Huvison (H5) |
| **auth/scope.py** | `infra/functions/scope.py` | `auth.scope` → `infra.functions.scope` *(new)* | Linus (L1) |
| **api/handlers.py** | `infra/functions/api.py` *(new)* | `api.handlers` → `infra.functions.api` *(new)*; Lambda handler `api.handlers:summary` → `infra.functions.api.summary` *(new)* (same for `entity`, `rows`, `ask`, `publish`, `approve`) | Linus (L1–L3) |
| **flow/steps.py** | `infra/functions/steps.py` *(new)* | `flow.steps` → `infra.functions.steps` *(new)* | Huvison (H2a, H2b) |
| **flow/spine.py** | `infra/functions/spine.py` *(new)* | `flow.spine` → `infra.functions.spine` *(new)* | Huvison (H2b) |
| **flow/local.py** | `infra/functions/local.py` *(new)* | `flow.local` → `infra.functions.local` *(new)* (`flow.local:ask` → `infra.functions.local.ask` *(new)*) | Huvison (H2b) |
| **flow/handlers.py** | `infra/functions/states.py` *(new)* (the Step Functions state handlers; renamed so it isn't confused with `api.py`) | `flow.handlers` → `infra.functions.states` *(new)* | Huvison (H2b, H4) |
| **flow/publish.py** | `infra/functions/publish.py` *(new)* | `flow.publish` → `infra.functions.publish` *(new)* | Huvison (H4) |
| **api/__init__.py**, **auth/__init__.py**, **flow/__init__.py** | `infra/__init__.py` *(new)* and `infra/functions/__init__.py` *(new)* (docstring only), created by whichever item lands first | | first item to land |

**Tests move with their code (mirroring rule):**
- **tests/api/** → `tests/infra/functions/` *(new)* (for example `test_api.py`);
- **tests/auth/test_scope.py** → `tests/infra/functions/test_scope.py` *(new)*;
- **tests/flow/test_budget.py** → `tests/tools/test_budget.py` *(new)*;
- **tests/flow/test_cost.py** → `tests/tools/test_cost.py` *(new)*;
- the other **tests/flow/*** → `tests/infra/functions/*` *(new)*.

**Coverage and collection:**
- Replace `--cov=api`, `--cov=auth` and `--cov=flow` with `--cov=infra/functions`. `tools.budget` and `tools.cost` are already covered by `--cov=tools`.
- In `pyproject.toml`'s `norecursedirs`, drop `"infra"` (it would skip `tests/infra/` *(new)*) and keep `"cdk.out"`, `"node_modules"`, `".venv"` and `"demo"`.
- Whichever item lands first makes both edits; later items only add nothing or check.

**Bundling (DevOps):**
- The Lambda asset includes `tools/`, `agents/`, `adapters/`, `config.py`, `infra/__init__.py` and `infra/functions/`.
- `infra/__init__.py` must not import CDK, so a handler import never pulls `aws_cdk`.

**Not changed:**
- CDK attribute names such as `api.http_api` or `auth.user_pool` (Python attributes on stack objects, not packages).
- The front end's `web/src/app/core/api/`.
- `agents/`, `tools/` (apart from the two new files), `evals/` and `demo/`.

## 4. Docs
- `docs/TEAM_PLAN.md` §2: the workstream folder lists use the new paths. Huvison gains `tools/budget.py` and `tools/cost.py`, and the `infra/functions/` modules above. Linus gains `infra/functions/api.py` and `infra/functions/scope.py`. DevOps keeps `infra/app.py` *(new)*, `infra/stacks/` and `infra/agent_runtime/`.
- `docs/DEVOPS_HANDOVER.md`: entry points become `infra.functions.<module>.<function>` *(new)*.
- `ARCHITECTURE.md`: one line on where handlers live.
- `README.md`: a repo map, one line per top-level folder, tying it to the brief.
- `DECISIONS.md`: D-024, "Repo layout: the brief's five folders" (D-023 stays reserved for the H7 latency decision).

## 5. Out of scope
- Moving any merged code.
- Changing the contracts (C1) or any behaviour.
- The front end's layout (`web/`, D-020).

Related: [[Build order]], [[Hackathon guideline]], [[C1 - API and spine contracts - spec]]
