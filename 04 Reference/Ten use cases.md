---
source: "[[Multi-agent orchestrator guideline.pdf]]"
tags: [reference, area/scope]
---
# Ten use cases (guideline §03)
Each brief names the portfolio reality it comes from, the agent roster, the AWS services and the **cut line** (smallest version that still demos). **Ours is none of these**: it's the separate [[Problem statement|ERP Migration Progress Portal]], which says it is *not* UC-03 (UC-03 = discovery; ours = execution). They're kept here for patterns and the cut-line discipline.

## UC-01 Week-zero data room triage
*Diligence.* > "On our last post-acquisition assessment the financial statements and ERP extracts did not arrive until week three or four. The engagement was sold as four weeks and ran five to six." (Delivery retrospective, Sept 2026)
An assessment team's first three weeks go on orientation (what systems exist, where the money goes, which of thirty PDFs matters) while a fixed-price clock runs. Build the agent that reads the data room the night it opens and hands the team a Day-1 hypothesis pack: the five things most likely to be wrong, each with evidence and the confidence it deserves.
- **Agents:** orchestrator → doc-classifier, schema-profiler (ERP extracts), spend-classifier (invoices, contracts), hypothesis-agent, critic, writer
- **Data shape:** ~30 mixed PDFs and spreadsheets, 2 CSV table dumps with unlabelled columns, one folder of invoices
- **Cut line:** three document types, five hypotheses, no UI beyond a rendered Markdown pack. **Citations not optional even in the cut version**
- **Demo moment:** drop a folder in S3; 90 s later, five findings with page-level citations, plus one the critic rejected, shown with its reason
- **Watch for:** confidently summarising documents nobody asked about. The value is prioritisation, not coverage
- **Services:** S3, Textract, Bedrock KB, Strands, Step Functions, DynamoDB

## UC-02 The interview glossary that learns
*Knowledge capture.* > "First time, you understand 20% of that. Three weeks later, you can actually make sense of 80 to 90% of what they said in the first meeting." (On transcribing assessment interviews)
Regional accents and company vocabulary make early interviews (with the most senior people) barely comprehensible; by the time the team has the vocabulary, the access is gone. Build a pipeline that transcribes each interview, *accumulates the client's vocabulary as it goes*, and retroactively re-reads earlier transcripts with everything learned since. Map statements onto the ten IT maturity dimensions and flag where two interviewees contradict each other.
- **Agents:** orchestrator → glossary-builder (writes to shared memory), dimension-mapper, contradiction-finder, critic, writer
- **Data shape:** 6–8 interview recordings, 20–40 min each, with jargon and at least one pair who disagree
- **Cut line:** three interviews, one dimension mapped properly rather than ten badly, and the re-read pass working. The re-read *is* the idea; don't cut it
- **Demo moment:** interview one read on arrival, next to interview one re-read after interview six. The diff is the product
- **Watch for:** a glossary that's just a term list. It must change how later passes interpret earlier audio
- **Services:** Transcribe, Bedrock, AgentCore Memory, Bedrock KB, S3

