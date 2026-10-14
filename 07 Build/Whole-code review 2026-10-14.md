---
tags: [build, review]
updated: 2026-10-14
---
# Whole-code review, 2026-10-14
> `/simplify` and `/code-review` were run over everything on `develop` (2f372c7) at Patrick's request. **Fixes in Patrick's files** are on `refactor/simplify-core`. **The items below belong to their owners:** pick them up in your next PR. Nobody has edited your files. "Reproduced" means the reviewer ran it and saw it fail.

## Huvison
**Correctness (fix first)**
- [ ] **Critic verdicts aren't validated.** `agents/critic.py` (`judge`) checks the model's verdict only with `_is_valid_verdict` (claim_id, pass, reason), never with `Verdict.model_validate`. A malformed verdict, for example `missing_evidence` as a string, is stored and then crashes `record_rejection` (**reproduced**). It can be triggered by text injected through a cited row. Fix: validate inside `judge`, and turn any failure into `Verdict.rejection`.
- [ ] **No budget check before the critic and the writer.** `infra/functions/steps.py` checks the budget only in `check_budget` and inside the orchestrator. `judge_claim` (the critic) and `write_answer` call models unchecked, and the number of claims has no cap, so a $0.50 run can end at several dollars (guideline §02 rule 7). Fix: `require_budget` before each critic and writer call, and a cap on claims per plan.
- [ ] **State Lambdas read the default tenant's data.** `infra/functions/states.py` builds the repository with `repository_from_settings()` for the default tenant, while the API builds one per tenant from the token. A second tenant's run would be judged against the wrong data. Fix: build it from `ledger.run(run_id)["scope"]["tenant_id"]`.
- [ ] **Usage is lost when the critic or writer raises.** The writer (`writer.py`) and the critic wrapper (`steps.py` `judge_claim`) drop the usage of calls that completed before the error. Fix: `agents.agent_support.record_usage_as_it_happens`, as the orchestrator and the retriever now do.

**Duplication and simplification**
- [ ] **The critic copies `agent_support`.** `critic.py` copies `ESCAPED_CHARACTERS`, `_as_data` and `_tagged` (the D-009 escaping) and builds its `BedrockModel` by hand, without `callback_handler=None`, so it streams raw model text to the logs. Use `agent_support.tagged` and `bedrock_model`, and add `callback_handler=None`.
- [ ] **Unused critic code.** `critic.precheck` has no production caller, and `citations_of` exists in both `critic.py` and `writer.py`.
- [ ] **"Passed claims" is filtered twice.** `steps.write_answer` and `states.write_answer` both filter them from the ledger, and `steps.write_answer` has an unused `repository` parameter.
- [ ] **A stale import workaround.** `steps.py` uses `importlib` for the orchestrator, citing a reason that no longer holds; it duplicates `ORCHESTRATOR_AGENT_NAME`.
- [ ] **Two sources for the retry limit.** `Question.max_attempts` and `get_settings().max_claim_attempts` both set it. Make the Question the only source.
- [ ] **Docstrings name missing files.** They cite `infra/functions/local.py`, `publish.py` and `agents.loop:ask`.
- [ ] **Repeated timestamps.** `dynamo_ledger.py` writes `int(time.time())` 5 times; add a helper.

**Speed** (matters for the 29 s API limit)
- [ ] **Judge claims in parallel.** Each claim is judged one after another, at about 3–6 s per Sonnet call. A thread pool in `run_spine`, or a Step Functions Map state (Yaw), would save about 12 s for 4 claims. That's the biggest latency win in the repo.
- [ ] **Extra ledger reads per state.** Each state does about 8 ledger calls where 4–5 are needed. Pass the stored claim and scope through.

## Linus
**Correctness**
- [ ] **The figure recheck crashes, and nothing calls it.** `tools/claims.py` `_recheck_figures` calls `tool(**figure.args)` with argument names the model chose. A wrong name raises `TypeError`, which isn't caught, so `validate_claim` crashes instead of rejecting the claim (**reproduced**). Also confirm that L5 calls `validate_claim` on the production path. If nothing does, figures are never re-computed (needs coordination: one place, the analyst or `store_claims`).
- [ ] **Every `KeyError` and `ValueError` becomes a client error.** `infra/functions/api.py` `ERROR_CODE_BY_EXCEPTION` maps every `KeyError` to 404 and every `ValueError` to 400, so a data or metrics bug looks like the caller's fault. Raise specific exceptions (unknown entity, malformed request) and let the rest be 500.

**Duplication and simplification**
- [ ] **Error codes are re-exported.** `tools/agent_tools.py` re-exports them with `noqa: F401`. Import all `ERROR_*` from `tools.constants` (Patrick's modules already do).
- [ ] **The scope check is repeated.** `scope.require(entity_id)` is written in 12 tools in `agent_tools.py`; one decorator would cover them. `_visible_entity_ids` re-implements `Scope.allows`.
- [ ] **Blockers are computed repeatedly.** `tools/metrics.py` calls `open_blockers` 8 times per `/summary` for 4 entities. That's cheap today, but compute it once and pass it in. `recon_pass_rate` is a one-line wrapper.
- [ ] **A duplicate status constant.** `evals/run.py` `REFUSED_STATUS_CODE = 403` duplicates `api_schema.HTTP_FORBIDDEN`. Also, `check_citations` runs twice per label.
- [ ] **A duplicate demo user.** `scripts/export_summary.py` builds its own CFO `Scope`; `demo_scope` already does that.
- [ ] **Two repository caches.** `api.py` `repository_for` and `states.make_repository` both cache the repository. Cache it once, in the factory.

## Michael / Yaw
- [ ] **Stack IAM is tight.** No findings for the stacks that exist: GetObject on `artefacts/*`, ledger Get/Put/Update/Query only, ApplyGuardrail on the one guardrail, and client writes limited to `name`.
- [ ] **For the function and state-machine stacks:**
  - set the Lambdas' `LEDGER_TABLE`, `REJECTED_TABLE` and `STATUS_PACK_PREFIX` from the stack's own values, the same ones the IAM statements use;
  - judge claims with a Map state over `judge_claim` (see Huvison);
  - keep the `/summary` and `/entity` Lambdas separate from the Strands Lambdas, for cold start;
  - give the agent Lambdas about 1024 MB.
- [ ] **Small cleanups:**
  - `S3_URI_SCHEME` is duplicated in `infra/constants.py` and `adapters/csv_repo.py`;
  - `get_args(Role)` is written in three places;
  - the demo users repeat role and entity strings.

## Shared adapters
- [ ] **`csv_repo.py`** creates a new S3 client per read and reads one artefact at a time. A cold `/summary` costs about 0.5–1.2 s. One client per repository, plus a parallel prefetch, would make it about 0.1–0.2 s. Also pass `aws_region`.
- [ ] **Backend names live in two places.** `ATHENA_BACKEND` and `DYNAMO_BACKEND` sit in `adapters/__init__.py`, while the defaults are in `config.py`. Put them in one place and validate them, as `AUTH_MODE` is, so a typo fails instead of silently falling back.

## Open decisions (Patrick)
- [ ] **Replace the retriever's model call with a fixed lookup.** The model only maps a lead kind to tools. Saves 1–3 s per retrieve, up to about 18 s per ask.
- [ ] **Delete the root guard tests that police layout** (about 250 lines), keeping the import, single-character-name and inline-prompt checks.

Related: [[Build order]], [[Open follow-ups]]
