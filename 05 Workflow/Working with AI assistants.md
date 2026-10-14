---
tags: [workflow, area/process]
---
# Working with AI assistants
Rules for each teammate's AI assistant (Claude Code or similar). Full detail lives in the repo `docs/TEAM_PLAN.md`; this note is the working checklist.

## Read first, every session
`docs/TEAM_PLAN.md` → `AGENTS.md` → `ARCHITECTURE.md`, then this vault's [[00 Home]] read order.

## Rules
- **Stay in your workstream.** Edit only the folders your workstream owns ([[Workstreams]], [[Team plan]] §2); mock the others against the contracts in [[Team plan]] §3.
- **Never change a frozen contract** (scope, API routes, citation format, ports, ledger keys) without the lead.
- **Never weaken a security rule** to make a test pass: scope gate, create-once ledger, fail-closed critic, data escaping.
- **Run `uv run --locked pytest` before every commit.** The architecture and code-style tests enforce the house rules automatically.
- **No real data, no secrets**, `eu-west-1` and `eu.*` models only.
- **Permissions are the human's.** If the assistant is blocked (e.g. creating IAM users), it writes a script for the human to run; it doesn't route around the block ([[Auto mode blocks IAM permission grants]]).

## Good prompts to give it
- Start from your starter prompt: `06 Workstreams/prompts/<your-name>.txt`. Or: "Read TEAM_PLAN, AGENTS and ARCHITECTURE and my brief in 06 Workstreams. Implement <X> test-first against the contract in §3."
- "Review this PR diff for clean-code and security issues; don't change behaviour."

Related: [[Workflow]], [[Team plan]]
