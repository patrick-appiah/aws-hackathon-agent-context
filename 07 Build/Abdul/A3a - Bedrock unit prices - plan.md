---
tags: [build, plan, area/cost]
id: A3a
owner: Abdul
spec: "[[A3a - Bedrock unit prices - spec]]"
status: ready
updated: 2026-10-14
---
# A3a: Bedrock eu-west-1 unit prices for COST.md (implementation plan)

> **For the executing agent (and Abdul):** follow [[How to execute a plan]] exactly, with one change: **Abdul does not run Python, uv or pytest.** Where a command is needed, ask Linus to run it and send you the output, and compare it with `Expected:`. Work the tasks in order. If anything differs from `Expected:`, stop and follow "When output doesn't match".

## 0. Context: read the vault first
The vault is the context space for this work (clone `git@github.com:patrick-appiah/aws-hackathon-agent-context.git`, then `git pull`). Read before Task 1:
1. [[How to execute a plan]].
2. [[A3a - Bedrock unit prices - spec]]: **the authority.** Where this plan and the spec disagree, the spec wins; record the conflict in your ledger.
3. [[Abdul - evals, Cognito, docs]] §6 and [[Huvison - trust and flow]] §6.
4. [[2026-10-13 Default models]] and [[2026-10-13 EU-only Bedrock inference profiles]].
5. [[C2 - Repo layout - spec]]: where every file goes (no `api/`, `auth/`, `flow/`).

When something here is unclear, look in the vault (`04 Reference/`, `03 Sessions/`, `Open follow-ups.md`) before guessing. If it's still unclear, stop and ask Huvison or Patrick.

**Goal:** `COST.md` has sourced, dated eu-west-1 unit prices for every model ID in `config.py` (plus Haiku 4.5 and AgentCore Runtime), and Huvison has them for the price table in code.

**Architecture:** prices → `COST.md` "Unit prices" (you) → `tools/constants.py` `MODEL_PRICES_USD_PER_1K_TOKENS` (Huvison, H5) → `tools/cost.py` *(new)* (created by H5) `cost_usd(usage)` → `AskResponse.cost_usd` → the results file → [[A3b - COST measured figures - plan]].

**Tech stack:** a browser (AWS pricing pages; the AWS console read-only for the Haiku profile ID), a calculator, VS Code + Git.

## Global Constraints
- **Repo:** `~/amalitech/aws-hackathon/erp-migration-portal`. Branch: `docs/bedrock-prices` from an up-to-date `develop`.
- **Start state:** `develop` has C1 merged; Linus's `uv run --locked pytest` → **`204 passed`**, 96% (or higher once more items merge: that's your baseline). `COST.md` has `## Per question`, `## Scale`, `## Cost levers`, `## Value side`, and every price cell says `TODO`. `config.py` has `DEFAULT_REASONING_MODEL = "eu.anthropic.claude-sonnet-4-6"` and `DEFAULT_RETRIEVAL_MODEL = "eu.amazon.nova-lite-v1:0"`.
- **Your ledger:** `.superpowers/ledger-A3a.md` (gitignored).
- **Rules:**
  - Prices only from the AWS pages named in the spec, for **Europe (Ireland)**. Never from memory or another region.
  - Copy model IDs exactly (`eu.amazon.nova-lite-v1:0` has a colon and a zero).
  - AWS console **read-only**.
  - Markdown guard tests: no bare `` `pytest` ``, no `uv run pytest`, no `python scripts/…` without `uv run `, test files only by `tests/…` path.
  - Commits: the messages given; **no `Co-Authored-By` and no "Generated with" lines.** Never push to `develop` or `main`; PR to `develop`; Linus reviews; Patrick merges.

## Review Focus (what nothing tests; check by hand at the end)
1. Every per-1K number is the page's per-1M number divided by 1,000 (move the decimal point three places left), not divided by 100 or 1,000,000.
2. The row used is the **EU / geo cross-region** one, not "Global".
3. Input and output aren't swapped (output is the larger number for every model).
4. Haiku 4.5's row says "not in `config.py` yet", so nobody thinks it's in use.
5. The date on every row is the day you read the page.

---

### Task 1: Read the Bedrock prices (D1, by 16:00)

**Files:** none (notes in the ledger).
**Produces:** six numbers and three row labels. **Consumes:** the pricing page.

- [ ] **Step 1: Start the ledger.**
```bash
cd ~/amalitech/aws-hackathon/erp-migration-portal && git switch develop && git pull
mkdir -p .superpowers && printf '# Ledger: A3a Bedrock prices\n' > .superpowers/ledger-A3a.md
```
Expected: `Already up to date.` or a pull summary; the ledger file exists.

