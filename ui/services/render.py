"""Render a tailored CV to PDF using WeasyPrint.

HTML generation is delegated to the shared Jinja2 render service in
``pipeline.cv_render`` so the PDF and preview paths stay in lockstep. This
module keeps the WeasyPrint dependency isolated from the gspread-heavy
``render_approved.py``.
"""
from pathlib import Path

from weasyprint import HTML

from pipeline.cv_render import render_html


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def render_pdf_for_job(output_folder: Path, tailored_cv: dict, template_choice: str) -> Path:
    """Render the chosen CV template as a PDF.
    Writes two files to the output folder:
      - cv_rendered.html (the filled HTML, kept for debugging)
      - cv_output.pdf (the final PDF)
    Returns the path to the PDF.
    """
    filled_html = render_html(tailored_cv, template_choice)
    output_folder.mkdir(parents=True, exist_ok=True)
    rendered_html_path = output_folder / "cv_rendered.html"
    pdf_path = output_folder / "cv_output.pdf"
    rendered_html_path.write_text(filled_html, encoding="utf-8")
    HTML(filename=str(rendered_html_path)).write_pdf(str(pdf_path))
    return pdf_path
