---
tags: [build, plan, area/devops]
id: M1
owner: Michael
spec: "[[M1 - Jenkins CI - spec]]"
status: ready
updated: 2026-10-14
---
# M1: Jenkins CI merged and green (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Run each command, **compare its output with the `Expected:` line**, and only then go on. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it. Pushing and the Jenkins credential are outward-facing: ask Michael (the owner) before each.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]]: the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[M1 - Jenkins CI - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in the ledger.
3. [[Workstreams]] §7 (rules) and [[Michael - DevOps]] ("What you build" step 1).
4. [[2026-10-14 ERP-layer dataset is the single source]] (D-018 is reserved for this PR) and [[2026-10-14 Two apps in one repo]] (`cloud9-npm-token`).
5. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If the vault doesn't answer it, stop and ask Michael or Patrick.

**Goal:** PR #8 is conflict-free, bandit scans every back-end folder that exists, the npm credential exists, and PR #8 is merged with a green Jenkins check.

**Architecture:** no code changes. Two files on an existing branch: `DECISIONS.md` (conflict resolution) and `Jenkinsfile` *(new)* (bandit targets). Every stage runs in a pinned container (D-018), so the local dry run uses the same containers.

**Tech stack:** Jenkins declarative pipeline, Docker, uv `0.13.0` (pinned in the Jenkinsfile), bandit `1.7.10`, pip-audit `2.7.3`.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal` (`git@github-amalitech:Amali-Tech/cloud-9-hackathon.git`, or your own clone). **Branch: the existing `chore/ci-minimal-checks`** (PR #8). Don't create a new branch, don't rebase it, don't force-push it.
- **Start state:** on `develop`, `uv run --locked pytest` → **160 passed**, `TOTAL` 95% (if C1, `feature/api-and-spine-contracts`, is already merged: **206 passed**, 96%). Write down which one you see: the merged PR branch must give the same number.
- `eu-west-1` only; Bedrock `eu.*` inference profiles only; synthetic data only; **no secrets anywhere** (the npm token goes only into the Jenkins credential store).
- Settings only in `config.py`; domain constants only in `tools/constants.py`; descriptive names; no single-character names; no magic numbers. The core (`tools/`) imports no boto3, Strands, adapters, config or os. (Nothing here touches Python, but the suite enforces it.)
- Tests in `tests/`; `uv run --locked pytest` from the repo root; coverage must not drop.
- PR to `develop`; **Patrick merges**; never push to `develop` or `main`; **no `Co-Authored-By` and no "Generated with" lines**.
- Stay in DevOps's files: `Jenkinsfile` and `infra/` (`docs/TEAM_PLAN.md` §2). `DECISIONS.md` is touched only to resolve the conflict, keeping both sides word for word.
- No layout or "meta" guard tests.

## Review Focus (what no test covers; check by hand at the end)
1. `DECISIONS.md` has no conflict markers, D-018's text is the PR's latest (the Jenkins version, not the Actions version), and the order is D-017, D-018, then every later entry exactly as on `develop` (D-019, D-020, D-021 if C1 is merged, D-022).
2. Bandit really scanned files: the log says `Files skipped (0)`. Bandit 1.7.10 on Python 3.14 skips every file and still exits 0, so a "No issues identified" with skipped files is a false green.
3. The candidate loop runs under `set -euo pipefail`: it uses `if ...; then ...; fi`, never `[ -e ] && ...` (which would end the loop with a non-zero status on the last missing folder and kill the stage).
4. The npm token appears nowhere in the repo, the build log (Jenkins masks it) or the vault.
5. `git diff origin/develop --stat` on the branch lists only `Jenkinsfile` and `DECISIONS.md`.

---

### Task 1: Merge `develop` into PR #8 and resolve `DECISIONS.md`

**Files:**
- Modify: `DECISIONS.md` (conflict only)

**Produces:** an up-to-date `chore/ci-minimal-checks`. **Consumes:** `origin/develop`.

- [ ] **Step 1: Baseline on `develop`**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
mkdir -p .superpowers && printf '# Ledger: M1 Jenkins CI\n' > .superpowers/ledger-M1.md
```
Expected: `160 passed` and `TOTAL ... 95%` (or `206 passed`, 96% if C1 is merged). Write the number in the ledger.

