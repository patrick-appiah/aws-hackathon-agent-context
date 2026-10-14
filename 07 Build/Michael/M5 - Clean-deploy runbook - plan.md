---
tags: [build, plan, area/devops]
id: M5
owner: Michael
spec: "[[M5 - Clean-deploy runbook - spec]]"
status: ready
updated: 2026-10-14
---
# M5: the clean-deploy runbook and the two checks (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Run each command, **compare its output with the `Expected:` line**, and only then go on. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Tasks 2 and 3 deploy into AWS and are run **by Michael with Patrick present**; an agent may prepare the commands but never runs a deploy, a destroy or a password command on its own.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[M5 - Clean-deploy runbook - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger.
3. [[Workstreams]] §5–§7, [[Michael - DevOps]], [[Deploy and demo checks]].
4. The deploy and acceptance tasks of every stack plan: [[M2 - App, DataStack and LedgerStack - plan]], [[M3a - GuardrailStack - plan]], [[M3b - AuthStack - plan]], [[M4a - WebStack - plan]], [[M4b - Observability - plan]], [[Y1 - ApiStack - plan]], [[Y2a - Express ask spine - plan]], [[Y2b - Standard publish flow - plan]], [[Y3a - AgentCore runtime - plan]], [[Y3b - Agent shim and host switch - plan]], [[Y4 - IAM least-privilege review - plan]].

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Michael or Patrick.

**Goal:** the repo says exactly how to deploy from clean, and two fresh copies (`demo2`, `demo3`) have been deployed, checked and destroyed with nothing but those commands.

**Architecture:** documentation only (`README.md`, `infra/README.md`, `DECISIONS.md`), then two manual runs of the documented table against AWS.

**Tech stack:** uv, Node 22 + yarn (web), the pinned CDK CLI (`infra/package.json` *(new)*), AWS CLI v2, curl.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. **Branch:** `docs/clean-deploy-runbook` from an up-to-date `develop`, **after every stack item is merged** ([[Build order]]). The checks themselves run from a **separate fresh clone** (Task 2 Step 1), never from your working copy.
- **Start state:** `uv run --locked pytest` → all passed, `TOTAL` ≥ 96%. Write the count in the ledger as **S**; this item adds no tests, so every later count is **S** (dry-run on C1 + M2: S = 226).
- `eu-west-1` only; Bedrock `eu.*` inference profiles only; synthetic data only; **no secrets anywhere**: passwords are typed at a hidden prompt, tokens are never printed, saved or pasted.
- Settings only in `config.py`; domain constants only in `tools/constants.py`; no single-character names; no magic numbers (nothing here adds code).
- Never weaken a security rule to make a row pass. A failing row goes to that stack's owner; the check restarts from row 1 after the fix is merged.
- Tests in `tests/`; `uv run --locked pytest` from the repo root; coverage must not drop.
- Deploys are manual (D-018). Every `cdk` and `aws` command runs with `AWS_PROFILE=hackathon AWS_REGION=eu-west-1`.
- PR to `develop`; Patrick merges; never push to `develop` or `main`; **no `Co-Authored-By` and no "Generated with" lines**.
- `README.md` and `DECISIONS.md` are Patrick's files: write those parts with him. `HANDOFF.md` is Abdul's: give him the lines.
- No layout or "meta" guard tests.

## Review Focus (what no test covers; check by hand at the end)
1. **Nothing outside the table was needed** in either check. Every extra command anyone typed is written in the ledger and either added to the table (and the README) or fixed in code.
2. **The second copy didn't touch the first:** after each destroy, `demo-*` stacks are still `CREATE_COMPLETE`/`UPDATE_COMPLETE` and the demo portal still loads.
3. **The copy used `-c transaction_search=off`** on deploy **and** destroy, so the account's Transaction Search (owned by `demo-ObservabilityStack`) is untouched.
4. **No secret was written down:** `git log -p | grep -ci "password\|IdToken"` shows nothing new from this branch; the ledger holds no token or password.
5. **The README's five lines are the ones that were run** (copy-paste them in Task 2, don't retype).

---

### Task 1: Write the runbook into the repo

**Files:**
- Modify: `README.md` (section "Run it in 5 commands"), `infra/README.md` (append "Clean-deploy check"), `DECISIONS.md` (one entry)

