"""`eval build-report` -- Section 15 report template, generated from run
artifacts only (never hand-typed numbers). Produces:

  reports/<run_id>_summary.csv
  reports/<run_id>_report.md

If multiple run_ids are given, comparisons are grouped by split and never
pooled across unlike sets (Section 5 requirement).
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rebelan_eval.paths import REPORTS_DIR, RUNS_DIR


def _load_run(run_id: str) -> dict[str, Any]:
    run_dir = RUNS_DIR / run_id
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No manifest for run '{run_id}' at {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    scores = {}
    scores_dir = run_dir / "scores"
    if scores_dir.exists():
        for p in scores_dir.glob("*.json"):
            scores[p.stem] = json.loads(p.read_text(encoding="utf-8"))

    interventions = []
    interventions_path = run_dir / "interventions.jsonl"
    if interventions_path.exists():
        for line in interventions_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                interventions.append(json.loads(line))

    return {"manifest": manifest, "scores": scores, "interventions": interventions}


def build_summary_csv(run_ids: list[str], out_path: Path) -> Path:
    rows = []
    for run_id in run_ids:
        data = _load_run(run_id)
        manifest = data["manifest"]
        for case in manifest.get("cases", []):
            case_id = case["case_id"]
            score = data["scores"].get(case_id, {})
            structural = score.get("structural", {})
            hard_fail = score.get("automatic_hard_failure", {})
            rows.append(
                {
                    "run_id": run_id,
                    "split": manifest.get("split"),
                    "condition": manifest.get("condition"),
                    "case_id": case_id,
                    "schema_valid": case.get("schema_valid"),
                    "json_repair_needed": case.get("json_repair_needed"),
                    "structural_all_sections_present": structural.get("all_sections_present"),
                    "structural_citations_resolve": structural.get("citations_resolve"),
                    "structural_leakage_clean": structural.get("leakage_scan_clean"),
                    "automatic_hard_failure": hard_fail.get("failed"),
                    "hard_failure_reasons": ";".join(hard_fail.get("reasons", [])),
                    "rubric_label": score.get("rubric", {}).get("label", ""),
                    "rubric_total": score.get("rubric", {}).get("total"),
                    "latency_seconds": case.get("latency_seconds"),
                    "estimated_cost_usd": case.get("estimated_cost_usd"),
                }
            )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        out_path.write_text("no rows: no runs found\n", encoding="utf-8")
        return out_path
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return out_path


def build_markdown_report(run_ids: list[str], out_path: Path) -> Path:
    lines = ["# Rebelan.ai Evaluation Report", ""]
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append(
        "This report is generated entirely from files under `runs/`. It does not "
        "assert real-world appeal-drafting efficacy; structural metrics are "
        "automated, and all substantive quality claims are "
        "'provisional—expert review required' pending review by an "
        "insurance-appeals expert."
    )
    lines.append("")

    for run_id in run_ids:
        data = _load_run(run_id)
        manifest = data["manifest"]
        cases = manifest.get("cases", [])
        n = len(cases)
        n_schema_valid = sum(1 for c in cases if c.get("schema_valid"))
        n_hard_fail = sum(
            1 for c in cases if data["scores"].get(c["case_id"], {}).get("automatic_hard_failure", {}).get("failed")
        )
        total_minutes = sum(i.get("minutes", 0) for i in data["interventions"])
        total_cost = manifest.get("total_estimated_cost_usd", 0.0)

        lines.append(f"## Run `{run_id}`")
        lines.append("")
        lines.append(f"- Split: `{manifest.get('split')}`  |  Condition: `{manifest.get('condition')}`")
        lines.append(f"- Model: `{manifest.get('model')}`  |  Provider: `{manifest.get('provider')}`")
        lines.append(f"- Prompt: `{manifest.get('prompt_name')}` (hash `{manifest.get('prompt_hash', '')[:12]}`)")
        lines.append(f"- Code commit: `{manifest.get('code_commit')}`")
        lines.append(f"- Cases run: {n}  |  Schema-valid outputs: {n_schema_valid}/{n}")
        lines.append(f"- Automatic hard failures: {n_hard_fail}/{n}")
        lines.append(f"- Human intervention time logged: {total_minutes:.1f} minutes across {len(data['interventions'])} events")
        lines.append(f"- Estimated model spend this run: ${total_cost:.4f}")
        lines.append("")
        if n_hard_fail:
            lines.append("**Hard-failed cases:**")
            for c in cases:
                s = data["scores"].get(c["case_id"], {})
                if s.get("automatic_hard_failure", {}).get("failed"):
                    lines.append(f"- `{c['case_id']}`: {', '.join(s['automatic_hard_failure']['reasons'])}")
            lines.append("")

    lines.append("## Limitations")
    lines.append("")
    lines.append(
        "Public external-appeal/IMR decisions are a curated, already-decided "
        "subset of the full consumer journey. They are strongest for "
        "medical-necessity denials and do not represent out-of-network or "
        "billing disputes, which typically require an EOB, itemized bill, and "
        "full plan document not present in these public records. Sample sizes "
        "this week (6-10 development cases, 2-3 challenge cases) are far too "
        "small to support a real-world efficacy claim; this report measures "
        "engineering readiness (schema validity, leakage control, structural "
        "completeness) rather than appeal-drafting quality, which remains "
        "provisional pending expert review."
    )
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