- [ ] **Step 2: Open the page.** Browser → `https://aws.amazon.com/bedrock/pricing/`. Scroll to the provider tabs/sections ("Anthropic", "Amazon").
Expected: price tables per model; a region selector above them (or one table per region). Choose **Europe (Ireland)**.

- [ ] **Step 3: Claude Sonnet 4.6.** In the Anthropic section, find "Claude Sonnet 4.6". Find the on-demand **input** and **output** price per 1M tokens for Europe (Ireland), on the row for EU / geo cross-region inference (labelled like "Geo Cross-region inference and in-region"; never "Global"). If there's a separate "long context" price, use the standard one.
Expected: two dollar amounts per 1M tokens, output larger than input. Write in the ledger: `Sonnet 4.6: in $<x>/1M, out $<y>/1M, row "<label>"`.

- [ ] **Step 4: Nova Lite.** In the Amazon section, "Amazon Nova" → understanding models → "Nova Lite", Europe (Ireland), the geo / in-region row.
Expected: two amounts per 1M, output larger than input, both much smaller than Sonnet's. Ledger line `Nova Lite: in $<x>/1M, out $<y>/1M, row "<label>"`.

- [ ] **Step 5: Haiku 4.5.** Anthropic section → "Claude Haiku 4.5", same rules. Then the profile ID: AWS console, region eu-west-1 → Amazon Bedrock → "Cross-region inference" (Inference profiles) → find Claude Haiku 4.5's **EU** profile and copy its ID (it starts `eu.anthropic.claude-haiku-4-5`). Read only; don't request access or change anything.
Expected: two amounts per 1M (between Nova Lite's and Sonnet's), and a profile ID starting `eu.anthropic.claude-haiku-4-5`. Ledger line. If the console doesn't show the profile, write "profile ID: not visible in the console on <date>".

- [ ] **Step 6: Convert to per 1K.** For each of the six amounts, divide by 1,000 (example: `$3.00` per 1M = `0.003` per 1K; `$0.06` per 1M = `0.00006` per 1K). Write them next to the per-1M figures.
Expected: six per-1K numbers; each equals its per-1M figure with the decimal point moved three places left.

**Task done when:**
- the ledger has, for Sonnet 4.6, Nova Lite and Haiku 4.5, input and output per 1M and per 1K, the row label, and today's date;
- the Haiku EU profile ID (or "not visible") is in the ledger.

### Task 2: Read the AgentCore Runtime price (D1, by 16:30)

**Files:** none.
**Produces:** two numbers and a label.

- [ ] **Step 1:** Browser → `https://aws.amazon.com/bedrock/agentcore/pricing/` → "Runtime". Select Europe (Ireland) if the page has a region selector.
Expected: a CPU price "per vCPU-hour" and a memory price "per GB-hour". The page may list several runtime generations (for example "v1" and "v2", "consumption" and "committed baseline").

- [ ] **Step 2: Pick the row.** Ask Yaw (owner of AgentStack, Y3): *"Which AgentCore Runtime generation and billing (for example v2 consumption) does AgentStack deploy?"* Use that row; if he hasn't decided, use the consumption (pay-per-use) row of the newest generation and write "assumed: <row>" in the label.
Expected: one vCPU-hour price and one GB-hour price with the row label. Ledger line `AgentCore Runtime: $<x> per vCPU-hour, $<y> per GB-hour, row "<label>", region <Europe (Ireland) / the page shows no region>`.

**Task done when:**
- the ledger has both AgentCore prices, the row label and whether the page was regional.

### Task 3: Write the prices into `COST.md` (D1, by 17:30)

**Files:** Modify `COST.md`.
**Produces:** the "Unit prices" section and three cells of the per-question table.

- [ ] **Step 1: Branch.**
```bash
git switch -c docs/bedrock-prices
```
Expected: `Switched to a new branch 'docs/bedrock-prices'`.

- [ ] **Step 2: Insert the section.** Open `COST.md`. After the line starting `> **Measured, not guessed.**` and the blank line under it, paste the whole block from spec §3 (1), from `## Unit prices (on-demand, eu-west-1)` to the AgentCore row, followed by a blank line. Then replace every `<…>` with your ledger values: the date as `2026-10-14` style, prices as plain numbers (`0.003`), labels as the page shows them, the Haiku profile ID.
Expected: Ctrl+F `<` in `COST.md` finds **nothing** in the new section; the preview (Ctrl+Shift+V) shows a 4-row table between the intro and "Per question", every row with a clickable link.

