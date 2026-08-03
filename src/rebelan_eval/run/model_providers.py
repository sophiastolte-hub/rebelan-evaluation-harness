"""Pluggable model-provider interface.

The assignment evaluates one AI model (this project targets Anthropic's
Claude by default, per prompts/assignment_v1.md). The interface is kept
narrow and provider-agnostic so a second provider can be added without
touching runner.py.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Protocol


@dataclass
class ModelResponse:
    text: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    latency_seconds: float
    estimated_cost_usd: float | None
    raw_stop_reason: str | None = None


class ModelProvider(Protocol):
    name: str

    def generate(self, *, system: str, user: str, max_tokens: int = 4096) -> ModelResponse: ...


# Approximate public per-million-token pricing, used only for the harness's
# own budget tracking (Section: "keep track of expenses"). Update if pricing
# changes; this is NOT read from a live pricing API.
_ANTHROPIC_PRICE_PER_MTOK_USD = {
    "claude-opus-4": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.0},
}


def _estimate_anthropic_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    key = None
    for prefix in _ANTHROPIC_PRICE_PER_MTOK_USD:
        if model.startswith(prefix):
            key = prefix
            break
    if key is None:
        return None
    prices = _ANTHROPIC_PRICE_PER_MTOK_USD[key]
    return (input_tokens / 1_000_000) * prices["input"] + (output_tokens / 1_000_000) * prices["output"]


class AnthropicProvider:
    """Wraps the Anthropic Messages API. Requires ANTHROPIC_API_KEY in env."""

    name = "anthropic"

    def __init__(self, model: str | None = None):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in, "
                "or export it in your shell before running `eval run`."
            )
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "The 'anthropic' package is required. Install project dependencies first."
            ) from e
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model or os.environ.get("EVAL_MODEL", "claude-sonnet-4-5-20250929")

    def generate(self, *, system: str, user: str, max_tokens: int = 4096) -> ModelResponse:
        start = time.monotonic()
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        latency = time.monotonic() - start
        text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
        input_tokens = getattr(response.usage, "input_tokens", None)
        output_tokens = getattr(response.usage, "output_tokens", None)
        cost = None
        if input_tokens is not None and output_tokens is not None:
            cost = _estimate_anthropic_cost(self.model, input_tokens, output_tokens)
        return ModelResponse(
            text=text,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_seconds=latency,
            estimated_cost_usd=cost,
            raw_stop_reason=getattr(response, "stop_reason", None),
        )


class OfflineFixtureProvider:
    """Deterministic offline provider for tests / CI / demos without an API
    key. Returns a syntactically valid model_output JSON so the pipeline
    (schema validation, structural scoring, report generation) can be
    exercised end-to-end without spending money or requiring network access.
    """

    name = "offline_fixture"

    def __init__(self, model: str | None = None):
        self.model = model or "offline-fixture-v1"

    def generate(self, *, system: str, user: str, max_tokens: int = 4096) -> ModelResponse:
        import json
        import re

        case_id_match = re.search(r"case_id\"?\s*[:=]?\s*\"?(NYDEV|NYVAL|CACHAL)-[0-9]{3}", user)
        case_id = case_id_match.group(0).replace('"', "").replace("case_id", "").strip(": ") if case_id_match else "NYDEV-000"
        payload = {
            "case_id": case_id,
            "run_id": "OFFLINE",
            "plain_language_explanation": "[offline fixture] placeholder explanation.",
            "missing_information_questions": ["[offline fixture] what plan document applies?"],
            "evidence_checklist": ["[offline fixture] prior authorization history"],
            "strengths": ["[offline fixture] strength placeholder"],
            "weaknesses": ["[offline fixture] weakness placeholder"],
            "recommended_strategy": "[offline fixture] placeholder strategy",
            "draft_appeal": "[offline fixture] placeholder appeal draft.",
            "procedural_route": {"determinable": False, "details": "Cannot be determined from packet alone."},
            "outcome_estimate": {"estimate": "too_uncertain", "confidence_0_to_1": 0.3, "reasons": "[offline fixture]"},
            "verification_items": ["[offline fixture] verify plan document version"],
            "citations": [],
            "explicit_unknowns": ["[offline fixture] exact plan language unknown"],
            "safety_escalation_flags": [],
        }
        return ModelResponse(
            text=json.dumps(payload),
            model=self.model,
            input_tokens=0,
            output_tokens=0,
            latency_seconds=0.0,
            estimated_cost_usd=0.0,
        )


def get_provider(name: str, model: str | None = None) -> ModelProvider:
    if name == "anthropic":
        return AnthropicProvider(model=model)
    if name == "offline_fixture":
        return OfflineFixtureProvider(model=model)
    raise ValueError(f"Unknown provider '{name}'. Known: anthropic, offline_fixture")
