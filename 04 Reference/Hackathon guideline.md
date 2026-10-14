---
date: 2026-09-30
source: "[[Multi-agent orchestrator guideline.pdf]]"
tags: [reference, area/process]
---
# Hackathon guideline: "Ten portfolio problems, two days, one orchestrator"
AmaliTech × American Industrial Partners (AIP) · Engineering hackathon brief · September 2026.
**Format:** teams of 3–4 · 2 working days · **Stack:** Amazon Bedrock · AgentCore · Strands · **Pick:** one brief per team, first come · **Judged on:** §5 (now see [[Pitch track grading rubric]]).
Every brief is a real problem inside an AIP portfolio company, cut down to something four engineers can prototype in two days on AWS. **None of them is a chatbot.** The ten briefs → [[Ten use cases]]. Our brief is separate → [[Problem statement]].

![[Multi-agent orchestrator guideline.pdf]]

## 01 The brief
AIP buys mid-market industrial companies (explosives, drilling, industrial services, lubricants distribution) and needs them worth more in five years than at close. The tech problems in the way are unglamorous, specific, and remarkably consistent across portfolio companies. **That consistency is the opportunity: a prototype that works on one portfolio company's problem is a template for the next four.** Hence a hackathon, not a roadmap: ten shots at *which of these is worth building properly*.

### The four rules
1. **A portfolio-company executive has to want it.** Not the CIO: the COO, the CFO, the VP of operations. If you can't name the person whose week gets better, you've picked a technology, not a problem.
2. **It has to be agentic, and you have to be able to say why.** Multiple steps, a decision about what to do next, tools it chooses between. If a Lambda and a SQL query would do the job, use them and pick a different brief.
3. **Two days means two days.** Every brief names the cut line. Scope down to the demo, then down again.
4. **It ships documented.** §4 lists the files. A brilliant demo with no `AGENTS.md` scores below a modest one that has it, deliberately.

### On using real data
Sandbox account with **synthetic or anonymised data only**. No portfolio-company production credentials, no real customer records, no financial statements. Several briefs list a data shape: generate data of that shape. **A judge who sees a real client name in a prompt log stops the demo.**

## 02 The orchestrator pattern
All ten briefs use the same shape; what changes is the specialists and tools, never the skeleton.

```
Request (file drop · form · event)
  → ORCHESTRATOR (plans and routes, does no domain work)
      → Retriever (finds evidence, cites it)   → Run ledger (claims, evidence, verdicts, attempt count, cost)
      → Analyst (computes via code tools)      ↗
  → CRITIC (judges blind, never sees the plan or the attempt count)
      ├─ rejected → [attempts < limit?] (a guard, not an agent)
      │     ├─ yes → retry, attempt n+1 → ORCHESTRATOR
      │     └─ limit reached → REJECTED RECORDS (every attempt's verdict and reason · human triage)
      └─ passes → Writer (assembles the artefact) → Human approval
                     ├─ sent back → ORCHESTRATOR
                     └─ approved → Deliverable · write to record
```

### The five roles
| Agent | Single responsibility | What it must never do |
|---|---|---|
| orchestrator | Decide what happens next and in what order. Hold the plan. Stop when the goal is met or the budget is gone | Answer a domain question itself. The moment it does, you have one big agent again |
| retriever | Find evidence and return it with a citable identifier (document, page, row, timestamp) | Interpret. It returns what it found, not what it means |
| analyst | Turn evidence into a claim. Arithmetic goes through a code tool, never through the model's head | Invent a number that is not in the evidence it was given |
| critic | Receive a claim plus its evidence (*without* the plan, the conversation, or how many attempts are left) and reject anything unsupported | See the orchestrator's reasoning or the retry counter. Its independence is the entire point |
| writer | Assemble passed claims into the artefact a human asked for, carrying every citation through | Add a claim of its own while writing. The most common way a hallucination reaches the deliverable |

> **The critic is the highest-value agent you will build.** Also the one teams cut first when late. Don't. Two days is enough to build something that produces confident output; the critic is what makes it worth showing to someone who will act on it. The demo lands when the critic *catches something on stage*: keep a deliberately weak input in the demo set and let it get rejected in front of the judges. → [[Critic is the highest-value agent]]

> **The reject loop is the one that will bite you.** Critic rejects → orchestrator re-plans → critic rejects has no floor. A claim the evidence will never support goes round until the account notices: no error, no crash, just a run that never finishes and a bill that does.
> - **Bound it, and enforce the bound on the edge, not inside the critic.** Every rejection increments an attempt counter **held in the run ledger against that claim**, not carried in the message (where an agent can drop or reset it). The rejected path is a guard, not a hop: under the limit → back to the orchestrator to re-plan; at the limit → claim leaves the loop and is written to a **rejected-record store** with every attempt's verdict and reason, for a human queue someone actually works.
> - **Two retries is the right default** for a 72-hour build. If three attempts can't evidence a claim, the fault is almost never in the claim; it's upstream, in retrieval or data.
> - **Why the counter isn't the critic's job:** a critic that knows it's on the last attempt has a reason to soften. Let it judge blind every time; let the edge after it do the arithmetic.
> - The human *sent back* edge needs no limit (a person is the control), but write each return to the same ledger so a draft that's been round four times is visible.

