---
tags: [build, plan, area/api, area/frontend]
id: L4
owner: Linus
spec: "[[L4 - Front-end fixtures from the real summary - spec]]"
status: ready
updated: 2026-10-14
---
# L4: front-end fixtures from the real summary (implementation plan)

> **For the executing agent:** follow [[How to execute a plan]] exactly. Work the tasks in order, and in each task the steps in order. Write the test, run it, **watch it fail with the expected message**, implement, run it, watch it pass, commit. Compare every command's output with its `Expected:` line. If anything differs, stop and follow "When output doesn't match" in [[How to execute a plan]]. Never improvise around it.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[L4 - Front-end fixtures from the real summary - spec]]: **the authority**, including the file-name and `rows.json` assumptions agreed with Mildred.
3. [[C1 - API and spine contracts - plan]] Task 5: the export-script pattern this follows.
4. [[Mildred - front end]] items 1–2, and [[Synthetic data rules]].

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[Problem statement]], [[Judging rubric]], [[Pitch track grading rubric]], [[Hackathon guideline]]); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Linus. Never invent a name, a shape or a rule.

**Goal:** `uv run python scripts/export_summary.py` writes the dashboard's mock responses from the real code, in the API's own shapes.

**Architecture:** one script at the edge (it may import `adapters` and `config`, like `scripts/export_api_schema.py`). It calls C1's builders in `tools/api_schema.py`, so it computes nothing itself.

**Tech stack:** Python 3.11, pydantic 2, pytest, uv. No AWS (the default repository is the committed CSV data).

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: **`feature/export-summary-fixtures`** from an up-to-date `develop` after C1 is merged. Task 3 is a **second branch and PR**, `test/fixtures-drift`, after Mildred's F1 is merged.
- **Start state:** `uv run --locked pytest` → **213 passed**, `TOTAL` **96%** (develop with C1). If other items merged since, write your count in the ledger as START and read every `N passed` as START + the same increase.
- **AWS:** `eu-west-1` only; Bedrock `eu.*` inference profiles only, never `global.*` (D-002). Synthetic data only. **No secrets** anywhere: code, tests, fixtures, the repo, the vault, Slack, commit messages.
- **Clean code (enforced by tests):** no single-character names anywhere (comprehensions, lambdas and `except ... as` included); no magic numbers or strings, so every limit, code and key is a named constant; settings only in `config.py`; domain constants only in `tools/constants.py`; descriptive names.
- **The core (`tools/`) never imports** boto3, Strands, `adapters`, `config` or `os` (`tests/test_architecture.py`).
- **Agents reach data only through `tools/agent_tools.py`.** Scope is never a tool argument and never comes from a request body, a query string or a model. Prompts live only in `agents/prompts/<agent>.txt`, versioned and locked (`uv run python scripts/lock_prompts.py`).
- **Never weaken a security rule** (the scope gate, the create-once ledger, the fail-closed critic, the `<evidence>` escaping) to make a test pass.
- **Tests** live in `tests/`, mirroring the code; run `uv run --locked pytest` from the repo root. Coverage must not drop below the start state. **No layout or "meta" guard tests**: test behaviour, not where files sit.
- **Git:** small commits, one per task, with the messages given. **No `Co-Authored-By` and no "Generated with" lines.** Never push to `develop` or `main`; the PR goes to `develop` after the owner's OK, and Patrick merges.
- **Stay in your folders** (`docs/TEAM_PLAN.md` §2, workstream 3: `api/`, `auth/`, `tools/metrics.py`, `tools/queries.py`, `tools/agent_tools.py`, `tools/claims.py`, `agents/blocker_analyst.py` *(new)*, `agents/prompts/blocker_analyst.txt` *(new)*, `scripts/export_summary.py` *(new)*, the eval runner). Any other file this plan touches is named in its task, with the owner who must review it.
- **`web/` is Mildred's and Clement's folder.** Tasks 1–2 write fixtures only into `tmp_path` (tests) or your working tree (to look at them). **Don't commit anything under `web/` in Tasks 1–2.** Task 3 commits the six generated files with Mildred's OK.
- **Run the script only through uv:** `uv run python scripts/export_summary.py` (a test checks documented commands).

