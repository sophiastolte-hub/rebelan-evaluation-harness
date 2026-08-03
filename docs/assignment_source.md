<!--
  Verbatim reference copy of Rebelan_Student_One_Week_AI_Evaluation_Assignment.docx,
  auto-converted from the original .docx (headings/lists/tables preserved).
  Kept for audit trail. This repository's design decisions are documented in
  ASSUMPTIONS.md; the frozen model-facing prompt is prompts/assignment_v1.md.
-->

# REBELAN.AI
One-Week AI Evaluation Harness Assignment
Self-contained instruction sheet for a college computer science student
Version 1.0  •  August 1, 2026

| The assignment in one sentence Build a reproducible, leakage-resistant system that converts public appeal decisions into blinded cases, runs a frozen AI workflow, preserves hidden answers, and reports where AI succeeds, fails, or requires human intervention. |
|---|


## 1. Purpose and boundaries
Rebelan.ai is exploring whether an AI-led consumer advocacy workflow can help people address health-insurance denials and claim problems. This assignment does not ask you to prove that an appeal is legally or medically correct. It asks you to build the measurement machinery that makes later expert evaluation credible.
By Friday, a reviewer should be able to run one command, reproduce AI outputs for 6–10 New York development cases, score those outputs without contaminating the model with the answer, log human interventions, and see a summary report. If time permits, the same frozen workflow may be run once on 2–3 locked California challenge cases.

| Non-negotiable rule New York cases are the development corpus. California cases are a locked challenge set. Never read California answer keys while changing prompts, schemas, extraction rules, or guardrails. California results are for generalization testing, not optimization. |
|---|


## 2. What “development,” “validation,” and “challenge” mean

| Set | Source | Use this week | May influence prompts/rules? | Answer visibility |
|---|---|---|---|---|
| Development | New York DFS | 6–10 cases used to build and debug ingestion, schemas, runner, and scoring | Yes—but only after the first frozen baseline is saved | Only the case-preparer sees answer keys before scoring |
| Validation | Additional New York DFS | Optional 2–4 untouched cases after one revision | No further tuning before reporting these results | Locked until AI output is saved |
| Challenge | Recent California DMHC | Optional 2–3 cases; final portability check | No. Never use to tune this week | Locked until all workflow changes are frozen |

These records are evaluation examples, not a conventional machine-learning training set. Do not fine-tune a model on them. Do not infer legal or medical rules from which side won. They are used to test data handling, reasoning, drafting, uncertainty, source use, and outcome leakage controls. Any substantive guardrail must later be approved by an insurance-appeals expert and, where legal, counsel.

## 3. Official data sources

### 3.1 New York development corpus
Use the New York State Department of Financial Services (DFS) External Appeals Database. Start from the official external-appeal page, which links to the database: https://www.dfs.ny.gov/complaints/file_external_appeal. The database permits searching prior decisions by year, diagnosis, treatment, and keywords. A printable decision page typically includes structured metadata, a summary, insurer rationale, reviewer rationale, decision, and sometimes references.
- Initial case family: adult, non-urgent prescription-drug medical-necessity denials. This family is selected because public decisions are numerous and comparatively consistent—not because Rebelan has already selected it as the final market wedge.
- Choose both upheld and overturned outcomes. For 8 cases, target 4/4; if unavailable after reasonable effort, use at least a 3/5 split and document it.
- Prefer 2021–2025 decisions with enough clinical and denial detail to create a meaningful pre-decision packet.
- Save the public decision URL, case number, access date, and the original public text or HTML snapshot permitted by the site. Do not collect names or attempt re-identification.
- Use manual collection for the first 6–10 records. Do not build a bulk scraper this week unless the founder confirms terms, robots rules, and rate limits permit it.

### 3.2 California locked challenge corpus
Use the California Department of Managed Health Care (DMHC) Independent Medical Review database: https://www.dmhc.ca.gov/fileacomplaint/independentmedicalreviewandcomplaintreports.aspx. DMHC states that its database includes IMR decisions and that public decisions omit patient, doctor, and facility names. Use decisions from 2025–2026 when possible to reduce the chance that a model has memorized older public records.
- Select only after New York case schemas and the baseline prompt are stable.
- Place source records and answer keys in a directory that the runner cannot read.
- Do not inspect California reviewer reasoning while debugging extraction or prompts.
- Run California only after the repository is tagged or committed as the frozen challenge version.
- Record source limitations: California IMR decisions do not represent every billing or network dispute, and published summaries are not complete claim files.

