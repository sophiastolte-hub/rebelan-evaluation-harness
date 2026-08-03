# Assumptions log — Day 1

Written before any case collection began. This records choices made where
the assignment allowed discretion, plus a few things deliberately **not**
inferred as hidden product requirements.

## Scope choices

- **Language: Python 3.10+.** Strong JSON Schema tooling, easy scripting for
  data collection, and `pytest` is the most common review tool for this kind
  of harness.
- **Model under evaluation: Anthropic Claude**, via the Messages API
  (`ANTHROPIC_API_KEY`). The runner is written behind a `ModelProvider`
  interface (`src/rebelan_eval/run/model_providers.py`) so a second provider
  can be added without touching the runner.
- **Initial case family: adult, non-urgent Rx medical-necessity denials**,
  as the assignment specifies (Section 3.1) — not because any market wedge
  has been chosen, exactly as flagged in the source material.
- **`controlled_retrieval` and `open_web` conditions are interface-only this
  week.** Section 9 says to implement the interface but only run
  closed-book for real; `eval run --condition controlled_retrieval` raises
  `NotImplementedError` rather than silently downgrading to closed-book.
- **`out_of_network` and `billing_claim` tracks are schema-supported but
  unpopulated.** Per Section 3.3, public IMR/external-appeal repositories
  are weak for these tracks; populating them this week would mean either
  thin/misleading labels or fabricated synthetic data presented as real,
  neither of which is acceptable.

## Isolation design

- **The isolation boundary is enforced in-process** (`RestrictedAccessGuard`
  monkeypatches `open`/`Path.open` for the duration of the prompt-build +
  model-call sequence), not via OS-level sandboxing (separate user, container,
  or subprocess with restricted filesystem permissions). A one-week trial
  harness cannot stand up real process isolation credibly; the in-process
  guard is honest about being a *tested, documented* substitute, not
  production-grade defense-in-depth. This is called out again in the README
  "Known limitations" section so it isn't mistaken for something stronger.
- Two independent layers exist on purpose (`read_allowlisted` at call sites,
  `RestrictedAccessGuard` as a blanket net) because a call-site check alone
  only protects code paths that remember to use it.

## Data handling

- **No bulk scraper this week.** Section 3.1 requires manual collection for
  the first 6-10 records and founder confirmation before automating
  collection. Case sourcing this week means a human (with AI drafting
  assistance per the "AI may help with" column) reading DFS decision pages
  directly.
- **Synthetic fixtures are clearly marked** (`"synthetic": true` in the case
  packet schema) and live only in `tests/fixtures/`, never in `cases/`. They
  exist to prove the pipeline works, not to represent real outcomes.

## What was deliberately *not* inferred

- No assumption about which insurer(s), specific drugs, or diagnoses to
  prioritize beyond "prescription-drug medical necessity" — Section 3.1 says
  this family was picked for data availability, not as a product decision.
- No assumption about scoring weights beyond the Section 10 rubric as
  written; the harness stores `max_points` from that table verbatim rather
  than re-deriving them.
- No assumption that this week's small sample (6-10 dev cases, 2-3 challenge
  cases) supports any real-world efficacy claim. The report template
  states this limitation explicitly rather than leaving it implicit.

## Open questions for Dan (per Section 14, to raise if/when they come up)

- Whether "adult" should be enforced as an explicit filter on the DFS search
  UI or verified case-by-case from the decision text (DFS's public search
  does not always expose age directly).
- Preferred severity threshold for what counts as an "urgent safety flag"
  the harness should treat as an automatic hard failure if missed.
