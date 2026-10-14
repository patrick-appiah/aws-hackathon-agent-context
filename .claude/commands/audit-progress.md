---
description: Run the progress auditor and write a dated report to 08 Progress/
argument-hint: "[--at <sha>] [--no-tests]"
---
Launch the `progress-auditor` agent (Agent tool, `subagent_type: progress-auditor`) in the foreground, and wait for it to finish, with this prompt, word for word:

"Run a progress audit now. Collector arguments: $ARGUMENTS"

If the `progress-auditor` agent type isn't available, print exactly "progress-auditor agent not loaded: start Claude Code at the vault root" and stop, doing nothing yourself.

Do nothing else yourself: don't run the collector, and don't read, edit or summarise the report. When the agent returns, print the report path and its summary paragraph exactly as it gave them. If it stopped with a collector message, print that message.