**Produces:** the documented commands. **Consumes:** every merged stack (names of outputs: `BucketName`, `PortalUrl`, `UserPoolId`; context keys `prefix`, `transaction_search`, `agent_host`; `PORTAL_CALLBACK_REVISION`).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c docs/clean-deploy-runbook
mkdir -p .superpowers && printf '# Ledger: M5 Clean-deploy runbook\n' > .superpowers/ledger-M5.md
grep -rn "transaction_search\|agent_host\|PORTAL_CALLBACK_REVISION" infra/*.py infra/stacks/*.py | head
```
Expected: `S passed`, `TOTAL ... 96%`; the grep shows the three names defined in `infra/` (if any is missing, the stack that owns it isn't merged: stop).

- [ ] **Step 2: Replace the README section.** In `README.md`, replace everything from the line `## Run it in 5 commands` up to (not including) the line starting `**Front end (\`web/\`, Angular):**` with:
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
(Keep one blank line before the `**Front end ...**` line.)

- [ ] **Step 3: Append the check to `infra/README.md`:**
```markdown

## Clean-deploy check (hard gate 1; Michael with Patrick, D1 18:00 and D2 13:00)
A fresh copy, from a fresh clone, with only the commands below. Anything you have to click or type that isn't here is a failed check: fix the code or this list, then start again.

| # | Step | Command | Expected |
|---|---|---|---|
| 1 | Fresh clone | `git clone git@github.com:Amali-Tech/cloud-9-hackathon.git clean-deploy && cd clean-deploy && git switch develop` | a clean `develop` |
| 2 | Profile | `export AWS_PROFILE=hackathon AWS_REGION=eu-west-1 PREFIX=demo2` (`demo3` on Day 2) | `aws sts get-caller-identity --query Account --output text` prints `796973512193` |
| 3 | Tests | `uv sync && uv run --locked pytest` | all passed, coverage not below the last merge |
| 4 | Portal build | `cd web && corepack enable && yarn install --frozen-lockfile && yarn build && cd ..` | `web/dist/web/browser/index.html` exists |
| 5 | Deploy | `cd infra && npm ci && npx cdk deploy --all --require-approval never -c prefix=$PREFIX -c transaction_search=off && cd ..` | every stack ends with ✅; `transaction_search=off` because the first copy owns the account's Transaction Search |
| 6 | Passwords | the `admin-set-user-password` loop in the AuthStack plan (hidden prompt; passwords from Patrick, never written down) | five users `CONFIRMED` |
| 7 | Data | `aws s3 ls s3://<BucketName of $PREFIX-DataStack>/artefacts/ \| wc -l` | `15` |
| 8 | API without a token | `curl -s -o /dev/null -w "%{http_code}\n" <PortalUrl>/api/summary` | `401` |
| 9 | Portal | open `<PortalUrl>`, sign in as `e4-lead-user` | the one screen for E4; asking about E2 is refused |
| 10 | Ask | in the portal, ask "What is blocking cutover for E4?" | a cited answer with a trace and a cost |
| 11 | Remove the copy | `cd infra && npx cdk destroy --all --force -c prefix=$PREFIX -c transaction_search=off && cd ..` | every stack deleted; no `$PREFIX-` stack left in `aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE` |

Read any output with `aws cloudformation describe-stacks --stack-name $PREFIX-<Stack> --query "Stacks[0].Outputs"`. CDK selects stacks by construct ID (`npx cdk deploy WebStack`), CloudFormation by name (`demo-WebStack`).

**If AuthStack's app client is redeployed,** CloudFormation resets its callback URLs to `http://localhost:4200`: bump `PORTAL_CALLBACK_REVISION` in `infra/constants.py` *(new)* and redeploy `WebStack` (M4a). **Agent host fallback:** `npx cdk deploy FlowStack -c agent_host=lambda` runs the agents inside the step Lambdas instead of AgentCore (Y3b); say which one the demo used in `HANDOFF.md`.
```

- [ ] **Step 4: Doc checks** (they parse every command in Markdown):
```bash
uv run --locked pytest tests/test_dependencies.py tests/test_code_style.py --no-cov 2>&1 | tail -1
```
Expected: `16 passed` (dry-run on C1 + M2; more if later items added doc checks), 0 failed. A failure names the offending command: fix the wording (`uv run --locked pytest`, `uv run python scripts/...`), never the test.

- [ ] **Step 5: The infra decision (with Patrick).** Find the next free number: `grep -o "^### D-0[0-9]*" DECISIONS.md | tail -1` (dry-run: `D-022`, so the next is `D-023`, unless an item merged since took it). Append to `DECISIONS.md`, with that number:
```markdown

### D-0NN · Infrastructure conventions: one CDK app, prefixed copies, outputs not names
- **What:** CDK in Python under `infra/` (`aws-cdk-lib` in the uv `infra` group, which `dev` includes and `uv export --no-dev` leaves out of every bundle; the CLI pinned in `infra/package.json`). `infra/app.py` *(new)* `build_stacks` creates every stack in deploy order; stacks hand resources to each other as Python attributes and publish `CfnOutput`s for people. Every physical name that must be unique carries the `-c prefix=` value (default `demo`), and account-wide singletons sit behind a switch (`-c transaction_search=off` for a second copy). Every resource is `RemovalPolicy.DESTROY`. IAM statements are built by the stack that owns the resource, with named actions on named resources: no `grant_*` helpers and no bare `*` (Y4's template test). CDK tests use `aws_cdk.assertions` in `tests/infra/` *(new)*; synth needs no credentials; CI runs the tests and never deploys (D-018). Lambda and AgentCore code is bundled without Docker.
- **Why:** Hard gate 1: a fresh copy must deploy next to the demo copy, from the README, with nothing clicked. Templates that are unit-tested can be reviewed and their least privilege proved without an AWS account.
- **Rejected:** Terraform or SAM (a second toolchain); hardcoded names (the second copy collides); SSM parameters for wiring (another moving part); CI-driven deploys (D-018); Docker bundling (not every laptop has it; slower).
```

- [ ] **Step 6: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add README.md infra/README.md DECISIONS.md
git commit -m "Clean-deploy runbook: the five README commands, the check table in infra/README, and the infra conventions decision"
```
Expected: `S passed` (dry-run 226), `TOTAL ... 96%`.

**Task done when:**
- `grep -c "^| [0-9]* |" infra/README.md` → `11` (the table rows) and `grep -n "yarn build && cd .." README.md` finds the third command.
- The doc checks pass and the suite count is S.

### Task 2: Clean-deploy check 1 (D1 18:00, prefix `demo2`, with Patrick; verify in AWS)

**Files:** none. **Produces:** the result of each row in the ledger. **Consumes:** Task 1's table on `develop` (merge Task 1's PR first, or run from its branch and say so).

- [ ] **Step 1: Rows 1–4, from a fresh clone in a new directory** (copy each command from `infra/README.md`):
```bash
cd ~ && rm -rf ~/clean-deploy && git clone git@github.com:Amali-Tech/cloud-9-hackathon.git clean-deploy && cd clean-deploy && git switch develop
export AWS_PROFILE=hackathon AWS_REGION=eu-west-1 PREFIX=demo2
aws sts get-caller-identity --query Account --output text
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
cd web && corepack enable && yarn install --frozen-lockfile && yarn build && cd ..
ls web/dist/web/browser/index.html
```
Expected: `796973512193`; the same `S passed` as `develop`; `web/dist/web/browser/index.html`. Write the start time in the ledger.

- [ ] **Step 2: Row 5, the deploy** (verify in AWS):
```bash
cd infra && npm ci && npx cdk deploy --all --require-approval never -c prefix=$PREFIX -c transaction_search=off 2>&1 | grep -E "✅|❌|Outputs:" ; cd ..
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE --query "StackSummaries[?starts_with(StackName, 'demo2-')].StackName" --output text
```
Expected: one `✅  demo2-<Stack>` line per stack in `build_stacks` (Data, Ledger, Guardrail, Auth, Agent, Flow, Api, Web, Observability), no `❌`; the list shows the same nine names. Write the deploy duration in the ledger.

- [ ] **Step 3: Row 6, passwords.** Run the M3b password loop ([[M3b - AuthStack - plan]], the `admin-set-user-password` step) with `USER_POOL_ID` from `aws cloudformation describe-stacks --stack-name demo2-AuthStack --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text`. Patrick types the passwords.
Expected: `CONFIRMED` five times.

- [ ] **Step 4: Rows 7–8, data and the API's door** (verify in AWS):
```bash
BUCKET=$(aws cloudformation describe-stacks --stack-name demo2-DataStack --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text)
PORTAL_URL=$(aws cloudformation describe-stacks --stack-name demo2-WebStack --query "Stacks[0].Outputs[?OutputKey=='PortalUrl'].OutputValue" --output text)
aws s3 ls "s3://$BUCKET/artefacts/" | wc -l
curl -s -o /dev/null -w "%{http_code}\n" "$PORTAL_URL/api/summary"
curl -s -o /dev/null -w "%{http_code}\n" "$PORTAL_URL/"
```
Expected: `15`; `401`; `200`.

- [ ] **Step 5: Rows 9–10, the portal (verify in AWS, in a private browser window).** Open `$PORTAL_URL`, sign in as `e4-lead-user`.
Expected: the managed login page, then the one screen scoped to E4 (E4's figures; no other entity's rows). Ask "What is blocking cutover for E4?": an answer whose bullets cite rows (including `DEF-0412`), a trace with the steps and prompt versions, and a cost. Try E2 (the URL or the selector): refused (the 403 message, not a blank page). Write each result in the ledger.

- [ ] **Step 6: Row 11, destroy** (verify in AWS):
```bash
cd infra && npx cdk destroy --all --force -c prefix=$PREFIX -c transaction_search=off 2>&1 | grep -E "destroyed|❌"; cd ..
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query "StackSummaries[?starts_with(StackName, 'demo2-')].StackName" --output text
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query "StackSummaries[?starts_with(StackName, 'demo-')].StackName" --output text
```
Expected: one `✅  demo2-<Stack>: destroyed` per stack, no `❌`; the `demo2-` list is empty; the `demo-` list still shows the demo copy's stacks (Review Focus 2). Write the end time.

- [ ] **Step 7: Record.** In the ledger: each row pass/fail, the timings, and every command typed that isn't in the table. For each failure: a `Ruling:` line naming the owner and the fix; after the fix merges, restart from Step 1.

**Task done when:**
- All eleven rows are `pass` in the ledger, with no extra command, or each failure has an owner and a merged fix followed by a full re-run that passes.
- No `demo2-` stack remains.

### Task 3: Clean-deploy check 2 (D2 13:00, prefix `demo3`, with Patrick; verify in AWS)
- [ ] **Step 1:** Repeat Task 2 Steps 1–7 exactly, with `PREFIX=demo3` (and `demo3-` in every stack name and `starts_with` filter).
Expected: the same results as Task 2, on the code-freeze candidate of `develop`. Write `git -C ~/clean-deploy rev-parse --short HEAD` in the ledger.

**Task done when:**
- All eleven rows pass for `demo3`, and no `demo3-` stack remains.

### Task 4: Record the results and open the PR
- [ ] **Step 1: Give Abdul the `HANDOFF.md` lines** (he owns the file), for example under "What's real": "Deploys from a clean copy with the README commands: checked D1 18:00 (`demo2`, commit `<sha>`, <n> min) and D2 13:00 (`demo3`, commit `<sha>`, <n> min). One manual step: demo passwords set out of band." and, if used, "Agents ran on <AgentCore | the Lambda fallback> in the demo."
Expected: Abdul's PR contains the lines; `grep -n "clean copy" HANDOFF.md` finds them after it merges.
- [ ] **Step 2: Review Focus** by hand; write each result in the ledger.
- [ ] **Step 3: PR (with Michael's OK)**
```bash
git push -u origin docs/clean-deploy-runbook
gh pr create --repo Amali-Tech/cloud-9-hackathon --base develop --title "Clean-deploy runbook and infra conventions decision (M5)" --body-file .superpowers/pr-M5.md
```
Write `.superpowers/pr-M5.md` first: the two checks' row results and timings, the commit each ran on, the `Ruling:` lines, no attribution lines.
Expected: the PR opens against `develop` with a green Jenkins check (the Python stage runs: `.md` files changed).
- [ ] **Step 4:** Update [[Build order]]: M5 `in review (PR #nn)`, then `merged`.

**Task done when:**
- The PR is merged and [[Build order]] says M5 `merged`.

## Done means
- [ ] **The README has the five commands.** Verify: `git show origin/develop:README.md | sed -n '/## Run it in 5 commands/,/Front end/p'` shows the five lines of Task 1 Step 2, including `yarn build` and `npm ci && npx cdk deploy --all`.
- [ ] **The check table is in the repo.** Verify: `git show origin/develop:infra/README.md | grep -c "^| [0-9]* |"` → `11`.
- [ ] **The doc checks pass.** Verify: `uv run --locked pytest tests/test_dependencies.py tests/test_code_style.py --no-cov 2>&1 | tail -1` → `... passed`, 0 failed.
- [ ] **Check 1 passed (D1 18:00).** Verify: the PR body lists rows 1–11 `pass` for `demo2` with a commit SHA and timings; `aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query "StackSummaries[?starts_with(StackName, 'demo2-')]"` → `[]`.
- [ ] **Check 2 passed (D2 13:00).** Verify: the same for `demo3`.
- [ ] **The demo copy survived both checks.** Verify: `curl -s -o /dev/null -w "%{http_code}\n" "$(aws cloudformation describe-stacks --stack-name demo-WebStack --query "Stacks[0].Outputs[?OutputKey=='PortalUrl'].OutputValue" --output text)/"` → `200`.
- [ ] **The decision and the hand-off lines exist.** Verify: `git show origin/develop:DECISIONS.md | grep "Infrastructure conventions"` finds the entry; `git show origin/develop:HANDOFF.md | grep "clean copy"` finds Abdul's lines.
- [ ] **[[Build order]] shows M5 `merged`.**

## Never
- Run a check from your working copy, or with a `cdk.out` left from an earlier synth.
- Type a command during a check that isn't in the table without writing it in the ledger.
- Deploy or destroy the second copy without `-c transaction_search=off`, or destroy with the wrong prefix (`demo` is the demo copy).
- Write a password or token anywhere; deploy from CI; push to `develop` or `main`; add attribution lines.

Related: [[M5 - Clean-deploy runbook - spec]], [[Build order]], [[Michael - DevOps]], [[How to execute a plan]]
