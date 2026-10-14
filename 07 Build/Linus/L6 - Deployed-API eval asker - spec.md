---
tags: [build, spec, area/evals]
id: L6
owner: Linus
status: ready
updated: 2026-10-14
---
# L6: the deployed-API eval asker (spec)
> **The same 14 questions, asked of the real system in AWS.** An asker for `evals/run.py` that sends each question to `POST /ask` with the right user's ID token and maps the reply to the runner's contract. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop`; usable once L3, Y1 and M3* are deployed.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Workstreams]] §6 ("evals recorded honestly" is a hard gate) and §7; [[Linus - API, identity, blocker-analyst]] §6.
3. The repo's `evals/run.py` (its docstring is the **asker contract**) and `EVALS.md` (the 14 questions, how a run is recorded).
4. [[L3 - Ask, publish and approve entry points - spec]]: the `/ask` route this asker calls, and its 403 `out_of_scope` refusal (Q11).
5. [[Abdul - evals, Cognito, docs]] (the test users per role, the results write-up) and [[Michael - DevOps]] / [[Yaw - DevOps]] (the Cognito pool, the API's base path `/api`).
6. [[Huvison - trust and flow]] §7: the **local** asker (`flow/local.py` *(new)*), which applies `inject`; this one can't.
7. `01 Decisions/`: [[2026-10-13 Scope from the token, enforced twice]] (D-010); `05 Workflow/`: [[Deploy and demo checks]], [[Handling security findings]].

**Whenever this note is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline ([[Problem statement]], [[Judging rubric]], [[Pitch track grading rubric]], [[Hackathon guideline]]); `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Linus. Never invent a name, a shape or a rule.

## 1. Intent
**What:**
1. Two settings in `config.py`: `eval_api_base_url` (`EVAL_API_BASE_URL`) and `eval_id_tokens_file` (`EVAL_ID_TOKENS_FILE`), both default `None`.
2. `evals/api_asker.py` *(new)*: `ask(case_input, scope, _repository) -> dict`, run as `uv run python -m evals.run --asker evals.api_asker:ask`.
   - `POST <EVAL_API_BASE_URL>/ask` with `AskRequest {entity_id, question}` and `Authorization: Bearer <ID token>` for the case's scope, read from the tokens file (keyed `role:entity_ids`, e.g. `entity_lead:E4`).
   - 200 → the `AskResponse` body. 403 with `"error": "out_of_scope"` → that body plus `"refused": true, "status_code": 403`. Any other status → `AskFailed`.
   - Questions it can't send raise before anything is sent: an `inject` condition (Q08, Q09) → `InjectNeedsTheLocalAsker`; no `entity_id` (Q05) → `NoEntityToAsk`; a scope with no token in the file → `NoTokenForScope`; a base URL that isn't `https://` → `DeployedApiCannotAsk`.
3. An `EVALS.md` paragraph on how to run it.

**Why:**
- The judges check that evals are recorded honestly, failures included, and the rubric rewards a system that genuinely runs. The local asker proves the agents; this one proves the deployed path: API Gateway, the JWT authorizer, the Lambda, the state machine and the scope gate in AWS.
- Q11 against the deployed API is the end-to-end proof of the Cognito slice (the D2 12:00 go/no-go).

**Success means:**
- With a fake HTTP layer: Q01 is posted to `<base>/ask` as `POST` with the CFO's token and the exact body, and the 200 body comes back unchanged; Q11's 403 `out_of_scope` comes back as a refusal with the E4 lead's token; a 403 `forbidden` and a 500 raise `AskFailed`; Q05, Q08 and Q09 raise before any request; `""`, `http://` and `file://` base URLs are refused; a missing token for a scope is refused; no tokens file means no `Authorization` header.
- Through the runner: Q11 and Q01 score `pass`; Q08 scores `fail` with `agent loop answered` in its detail.
- `uv run --locked pytest`: START + 15 (219 on a develop with only C1), coverage unchanged (96%; `evals/` isn't measured).
- On D2, one results file `evals/results/run-*.json` from this asker against AWS is committed and handed to Abdul.

**Assumptions:**
- **L3** returns the `AskResponse` JSON on 200 and `ErrorResponse {"error": "out_of_scope", ...}` with 403 for Q11 (the C1 contract).
- **Y1** serves the API at `https://<portal domain>/api` (CloudFront `/api/*`, Michael's M4) or the API Gateway URL; the JWT authorizer reads `Authorization` (with or without `Bearer `).
- **Abdul + Michael (A2, M3\*)** have test users for the CFO (`cfo`, `*`) and the E4 lead (`entity_lead`, `E4`). Their ID tokens are fetched by hand before a run (signing in to the portal, or the Cognito CLI if Michael enables a password flow on the test client), pasted into a file **outside the repo**, and never committed. Tokens expire after an hour.
- `config.py` is Patrick's file: the two settings need his review in the PR.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| What counts as "refused" | Only 403 with `error == "out_of_scope"` | Any 403 (a broken token gives 403 `forbidden`, which would falsely pass Q11) |
| Questions the API can't express | Raise a named exception before sending; the runner records the case as `fail` with the exception's name | Skipping them (looks like a pass); a fault switch in the API (forbidden: "No fault switch exists in the API", Huvison's brief) |
| Where tokens come from | A local JSON file named by `EVAL_ID_TOKENS_FILE`, one token per scope | Passwords in settings (secrets in the environment); tokens in the repo (a hard-gate failure) |
| How settings are read | `config.get_settings()` (the only place settings live) | `os.environ` in `evals/` (breaks the settings rule) |
| HTTP client | The standard library (`urllib.request`), https only (`# nosec B310` with the reason) | Adding `requests` (a new dependency for one call) |
| Timeout | 35 s, a little over API Gateway's 29 s, so the gateway's 504 arrives | No timeout (a hung run blocks the whole eval) |

## 3. Shapes and behaviour
| Name | Signature | Behaviour |
|---|---|---|
| `ask` | `(case_input: EvalInput, scope: Scope, _repository) -> dict` | the asker contract (`evals/run.py`) |
| `post_ask` | `(url: str, body: bytes, id_token: str \| None) -> tuple[int, dict]` | one POST; status and JSON reply, for error statuses too |
| `id_token_for` | `(scope: Scope, tokens_file: str \| None) -> str \| None` | the token for `scope_key(scope)`, `None` without a file |
| `scope_key` | `(scope: Scope) -> str` | `"<role>:<entity_ids joined by ,>"` |
| Exceptions | `DeployedApiCannotAsk(ValueError)` and its subclasses `InjectNeedsTheLocalAsker`, `NoEntityToAsk`, `NoTokenForScope`; `AskFailed(RuntimeError)` | raised as described in §1 |

Tokens file shape: `{"cfo:*": "<ID token>", "entity_lead:E4": "<ID token>"}`.

## 4. Tests
- `tests/test_config.py`: the two settings' defaults and environment overrides (+2 parametrised cases).
- `tests/evals/test_api_asker.py` *(new)*, 13 tests with a fake `urllib.request.urlopen`: the request sent; the refusal; two failing statuses; Q08, Q09, Q05 raise before sending; three bad base URLs; a missing token; no tokens file; the runner scoring Q11, Q01 and Q08.

## 5. Out of scope
- The local asker and `inject` (Huvison, H6); the runner itself (`evals/run.py`, unchanged).
- Creating Cognito users or fetching tokens automatically.
- Writing up the results in `EVALS.md` (Abdul, A5): this item produces the results file.

Related: [[L6 - Deployed-API eval asker - plan]], [[L3 - Ask, publish and approve entry points - spec]], [[Build order]]
