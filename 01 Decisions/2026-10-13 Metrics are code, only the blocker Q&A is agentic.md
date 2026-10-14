---
date: 2026-10-13
status: done
tags: [decision, status/done, area/architecture]
---
# Metrics are code
## Decision
All five KPIs come from `tools/metrics.py`; the only agent loop answers 'what is blocking cutover for entity X?'.
## Why
Known formulas are arithmetic. One source of truth means the screen and the answer can't disagree. The brief says the agent layer must genuinely run, so it has to carry real weight where the path is open.
## Rejected
An LLM summarising the dashboard: decorative, and a second source of truth.

Related: [[Decisions]], [[One source of truth per number]]
