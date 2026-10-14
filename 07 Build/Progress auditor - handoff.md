---
tags: [build, handoff, area/process]
owner: Patrick (requester) · built by the erp-migration-portal-e5 session
status: handed off
updated: 2026-10-14
---
# Progress auditor: handoff brief
> For the Claude session **erp-migration-portal-e5**, handed off by the **aws-hackathon** session on Patrick's instruction. Build a read-only agent, or a small team of agents, that checks the team's progress against everything we've written down and reports what is done, what isn't, who owns each gap, and how to fix it.

## 0. Context: read the vault first
The team vault is the context space: decisions, briefs, rules, the build order and the reasons behind them. On this machine it's at `/mnt/c/dev/aws-hackathon/aws-hackathon/`; the remote is `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`. Run `git pull` first. Read, in order:
1. `00 Home.md`, then the latest `03 Sessions/` note and `Open follow-ups.md`.
2. `06 Workstreams/Workstreams.md`: the architecture with owners, the code already built, the contracts table, the timeline, what's graded (the Pitch Track rubric and the five hard gates), and the non-negotiable rules.
3. All nine briefs in `06 Workstreams/` (Patrick, Huvison, Linus, Abdul, Michael, Yaw, Mildred, Clement, Business case and pitch). **Their "What you build", "Your milestones" and "Definition of done" sections are what the auditor checks against.**
4. `07 Build/`: the C1 spec and plan in `00 Contracts/` (the format every build item follows). `Build order` and `How to execute a plan` are coming; check whether they exist.
5. `04 Reference/`: `Pitch track grading rubric.md` (how we're scored), `Judging rubric.md`, `Hackathon guideline.md`, `Problem statement.md`.
6. `01 Decisions/` and `05 Workflow/`, especially `Dev loop`, `Working with AI assistants`, `Deploy and demo checks` and `Vault upkeep`.

The repo is `~/amalitech/aws-hackathon/erp-migration-portal` (GitHub `Amali-Tech/cloud-9-hackathon`, branch `develop`). Read `docs/TEAM_PLAN.md` (§2 workstreams, §3 contracts, §4 schedule, §6 rules), `AGENTS.md`, `ARCHITECTURE.md`, `EVALS.md`, `COST.md`, `HANDOFF.md`, `DEMO.md` and `DECISIONS.md`.

**How the support-tickets agent was built:** ask the peer session **support-tickets**; it's expecting your questions. It's also writing `/home/noblet/amalitech/aws-hackathon/briefs/how-the-support-tickets-agent-was-built.md`. It built a read-only investigator agent (`relitix-support`) with a grader and evals, which is the pattern to reuse.

## 1. What Patrick asked for
"An agent or agents that will check the progress of the work: what has been done or not, what or who didn't do something as per the requirement, and suggest fixes."

Patrick's answers on the open points:
- **Audience: the whole team.** Name the owner of each item, because the briefs name owners, but frame findings constructively, by workstream and item, never as blame.
- **Output: written into the vault only.** No Slack posting.
- **When: on demand only.** No schedule.

## 2. What the auditor checks (proposed; refine in your spec)
1. **Delivery:** per person and per build item, done, in progress, not started or blocked, by comparing:
   - the briefs' tasks, milestones and done-lists;
   - the `07 Build` plans' task checkboxes and `Build order` statuses;
   - the repo: branches, commits, open and merged PRs (`gh pr list --repo Amali-Tech/cloud-9-hackathon --state all`; `gh` is logged in as `patrick-appiah`), files that should exist (for example `tools/api_schema.py` *(new)*, `api/handlers.py` *(new)*, `flow/steps.py` *(new)*, `agents/orchestrator.py` *(new)*).

   Compare against the timeline (`Workstreams.md` §5): what should be done by now.
2. **Conformance:** the work against its spec, plan and contracts:
   - names and signatures match the contracts (C1);
   - tests exist and pass (`uv run --locked pytest`), coverage hasn't dropped (95% today);
   - the rules hold: eu-west-1 and `eu.*` only; no secrets; no single-character names; scope never a tool argument; prompts only in locked `.txt` files; agents read-only; nothing written before approval;
   - no one edited another workstream's folders.
3. **Score:** the documents and gates against the rubric:
   - every `AGENTS.md` row complete (7 columns);
   - EVALS results with failures;
   - COST measured;
   - HANDOFF real/faked/breaks first;
   - README runs in 5 commands;
   - worked examples per agent;
   - the business case's `[TBC]`s closed;
   - the deck present;
   - the five hard gates.
4. **Process:** small commits with clear messages (history is graded); branch prefixes (`feature/` etc., never seat names); PRs to `develop` only; CI (Jenkins, PR #8) green; no attribution lines; vault notes Windows-safe (no `:` in file names).

For every gap: **what**, **where** (file, PR or brief section), **who** (the owner from the brief), **the fix** (concrete: what to change or run), and **urgency** against the next milestone.

## 3. Output
A dated report in the vault: `08 Progress/<YYYY-MM-DD> <HHMM>.md`. Windows-safe: write `1300`, not `13:00`. It contains:
- a one-paragraph summary;
- a per-workstream table (item · status · evidence · gap · fix · owner);
- the top 5 risks to the next milestone;
- the rubric and gates scorecard;
- process issues;
- what changed since the previous report.

Add a row to an `08 Progress/Progress.md` index (MOC), and link the report from the day's session note.

## 4. Constraints (non-negotiable)
- **Read-only.** The auditor never edits code, docs, briefs or plans, never pushes, merges or comments on PRs, and never touches AWS. Its only write is its own report in `08 Progress/`.
- **Evidence for every claim.** Each status cites a file and line, a commit, a PR number or a test result. If it can't verify something, it says "not verified", never guesses (the lesson from the support-tickets agent).
- **No secrets** in reports. Synthetic data only. Refer to client people by role.
- Follow the vault conventions (`05 Workflow/Vault upkeep.md`): Windows-safe names, `Related:` footers, no PII.
- **Process for building it:** brainstorm → spec → plan → implement, as for every build item. **Patrick approves the spec and the plan before you implement.** Put both in the vault at `07 Build/Progress auditor/`, and open them with a "Context: read the vault first" section, as `07 Build/00 Contracts/C1 - API and spine contracts - spec.md` does.
- **Where the agent definition lives: your proposal, for Patrick to approve.** For example `.claude/agents/progress-auditor.md` in the repo, so every teammate can run it, or user-level like `relitix-support`. Prompts for any agent we ship follow the team's rule: plain-text files, versioned.
- **Git:**
  - commits under Patrick Noblet Appiah <patrick.appiah@amalitech.com>;
  - no `Co-Authored-By` and no "Generated with Claude" lines anywhere;
  - branches `<type>/<short-topic>` from `develop`, PR to `develop`;
  - ask Patrick before any push or PR;
  - the vault is pushed to its `main` after Patrick's OK.

## 5. Done when
- The spec and plan are approved by Patrick.
- The auditor runs on demand with one documented command or prompt, and writes a correct report.
- It's validated on today's state: at minimum it must find these known facts (use them as an eval):
  - C1 isn't implemented yet;
  - `EVALS.md` has no answer-check results (no asker yet);
  - `COST.md` is all TODO;
  - PR #8 (CI) is open;
  - the business case still has `[TBC]`s;
  - the Q09 verdict count is open.
- A short "how to run the progress auditor" note sits in `07 Build/Progress auditor/` and is linked from `Workstreams.md`.

Related: [[Workstreams]], [[Build order]], [[Open follow-ups]]
