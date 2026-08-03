"""Outcome-leakage scanning (Section 7).

Two distinct checks, used at two distinct times:

1. `scan_packet_text()` -- run against a blinded case packet BEFORE it is
   committed. Flags decision-revealing vocabulary that should never appear
   in pre-decision-only text (e.g. "the denial was overturned").

2. `scan_serialized_payload_against_answer_key()` -- run against the exact
   serialized request the runner is about to send to the model, immediately
   before the model call (Section 12 "Automatic hard failure": stop before
   any model call). Flags any answer-key field value that leaked into the
   payload -- this catches leakage the vocabulary list misses (e.g. a
   distinctive clinical detail copy-pasted from the reviewer section).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Vocabulary that only makes sense once a decision has been reached. Case
# packets are pre-decision-only, so any of these phrases in a packet is a
# strong leakage signal. Matched case-insensitively as whole phrases.
FORBIDDEN_OUTCOME_PHRASES = [
    "was overturned",
    "was upheld",
    "denial was overturned",
    "denial was upheld",
    "therefore the denial",
    "the appeal was granted",
    "the appeal was denied",
    "reversed the denial",
    "affirmed the denial",
    "the imr determined",
    "the external appeal agent determined",
    "final determination",
    "decision: overturned",
    "decision: upheld",
    "in favor of the member",
    "in favor of the plan",
    "the reviewer concluded that the denial",
]

# Filename/ID fragments that would encode outcome and must never appear in
# any committed file name, directory name, or case_id.
FORBIDDEN_ID_FRAGMENTS = ["won", "lost", "upheld", "overturned", "reversed", "affirmed", "win", "loss"]


@dataclass
class LeakageResult:
    clean: bool
    findings: list[str] = field(default_factory=list)


def scan_packet_text(packet: dict[str, Any]) -> LeakageResult:
    findings: list[str] = []
    blob = _flatten_strings(packet).lower()
    for phrase in FORBIDDEN_OUTCOME_PHRASES:
        if phrase in blob:
            findings.append(f"forbidden outcome phrase found in packet: '{phrase}'")
    case_id = str(packet.get("case_id", ""))
    for frag in FORBIDDEN_ID_FRAGMENTS:
        if frag in case_id.lower():
            findings.append(f"case_id '{case_id}' contains outcome-revealing fragment '{frag}'")
    return LeakageResult(clean=not findings, findings=findings)


def scan_filenames_and_ids(paths: list[str]) -> LeakageResult:
    findings: list[str] = []
    for p in paths:
        lower = p.lower()
        for frag in FORBIDDEN_ID_FRAGMENTS:
            if re.search(rf"(^|[^a-z]){frag}([^a-z]|$)", lower):
                findings.append(f"path '{p}' contains outcome-revealing fragment '{frag}'")
    return LeakageResult(clean=not findings, findings=findings)


def scan_serialized_payload_against_answer_key(
    payload: str, answer_key: dict[str, Any] | None
) -> LeakageResult:
    """Fail-closed pre-model-call check. If an answer_key is available (it
    should NEVER be available to the real runner -- this signature exists so
    tests can prove the scanner catches leakage if it were ever mistakenly
    reachable), verify none of its substantive fields appear in the payload
    about to be sent to the model.
    """
    findings: list[str] = []
    if answer_key is None:
        return LeakageResult(clean=True, findings=[])

    payload_lower = payload.lower()
    sensitive_fields = [
        "actual_outcome",
        "reviewer_rationale",
        "decisive_facts",
        "cited_authorities",
    ]
    for field_name in sensitive_fields:
        value = answer_key.get(field_name)
        for needle in _iter_strings(value):
            needle = needle.strip()
            if len(needle) >= 12 and needle.lower() in payload_lower:
                findings.append(
                    f"answer_key.{field_name} value leaked into runner payload: '{needle[:60]}...'"
                )
    outcome = answer_key.get("actual_outcome")
    if outcome and re.search(rf"\b{re.escape(str(outcome))}\b", payload_lower):
        findings.append(f"answer_key.actual_outcome token '{outcome}' present in runner payload")

    return LeakageResult(clean=not findings, findings=findings)


def _iter_strings(value: Any):
    if value is None:
        return
    if isinstance(value, str):
        yield value
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _iter_strings(v)
    elif isinstance(value, dict):
        for v in value.values():
            yield from _iter_strings(v)


def _flatten_strings(value: Any) -> str:
    return " ".join(_iter_strings(value))
