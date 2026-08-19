# Backlog — prioritized next steps

Generated 2026-08-19, after `baseline-aug17` and `v2-aug18`. No more than 5 items per Day 5 requirement.

1. **Test an `outcome_estimate` calibration hypothesis (v3).** `INT-0002` (logged during `open-review` on `v2-aug18`) found that confidence scores look anchored to plan-specific details that are structurally unknowable in every `closed_book` case, rather than to case-specific evidence strength — in NYDEV-004 the hidden key shows nothing missing and the case was overturned, yet the model still reported `too_uncertain` at 0.4. Write a `v3` prompt instructing the model to weight confidence primarily on case-specific evidence completeness, rerun the same 8 dev cases, and check whether confidence differentiates better across cases. Highest priority because it's the one finding backed by actual review evidence rather than a guess.

2. **Run the locked California challenge set (2-3 cases).** Deferred this week per Section 1's "if time permits" allowance and `ASSUMPTIONS.md`. Must be prepared by someone other than the prompt editor, and the repo must be frozen/tagged before opening any CA answer key, per Section 3.2 and the non-negotiable NY/CA separation rule.

3. **Full expert rubric review of `v2-aug18`.** Structural scoring (schema validity, citation resolution, forbidden claims, leakage) is automated and complete for all 8 cases; only 2 of 8 got a human open-review pass tonight, and none have real rubric point scores — those require an actual insurance-appeals expert, not a student reviewer, per Section 10.

4. **Implement `controlled_retrieval` with a curated source set.** Currently interface-only (`NotImplementedError` by design). Needs an approved, curated list of plan/policy/government documents before it can run for real, per Section 9.

5. **Populate `out_of_network`/`billing_claim` tracks.** Schema-ready but empty — public IMR/external-appeal decisions are weak sources for these tracks (Section 3.3). Needs either sufficient public records or expert-constructed synthetic scenarios, clearly labeled, to avoid thin/misleading labels.