## Review Focus (check by hand at the end)
1. **The fixtures are the API's bodies.** They validate against the C1 models in the tests; also check one against the committed JSON Schema: `summary.json`'s top-level keys equal the `properties` of `web/src/app/core/api/schema/summary.schema.json`.
2. **The other mocks survive.** Run the script into a copy of the real fixtures folder; `ask-E4.json`, `ask-partial.json`, `publish.json` and `approve.json` are byte-identical before and after.
3. **One scope only (CFO).** Entity-lead views in mock mode come from Mildred's mock filter, not from these files. Say so to Mildred.
4. **Synthetic data only.** The fixtures copy CSV text (defect titles, notes). The data is synthetic (D-019); skim `rows.json` once for anything that looks like a real company or person name, and stop if you find one ([[Synthetic data rules]]).
5. **Size.** `rows.json` is about 100 KB (139 rows in the dry run). Fine for a lazily imported fixture; tell Mildred the number.

---

### Task 1: `scripts/export_summary.py`

**Files:**
- Create: `scripts/export_summary.py`, `tests/scripts/test_export_summary.py` *(new)*

**Produces:** `scripts/export_summary.py` with `citations_in(body) -> list[Citation]`, `fixture_bodies(repository: ArtefactRepository, scope: Scope) -> dict[str, dict]`, `export(output_folder: Path) -> list[Path]`, `main() -> int`. **Consumes:** C1's `summary_response(repository, scope)`, `entity_response(repository, scope, entity_id)`, `rows_response(repository, scope, citations)`, `SummaryResponse`, `EntityResponse`, `RowsResponse`; `adapters.repository_from_settings(tenant_id)`; `config.get_settings().default_tenant_id`. **Consumed by:** Mildred (F1).

- [ ] **Step 1: Branch and baseline**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
uv sync && uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git switch -c feature/export-summary-fixtures
mkdir -p .superpowers && printf '# Ledger: L4 front-end fixtures from the real summary\n' > .superpowers/ledger-L4.md
```
Expected: `213 passed` (or START), `TOTAL ... 96%`.

- [ ] **Step 2: Write the failing test.** Create `tests/scripts/test_export_summary.py`:
```python
"""scripts/export_summary.py writes the front end's dashboard fixtures from the real code, in the API's shapes."""
import json
import subprocess
import sys

from config import REPO_ROOT
from tools.api_schema import EntityResponse, RowsResponse, SummaryResponse

EXPORT_SCRIPT = REPO_ROOT / "scripts" / "export_summary.py"
EXPECTED_FILES = ["entity-E1.json", "entity-E2.json", "entity-E3.json", "entity-E4.json", "rows.json",
                  "summary.json"]
EXPECTED_STATUSES = {"E1": "Live", "E2": "On track", "E3": "At risk", "E4": "Blocked"}
UNTOUCHED_FIXTURE = "ask-E4.json"
UNTOUCHED_TEXT = '{"kept": true}\n'


def export_to(output_folder) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(EXPORT_SCRIPT), "--out", str(output_folder)], cwd=REPO_ROOT,
                          check=True, capture_output=True, text=True)