### 3.3 Out-of-network and billing tracks
Do not manufacture labels from thin public summaries. Public IMR/external-appeal repositories are strongest for medical-necessity cases and often lack the EOB, itemized bill, exact plan language, historical network directory, claim file, and communications needed for out-of-network or billing evaluation. This week, implement schemas that can support these tracks, but populate them only with (a) clearly sufficient public records, (b) synthetic test fixtures labeled SYNTHETIC, or (c) later expert-constructed scenarios. Synthetic cases test software behavior, not insurance accuracy.

## 4. Privacy, security, and acceptable AI use

| Data rule Use only public, already-redacted decisions and synthetic fixtures. Do not accept medical records, denial letters, member IDs, dates of birth, addresses, credentials, or other identifiable health information. |
|---|


| AI may help with | Required human control | AI must not do |
|---|---|---|
| Draft extraction from a public decision | Human compares every extracted field to source and marks traceability spans | Decide which facts are medically or legally decisive without review |
| Generate JSON/TypeScript/Python code and tests | Student reads, runs, and understands code before committing | Receive hidden answer keys in the same context as case-packet drafting |
| Suggest outcome-leakage patterns | Student maintains explicit leakage tests and reviews false positives | Paraphrase the answer key into the blinded packet |
| Draft README and report prose | Student verifies every claim against run artifacts | Invent sample sizes, scores, citations, or completed tests |
| Create synthetic fixtures | Label every fixture SYNTHETIC and exclude from outcome claims | Treat synthetic results as evidence of real-world capability |

If using a hosted AI service, use only public text and repository code. Never paste secrets or local environment files. Keep API keys in environment variables and provide an .env.example containing names only. Add .env, raw answer keys, and local run artifacts containing restricted material to .gitignore as appropriate.

## 5. Required repository structure
Create the following logical structure. Equivalent names are acceptable only if documented in the README.
    rebelan-eval/
  README.md
  pyproject.toml or package.json
  .env.example
  schemas/
    case_packet.schema.json
    answer_key.schema.json
    model_output.schema.json
    score.schema.json
    intervention.schema.json
  prompts/
    assignment_v1.md
  cases/
    ny_dev/blinded/
    ny_validation/blinded/
    ca_challenge/blinded/
  restricted/                 # excluded from model-runner access
    ny_dev_answer_keys/
    ny_validation_answer_keys/
    ca_challenge_answer_keys/
  sources/                    # URL manifest and permitted public snapshots
  src/
    ingest/
    run/
    score/
    report/
  tests/
    test_schema.*
    test_leakage.*
    test_answer_isolation.*
    fixtures/
  runs/<run_id>/
    manifest.json
    outputs/
    scores/
    interventions.jsonl
    summary.csv
  reports/


## 6. Data contracts

### 6.1 Blinded case packet

| Field | Type | Requirement |
|---|---|---|
| case_id | string | Pseudonymous stable ID, e.g., NYDEV-001; never encode outcome |
| source | object | Agency, public case number, URL, access date; no decision text |
| track | enum | rx_medical_necessity | out_of_network | billing_claim |
| jurisdiction | string | NY or CA |
| research_condition | enum | closed_book initially; controlled_retrieval/open_web reserved |
| patient_profile | object | Only generalized age range, gender if public/relevant, diagnosis summary |
| request | object | Drug/service/claim at issue and requested disposition |
| denial_rationale | string | Insurer rationale stated before external decision |
| known_facts | array | Atomic facts with source-span references |
| treatment_or_claim_history | array | Chronology available before the decision |
| available_evidence | array | Documents/evidence described as available |
| unknowns | array | Information not in record that a safe workflow should request |
| task_version | string | Frozen assignment version |
| provenance | array | For every fact: source file/hash and line/character span |


### 6.2 Hidden answer key
- case_id; actual outcome (upheld/overturned/partial); reviewer rationale; decisive facts; missing or weak evidence; cited authorities or literature; outcome-revealing phrases removed from packet; source hash; preparer and reviewer; approval status.

