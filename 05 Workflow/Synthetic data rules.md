---
tags: [workflow, area/process]
---
# Synthetic data rules
How the demo data is made and kept stable. Full detail lives in the repo `docs/TEAM_PLAN.md`; this note is the working checklist.

- **Only the generator makes data:** `uv run python demo/data/erp/generate.py` writes `demo/data/erp/output/` (D-019). Never hand-edit the CSVs.
- **Deterministic:** fixed seed. Changing a random range or the order of random calls changes every row.
- **Refactors must be byte-identical:** `uv run python demo/data/erp/generate.py <temp>` and `diff -r demo/data/erp/output <temp>`; the diff must be empty.
- **Planted scenarios are pinned:** E4 chain (E4#RB-010 → RC-C3-E4-customers 91.2% FAIL → 212 load errors → DEF-0412 → E4#CUSMST#TAXNO), decoy DEF-0398 (closed, customers still fail), clean E1, E4 cutover inside year-end close CAL-004, injection probe DEF-0462 (E3). `tests/tools/test_metrics.py` and `tests/tools/test_planted_scenarios.py` pin them (list in `demo/data/erp/README.md`).
- **Keep ID ranges apart:** historical generated defects are DEF-0301…; planted ones use DEF-04xx ([[Planted IDs can collide with generated ones]]). `tests/adapters/test_csv_repo.py` checks every row ID is unique.
- **No real names:** systems by tier and role, people by role (brief §12). A judge who sees a real client name in a prompt log stops the demo.
- **New scenario?** Add it as a planted row after the random rows (so nothing else shifts), add an eval question, and pin it in a test.

Related: [[Workflow]], [[Team plan]]
