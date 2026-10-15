---
date: 2026-10-15
status: in progress
tags: [decision, area/agents, area/evals]
---
# Figures are verified by code; the critic judges the rows and the wording (D-029)
## Decision
- **Code checks the numbers.** A claim's `figures` (`{value, tool, args, field}`) are recomputed before the critic sees the claim: `tools/claims.validate_claim` calls the tool again and rejects a mismatch. This already runs on the production path (`blocker_analyst.checked_claims`, L5).
- **The critic is told.** Its input marks the figures as recomputed by code, and its prompt drops "every figure must appear in, or be directly computable from, the cited rows". It still checks that the statement uses each figure's value as given, and still rejects any other number or date that no cited row shows.
- **The analyst puts every computed number in `figures`** (days to cutover, days behind, days a defect has been open, percentages), with its tool, never only in the statement.
- **Owners:** the critic's input and prompt (Huvison); the analyst's prompt (Linus). Repo: D-029 in `DECISIONS.md` (Patrick, 2026-10-15).

## Why
- The first eval run (Huvison, 2026-10-15) failed **Q06** ("102 days, 6 behind") and part of **Q01**: the critic rejected `records_reconciled_pct` and "102 days" because no cited row shows them.
- They come from `metrics` tools; days to cutover depends on today's date, so no row ever can. The critic was right by its prompt, and code had already confirmed the numbers.
- Arithmetic is code's job (D-010); the critic's job is whether the rows support the claim.

## Rejected
- **A "metrics" pseudo-row per figure:** rows are artefact rows; a computed value has no row ID.
- **The critic calling the figure tools:** a second recheck, and tools for an agent that must stay blind and tool-less.
- **No figures in claims:** Q06 asks for them.

## Revisit when
- An eval shows a figure passing the recheck but used wrongly in the statement (the critic missed it).

Related: [[Decisions]], [[2026-10-15]], [[Open follow-ups]]
