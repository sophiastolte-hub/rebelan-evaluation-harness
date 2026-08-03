"""Frozen runner: `eval run --set ny_dev --condition closed_book --prompt assignment_v1`

Guarantees this module is responsible for:
  * Loading blinded case packets ONLY through ingest.allowlist.read_allowlisted,
    wrapped in RestrictedAccessGuard for the whole build-prompt-through-model-call
    sequence (Section 12 "Automatic hard failure").
  * Serializing the exact prompt sent to the model and running the leakage
    scan on it before the call is made.
  * Writing an immutable original output per case, plus a run manifest that
    fully identifies what produced it (model/provider id, params, prompt
    hash, code commit, schema versions, timestamp, latency, token/cost,
    case hash, seed if supported).
  * Never overwriting a prior run's outputs -- each run gets its own run_id
    directory under runs/.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rebelan_eval import schema_validate
from rebelan_eval.ingest.allowlist import IsolationViolation, RestrictedAccessGuard, read_allowlisted
from rebelan_eval.ingest.leakage import scan_serialized_payload_against_answer_key
from rebelan_eval.paths import PROMPTS_DIR, REPO_ROOT, RUNS_DIR, SPLIT_DIRS
from rebelan_eval.run.model_providers import get_provider


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except Exception:
        return "unknown (not a git checkout or git unavailable)"


def _schema_versions() -> dict[str, str]:
    versions = {}
    for name, filename in schema_validate.SCHEMA_FILES.items():
        path = schema_validate.SCHEMAS_DIR / filename
        versions[name] = _sha256(path.read_text(encoding="utf-8"))[:12]
    return versions


def _build_prompt(system_prompt: str, packet: dict[str, Any]) -> str:
    return (
        "Below is a blinded case packet. Respond ONLY with a single JSON object "
        "matching the model_output schema described in the system prompt. Do not "
        "include any text outside the JSON object.\n\n"
        f"CASE PACKET:\n{json.dumps(packet, indent=2)}"
    )


def _extract_json(text: str) -> tuple[dict[str, Any] | None, str | None]:
    """Best-effort JSON extraction. Returns (parsed_or_None, error_or_None).
    Original raw text is ALWAYS saved separately -- this is only used to
    populate the validated/repaired copy.
    """
    try:
        return json.loads(text), None
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate), None
        except json.JSONDecodeError as e:
            return None, f"JSON repair attempt failed: {e}"
    return None, "no JSON object found in model output"


def run_set(
    *,
    split: str,
    condition: str,
    prompt_name: str,
    run_id: str,
    provider_name: str = "anthropic",
    model: str | None = None,
    limit: int | None = None,
) -> Path:
    if split not in SPLIT_DIRS:
        raise ValueError(f"Unknown split '{split}'. Known: {sorted(SPLIT_DIRS)}")
    if condition != "closed_book":
        raise NotImplementedError(
            "Only 'closed_book' is implemented for real runs this week. "
            "controlled_retrieval/open_web interfaces exist in schema/prompt design only "
            "(Section 9) and require curated approved sources before use."
        )

    prompt_path = PROMPTS_DIR / f"{prompt_name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    system_prompt = read_allowlisted(prompt_path)
    prompt_hash = _sha256(system_prompt)

    case_dir = SPLIT_DIRS[split]
    case_files = sorted(case_dir.glob("*.json"))
    if limit:
        case_files = case_files[:limit]
    if not case_files:
        raise RuntimeError(f"No case packets found in {case_dir}")

    run_dir = RUNS_DIR / run_id
    outputs_dir = run_dir / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    provider = get_provider(provider_name, model=model)

    manifest: dict[str, Any] = {
        "run_id": run_id,
        "split": split,
        "condition": condition,
        "prompt_name": prompt_name,
        "prompt_hash": prompt_hash,
        "provider": provider.name,
        "model": getattr(provider, "model", model or "unknown"),
        "code_commit": _git_commit(),
        "schema_versions": _schema_versions(),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "cases": [],
        "total_estimated_cost_usd": 0.0,
    }

    for case_path in case_files:
        case_id = case_path.stem
        packet_text = read_allowlisted(case_path)
        packet = json.loads(packet_text)
        case_hash = _sha256(packet_text)

        with RestrictedAccessGuard():
            user_prompt = _build_prompt(system_prompt, packet)

            leak = scan_serialized_payload_against_answer_key(user_prompt, answer_key=None)
            if not leak.clean:
                raise IsolationViolation(
                    f"Pre-call leakage scan failed for {case_id}: {leak.findings}"
                )

            try:
                response = provider.generate(system=system_prompt, user=user_prompt)
            except Exception as e:
                print(f"[run_set] model call failed for {case_id}: {e}", file=sys.stderr)
                continue

        original_path = outputs_dir / f"{case_id}.original.txt"
        original_path.write_text(response.text, encoding="utf-8")

        parsed, repair_error = _extract_json(response.text)
        validated_path = outputs_dir / f"{case_id}.validated.json"
        case_record: dict[str, Any] = {
            "case_id": case_id,
            "case_hash": case_hash,
            "latency_seconds": response.latency_seconds,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "estimated_cost_usd": response.estimated_cost_usd,
            "json_repair_needed": repair_error is not None or response.text.strip() != json.dumps(parsed) if parsed else True,
            "schema_valid": False,
        }
        if parsed is not None:
            parsed.setdefault("run_id", run_id)
            parsed.setdefault("case_id", case_id)
            result = schema_validate.validate("model_output", parsed)
            case_record["schema_valid"] = result.valid
            case_record["schema_errors"] = result.errors
            validated_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
        else:
            case_record["schema_errors"] = [repair_error or "unparseable output"]

        if response.estimated_cost_usd:
            manifest["total_estimated_cost_usd"] += response.estimated_cost_usd

        manifest["cases"].append(case_record)
        print(f"[run_set] {case_id}: schema_valid={case_record['schema_valid']}")

    manifest["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return run_dir
