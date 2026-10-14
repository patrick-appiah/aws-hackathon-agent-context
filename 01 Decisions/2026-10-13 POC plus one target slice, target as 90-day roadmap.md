---
date: 2026-10-13
status: done
tags: [decision, status/done, area/architecture, area/scope]
---
# POC plus one target slice; target as a 90-day roadmap
## Decision
Build the POC in two days, plus one target layer end-to-end: Cognito sign-in with entity scope. Verified Permissions, Athena + Glue, Lake Formation, connectors + EventBridge, CloudTrail and multi-tenant onboarding go into the target diagram and the 90-day roadmap → [[Roadmap]]. Repo: `DECISIONS.md` D-015.
## Why
The 9 Oct rubric proposal asks for "POC and target production state" plus "a 90-day delivery plan with top 3 risks". The 13 Oct rubric scores "real vs faked" and "what gets built first". A POC is far safer for the clean-deploy gate, and it frees seats for evals, cost and the business documents (half the score). The Cognito slice proves the reuse story.
## Rejected
The full target behind fallback switches (the earlier decision, now superseded). POC only (leaves reuse unproven).

Related: [[Decisions]], [[2026-10-13 Two architecture views, POC and target|superseded: build the target]], [[Team plan]]
