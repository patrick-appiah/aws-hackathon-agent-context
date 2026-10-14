---
date: 2026-10-13
tags: [learning, area/agents]
---
# Agent parsers must fail closed
`json.loads(str(result))` with no error handling meant a malformed critic reply raised instead of rejecting, so the gate failed open.

**Why:** Commit security review 2026-10-13 on `agents/critic.py`.
**How to apply:** Every agent output parser: try/except → reject with a reason; validate the schema; unit-test with a stub model that returns junk.

Related: [[Learnings]]
