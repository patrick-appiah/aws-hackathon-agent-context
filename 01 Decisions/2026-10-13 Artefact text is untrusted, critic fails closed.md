---
date: 2026-10-13
status: done
tags: [decision, status/done, area/security]
---
# Untrusted artefact text, critic fails closed
## Decision
Artefact free text goes inside `<evidence>` tags as data; Guardrail prompt-attack filter on; citations checked in code before the critic runs; critic rejects on any malformed output, model error or guardrail block. Probe row DEF-0462 (was DEF-0430 before D-019), eval Q12.
## Why
Background security review flagged prompt injection in the critic; also found `json.loads` without handling, i.e. the critic failed open.
## Rejected
System prompt as the only defence; exceptions bubbling up

Related: [[Decisions]]
