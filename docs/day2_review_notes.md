# Day 2 output: what needs Sophia's review before Day 3

The assignment's Day 2 checkpoint calls for the founder to review two
packet/key pairs before the remainder are prepared. Given the one-session
build constraints here, all 8 NY development cases were drafted in one
pass instead -- so please treat **all 8** as needing your review, not just
two, before they're used as the frozen baseline input.

## What to check per case (`cases/ny_dev/blinded/NYDEV-0XX.json` +
`restricted/ny_dev_answer_keys/NYDEV-0XX.json`)

1. Open `sources/raw_snapshots/NYDEV-0XX.txt` (the saved public-page text)
   side by side with the blinded packet.
2. Confirm every `known_facts` / `treatment_or_claim_history` /
   `available_evidence` entry in the packet is something that was actually
   knowable *before* the reviewer's decision (not reasoning introduced only
   to justify the outcome).
3. Confirm the packet contains **no** outcome words or result-revealing
   phrasing (`eval check-leakage --split ny_dev` already passed on all 8,
   but that's a mechanical keyword/phrase scan, not a substitute for your
   read).
4. Confirm the answer key's `reviewer_rationale` and `decisive_facts`
   accurately capture *why* the case was decided the way it was.
5. Once you're satisfied with a case, flip its answer key's
   `approval_status` from `"pending_founder_review"` to `"approved"` and
   set `founder_reviewed: true`.

## Known judgment call to sign off on

`NYDEV-007` and `NYDEV-008` are both Wegovy-for-obesity cases (one upheld,
one overturned) -- kept deliberately as a near-matched pair, but it does
mean the 8-case set isn't maximally diagnosis-diverse. If you'd rather swap
one out, `sources/selection_log.md` lists 9 more candidates that were
surfaced by search but not opened.

## Appeal Type boundary

All 8 cases were filtered to DFS's own "Appeal Type: Medical necessity"
field specifically (as opposed to "Formulary Exception" or
"Experimental/Investigational," which DFS treats as separate categories).
Two candidates were rejected on exactly this basis
(`sources/selection_log.md`). Worth a quick sanity check that this is the
scope you want for `rx_medical_necessity` -- Formulary Exception cases are
arguably in-scope conceptually (they're still about whether a drug is
necessary vs. a formulary alternative) and could be added later as a
documented sub-track if useful.
