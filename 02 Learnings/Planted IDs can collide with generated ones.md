---
date: 2026-10-13
tags: [learning, area/agents]
---
# Planted IDs can collide with generated ones
Random defects numbered DEF-0401+ collided with planted DEF-0412/0419, so two rows shared each ID and citations were ambiguous.

**Why:** Found while adding the DEF-0430 injection probe.
**How to apply:** Keep generated and planted ID ranges apart (random now DEF-0101+); `test_row_ids_are_unique_in_every_artefact` guards it.

Related: [[Learnings]]
