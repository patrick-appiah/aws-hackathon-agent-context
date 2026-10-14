---
date: 2026-10-13
status: done
tags: [decision, status/done, area/architecture]
---
# Ask spine on Step Functions
## Decision
`/ask`: budget check → orchestrator → claims to ledger → critic per claim → retry Choice (counter read from ledger) → writer, as a synchronous Express workflow. `/publish`: Standard workflow + `waitForTaskToken`.
## Why
The rubric scores saying which steps are fixed flows vs agents. The state machine (not the orchestrator) invokes the critic, keeping it blind. Questions are read-only, so they answer in seconds; only publish waits for a human.
## Rejected
Every answer through human approval (teammate's v1 diagram); orchestrator calling the critic directly.

Related: [[Decisions]], [[Teammate target diagram v1 review]]
