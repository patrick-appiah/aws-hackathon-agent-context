---
tags: [build, plan, area/architecture]
id: A4a
owner: Abdul
spec: "[[A4a - Target architecture diagram v2 - spec]]"
status: ready
updated: 2026-10-14
---
# A4a: target architecture diagram v2 (implementation plan)

> **For the executing agent (and Abdul):** follow [[How to execute a plan]] exactly, with one change: **Abdul does not run Python, uv or pytest.** Where a command is needed, ask Linus to run it and send you the output, and compare it with `Expected:`. Work the tasks in order. If anything differs from `Expected:`, stop and follow "When output doesn't match".

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[A4a - Target architecture diagram v2 - spec]]: **the authority** (§3 boxes, §4 arrows). Where this plan and the spec disagree, the spec wins; record the conflict in your ledger.
3. [[Teammate target diagram v1 review]] and repo `ARCHITECTURE.md` §3b and §6.
4. [[Roadmap]].

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If it's still unclear, stop and ask Patrick.

**Goal:** `docs/architecture-target-v2.png` and its source on `develop`, reviewed by Patrick, with every box of spec §3 (phase badge included) and every arrow of spec §4.

**Architecture:** a picture of `ARCHITECTURE.md` §3b. Nothing in the code reads it; `ARCHITECTURE.md` and the slides (B3) point to it.

**Tech stack:** draw.io (desktop app or `https://app.diagrams.net`, "Device" storage, so nothing goes to a cloud account) or Excalidraw; VS Code + Git; GitHub.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: `docs/architecture-target-v2` from an up-to-date `develop`.
- **Start state:** `docs/` holds `architecture-target-v1.png`, `DEVOPS_HANDOVER.md`, `ROADMAP.md`, `TEAM_PLAN.md`; no `architecture-target-v2.*`. `ARCHITECTURE.md` §3b ends with the line "… `docs/architecture-target-v1.png` (v2 pending, to match this diagram)." Linus's `uv run --locked pytest` on `develop`: your baseline count (≥ `204 passed`, ≥ 96%).
- **Your ledger:** `.superpowers/ledger-A4a.md` (gitignored).
- **Rules:** only names from `ARCHITECTURE.md`; no real company, system or person names, no vendor logos; stay in `docs/architecture-target-*` (the `ARCHITECTURE.md` line only with Patrick's OK); Markdown guard tests (no bare `` `pytest` ``, no `uv run pytest`, no `python scripts/…` without `uv run `, test files only by `tests/…` path); commits with the given messages; **no `Co-Authored-By` and no "Generated with" lines**; never push to `develop` or `main`; PR to `develop`; Patrick reviews and merges.

## Review Focus (what nothing tests; check by hand at the end)
1. The writer's answer goes **straight to the portal**; only `POST /publish` goes through the delivery lead (v1's main error).
2. The dashed arrow **Run ledger ⇢ Retry guard "attempt count"** is there.
3. Every box has a badge, and the badges match spec §3 exactly (`P0 + P1` for Cognito, `P2` for Lake Formation and CloudTrail).
4. The critic box says "claim + cited rows only"; no arrow reaches the critic from the orchestrator.
5. The exported PNG is the **same** as the committed source (re-export after the last edit).

---

### Task 1: Draw it (D2 09:00–11:30, or D1 evening)

**Files:** Create `docs/architecture-target-v2.drawio` *(new)*.
**Produces:** the source diagram. **Consumes:** spec §2–§4.

