---
tags: [build, spec, area/agents]
id: P3
owner: Patrick
status: awaiting review
updated: 2026-10-14
---
# P3: `scripts/ask.py`, the local ask runner (spec)
> **The README's command 5: `uv run python scripts/ask.py --entity E4 "What is blocking cutover?"` runs the whole ask spine on this machine and prints the answer.** Committed CSV data, an in-memory ledger, the real agents on Bedrock, through Huvison's `infra.functions.spine.run_spine` (H2b). Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` once H2b is merged. The repo is the source of truth for code; the vault is the source of context.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]]: the architecture (§2), the code already built (§3), the contracts (§4), the rules (§7).
3. [[Patrick - contracts, orchestrator, retriever]] §4 "`scripts/ask.py`" and §5 (the README's 5 commands): the owner's brief.
4. [[Huvison - trust and flow]] §3 (the seven ask-spine states) and [[H2b - Agent states, local spine and Lambda handlers - spec]] (`infra.functions.spine.run_spine`, `SpineAgents`): the spine this runner calls.
5. [[Build order]]: P3 depends on **H2b** (and so C1, H1, H2a, H3, H5). The live answer also needs P2 and L5 merged.
6. [[L1 - Scope from the token and the summary handler - spec]] (`infra.functions.scope.demo_scope`, the demo user), [[P2 - Orchestrator agent - spec]] (the orchestrator's entity gate), [[C1 - API and spine contracts - spec]] §3 (`AskResponse`) and §4.
7. `01 Decisions/`: [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]] (D-007, the state order), [[2026-10-13 Scope from the token, enforced twice]] (D-010). The repo's `DECISIONS.md` D-012 (the retry is the ledger's). `05 Workflow/`: [[Dev loop]], [[Deploy and demo checks]].
8. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[Judging rubric]], [[Pitch track grading rubric]], [[Hackathon guideline]], [[Problem statement]]); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask the owner (Patrick). Never invent a name, a shape or a rule.

## 1. Intent
**What:** `scripts/ask.py` *(new)*:
1. builds a `Question` for the demo CFO (`AUTH_MODE=none`'s user) from `--entity` and the question text, with `run_budget_usd` and `max_claim_attempts` from `config.get_settings()`;
2. calls H2b's `infra.functions.spine.run_spine(question, ledger=InMemoryLedger(), repository=CsvRepository(DEFAULT_ARTEFACTS_URI))`, which runs the ask-spine states in the Express state machine's order with the real agents;
3. prints the answer with its citations, the claims that could not be verified, the trace with prompt versions, and the cost; or, with `--json`, the `AskResponse` as JSON (`by_alias=True`, so verdicts show `pass`).

**Why:**
- It is the README's "Run it in 5 commands", step 5 (Workstreams §6: the commit history and the README are graded; the brief's "the agent layer may not be stubbed").
- It is the walking skeleton's local half (D1 16:00 milestone: "the full `/ask` sequence runs locally") before Step Functions exists, and the lead's tool for the demo rehearsal and the Q10 unseen-question rehearsal.
- One spine, one place: the state order, the retry guard and the partial answers live once, in `infra/functions/spine.py` *(new)*; the script only builds the question and prints.

**Success means:**
- `main` builds the demo CFO's `Question` (a `local-<uuid4 hex>` run ID, the settings' budget and attempts) and passes it to `run_spine` with a fresh `InMemoryLedger` and `CsvRepository(DEFAULT_ARTEFACTS_URI)`. Tested with a stand-in `run_spine`.
- An unknown entity returns partial: with the real `run_spine` and a stub orchestrator, the E9 run prints `Partial answer: …` and the writer is not called. Live (P2 merged, no AWS needed): `Partial answer: unknown entity: E9 is not in this programme`, `Cost: $0.0000`.
- `uv run python scripts/ask.py --entity E-4 "…"` exits **2** with `invalid question: entity_id: …` before anything runs.
- With AWS credentials, Q01 (`--entity E4 "What is blocking cutover for E4?"`) prints an answer whose citations include `DEF-0412` and `RC-C3-E4-customers` (verify in AWS).
- `uv run --locked pytest`: the start count **+8 passed**; coverage unchanged (`scripts/` is outside the coverage sources, like `scripts/export_api_schema.py`).

**Assumptions about other items (the reviewer reconciles these):**
| # | Assumes | From | If it differs |
|---|---|---|---|
| B1 | `infra.functions.spine.run_spine(question: Question, *, ledger: Ledger, repository: ArtefactRepository, agents: SpineAgents = SpineAgents()) -> AskResponse`; the default agents are the real ones | H2b | Adapt the one call in `main` and the test stand-in; ledger a Ruling, tell Huvison |
| B2 | `infra.functions.spine.SpineAgents(orchestrator=None, writer=None, critic_agent=None)`, and an orchestrator stand-in with `orchestrate(question, repository, ledger)` and `replan(question, rejected_claim, verdict, repository, ledger)` | H2b | Adapt the unknown-entity test's stand-in only |
| B3 | `infra.functions.scope.demo_scope(settings: Settings) -> Scope` gives `Scope(user_id="demo-cfo", role="cfo", tenant_id=settings.default_tenant_id, entity_ids=("*",))` with the default `DEMO_ROLE` | L1 | Until L1 is merged, `local_scope` builds that same scope itself (pre-L1 variant); once it is, `local_scope` returns `demo_scope(settings)` |

Other assumptions: C1 as reviewed (`AUTH_MODE` defaults to `cognito`; the runner doesn't read it, because `local_scope` and L1's `demo_scope` build the demo user directly; `AskResponse` requires `partial_reason` exactly when `partial` is true). The live run needs `AWS_PROFILE=hackathon`, `AWS_REGION=eu-west-1`, Bedrock access for your sign-in, and P2, L5 and H3 merged.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Who sequences the states locally | H2b's `infra.functions.spine.run_spine`; the script calls it once | A second sequence in the script (two sources of truth for the order and the retry); calling the Step Functions API (needs the deployed stack; the point is to run before it exists) |
| H6 (`infra/functions/local.py` *(new)*) | The script keeps calling `run_spine` after H6 lands. `infra/functions/local.py` is the eval asker (it applies `inject` and maps eval cases); this runner asks one plain question | Switching to `infra.functions.local` (eval-only concerns in the README's command) |
| The user | The demo user of `AUTH_MODE=none`: L1's `infra.functions.scope.demo_scope(settings)` once L1 is merged; until then the same CFO scope (`demo-cfo`, `cfo`, every entity, default tenant) built in `local_scope` | A `--role`/`--entities` flag (scope from the command line is the pattern the rules forbid in the API; the eval runner covers other scopes); a second demo user that can drift from L1's |
| Ledger and data | A fresh `InMemoryLedger` per run and `CsvRepository(DEFAULT_ARTEFACTS_URI)` (the committed CSVs) | DynamoDB or S3 (needs the deployed stacks) |
| Output | Text for people by default; `--json` prints `AskResponse.model_dump(mode="json", by_alias=True)` | JSON only (unreadable in a demo); text only (no machine-checkable output) |
| Bad input | Validated by building `Question` before anything runs; a `ValidationError` → `argparse` error, exit 2, `invalid question: <field>: <message>` | Letting the orchestrator refuse it (it would start a run first) |
| Testing a script | `from scripts import ask` (the repo root is on `pythonpath`; `scripts/` is a namespace package), `run_spine` monkeypatched, plus two subprocess runs for the exit code | Only subprocess tests (can't inject a stand-in) |

## 3. Shapes and behaviour (`scripts/ask.py` *(new)*)
| Name | Signature / value | Behaviour |
|---|---|---|
| `DEMO_USER_ID`, `DEMO_ROLE` | `"demo-cfo"`, `"cfo"` | the pre-L1 demo user (removed in the L1 variant) |
| `LOCAL_RUN_PREFIX` | `"local-"` | run IDs are `local-<uuid4 hex>` |
| `local_scope(settings)` | `-> Scope` | the demo CFO; `demo_scope(settings)` once L1 is merged |
| `render(response)` | `-> str` | lines: `Run <id>`; `Partial answer: <reason>` if partial; `Answer: <headline>` and `  - <text>  [artefact:row_id, …]` per bullet; `Could not verify (n):` and `  - <claim_id>: <statement> (<reason>)`; `Trace: step -> step (agent version) -> …`; `Cost: $0.0000` (4 decimals, `COST_DECIMALS`) |
| `main(argv=None)` | `-> int` | `--entity` (required), the question (positional), `--json`; builds the `Question`, calls `run_spine(question, ledger=InMemoryLedger(), repository=CsvRepository(DEFAULT_ARTEFACTS_URI))`, prints; exit `0` (`EXIT_OK`); `2` on bad input (argparse) |

## 4. Tests (new): `tests/scripts/test_ask.py` *(new)*, 8 tests
- `render` shows the headline, the citation labels, the rejected claims, the trace with prompt versions and the cost; and a partial answer.
- `local_scope` is the demo CFO (`demo-cfo`) of the default tenant.
- `main` passes the demo CFO's question (run ID prefix, entity, text, budget, attempts), a fresh `InMemoryLedger` and a `CsvRepository` to `run_spine`, and prints the text answer.
- `main` with `--json` prints the response with citations as `{artefact, row_id}` and a `local-` run ID.
- An unknown entity, through the real `run_spine` with a stub orchestrator (partial, no claims) and a writer that must not run, prints the partial answer and no `Answer:` line.
- The command exits 2 with `invalid question` for `E-4` and for an empty question (subprocess).

## 5. Out of scope
- The ask-spine states and their order (H2a, H2b), the writer (H3), cost pricing (H5), the eval asker and `inject` (H6).
- Step Functions, Lambda and AgentCore (Yaw).
- Changing the README: command 5 is already `uv run python scripts/ask.py --entity E4 "What is blocking cutover?"`.

Related: [[Build order]], [[Patrick - contracts, orchestrator, retriever]], [[P3 - Local ask runner - plan]]
