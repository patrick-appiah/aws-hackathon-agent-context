---
tags: [build, spec, area/agents, area/evals]
id: H9
owner: Huvison
status: ready
updated: 2026-10-15
---
# H9: the critic trusts code-checked figures, and a clean entity says "nothing is blocking" (spec)
> **Two eval failures with fixes in Huvison's files.** Q06 (and part of Q01) fail because the critic requires every figure to appear in a cited row, while figures come from metrics tools and code has already rechecked them (D-029). Q03 fails because a clean entity's answer says "No finding could be verified", which reads like a failure, not an all-clear. Also: the critic onto `bedrock_model` with nothing streamed, and its verdict validated with `Verdict`. Repo: `Amali-Tech/cloud-9-hackathon`, branch `feature/critic-figures-and-all-clear` from `develop` **after H8 merges** (both touch `infra/functions/steps.py`). The repo is the source of truth for code; the vault is the source of context.

## 0. Context: read the vault first
Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`. **Before writing any code, read, in this order:**
1. [[How to execute a plan]].
2. [[2026-10-15 Figures are verified by code and the critic judges rows]] (D-029): **the decision this item builds.**
3. [[2026-10-15]]: the first eval run (Q03, Q06 failures) and live run 4 (the critic's reasons).
4. [[Whole-code review 2026-10-14]], Huvison's section: "Critic verdicts aren't validated", "The critic copies `agent_support`".
5. [[H3 - Writer agent - spec]] (`verbatim_answer`, the headlines), [[H8 - Stored answer with budget gates and a claim cap - spec]] (`write_answer` after H8).
6. `01 Decisions/`: [[2026-10-13 Artefact text is untrusted, critic fails closed]] (D-009), [[2026-10-13 Metrics are code, only the blocker Q&A is agentic]]; the repo's `DECISIONS.md` D-029, `agents/prompts/` and `scripts/lock_prompts.py` (changing a prompt: TEAM_PLAN §6).

**Whenever this spec is silent or unclear, look in the vault before guessing.** If it doesn't answer, stop and ask Patrick.

## 1. Intent
### 1.1 Figures recomputed by code (D-029)
- `agents/critic.build_input` sends the claim **without** `figures`, and the figures in their own tag after the evidence: `<figures_recomputed_by_code>{name: value, ...}</figures_recomputed_by_code>` (`FIGURES_TAG`), escaped with `agent_support.tagged` like the other tags.
- `agents/prompts/critic.txt` → **v1.1.0** (MINOR, a rule changes): the rule "Every figure in the claim must appear in, or be directly computable from, the cited rows" becomes: "The values inside `<figures_recomputed_by_code>` were recomputed by code from the records; accept them as correct. Check that the statement uses each one as given. Any other number or date in the statement must appear in, or be directly computable from, the cited rows." The injection-defence lines stay. Run `uv run python scripts/lock_prompts.py`.
- **Why it's safe:** `validate_claim` (on the production path through `blocker_analyst.checked_claims`) recomputes every figure with its tool and drops a claim whose figure doesn't match, before the critic sees it. The tag only says what code already checked.

### 1.2 "Nothing is blocking" for a clean entity (Q03)
- In `infra/functions/steps.write_answer`: when the run has **no claims at all** in the ledger (none proposed, none rejected), the response isn't partial, and `metrics.open_blockers(repository, question.entity_id)` is empty, the answer is `Answer(headline=NOTHING_BLOCKING_HEADLINE.format(entity_id=...))` with no bullets, and no writer call.
- `NOTHING_BLOCKING_HEADLINE = "Nothing is blocking cutover for {entity_id} in the migration records"` (in `agents/writer.py`, next to the other headlines).
- Decided in code from the metrics, never by a model, so a model can't invent an all-clear. If claims were proposed and all rejected, the existing "No finding could be verified…" stays.

### 1.3 The critic's model and verdict
- `critic.make_agent` builds its model with `agent_support.bedrock_model(settings.critic_model_id)` and `callback_handler=None` (nothing streamed to stdout or the Lambda logs; live run 4's output began with the critic's raw reasoning). Delete the copied `ESCAPED_CHARACTERS`, `_as_data` and `_tagged`; use `agent_support.tagged`.
- `judge` validates the verdict with `Verdict.model_validate` (inside the fail-closed `try`), replacing `_is_valid_verdict`; any failure is a rejection (whole-code review: a malformed `missing_evidence` crashed `record_rejection`).

**Success means:**
- The critic's input has the figures only inside `<figures_recomputed_by_code>`; its prompt is v1.1.0 and locked.
- With a scripted critic, a claim whose figure is in that tag and whose rows support it passes (the critic logic is unchanged; the test checks the input).
- E1 (clean) through `run_spine` with a stub orchestrator returning no claims: the headline is "Nothing is blocking cutover for E1 in the migration records", no writer call. E4 with no claims: not that headline (E4 has open blockers).
- `critic.make_agent` has no callback handler and uses `bedrock_model`; a verdict with `missing_evidence: "x"` (a string) is a rejection, not a crash.
- `uv run --locked pytest` green, coverage ≥ 98%.
- **Live (Patrick's OK):** EVALS Q03 and Q06 pass on the next eval run.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| How the critic learns figures are checked | A separate tag after the evidence, figures removed from the claim | A note in the prompt only (the critic can't tell which numbers were checked); passing the tool output (the critic must stay tool-less and blind) |
| Who says "nothing is blocking" | Code, from `metrics.open_blockers` and an empty ledger | The writer model (could invent an all-clear); the analyst's empty reply alone (a model error also gives no claims) |
| Where | `steps.write_answer` | The writer (has no repository) |

## 3. Shapes
| Name | Where | Value |
|---|---|---|
| `FIGURES_TAG` | `agents/critic.py` | `"figures_recomputed_by_code"` |
| `NOTHING_BLOCKING_HEADLINE` | `agents/writer.py` | `"Nothing is blocking cutover for {entity_id} in the migration records"` |
| critic prompt | `agents/prompts/critic.txt` | v1.1.0 |

## 4. Tests (about 5, in the existing files)
- `tests/agents/test_critic.py`: the input has figures only in the figures tag (escaped); a string `missing_evidence` is a rejection; `make_agent` (with `settings_without_guardrail`) has no callback handler.
- `tests/agents/test_prompts.py`: the critic prompt is v1.1.0, keeps its injection defence and names the figures tag.
- `tests/infra/functions/test_spine.py`: E1 with no claims → the nothing-blocking headline and no writer call; E4 with no claims → not.

## 5. Out of scope
- The analyst's prompt (one blocker per claim, figures for every computed number): Linus.
- Budget checks and the stored answer: H8.
- Q05 (D-030, the eval runner): Linus with Abdul.

Related: [[Build order]], [[H9 - Critic figures and the nothing-blocking answer - plan]]
