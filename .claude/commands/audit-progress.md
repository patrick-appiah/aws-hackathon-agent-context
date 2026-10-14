---
description: Run the progress auditor and write a dated report to 08 Progress/
argument-hint: "[--at <sha>] [--no-tests]"
---
Launch the `progress-auditor` agent (Agent tool, `subagent_type: progress-auditor`) with this prompt, word for word:

"Run a progress audit now. Collector arguments: $ARGUMENTS"

Do nothing else yourself: don't run the collector, and don't read, edit or summarise the report. When the agent returns, print the report path and its summary paragraph exactly as it gave them. If it stopped with a collector message, print that message.
