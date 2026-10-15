---
date: 2026-10-14
status: decided
tags: [decision, area/agents, area/cost]
---
# One analyse call per plan (D-027)
## Decision
The orchestrator calls the blocker-analyst **once** per question. It gathers its leads with `retrieve`, then calls `analyse` once over all the rows it fetched.
- **Code:** a second `analyse` in the same plan is refused in code. The prompt (v1.2.0) says "gather your leads first, then analyse once".
- **Not affected:** a re-plan (`replan`, after the critic rejects one claim) is its own plan, so it still gets its own single `analyse`.
- **Repo decision:** D-027 in `DECISIONS.md` (Patrick, 2026-10-14).

## Why
The second live E4 run (`scripts/ask.py --entity E4`, Bedrock, account 796973512193) cost **$0.46 of the $0.50 run budget and took 87 s**.
- The orchestrator called `analyse` **twice**. Each call ran the analyst (Sonnet with figure tools) over **all** rows fetched so far.
- The second call re-read the earlier rows and tended to repeat the same claims under new IDs, so the critic would judge duplicates.
- The analyst is the most expensive step. Halving its calls is the biggest single cost and latency lever left after the lead digest (PR #58).
- **Expected effect** (to confirm live):
  - about $0.25–0.30 per question instead of about $0.46;
  - about 15–20 s less;
  - no duplicate claims.

## Rejected
- **Several analyse calls (the P2 spec as built).** Analysing, noticing a gap, fetching more and re-analysing costs a full analyst pass each time. The critic's reject-and-re-plan loop already covers "this claim needs more evidence", one claim at a time.
- **A prompt-only rule.** It's fragile, as the 6-step limit showed in the first live run. The limit is enforced in code.
- **Sending the analyst only the new rows on a second call.** Its claims would miss the earlier evidence, and the cost would only fall partly.

## Revisit when
- Live runs show the single analysis missing blockers that need evidence fetched after analysing.
- **Or** the model allowance changes enough that cost stops mattering, for example when the Opus or Sonnet 5.5 models open (see D-026).

**Measure first:** the EVALS pass rate, and COST per run before and after.

Related: [[Decisions]], [[P2 - Orchestrator agent - spec]], [[2026-10-14]]
