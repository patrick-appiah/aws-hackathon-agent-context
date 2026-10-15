---
date: 2026-10-15
status: decided
tags: [decision, area/evals, area/api]
---
# Q05 (the most over-plan role) is a dashboard check, not an /ask (D-030)
## Decision
- **EVALS Q05** ("Which role is most over plan this month?") is checked against `/summary`'s capacity card (`tools.api_schema.summary_response`): *Tester*, 8 working vs 6 planned, 133.3 %, roster rows cited, the figure equal to `metrics.role_utilisation`.
- **`/ask` stays per entity:** `AskRequest.entity_id` is still required (C1).
- **Owner of the runner change:** `evals/run.py` (Linus, with Abdul for A5a). Repo: D-030 in `DECISIONS.md` and the Q05 row in `EVALS.md`.

## Why
- Q05 failed with a `ValidationError` before any agent ran: it is portfolio-wide, and the ask spine is per entity by design (the scope narrowed to one entity for the retriever and the analyst).
- The answer is a figure the dashboard already computes in code; "metrics are code" (D-010).

## Rejected
- **An optional `entity_id` on `/ask`:** a cross-entity scope through every agent, the night before the demo.
- **Asking Q05 for one entity:** not the question the eval asks.

## Revisit when
- Portfolio-wide questions become a product need (target architecture, the 90-day roadmap).

Related: [[Decisions]], [[2026-10-15]]
