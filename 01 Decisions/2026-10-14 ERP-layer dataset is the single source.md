---
date: 2026-10-14
status: done
tags: [decision, status/done, area/data, area/architecture]
---
# The ERP-layer dataset is the single source and the data contract (D-019)
## Decision
Seat 2's dataset (`demo/data/erp/`: four legacy ERPs, the target ERP, and migration artefacts derived from them down to record-level load errors) is the only dataset. The core reads `demo/data/erp/output/migration/`; its 14 artefacts and row IDs are the contract (composite IDs such as `E4#RB-014`). `tools/metrics.py` implements its KPI definitions and the dashboard mockup figures are pinned in tests. The old generator, its CSVs and `kpis.py` are deleted. Planted scenarios: E1 clean, decoy `DEF-0398`, probe `DEF-0462`, E4 cutover inside the year-end close (`CAL-004`).
## Why
"Every figure derived from the migration's own artefacts", down to the rejected records; a deeper evidence trail for the agent; a cost view for the CFO; ends two datasets and two KPI implementations (non-negotiable #6).
## Rejected
Adapter translating to the old columns; generator also exporting the old format; porting `kpis.py` as-is; keeping both KPI implementations cross-checked.
## Found while planning
Decoy is the existing `DEF-0398` (not a new `DEF-0461`); `RB-014` is an E4 step; `mapping_for_field` looks up by target field (load errors name `tax_id`, not `TAXNO`). Numbered D-019 because the CI branch took D-018.

Related: [[Decisions]], [[Team plan]], [[Synthetic data rules]]
