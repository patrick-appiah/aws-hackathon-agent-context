---
tags: [build, workflow, area/process]
updated: 2026-10-14
---
# How to run the progress auditor
> Checks what's done and what isn't against the briefs, [[Build order]], specs, plans and the rubric, and writes a dated report to `08 Progress/`. Read-only: its only writes are the report and a row in [[Progress]]. Spec: [[Progress auditor - spec]].

## Once per machine
1. Pull this vault (`git pull`), and have the repo cloned and `gh` logged in (`gh auth status`).
2. `cp .claude/auditor/local.example.json .claude/auditor/local.json` and set `"repo"` to your clone of `Amali-Tech/cloud-9-hackathon`.

## Each run
1. Start Claude Code **at the vault root** (the folder with `00 Home.md`): `claude`.
2. Type `/audit-progress`. Options: `--no-tests` (skips the ~1-minute test run), `--at <sha>` (audits an older commit).
3. It prints the report path and summary. Link the report from today's [[Sessions]] note yourself; the auditor never edits other notes.
4. Commit the report and the index row: `git add "08 Progress" && git commit -m "Progress report <date> <time>"`.

## What it can't check
AWS (deploys, endpoints, the Guardrail) and the front-end tests (it reads CI instead). The report lists these under "Not checked".

## If something's wrong
- "missing …/local.json": step 2 above.
- "a report for … already exists": wait a minute.
- A finding is wrong: tell Patrick, with the report name and the row. Wrong findings become eval cases (`evals/`).

Related: [[Workstreams]], [[Build order]], [[Progress]]
