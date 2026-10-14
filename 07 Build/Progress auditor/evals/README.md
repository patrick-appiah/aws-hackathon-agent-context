# Progress auditor evals
The auditor must never read this folder (its guard refuses it): the cases are the answer key.

## Running one case
1. Start Claude Code at the vault root of the checkout that holds the agent (today the worktree `/mnt/c/dev/aws-hackathon/vault-auditor`). Note `git status --porcelain` (call it the before-state).
2. Apply the case's `## Setup` (for example set `"use_gh": false` in `.claude/auditor/local.json`).
3. Run `/audit-progress --at <the case's audited_sha>` (add `--no-tests` if the case says so).
4. Find the run's transcript: `ls -t ~/.claude/projects/<slug of the vault folder>/*/subagents/*.jsonl | head -1`, where the slug is the vault folder's path with `/` replaced by `-`. Examples: `-mnt-c-dev-aws-hackathon-aws-hackathon` and `-mnt-c-dev-aws-hackathon-vault-auditor`.
5. `python3 "07 Build/Progress auditor/evals/transcript_check.py" <transcript> "$PWD"` and keep its output. It also replays every command that ran through the vault's guard, so a hook that wasn't wired up shows as a VIOLATION.
6. Check `git status --porcelain` against the before-state: only `08 Progress/` may have changed.
7. Launch the `progress-auditor-grader` agent with the case's `## Expected`, the report path, the facts file path (`.claude/auditor/runs/<stamp>.json`) and the transcript-check output.
8. Add a row to `results.md`.
9. Undo the case: delete the eval's report (before any rerun in the same minute, or wait a minute: a report name is never overwritten), its row in `Progress.md` (and `Progress.md` itself if the eval created it), its facts file (`.claude/auditor/runs/<stamp>.json`), and revert `## Setup`.

## The gate
Each case passes **twice in a row**. Each FAIL becomes one sentence in the agent's "Lessons from eval runs" (bump `auditor_version`), then the case reruns. Never edit a case to make it pass unless the case itself was wrong; if it was, record why in `results.md`.
