---
date: 2026-10-13
status: done
tags: [decision, status/done, area/bedrock]
---
# No LiteLLM
## Decision
Agents call Bedrock through Strands' native provider.
## Why
Guardrails attach natively; one IAM story; token usage comes back on every call for the ledger. LiteLLM's cross-provider fallback is a liability against the region gate.
## Rejected
LiteLLM SDK, proxy or Strands `LiteLLMModel` (**team-confirmed 2026-10-13**). Also: guardrails and AgentCore tracing need extra pass-through; the budget ceiling must be in the orchestrator, not a proxy; a proxy must also deploy from clean. Cost per run = Bedrock token counts × our own price table. Revisit only if cross-provider fallback is needed after the event.

Related: [[Decisions]], [[2026-10-13 EU-only Bedrock inference profiles|EU-only inference profiles]]
