"""rebelan_eval: reproducible, leakage-resistant AI evaluation harness.

See README.md for the full assignment context. This package intentionally
keeps a hard boundary between:

  * cases/**/blinded/         -- readable by the model runner
  * restricted/**/            -- NEVER readable by the model runner
                                  (see ingest.allowlist)

Any change that blurs that boundary should be treated as a critical bug.
"""

__version__ = "0.1.0"