### Eight non-negotiables
1. **Every claim cites its source.** A claim without an evidence identifier is a bug: fail the run.
2. **Every loop has a bound and a terminal state.** Retry ceiling in the ledger, guard on the rejected edge, rejected-record store at the end. "It will converge" is not a design.
3. **No agent writes to a system of record.** Writes go behind a human approval step. Step Functions `waitForTaskToken` is four lines and is the difference between a prototype we can show a client and one we can't.
4. **Tools are code.** Anything deterministic (a join, a rate lookup, a date difference, a currency conversion) is a function the agent calls, not a paragraph it reasons through.
5. **State lives outside the agents.** A DynamoDB run ledger keyed by `run_id`, holding every claim, its evidence, the critic's verdict, **the attempt count** and tokens spent. Runs become resumable, auditable and demoable after the fact, and the loop counter has somewhere tamper-proof to live.
6. **One source of truth per computed thing.** If two places decide the same number they will disagree, and the one on screen will be wrong. Shipped four times on this account. → [[One source of truth per number]]
7. **A budget ceiling per run, enforced in the orchestrator.** Fail closed with a partial result and a reason. An agent loop with no ceiling is how a hackathon account gets suspended on day two.
8. **Guardrails on every model call that touches client text.** Bedrock Guardrails, PII filter on. Free, one config, the first thing a client's security lead asks about.

## 03 Ten use cases
→ [[Ten use cases]]

## 04 Delivery guidelines
Same repo shape for all ten, so a judge can navigate any team's work in two minutes and good ideas survive past Friday.

| Path | Contents |
|---|---|
| `README.md` | what it does · who for · run it in 5 commands |
| `ARCHITECTURE.md` | the diagram, the data flow, why each service |
| `AGENTS.md` | one row per agent: **graded hardest** |
| `EVALS.md` | the fixed input set, the scores, what still fails |
| `DEMO.md` | the 3-minute script, literally, with timings |
| `COST.md` | cost per run, and at 100 runs/day |
| `DECISIONS.md` | 5 lines per decision: what, why, what we rejected |
| `HANDOFF.md` | what is real, what is faked, what breaks first |
| `agents/` | one file per agent, prompt + tool bindings |
| `tools/` | deterministic code the agents call |
| `evals/` | fixed inputs + expected outputs + the runner |
| `infra/` | CDK or SAM: it has to deploy from clean |
| `demo/` | the data you will demo on |

> **AGENTS.md decides your documentation score.** One table, one row per agent, seven columns: **name · single responsibility · input schema · output schema · tools it may call · guardrail · failure mode.** If you can't fill the row, the agent isn't designed yet. Writing it in hour three is the cheapest architecture review you'll get all week. Teams that write it at the end always discover two agents doing the same job.

### The two days
| When | What |
|---|---|
| D1 09:00–10:30 | Pick the brief. Name the executive. Write `AGENTS.md` (the table, before any code). Draw the orchestration on a whiteboard and photograph it into `ARCHITECTURE.md` |
| D1 10:30–12:00 | **Build the eval set first:** ten fixed inputs, expected outputs, including one input designed to fail and one that should be rejected. The single highest-leverage 90 minutes |
| D1 12:00–16:00 | **Tools before agents.** Write the deterministic functions and unit-test them. Agents on untested tools debug very badly |
| D1 16:00–18:00 | One specialist agent end to end, with the run ledger writing. Prove the skeleton on one path before adding a second agent |
| D2 09:00–12:00 | Remaining specialists, then the orchestrator, then the critic. Run the eval set after each addition: a score drop tells you which agent did it |
| D2 12:00–14:00 | Human-in-the-loop step. Guardrails on. Budget ceiling enforced. ~1 hour together; they make it showable to a client |
| D2 14:00–16:00 | **Freeze the code.** Write the docs. Record eval scores as they are, failures included |
| D2 16:00–17:00 | Rehearse the demo twice, on the clock, from a cold start. A demo that needs a warm cache fails on stage |

> **The 14:00 freeze on day two is real.** Every hackathon has a team with something genuinely good and no documentation; their work is unusable a week later, so the two days are a total loss. Freeze, then write. If the freeze costs a feature, it was the right feature to lose. → [[Code freeze is Day 2 1400|Code freeze is Day 2 14:00]]

### Documenting an agent well
A well-documented agent is one a different engineer can modify without reading your prompt. Four things, and prose isn't one:
- **A schema on both sides.** Typed input, typed output, validated at the boundary. Output shaped "whatever the model said" can't be composed.
- **An explicit tool list.** What it may call, and (worth stating) what it deliberately may not.
- **A named failure mode.** What it does when it can't do its job. A confident guess is the wrong answer; say what the right one is.
- **One worked example in the repo.** A real input and its real output, committed. Doubles as a regression test.

