---
tags: [build, spec, area/devops]
id: M5
owner: Michael
status: ready
updated: 2026-10-14
---
# M5: the clean-deploy runbook and the two checks (spec)
> **Hard gate 1 is "deploys from a clean account".** This item writes the exact commands into the repo (root `README.md` "Run it in 5 commands", `infra/README.md` "Clean-deploy check") and runs the check with Patrick twice: D1 18:00 and D2 13:00, each time as a **fresh second copy** with a new stack prefix. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop`.

## 0. Context: read the vault first
The vault is the shared context space. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before changing anything, read, in this order:**
1. [[How to execute a plan]].
2. [[Workstreams]] §5 (timeline: the checks at D1 18:00 and D2 13:00), §6 (hard gates) and §7 (rules).
3. [[Michael - DevOps]] ("What you build" step 8) and [[Yaw - DevOps]].
4. [[Build order]]: M5 depends on every stack being merged.
5. The stack items whose commands this runbook strings together: [[M2 - App, DataStack and LedgerStack - spec]], [[M3a - GuardrailStack - spec]], [[M3b - AuthStack - spec]], [[M4a - WebStack - spec]], [[M4b - Observability - spec]], [[Y1 - ApiStack - spec]], [[Y2a - Express ask spine - spec]], [[Y2b - Standard publish flow - spec]], [[Y3a - AgentCore runtime - spec]], [[Y3b - Agent shim and host switch - spec]], [[Y4 - IAM least-privilege review - spec]].
6. `05 Workflow/`: [[Deploy and demo checks]], [[Dev loop]]; `04 Reference/`: [[AWS sandbox]], [[Hackathon guideline]], [[Judging rubric]].

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/`, `03 Sessions/`, `Open follow-ups.md`. If it's still unclear, stop and ask Michael or Patrick. Never invent a command: every command below comes from a merged item's plan.

