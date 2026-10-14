---
tags: [workflow, area/process]
---
# Handling security findings
What to do when a review (automated or human) flags a security issue. Full detail lives in the repo `docs/TEAM_PLAN.md`; this note is the working checklist.

1. **Confirm it against the code.** Findings can be vague (a file name only). Read the code and state the concrete failure in one sentence.
2. **Fix it with a test** that fails before the fix and passes after.
3. **Check siblings.** The same rule usually belongs elsewhere: the critic's missing scope gate was a "sibling parity" finding, because `tools/claims.py` already had it. Search for the pattern across modules.
4. **Record it:** a `DECISIONS.md` entry (what, why, rejected) and a vault decision note; a learning note if it's a reusable lesson.
5. **Say what can't be eliminated.** Some risk is inherent (an LLM must read untrusted text). Document the layers instead (ARCHITECTURE §7).

Examples: [[2026-10-13 Artefact text is untrusted, critic fails closed|critic injection]], [[Agent parsers must fail closed]], D-012 (ledger counter reset, critic scope parity).

Related: [[Workflow]], [[Team plan]]
