---
date: 2026-10-15
status: decided
tags: [decision, area/flow, area/api]
---
# /ask is asynchronous: start, then poll (D-023)
## Decision
- **`POST /ask`** checks the scope, starts the Express ask machine with `states:StartExecution` (not `StartSyncExecution`) and returns `AskPending` `{run_id, status: "running"}` at once. The API makes the `run_id`.
- **`GET /ask/{run_id}`** returns the `AskResponse` once `write_answer` has stored it on the run in the ledger, and `AskPending` until then.
  - It answers only a caller whose scope covers the run's stored scope.
  - A run the ledger doesn't hold yet is a 404. The machine's first state (`check_budget`) creates it within about a second, so the ask panel waits a few seconds before its first poll. The ledger stays create-once.
- **Polling reads the ledger, never Step Functions,** so the ask spine stays Express (D-007).
- **The ask machine's timeout** rises above the measured run time, within Express's 5-minute limit.
- **Repo decision:** D-023 in `DECISIONS.md` (Patrick, 2026-10-15).

## Who builds what
- **Patrick:** `AskPending` in `tools/api_schema.py`, with its JSON Schema for the front end (PR, `feature/ask-async-contract`).
- **Linus (L3):** `api.ask` returns `AskPending`; new `api.ask_result` for `GET /ask/{run_id}` (scope check, 404 for an unknown run).
- **Yaw (Y2a §6):** the `GET /ask/{run_id}` route; the ask Lambda gets `states:StartExecution` and `dynamodb:GetItem` on the ledger; the machine timeout.
- **Huvison:** `write_answer` stores the `AskResponse` on the run; a ledger method to read it back.
- **Clement (F4b):** the ask panel polls, after F4a.

## Why
- **H7's rule:** any single run over 25 s moves `/ask` to async. API Gateway ends a synchronous request at 29 s.
- **Every measured run is far over:**
  - local `scripts/ask.py --entity E4` (Bedrock, account 796973512193): 26 s before any critic or writer call (first run), 87 s (second), 2 min 42 s (third, develop 86a03bd);
  - deployed (demo-FlowStack, Michael, 2026-10-15): `run_orchestrator` alone over 60 s, Sonnet about 5.7 s per call, no throttling.
- **Faster isn't enough:** parallel judging and a cheaper retriever cut seconds, not the minute the orchestrator and analyst need.
- **No ten-run p95 needed:** no single run comes near the limit, so H7's timing part is replaced by these figures.

## Rejected
- **Keep `/ask` synchronous and make it faster:** fewer, cheaper model calls can't get a judged, cited answer under 29 s.
- **A Standard ask machine read with `DescribeExecution`:** reverses D-007; asynchronous Express executions have no `DescribeExecution`.
- **WebSockets:** a second API type for one panel.

## Revisit when
- A full judged ask runs reliably under about 20 s (for example a much faster model, or the retriever and critic made cheaper), and the sync path would make the demo simpler.

Related: [[Decisions]], [[H7 - Guardrail settings and ask latency - spec]], [[Y2a - Express ask spine - spec]], [[F4b - Async ask polling - spec]], [[2026-10-15]]
