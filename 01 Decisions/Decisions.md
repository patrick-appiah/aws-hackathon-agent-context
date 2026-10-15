---
tags: [moc]
---
# Decisions
Newest first. Make new ones from [[Decision template]]. Mirrors `DECISIONS.md` in the repo; the repo file is what judges read.
| Date | Decision | Alternatives rejected | Status |
|---|---|---|---|
| 2026-10-15 | [[2026-10-15 Figures are verified by code, the critic judges rows\|Figures verified by code; critic judges rows (D-029)]] | Metrics pseudo-rows; critic calls tools; no figures | in progress |
| 2026-10-15 | [[2026-10-15 Q05 is a dashboard check\|Q05 is a dashboard check (D-030)]] | Optional entity_id on /ask; Q05 per entity | done |
| 2026-10-15 | [[2026-10-15 Ask is asynchronous, start then poll\|/ask is asynchronous: start, then poll (D-023)]] | Sync /ask made faster; Standard machine with DescribeExecution; WebSockets | done |
| 2026-10-14 | [[2026-10-14 One analyse call per plan\|One analyse call per plan (D-027)]] | Several analyse calls; prompt-only rule; new rows only on a second call | done |
| 2026-10-14 | [[2026-10-14 Two apps in one repo\|Two apps in one repo: Python root, Angular web/ (D-020)]] | backend/+web/; Nx; separate repo; Makefile | done |
| 2026-10-14 | [[2026-10-14 ERP-layer dataset is the single source\|ERP-layer dataset is the single source (D-019)]] | Adapter to old columns; two datasets; porting kpis.py | done |
| 2026-10-13 | [[2026-10-13 POC plus one target slice, target as 90-day roadmap\|POC + one target slice; target = 90-day roadmap]] | Full target behind switches; POC only | done |
| 2026-10-13 | [[2026-10-13 Prompts as versioned locked files\|Prompts as versioned locked files]] | Prompt-store port; Bedrock Prompt Management | done |
| 2026-10-13 | [[2026-10-13 Clean-code rules enforced by tests\|Clean-code rules enforced by tests]] | Linter-only; per-edit reviews | done |
| 2026-10-13 | [[2026-10-13 Artefact text is untrusted, critic fails closed\|Untrusted artefact text, critic fails closed]] | System prompt as the only defence | done |
| 2026-10-13 | [[2026-10-13 Scope from the token, enforced twice\|Scope from the token, enforced twice]] | Client-sent scope | done |
| 2026-10-13 | [[2026-10-13 Ask spine is Step Functions Express, publish is Standard\|Ask spine on Step Functions]] | Every answer through human approval (teammate's v1 diagram) | done |
| 2026-10-13 | [[2026-10-13 Two architecture views, POC and target\|Build the target, with fallbacks]] | POC-only (reversed); target with no fallbacks | done |
| 2026-10-13 | [[2026-10-13 Problem is the Migration Progress Portal, not UC-03\|Problem is Portal not UC-03]] | Keeping UC-03 (the brief rules it out) | done |
| 2026-10-13 | [[2026-10-13 Metrics are code, only the blocker Q&A is agentic\|Metrics are code]] | An LLM summarising the dashboard: decorative, and a second source of truth | done |
| 2026-10-13 | [[2026-10-13 EU-only Bedrock inference profiles\|EU-only inference profiles]] | `global | done |
| 2026-10-13 | [[2026-10-13 No LiteLLM, native Strands BedrockModel\|No LiteLLM]] | LiteLLM SDK or proxy | done |
| 2026-10-13 | [[2026-10-13 Team are admins, workload roles least-privilege\|Team admin vs workload IAM]] | Per-person scoped IAM (too slow for 2 days) | done |
| 2026-10-13 | [[2026-10-13 Default models\|Default models]] | Opus-class models (too slow and costly for a live loop) | open |
| 2026-10-13 | [[2026-10-13 Front end\|Front end]] | Decide by Day 1 12:00 | open |

Related: [[00 Home]]
