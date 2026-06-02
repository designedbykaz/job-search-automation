"""Dev helper: re-tailor and re-render one existing job from the terminal.

Fills the gap until the UI has a re-tailor / re-render button. It re-runs the
three-call engine for a job already in outputs/_index.json (reading the live
vault, cluster mapping, and template choice), overwrites cv_tailored.json and
its report, then re-renders cv_output.pdf. Run from the repo root.

Usage:
    python retailor.py <substring>                 # re-tailor (API calls) + render
    python retailor.py <substring> --render-only   # re-render existing cv_tailored.json

Example:
    python retailor.py clinical_engineering
    python retailor.py clinical_engineering --render-only
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # ANTHROPIC_API_KEY / CLAUDE_MODEL for the live engine calls

from pipeline import cluster_map
from pipeline.cv_render import resolve_template_id
from pipeline.tailor import (
    tailor_cv,
    _read_template_choice,
    _read_cluster_for_folder,
)
from ui.services.render import render_pdf_for_job

REPO_ROOT = Path(__file__).resolve().parent
INDEX_PATH = REPO_ROOT / "outputs" / "_index.json"


def _find_job(needle: str) -> dict:
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    jobs = index.get("jobs", {})
    items = list(jobs.values()) if isinstance(jobs, dict) else list(jobs)
    matches = [
        j for j in items
        if needle.lower() in str(j.get("slug", "")).lower()
        or needle.lower() in str(j.get("output_folder", "")).lower()
    ]
    if not matches:
        sys.exit(f"No job in the index matches {needle!r}.")
    if len(matches) > 1:
        print(f"{len(matches)} jobs match {needle!r}; using the first:")
        for j in matches:
            print("  -", j.get("output_folder"))
    return matches[0]


def main(needle: str, render_only: bool = False) -> None:
    job = _find_job(needle)
    output_folder = REPO_ROOT / job["output_folder"]
    if not output_folder.is_dir():
        sys.exit(f"Output folder not found: {output_folder}")

    if render_only:
        tailored_path = output_folder / "cv_tailored.json"
        if not tailored_path.is_file():
            sys.exit(f"No cv_tailored.json to render in {output_folder}")
        tailored = json.loads(tailored_path.read_text(encoding="utf-8"))
        print(f"Re-rendering (no API calls): {job.get('title', '')}")
        print(f"  folder : {output_folder}")
    else:
        job_for_tailor = {
            "title": job.get("title", ""),
            "employer": job.get("employer", ""),
            "description": job.get("description", "")
            if isinstance(job.get("description"), str)
            else "\n\n".join(job.get("description") or []),
        }
        print(f"Re-tailoring: {job.get('title', '')}")
        print(f"  folder : {output_folder}")
        print(f"  cluster: {_read_cluster_for_folder(output_folder)}")
        tailored = tailor_cv(job_for_tailor, output_folder)  # overwrites cv_tailored.json

    # Mirror tailor_cv's template precedence so the render matches the tailoring:
    # explicit per-job choice, else the cluster's default template, else plain.
    explicit = _read_template_choice(output_folder)
    cluster_id = _read_cluster_for_folder(output_folder)
    mapping = cluster_map.get_mapping(cluster_id)
    template_id = resolve_template_id(
        explicit if explicit is not None else mapping["default_template"]
    )
    print(f"  template: {template_id}")

    pdf_path = render_pdf_for_job(output_folder, tailored, template_id)
    print(f"\nDone. PDF: {pdf_path}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if len(args) != 1:
        sys.exit("Usage: python retailor.py <slug-or-folder-substring> [--render-only]")
    main(args[0], render_only="--render-only" in flags)
