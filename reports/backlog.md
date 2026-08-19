# Backlog — prioritized next steps

Generated 2026-08-19, after `baseline-aug17` and `v2-aug18`. No more than 5 items per Day 5 requirement. Supersedes the pre-baseline draft version of this file, which was explicitly written to be revisited once real results existed.

1. **Test an `outcome_estimate` calibration hypothesis (v3).** `INT-0002` (logged during `open-review` on `v2-aug18`) found that confidence scores look anchored to plan-specific details that are structurally unknowable in every `closed_book` case, rather than to case-specific evidence strength — in NYDEV-004 the hidden key shows nothing missing and the case was overturned, yet the model still reported `too_uncertain` at 0.4. Write a `v3` prompt instructing the model to weight confidence primarily on case-specific evidence completeness, rerun the same 8 dev cases, and check whether confidence differentiates better across cases. Highest priority because it's backed by actual review evidence, not a guess.

2. **Run the locked California challenge set (2-3 cases).** The assignment's explicit "final portability check," deferred this week per Section 1's "if time permits" allowance. Must be prepared by someone other than the prompt editor, and the repo must be frozen/tagged before opening any CA answer key, per Section 3.2 and the non-negotiable NY/CA separation rule.

3. **Full expert rubric review of `v2-aug18`, including the `rx_medical_necessity` vs. `Formulary Exception` case-inclusion boundary question.** Structural scoring is automated and complete for all 8 cases; only 2 of 8 got a human open-review pass tonight, and none have real rubric point scores. That review should also resolve the case-inclusion boundary question flagged in `sources/selection_log.md` — both the substantive scoring and the case-selection criteria need expert sign-off before any claim beyond "the software works" is made.

4. **Strengthen the in-process isolation guard before any production or external use.** `RestrictedAccessGuard` (see README "Known limitations") is a tested, documented substitute for real process isolation, not the real thing. Worth OS-level sandboxing — separate user, container, or subprocess with no filesystem access to `restricted/` — before anyone outside this harness's author touches it.

5. **Expand past `rx_medical_necessity` into `out_of_network`/`billing_claim` tracks only with sufficient real records or clearly-labeled expert-constructed synthetic scenarios (Section 3.3).** Do not backfill these tracks with thin public summaries just to have more data.
