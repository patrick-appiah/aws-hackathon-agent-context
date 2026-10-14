---
date: 2026-10-13
tags: [learning, area/claude-code]
---
# Auto mode blocks IAM permission grants
Claude Code auto mode refuses to create IAM users or attach admin policies itself.

**Why:** Classified as a permission grant.
**How to apply:** Claude writes the script (`create-team-users.sh`); the user runs it with `! bash ...`.

Related: [[Learnings]]