- [ ] **Step 2: Check out the PR branch and merge `develop`**
```bash
git fetch origin && git switch chore/ci-minimal-checks && git pull
git merge --no-edit origin/develop
```
Expected: `CONFLICT (content): Merge conflict in DECISIONS.md` and `Automatic merge failed`. `git diff --name-only --diff-filter=U` prints only `DECISIONS.md`. If any other file conflicts, stop and ask Patrick.

- [ ] **Step 3: Resolve the conflict by keeping both sides.** The conflict block has the PR's D-018 (`HEAD`) above `=======` and `develop`'s D-019 onwards (D-019, D-020, D-022, and D-021 if C1 is merged) below. Delete the three marker lines and leave one blank line where `=======` was:
```bash
sed -i '/^<<<<<<< HEAD$/d; /^>>>>>>> origin\/develop$/d; s/^=======$//' DECISIONS.md
grep -nE "^(<<<<<<<|=======|>>>>>>>)" DECISIONS.md; echo "markers left: $?"
grep -n "^### D-01[789]\|^### D-02" DECISIONS.md
```
Expected: `markers left: 1` (grep found nothing), then the headings in order `D-017`, `D-018 · Minimal CI on AmaliTech Jenkins: ...`, `D-019 · The ERP-layer dataset ...`, `D-020 · Two apps in one repo ...`, `D-021 · API and ask-spine contracts ...` (if C1 is merged), `D-022 · A claim gets at most 2 attempts ...`. Open the file and check there is exactly one blank line before each `### D-0` heading.

- [ ] **Step 4: Full suite on the merged branch, then commit the merge**
```bash
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add DECISIONS.md
git commit --no-edit
git diff origin/develop --stat
```
Expected: the same count as Step 1 (`160 passed` or `206 passed`), coverage unchanged; the merge commit is created with Git's default message `Merge remote-tracking branch 'origin/develop' into chore/ci-minimal-checks`; the diff stat lists only `DECISIONS.md` and `Jenkinsfile`.

**Task done when:**
- `git log -1 --format=%s` shows the merge commit and `git status` is clean.
- `grep -c "^### D-018" DECISIONS.md` prints `1`, and no conflict markers remain.
- The suite count equals Step 1's.

### Task 2: Bandit scans every back-end folder that exists

**Files:**
- Modify: `Jenkinsfile`

**Produces:** the `BANDIT_CANDIDATES` environment variable and the existence filter in the Python stage. **Consumes:** nothing.

- [ ] **Step 1: See today's targets (the "failing" state).**
```bash
grep -n "bandit==1.7.10 -r" Jenkinsfile
```
Expected: two lines, both `-r tools adapters agents scripts config.py` (no `evals`, although `evals/run.py` exists on `develop`).

- [ ] **Step 2: Add the candidate list.** In the `environment { ... }` block, directly after the `WEB_PATHS = '^ALL$|^web/|^Jenkinsfile$'` line, add:
```groovy
    // Every back-end folder bandit scans once it exists, so new folders are covered the day they land.
    BANDIT_CANDIDATES = 'tools adapters agents scripts evals infra config.py'
```

- [ ] **Step 3: Pass it into the Python container.** In the `Python tests and security checks` stage, change
```
            -e UV_VERSION -v "$WORKSPACE:/work" -w /work "$PYTHON_IMAGE" bash -euo pipefail -c '
```
to
```
            -e UV_VERSION -e BANDIT_CANDIDATES -v "$WORKSPACE:/work" -w /work "$PYTHON_IMAGE" bash -euo pipefail -c '
```

