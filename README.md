# rebelan-eval

A reproducible, leakage-resistant evaluation harness for an AI-led
health-insurance appeals workflow. Built for Rebelan.ai's one-week trial
assignment; the original assignment text is preserved verbatim in
`docs/assignment_source.md` for reference.

This measures **engineering readiness** — schema validity, outcome-leakage
control, structural completeness, reproducibility — for an AI model asked to
analyze health-insurance denial cases. It does **not** claim the model's
appeal drafts are medically or legally correct; that judgment is explicitly
reserved for an insurance-appeals expert (see "Scope" below).

## Quick start

```bash
git clone <this-repo> && cd rebelan-eval
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # fill in ANTHROPIC_API_KEY

pytest                                  # full test suite
eval validate-cases                     # schema/ID/provenance checks
eval check-leakage                      # outcome-leakage scan
eval run --set ny_dev --condition closed_book --prompt assignment_v1
eval score-structural --run-id <run_id-printed-above>
eval open-review --run-id <run_id>
eval build-report --run-id <run_id>
```

No API key yet? Everything except real model calls works with
`--provider offline_fixture`, which returns a deterministic, schema-valid
placeholder response so you can exercise the full pipeline for free:

```bash
eval run --set ny_dev --condition closed_book --prompt assignment_v1 --provider offline_fixture
```

## This week's results

- **Baseline** (`runs/baseline-aug17`, prompt `assignment_v1`, 8 real NY dev cases, `closed_book`): 0/8 schema-valid, 7/8 automatic hard failure (`fabricated_citation`). Root cause: the prompt didn't specify the exact JSON shape for `evidence_checklist`/`strengths`/`weaknesses`, or the exact citation-token format.
- **Revision** (`runs/v2-aug18`, prompt `assignment_v2`, same 8 cases): 8/8 schema-valid, 0/8 hard failure, after one single, documented prompt fix.
- Full comparison: `reports/baseline-aug17_v2-aug18_report.md`. Prioritized next steps: `reports/backlog.md`.
- 2 real interventions logged during a light review of `v2-aug18` against hidden answer keys: `runs/v2-aug18/interventions.jsonl`.
- California challenge set intentionally not run this week — see backlog item 2.

## Commands

| Command | What it does |
|---|---|
| `eval validate-cases [--split ny_dev]` | Validates schemas, IDs, provenance, split rules, and file placement |
| `eval check-leakage [--split ny_dev]` | Scans packets, filenames, and metadata for answer-key fields/cues |
| `eval run --set <split> --condition closed_book --prompt assignment_v1` | Executes a split with a frozen prompt; never overwrites a prior run |
| `eval score-structural --run-id <id>` | Objective checks only — schema validity, citation resolution, forbidden claims, leakage |
| `eval open-review --run-id <id>` | After run lock: assembles original output + hidden key + rubric template per case |
| `eval log-intervention --run-id <id> ...` | Appends one human-correction event to `runs/<id>/interventions.jsonl` |
| `eval build-report --run-id <id> [--run-id <id> ...]` | Generates `reports/*_summary.csv` and `reports/*_report.md` |
| `eval verify-reproduction --run-id <id>` | Reports what produced a run and what "reproducible" means for a hosted LLM |

## Architecture

```
schemas/     five JSON Schemas (Draft 2020-12) — the data contracts
prompts/     frozen prompt text, version-controlled, hashed into every run manifest
cases/<split>/blinded/       pre-decision-only packets — the ONLY thing the runner may read
restricted/<split>_answer_keys/   hidden answers — the runner must NEVER read these
sources/     source manifest + selection log for case provenance
src/rebelan_eval/
  ingest/allowlist.py    isolation boundary (two independent enforcement layers)
  ingest/leakage.py      outcome-leakage scanning
  run/runner.py          frozen runner: build prompt -> isolation/leakage check -> model call -> immutable save
  run/model_providers.py pluggable model interface (anthropic | offline_fixture)
  score/structural.py    automatic, objective scoring only
  report/build_report.py generates CSV + Markdown from run artifacts, never hand-typed numbers
  cli.py                 the `eval` command group
tests/       pytest suite: schema, leakage, isolation, structural scoring
runs/<run_id>/            manifest.json, outputs/ (immutable original + validated), scores/, interventions.jsonl
reports/     generated summary.csv + human-readable report
```

### The isolation boundary, precisely

`restricted/` holds the hidden answer keys. The runner is only allowed to
read `cases/**/blinded/`, `prompts/`, and `schemas/`
(`paths.RUNNER_READABLE_ROOTS`). This is enforced twice:

1. `ingest.allowlist.read_allowlisted()` — every runner code path that reads
   a case file goes through this and raises `IsolationViolation` for
   anything outside the allowlist.