- [ ] **Step 1: Branch and ledger.**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
git switch -c docs/architecture-target-v2
mkdir -p .superpowers && printf '# Ledger: A4a target diagram v2\n' > .superpowers/ledger-A4a.md
```
Expected: `Switched to a new branch 'docs/architecture-target-v2'`.

- [ ] **Step 2: New diagram.** Open draw.io → Create New Diagram → Blank → name `architecture-target-v2.drawio` → save to `~/amalitech/aws-hackathon/erp-migration-portal/docs/`. Enable AWS shapes: left panel → "+ More Shapes" → tick "AWS 2025" (or "AWS 19") → Apply.
Expected: an empty canvas; the file `docs/architecture-target-v2.drawio` shows in VS Code's Explorer and in Source Control as a new file.

- [ ] **Step 3: The six containers.** Draw six labelled rectangles (Arrange → Insert → Container, or a rectangle with the text at the top), named exactly as spec §2 "Groups". Lay them out top to bottom: "Front end and access" at the top; "Data layer" on the left; "Read path 1" and "Read path 2" in the middle; "Write path" on the right; "Cross-cutting" along the bottom.
Expected: six empty, labelled containers.

- [ ] **Step 4: The boxes.** For each row of spec §3, add a box in its container with the box text, and a small rounded badge in its top-right corner with the badge text (`P0`, `P1`, `P0 + P1`, …). Use the AWS shape where there is one (S3, CloudFront, Cognito, API Gateway, Lambda, Step Functions, DynamoDB, Athena, Glue, Lake Formation, EventBridge, CloudWatch, CloudTrail, Bedrock, Verified Permissions, Systems Manager) with the text under it. As you place each, tick it in the spec §3 table (a copy in a scratch tab).
Expected: 34 boxes (one per row of spec §3, including the Users box and the multi-tenant note), every one except Users with a badge; the scratch copy of §3 fully ticked.

- [ ] **Step 5: The arrows.** For each bullet of spec §4, draw the arrows with their labels; dashed (Format panel → Line → dashed) where the spec says dashed.
Expected: every bullet ticked; three dashed kinds (Lake Formation "governs", ledger "attempt count", Guardrails "on every model call").

- [ ] **Step 6: Legend and title.** Bottom-left, the legend text from spec §2. Top, the title `ERP Migration Progress Portal: target architecture (90-day roadmap), v2`.
Expected: legend and title visible.

- [ ] **Step 7: Save and commit the source.**
```bash
git add docs/architecture-target-v2.drawio
git commit -m "Target architecture diagram v2 source: ARCHITECTURE.md §3b with the roadmap phase per box"
```
Expected: `1 file changed`.

**Task done when:**
- `docs/architecture-target-v2.drawio` is committed;
- every row of spec §3 and every bullet of spec §4 is ticked in your scratch copy.

### Task 2: Export and self-check (D2, by 11:45)

**Files:** Create `docs/architecture-target-v2.png` *(new)*.

- [ ] **Step 1: Export.** draw.io → File → Export as → PNG → Zoom `200%`, Border width `10`, Transparent background **off**, "Include a copy of my diagram" off → Export → save as `docs/architecture-target-v2.png`.
Expected: a PNG in `docs/`; opened in VS Code it shows the whole diagram on white.

- [ ] **Step 2: Self-check the five Review Focus points** on the PNG (not the source).
Expected: all five hold. Write `Review Focus: 1 ok, 2 ok, 3 ok, 4 ok, 5 ok` in the ledger (or what's wrong, then fix it in the source, re-export, re-check).

- [ ] **Step 3: Commit and push.**
```bash
git add docs/architecture-target-v2.png
git commit -m "Target architecture diagram v2 exported as PNG"
git push -u origin docs/architecture-target-v2
```
Expected: `1 file changed`, then the tracking line.

**Task done when:**
- the PNG is committed and pushed, and the ledger has the five Review Focus results.

### Task 3: Review with Patrick, PR (D2, by 15:00)

**Files:** Modify `ARCHITECTURE.md` (one line, only with Patrick's OK).

- [ ] **Step 1: Open the PR.** Base `develop`, title `Target architecture diagram v2 (A4a)`. Body:
```markdown
v2 of the target diagram, drawn from ARCHITECTURE.md §3b with the roadmap phase on every box (§6), and the seven fixes from the v1 review:
1. ask answers go straight to the portal; only publish waits for the delivery lead
2. purely the target, with P0–P3 badges
3. budget check before the orchestrator
4. retry guard ← run ledger (attempt count)
5. Step Functions labelled: Express ask spine, Choice retry guard, Standard publish + waitForTaskToken; orchestrator = the one planning agent
6. external data in sources
7. critic gets claim + cited rows only; rejected records reach the portal as "could not verify"
Source: docs/architecture-target-v2.drawio. @Patrick: OK to also update the "v2 pending" line in ARCHITECTURE.md §3b (text in the A4a spec §5)?
```
  Request review from Patrick.
Expected: the PR shows 2 files (`.drawio`, `.png`); GitHub renders the PNG in "Files changed".

- [ ] **Step 2: Apply Patrick's comments** in the source, re-export the PNG (Task 2 Step 1), commit `Target diagram v2: review fixes`, push.
Expected: Patrick's comments are each answered "done" in the PR.

- [ ] **Step 3: The `ARCHITECTURE.md` line (only if Patrick said yes).** Replace the line exactly as spec §5. Commit `ARCHITECTURE: point the target view at diagram v2`, push. Ask Linus to run `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"` on the branch.
Expected: `1 file changed, 1 insertion(+), 1 deletion(-)`; Linus's output shows the baseline count, no `failed`.

- [ ] **Step 4: Ledger:** `Task 3: complete (PR #nn approved by Patrick <date>)`. Tell Patrick and Michael the PNG path for the slides (B3).

**Task done when:**
- Patrick approved the PR (or wrote OK in it);
- if the `ARCHITECTURE.md` line was changed, Linus's output shows 0 failed.

## Never
- Add a service or box that isn't in `ARCHITECTURE.md`.
- Draw the writer's answer through the approval step.
- Commit a PNG exported before your last source edit.
- Use a real company, system or person name, or a vendor logo.
- Push to `develop` or `main`, or add attribution lines.

## Done means
- [ ] **`docs/architecture-target-v2.png` and `docs/architecture-target-v2.drawio` are on `develop`.** *Verify:* GitHub → `develop` → `docs/` lists both; the PNG opens.
- [ ] **Every box and arrow is there.** *Verify:* a second person ticks spec §3 (34 boxes; all but Users with the badge in the table) and spec §4 against the PNG; none missing.
- [ ] **The seven v1 fixes are visible.** *Verify:* the PR body's list, each point visible in the PNG (for example, no arrow from Writer to "Delivery lead approves").
- [ ] **Patrick approved.** *Verify:* the merged PR shows his approval or written OK.
- [ ] **`ARCHITECTURE.md` points to v2** (if Patrick agreed). *Verify:* `ARCHITECTURE.md` §3b on `develop` names `docs/architecture-target-v2.png`; Linus's output in the PR shows 0 failed.

Related: [[A4a - Target architecture diagram v2 - spec]], [[Build order]], [[How to execute a plan]]
