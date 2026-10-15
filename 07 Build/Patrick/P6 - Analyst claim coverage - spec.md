---
tags: [build, spec, area/agents, area/evals]
id: P6
owner: Patrick (the analyst prompt is Linus's; he reviews)
status: ready
updated: 2026-10-15
---
# P6: the analyst covers every distinct blocker, the calendar clash included (spec)
> **Q04 failed in the deployed eval run because the analyst never made the CAL-004 claim.** Its 4 claims (store_claims input, run `run-4ee9c6173ed54c4f9fe03db7b7dd180f`) were the schedule slip, the reconciliation, RB-014/RB-015 and WP-022, and two of them shared WP-022 and WP-032. The prompt tells it "at most 4 claims are judged", so it stops at 4 itself. P6 fixes the prompt and gives the cap one more slot. Repo: `Amali-Tech/cloud-9-hackathon`, branch `fix/analyst-claim-coverage` from `develop` (709 tests or more). Before the 14:00 code freeze.

## 0. Context: read the vault first
Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`. Read: [[How to execute a plan]]; [[2026-10-15]] (the deployed eval run, the Q04 and Q02 squeeze, the Q02 rerun); [[2026-10-15 Figures are verified by code and the critic judges rows]] (D-030); [[H8 - Stored answer with budget gates and a claim cap - spec]] (`MAX_CLAIMS_PER_PLAN`); the repo's `agents/prompts/blocker_analyst.txt` v1.2.0 and `DECISIONS.md` D-027. If unclear, look in the vault, then ask Patrick.

## 1. Intent
**What:**
1. **Prompt v1.3.0** (`agents/prompts/blocker_analyst.txt`):
   - drop "(at most 4 claims are judged)": the analyst reports every distinct blocker; code applies the cap;
   - a calendar window (close, audit, holiday) that contains the forecast cutover date is **always its own claim**, like a conflict between rows; for a question about the cutover date or schedule it comes first;
   - **a row belongs to one claim's chain only**: related tasks with one cause join one claim, never two.
2. **`MAX_CLAIMS_PER_PLAN` 4 → 5** (`tools/constants.py`), so a fifth real blocker isn't cut. About one more critic call, roughly $0.03 a question; the $0.50 budget and the H8 checks still bound every run.

**Why:** Q04 ("Is E4's cutover date realistic?") must cite CAL-004; Q02 deployed kept CAL-004 but lost the DEF-0398 conflict. Both are the same squeeze: the analyst caps itself at 4 and spends a slot on a duplicate.

**Success means:**
- The prompt is v1.3.0, locked, keeps its injection-defence phrases; the "at most 4" text is gone.
- `MAX_CLAIMS_PER_PLAN == 5`; the cap test still holds (it reads the constant).
- **Live (local asker, Guardrail on, about $0.60):** Q04 cites CAL-004 and says "year-end"; Q02 cites DEF-0398; both PASS.
- `uv run --locked pytest` green, coverage ≥ 98%.

## 2. Out of scope
The critic, the writer, the orchestrator; Q12 (Huvison's guarded-content fix); Q08/Q09 on the deployed asker (Linus).

Related: [[Build order]], [[P6 - Analyst claim coverage - plan]]
