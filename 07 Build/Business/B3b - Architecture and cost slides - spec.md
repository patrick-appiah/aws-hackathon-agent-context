---
tags: [build, spec, area/business]
id: B3b
owner: Patrick + Michael
status: awaiting review
updated: 2026-10-14
---
# B3b: The architecture slides and the cost + 90-day-plan slide (spec)
> **Two required submissions of the 9 Oct proposal:** "architecture diagram: POC + target, 1–2 slides" (judged on 3.1) and "cost estimate + 90-day plan with top-3 risks, 1 slide" (3.2, 3.3). B3b makes them as a three-slide companion to the deck, `business/submission-slides.pptx` *(new)* and `.pdf` *(new)*, in the deck's look. Part of B3, split in three (B3a value case, **B3b** these slides, B3c pitch and Q&A). Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop`.

## 0. Context: read the vault first
The team vault is the shared context space. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before building the slides, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Workstreams]] and [[Business case and pitch]] (the brief: "the POC and target architecture as 1–2 slides; a cost and 90-day-plan slide").
3. [[Judging rubric]]: required submissions; descriptors 3.1 (POC vs target diagram: identity, data flow, integration, security controls, Well-Architected trade-offs), 3.2 (monthly run cost at pilot and full scale, cost levers, monitoring), 3.3 (phased plan, team, customer dependencies, top-3 risks with mitigations, go/no-go).
4. [[2026-10-13 Two architecture views, POC and target]], [[2026-10-13 POC plus one target slice, target as 90-day roadmap]] (D-015), [[Teammate target diagram v1 review]] (what v2 must fix).
5. [[B2 - Pitch deck - spec]] (the look, the evidence-line convention, the Cognito wording).
6. [[Abdul - evals, Cognito, docs]] (A3 `COST.md`, A4 `docs/architecture-target-v2.png` *(new)*, created by A4a), [[Linus - API, identity, blocker-analyst]] (L7 `docs/ROADMAP.md`).
7. Repo: `ARCHITECTURE.md` §3, §3b, §6, §7, §8; `COST.md`; `docs/ROADMAP.md`; `HANDOFF.md`.

