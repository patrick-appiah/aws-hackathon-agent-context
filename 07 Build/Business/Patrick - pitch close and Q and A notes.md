---
tags: [business, pitch, speaker-notes]
owner: Patrick
updated: 2026-10-15
---
# Patrick: pitch close and Q and A notes

> Patrick's own speaking notes: the closing section of the pitch and prepared answers. Not a repo file. Related: [[B3c - Pitch script and Q and A - spec]], [[2026-10-15]].

## Closing: how the agents work together (Patrick, about 2½ minutes)

**On screen:** the answer card for *"What is blocking cutover for Entity 4?"*, its trace open (one line per step, each agent's prompt version), and a rejected claim under "Could not verify". Point at the trace as each step is named.

```
CFO asks "What is blocking cutover for Entity 4?"
        │
 ORCHESTRATOR ── decides what to look at next, never answers
   │   └─ RETRIEVER (code) ── fetches the rows for the lead it picked
 BLOCKER-ANALYST ── turns rows into claims; every number from a code tool
        │
 CODE CHECK ── rows exist, the user may see them, figures recomputed
        │
 CRITIC (blind) ── one claim and its rows, nothing else
   │ pass                │ reject
 WRITER                back to the ORCHESTRATOR (2 tries at most, counted in the ledger)
   │                     → then "could not verify"
 Answer, every line cited ── publish ── DELIVERY LEAD APPROVES ── status pack
```

| Time | Beat | Say |
|---|---|---|
| 0:00 | The setup | "A dashboard can show numbers. But 'what is blocking cutover for Entity 4?' has no fixed checklist: where you look next depends on what you just found. That's why this part is agentic, and only this part. Every number on the screen is plain code." |
| 0:15 | The orchestrator plans | "The orchestrator is the planner. It never answers anything itself. It looks at Entity 4 first, sees a customer reconciliation failing at 91% against a 98% target, and decides that's worth following, so it pulls the failing object, then the defect behind it. It chooses those leads from what it found, and stops when it has enough." |
| 0:45 | The analyst connects the evidence | "The blocker-analyst turns those rows into claims: what is blocking, why, and who owns it. Here: 212 customer records rejected for bad tax IDs, logged as defect DEF-0412, and the runbook won't let the final customer load run until that reconciliation passes. Every number in that sentence comes from a tool that code calculates. The AI never does arithmetic." |
| 1:10 | Trust: code, then a blind critic | "Before anyone sees it, code checks every claim: do the cited rows exist, may this user see them, does every figure recompute to the same value? Then a separate critic judges each claim, blind. It sees one claim and its evidence: not the plan, not the question, not how many tries are left, so it can't be talked into agreeing. Watch it reject the trap: a defect marked closed, while the data still fails. A status report would have shown that green; the critic doesn't. A rejected claim gets one re-plan, and the try count lives in our run ledger, not in the AI's memory, so the loop always ends. After two tries it says 'could not verify', never a guess." |
| 1:50 | The answer, and the human | "The writer turns the passed claims into a short answer, every line linked to its source; click any of them and you see the record. Nothing leaves the system until the delivery lead approves it. That's the only write we make, and it waits for a person." |
| 2:10 | Guard-rails, and the close | "Around all of it: the user's access comes from their sign-in, so an Entity 4 lead can't see Entity 2. Bedrock Guardrails sit on every model call. Every run has a 50-cent budget; on AWS the median run costs 27 cents and takes about a minute. Five roles, one job each, every step traced. That's how a CFO gets an answer they can act on, not just another dashboard." |
| 2:30 | End | |

**Sources:** the flow and the roles, `AGENTS.md` and `ARCHITECTURE.md` §3; 91% vs 98%, DEF-0412 and 212 records, `EVALS.md` Q01; the decoy (DEF-0398 closed, the reconciliation still failing), `EVALS.md` Q02; two tries, `DECISIONS.md` D-022; 27 cents and about a minute on AWS, `COST.md`; the Entity 2 refusal, `EVALS.md` Q11.

---

## Q&A: "How will you make the AI answer faster?" (about 40 seconds)

> "Today a question takes about a minute; on AWS the median run is about a minute and costs 27 cents. A consultant takes two days, but we still want it faster. We know exactly where the time goes, because every step is traced: about 40 seconds is the planner and analyst reading the evidence, 15 to 25 is the critic checking each claim, and a rejected claim adds a re-check.
>
> We've already cut it: fetching data is plain code instead of AI, the analyst gets only the rows it needs, and the question runs in the background so the screen never freezes. We also tested a cheaper, smaller model. It was slower overall and saved nothing, so we kept quality.
>
> Next: check claims in parallel instead of one by one, which saves 10 to 20 seconds; cache what doesn't change between questions; and answer the common questions ahead of time after each data refresh, so 'what's blocking Entity 4?' comes back instantly. The target is under 30 seconds for a fresh question, and instant for the common ones."

**If they push: the detail**

| Where the time goes (measured on AWS) | Seconds | What we do about it |
|---|---|---|
| Planner plus analyst reading the evidence | about 40 | **Done:** the retriever is code, not a model (D-028); the analyst gets 5 sample load errors instead of 50 (P7). **Next:** Bedrock prompt caching |
| Critic checking each claim, one at a time | 15–25 | **Next:** check claims in parallel (one Step Functions Map setting): 10–20 s saved |
| A rejected claim's re-check | 20–40 each | **Done:** analyst prompt fixes that cut rejections. **Next:** re-check with the analyst only, no fresh plan |
| Cold starts after a quiet spell | about 15, first question | **Next:** keep functions warm in working hours |
| Perceived wait | | **Done:** runs in the background with a progress line. **Next:** show each verified claim as it passes |
| Common questions | | **Next:** answer the top questions per entity after each data refresh; serve from cache, citations intact |

- *"Why not a faster model?"* → "We measured it: a smaller model planned more steps, slower (79 s against 57 s) and the same cost. Speed comes from the design. Newer models swap in only if the evals pass; it's a settings change."
- *"Is a minute acceptable?"* → "Against two consultant-days, yes. For a live conversation, our target is under 30 seconds; parallel checks and caching get us there."

**Don't overclaim:** parallel checking, prompt caching, warm functions and pre-computed answers are plans, not built; "under 30 seconds" is a target. Done: the code retriever, the row trim, the async UI, the cheaper-model measurement.