## 05 Definition of done (guideline's own scoring, out of 100)
| Item | Pts | Meaning |
|---|---|---|
| Client value | 25 | A named portfolio-company executive would pay for this; you can say what it replaces |
| Orchestration quality | 20 | Real roles with real contracts; orchestrator plans and does no domain work |
| Trustworthiness | 20 | Citations throughout, a critic that actually rejects, guardrails, human in the loop before any write |
| Documentation | 15 | The eight files. `AGENTS.md` complete. Another team could pick this up on Monday |
| Works on unseen input | 10 | **We will hand you an input you have not seen.** Degrading honestly beats failing loudly |
| Cost and path to production | 10 | Cost per run **measured, not guessed**; honest account of what breaks at scale |

**Hard gates** (below any, score doesn't matter): deploys from a clean account with the documented commands · eval set runs and results written down *including* failures (a perfect `EVALS.md` = missing) · no autonomous write to any system of record · no real client data in repo, logs or prompts · `AGENTS.md` exists and every row complete.

> **What we are actually shopping for:** two or three of these become real engagements. Not the flashiest: the ones where a judge can read `HANDOFF.md` and see exactly what **week three** looks like. Write it for a colleague about to be given your prototype with no context.

## 06 Default stack
Use these unless you have a reason not to, and put the reason in `DECISIONS.md`. Nobody should spend hackathon hours choosing a vector store.
| Job | Use | Why |
|---|---|---|
| Models | Amazon Bedrock | One endpoint, one IAM story, guardrails attach natively |
| Agent framework | Strands Agents | Multi-agent patterns first class; agent-as-tool is a decorator |
| Agent runtime | Bedrock AgentCore | Session isolation, Memory, Identity, Observability and a Code Interpreter without building any of it |
| Retrieval | Bedrock Knowledge Bases | S3 in, chunking and embedding handled, citations come back with the chunk |
| Vectors | OpenSearch Serverless | The KB default. Don't litigate it in two days |
| Deterministic flow | Step Functions | Where a step order is known, encode it. Cleanest human-approval primitive |
| Run ledger | DynamoDB | One table, `run_id` partition key. Claims, evidence, verdicts, tokens |
| Documents | Textract | Tables and forms survive extraction |
| Speech | Transcribe | Diarisation and custom vocabulary (UC-02) |
| Tabular at volume | Athena over S3 | No cluster; an agent can hold a SQL tool against it |
| Arithmetic | Code Interpreter | Every number a model states unaided is a number you can't defend |
| Safety | Bedrock Guardrails | PII and topic filters, one config, no code |

### Where the orchestration should *not* be an agent
An orchestrator that plans is worth its cost when the next step genuinely depends on what was just found. When the order is known in advance (extract → classify → score → write) that's a state machine: cheaper, faster, debuggable, doesn't wander. Most briefs want a **Step Functions spine with agents at the nodes, and exactly one planning agent where the path is genuinely open.** Saying which is which in `ARCHITECTURE.md` earns marks; making everything an agent loses them.

## 07 Traps
| Trap | How it shows up | Do instead |
|---|---|---|
| The mega-prompt | One agent, 4,000 tokens of instructions, no roles. Works on the demo input only | Split by responsibility. If you can't name an agent's job in six words, it's two agents |
| Agent sprawl | Nine agents by lunch on day two, none tested, no idea which is wrong | Add the next agent only when the eval score for the current set is understood |
| Chat as the interface | A chat box in front of a task with four known inputs | A form. Agentic is what happens behind the screen, not a conversation on it |
| Demo-only data | Flawless on the one PDF you tuned against; collapses on the second | Ten inputs in the eval set from hour two, at least three awkward |
| No critic | Confident, fluent, unverifiable output: the most expensive failure, because it looks like success | Build the critic third, not last, and demo it catching something |
| A loop with no floor | Reject, re-plan, reject. No error, no crash, a bill that doesn't stop | Retry ceiling in the ledger, guard on the rejected edge, rejected-record store |
| Two sources of truth | Summary card and detail table disagree | One function, called twice. Shipped four times on this account |
| Autonomous writes | "It updates the ERP automatically." No client allows it near production; unbuyable | Human approval before every write, from the first commit |
| Docs after the demo | Day two, 17:30, a README that says `npm start` | The 14:00 freeze. Not negotiable |
| Scraping past an API | Browser agent clicking through a portal that has a REST endpoint | Use the API. Browser tool only for systems with no other door |
| Solving our problem, not theirs | A tool that makes consultants faster, pitched as client value | Legitimate (UC-10 is exactly this), but say so. Don't dress internal efficiency up as a client outcome |

*Footer: "Pick a brief, name your executive, write AGENTS.md before you write code."*

Related: [[Reference]], [[Pitch track grading rubric]], [[Ten use cases]]
