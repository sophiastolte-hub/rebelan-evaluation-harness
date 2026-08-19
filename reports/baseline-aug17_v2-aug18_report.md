# Rebelan.ai Evaluation Report

Generated: 2026-08-19T05:11:28.143810+00:00

This report is generated entirely from files under `runs/`. It does not assert real-world appeal-drafting efficacy; structural metrics are automated, and all substantive quality claims are 'provisional—expert review required' pending review by an insurance-appeals expert.

## Executive summary

This week's harness was built and tested end-to-end against real data, not just synthetic fixtures. What was built: a leakage-resistant evaluation harness with a tested, two-layer isolation boundary (`RestrictedAccessGuard` + `read_allowlisted`) preventing the model runner from ever reading hidden answer keys; 8 real New York DFS medical-necessity denial cases, manually sourced and blinded, each with a verified hidden answer key; a frozen runner, an automatic structural scorer, and a report generator.

What was actually tested: the frozen `assignment_v1` prompt was run once against all 8 real development cases in the `closed_book` condition (run `baseline-aug17`). This produced a systematic, fully-diagnosed failure pattern -- 0/8 outputs were schema-valid and 7/8 triggered an automatic hard failure for fabricated citations -- traced to two specific prompt-format ambiguities rather than a model-capability problem. One single, documented revision (`assignment_v2`) targeting exactly those two ambiguities was then run once against the same 8 cases (run `v2-aug18`): 8/8 schema-valid, 0/8 hard failures. A light `open-review` pass against the hidden answer keys on 2 of the 8 v2 cases logged 2 genuine interventions, one of which points to a recurring calibration pattern worth testing next (see Recommendation below).

No claim is made here about the real-world quality of the AI's appeal-drafting or legal/medical reasoning -- that remains explicitly out of scope this week and is labeled "provisional--expert review required" throughout.

## Run `baseline-aug17`

- Split: `ny_dev`  |  Condition: `closed_book`
- Model: `claude-sonnet-4-5-20250929`  |  Provider: `anthropic`
- Prompt: `assignment_v1` (hash `d1338df83dfd`)
- Code commit: `1947d2f219cb423a0353da6df51dcfad7662cd9d`
- Cases run: 8  |  Schema-valid outputs: 0/8
- Automatic hard failures: 7/8
- Human intervention time logged: 0.0 minutes across 0 events
- Estimated model spend this run: $0.4870

**Hard-failed cases:**
- `NYDEV-001`: fabricated_citation
- `NYDEV-002`: fabricated_citation
- `NYDEV-003`: fabricated_citation
- `NYDEV-004`: fabricated_citation
- `NYDEV-006`: fabricated_citation
- `NYDEV-007`: fabricated_citation
- `NYDEV-008`: fabricated_citation

## Run `v2-aug18`

- Split: `ny_dev`  |  Condition: `closed_book`
- Model: `claude-sonnet-4-5-20250929`  |  Provider: `anthropic`
- Prompt: `assignment_v2` (hash `8b0d95a4596e`)
- Code commit: `c91b02d7fd6e2acc3ad9d2ce056fcb9597ca241d`
- Cases run: 8  |  Schema-valid outputs: 8/8
- Automatic hard failures: 0/8
- Human intervention time logged: 8.0 minutes across 2 events
- Estimated model spend this run: $0.4637

## Failure analysis: three representative baseline failures

All three original outputs are preserved unmodified at `runs/baseline-aug17/outputs/<case_id>.original.txt`.

**NYDEV-001 -- combined failure mode.** `evidence_checklist`, `strengths`, and `weaknesses` were returned as arrays of objects (e.g. `{"priority": 1, "item": "..."}`) instead of the required arrays of plain strings, and several `citations[].cite` values referenced packet sections rather than fact IDs (e.g. `"patient_profile.age_range, patient_profile.gender"`), which does not match the required single-bare-token pattern. Ten schema errors total.

**NYDEV-002 -- citation-only failure, descriptive field names.** All sections had the correct shape; every schema error was a citation format violation, and every one of them cited a packet section name instead of a fact/history/evidence ID (e.g. `"denial_rationale field in case packet"`, `"jurisdiction field in case packet"`). 5 schema errors, all the same root cause.

**NYDEV-008 -- citation-only failure, bundled IDs.** The cleanest and smallest failure: only 3 schema errors, all from bundling multiple valid IDs into one citation string (e.g. `"F002, H001"`) or citing a non-ID field (`"source.public_case_number"`) instead of splitting into separate citation entries.

All three traced back to the same root cause: `assignment_v1` described these fields in prose without specifying their exact machine-parseable shape, unlike `procedural_route` and `outcome_estimate`, which spelled out their JSON shape inline. `assignment_v2` closed this gap by making the shape and citation-token rules explicit, which resolved all three failure types with zero other prompt changes.

## Recommendation

**Proceed**, with the next experiment scoped narrowly. The `v2` revision demonstrates that this class of failure (prompt underspecifying output format) is cheap to find and cheap to fix once a real baseline exists -- exactly what this week's harness was built to enable.

**Single highest-value next experiment:** test whether `outcome_estimate.confidence_0_to_1` is actually calibrated to case-specific evidence strength, or is systematically anchored to categories of information (plan-specific formulary/step-therapy details) that are structurally unavailable in every `closed_book` case regardless of how strong the packet's own evidence is. This was flagged in `INT-0002` during review: in NYDEV-004, the hidden answer key shows `missing_or_weak_evidence: []` (nothing missing) and the case was overturned, yet the model still reported `too_uncertain` at 0.4 confidence for reasons dominated by unknowable plan details rather than case-specific weakness. If confidence converges toward "too_uncertain" regardless of case strength, it fails the Section 10 "calibrated confidence" rubric dimension in a way structural scoring alone won't catch. A `v3` prompt hypothesis instructing the model to weight confidence primarily on case-specific evidence completeness, with plan-specific unknowns treated as a fixed caveat rather than a fresh per-case uncertainty source, is the next single controlled revision worth running against the same 8 dev cases.

## Limitations

Public external-appeal/IMR decisions are a curated, already-decided subset of the full consumer journey. They are strongest for medical-necessity denials and do not represent out-of-network or billing disputes, which typically require an EOB, itemized bill, and full plan document not present in these public records. Sample sizes this week (6-10 development cases, 2-3 challenge cases) are far too small to support a real-world efficacy claim; this report measures engineering readiness (schema validity, leakage control, structural completeness) rather than appeal-drafting quality, which remains provisional pending expert review.