def read_json(path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def citation_labels(value) -> set[str]:
    """Every artefact:row_id citation anywhere inside a JSON body."""
    if isinstance(value, dict):
        own = {f"{value['artefact']}:{value['row_id']}"} if set(value) == {"artefact", "row_id"} else set()
        return own.union(*(citation_labels(child) for child in value.values()))
    if isinstance(value, list):
        return set().union(*(citation_labels(child) for child in value))
    return set()


def test_export_writes_the_six_dashboard_fixtures_and_leaves_the_others_alone(tmp_path):
    (tmp_path / UNTOUCHED_FIXTURE).write_text(UNTOUCHED_TEXT, encoding="utf-8")
    completed = export_to(tmp_path)
    assert sorted(path.name for path in tmp_path.glob("*.json") if path.name != UNTOUCHED_FIXTURE) == EXPECTED_FILES
    assert (tmp_path / UNTOUCHED_FIXTURE).read_text(encoding="utf-8") == UNTOUCHED_TEXT
    assert len(completed.stdout.splitlines()) == len(EXPECTED_FILES)


def test_the_summary_fixture_shows_the_dashboard_figures(tmp_path):
    export_to(tmp_path)
    summary = SummaryResponse.model_validate(read_json(tmp_path / "summary.json"))
    assert (summary.overall.records_reconciled, summary.overall.records_in_scope, summary.overall.pct) == (
        18420, 31700, 58.1)
    assert (summary.pass_rate.latest.cycle_id, summary.pass_rate.latest.pct, summary.pass_rate.previous.pct) == (
        "C3", 96.4, 94.8)
    assert (summary.open_blockers.count, summary.open_blockers.oldest_days) == (7, 18)
    cutover = summary.final_cutover
    assert (cutover.entity_id, cutover.cutover_forecast, cutover.days_remaining, cutover.days_behind_plan) == (
        "E4", "2027-01-23", 102, 6)
    assert (summary.capacity.people_used, summary.capacity.people_planned) == (38, 37)
    assert {entity.entity_id: entity.status for entity in summary.entities} == EXPECTED_STATUSES


def test_each_entity_fixture_is_that_entitys_api_response(tmp_path):
    export_to(tmp_path)
    for entity_id in EXPECTED_STATUSES:
        detail = EntityResponse.model_validate(read_json(tmp_path / f"entity-{entity_id}.json"))
        assert detail.entity.entity_id == entity_id


def test_the_rows_fixture_holds_every_row_the_other_fixtures_cite(tmp_path):
    export_to(tmp_path)
    rows = RowsResponse.model_validate(read_json(tmp_path / "rows.json"))
    cited = set().union(*(citation_labels(read_json(tmp_path / name)) for name in EXPECTED_FILES
                          if name != "rows.json"))
    assert rows.missing == [] and cited and {f"{row.artefact}:{row.row_id}" for row in rows.rows} == cited


def test_the_export_is_deterministic(tmp_path):
    first_folder, second_folder = tmp_path / "first", tmp_path / "second"
    export_to(first_folder)
    export_to(second_folder)
    for name in EXPECTED_FILES:
        assert (first_folder / name).read_bytes() == (second_folder / name).read_bytes()
```

- [ ] **Step 3: Run it and watch it fail**
```bash
uv run --locked pytest tests/scripts/test_export_summary.py --no-cov 2>&1 | tail -1
```
Expected: `5 failed`, each with `subprocess.CalledProcessError: Command '[...python', '.../scripts/export_summary.py', '--out', ...]' returned non-zero exit status 2` (the script doesn't exist).

