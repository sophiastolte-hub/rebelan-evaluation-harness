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

## What's left for you to do

Everything through Day 2 is committed and real (8 real NY DFS cases,
schema-validated, leakage-scanned, git-tagged `day1-schemas`). Day 3
onward needs your Anthropic API key and your human judgment calls, which
the assignment requires anyway (Section 12 checkpoints are explicitly
founder/student review points, not automatable). A `day3-smoke-offline`
run is already committed proving the whole pipeline works end to end with
zero spend -- here's the walkthrough to turn it into the real thing:

1. **Review the 8 draft cases.** Read `docs/day2_review_notes.md` first --
   it explains exactly what to check in each `cases/ny_dev/blinded/*.json`
   / `restricted/ny_dev_answer_keys/*.json` pair before trusting them as
   the frozen baseline input. Flip each answer key's `approval_status` to
   `"approved"` once you're satisfied.
2. **Set your API key.** `cp .env.example .env`, fill in
   `ANTHROPIC_API_KEY`.
3. **Run the real baseline** (this is the first step that spends money --
   8 cases, one call each):
   ```bash
   eval run --set ny_dev --condition closed_book --prompt assignment_v1 --run-id baseline-<today's date>
   git add -A && git commit -m "Real baseline run" && git tag baseline-frozen
   ```
   Tagging before you look at aggregate results matters -- Section 8 wants
   the baseline frozen before you know how it did.
4. **Score and review:**
   ```bash
   eval score-structural --run-id baseline-<date>
   eval open-review --run-id baseline-<date>
   ```
   `open-review` writes one `runs/<id>/review/<case>.review.json` per case
   with the original output, the hidden answer key, and a rubric template.
   Fill in `rubric_to_fill`, save it as `runs/<id>/scores/<case>.json`
   (replacing the structural-only version), and log any correction you make
   with `eval log-intervention` (real minutes, real category, real
   severity -- not placeholders like the smoke-test entry).
5. **Pick one revision.** Look for the single largest recurring failure
   pattern across the 8 cases. Write `prompts/assignment_v2.md` with one
   change and a one-paragraph hypothesis at the top of that file. Rerun:
   ```bash
   eval run --set ny_dev --condition closed_book --prompt assignment_v2 --run-id v2-<date>
   ```
   Baseline outputs are never overwritten -- `build-report` can compare
   both run_ids side by side.
6. **Optional: California challenge set.** Only after the repo is tagged
   frozen with v2 locked in. Prepare 2-3 CA DMHC IMR cases the same way as
   Day 2 (answer key first, then blinded packet), ideally with someone
   other than the prompt author preparing the keys. Run once, don't tune
   anything in response.
7. **Final report:**
   ```bash
   eval build-report --run-id baseline-<date> --run-id v2-<date> [--run-id ca-<date>]
   ```
   Then fill in `reports/backlog.md` (drafted for you, needs your
   real-results-informed prioritization) and write the executive
   summary/limitations prose using the Section 15 template.

## Backlog

Draft prioritized backlog in `reports/backlog.md` -- written before any
real model run, so it's a starting point based on what the engineering
build surfaced, not on real failure data. Revisit and reorder it once
step 5 above gives you an actual recurring-failure pattern to point at.
