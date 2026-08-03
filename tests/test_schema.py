"""Proves: a clean checkout's schema validator accepts the good synthetic
fixture and rejects the bad one, with specific, actionable error messages.
"""
from pathlib import Path

from rebelan_eval import schema_validate

FIXTURES = Path(__file__).parent / "fixtures"


def test_all_five_schemas_are_self_consistent():
    for name in schema_validate.SCHEMA_FILES:
        validator = schema_validate.load_validator(name)
        assert validator is not None


def test_valid_synthetic_packet_passes():
    result = schema_validate.validate_file("case_packet", FIXTURES / "synthetic_valid_packet.json")
    assert result.valid, result.errors


def test_invalid_synthetic_packet_fails():
    result = schema_validate.validate_file("case_packet", FIXTURES / "synthetic_invalid_packet.json")
    assert not result.valid
    # It should fail on multiple independent grounds, not just one lucky field.
    assert len(result.errors) >= 3, result.errors


def test_invalid_packet_flags_wrong_track_enum():
    result = schema_validate.validate_file("case_packet", FIXTURES / "synthetic_invalid_packet.json")
    joined = " ".join(result.errors)
    assert "track" in joined


def test_valid_synthetic_answer_key_passes():
    result = schema_validate.validate_file("answer_key", FIXTURES / "synthetic_valid_answer_key.json")
    assert result.valid, result.errors


def test_model_output_schema_rejects_unknown_fields():
    good = {
        "case_id": "NYDEV-000",
        "run_id": "test-run",
        "plain_language_explanation": "x",
        "missing_information_questions": ["x"],
        "evidence_checklist": ["x"],
        "strengths": ["x"],
        "weaknesses": ["x"],
        "recommended_strategy": "x",
        "draft_appeal": "x",
        "procedural_route": {"determinable": False, "details": "cannot be determined"},
        "outcome_estimate": {"estimate": "too_uncertain", "confidence_0_to_1": 0.4, "reasons": "x"},
        "verification_items": ["x"],
        "citations": [],
        "explicit_unknowns": ["x"],
        "safety_escalation_flags": [],
    }
    assert schema_validate.validate("model_output", good).valid

    bad = dict(good)
    bad["unexpected_field"] = "should not be allowed"
    result = schema_validate.validate("model_output", bad)
    assert not result.valid


def test_intervention_schema_bounds_severity():
    base = {
        "intervention_id": "INT-0001",
        "run_id": "test-run",
        "case_id": "NYDEV-000",
        "stage": "evidence_analysis",
        "actor_role": "student_reviewer",
        "category": "factual_correction",
        "severity": 2,
        "minutes": 5.5,
        "original": "x",
        "corrected": "y",
        "reason": "z",
        "automatable": "yes",
        "ai_work_preserved": "80%",
    }
    assert schema_validate.validate("intervention", base).valid

    too_high = dict(base, severity=9)
    assert not schema_validate.validate("intervention", too_high).valid