**Whenever this spec is silent or unclear, look in the vault before guessing** (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`). If it's still unclear, stop and ask Patrick.

## 1. Intent
**What:** three slides in `business/submission-slides.pptx` *(new)*, exported to `business/submission-slides.pdf` *(new)*:
- **A1, the POC architecture** (what is built): the `ARCHITECTURE.md` §3 diagram rendered as an image, with a side panel of the security controls and the "Cognito slice" note.
- **A2, the target architecture** (90 days): Abdul's `docs/architecture-target-v2.png`, with the roadmap phase on each target layer and a small POC-vs-target table from `ARCHITECTURE.md` §6.
- **A3, cost and the 90-day plan**: the measured cost per question and at pilot and full scale, the cost levers, the three phases with their go/no-go, the team, the client dependencies, and the top-3 risks with their stop conditions.

**Why:** the judges score 3.1–3.3 from exactly these sheets, and the rule of evidence caps a claim that isn't shown. The deck's slide 7 is a summary; these are the full views. Keeping them in a separate file keeps the deck at its 10 slides (B2).

**Success means:**
- The pptx has 3 slides; the PDF has 3 pages and was exported after the pptx.
- A1 shows the POC diagram and labels nothing from §3b's target-only layers as built.
- A2 shows the v2 target diagram (or, if A4 isn't ready, the §3b Mermaid render labelled as such), with phase tags 1, 2 and 3.
- A3's cost figures equal `COST.md`; its phases, go/no-go lines, team, dependencies and risks equal `docs/ROADMAP.md`.
- Every slide has an evidence line naming its sources.

**Assumptions:**
- **B2 is merged**, so `business/pitch-deck.pptx` holds the final look to copy.
- **A4:** `docs/architecture-target-v2.png` exists on `develop` by D2 15:00 (the name in Abdul's brief). If not, A2 uses the §3b render (§2).
- **A3/H5:** `COST.md`'s "Per question" table rows (Sonnet, Haiku/Nova, AgentCore, Lambda/…, **Total**), "Scale" rows (**Pilot**, **Full**) and the "Measured on" line are filled. The per-question figure on A3 is the "Measured on" **average** (the team's one cost per question, as on business case line 34 and deck slide 9); the Total row is labelled "Q01 worked example" and is not quoted.
- **L7:** `docs/ROADMAP.md` keeps today's headings: the three phases with "Go / no-go at week 6 / 10 / 13 (proposed)", "Team (proposed)", "What we need from the client", "Top 3 risks" (columns Risk, Effect, Mitigation, Stop if).

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Where the slides live | `business/submission-slides.pptx` + `.pdf` *(new)*, made by copying `business/pitch-deck.pptx` and keeping one slide as the template | Appendix slides in the deck (breaks B2's 10-slide count); slides in `docs/` (another workstream's folder) |
| The POC diagram | Rendered from the `ARCHITECTURE.md` §3 Mermaid code at mermaid.live (Actions → PNG), so it is exactly the documented design | Redrawing it by hand (drifts from the doc) |
| The target diagram | Abdul's v2 PNG. Fallback: the §3b Mermaid render, with the evidence line `Rendered from ARCHITECTURE.md §3b; v2 visual pending` | The v1 PNG (superseded: [[Teammate target diagram v1 review]] lists seven fixes) |
| Phase tags on A2 | Rounded labels on the diagram from `ARCHITECTURE.md` §6: Verified Permissions and connectors + EventBridge + Glue/Athena = Phase 1; Lake Formation and CloudTrail = Phase 2; multi-tenant onboarding = Phase 3; Cognito = "built (POC)" or "Phase 1" after a no-go | No tags (the reviewer can't tell built from planned) |
| Cost numbers | Copied from `COST.md`, labelled *measured*, with its date. A row still `TODO` at 15:00 shows `not measured` in words | An estimate in place of a measured figure |
| Cognito on A1 | As B2 slide 7: built only after a **go** at D2 12:00 | Showing it as built regardless |

## 3. The slides: exact content
Same layout conventions as B2: kicker, title, body, evidence line (small grey, bottom left), footer `ERP Migration Progress Portal · Team Cloud 9` and slide number `A1`–`A3`.

**A1: the POC architecture**
- Kicker: `ARCHITECTURE: THE POC (BUILT IN TWO DAYS)`
- Title: `One screen from code, one agent loop on a Step Functions spine`
- Left (about 70% width): the §3 diagram PNG.
- Right panel `Controls in the POC`:
  - `Scope from the sign-in token, never the browser; checked in every tool`
  - `Agents are read-only; the only write waits for the delivery lead (waitForTaskToken)`
  - `Retry limit read from the run ledger, not the critic`
  - `Budget ceiling of $0.50 per question`
  - `Bedrock Guardrails on every model call; artefact text is data`
  - `eu-west-1 only; eu.* inference profiles only`
  - Cognito line: `Cognito sign-in with role and entity scope: the one target layer built (D-015)` **or** `Cognito: no-go at D2 12:00; the demo runs as a CFO demo user (AUTH_MODE=none)`
- Evidence: `ARCHITECTURE.md §2 (flows vs agents), §3 (this diagram), §7 (security controls); DECISIONS.md D-002, D-007, D-015. Data: synthetic CSVs in S3.`

**A2: the target architecture**
- Kicker: `ARCHITECTURE: THE 90-DAY TARGET`
- Title: `The same loop, with live data, policy-based access and a second line of scope`
- Left (about 70%): the v2 PNG (or the §3b render), with phase tags.
- Right panel, a small table `POC → target`, five rows from `ARCHITECTURE.md` §6: Identity (Cognito → + IdP federation, Verified Permissions, Phase 1); Data (synthetic CSVs → connectors + EventBridge, Glue + Athena, Phase 1); Data-layer scope (code filter → + Lake Formation row filters, Phase 2); Audit (CloudWatch + AgentCore Observability → + CloudTrail data events, Phase 2); Tenants (one → many, onboarding = prefix + connector config + users, Phase 3).
- Strip: `Well-Architected trade-off: more layers of defence mean more moving parts, so each target layer arrives behind a switch, one phase at a time.`
- Evidence: `ARCHITECTURE.md §3b, §6, §8; docs/architecture-target-v2.png (Abdul); docs/ROADMAP.md.`

**A3: cost and the 90-day plan**
- Kicker: `COST AND THE 90-DAY PLAN`
- Title: `$<cost per question> per question measured; three phases, each with a stop condition`
- Left third `Cost (measured, COST.md, <date>)`:
  - a table: `Per question (average)` = `$<"Measured on" average>`; `Pilot, ~200 questions a month` = `$<Pilot>`; `100 questions a day` = `$<Full>`; `Dashboard loads` = `no model calls`
  - `Levers:` the four bullets of `COST.md` "Cost levers", shortened to one line each.
- Middle third `90 days (docs/ROADMAP.md)`: three stacked bars:
  - `Weeks 1–6 · Pilot` / `real data, real users, 40-question eval set` / `Go if: ≥ 85 % right with citations; zero out-of-scope answers; two packs approved; cost within estimate`
  - `Weeks 7–10 · Hardening` / `Lake Formation, CloudTrail, evals in CI, runbook` / `Go if: security review passes; evals hold for two weeks; no Sev-1`
  - `Weeks 11–13 · Reuse` / `second portfolio company as a tenant` / `Go if: live in 5 working days; sees none of the first tenant's data`
  - under it: `Team: 3 engineers + part-time delivery lead (weeks 1–6); 2 engineers + part-time platform/security engineer (weeks 7–13). From the client: a sponsor and a product owner; read access to the project tool, defect tracker and reconciliation outputs; IdP federation; a security reviewer in weeks 6–9; the finance calendars.`
- Right third `Top 3 risks`: the `docs/ROADMAP.md` table, three rows, columns Risk / Mitigation / Stop if (drop the Effect column to fit).
- Evidence: `Measured: COST.md (<date>). Plan, team, dependencies, risks: docs/ROADMAP.md; all go / no-go thresholds proposed, to confirm with the problem owner.`

## 4. Checks
- `unzip -l business/submission-slides.pptx | grep -c -E 'ppt/slides/slide[0-9]+\.xml$'` → `3`.
- Text per slide: `for number in 1 2 3; do printf 'slide %s: ' "$number"; unzip -p business/submission-slides.pptx "ppt/slides/slide${number}.xml" | sed 's/<[^>]*>/ /g' | tr -s ' ' | cut -c1-200; echo; done`.
- Required strings: slide 1 `ARCHITECTURE.md §3`; slide 2 `Phase 1`, `Phase 2`, `Phase 3`; slide 3 `COST.md`, `ROADMAP`, `Stop if`.
- Each slide's extracted text: `grep -c 'TBC\|TODO\|&lt;'` → `0`.
- A3's dollar figures each appear in `COST.md` (`grep -c -F '<figure>' COST.md` ≥ 1).
- The PDF: 3 pages; its commit timestamp ≥ the pptx's.

## 5. Out of scope
- Drawing or fixing the target diagram (A4, Abdul) or changing `ARCHITECTURE.md` (Patrick) or `COST.md`/`docs/ROADMAP.md` (A3, L7). Report mismatches to their owners.
- The deck (B2), the value case (B3a), the pitch (B3c).

Related: [[Build order]], [[Business case and pitch]], [[B3b - Architecture and cost slides - plan]]
