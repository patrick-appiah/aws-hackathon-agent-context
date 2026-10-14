---
tags: [build, spec, area/frontend, area/demo]
id: F6
owner: Clement (with Patrick)
status: ready
updated: 2026-10-14
---
# F6: demo rehearsal, 2-minute backup video, `DEMO.md` (spec)
> **No code.** The live demo is scored (Judging rubric 2.2: "end-to-end live on AWS"; "relying on the backup recording caps 2.2 at 3"), and the organisers require a 2-minute backup video. This item makes `DEMO.md` the real script and checklist, runs two cold-start rehearsals, and records the video. Day 2, 16:00–17:00 (M5), after everything else is merged.

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`; lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`). Read, in this order:
1. [[How to execute a plan]] (`07 Build/`): the procedure, the rules for commits and PRs, and what to do when stuck.
2. [[Workstreams]] (§3 the code already built, §7 the rules) and your brief, [[Clement - front end]].
3. [[Build order]]: every item in this one's "Depends on" column must be `merged` before you start.
4. [[C1 - API and spine contracts - spec]]: the API shapes this item builds on (`web/src/app/core/api/schema/*.schema.json` are generated from them).
5. [[Patrick - contracts, orchestrator, retriever]] (he presents and drives the demo with you).
6. `04 Reference/`: [[Judging rubric]] (2.2, the demo process: 10 minutes pitch and demo, live), [[Pitch track grading rubric]], [[Hackathon guideline]].
7. `05 Workflow/` [[Deploy and demo checks]] (rehearse twice, the decoy live, the video on the laptop, pre-flight).
8. [[A2 - Cognito groups, claims and test users - spec]] (the test usernames) and [[A4b - HANDOFF and DEMO lines - spec]] (Abdul adds eval and cost lines to `DEMO.md`: keep them).
9. Every front-end item: [[F2 - Click a number and the live API - spec]], [[F3a - Cognito sign-in - spec]], [[F3b - Role views and the 403 refusal - spec]], [[F4a - Ask panel on the real ask contract - spec]], [[F5 - Publish and approve on the real API - spec]].
10. [[Dev loop]] and [[Working with AI assistants]] (`05 Workflow/`).

**When this document is silent or unclear, look in the vault before guessing:** `04 Reference/` (the brief, the rubrics, the guideline), `03 Sessions/` (what happened when) and `Open follow-ups.md` (known open questions). If it is still unclear, **stop and ask the owner** named in the frontmatter. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. `DEMO.md` rewritten for the real portal: two browser windows (CFO driver, delivery-lead approver), the 3-minute script with exact clicks and the figures that must appear, an access answer for Q&A (the E4 lead's refusal), the pre-flight checklist, a rehearsal log, and where the video is.
2. **Two cold-start rehearsals**, on the clock, each logged with its time and what went wrong.
3. **The 2-minute backup video**, recorded from the live portal, kept on the laptop and a USB stick.

**Why:** 2.2 is 12 % of the score and the demo must be live; a weeks-old-deck problem is told best by the screen, the cited answer and the critic catching the decoy. Rehearsing from cold finds the cold-start latency and the forgotten sign-in before the judges do.

**Success means:** `DEMO.md` on `develop` holds the script and checklist below (Abdul's lines kept); two rehearsal rows with total times of 3:00 or less; `demo-backup-2026-10-15.mp4` plays, lasts 1:45–2:05, and is on the laptop and the USB stick.

**Assumptions:** Abdul's test users exist as in A2 (`demo-cfo`, `demo-delivery-lead`, `demo-entity-lead-e4`; passwords given out of band). The figures are the dataset's (58 %, 96 %, 7, 102, 103 %). The organisers accept MP4. The final demo date in the file name is the Day 2 date (2026-10-15); change it if Day 2 differs.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Who drives | Clement drives, Patrick presents | One person doing both (slows the clicks) |
| Signed in as | CFO in window A, delivery lead in window B | One user (the CFO can't approve; a sign-out mid-demo costs 20 s) |
| Recording tool | **OBS Studio** (free, Windows/macOS/Linux; "Display Capture" + microphone, MP4) | Phone filming the screen (unreadable figures) |
| Where the video lives | Laptop + USB stick + the organisers' submission | Only in the cloud (the guideline says keep it on the laptop) |
| The refusal | In Q&A, not the 3 minutes (time) | Cutting it (security is a gate; be ready to show it) |

## 3. Out of scope
The pitch slides and the value case (B2, B3a); the eval and cost lines in `DEMO.md` (Abdul, A4b); any code change.

Related: [[F6 - Demo rehearsal and backup video - plan]], [[Build order]], [[Clement - front end]]
