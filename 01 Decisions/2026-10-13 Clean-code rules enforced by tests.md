---
date: 2026-10-13
status: done
tags: [decision, status/done, area/process]
---
# Clean-code rules enforced by tests
## Decision
DRY, no magic numbers (domain constants in `tools/constants.py`), nothing hardcoded (deployment settings only in `config.py`), descriptive names with no single characters (`test_code_style.py`). One ledger test suite runs against both the in-memory and DynamoDB adapters (moto). Coverage on by default. Reviews (code-simplifier / code-review) per PR, not per edit.
## Why
The lead's standards for 8 engineers + AI assistants; rules a test can enforce survive a hackathon.
## Rejected
Linter-only; per-edit reviews.

Related: [[Decisions]]
