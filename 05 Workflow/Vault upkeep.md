---
tags: [workflow, area/process]
---
# Vault upkeep
When and how to write to this vault. Full detail lives in the repo `docs/TEAM_PLAN.md`; this note is the working checklist.

## Read (start of every session)
Latest [[Sessions]] note (top line: **Next command**) → [[Open follow-ups]] → the MOC for your area.

## Write at three moments, not at the end
1. **A decision is made:** a note in `01 Decisions/` (decision, why, rejected) + a row in [[Decisions]]. Keep the repo's `DECISIONS.md` in sync.
2. **Something is learned or confirmed:** one fact per note in `02 Learnings/` with **Why** and **How to apply** + a row in [[Learnings]].
3. **A loose end appears:** a checkbox in [[Open follow-ups]] immediately, with an `#area/` tag.

## Conventions
- Tick follow-ups with the commit or run ID that closed them; never delete them.
- Update an existing note rather than creating a second one.
- End every note with `Related: [[<its MOC>]]`. Use aliases for long names.
- Today's [[Sessions]] note: what shipped, what's half done, and the exact next command.
- No client/company/system names, no PII, no passwords or keys.
- **File names must work on Windows:** no `: * ? " < > | \ /` in note names (Windows can't check them out; the vault is a shared git repo). Write times as `1400`, not `14:00`; use an alias for the display text: `[[Code freeze is Day 2 1400|… 14:00]]`.
- **Team plan has three copies:** the repo's `docs/TEAM_PLAN.md` is canonical. After any change to it, regenerate [[Team plan]] from it (the note records `synced_from_commit`) and republish the shared team page.

Related: [[Workflow]], [[Team plan]]
