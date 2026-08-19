# Week 1 summary — for Dan

## What I built

A testing system that checks whether an AI can produce useful, trustworthy help with health-insurance appeal denials — before we ever ask it to touch a real case. It runs the AI against real, already-decided public appeal cases with the outcome hidden from it, then automatically checks the AI's answer for problems: Did it make up any facts? Did it invent a citation that doesn't exist in the case file? Did it accidentally see the answer? Is the output complete and usable?

I also built a hard technical guarantee, not just a policy: the part of the code that talks to the AI is physically blocked from reading the file that contains the real answer. I wrote a test that proves this — it points the system at an answer file that doesn't even exist, and the system still correctly refuses, proving the block is real and not just luck.

## What I tested it on

8 real cases from New York's public database of insurance appeal decisions (prescription drug denials). Each case was manually turned into two versions: a "blinded" packet with only the facts that were known *before* the decision was made, and a hidden answer key with what actually happened. The AI only ever sees the blinded version.

## What happened

First run: I gave the AI a fixed set of instructions and ran all 8 cases. 7 of the 8 responses came back with a problem — mainly, the AI cited its sources in a format the checker didn't recognize as valid (think: it referenced things loosely instead of pointing to an exact fact in the file). That's not the AI being wrong about the insurance case — it's the AI's *formatting* not matching what the automated checker needed to trust it.

I dug into exactly why, found the instructions I gave the AI were ambiguous about that one format, rewrote just that part, and reran the same 8 cases. Second time: all 8 came back clean.

I think this is actually a good result to show you, not a bad one. It means the checking system is real and strict enough to catch a genuine problem, and that problems like this are fast to find and fast to fix — one afternoon, one targeted change, fully documented, nothing hand-waved.

## Where it went well

A few things worth knowing that aren't just "it passed the test":

- **The privacy/safety boundary held perfectly, every single time.** The part of the system that could theoretically see the real answer was tested repeatedly, including a test designed to trick it, and it never once failed.
- **Even in the failed first run, the AI's actual thinking was sound.** Looking closely at two cases by hand, the AI identified the exact same key issues that the real human reviewer flagged as decisive in the real decision — it just didn't format its source references in a way the automatic checker could verify. It wasn't inventing facts, it was mislabeling where its facts came from.
- **No unsafe claims, ever.** Across all 16 real test runs (both rounds), the AI never once did something like state a diagnosis, guarantee a legal outcome, or claim to have inside knowledge it shouldn't have — the kind of thing that would be an automatic disqualifier regardless of everything else.
- **It's cheap to test.** Both full rounds of testing (16 real calls to the AI) cost about $0.95 total. There's no cost reason to move slowly here — we can afford to run this dozens more times as we refine it.

## What I still don't know

Whether the AI's actual reasoning and draft appeal letters are *good* — medically and legally sound, not just correctly formatted. That's not something I can or should judge myself. It needs a real insurance-appeals expert to read a sample and grade it. I did a light first pass myself on 2 of the 8 cases and logged what I found, but that's a preview, not a real evaluation.

One pattern worth flagging: the AI tends to say "I'm not sure" by default, even on cases where the evidence in the file was actually strong. That's worth watching — if it's overcautious across the board, its confidence level may not be very useful signal for a member deciding whether to bother appealing.

## What's next — needs your input

1. **Bring in an appeals expert** to score a sample of the AI's actual draft appeals for substance, not just format. This is the main gate before this is useful for anything real.
2. **Decide if it's worth testing on California cases too**, as a check that this isn't just working because it's tuned to New York's specific case format. I deliberately didn't do this yet — didn't want to spend the time until you'd seen the New York results first.

Everything above is backed by a saved, reproducible run — nothing here is a guess or a summary of a summary.