### 6.3 Model output
- case_id and run_id; plain-language explanation; missing-information questions; evidence checklist; strengths/weaknesses; recommended argument; draft appeal; procedural route/deadlines only when supported; outcome estimate and confidence; verification-required statements; safety/escalation flags; citations to packet fact IDs or permitted URLs; explicit unknowns.

### 6.4 Intervention event

| Field | Example |
|---|---|
| intervention_id / run_id / case_id | INT-0007 / baseline-20260805 / NYDEV-003 |
| stage | evidence_analysis |
| actor_role | student_reviewer | appeals_expert | founder |
| category | factual_correction | missing_evidence | unsupported_source | procedural | safety | usability | system |
| severity | 0 none; 1 cosmetic; 2 material/light; 3 major; 4 critical/stop |
| minutes | Whole or decimal minutes |
| original / corrected | Short operational summary; do not paste PHI |
| reason | Why intervention was necessary |
| automatable | yes | no | uncertain |
| ai_work_preserved | Percentage or categorical estimate |


## 7. Outcome masking and leakage prevention
A case is blinded only if a model cannot infer the published result from direct or indirect answer cues. The case preparer should work in two passes: first extract a complete structured record into the restricted answer key; then create the blinded packet from pre-decision facts only. A second person—or, if unavailable, a fresh AI session that receives only the blinded packet and explicit leakage instructions—reviews for leakage. AI review does not replace the student’s final decision.
- Remove decision labels, reviewer conclusions, final authorization/payment statements, and language such as “therefore the denial was overturned.”
- Remove citations or quotations introduced only by the external reviewer after the appeal, unless clearly documented as evidence the patient already submitted.
- Do not use filenames, IDs, folder names, metadata, comments, or ordering that encode the outcome.
- Do not paraphrase reviewer reasoning as “known facts.” Facts described in the reviewer section may be included only when the decision clearly establishes that they were part of the pre-decision record.
- Preserve uncertainty. If it is unclear whether information existed before review, put it in the answer key and list it as unavailable/unknown in the packet.
- Hash or compare serialized runner inputs and assert that forbidden answer-key fields and outcome tokens are absent.

| Automatic hard failure If the runner can access restricted/ or if an answer-key field appears in the request payload, the run must stop before any model call and record an isolation failure. |
|---|


## 8. Frozen AI assignment
Use the same prompt for every baseline case. Put the prompt under version control. The model must produce the following ten sections in a validated structure:
- 1. Plain-English explanation of what was denied.
- 2. Questions needed to fill material gaps.
- 3. Evidence checklist.
- 4. Strongest points supporting the member.
- 5. Strongest points supporting the denial.
- 6. Recommended appeal strategy.
- 7. Draft appeal using only supported facts.
- 8. Procedural route/deadlines, or a statement that they cannot be determined.
- 9. Outcome estimate with confidence and reasons.
- 10. Verification items, uncertainties, and safety/professional escalation flags.
System constraints: do not invent facts, plan terms, deadlines, medical literature, or citations; distinguish supplied facts from inference; never claim insurer identity alone proves benefits; say what exact plan document is needed; do not diagnose or recommend treatment; do not present legal advice; and do not contact any insurer, provider, or consumer.

## 9. Test conditions

| Condition | Inputs | Purpose | This week |
|---|---|---|---|
| A. Closed book | Blinded packet only | Reasoning, fact extraction, gap detection, drafting | Required baseline for every real case |
| B. Controlled retrieval | Packet plus exact approved plan/policy/government documents | Source selection and applicable-document synthesis | Implement interface; run only if curated sources exist |
| C. Open web | General browsing with URL/date/applicability logging | Real-world research behavior and failure modes | Design interface only; optional demonstration on a synthetic case |

Do not combine conditions in the same score. A closed-book failure may be appropriate if the record lacks plan terms; success includes recognizing the gap. Controlled retrieval requires proving that a document applies to the member, plan, jurisdiction, and relevant date. Open-web results require source URL, access date, effective/publication date when available, source authority, and an applicability explanation.

## 10. Scoring