- [ ] **Step 4: Implement.** Create `scripts/export_summary.py`:
```python
"""Write the front end's dashboard fixtures from the real code, in the API's own shapes (tools/api_schema.py).

Usage, from the repo root:
  uv run python scripts/export_summary.py                  # writes web/src/app/core/api/fixtures/
  uv run python scripts/export_summary.py --out <folder>   # somewhere else (the tests do this)

Writes, for a CFO who sees every entity:
  summary.json          the GET /summary body;
  entity-<id>.json      the GET /entity/{id} body, one per entity on the summary (E1 to E4);
  rows.json             a GET /rows body holding every row the files above cite, so the mock can show any source.
Every number comes from tools/metrics.py through the same builders the API handlers use. Re-run it after a change to
the data, the metrics or the contract. The ask, publish and approve fixtures are not written here.
"""
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from adapters import repository_from_settings  # noqa: E402
from config import get_settings  # noqa: E402
from tools.api_schema import entity_response, rows_response, summary_response  # noqa: E402
from tools.constants import ALL_ENTITIES_WILDCARD  # noqa: E402
from tools.models import Citation, Scope  # noqa: E402
from tools.ports import ArtefactRepository  # noqa: E402

DEFAULT_OUTPUT_FOLDER = REPO_ROOT / "web" / "src" / "app" / "core" / "api" / "fixtures"
SUMMARY_FILE_NAME = "summary.json"
ENTITY_FILE_NAME = "entity-{entity_id}.json"
ROWS_FILE_NAME = "rows.json"
FIXTURE_USER_ID = "fixtures-cfo"
FIXTURE_ROLE = "cfo"
CITATION_KEYS = frozenset({"artefact", "row_id"})
JSON_INDENT = 2
EXIT_OK = 0


def citations_in(body) -> list[Citation]:
    """Every {artefact, row_id} citation anywhere inside a JSON body, in the order they appear."""
    if isinstance(body, dict):
        own = [Citation.model_validate(body)] if set(body) == CITATION_KEYS else []
        return own + [citation for child in body.values() for citation in citations_in(child)]
    if isinstance(body, list):
        return [citation for child in body for citation in citations_in(child)]
    return []


def fixture_bodies(repository: ArtefactRepository, scope: Scope) -> dict[str, dict]:
    """File name → the API's JSON body, built by tools/api_schema.py exactly as the handlers build it."""
    summary = summary_response(repository, scope)
    bodies = {SUMMARY_FILE_NAME: summary.model_dump(mode="json", by_alias=True)}
    for entity in summary.entities:
        bodies[ENTITY_FILE_NAME.format(entity_id=entity.entity_id)] = entity_response(
            repository, scope, entity.entity_id).model_dump(mode="json", by_alias=True)
    cited = [citation for body in bodies.values() for citation in citations_in(body)]
    bodies[ROWS_FILE_NAME] = rows_response(repository, scope, cited).model_dump(mode="json", by_alias=True)
    return bodies


def export(output_folder: Path) -> list[Path]:
    settings = get_settings()
    scope = Scope(user_id=FIXTURE_USER_ID, role=FIXTURE_ROLE, tenant_id=settings.default_tenant_id,
                  entity_ids=(ALL_ENTITIES_WILDCARD,))
    output_folder.mkdir(parents=True, exist_ok=True)
    written = []
    for file_name, body in fixture_bodies(repository_from_settings(scope.tenant_id), scope).items():
        output_path = output_folder / file_name
        output_path.write_text(json.dumps(body, indent=JSON_INDENT, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(output_path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the dashboard fixtures for the front end.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_FOLDER, help="folder to write the fixtures to")
    for output_path in export(parser.parse_args().out):
        print(output_path)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run it and watch it pass**
```bash
uv run --locked pytest tests/scripts/test_export_summary.py --no-cov 2>&1 | tail -1
```
Expected: `5 passed`.

- [ ] **Step 6: Look at the output (don't commit it)**
```bash
uv run python scripts/export_summary.py --out /tmp/l4-fixtures | wc -l
python3 -c "import json; print(len(json.load(open('/tmp/l4-fixtures/rows.json'))['rows']))"
```
Expected: `6`, then `139` (the rows cited on the summary and the four entity pages).

- [ ] **Step 7: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git status --short web/
git add scripts/export_summary.py tests/scripts/test_export_summary.py
git commit -m "Export the dashboard fixtures for the front end from the real summary, entity and rows builders"
```
Expected: `218 passed`, `TOTAL ... 96%`; `git status --short web/` prints nothing (no fixture changed in the working tree).

**Task done when:** `uv run --locked pytest tests/scripts/test_export_summary.py --no-cov` prints `5 passed`; `git show --stat HEAD` lists only the two new files.

### Task 2: Review, then PR (after Linus's OK)
- [ ] **Step 1:** Work through the Review Focus; write each result in the ledger.
- [ ] **Step 2:** `git diff develop --stat` lists only `scripts/export_summary.py` and `tests/scripts/test_export_summary.py`. Expected: `2 files changed`.
- [ ] **Step 3:** Fresh review against the spec; fix critical and important findings test-first.
- [ ] **Step 4: With the OK only:** `git push -u origin feature/export-summary-fixtures`; PR to `develop`, titled "Front-end fixtures from the real summary (L4)". The body: the six files, the `rows.json` shape change, why the fixtures aren't committed yet, `218 passed`. No attribution lines.
- [ ] **Step 5:** L4's [[Build order]] row → `in review (PR #nn)`. Send Mildred: the command, the six file names, the new `rows.json` shape (`{rows, missing}`), the row count, and "commit the generated files in your F1 PR, or tell me when F1 is merged and I'll do Task 3".

**Task done when:** the PR is open to `develop`, L4's [[Build order]] row says `in review (PR #nn)`, and Mildred has the message.

### Task 3 (separate PR, after Mildred's F1 is merged): commit the fixtures and keep them current
Run this only when `git log develop --oneline | grep -i "F1\|fixtures"` shows F1 merged **and** `cd web && yarn test` passes on `develop` with the fixtures F1 committed.

