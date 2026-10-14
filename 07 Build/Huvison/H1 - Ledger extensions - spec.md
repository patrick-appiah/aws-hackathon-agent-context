---
tags: [build, spec, area/flow]
id: H1
owner: Huvison
status: awaiting review
updated: 2026-10-14
---
# H1: Ledger extensions on both adapters (spec)
> **Every ask-spine state, the publish flow and the eval asker read or write the run ledger through these methods.** H2a, H2b, H4 and H6 build on them; Yaw's IAM and Michael's LedgerStack follow the item layout below. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` once C1 is merged. The repo is the source of truth for code; the vault is the source of context.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] (`06 Workstreams/`): the architecture with owners (§2), the code already built (§3), the contracts (§4), the rules (§7).
3. [[Huvison - trust and flow]] §1 "Ledger extensions": the owner's brief for this item.
4. [[Build order]]: H1 depends on **C1** only. Check it is `merged`.
5. [[C1 - API and spine contracts - spec]] §3 (`AskResponse.rejected`, `trace`), §5 (`rejected_table`).
6. `01 Decisions/`: [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]], [[2026-10-13 Clean-code rules enforced by tests]]. The repo's `DECISIONS.md` D-012 (create-once ledger) and D-013 (one test suite per port). `05 Workflow/`: [[Dev loop]], [[Handling security findings]].

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[Hackathon guideline]] §02 "the reject loop", non-negotiable 5 "state lives outside the agents"); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask the owner (Huvison). Never invent a name, a shape or a rule.

## 1. Intent
**What:** extend the `Ledger` port (`tools/ports.py`) and **both** adapters (`adapters/memory_ledger.py`, `adapters/dynamo_ledger.py`) with:
1. `run(run_id)` and `claims(run_id)`: read back the run (scope, budget, cost, tokens, publish decisions) and every claim (content, attempts, verdicts, status);
2. `put_rejected(run_id, claim_id, verdicts)` / `rejected(run_id)`: the **rejected records**, in their own table;
3. `add_step(run_id, step)` / `steps(run_id)`: the trace, `STEP#<n>` items;
4. `put_task_token(run_id, task_token)` / `task_token(run_id)`: the publish approval token, keyed by `run_id`;
5. `record_decision(run_id, decision)`: each publish decision (approve or send back), appended to the run.

Every method gets tests in the **shared** suite `tests/adapters/test_ledgers.py`, which runs them against `InMemoryLedger` and against `DynamoLedger` on moto.

**Why:**
- The guideline's non-negotiable 5: "a DynamoDB run ledger keyed by `run_id`, holding every claim, its evidence, the critic's verdict, the attempt count and tokens spent". `AskResponse.rejected[]` and `trace[]` (C1) are read from it, and the retry guard reads only its counter (D-012).
- The rejected-record store is the loop's terminal state ("a rejected-record store at the end", guideline §02). It's a separate table so the human triage queue can be read and retained on its own (Michael's LedgerStack, `REJECTED_TABLE`).
- `/approve` takes `run_id` (C1 decision), so the Standard machine's task token must be findable by `run_id`.
- Found while dry-running: `DynamoLedger.put_claim` raises `TypeError: Float types are not supported` for any claim with a decimal figure (`91.2`). The blocker-analyst's claims carry such figures, so the deployed ledger would crash on the first real claim. H1 fixes it, and a shared test pins it.

**Success means:**
- `tools/ports.py` `Ledger` declares the nine new methods with docstrings; both adapters implement them; the shared suite has **13 new behaviours × 2 ledgers = 26 new tests**, and the 5 existing ones still pass on both.
- `DynamoLedger(table_name, region, rejected_table_name)`; `adapters.ledger_from_settings()` passes `settings.rejected_table`.
- A claim with `91.2` and `102` figures reads back identical, `float` and `int` kept, on both adapters.
- Create-once holds for runs, claims, rejected records and task tokens; every method on an unknown run raises `LedgerConflict`.
- `uv run --locked pytest`: **230 passed** on a `develop` with only C1 merged (204 + 26), coverage 96%.

**Assumptions:**
- C1 is merged (`rejected_table` setting, `TraceStep`'s keys `step`, `agent`, `prompt`).
- Michael's LedgerStack (M2) creates the rejected-records table with the **same key schema** as the ledger: partition key `pk` (string), sort key `sk` (string); `sk` holds the claim ID there. Yaw's IAM gives the ask and publish functions `GetItem`, `PutItem`, `UpdateItem`, `Query` on both tables (already in `docs/DEVOPS_HANDOVER.md`).

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| `put_rejected` signature | As the brief: `put_rejected(run_id, claim_id, verdicts)`. The adapter copies the claim's **stored content** into the record, so a rejected record is self-contained for the human queue. It raises `LedgerConflict` if the claim was never stored | Passing the claim content in (a caller could record something other than what the critic judged) |
| Rejected-record shape | `rejected(run_id) -> [{claim_id, claim, verdicts}]` in claim-ID order. The reason shown to the user is the last verdict's (H2a builds `RejectedClaim` from it) | Storing a separate `reason` (a second copy of the verdict's text) |
| `run(run_id)` keys | `{run_id, scope, budget_usd, cost_usd, tokens_in, tokens_out, decisions}`. Money as `float`, tokens as `int`, scope as JSON (`entity_ids` is a list) on both adapters | A stored `status` field: the brief lists "status", but the run's state is fully derived from its claims and decisions; a stored copy would need keeping in sync. Callers derive it |
| Token totals | Already persisted by `add_cost` on both adapters; `run()` exposes them. `add_cost` is unchanged | Rewriting cost storage |
| Step numbering | `add_step` returns the step's number, 1, 2, …; DynamoDB keeps an atomic `step_count` on the RUN item (`ADD step_count :one`, `UPDATED_NEW`) and writes `STEP#0001` (four digits, `STEP_NUMBER_DIGITS`) so the sort key orders steps | `STEP#<n>` unpadded (`STEP#10` sorts before `STEP#2`); a timestamp key (collisions, clock skew) |
| Task token | `pk=run_id, sk=TASK`, create-once; `task_token(run_id)` returns `None` while none is stored | Overwritable (a second publish could swap the token under a waiting approval) |
| Publish decisions | A `decisions` list on the RUN item, appended (`list_append(if_not_exists(...))`); `run()["decisions"]` reads it | A separate item per decision (one more prefix to query; the list is short) |
| Reads | Return copies: DynamoDB naturally; `InMemoryLedger` now deep-copies, so a caller can't change the ledger by editing what it read | Returning internal dicts (the reference adapter would allow what the real one can't) |
| Numbers in DynamoDB | `_to_item` turns floats into `Decimal(str(value))` (and tuples into lists) on every write; `_from_item` turns a `Decimal` with a non-negative exponent back into `int`, any other into `float`. So `102` stays `int`, `91.2` and `6.0` stay `float` | `json` round-tripping (slower, and loses nothing more); leaving floats in (boto3 refuses them) |
| Unknown run on reads | `claims`, `rejected`, `steps`, `task_token`, `run` raise `LedgerConflict` (no silent empty list) | Returning `[]` for a run that doesn't exist (hides a wrong `run_id`) |
| `InMemoryLedger.claims` attribute | Renamed `stored_claims`, because `claims` is now the method | Keeping the attribute (it would shadow the method) |

