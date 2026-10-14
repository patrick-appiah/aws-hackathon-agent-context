---
tags: [build, spec, area/architecture]
id: A4a
owner: Abdul
status: awaiting review
updated: 2026-10-14
---
# A4a: target architecture diagram v2 (spec)
> **Split of A4.** A4a (this note): `docs/architecture-target-v2.png`. [[A4b - HANDOFF and DEMO lines - spec]]: the `HANDOFF.md` and `DEMO.md` lines. [[A4c - Prompt wording review - spec]]: the prompt wording review. No Python: draw.io (diagrams.net) or Excalidraw, then export a PNG.

## 0. Context: read the vault first
The team vault is the shared context space for this project: decisions, briefs, rules, the build order and the reasons behind them. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before you start, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Teammate target diagram v1 review]] (`04 Reference/`): what v1 got right and the **seven fixes** v2 must make. v1 is `04 Reference/Sources/architecture-target-v1.png` and `docs/architecture-target-v1.png` in the repo.
3. Repo `ARCHITECTURE.md` §3b (the target Mermaid diagram: **the reference**), §4 (how scope flows), §5 (services) and §6 (POC vs target, with the roadmap phase per component).
4. [[Roadmap]] (`04 Reference/`, synced from `docs/ROADMAP.md`): Phase 0 = the POC, Phases 1–3.
5. [[Abdul - evals, Cognito, docs]] §7 ("Target diagram v2"), [[Build order]] (A4 feeds B3, the architecture slides).
6. `01 Decisions/`: [[2026-10-13 Two architecture views, POC and target]], [[2026-10-13 POC plus one target slice, target as 90-day roadmap]], [[2026-10-13 Ask spine is Step Functions Express, publish is Standard]]. `04 Reference/`: [[Judging rubric]] 3.1 ("POC vs target diagram covering identity, data flow, integration, security controls").

**Whenever this spec is silent or unclear, look in the vault before guessing:** `04 Reference/`, `03 Sessions/`, `Open follow-ups.md` ("Teammate revises target diagram to v2 (7 fixes)"). If it's still unclear, stop and ask Patrick (he reviews the diagram). Never add a service that isn't in `ARCHITECTURE.md`.

## 1. Intent
**What:** one PNG, `docs/architecture-target-v2.png` *(new)*, plus its editable source `docs/architecture-target-v2.drawio` *(new)* (or `.excalidraw` *(new)*), drawing the **target** architecture of `ARCHITECTURE.md` §3b with the **roadmap phase on every box** (from §6), and making the seven fixes of the v1 review.

**Why:** criterion 3.1 needs a POC and a target diagram; the POC is Mermaid in §3, the target needs a readable picture for the slides (B3). v1 mixed POC and target and made every answer wait for the delivery lead.

**Success means:**
- The PNG shows every box in §3 below, each with its phase badge, and every arrow in §4 below.
- Patrick has reviewed it and said OK in the PR.
- `ARCHITECTURE.md`'s line "v2 pending" is updated (Patrick's file; §5 below).

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Reference | `ARCHITECTURE.md` §3b Mermaid (v0.6), not v1 | Redrawing v1 with tweaks |
| Phase labels | A small badge in each box's top-right corner: `P0` (built in the POC), `P1`, `P2`, `P3` (roadmap phases, `ARCHITECTURE.md` §6 and `docs/ROADMAP.md`). A box that is built now and extended later shows both, for example `P0 + P1` | Colours only (unreadable in print and for colour-blind readers) |
| Legend | Bottom-left: `P0 = built in the hackathon POC · P1 = pilot, weeks 1–6 · P2 = production hardening, weeks 7–10 · P3 = scale and reuse, weeks 11–13` | No legend |
| Groups | The six §3b subgraphs as labelled containers: "Front end and access", "Data layer", "Read path 1 · dashboard, no model", "Read path 2 · ask, answers in seconds", "Write path · human-approved", "Cross-cutting" | One flat canvas |
| Names | Only names from `ARCHITECTURE.md` (§3b box text, §5 service names). No real company, system or person names | Vendor logos for Jira or Smartsheet (the box text names them as examples; logos imply an integration exists) |
| Tool | draw.io (diagrams.net, free, has AWS shapes: More Shapes → AWS 2025/AWS 19) or Excalidraw. Commit the source next to the PNG | PNG only (no one can edit it later) |
| Export | PNG, white background, 2× scale (draw.io: File → Export as → PNG, Zoom 200%, "Border width" 10, "Transparent background" off) | SVG only (the slides and the README need PNG) |

