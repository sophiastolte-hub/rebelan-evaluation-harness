"""Proves the runner process cannot read restricted/ under any of the
mechanisms this harness provides, and that the pre-model-call leakage scan
would catch a key that somehow reached the payload anyway.

This is the single most important test file in the repo: Section 12's
"automatic hard failure" rule depends on it.
"""
import json
from pathlib import Path

import pytest

from rebelan_eval.ingest.allowlist import IsolationViolation, RestrictedAccessGuard, read_allowlisted
from rebelan_eval.ingest.leakage import scan_serialized_payload_against_answer_key
from rebelan_eval.paths import RESTRICTED_DIR, REPO_ROOT

FIXTURES = Path(__file__).parent / "fixtures"


def test_read_allowlisted_rejects_restricted_directory():
    target = RESTRICTED_DIR / "ny_dev_answer_keys" / "does_not_need_to_exist.json"
    with pytest.raises(IsolationViolation):
        read_allowlisted(target)


def test_read_allowlisted_rejects_arbitrary_outside_paths():
    with pytest.raises(IsolationViolation):
        read_allowlisted(Path("/etc/hosts"))


def test_read_allowlisted_accepts_prompt_file():
    # Sanity check the allowlist isn't just rejecting everything.
    prompt_path = REPO_ROOT / "prompts" / "assignment_v1.md"
    if prompt_path.exists():
        text = read_allowlisted(prompt_path)
        assert isinstance(text, str)


def test_restricted_access_guard_blocks_open_of_restricted_file():
    # Deliberately point at a path that does not exist on disk. The guard
    # must raise IsolationViolation from path inspection alone, before the
    # OS ever gets a chance to return FileNotFoundError -- proving this is a
    # real access-control boundary, not just a side effect of the file being
    # missing.
    nonexistent_restricted = RESTRICTED_DIR / "ny_dev_answer_keys" / "does-not-exist-on-disk.json"
    assert not nonexistent_restricted.exists()
    with RestrictedAccessGuard():
        with pytest.raises(IsolationViolation):
            open(nonexistent_restricted, "r", encoding="utf-8")
        with pytest.raises(IsolationViolation):
            nonexistent_restricted.open("r", encoding="utf-8")


def test_restricted_access_guard_allows_non_restricted_reads(tmp_path):
    scratch = tmp_path / "not_restricted.txt"
    scratch.write_text("fine", encoding="utf-8")
    with RestrictedAccessGuard():
        assert open(scratch, encoding="utf-8").read() == "fine"


def test_leakage_scan_catches_answer_key_reaching_payload():
    answer_key = json.loads((FIXTURES / "synthetic_valid_answer_key.json").read_text(encoding="utf-8"))
    # Simulate a bug where the reviewer rationale accidentally ended up in
    # the payload sent to the model.
    poisoned_payload = (
        "CASE PACKET:\n{...}\n\nReviewer notes: "
        + answer_key["reviewer_rationale"]
    )
    result = scan_serialized_payload_against_answer_key(poisoned_payload, answer_key)
    assert not result.clean
    assert any("reviewer_rationale" in f for f in result.findings)


def test_leakage_scan_clean_payload_passes():
    answer_key = json.loads((FIXTURES / "synthetic_valid_answer_key.json").read_text(encoding="utf-8"))
    clean_payload = "CASE PACKET:\n{\"case_id\": \"NYDEV-000\", \"denial_rationale\": \"step therapy not completed\"}"
    result = scan_serialized_payload_against_answer_key(clean_payload, answer_key)
    assert result.clean


def test_leakage_scan_with_no_answer_key_is_trivially_clean():
    # This is the real runner's normal condition: it never has an answer_key
    # object to compare against in the first place.
    result = scan_serialized_payload_against_answer_key("anything at all", None)
    assert result.clean