## 3. Shapes and behaviour
**`tools/ports.py` `Ledger`, new methods** (docstrings as in the plan):
| Method | Returns | Rules |
|---|---|---|
| `claims(run_id)` | `list[dict]`: `{claim_id, claim, attempts, verdicts, status}` | claim-ID order |
| `run(run_id)` | `dict`: `{run_id, scope, budget_usd, cost_usd, tokens_in, tokens_out, decisions}` | |
| `put_rejected(run_id, claim_id, verdicts)` | `None` | create-once; the claim must exist |
| `rejected(run_id)` | `list[dict]`: `{claim_id, claim, verdicts}` | claim-ID order |
| `add_step(run_id, step)` | `int`, the step number | run must exist |
| `steps(run_id)` | `list[dict]`, in order | |
| `put_task_token(run_id, task_token)` | `None` | create-once; run must exist |
| `task_token(run_id)` | `str \| None` | |
| `record_decision(run_id, decision)` | `None` | appended; run must exist |

**DynamoDB items** (run ledger table, `pk = run_id`):
- `sk = RUN`: `scope`, `budget_usd`, `cost_usd`, `tokens_in`, `tokens_out`, `decisions` *(new)*, `step_count` *(new)*, `created_at`.
- `sk = CLAIM#<claim_id>`: unchanged (`claim`, `attempts`, `verdicts`, `status`, `created_at`), numbers stored as `Decimal`.
- `sk = STEP#<nnnn>` *(new)*: `step` (`{step, agent, prompt}`), `created_at`.
- `sk = TASK` *(new)*: `task_token`, `created_at`.

**Rejected-records table** (`REJECTED_TABLE`, default `erp-portal-rejected-records`): `pk = run_id`, `sk = claim_id`, `claim`, `verdicts`, `created_at`.

## 4. Tests (`tests/adapters/test_ledgers.py`, the shared suite; each runs on both ledgers)
- The fixture creates both tables on moto and builds `DynamoLedger(TEST_TABLE, DEFAULT_REGION, TEST_REJECTED_TABLE)`.
- `run` reads back scope, budget, summed tokens and cost, and an empty `decisions`.
- `claims` lists every claim with attempts, verdicts and status, in claim-ID order.
- A claim with an `int` and a `float` figure reads back identical, types kept (the DynamoDB float fix).
- `run` and `claims` on an unknown run raise.
- A rejected record keeps the claim's content and every verdict; it's create-once; only a stored claim can be rejected; `rejected` on an unknown run raises.
- Steps are numbered and read back in order; the order survives more than nine steps; steps need an existing run.
- The task token is stored once by `run_id`; task tokens need an existing run.
- Publish decisions are appended to the run; an unknown run raises.

## 5. Out of scope
- Any state function (H2a, H2b), publish (H4), the eval asker (H6).
- The CDK tables (Michael, M2) and IAM (Yaw, Y4). The plan's last task tells them the item layout.
- A `status` field on the run (see Decisions).

Related: [[H1 - Ledger extensions - plan]], [[Huvison - trust and flow]], [[Build order]]