## 3. Boxes and their phase badges (all required)
| Container | Box text (from §3b) | Badge | Why that badge |
|---|---|---|---|
| (outside) | Users: CFO · sponsor · delivery lead · entity lead | none | |
| Front end and access | Portal · Angular on S3 + CloudFront | `P0` | §3 POC |
| Front end and access | Cognito: groups = roles; tenant + entity claims; **federation with the client's identity provider** | `P0 + P1` | §6 Identity: sign-in is POC, federation is phase 1 (fix: "Cognito is built in the POC") |
| Front end and access | API Gateway · JWT authorizer | `P0` | §3, §4 step 2 |
| Front end and access | Verified Permissions · Cedar: role · tenant · entity | `P1` | §6 Identity; v1 review fix 2 |
| Data layer | Sources: prod: project tool · defect tracker · migration-tool exports; demo: synthetic ERP-layer dataset (CSVs) | `P0 (synthetic) + P1 (real)` | §6 Data |
| Data layer | External data: close + holiday calendars · vendor support dates | `P0 (calendar) + P3 (vendor dates)` | §6 External data; v1 review fix 6 |
| Data layer | EventBridge schedule | `P1` | §6 Data |
| Data layer | Connector Lambdas · swappable | `P1` | §6 Data |
| Data layer | S3 data lake · `tenant=` / artefact / `entity=` | `P0 (one tenant) + P3 (many)` | §6 Data and Tenants |
| Data layer | Glue Data Catalog | `P1` | §6 Data |
| Data layer | Athena | `P1` | §6 Data |
| Data layer | Lake Formation · row filters by tenant + entity | `P2` | §6 Data-layer scope |
| Read path 1 | KPI Lambda · `tools/metrics.py` · one source of truth · scope-filtered | `P0` | §3 |
| Read path 2 | Step Functions Express · ask spine | `P0` | §3; fix 5 |
| Read path 2 | Budget left? (reads cost from the run ledger) → partial answer + reason | `P0` | §3; fix 3 |
| Read path 2 | Orchestrator · AgentCore + Strands · **the one planning agent** | `P0` | §3; fix 5 |
| Read path 2 | Retriever · scoped SQL tools | `P0 + P1 (SQL on Athena)` | §3 (scoped tools), §3b (SQL tool) |
| Read path 2 | Blocker-analyst · KPI tool | `P0` | §3 |
| Read path 2 | Run ledger · DynamoDB: claims · evidence · verdicts · attempts · tokens · cost · user + scope | `P0` | §3 |
| Read path 2 | Citation pre-check · code | `P0` | §3 |
| Read path 2 | Critic · judges blind · **claim + cited rows only** | `P0` | §3; fix 7 |
| Read path 2 | Retry guard · **Choice state** | `P0` | §3; fix 5 |
| Read path 2 | Rejected records · shown as "could not verify" | `P0` | §3; fix 7 |
| Read path 2 | Writer · cited answer | `P0` | §3 |
| Write path | Step Functions Standard | `P0` | §3; fix 5 |
| Write path | Delivery lead approves · `waitForTaskToken` | `P0` | §3; fix 5 |
| Write path | S3 `status-packs/` | `P0` | §3 |
| Cross-cutting | Bedrock Guardrails · PII + prompt-attack filters | `P0` | §3 |
| Cross-cutting | CloudWatch + AgentCore Observability | `P0 + P2 (dashboards, alarms)` | §6 Audit and monitoring |
| Cross-cutting | CloudTrail · who saw what | `P2` | §6; fix 2 |
| Cross-cutting | SSM Parameter Store · fallback switches | `P0` | §5 |
| Cross-cutting | Evals in CI (a score drop blocks the release) | `P2` | §6 Agents row "plus evals in CI"; `docs/ROADMAP.md` Phase 2 |
| (a note box) | Multi-tenant onboarding: new `tenant=` prefix + connector config + users, no code changes | `P3` | §6 Tenants; fix 2 |

## 4. Arrows (all required; labels as written)
- Users → Portal; Portal → Cognito "sign in"; Portal → API Gateway "JWT"; API Gateway → Verified Permissions "allowed?".
- Sources → Connector Lambdas; External data → Connector Lambdas; EventBridge → Connector Lambdas; Connector Lambdas → S3 data lake → Glue → Athena; Lake Formation ⇢ Athena "governs" (dashed).
- API Gateway → KPI Lambda "GET /summary · scope"; KPI Lambda → Athena.
- API Gateway → Step Functions Express "POST /ask · scope" → Budget left?; Budget "no" → partial answer + reason; Budget "yes" → Orchestrator.
- Orchestrator → Retriever → Athena "SQL tool"; Orchestrator → Blocker-analyst → KPI Lambda "KPI tool".
- Retriever → Run ledger; Blocker-analyst → Run ledger; Run ledger → Citation pre-check.
- Pre-check "rows exist" → Critic; Pre-check "missing rows" → Retry guard.
- Critic "pass" → Writer; Critic "reject" → Retry guard; **Run ledger ⇢ Retry guard "attempt count"** (dashed; fix 4).
- Retry guard "attempts under 2" → Orchestrator; Retry guard "limit reached" → Rejected records.
- Writer → Portal "answer + citations" (**straight to the portal, no approval**; fix 1); Rejected records → Portal.
- Portal → Step Functions Standard "POST /publish" → Delivery lead approves; "sent back" → Orchestrator; "approved" → S3 `status-packs/`.
- Guardrails ⇢ Orchestrator, Retriever, Blocker-analyst, Critic, Writer "on every model call" (dashed).

## 5. The `ARCHITECTURE.md` line (Patrick's file; change only with his OK in the PR)
Replace `The teammate's visual of the same design: \`docs/architecture-target-v1.png\` (v2 pending, to match this diagram).` with `The visual of the same design, with the roadmap phase on every box: \`docs/architecture-target-v2.png\` (source \`docs/architecture-target-v2.drawio\`). v1 is kept for history: \`docs/architecture-target-v1.png\`.`

## 6. Tests
No code. The checks:
- **Box and arrow audit:** a second person ticks every row of §3 and every bullet of §4 against the PNG.
- **Readable:** at 100 % on a laptop screen, every box text and badge is legible; printed on A4 landscape, so are the badges.
- **Patrick's review:** an "Approve" or written OK on the PR.
- **Doc guards** (only if the `ARCHITECTURE.md` line is in the PR): Linus runs `uv run --locked pytest` → the baseline count, 0 failed.

## 7. Out of scope
- The POC diagram (Mermaid, `ARCHITECTURE.md` §3), the slides (B3), `docs/ROADMAP.md` (L7).
- Any service not in `ARCHITECTURE.md` §3b or §5.

Related: [[Build order]], [[Abdul - evals, Cognito, docs]], [[A4a - Target architecture diagram v2 - plan]]