- [ ] **Step 4: Replace the four bandit lines.** Replace exactly these lines:
```
              echo "--- bandit: fails on high severity"
              uvx bandit==1.7.10 -r tools adapters agents scripts config.py -lll -ii
              echo "--- bandit: medium severity, warning only"
              uvx bandit==1.7.10 -r tools adapters agents scripts config.py -ll -ii || echo "WARNING: bandit medium-severity findings above"
```
with:
```
              bandit_targets=""
              for target in $BANDIT_CANDIDATES; do
                if [ -e "$target" ]; then bandit_targets="$bandit_targets $target"; fi
              done
              echo "--- bandit on:$bandit_targets (fails on high severity)"
              uvx bandit==1.7.10 -r $bandit_targets -lll -ii
              echo "--- bandit: medium severity, warning only"
              uvx bandit==1.7.10 -r $bandit_targets -ll -ii || echo "WARNING: bandit medium-severity findings above"
```
The surrounding `sh '''...'''` is a Groovy single-quoted string, so `$bandit_targets` reaches bash unchanged. The inner script is inside `bash -c '...'`, so it must not contain a single quote (it doesn't).

- [ ] **Step 5: Dry-run the Python stage locally, in its container.** From the repo root (Docker must be running). `UV_PROJECT_ENVIRONMENT=/tmp/venv` keeps your own `.venv` untouched:
```bash
docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -e UV_PYTHON_DOWNLOADS=never -e UV_VERSION=0.13.0 \
  -e BANDIT_CANDIDATES='tools adapters agents scripts evals infra config.py' \
  -e UV_PROJECT_ENVIRONMENT=/tmp/venv -v "$PWD:/work" -w /work python:3.11-bookworm bash -euo pipefail -c '
    pip install --quiet --user "uv==${UV_VERSION}"
    export PATH="$HOME/.local/bin:$PATH"
    uv sync --locked -q
    uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
    bandit_targets=""
    for target in $BANDIT_CANDIDATES; do
      if [ -e "$target" ]; then bandit_targets="$bandit_targets $target"; fi
    done
    echo "--- bandit on:$bandit_targets (fails on high severity)"
    uvx bandit==1.7.10 -r $bandit_targets -lll -ii 2>&1 | grep -E "No issues identified|Files skipped"
    uv export --locked --no-dev --format requirements-txt --no-hashes > /tmp/runtime-requirements.txt
    uvx pip-audit==2.7.3 -r /tmp/runtime-requirements.txt --no-deps --disable-pip --progress-spinner off 2>&1 | tail -1'
```
Expected (dry-run on `develop` merged into the PR branch):
- `160 passed` (or `206 passed`) and `TOTAL ... 95%` (96%);
- `--- bandit on: tools adapters agents scripts evals infra config.py (fails on high severity)` (`infra` is there because `infra/README.md` exists; it also covers `infra/functions/` *(new)* when that lands);
- `No issues identified.` and `Files skipped (0):`;
- `No known vulnerabilities found`.

If you run bandit outside the container, use `uvx --python 3.11 bandit==1.7.10 ...`; on a newer Python it prints `Files skipped (18)` with "exception while scanning file" and exits 0 (a false green).

- [ ] **Step 6: Commit**
```bash
git add Jenkinsfile
git commit -m "CI: bandit scans every back-end folder that exists (evals now; infra, with the Lambda glue in infra/functions/, as it lands)"
git diff origin/develop --stat
```
Expected: the commit is created; the diff stat lists `DECISIONS.md` and `Jenkinsfile` only.

**Task done when:**
- `grep -c "BANDIT_CANDIDATES" Jenkinsfile` prints `3` (the definition, the `-e BANDIT_CANDIDATES` and the `for` loop; dry-run).
- The local dry run prints `evals` in the bandit target list and `Files skipped (0):`.

### Task 3: The npm credential, the push and the green check (ask Michael first)

**Files:** none.

**Produces:** Jenkins credential `cloud9-npm-token`; an updated PR #8. **Consumes:** the read-only npm token (from Patrick, privately).

- [ ] **Step 1: Check the credential exists (verify in Jenkins).** In AmaliTech Jenkins: *Manage Jenkins → Credentials →* the folder or global domain the `cloud-9-hackathon` job uses. Look for ID **`cloud9-npm-token`**, kind **Secret text**.
Expected: it is listed. If not: *Add Credentials → Kind: Secret text → Secret: <the token> → ID: `cloud9-npm-token` → Description: "read-only npm token for @amalitechnpm (cloud-9-hackathon web build)"*. Never paste the token anywhere else.

- [ ] **Step 2: Push (only with Michael's OK)**
```bash
git push origin chore/ci-minimal-checks
gh pr view 8 --repo Amali-Tech/cloud-9-hackathon --json mergeable,headRefOid --jq '.mergeable'
```
Expected: the push succeeds without `--force`; `MERGEABLE` (GitHub may need a few seconds; re-run if it says `UNKNOWN`).

- [ ] **Step 3: Watch the Jenkins build (verify in Jenkins).** Open PR #8's Checks / status on GitHub, then the Jenkins build log.
Expected in the log: `Python checks: true · Frontend build: true` (the merge brought in `web/` and Python changes); gitleaks `no leaks found`; the pytest line with the Step 1 count; `--- bandit on: tools adapters agents scripts evals infra config.py`; `No known vulnerabilities found`; the front-end `yarn build` succeeds; the final status is **SUCCESS** and GitHub shows the check green.
If the front-end stage fails with a 404 on `@amalitechnpm/at-design-system`, the credential is missing or wrong: fix Step 1, then *Build Now* on the PR job.

- [ ] **Step 4: Ask Patrick to review and merge.** Post in the team channel: "PR #8 (Jenkins CI, D-018) is up to date with develop and green; bandit now scans evals too and picks up infra (and infra/functions/) automatically. Ready for review." Add the Review Focus results from the ledger to the PR as a comment.
Expected: Patrick merges; `gh pr view 8 --repo Amali-Tech/cloud-9-hackathon --json state --jq .state` prints `MERGED`.

**Task done when:**
- `gh pr view 8 ... --jq .state` prints `MERGED`.
- The Jenkins build for the merge commit on `develop` is green.

### Task 4: Prove it on the next PR
- [ ] **Step 1:** When the next PR to `develop` opens (any workstream), open its checks.
Expected: one Jenkins status check, green (or red for a real reason shown in the log). Record the PR number in the ledger.
- [ ] **Step 2: Update [[Build order]]:** set M1 to `merged`. Copy any `Ruling:` lines from the ledger into a PR #8 comment, then delete the ledger.

**Task done when:**
- A second PR shows the Jenkins check, and [[Build order]] says M1 `merged`.

## Done means
- [ ] **PR #8 is merged.** Verify: `gh pr view 8 --repo Amali-Tech/cloud-9-hackathon --json state --jq .state` → `MERGED`.
- [ ] **`develop` has D-018 once, in order, with no markers.** Verify: `git show origin/develop:DECISIONS.md | grep -n "^### D-01[789]"` prints D-017, D-018, D-019 in that order; `git show origin/develop:DECISIONS.md | grep -cE "^(<<<<<<<|>>>>>>>)"` → `0`.
- [ ] **Bandit covers `evals` and future folders.** Verify: `git show origin/develop:Jenkinsfile | grep "BANDIT_CANDIDATES = "` shows `tools adapters agents scripts evals infra config.py`; the latest `develop` Jenkins log shows `--- bandit on:` with `evals` and `Files skipped (0):`.
- [ ] **CI is green on `develop` and reports to PRs.** Verify: the Jenkins job's last `develop` build is SUCCESS; the next PR after #8 shows a Jenkins status check on GitHub (`gh pr checks <n> --repo Amali-Tech/cloud-9-hackathon` lists it).
- [ ] **The npm token is only in Jenkins.** Verify: `git log -p origin/develop | grep -c "_authToken=npm_"` → `0`; the credential `cloud9-npm-token` is listed in Jenkins.
- [ ] **[[Build order]] shows M1 `merged`.**

## Never
- Rebase or force-push `chore/ci-minimal-checks`.
- Put the npm token (or any secret) in a file, a commit, the vault or Slack.
- Trust a bandit run that skipped files.
- Add deploy steps to the Jenkinsfile (D-018).
- Push to `develop` or `main`; add attribution lines.

Related: [[M1 - Jenkins CI - spec]], [[Build order]], [[Michael - DevOps]], [[How to execute a plan]]
