---
date: 2026-10-13
status: done
tags: [decision, status/done, area/agents]
---
# Prompts as versioned, locked files
## Decision
Each agent's system prompt is `agents/prompts/<agent>.txt` (YAML frontmatter + exact prompt), loaded only by `load_prompt()`, which refuses anything not matching `prompts.lock`. Verdicts record the prompt version and hash. (A)
## Why
Readable and diffable for reviewers, safe for non-coders to edit, and every verdict and eval result says which prompt produced it.
## Rejected
`.md` files (amended same day): GitHub's rendered view hides `<claim>`/`<evidence>` and merges lines, so reviewers would read different text from what the model gets.
(B) Prompt-store port with S3/SSM adapters: not needed yet. (C) Bedrock Prompt Management: prompts leave the graded repo; local tests would need AWS.

Related: [[Decisions]], [[Changing a prompt]]
