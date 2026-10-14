---
date: 2026-10-13
tags: [learning, area/architecture]
---
# One source of truth per number
If two components compute the same number they eventually disagree; the guideline says this bug shipped four times on their account.

**Why:** Non-negotiable #6.
**How to apply:** Every figure on screen or in an answer comes from `tools/metrics.py`.

Related: [[Learnings]]
