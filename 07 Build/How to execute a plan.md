---
tags: [build, workflow]
updated: 2026-10-14
---
# How to execute a plan
> **The procedure every person and every AI agent follows to implement a `07 Build/` plan.** It's written so an agent with no other context can run a plan alone. If a plan and this note disagree, the plan's spec wins, then the plan, then this note. Record any conflict (see "Rulings" below).

## 0. Context: the vault first
The vault is the project's context space. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` before every session. Before your first task, read:
1. [[Workstreams]]: the architecture with owners, the code already built, the contracts, the timeline, what's graded, and the rules (§7).
2. Your own brief in `06 Workstreams/`.
3. [[Build order]]: check that every item your plan depends on is **merged**. If one isn't, stop: build against today's types and fakes only if the plan says so, otherwise wait and tell the owner.
4. The plan's **spec**, then the **plan**.
5. The decisions the spec cites (`01 Decisions/`), and [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

When the plan is silent, look in the vault (`04 Reference/` for the brief and rubrics, `03 Sessions/`, `Open follow-ups.md`). If it's still unclear, **stop and ask the item's owner**. Never invent a name, a shape or a rule.

## 1. Setup
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal     # or your clone of Amali-Tech/cloud-9-hackathon
git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c <the branch the plan names>
mkdir -p .superpowers && printf '# Ledger: <plan ID and title>\n' > .superpowers/ledger-<ID>.md
```
- The test count and coverage must match the plan's **start state**. If they don't, stop: you're not on the expected `develop`.
- `.superpowers/` is gitignored. The ledger is your memory; it survives a context reset. Front-end plans: `cd web && corepack enable && yarn install --frozen-lockfile && yarn test` instead (the npm token is in your home `~/.npmrc`). DevOps plans: `export AWS_PROFILE=hackathon AWS_REGION=eu-west-1`.

## 2. The loop, for each task in order
1. **Read the whole task** before touching anything. Note what it produces and consumes.
2. **Write the test exactly as given.** Run it. **Watch it fail with the expected message.** A test that passes before the code exists is a finding: stop and check.
3. **Write the code exactly as given.** Adapt only what the plan explicitly leaves to you.
4. **Run the command and compare the output with the `Expected:` line,** every time.
5. **Run the full suite** as the task says. Coverage must not drop.
6. **Commit** with the plan's message. Small commits; the history is graded.
7. **Append to the ledger:** `Task <N>: complete (commits <first>..<last>, tests: <command> → <result>)`.

## 3. When output doesn't match `Expected:`
- **The code is wrong** (your typo, a missed step): find the cause, fix it, re-run. Never patch the symptom.
- **The plan is wrong** (a step contradicts its spec, a name doesn't exist, a command can't work): make the **smallest** change that satisfies the spec. Record it in the ledger as `Task <N>: Ruling: <what was wrong> — <what you did and why> — <cost if wrong>`, then continue.
- **Stop and ask the owner**, without improvising, when:
  - the change would be irreversible or destructive;
  - it touches security (scope, the critic, the ledger's create-once rule, secrets, IAM);
  - it needs a push, merge, deploy or anything outward-facing;
  - the plan is so broken that every path is a guess.

## 4. Before you call a task done
- Every test the task names exists, ran, and you read its output.
- Every `Expected:` line was compared with real output.
- Every deviation has a `Ruling:` line in the ledger.
- The full suite passed after the last commit.

## 5. When the whole plan is done
1. Work through the plan's **Review Focus** by hand and write the result of each line in the ledger.
2. Review the whole branch: `git diff develop --stat` touches only the plan's files. Get a review from a fresh reviewer (another person, or an agent with no prior context, ideally a strong model) of the diff against the spec. Fix the critical and important findings test-first, and list the minor ones in the PR.
3. **Ask the owner before pushing.** Then `git push -u origin <branch>` and open the PR **to `develop`**. The body covers what changed, the tests, the rulings and the deferred minors. Patrick merges.
4. **Update [[Build order]]**: set your item's status to `in review (PR #nn)`, and to `merged` once Patrick merges it. Then `git pull --rebase`, commit and push the vault.
5. Copy your `Ruling:` lines into the PR body, then delete the ledger.

## 6. Rules that apply to every plan
- `eu-west-1` only; Bedrock `eu.*` inference profiles only. Synthetic data only. **No secrets** in code, the repo, the vault or Slack.
- Settings only in `config.py`, domain constants only in `tools/constants.py`. Descriptive names, **no single-character names** (a test enforces it). No magic numbers.
- The core (`tools/`) never imports boto3, Strands, `adapters`, `config` or `os`. Agents reach data only through `tools/agent_tools.py`. Scope is never a tool argument.
- Prompts live only in `agents/prompts/<agent>.txt`: bump the version, run `uv run python scripts/lock_prompts.py`.
- Tests live in `tests/`, mirroring the code. Run `uv run --locked pytest` from the repo root.
- Branches `<type>/<short-topic>` from `develop` (`feature/`, `fix/`, `chore/`, `docs/`, `refactor/`, `test/`). PRs to `develop`. Never push to `develop` or `main`.
- **No `Co-Authored-By` and no "Generated with" lines** in commits or PRs.
- Stay in your workstream's folders ([[Workstreams]]). Need something from another workstream? Ask its owner.
- Never weaken a security rule (scope gate, create-once ledger, fail-closed critic, escaping) to make a test pass.
- Vault notes: Windows-safe names (no `:`); end with a `Related:` line that links the note's MOC.

Related: [[Build order]], [[Workstreams]], [[Dev loop]]
