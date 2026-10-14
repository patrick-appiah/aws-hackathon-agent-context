---
date: 2026-10-13
status: open
tags: [decision, status/open, area/bedrock]
---
# Default models
## Decision
Sonnet 4.6 (`eu.anthropic.claude-sonnet-4-6`) for orchestrator, analyst, critic and writer; Haiku 4.5 for the retriever once it activates, else `eu.amazon.nova-lite-v1:0`.
## Why
Smoke test: Sonnet 4.6 OK at 0.9 s; Nova Lite OK at 0.36 s; Haiku blocked.
## Rejected
Opus-class models (too slow and costly for a live loop).

Related: [[Decisions]], [[Bedrock smoke test 2026-10-13]], [[Haiku needs use-case form and agreement]]