## UC-03 Eighteen ERP systems, one map
*Enterprise architecture.* > "Eighteen ERP systems: three SAP ECC, five Business One, more inside the SAP family, and others from a different vendor entirely." (An AIP portfolio company's actual estate)
Nobody can draw it. ERP programme cost is driven less by how many systems than by how many *different kinds*: three copies of one product is a fraction of the work of three different products, and nobody can answer that either. Build the cartographer: connector agents read each system's schema and config export, a normaliser maps each onto a canonical model, a duplicate-detector finds the same customer and material in five places, and the orchestrator emits a landscape map, an integration inventory and a proposed migration wave order with reasoning.
- **Agents:** orchestrator → schema-reader (one per product), canonical-mapper, entity-overlap-detector, wave-planner, critic
- **Data shape:** six synthetic schema exports across three ERP products, with overlapping customer and material masters
- **Cut line:** two products, four instances, overlap detection working. Drop the wave planner before the overlap detection
- **Demo moment:** generated landscape diagram beside the answer: *four vendors, seven products, eighteen instances*, and what each tier costs to learn
- **Watch for:** a pretty diagram with no reconciliation underneath. The overlap is the insight; the diagram is packaging
- **Services:** Glue, Athena, Bedrock, Strands, OpenSearch Serverless

## UC-04 Golden record, with its reasons
*Data governance.* > "Your master data governance is a mess." (Assessment finding, verbatim, more than once)
The same customer exists seven times across seven instances, spelled differently each time. Off-the-shelf matching gets 80% then stalls; the last 20% needs judgement, and a data steward won't accept a match they can't interrogate. Build a reconciliation crew where every proposed merge arrives with an argument: a candidate-matcher does cheap blocking and embedding similarity, an adjudicator proposes the golden record *and writes down why*, a steward approves or rejects in a queue, and a rules-learner turns each human decision into a reusable rule so the queue shrinks as it's worked.
- **Agents:** orchestrator → candidate-matcher, adjudicator, rules-learner, critic + **human steward queue**
- **Data shape:** 5,000 customer records across four instances with realistic mess (abbreviations, legal-entity suffixes, address variants), one genuine near-twin that must *not* merge
- **Cut line:** one entity type, one merge dimension, a working approval queue. Rules-learner can be one rule type
- **Demo moment:** approve four merges; the fifth is auto-proposed with higher confidence because of what it learned from the first four
- **Watch for:** merging the near-twin. Put one in the eval set and hold it apart
- **Services:** Bedrock embeddings, OpenSearch Serverless, DynamoDB, Step Functions, AgentCore Memory

## UC-05 Where the order-to-cash money leaks
*Value chain.* > "Here is a mapping of levers against pain points, and what we think your revenue and profit impact would be if you tackle this." (Core exhibit of a CEO board deck, built by hand)
The deliverable that turns an IT finding into something a CEO acts on takes a senior consultant weeks. Inputs aren't exotic: order, delivery and invoice events. Build the analyst that mines the real process from event data (not the documented one), finds where time and margin go, sizes the impact in currency, and maps each bottleneck to a fix with a cost estimate. Every number traceable to a row.
- **Agents:** orchestrator → event-loader, process-miner, impact-quantifier (code tool, not prose), lever-mapper, critic, writer
- **Data shape:** ~200k order-to-cash events, 18 months, with a credit-check bottleneck and a regional delivery problem planted
- **Cut line:** one value chain, three bottlenecks, impact sized on a stated assumption (state it on the slide)
- **Demo moment:** "Credit blocks add 4.1 days to 23% of orders; here are the eleven rows behind that number."
- **Watch for:** a model doing arithmetic. Every figure comes out of the code interpreter or it doesn't ship
- **Services:** Athena, Bedrock Code Interpreter, Strands, QuickSight, S3

## UC-06 Shadow IT, found by follow the money
*Cost & FinOps.* > "IT spend and savings potential, including shadow IT." (Standing line item in every assessment scope)
Mid-market industrials can't say what they spend on IT: much is bought on departmental cards and never passes through IT. Reconstructable from finance data. Build the detective: ingest AP lines, card transactions and SSO sign-in logs; classify every vendor; flag spend with no IT owner (or an owner who left); propose consolidations with a saving and an honest risk note beside each.
- **Agents:** orchestrator → vendor-normaliser, category-classifier, shadow-detector, savings-proposer, critic
- **Data shape:** ~8k AP and card lines with inconsistent vendor naming, an SSO app list, a deliberately incomplete IT-owned application register
- **Cut line:** AP lines plus the SSO list. Skip the cloud bill; reconciling "paid for" vs "signed into" is the whole trick
- **Demo moment:** four tools paid for, two signed into by nobody for ninety days, one duplicating a tool IT already owns
- **Watch for:** claiming a saving without a risk note. A consolidation that breaks a workflow isn't a saving
- **Services:** Textract, Comprehend, Athena, Bedrock, Guardrails

## UC-07 Forecast scoping in an afternoon
*Machine learning.* > "They just tell us how it is and give us some sample data, and we look at the data ourselves and see how complex it is." (How ML scoping works today)
Scoping a forecasting engagement is fixed, repeatable, almost entirely mechanical work (standard interviews plus reading sample data): the best automation target on the menu. Build the scoping agent: profile each forecast target for quality, history depth, seasonality and intermittency; scout external drivers that are useful and actually obtainable; recommend one-shot vs trained with a defensible reason; produce the phase-one report a client pays for.
- **Agents:** orchestrator → data-profiler, feature-scout, model-selector, baseline-runner, critic, writer
- **Data shape:** three targets of differing difficulty: one clean seasonal series, one intermittent and spiky, one with an obvious external driver
- **Cut line:** two targets, a naive baseline actually run, one external driver checked for real availability. A recommendation with no baseline is an opinion
- **Demo moment:** two targets, two different recommendations, and the specific dataset property that drove the difference
- **Watch for:** recommending a foundation model for everything. The interesting output is *"this one does not need training and here is the evidence"*
- **Services:** Bedrock, Code Interpreter, SageMaker, Step Functions, S3

## UC-08 Incident learnings that travel between sites
*Safety & compliance.* > "Is somebody doing the pen testing for you? Have there been remediations? Or are you stuck actioning them?" (The same question, asked of safety findings)
An explosives manufacturer and an industrial services contractor both carry heavy regulatory load, report incidents as free text, and can't see that the same root cause has appeared at four sites. Corrective actions are local; learning stays local. Build the copilot: normalise incident narratives, cluster by cause across sites, retrieve the applicable regulation from a team-supplied corpus, assess reportability, draft a corrective action a named human signs. Nothing is ever filed automatically.
- **Agents:** orchestrator → narrative-normaliser, cause-clusterer, regulation-retriever, capa-drafter, critic + **mandatory human sign-off**
- **Data shape:** 400 synthetic incident narratives across six sites, one root cause recurring in three under different wording, plus a small public regulation corpus
- **Cut line:** clustering plus the reportability question. The corrective-action drafter can be a template
- **Demo moment:** "This has happened three times, at three sites, described three different ways", with the three narratives side by side
- **Watch for:** any path where the system files, notifies a regulator, or closes a finding without a human. Automatic fail on this brief
- **Services:** Bedrock KB, Guardrails, Step Functions, AgentCore Identity, DynamoDB

## UC-09 Field service quotes that hold their margin
*Commercial operations.* > "Price realisation versus list: how much discount leaks." (A KPI clients ask for and cannot produce)
Industrial services quoting depends on a few experienced estimators: slow turnaround, knowledge in their heads, margin leaking through discounts nobody aggregates. When an estimator retires, the capability goes. Build the quoting crew: turn an inbound request (email, spreadsheet, scanned drawing) into a structured job spec; price labour, equipment and travel from historical jobs; flag anything below the margin floor *with the reason*; check crew and equipment feasibility before a human presses send.
- **Agents:** orchestrator → rfq-parser, estimator, margin-guard, feasibility-checker, critic + **human send approval**
- **Data shape:** twelve inbound requests in mixed formats; 2,000 historical jobs with labour, equipment, travel and realised margin
- **Cut line:** one service line, email and spreadsheet inputs only. Skip the scheduler; keep the margin guard (the part a CFO cares about)
- **Demo moment:** a messy email in; a priced quote out in forty seconds, one line flagged *"3 points below floor: travel to this site has run over on the last four jobs"*
- **Watch for:** a quote with no comparable behind it. Every price cites the historical jobs it came from
- **Services:** Textract, Bedrock KB, DynamoDB, Step Functions, AgentCore Browser

## UC-10 The debrief that writes the playbook
*Internal capability.* > "One simple rule we should introduce at the end of every engagement: the team writes up learnings into reusable pieces. Nobody wants to do documentation." (Engineering leadership, Sept 2026)
Our own constraint, and the reason the other nine matter less than they look: we can't deliver the next four engagements the way we delivered the last, because the learning doesn't survive the engagement. People will talk for an hour; they won't write for an hour. So invert it: a facilitator agent runs a structured debrief with good reflection questions, a second turns the conversation into a template or checklist, a third diffs it against the existing playbook and proposes *only the delta*, and a librarian files it where delivery agents will read it.
- **Agents:** orchestrator → facilitator (asks, doesn't summarise), artefact-extractor, playbook-differ, librarian, critic
- **Data shape:** one real recorded team debrief (run it live at the hackathon, on the hackathon) plus an existing playbook page to diff against
- **Cut line:** facilitator + extractor + differ. Librarian can write to a folder
- **Demo moment:** debrief your own two days; show the checklist it produced and the three lines it proposed adding to the playbook
- **Watch for:** producing a summary. A summary isn't reusable; a checklist someone follows next time is. Test: could another team use the output tomorrow?
- **Services:** Transcribe, Bedrock, Bedrock KB, AgentCore Memory, S3 versioning

Related: [[Reference]], [[Hackathon guideline]], [[Problem statement]]