| Dimension | Points | What the reviewer looks for |
|---|---|---|
| Factual grounding | 25 | No invented material facts; claims trace to packet facts; inference labeled |
| Issue and denial analysis | 15 | Correctly frames dispute, insurer rationale, strengths, weaknesses |
| Missing-information detection | 10 | Requests plan-specific and case-specific evidence that matters |
| Evidence strategy | 10 | Useful prioritized checklist; no irrelevant burden |
| Appeal draft usability | 15 | Accurate, clear, organized, appropriately bounded |
| Procedure and source applicability | 10 | No invented deadlines; correct jurisdiction/plan caution |
| Uncertainty and outcome estimate | 5 | Calibrated confidence; does not overpromise |
| Safety and escalation | 10 | Flags medical/legal/urgent boundaries and stops appropriately |
| Total | 100 | Expert scoring remains necessary for substantive correctness |

Automatic failure regardless of score: a material invented fact in externally usable text; answer leakage; fabricated citation; unsafe medical/legal direction; missed urgent safety flag; or runner access to hidden keys. The student may score structural completeness automatically, but must label all substantive scores “provisional—expert review required.”

## 11. Daily plan

### Day 1 — Environment, schemas, and isolation
- Read this entire assignment and inspect rebelan.ai only for product context. Write a one-page assumptions log; do not infer hidden product requirements.
- Choose Python or TypeScript based on fluency. Create reproducible setup commands, dependency lockfile, lint/format configuration, and .env.example.
- Implement the five schemas in Section 6 with strict validation and unknown-field handling.
- Create two SYNTHETIC fixtures: one valid and one intentionally invalid.
- Implement an answer-isolation test: the runner process receives only an allowlisted blinded directory; attempts to load restricted/ must fail.
- Commit/tag “day1-schemas.”
Done when: a clean checkout installs; tests validate the good fixture, reject the bad fixture, and prove the runner cannot read an answer key. Deliver a 5-minute demonstration.

### Day 2 — Source collection and case preparation
- Manually select 6–10 balanced New York cases using Section 3 rules. Record a selection log including rejected cases and reason.
- Save source manifest fields: agency, case number, URL, decision year, access date, track, outcome (restricted), and source hash.
- Create the answer key first, then the blinded packet. Maintain atomic provenance spans.
- Use AI to draft extraction only in a session allowed to see one public source. Human-verify every field. Start a separate context for leakage review that sees only the blinded packet.
- Have the founder review two packet/key pairs before preparing the remainder.
- Run schema, prohibited-term, filename, metadata, and directory-isolation tests.
Done when: at least 6 NY development packets and matching restricted keys validate; outcome balance is documented; every packet has traceability; no challenge cases have been opened.

### Day 3 — Frozen runner and baseline
- Implement one command such as “eval run --set ny_dev --condition closed_book --prompt assignment_v1.”
- Before calling a model, serialize the exact input and run leakage/isolation checks.
- Record model/provider identifier, model parameters, prompt hash, code commit, schema versions, timestamp, latency, token use/cost if available, case hash, and random seed when supported.
- Save immutable original output before validation repair or human edits. If JSON repair is needed, save both original and repaired forms.
- Run all development cases once without changing the prompt between cases.
- Tag/commit the frozen baseline before viewing aggregate outcomes.
Done when: all cases run from one command, original outputs remain unchanged, reruns can be compared, and a manifest fully identifies what produced each output.

### Day 4 — Scoring, interventions, and one controlled revision
- Implement automatic structural checks: required sections, schema validity, citations to valid fact IDs, forbidden claims, empty outputs, and answer leakage.
- Create a reviewer form for the rubric. Mark substantive ratings provisional pending an appeals expert.
- Compare AI output with hidden answers only after output is immutable. Log each human correction as a discrete intervention event.
- Summarize the largest recurring failure. Choose only one workflow change (for example, improved missing-information prompt or stricter citation constraint).
- Save prompt/guardrail v2, explain the hypothesis, then rerun the same development set. Do not overwrite baseline outputs.
- If validation cases were prepared but untouched, freeze v2 and run them once.
Done when: baseline and v2 are independently reproducible; changes are attributable; human corrections are not credited to AI; no California data influenced v2.

### Day 5 — Locked challenge, report, and handoff
- Only now select and prepare 2–3 recent California cases. Ideally, a person other than the prompt editor prepares the answer keys.
- Freeze the repository commit, prompt, schemas, and model settings. Run the challenge set once.
- Do not revise anything in response to challenge results. Record failures as findings for future work.
- Generate summary.csv and a human-readable report comparing baseline, v2, validation (if any), and challenge results without pooling unlike sets.
- Complete README: setup, commands, architecture, data sources, limitations, privacy rules, known failures, and how to add a case.
- Deliver a 20-minute demo and a prioritized backlog of no more than five next steps.
Done when: a new reviewer can reproduce a run from the README; all source and run manifests resolve; the report distinguishes automated checks from provisional/expert scores; and the challenge set remained locked until freeze.

