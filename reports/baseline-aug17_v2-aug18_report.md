# Rebelan.ai Evaluation Report

Generated: 2026-08-19T01:24:21.983256+00:00

This report is generated entirely from files under `runs/`. It does not assert real-world appeal-drafting efficacy; structural metrics are automated, and all substantive quality claims are 'provisional—expert review required' pending review by an insurance-appeals expert.

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
- Human intervention time logged: 0.0 minutes across 0 events
- Estimated model spend this run: $0.4637

## Limitations

Public external-appeal/IMR decisions are a curated, already-decided subset of the full consumer journey. They are strongest for medical-necessity denials and do not represent out-of-network or billing disputes, which typically require an EOB, itemized bill, and full plan document not present in these public records. Sample sizes this week (6-10 development cases, 2-3 challenge cases) are far too small to support a real-world efficacy claim; this report measures engineering readiness (schema validity, leakage control, structural completeness) rather than appeal-drafting quality, which remains provisional pending expert review.
