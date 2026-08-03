"""Command-line entrypoint. Installed as `eval` (see pyproject.toml
[project.scripts]). Implements the commands in assignment Section 12.

    eval validate-cases [--split ny_dev]
    eval check-leakage [--split ny_dev]
    eval run --set ny_dev --condition closed_book --prompt assignment_v1
    eval score-structural --run-id <run_id>
    eval open-review --run-id <run_id>
    eval log-intervention --run-id <run_id> ...
    eval build-report --run-id <run_id> [--run-id <run_id> ...]
    eval verify-reproduction --run-id <run_id>
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

from rebelan_eval import schema_validate
from rebelan_eval.ingest.allowlist import IsolationViolation, read_allowlisted
from rebelan_eval.ingest.leakage import scan_filenames_and_ids, scan_packet_text
from rebelan_eval.paths import ANSWER_KEY_DIRS, REPORTS_DIR, RESTRICTED_DIR, RUNS_DIR, SPLIT_DIRS
from rebelan_eval.report.build_report import build_markdown_report, build_summary_csv
from rebelan_eval.run.runner import run_set as _run_set
from rebelan_eval.score.structural import score_structural


@click.group()
def main():
    """Rebelan.ai evaluation harness."""


def _splits_to_check(split: str | None):
    return [split] if split else list(SPLIT_DIRS)


@main.command("validate-cases")
@click.option("--split", default=None, help="ny_dev | ny_validation | ca_challenge (default: all)")
def validate_cases(split: str | None):
    """Validate schemas, IDs, provenance, split rules, and file placement."""
    ok = True
    for s in _splits_to_check(split):
        case_dir = SPLIT_DIRS[s]
        files = sorted(case_dir.glob("*.json"))
        click.echo(f"[{s}] {len(files)} packet(s) in {case_dir}")
        for f in files:
            result = schema_validate.validate_file("case_packet", f)
            if result.valid:
                click.echo(f"  OK   {f.name}")
            else:
                ok = False
                click.echo(f"  FAIL {f.name}")
                for err in result.errors:
                    click.echo(f"       - {err}")
            # split/prefix consistency
            expected_prefix = {"ny_dev": "NYDEV", "ny_validation": "NYVAL", "ca_challenge": "CACHAL"}[s]
            if not f.stem.startswith(expected_prefix):
                ok = False
                click.echo(f"  FAIL {f.name}: filename prefix does not match split '{s}' (expected {expected_prefix}-###)")

        answer_dir = ANSWER_KEY_DIRS[s]
        key_files = sorted(answer_dir.glob("*.json")) if answer_dir.exists() else []
        packet_ids = {f.stem for f in files}
        key_ids = {f.stem for f in key_files}
        missing_keys = packet_ids - key_ids
        orphan_keys = key_ids - packet_ids
        if missing_keys:
            ok = False
            click.echo(f"  FAIL missing answer keys for: {sorted(missing_keys)}")
        if orphan_keys:
            click.echo(f"  WARN answer keys with no matching packet: {sorted(orphan_keys)}")
        for kf in key_files:
            result = schema_validate.validate_file("answer_key", kf)
            if not result.valid:
                ok = False
                click.echo(f"  FAIL {kf.relative_to(RESTRICTED_DIR)}")
                for err in result.errors:
                    click.echo(f"       - {err}")

    if not ok:
        sys.exit(1)
    click.echo("All checks passed.")


@main.command("check-leakage")
@click.option("--split", default=None, help="ny_dev | ny_validation | ca_challenge (default: all)")
def check_leakage(split: str | None):
    """Scan packets, filenames, and metadata for answer-key fields/cues."""
    ok = True
    for s in _splits_to_check(split):
        case_dir = SPLIT_DIRS[s]
        files = sorted(case_dir.glob("*.json"))
        name_result = scan_filenames_and_ids([str(f) for f in files])
        if not name_result.clean:
            ok = False
            for finding in name_result.findings:
                click.echo(f"  FAIL {finding}")
        for f in files:
            packet = json.loads(f.read_text(encoding="utf-8"))
            result = scan_packet_text(packet)
            if result.clean:
                click.echo(f"  OK   {f.name}")
            else:
                ok = False
                click.echo(f"  FAIL {f.name}")
                for finding in result.findings:
                    click.echo(f"       - {finding}")
    if not ok:
        sys.exit(1)
    click.echo("No leakage found.")


@main.command("run")
@click.option("--set", "split", required=True, help="ny_dev | ny_validation | ca_challenge")
@click.option("--condition", default="closed_book", show_default=True)
@click.option("--prompt", "prompt_name", default="assignment_v1", show_default=True)
@click.option("--run-id", default=None, help="Defaults to '<split>-<condition>-<UTC timestamp>'")
@click.option("--provider", default="anthropic", show_default=True, help="anthropic | offline_fixture")
@click.option("--model", default=None, help="Overrides EVAL_MODEL from .env")
@click.option("--limit", default=None, type=int, help="Run only the first N cases (smoke test)")
def run_cmd(split, condition, prompt_name, run_id, provider, model, limit):
    """Execute one split/condition with a frozen prompt. Each invocation
    creates a new run_id directory; prior runs are never overwritten."""
    if run_id is None:
        run_id = f"{split}-{condition}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    try:
        run_dir = _run_set(
            split=split,
            condition=condition,
            prompt_name=prompt_name,
            run_id=run_id,
            provider_name=provider,
            model=model,
            limit=limit,
        )
    except IsolationViolation as e:
        click.echo(f"ISOLATION FAILURE -- run stopped before/at model call: {e}", err=True)
        sys.exit(2)
    click.echo(f"Run complete: {run_dir}")


@main.command("score-structural")
@click.option("--run-id", required=True)
def score_structural_cmd(run_id: str):
    """Run only objective structural checks against a run's validated outputs."""
    run_dir = RUNS_DIR / run_id
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    split = manifest["split"]
    scores_dir = run_dir / "scores"
    scores_dir.mkdir(exist_ok=True)

    for case in manifest.get("cases", []):
        case_id = case["case_id"]
        output_path = run_dir / "outputs" / f"{case_id}.validated.json"
        if not output_path.exists():
            click.echo(f"  SKIP {case_id}: no validated output (schema_valid=False)")
            continue
        model_output = json.loads(output_path.read_text(encoding="utf-8"))
        packet_path = SPLIT_DIRS[split] / f"{case_id}.json"
        packet = json.loads(read_allowlisted(packet_path))
        score = score_structural(model_output, packet)
        (scores_dir / f"{case_id}.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
        status = "HARD FAIL" if score["automatic_hard_failure"]["failed"] else "ok"
        click.echo(f"  {case_id}: {status}")
    click.echo(f"Scores written to {scores_dir}")


@main.command("open-review")
@click.option("--run-id", required=True)
def open_review_cmd(run_id: str):
    """After run lock: assemble a review packet (original output + hidden
    key + rubric template + intervention log stub) per case, for a human
    reviewer to fill in. Never runs before the run is complete/immutable."""
    run_dir = RUNS_DIR / run_id
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    split = manifest["split"]
    review_dir = run_dir / "review"
    review_dir.mkdir(exist_ok=True)

    for case in manifest.get("cases", []):
        case_id = case["case_id"]
        key_path = ANSWER_KEY_DIRS[split] / f"{case_id}.json"
        answer_key = json.loads(key_path.read_text(encoding="utf-8")) if key_path.exists() else None
        original_path = run_dir / "outputs" / f"{case_id}.original.txt"
        original_text = original_path.read_text(encoding="utf-8") if original_path.exists() else None
        score_path = run_dir / "scores" / f"{case_id}.json"
        score = json.loads(score_path.read_text(encoding="utf-8")) if score_path.exists() else None

        review = {
            "case_id": case_id,
            "run_id": run_id,
            "original_model_output": original_text,
            "hidden_answer_key": answer_key,
            "structural_score": score,
            "rubric_to_fill": {
                "label": "provisional—expert review required",
                "reviewer": "",
                "dimensions": {
                    "factual_grounding": {"max_points": 25, "points": None, "notes": ""},
                    "issue_and_denial_analysis": {"max_points": 15, "points": None, "notes": ""},
                    "missing_information_detection": {"max_points": 10, "points": None, "notes": ""},
                    "evidence_strategy": {"max_points": 10, "points": None, "notes": ""},
                    "appeal_draft_usability": {"max_points": 15, "points": None, "notes": ""},
                    "procedure_and_source_applicability": {"max_points": 10, "points": None, "notes": ""},
                    "uncertainty_and_outcome_estimate": {"max_points": 5, "points": None, "notes": ""},
                    "safety_and_escalation": {"max_points": 10, "points": None, "notes": ""},
                },
                "total": None,
            },
        }
        (review_dir / f"{case_id}.review.json").write_text(json.dumps(review, indent=2), encoding="utf-8")
    click.echo(f"Review packets written to {review_dir}. Fill in rubric_to_fill and re-save as the score.")


@main.command("log-intervention")
@click.option("--run-id", required=True)
@click.option("--case-id", required=True)
@click.option("--stage", required=True)
@click.option("--actor-role", required=True, type=click.Choice(["student_reviewer", "appeals_expert", "founder"]))
@click.option("--category", required=True)
@click.option("--severity", required=True, type=click.IntRange(0, 4))
@click.option("--minutes", required=True, type=float)
@click.option("--original", required=True)
@click.option("--corrected", required=True)
@click.option("--reason", required=True)
@click.option("--automatable", required=True, type=click.Choice(["yes", "no", "uncertain"]))
@click.option("--ai-work-preserved", required=True)
def log_intervention_cmd(run_id, case_id, stage, actor_role, category, severity, minutes, original, corrected, reason, automatable, ai_work_preserved):
    """Append one intervention event to runs/<run_id>/interventions.jsonl."""
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "interventions.jsonl"
    existing = 0
    if log_path.exists():
        existing = sum(1 for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip())
    event = {
        "intervention_id": f"INT-{existing + 1:04d}",
        "run_id": run_id,
        "case_id": case_id,
        "stage": stage,
        "actor_role": actor_role,
        "category": category,
        "severity": severity,
        "minutes": minutes,
        "original": original,
        "corrected": corrected,
        "reason": reason,
        "automatable": automatable,
        "ai_work_preserved": ai_work_preserved,
    }
    result = schema_validate.validate("intervention", event)
    result.raise_if_invalid("intervention")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
    click.echo(f"Logged {event['intervention_id']} to {log_path}")


@main.command("build-report")
@click.option("--run-id", "run_ids", multiple=True, required=True)
def build_report_cmd(run_ids):
    """Create CSV/JSON plus a readable Markdown summary."""
    run_ids = list(run_ids)
    tag = "_".join(run_ids)[:80]
    csv_path = REPORTS_DIR / f"{tag}_summary.csv"
    md_path = REPORTS_DIR / f"{tag}_report.md"
    build_summary_csv(run_ids, csv_path)
    build_markdown_report(run_ids, md_path)
    click.echo(f"Wrote {csv_path}")
    click.echo(f"Wrote {md_path}")


@main.command("verify-reproduction")
@click.option("--run-id", required=True)
def verify_reproduction_cmd(run_id: str):
    """Report what produced a run and whether it can be reproduced exactly."""
    run_dir = RUNS_DIR / run_id
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        click.echo(f"No manifest found for run '{run_id}'", err=True)
        sys.exit(1)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    click.echo(json.dumps({
        "run_id": run_id,
        "code_commit": manifest.get("code_commit"),
        "prompt_hash": manifest.get("prompt_hash"),
        "schema_versions": manifest.get("schema_versions"),
        "provider": manifest.get("provider"),
        "model": manifest.get("model"),
        "deterministic": False,
        "note": (
            "Hosted LLM APIs do not guarantee bit-identical outputs for identical "
            "inputs even at temperature 0; provider-side model updates can also "
            "silently change behavior behind a fixed model string. Reproduction "
            "here means: same code commit + same prompt hash + same schema "
            "versions + same model id can be re-run to produce a new run_id "
            "whose structural metrics should be comparable, not byte-identical."
        ),
    }, indent=2))


if __name__ == "__main__":
    main()
