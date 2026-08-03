# Rebelan.ai Evaluation Report

Generated: 2026-08-03T00:52:52.712917+00:00

This report is generated entirely from files under `runs/`. It does not assert real-world appeal-drafting efficacy; structural metrics are automated, and all substantive quality claims are 'provisional—expert review required' pending review by an insurance-appeals expert.

## Run `day3-smoke-offline`

- Split: `ny_dev`  |  Condition: `closed_book`
- Model: `offline-fixture-v1`  |  Provider: `offline_fixture`
- Prompt: `assignment_v1` (hash `d1338df83dfd`)
- Code commit: `e464cbd48dc3279a31bb04cde9032ab787927914`
- Cases run: 8  |  Schema-valid outputs: 8/8
- Automatic hard failures: 0/8
- Human intervention time logged: 2.0 minutes across 1 events
- Estimated model spend this run: $0.0000

## Limitations

Public external-appeal/IMR decisions are a curated, already-decided subset of the full consumer journey. They are strongest for medical-necessity denials and do not represent out-of-network or billing disputes, which typically require an EOB, itemized bill, and full plan document not present in these public records. Sample sizes this week (6-10 development cases, 2-3 challenge cases) are far too small to support a real-world efficacy claim; this report measures engineering readiness (schema validity, leakage control, structural completeness) rather than appeal-drafting quality, which remains provisional pending expert review.