**Files:**
- Modify: `tests/scripts/test_export_summary.py`
- Generated and committed (only if F1 didn't already commit an identical export): `web/src/app/core/api/fixtures/{summary,entity-E1,entity-E2,entity-E3,entity-E4,rows}.json`

- [ ] **Step 1: Branch**
```bash
git switch develop && git pull && git switch -c test/fixtures-drift
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)"
```
Expected: your new START (218 or more).
- [ ] **Step 2: Write the drift test.** Append to `tests/scripts/test_export_summary.py`:
```python
COMMITTED_FIXTURE_FOLDER = REPO_ROOT / "web" / "src" / "app" / "core" / "api" / "fixtures"
STALE_HINT = "stale fixtures: run `uv run python scripts/export_summary.py` and commit the result"


def test_the_committed_fixtures_match_a_fresh_export(tmp_path):
    export_to(tmp_path)
    for name in EXPECTED_FILES:
        assert (COMMITTED_FIXTURE_FOLDER / name).read_text(encoding="utf-8") == (tmp_path / name).read_text(
            encoding="utf-8"), STALE_HINT
```
- [ ] **Step 3: Run it**
```bash
uv run --locked pytest tests/scripts/test_export_summary.py --no-cov 2>&1 | tail -1
```
Expected: `6 passed` if F1 committed a current export. If it prints `1 failed, 5 passed` with `AssertionError: stale fixtures: run ...`, go on to Step 4.
- [ ] **Step 4 (only if Step 3 failed): regenerate, then check both apps**
```bash
uv run python scripts/export_summary.py | wc -l
uv run --locked pytest tests/scripts/test_export_summary.py --no-cov 2>&1 | tail -1
cd web && yarn test 2>&1 | tail -3 && cd ..
```
Expected: `6`; `6 passed`; `yarn test` ends without `error Command failed`. If `yarn test` fails, stop and ask Mildred: her tests disagree with the real figures.
- [ ] **Step 5: Full suite and commit**
```bash
uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"
git add tests/scripts/test_export_summary.py web/src/app/core/api/fixtures
git commit -m "Keep the committed front-end fixtures equal to a fresh export from the real summary"
```
Expected: START + 1 passed (`219` on the dry-run base), `TOTAL ... 96%`.
- [ ] **Step 6:** With Linus's and Mildred's OK, push and open the PR to `develop` ("Fixtures drift test (L4, after F1)"). No attribution lines. Update L4's [[Build order]] row.

**Task done when:** on `develop` after the merge, `uv run --locked pytest tests/scripts/test_export_summary.py --no-cov` prints `6 passed` and `cd web && yarn test` passes.

## Done means (checklist)
- [ ] `uv run python scripts/export_summary.py --out /tmp/l4-check | wc -l` prints `6`. *Verify:* run it from the repo root.
- [ ] `/tmp/l4-check/summary.json` shows `"records_reconciled": 18420` and `"days_remaining": 102` under `final_cutover`. *Verify:* `grep -n '"records_reconciled": 18420' /tmp/l4-check/summary.json` and `python3 -c "import json; print(json.load(open('/tmp/l4-check/summary.json'))['final_cutover']['days_remaining'])"` prints `102`.
- [ ] `uv run --locked pytest` prints `218 passed` (START + 5) after Task 1, and START + 1 more after Task 3. *Verify:* run it.
- [ ] PR 1 open or merged with only the two Python files; PR 2 (Task 3) open or merged after F1. *Verify:* `gh pr view <nn> --json files --jq '.files[].path'`.
- [ ] Mildred's mock mode shows 58% reconciled, 7 blockers and 102 days (her F1 acceptance). *Verify:* `cd web && yarn start`, open the dashboard in mock mode.
- [ ] [[Build order]] row L4 updated. *Verify:* open the note.

## Never
- Compute or round a figure in the script (the builders do it, D-001).
- Overwrite `ask-E4.json`, `ask-partial.json`, `publish.json` or `approve.json`.
- Commit generated fixtures that break `yarn test`.
- Push to `develop` or `main`, or add attribution lines.

Related: [[L4 - Front-end fixtures from the real summary - spec]], [[Mildred - front end]], [[Build order]], [[How to execute a plan]]
