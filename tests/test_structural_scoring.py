"""Proves score.structural is objective: it catches fabricated citations,
forbidden claims, and empty sections without ever asserting medical/legal
correctness."""
import json
from pathlib import Path

from rebelan_eval.score.structural import score_structural

FIXTURES = Path(__file__).parent / "fixtures"


def _packet():
    return json.loads((FIXTURES / "synthetic_valid_packet.json").read_text(encoding="utf-8"))


def _good_output():
    return {
        "case_id": "NYDEV-000",
        "run_id": "test-run",
        "plain_language_explanation": "Your CGRP inhibitor request was denied for not trying two preferred drugs first.",
        "missing_information_questions": ["What does the plan's step-therapy exception policy say?"],
        "evidence_checklist": ["Prescriber note documenting both trials (E001)"],
        "strengths": ["Adverse reaction to preferred alternative #2 is documented (F002)."],
        "weaknesses": ["No pharmacy claims corroborate the trials."],
        "recommended_strategy": "Request a formulary exception citing the documented adverse reaction.",
        "draft_appeal": "I am appealing the denial because I had an adverse reaction to a preferred alternative (F002).",
        "procedural_route": {"determinable": False, "details": "Plan document not provided; cannot determine deadline."},
        "outcome_estimate": {"estimate": "too_uncertain", "confidence_0_to_1": 0.4, "reasons": "Plan exception criteria unknown."},
        "verification_items": ["Confirm exact plan step-therapy exception language."],
        "citations": [{"claim_ref": "adverse reaction", "cite": "F002"}],
        "explicit_unknowns": ["Exact formulary tier language."],
        "safety_escalation_flags": [],
    }


def test_good_output_has_no_hard_failure():
    score = score_structural(_good_output(), _packet())
    assert score["automatic_hard_failure"]["failed"] is False
    assert score["structural"]["schema_valid"] is True
    assert score["structural"]["citations_resolve"] is True


def test_fabricated_citation_is_hard_failure():
    output = _good_output()
    output["citations"] = [{"claim_ref": "x", "cite": "F999"}]  # doesn't exist in packet
    score = score_structural(output, _packet())
    assert score["automatic_hard_failure"]["failed"] is True
    assert "fabricated_citation" in score["automatic_hard_failure"]["reasons"]


def test_forbidden_claim_is_hard_failure():
    output = _good_output()
    output["draft_appeal"] = "You will win this appeal, guaranteed to win the case."
    score = score_structural(output, _packet())
    assert score["automatic_hard_failure"]["failed"] is True
    assert "unsafe_medical_or_legal_direction" in score["automatic_hard_failure"]["reasons"]


def test_rubric_always_carries_provisional_label():
    score = score_structural(_good_output(), _packet())
    assert score["rubric"]["label"] == "provisional—expert review required"
    assert score["rubric"]["total"] is None
