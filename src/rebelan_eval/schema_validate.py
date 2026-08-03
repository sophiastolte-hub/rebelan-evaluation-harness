"""Strict JSON Schema loading and validation for the five data contracts in
schemas/. "Strict" means: every schema sets additionalProperties: false, so
an unknown field is a validation error rather than being silently ignored.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema

from rebelan_eval.paths import SCHEMAS_DIR

# Schemas are authored against Draft 2020-12. Prefer that validator when the
# installed jsonschema library provides it (>=4.18, what a fresh `pip
# install -e ".[dev]"` will pull in). Fall back to jsonschema's best
# available validator otherwise, so the harness still runs on older
# environments. None of these schemas use 2020-12-only keywords
# (unevaluatedProperties, prefixItems, etc.), so validation results are
# equivalent either way -- only $schema/meta-schema strictness differs.
_PreferredValidator = getattr(jsonschema, "Draft202012Validator", None)

SCHEMA_FILES = {
    "case_packet": "case_packet.schema.json",
    "answer_key": "answer_key.schema.json",
    "model_output": "model_output.schema.json",
    "score": "score.schema.json",
    "intervention": "intervention.schema.json",
}


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]

    def raise_if_invalid(self, context: str = "") -> None:
        if not self.valid:
            joined = "\n  - ".join(self.errors)
            prefix = f"{context}: " if context else ""
            raise ValueError(f"{prefix}schema validation failed:\n  - {joined}")


def _load_schema(name: str) -> dict[str, Any]:
    if name not in SCHEMA_FILES:
        raise KeyError(f"Unknown schema '{name}'. Known: {sorted(SCHEMA_FILES)}")
    path = SCHEMAS_DIR / SCHEMA_FILES[name]
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_validator(name: str):
    schema = _load_schema(name)
    validator_cls = _PreferredValidator or jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    return validator_cls(schema)


def validate(name: str, instance: dict[str, Any]) -> ValidationResult:
    validator = load_validator(name)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    if not errors:
        return ValidationResult(valid=True, errors=[])
    messages = []
    for e in errors:
        loc = "/".join(str(p) for p in e.path) or "<root>"
        messages.append(f"{loc}: {e.message}")
    return ValidationResult(valid=False, errors=messages)


def validate_file(name: str, path: Path) -> ValidationResult:
    with open(path, "r", encoding="utf-8") as f:
        try:
            instance = json.load(f)
        except json.JSONDecodeError as e:
            return ValidationResult(valid=False, errors=[f"invalid JSON: {e}"])
    return validate(name, instance)