## 1. Intent
**What:**
1. **Root `README.md` "Run it in 5 commands"** (Patrick's file; written together): the five lines that take a fresh clone to a deployed portal and one answered question, with the prerequisites above them and the second-copy flags below.
2. **`infra/README.md` "Clean-deploy check"**: an eleven-row table (step, command, expected result) for a fresh copy with prefix `$PREFIX`, from clone to destroy, plus the two known recovery moves (the Cognito callback revision, the agent-host fallback).
3. **Run it twice with Patrick:** prefix `demo2` at D1 18:00, `demo3` at D2 13:00, from a fresh clone, with no command outside the table. Record the result (pass/fail per row, timings) in `HANDOFF.md` lines given to Abdul and in the PR.
4. **Infra decisions recorded:** one `DECISIONS.md` entry (next free number; D-022 is taken) for the CDK conventions every DevOps item uses.

**Why:**
- The organisers check gate 1 by running the README. A command that only works on the author's laptop (a cached `cdk.out`, a manual `aws s3 sync`, a console click) fails it.
- A second copy in the same account surfaces every hardcoded name and every account-wide singleton: tables and the Cognito domain carry the prefix (M2, M3b), and Transaction Search is switched off for the copy (`-c transaction_search=off`, M4b).
- Rehearsing twice leaves time to fix what the first run finds.

**Success means:**
- `README.md` and `infra/README.md` contain the blocks in §3, and the doc checks pass (`tests/test_dependencies.py` reads every command in Markdown: `uv run --locked pytest`, `uv run python scripts/...`).
- Both checks pass every row: the second copy deploys with only the table's commands, the data, API, portal and ask rows show their expected results, and `cdk destroy` leaves no `$PREFIX-` stack.
- `HANDOFF.md` (through Abdul) states the two check results; `DECISIONS.md` has the infra-conventions entry.

**Assumptions:**
- Every stack item (M2, M3a, M3b, M4a, M4b, Y1, Y2a, Y2b, Y3a, Y3b) is merged, and Y4's review has passed, before the first check. If one isn't, run the check with what is merged and record the missing rows as "not built", never as "pass".
- `scripts/ask.py` *(new)* (Patrick's P3) exists for the fifth README command. Until it does, the README line stays and the check uses the portal's ask panel (row 10).
- The demo users' passwords are set out of band once per copy (M3b): a secret can't be in the README. This is the one human step, and the table names it.
- Docker isn't needed: Y3a builds the AgentCore runtime from a code zip, and no stack uses a container image.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Five commands | `export` profile → `uv sync && uv run --locked pytest` → `yarn build` in `web/` → `npm ci && npx cdk deploy --all --require-approval never` in `infra/` → `uv run python scripts/ask.py ...`. The uv install, Node, the npm token and the one-time bootstrap go in a "Prerequisites" line above | Keeping the uv install line inside the five (the web build has to be there: WebStack's synth fails without `web/dist/web/browser`) |
| Second copy | Same account, `-c prefix=demoN -c transaction_search=off`; destroyed at the end | A second account (we have one sandbox); reusing `demo` (proves nothing) |
| Stack selection | `--all` for deploy and destroy; single stacks by **construct ID** (`npx cdk deploy WebStack`), CloudFormation by name (`demo2-WebStack`) | `npx cdk deploy demo2-WebStack` ("No stacks match": the CLI selects by construct ID) |
| Passwords | The hidden-prompt loop from M3b, values from Patrick in person | Passwords in a script, the README, the vault or Slack |
| Recording results | A row per check in the PR body and two `HANDOFF.md` lines (via Abdul, who owns the file) | A results file in the repo (stale by D2) |
| Where the decision goes | `DECISIONS.md`, next free number, written with Patrick (his file) | One entry per stack (noise) |

## 3. Exact content
**Root `README.md`**, replacing the section from `## Run it in 5 commands` up to (not including) `**Front end (\`web/\`, Angular):**`:
````markdown
## Run it in 5 commands
Prerequisites (once per machine): uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`), Node 22 with `corepack enable`, the read-only npm token in your home `~/.npmrc` (`web/README.md`), AWS CLI v2 with the `hackathon` profile. Once per account: `cd infra && npm ci && npx cdk bootstrap aws://796973512193/eu-west-1`. No Docker needed.

```bash
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1
uv sync && uv run --locked pytest   # deps, tests + coverage (data is committed; regenerate with uv run python demo/data/erp/generate.py)
cd web && corepack enable && yarn install --frozen-lockfile && yarn build && cd ..
cd infra && npm ci && npx cdk deploy --all --require-approval never && cd ..
uv run python scripts/ask.py --entity E4 "What is blocking cutover?"
```
The portal URL is the `PortalUrl` output of `demo-WebStack`. Demo users' passwords are set out of band once per copy (`infra/README.md`, "Clean-deploy check"). A second, fresh copy in the same account: add `-c prefix=demo2 -c transaction_search=off` to the deploy line.
````
**`infra/README.md`**, appended: the "Clean-deploy check" section exactly as in [[M5 - Clean-deploy runbook - plan]] Task 1 Step 3 (eleven rows: clone, profile, tests, portal build, deploy, passwords, data, API without a token, portal sign-in, ask, destroy; then the outputs line and the two recovery notes).

**`DECISIONS.md`**, the next free number: "Infrastructure conventions: one CDK app, prefixed copies, outputs not names" (what, why, rejected; text in the plan, Task 1 Step 5).

## 4. Tests
- The existing doc checks (`tests/test_dependencies.py`, `tests/test_code_style.py`) pass with the new Markdown: every runnable command uses `uv run --locked pytest` or `uv run python scripts/...`; no test path outside `tests/`.
- The two checks themselves are run by hand (verify in AWS), row by row, with each row's expected result compared and written down.
- No new automated tests: this item adds no code.

## 5. Out of scope
- Fixing a stack: a failing row goes back to that stack's owner (with a `Ruling:` in the ledger), then the check restarts from row 1.
- CI-driven deploys (D-018).
- The demo rehearsal and backup video (F6).

Related: [[Build order]], [[Michael - DevOps]], [[Deploy and demo checks]]