- [ ] **Step 3: Fill the three cells** in `## Per question`, column "Unit price (eu-west-1)", using spec §3 (2):
  - `Bedrock: Sonnet (orchestrator, analyst, critic, writer)` row: `$<in> in / $<out> out per 1K tokens`.
  - `Bedrock: Haiku / Nova (retriever)` row: `Nova Lite: $<in> in / $<out> out per 1K tokens`.
  - `AgentCore Runtime` row: `$<x> per vCPU-hour + $<y> per GB-hour`.
  Leave the "Units / question" and "Cost / question" cells as `TODO` (they're A3b).
Expected: the preview shows the row "Bedrock: Sonnet …" with a unit price, "Haiku / Nova" with Nova Lite's, "AgentCore Runtime" with both runtime prices; the other cells unchanged.

- [ ] **Step 4: Commit and push.**
```bash
git add COST.md
git commit -m "COST: Bedrock and AgentCore eu-west-1 unit prices with sources and check date"
git push -u origin docs/bedrock-prices
```
Expected: `1 file changed`, then the tracking line.

- [ ] **Step 5: Ask Linus to run the guards** on `docs/bedrock-prices`: `uv run --locked pytest 2>&1 | grep -E "[0-9]+ (passed|failed)|TOTAL"`.
Expected: the baseline passed count, no `failed` (dry-run of this section with sample numbers on the C1 branch: `204 passed`, 96%).

- [ ] **Step 6: PR.** Base `develop`, title `COST: sourced eu-west-1 unit prices (A3a)`, body: the prices table, "checked <date> on the AWS pages", Linus's output. Reviewers: Linus, Huvison.
Expected: the PR page shows only `COST.md` changed, base `develop`.

**Task done when:**
- the PR to `develop` is open with `COST.md` only, and Linus's output shows 0 failed;
- `COST.md` on the branch has no `<` placeholder left in the new section and three filled unit-price cells.

### Task 4: Hand the prices to Huvison (D1, by 18:00)

**Files:** none.

- [ ] **Step 1: Send Huvison** (Slack or a comment on his H5 PR):
```markdown
A3a prices for MODEL_PRICES_USD_PER_1K_TOKENS (USD per 1K tokens, eu-west-1, EU cross-region row, checked <date>; PR #<nn>):
"eu.anthropic.claude-sonnet-4-6": (<in>, <out>)
"eu.amazon.nova-lite-v1:0": (<in>, <out>)
Haiku 4.5 (<profile ID>): (<in>, <out>), only when config.py names it.
Source: https://aws.amazon.com/bedrock/pricing/
```
Expected: Huvison replies that his table holds these exact values (or shows his PR's diff with them).

- [ ] **Step 2: Ledger:** `Task 4: complete (Huvison confirmed <date/time>; PR #nn)`.

**Task done when:**
- Huvison has confirmed in writing that the values in his price table equal yours.

## Never
- Use a price from memory, another region, the "Global" row, batch or caching.
- Leave a `<…>` placeholder in a committed file.
- Request model access, or change anything in the AWS console.
- Push to `develop` or `main`, or add attribution lines.

## Done means
- [ ] **`COST.md` on `develop` has "## Unit prices (on-demand, eu-west-1)"** with four rows, each with input/output (or vCPU-hour/GB-hour) prices, the page row label, a working link and a date. *Verify:* open `COST.md` on GitHub (`develop`), click each link (it opens the AWS pricing page).
- [ ] **The per-question table's unit-price cells are filled** for the Sonnet, Haiku / Nova and AgentCore Runtime rows. *Verify:* same file; those three cells don't say `TODO`.
- [ ] **The numbers are right.** *Verify:* a second person opens the AWS page for Europe (Ireland) and checks that each per-1K value × 1,000 equals the page's per-1M figure on the stated row.
- [ ] **Huvison's price table matches.** *Verify:* `tools/constants.py` `MODEL_PRICES_USD_PER_1K_TOKENS` on his merged H5 branch has the same two tuples (or his written confirmation if H5 isn't merged yet).
- [ ] **The PR is merged** with Linus's output showing 0 failed. *Verify:* the PR from `docs/bedrock-prices` shows "Merged".

Related: [[A3a - Bedrock unit prices - spec]], [[A3b - COST measured figures - plan]], [[Build order]], [[How to execute a plan]]
