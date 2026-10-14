---
tags: [build, spec, area/business]
id: B3a
owner: Patrick + Michael
status: awaiting review
updated: 2026-10-14
---
# B3a: The one-page value case (spec)
> **A required submission of the 9 Oct proposal** ("one-page value case: problem, owner, KPIs with baseline and target, ROI assumptions"), derived from `business/business-case.md`. B3 is split in three (the lead's rule): **B3a** this page, **B3b** the architecture and cost/90-day slides, **B3c** the pitch script and Q&A. Repo: `Amali-Tech/cloud-9-hackathon`, branch from `develop`.

## 0. Context: read the vault first
The team vault is the shared context space. Clone it from `git@github.com:patrick-appiah/aws-hackathon-agent-context.git` (lead's machine: `/mnt/c/dev/aws-hackathon/aws-hackathon/`) and run `git pull` first. **Before writing, read, in this order:**
1. [[How to execute a plan]] (`07 Build/`).
2. [[Workstreams]] (rules, §7) and [[Business case and pitch]] (the brief: "the one-page value case from the business case").
3. [[Judging rubric]]: the required submissions table and the level-4 descriptors 1.1 (owner and pain, validated during the event), 1.2 (baseline vs target on 1–2 KPIs, stated assumptions, payback) and 1.3 (pilot scope, users, duration, sponsor, change management, sign-off). [[Pitch track grading rubric]] (business case items).
4. [[B1 - Business case figures and validation - spec]]: **every figure on this page comes from the business case B1 finishes.**
5. [[2026-10-13 POC plus one target slice, target as 90-day roadmap]] (D-015), [[Graders are AI and read only what is written]].

**Whenever this spec is silent or unclear, look in the vault before guessing** (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`). If it's still unclear, stop and ask Patrick.

## 1. Intent
**What:** `business/value-case.md` *(new)* and its one-page export `business/value-case.pdf` *(new)*: who owns the problem, the pain, two headline KPIs with baseline and target, the ROI with every assumption, reuse, and the next engagement.

**Why:** the organisers asked for it as a separate one-pager, and the judges' 1.1–1.3 descriptors are exactly its sections. It also gives the presenter one sheet to hand over. A one-pager that disagrees with the business case is worse than none, so it holds **no figure of its own**: each one is copied from `business/business-case.md` with the same label.

**Success means:**
- `business/value-case.md` exists with the seven sections in §3, in that order.
- Every figure in it appears in `business/business-case.md` (or `docs/ROADMAP.md` for the pilot facts) with the same label.
- `business/value-case.pdf` is exactly **one page** (A4 portrait) and contains no `TBC` or `<`.
- `uv run --locked pytest` passes with the start count (the guards read every tracked `.md`).

**Assumptions:**
- **B1 is merged** before B3a's Task 2 (the figures are final). If it isn't by D2 14:45, B3a uses B1's open branch `docs/business-case-measured` and re-checks after B1 merges.
- `docs/ROADMAP.md` (L7) keeps its "Phase 1: pilot", "Go / no-go at week 6", "Team (proposed)" and "What we need from the client" sections.

## 2. Decisions
| Question | Decision | Rejected |
|---|---|---|
| Format | Markdown in the repo + a PDF export, like the business case and product spec | A slide (the organisers asked for a page); a Word file (not diffable) |
| Figures | Copied from the business case, never recomputed here; a figure that changes there changes here in the same PR | Separate rounding or "simplified" figures |
| Headline KPIs | Two, as 1.2 asks: **time to answer a status question** and **monthly status-pack effort**; cost per question and the picture's age as supporting rows | Five KPIs (the dashboard's KPIs are about the migration, not the value) |
| Next engagement | The ROADMAP pilot: 6 weeks, one programme, named roles, the week-6 go/no-go as the sign-off | A generic "next steps" list |
| Length | One A4 page at 10–11 pt. If it overflows, shorten the problem and reuse sections first, never the assumptions | Two pages (not what was asked) |

## 3. The page: `business/value-case.md` *(new)*
Exactly this content. `<…>` slots are copied from the named line of `business/business-case.md` (B1 numbering, found by its text), keeping that line's label.

```markdown
# One-page value case: ERP Migration Progress Portal

> Every figure is from `business/business-case.md`, where each assumption is stated in full. *(brief)*: the problem statement. *(validated)*: confirmed by the problem owner. *Measured*: from runs of the POC. *Proposed*: our assumption, with who confirms it.

## Who
| | |
|---|---|
| **Executive whose week gets better** | The **CFO** funding the ERP consolidation, with the **programme sponsor** |
| **Daily user** | The **delivery lead**, who builds the monthly status pack today |
| **Problem owner** | Vanessa Addo (AmaliTech Ventures, ERP modernisation track); oversight: Joseph Akayesi |
| **Validated** | <business case line 23: the date, and the quote if there is one; or "not yet: requested for <date>"> |

## The problem
A mid-market industrial group consolidates several ERPs onto one platform over about 18 months *(brief)*. Progress reaches the CFO as a hand-built monthly steering deck, up to four weeks old *(brief)*. Each "are we on track, what is blocked?" costs a consultant two days *(brief)*.

## KPIs: baseline and target
| KPI | Baseline today | With the portal |
|---|---|---|
| **Time to answer a status question** | 2 consultant-days *(brief)* | <business case line 31, third cell> |
| **Effort to produce the monthly status pack** | <sizing row "Days to rebuild the status pack": value and label> | 0.5 day to review and approve *(proposed)* |
| Cost per answered question | $2,000 (2 days × $1,000) | <business case line 34, third cell> |
| Age of the CFO's picture | Up to 4 weeks *(brief)* | Same day: recalculated from the artefacts |

## ROI, with every assumption
| | Value | Basis |
|---|---|---|
| Consultant days saved per month | <"Consultant days saved per month" figure> | 6 questions × 2 days + 3 pack days − 0.5 review day |
| Value per month | <"Value per month" figure> | × $1,000 blended day rate *(proposed; delivery to confirm)* |
| Portal run cost per month | <line 46 figure> | <line 46 label and basis, shortened to one clause> |
| **Net value per month** | <"Net value per month" figure> | value − run cost |
| Pilot cost | <"Payback" line: pilot cost> | 3 engineers × 30 days + a half-time delivery lead × 30 days *(proposed)* |
| **Payback** | <"Payback" line: months> | pilot cost ÷ net value per month |
| Value over one programme | <"Value over one programme" figure> | × 18 months *(brief)* |

## Reuse across portfolio companies
The six artefacts, the KPI definitions, the agent loop and the security model are the same in every ERP migration. A new company is configuration, not code: a tenant prefix, a connector configuration and its users (`ARCHITECTURE.md` §4), about 5 days to onboard *(proposed)*. <business case line 79, as one sentence>

## The next engagement: a 6-week pilot
| | |
|---|---|
| **Scope** | One portfolio company, one programme: live connectors, real users, the monthly status pack generated and approved twice (`docs/ROADMAP.md` Phase 1) |
| **Sponsor and users** | The CFO or programme sponsor; the delivery lead as product owner; entity leads |
| **Team** | 3 engineers + a part-time delivery lead *(proposed)* |
| **Change** | The delivery lead co-writes the 40-question eval set and approves every published pack |
| **Signed off when** (week 6, *proposed*) | ≥ 85 % of the eval set right, with citations; zero answers outside the asker's scope; two packs approved with minor edits; cost per question within the `COST.md` estimate |
```

**Line-by-line sources** (for the reviewer): Who and Problem → business case §1; KPIs → business case §2 KPI table and sizing table; ROI → business case §2 bullet lines; Reuse → business case §3; pilot → `docs/ROADMAP.md` Phase 1, "Go / no-go at week 6", "Team (proposed)".

## 4. Checks
- `test -f business/value-case.md` and `grep -c '^## ' business/value-case.md` → `6` (Who, The problem, KPIs, ROI, Reuse, The next engagement).
- `grep -c 'TBC\|<' business/value-case.md` → `0`.
- For each dollar figure: `grep -o '\$[0-9]\+\(,[0-9]\{3\}\)*\(\.[0-9]\+\)\?' business/value-case.md | sort -u` lists figures that each appear in `business/business-case.md` (`grep -c -F '<figure>' business/business-case.md` ≥ 1), except `$2,000` and `$1,000`, which the business case has as `**$2,000**` and `$1,000`.
- `business/value-case.pdf`: one page when opened.
- `uv run --locked pytest`: the start count.

## 5. Out of scope
- New figures or analysis: B1 owns them.
- The deck (B2), the slides (B3b), the pitch (B3c).

Related: [[Build order]], [[Business case and pitch]], [[B3a - One-page value case - plan]]
