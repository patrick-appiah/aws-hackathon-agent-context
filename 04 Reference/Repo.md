---
tags: [reference, area/repo]
---
# Repo
- GitHub: https://github.com/Amali-Tech/cloud-9-hackathon (account `patrick-appiah`, SSH alias `github-amalitech`; not the personal `thenoblet` account)
- Local: `~/amalitech/aws-hackathon/erp-migration-portal/` (WSL), remote `origin`
- Branches: **`develop`** = integration (branch from it, PR to it, lead merges); **`main`** = releases only (demo and submission), via a `develop` → `main` PR. PR #1 merged `feature/prompt-files` into `develop` (2026-10-14).
- Data: `demo/data/erp/` (Michael's ERP-layer dataset, the data contract, D-019); regenerate with `uv run python demo/data/erp/generate.py`
- Setup: `uv sync`; tests: `uv run --locked pytest` (from the repo root); add deps with `uv add` and commit `uv.lock`
- Planted scenarios: E4 chain (RB-010 → RC-C3-E4-customers 91.2% FAIL → 212 load errors → DEF-0412, 18 days → E4#CUSMST#TAXNO); decoy DEF-0398 closed but customers still fail; probe DEF-0462 (E3); E4 cutover 2027-01-23 inside year-end close CAL-004; E1 clean (live).
- Front end: `web/` (Angular 22, yarn 1.22.22 via corepack, Node 22 in `web/.nvmrc`), D-020. Needs the read-only npm token in the home `~/.npmrc` (never in the repo); `cd web && yarn install --frozen-lockfile && yarn start`
- Superseded: the UC-03 scaffold (deleted) → [[2026-10-13 Problem is the Migration Progress Portal, not UC-03|Pivot]]

Related: [[Reference]]
