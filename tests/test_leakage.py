"""Proves the packet-text and filename/ID leakage scanners catch the
patterns Section 7 calls out, and don't false-positive on clean text."""
import json
from pathlib import Path

from rebelan_eval.ingest.leakage import scan_filenames_and_ids, scan_packet_text

FIXTURES = Path(__file__).parent / "fixtures"


def test_scan_packet_text_flags_outcome_phrases():
    packet = json.loads((FIXTURES / "synthetic_invalid_packet.json").read_text(encoding="utf-8"))
    result = scan_packet_text(packet)
    assert not result.clean
    assert any("overturned" in f for f in result.findings)


def test_scan_packet_text_flags_outcome_encoded_case_id():
    packet = json.loads((FIXTURES / "synthetic_invalid_packet.json").read_text(encoding="utf-8"))
    result = scan_packet_text(packet)
    assert any("case_id" in f and "won" in f for f in result.findings)


def test_scan_packet_text_clean_on_good_fixture():
    packet = json.loads((FIXTURES / "synthetic_valid_packet.json").read_text(encoding="utf-8"))
    result = scan_packet_text(packet)
    assert result.clean, result.findings


def test_scan_filenames_flags_outcome_words():
    result = scan_filenames_and_ids(["cases/ny_dev/blinded/NYDEV-001-overturned.json"])
    assert not result.clean


def test_scan_filenames_clean_on_good_names():
    result = scan_filenames_and_ids([
        "cases/ny_dev/blinded/NYDEV-001.json",
        "cases/ny_dev/blinded/NYDEV-002.json",
    ])
    assert result.clean