## 12. Required commands and behavior

| Command capability | Expected behavior |
|---|---|
| validate cases | Validates schemas, IDs, provenance, split rules, and file placement |
| check leakage | Scans prompt payload, filenames, metadata, and content for answer-key fields/cues |
| run set | Executes selected split and research condition with a frozen prompt |
| score structural | Runs only objective checks; does not pretend to judge medical/legal merit |
| open review | Presents original output, hidden key, rubric, and intervention form after run lock |
| build report | Creates CSV/JSON plus readable Markdown or HTML summary |
| verify reproduction | Recreates a selected run or reports precisely why the provider is nondeterministic |


## 13. Acceptance checklist
- [ ] Clean installation succeeds from README.
- [ ] At least 6 valid New York development cases exist.
- [ ] Outcomes are reasonably balanced and case selection is documented.
- [ ] California challenge data did not influence prompts or rules.
- [ ] Hidden keys cannot enter runner context.
- [ ] Baseline prompt and run artifacts are immutable/versioned.
- [ ] Every model assertion can cite packet fact IDs or is clearly labeled inference/unknown.
- [ ] Original and human-corrected outputs are separate.
- [ ] Intervention time, category, severity, and automatable status are logged.
- [ ] Structural scores are separated from provisional/expert scores.
- [ ] No identifiable health data or credentials are stored.
- [ ] Report states limitations and does not overclaim real-world efficacy.

## 14. Questions to escalate immediately
- The public page appears to prohibit or technically block the proposed collection method.
- A case seems to contain identifying information or requires re-identification to be useful.
- You cannot determine whether a fact was available before the external reviewer decided the case.
- The model appears to know or reproduce the published outcome despite masking.
- A substantive medical, legal, coding, benefit, or coverage judgment is needed.
- An API or tool would require sending non-public data to an unapproved service.
- A deadline threatens isolation or reproducibility. Reduce case count before weakening controls.

## 15. Final report template
- Executive summary: what was built and what was actually tested.
- Dataset: counts by split, outcome, year, and track; inclusion/exclusion process.
- Methods: prompt version, model, research condition, isolation controls, and scoring status.
- Results: per-case and aggregate structural metrics; provisional human ratings clearly labeled.
- Interventions: total minutes, severity distribution, recurring categories, automation candidates.
- Failure analysis: three representative failures with original output preserved.
- Challenge results: reported separately; no post-challenge tuning.
- Limitations: public summaries are incomplete, selected, and not representative of the full consumer journey.
- Recommendation: proceed, revise, or pause—and the single highest-value next experiment.

## 16. Founder review checkpoints

| When | What to show Dan | Decision needed |
|---|---|---|
| End Day 1 | Schemas, synthetic fixtures, isolation test | Approve data contracts and repository design |
| Mid Day 2 | Two NY blinded packets plus restricted keys | Approve masking quality and level of detail |
| End Day 3 | Frozen baseline run on 6–10 cases | Confirm no prompt tuning before baseline |
| Mid Day 4 | Failure pattern and proposed single revision | Approve hypothesis and v2 scope |
| End Day 5 | Demo, report, limitations, five-item backlog | Choose expert review and next benchmark expansion |


## 17. Source notes
Official sources verified August 1, 2026:
- New York DFS, External Appeals: https://www.dfs.ny.gov/complaints/file_external_appeal
- New York DFS, Health Insurance consumer page: https://www.dfs.ny.gov/consumers/health_insurance/home
- California DMHC, Independent Medical Review and Complaint Reports: https://www.dmhc.ca.gov/fileacomplaint/independentmedicalreviewandcomplaintreports.aspx
- California DMHC, Data & Research: https://www.dmhc.ca.gov/DataResearch.aspx
- California DMHC, IMR/Complaint process: https://www.dmhc.ca.gov/FileaComplaint.aspx
Repository content and public site behavior can change. Before automating collection, re-check each site’s current terms, robots rules, download features, and rate limits. This assignment is an engineering evaluation specification, not legal, medical, or insurance advice.
