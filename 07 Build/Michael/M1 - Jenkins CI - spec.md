---
tags: [build, spec, area/devops]
id: M1
owner: Michael
status: ready
updated: 2026-10-14
---
# M1: Jenkins CI merged and green (spec)
> **PR #8 (`chore/ci-minimal-checks`: `Jenkinsfile` *(new)* + D-018) is open and conflicts with `develop`.** This item gets it reviewed and merged, and makes bandit scan every back-end folder the day it lands. Repo: `Amali-Tech/cloud-9-hackathon`. The repo is the source of truth for code; the vault is the source of context.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before touching anything, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] (`06 Workstreams/`), especially §6 (what's graded: the commit history) and §7 (rules).
3. [[Michael - DevOps]]: the owner's brief; this is "What you build" step 1.
4. [[Build order]]: M1 depends on nothing and is milestone M0.
5. `01 Decisions/`: [[2026-10-14 ERP-layer dataset is the single source]] (why D-018 is reserved for this PR) and [[2026-10-14 Two apps in one repo]] (Node 22, the `cloud9-npm-token` credential); `05 Workflow/`: [[Dev loop]], [[Handling security findings]], [[Working with AI assistants]].

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, rubrics and guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Michael (the owner) or Patrick (who merges). Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. Bring PR #8 up to date with `develop` by **merging `develop` into `chore/ci-minimal-checks`** (no rebase, no force-push). The only conflict is `DECISIONS.md`: `develop` added D-019 and D-020 where the PR adds D-018. Keep both: D-018 sits between D-017 and D-019.
2. **Bandit scans every back-end folder that exists.** Today it scans `tools adapters agents scripts config.py`. `evals/` is already on `develop` (PR #16) and unscanned. `api/`, `auth/`, `flow/` and `infra/` land in the next hours. The Jenkinsfile gets one candidate list, `BANDIT_CANDIDATES = 'tools adapters agents scripts evals api auth flow infra config.py'`, and the Python stage scans those that exist.
3. **The Jenkins credential `cloud9-npm-token` exists** (read-only npm token, secret text), so the front-end build stage passes.
4. Patrick reviews and merges. Every later PR shows one green Jenkins status check.

**Why:**
- Hard gate 1 (clean deploy) and the graded commit history both need a `develop` that stays green; eight people push for two days. CI is the guard.
- A folder bandit doesn't scan is a folder with no security check. Listing folders by hand means each new one is forgotten until someone notices.
- Merging (not rebasing) keeps the PR's two commits as they are, so no one's review is invalidated and nothing needs a force-push.

**Success means:**
- PR #8 is `MERGEABLE`; its diff against `develop` touches only `Jenkinsfile` and `DECISIONS.md` (plus the merge commit).
- The Python stage, run locally in its own container (`python:3.11-bookworm`, uv `0.13.0`), passes on the merged branch: the full suite, bandit high severity with **`Files skipped (0)`**, and pip-audit.
- PR #8 shows a green Jenkins check, Patrick merges it, and the next PR to `develop` also shows a green check.

**Assumptions:**
- Michael (GitHub `OdarteiL`) owns `chore/ci-minimal-checks` and can push to it.
- The Jenkins Multibranch job for `Amali-Tech/cloud-9-hackathon` exists and uses `amalitech-github-app-credential` (D-018 text). If it doesn't, stop and ask Patrick: creating it is outside this plan.
- Michael has, or can get from Patrick privately, the read-only npm token. It never goes in the repo, the vault or Slack.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| How to resolve the conflict | `git merge origin/develop` into the PR branch; keep both sides, D-018 before D-019 | Rebase + force-push (rewrites a branch under review); renumbering D-018 (D-019's vault note already says D-018 is the CI branch's) |
| How bandit learns about new folders | One `BANDIT_CANDIDATES` list in the Jenkinsfile `environment`; the stage keeps those that exist (`[ -e ]`) | Editing the `-r` list in every PR that adds a folder (forgotten); `bandit -r .` (scans `.venv`, `web/node_modules` *(new)*, `demo/`) |
| Which Python bandit runs on | The container's 3.11 (as in the PR) | A newer Python: **bandit 1.7.10 under Python 3.14 skips every file ("exception while scanning file") and still exits 0**. Local checks must use `uvx --python 3.11` |
| Where the npm token lives | The Jenkins credential `cloud9-npm-token` (secret text), as the Jenkinsfile already reads it | Any file in the repo |
| Extra checks now | None (checkov on `cdk synth` stays rejected, D-018) | Adding IaC scanning before `infra/` has code |

## 3. Exact behaviour
**Jenkinsfile `environment` block** gains, after `WEB_PATHS`:
```groovy
    // Every back-end folder bandit scans once it exists, so new folders are covered the day they land.
    BANDIT_CANDIDATES = 'tools adapters agents scripts evals api auth flow infra config.py'
```
**Python stage:** `-e BANDIT_CANDIDATES` is passed into the container, and both bandit calls scan `$bandit_targets`, built as:
```bash
bandit_targets=""
for target in $BANDIT_CANDIDATES; do
  if [ -e "$target" ]; then bandit_targets="$bandit_targets $target"; fi
done
echo "--- bandit on:$bandit_targets (fails on high severity)"
```
The high-severity call still fails the build (`-lll -ii`); the medium call is still a warning (`|| echo`).

**`DECISIONS.md`:** D-017, D-018 (the PR's text, unchanged), then D-019 onwards exactly as on `develop` (D-019, D-020, D-021 if C1 merged first, D-022), in that order, with one blank line between entries and no conflict markers.

## 4. Tests
There is no unit test for a Jenkinsfile. The checks are:
- the merged branch's Python suite passes in the CI container, with the same count as `develop`;
- bandit lists `evals` among its targets and reports `Files skipped (0)`;
- `git diff origin/develop --stat` on the branch shows only `Jenkinsfile` and `DECISIONS.md`;
- the Jenkins status check on PR #8 is green (verify in Jenkins / on GitHub).

## 5. Out of scope
- The Node download for the CDK tests, and the `^infra/` path in `PYTHON_PATHS`: those come with M2, when `infra/` has code.
- Creating the Jenkins job or the GitHub App credential.
- Any deploy from CI (D-018: deploys stay manual from the README).

Related: [[Build order]], [[Michael - DevOps]], [[Workstreams]]
