# Backlog (draft, pre-real-results)

Written before any real model call was made against the 8 NY cases, so
this is a build-informed starting point -- not a data-informed one.
**Revisit and reorder this after the real baseline run** (README "What's
left for you to do," step 5) surfaces an actual recurring failure pattern.

1. **Run the real baseline and let Section 12's structural + rubric
   scoring surface the actual top failure mode**, then pick the single v2
   revision the assignment calls for. Everything else on this list is
   speculative until this happens.
2. **Get insurance-appeals expert eyes on the rubric scores and the
   `rx_medical_necessity` vs. `Formulary Exception` boundary decision**
   (see `sources/selection_log.md`) -- both the substantive scoring and the
   case-inclusion criteria need expert sign-off before any claim beyond
   "the software works" is made.
3. **Decide whether `controlled_retrieval` is worth building this
   quarter.** The interface exists (`--condition controlled_retrieval`
   currently raises `NotImplementedError` by design); it needs a curated,
   approved source set (specific plan documents, formulary PDFs) before
   it's meaningful, which is a data-sourcing problem more than a code
   problem.
4. **Strengthen the in-process isolation guard if this moves toward
   production.** `RestrictedAccessGuard` (see README "Known limitations")
   is a tested, documented substitute for real process isolation, not the
   real thing -- worth OS-level sandboxing (subprocess/container with no
   filesystem access to `restricted/`) before any external users touch it.
5. **Expand past `rx_medical_necessity`** into `out_of_network` or
   `billing_claim` tracks only with either clearly sufficient public
   records or expert-constructed synthetic scenarios (Section 3.3) -- do
   not backfill these tracks with thin public summaries just to have more
   data.
