"""Manual smoke check for the CV structural render backbone.

Renders the structured sample fixture through all three templates and prints a
short report. Optionally writes a PDF for the full template if WeasyPrint is
available. Does not touch the scraper, sheets, or any live data.

Usage:
    python -m scripts.check_cv_render
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline import cv_render, manifest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "cv_tailored_structured_sample.json"


def main() -> int:
    with FIXTURE.open(encoding="utf-8") as f:
        sample = json.load(f)

    for template_id in ("full", "lean", "plain"):
        m = manifest.load_manifest(template_id)
        html = cv_render.render_html(sample, template_id)
        has_projects = "Projects" in html
        has_leadership = "Leadership Experience" in html
        print(
            f"[{template_id}] label={m['label']!r} "
            f"len={len(html)} projects={has_projects} leadership={has_leadership}"
        )

    empty_html = cv_render.render_html({"identity": {"name": "Empty Person"}}, "plain")
    print(
        "[empty] headings hidden: "
        f"education={'Education' not in empty_html} "
        f"experience={'Work Experience' not in empty_html}"
    )

    try:
        from weasyprint import HTML

        out_dir = REPO_ROOT / "outputs" / "_cv_render_check"
        out_dir.mkdir(parents=True, exist_ok=True)
        html = cv_render.render_html(sample, "full")
        html_path = out_dir / "cv_rendered.html"
        pdf_path = out_dir / "cv_output.pdf"
        html_path.write_text(html, encoding="utf-8")
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        print(f"[pdf] wrote {pdf_path} ({pdf_path.stat().st_size} bytes)")
    except Exception as exc:
        print(f"[pdf] skipped: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