2. `ingest.allowlist.RestrictedAccessGuard` — a context manager that
   monkeypatches `open`/`Path.open` for the duration of the
   build-prompt-through-model-call sequence, so even an accidental read of
   `restricted/` from anywhere in that call stack is blocked before it
   reaches disk.

Per the assignment's "automatic hard failure" rule: if either layer would
trigger, the run stops **before** any model call, and `eval run` exits 2.

`tests/test_answer_isolation.py` proves both layers, including one test
that points at a path that doesn't even exist on disk, to prove the block
happens from path inspection alone rather than as a side effect of a
missing file.

## Data sources

- **New York development corpus** — NY DFS External Appeals Database
  (https://www.dfs.ny.gov/complaints/file_external_appeal). Public
  external-appeal decisions, adult non-urgent Rx medical-necessity denials,
  2021-2025. See `sources/manifest.csv` and `sources/selection_log.md` for
  exactly which cases and why (including rejected candidates).
- **California challenge corpus (locked)** — CA DMHC Independent Medical
  Review database
  (https://www.dmhc.ca.gov/fileacomplaint/independentmedicalreviewandcomplaintreports.aspx).
  2025-2026 decisions, opened only after the repository was tagged as the
  frozen baseline. Never used to tune prompts or rules.

Both are official, government-run, already-redacted public decision
databases — no PHI, no scraping beyond individually viewing and manually
transcribing public decision pages (Section 3.1 explicitly disallows bulk
scraping this week).

## Privacy & security

- No names, DOB, addresses, member IDs, or other direct identifiers are
  collected — see `patient_profile` in `schemas/case_packet.schema.json`
  (generalized age range + diagnosis summary only).
- `.env` (real API keys) is git-ignored; `.env.example` lists variable names
  only.
- Hidden answer keys live only under `restricted/`, which the model runner
  cannot read (see above).

## Known limitations

- **Isolation is in-process, not OS-level.** `RestrictedAccessGuard`
  monkeypatches Python's own `open`. It stops accidental/careless reads from
  this codebase; it would not stop a determined attacker with code-execution
  access to the same process. Production hardening would run the model-call
  step in a separate OS user, container, or subprocess with no filesystem
  access to `restricted/` at all.
- **Hosted LLM output is not bit-reproducible.** `eval verify-reproduction`
  reports what *is* pinned (code commit, prompt hash, schema versions, model
  id) — not byte-identical output. See that command's output for the exact
  caveat.
- **Sample sizes this week are too small for an efficacy claim.** 6-10
  development cases and 2-3 challenge cases test the measurement machinery,
  not real-world performance. The generated report says this explicitly.
- **Public IMR/external-appeal decisions are a curated, already-decided
  subset.** They're strongest for medical-necessity denials; out-of-network
  and billing tracks are schema-ready but intentionally unpopulated this
  week (see `ASSUMPTIONS.md`).
- **`controlled_retrieval` and `open_web` conditions are interface-only.**
  `eval run --condition controlled_retrieval` raises `NotImplementedError`
  by design — Section 9 reserves those for when curated approved sources
  exist.

## How to add a case

1. Pick a candidate decision from an approved source (Section 3). Log it —
   accepted or rejected — in `sources/selection_log.md`.
2. Extract the **full** record into `restricted/<split>_answer_keys/<CASE_ID>.json`
   first (matches `schemas/answer_key.schema.json`).
3. From that, hand-author the blinded packet at
   `cases/<split>/blinded/<CASE_ID>.json` (matches
   `schemas/case_packet.schema.json`) using **only** pre-decision facts.
4. Run `eval check-leakage --split <split>` and have a second person (or a
   fresh AI session that only sees the blinded packet) review for leakage.
5. Run `eval validate-cases --split <split>` before committing.

## Report

See `reports/*_report.md` after running `eval build-report`. Structural
metrics are automated; any rubric score is labeled
`provisional—expert review required` and is not a substitute for an
appeals expert's review, per Section 10.

## Expenses

Model API spend is tracked per-run in `runs/<run_id>/manifest.json`
(`total_estimated_cost_usd`, using the public per-token pricing table in
`run/model_providers.py`). Cumulative spend across the week is summarized
in the final report.

## Status

Baseline and v2 are both real, frozen, tagged, and pushed -- see "This week's results" above. `docs/day2_review_notes.md` and the git tags `day1-schemas` / `day3-smoke-offline` document the earlier build stages; the step-by-step walkthrough that used to live in this section is complete, and its outcome is reflected in the tagged run history (`baseline-aug17`, `v2-aug18`) rather than repeated here.

## Backlog

See `reports/backlog.md` for the prioritized next-steps list, written after this week's real baseline and v2 runs surfaced an actual recurring failure pattern -- not a pre-results guess.
