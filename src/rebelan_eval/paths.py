"""Central path constants. Every module that touches the filesystem should
import these instead of hardcoding relative paths, so the isolation boundary
in ingest/allowlist.py has exactly one source of truth to defend.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SCHEMAS_DIR = REPO_ROOT / "schemas"
PROMPTS_DIR = REPO_ROOT / "prompts"
CASES_DIR = REPO_ROOT / "cases"
RESTRICTED_DIR = REPO_ROOT / "restricted"
SOURCES_DIR = REPO_ROOT / "sources"
RUNS_DIR = REPO_ROOT / "runs"
REPORTS_DIR = REPO_ROOT / "reports"
TESTS_DIR = REPO_ROOT / "tests"

# The ONLY directories the model runner process is allowed to read case data
# from. Anything under RESTRICTED_DIR must never appear here.
RUNNER_READABLE_ROOTS = (
    CASES_DIR / "ny_dev" / "blinded",
    CASES_DIR / "ny_validation" / "blinded",
    CASES_DIR / "ca_challenge" / "blinded",
    PROMPTS_DIR,
    SCHEMAS_DIR,
)

SPLIT_DIRS = {
    "ny_dev": CASES_DIR / "ny_dev" / "blinded",
    "ny_validation": CASES_DIR / "ny_validation" / "blinded",
    "ca_challenge": CASES_DIR / "ca_challenge" / "blinded",
}

ANSWER_KEY_DIRS = {
    "ny_dev": RESTRICTED_DIR / "ny_dev_answer_keys",
    "ny_validation": RESTRICTED_DIR / "ny_validation_answer_keys",
    "ca_challenge": RESTRICTED_DIR / "ca_challenge_answer_keys",
}
