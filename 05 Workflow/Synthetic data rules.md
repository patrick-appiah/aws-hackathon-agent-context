---
tags: [workflow, area/process]
---
# Synthetic data rules
How the demo data is made and kept stable. Full detail lives in the repo `docs/TEAM_PLAN.md`; this note is the working checklist.

- **Only the script makes data:** `python scripts/generate_synthetic_data.py --out demo/data`. Never hand-edit `demo/data/`.
- **Deterministic:** fixed seed. Changing a random range or the order of random calls changes every row.
- **Refactors must be byte-identical:** regenerate into a temp folder and `diff -r demo/data <temp>`; the diff must be empty.
- **Planted scenarios are pinned:** E4 blocker chain (DEF-0412, REC-0083), E4 decoy (DEF-0419 vs REC-0095), clean E2, E5 close-calendar clash, injection probe DEF-0430 (E3). `tools/test_metrics.py` pins the numbers the demo depends on.
- **Keep ID ranges apart:** generated defects start at DEF-0101; planted ones use DEF-04xx ([[Planted IDs can collide with generated ones]]). A test checks every row ID is unique.
- **No real names:** systems by tier and role, people by role (brief §12). A judge who sees a real client name in a prompt log stops the demo.
- **New scenario?** Add it as a planted row after the random rows (so nothing else shifts), add an eval question, and pin it in a test.

Related: [[Workflow]], [[Team plan]]
