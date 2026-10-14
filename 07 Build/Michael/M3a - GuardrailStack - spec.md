---
tags: [build, spec, area/devops]
id: M3a
owner: Michael
status: ready
updated: 2026-10-14
---
# M3a: GuardrailStack, the Bedrock Guardrail on every model call (spec)
> **Split from M3** (the lead's rule: one item per agent session). M3a is the Guardrail; [[M3b - AuthStack - spec]] is Cognito. Each is deployable and mergeable on its own. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop` after [[M2 - App, DataStack and LedgerStack - spec]] is merged.

## 0. Context: read the vault first
The vault is the shared context space: decisions, briefs, rules, the build order and the reasons behind them. Clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing any code, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`): the procedure every agent follows.
2. [[Workstreams]] (`06 Workstreams/`): the architecture, the code already built, the contracts and the rules (§7).
3. [[Michael - DevOps]] (step 4, `GuardrailStack`) and [[Huvison - trust and flow]] §8 (the Guardrail settings are his).
4. [[M2 - App, DataStack and LedgerStack - spec]]: the CDK patterns this item follows (`build_stacks`, prefix, outputs, tests).
5. [[Build order]]: M3a depends on M2.
6. `01 Decisions/`: [[2026-10-13 Artefact text is untrusted, critic fails closed]], [[2026-10-13 EU-only Bedrock inference profiles]], [[2026-10-13 Team are admins, workload roles least-privilege]]; `05 Workflow/`: [[Deploy and demo checks]], [[Handling security findings]].

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/` for the brief, the rubrics and the guideline; `03 Sessions/` for what happened when; `Open follow-ups.md` for known open questions. If the vault doesn't answer it either, stop and ask Michael (owner) or Huvison (the settings). Never invent a name, a shape or a rule.

## 1. Intent
**What:** a `GuardrailStack` *(new)* with one Bedrock Guardrail and one published version:
1. **Prompt-attack filter** on input at `HIGH` (Bedrock requires `NONE` on output for this filter).
2. **PII filter:** credentials (`AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `PASSWORD`) **blocked** in both directions; `EMAIL`, `PHONE`, `NAME` **masked in answers only** (input off, output on), so the evidence rows the critic needs are never rewritten on the way in.
3. A **published version** (`AWS::Bedrock::GuardrailVersion`), so the Lambdas pin a number, not `DRAFT`.
4. **Outputs** `GuardrailId`, `GuardrailVersion`, `GuardrailArn` (for `GUARDRAIL_ID`, `GUARDRAIL_VERSION` in `config.py` and Yaw's IAM), and `apply_guardrail_statement()`: `bedrock:ApplyGuardrail` on this guardrail's ARN only.

**Why:**
- `ARCHITECTURE.md` §7: "The Guardrail's prompt-attack filter is on" is defence 2 of 5 against prompt injection; the planted probe `DEF-0462` is EVALS Q12.
- `agents/critic.py` already passes `guardrail_id` / `guardrail_version` to `BedrockModel` when `GUARDRAIL_ID` is set; it just needs a guardrail to exist.
- Hard gate 4 ("no real client data") and the security rules: a credential must never reach or leave a model.

**Success means:**
- `uv run --locked pytest` → **230 passed** (226 after M2 + 4 new), `TOTAL` 96%.
- `cd infra && npx cdk synth -q` succeeds with no AWS credentials and writes `GuardrailStack.template.json`.
- **Verify in AWS:** `aws bedrock-runtime apply-guardrail` with a prompt-attack string returns `GUARDRAIL_INTERVENED`; a plain portal question returns `NONE`; an e-mail address in an `OUTPUT` comes back masked.

**Assumptions** (reconcile with the named owner before the PR):
- **Huvison (H7 "Guardrail settings and ask latency")** confirms the filter set above. Until he writes his settings into `docs/DEVOPS_HANDOVER.md`, these are the proposal; they live as named constants in `infra/constants.py` *(new)* (`GUARDRAIL_*`), so a change is one line.
- **Huvison / Patrick:** with Strands `BedrockModel(guardrail_id=...)` the guardrail sees the whole conversation, including the `<evidence>` rows. If the prompt-attack filter blocks a run whose evidence contains `DEF-0462`, the critic fails closed and Q12 shows a rejection instead of a clean verdict. That is a flow decision (for example, tag only the user's question as guarded content), not a stack change. M3a ships the filter; Huvison checks Q12 against it.
- **Yaw (Y1–Y3)** reads `guardrail.guardrail_id`, `guardrail.guardrail_version` and `guardrail.apply_guardrail_statement()` from `PortalStacks.guardrail` (INTERFACES, [[Y1 - ApiStack - spec]]).

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Construct | `aws_bedrock.CfnGuardrail` + `CfnGuardrailVersion` (L1; no stable L2 in `aws-cdk-lib` 2.273) | The alpha `@aws-cdk/aws-bedrock-alpha` (an extra dependency, unstable API) |
| Where the settings live | Named constants in `infra/constants.py` under a "settings are Huvison's" comment | Inline literals in the stack (magic strings); `config.py` (runtime settings only; nothing reads these at runtime) |
| PII on input | Credentials blocked; personal details **not** filtered on input | Masking on input (would rewrite evidence rows and break the critic's recomputation); no PII filter (fails ARCHITECTURE §7) |
| PII on output | `EMAIL`, `PHONE`, `NAME` masked (`ANONYMIZE`), credentials blocked | Blocking every PII type on output (a whole answer lost for one name) |
| Version | Publish one version; a settings change also changes `GUARDRAIL_VERSION_DESCRIPTION`, which replaces the version resource (new number) | Pointing Lambdas at `DRAFT` (changes under running code) |
| Name | `<prefix>-erp-portal-guardrail` (guardrail names are unique per account) | A fixed name (the second copy for the clean-deploy check would collide) |
| Construct IDs | The version resource is `PublishedVersion`, because the output is already `GuardrailVersion` (two constructs can't share an ID; dry-run error: `There is already a Construct with name 'GuardrailVersion'`) | — |
| IAM helper | `apply_guardrail_statement()` returns `bedrock:ApplyGuardrail` on this ARN | `grant_*`-style helpers with wildcards |

## 3. Exact shapes
**`infra/constants.py` additions:**
| Constant | Value |
|---|---|
| `GUARDRAIL_BASE_NAME` | `"erp-portal-guardrail"` |
| `GUARDRAIL_PROMPT_ATTACK_STRENGTH` | `"HIGH"` |
| `GUARDRAIL_BLOCKED_PII_TYPES` | `("AWS_ACCESS_KEY", "AWS_SECRET_KEY", "PASSWORD")` |
| `GUARDRAIL_MASKED_PII_TYPES` | `("EMAIL", "PHONE", "NAME")` |
| `GUARDRAIL_BLOCKED_INPUT_MESSAGE` | `"This request was blocked by the portal's safety filter."` |
| `GUARDRAIL_BLOCKED_OUTPUT_MESSAGE` | `"The answer was blocked by the portal's safety filter."` |
| `GUARDRAIL_VERSION_DESCRIPTION` | `"v1: prompt attack HIGH on input; credentials blocked; email, phone, name masked"` |

**`infra/stacks/guardrail_stack.py` *(new)*:** `GuardrailStack(scope, construct_id, *, prefix: str, **kwargs)`.
- Attributes: `guardrail_id: str` (token, `attr_guardrail_id`), `guardrail_version: str` (token, the version resource's `attr_version`), `guardrail_arn: str`.
- Method: `apply_guardrail_statement() -> iam.PolicyStatement`.
- Outputs: `GuardrailId`, `GuardrailVersion`, `GuardrailArn`.

**`infra/app.py` *(new)*:** `PortalStacks.guardrail: GuardrailStack`, built third (after `ledger`), stack name `<prefix>-GuardrailStack`.

**Synthesised resources:** `AWS::Bedrock::Guardrail` (`Name`, `BlockedInputMessaging`, `BlockedOutputsMessaging`, `ContentPolicyConfig.FiltersConfig = [{Type: PROMPT_ATTACK, InputStrength: HIGH, OutputStrength: NONE}]`, `SensitiveInformationPolicyConfig.PiiEntitiesConfig` = three `{Type, Action: BLOCK}` then three `{Type, Action: ANONYMIZE, InputEnabled: false, OutputEnabled: true}`); `AWS::Bedrock::GuardrailVersion` (`GuardrailIdentifier`, `Description`).

## 4. Tests (`tests/infra/stacks/test_guardrail_stack.py` *(new)*, 4 tests)
- The prompt-attack filter is on for input at `HIGH`, output `NONE`, and the name carries the prefix (`test-erp-portal-guardrail`).
- The PII list is exactly the blocked credentials plus the output-only masked types.
- One version resource; the three outputs exist.
- `apply_guardrail_statement()` is exactly `bedrock:ApplyGuardrail` on this guardrail's ARN.
- `tests/infra/test_app.py` *(new)* (M2) covers the prefix and region of the new stack without edits.

## 5. Out of scope
- Setting `GUARDRAIL_ID` / `GUARDRAIL_VERSION` on Lambdas and runtimes (Yaw, Y1–Y3), and the per-agent `make_agent` wiring (Huvison H7, Patrick, Linus).
- Topic, word and contextual-grounding filters (not in the brief).
- Changing the critic or the flow to tag guarded content (Huvison, if Q12 needs it).

Related: [[M3a - GuardrailStack - plan]], [[Build order]], [[Michael - DevOps]]
