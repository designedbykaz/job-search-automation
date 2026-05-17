"""Render a tailored CV to PDF using WeasyPrint.
This module fills a CV HTML template with tailored JSON data and produces
a PDF using WeasyPrint. The fill loop is duplicated from render_approved.py
deliberately, to keep this service free of gspread imports.
"""
from pathlib import Path

from weasyprint import HTML

_VALID_TEMPLATES = {"a", "b", "c"}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _template_path(template_choice: str) -> Path:
    """Resolve the path to a CV template HTML file by choice letter.
    Falls back to template "c" if the choice is invalid.
    """
    choice = (template_choice or "").lower()
    if choice not in _VALID_TEMPLATES:
        choice = "c"
    return _repo_root() / "templates" / f"cv_template_{choice}.html"


def _fill_template(template_html: str, tailored_cv: dict) -> str:
    """Replace {{KEY}} placeholders with tailored CV values.
    Lists become comma-joined strings to match the v1 render_approved.py behaviour.
    """
    html = template_html
    for key, value in tailored_cv.items():
        placeholder = "{{" + str(key) + "}}"
        if isinstance(value, list):
            value_str = ", ".join(str(item) for item in value)
        else:
            value_str = str(value)
        html = html.replace(placeholder, value_str)
    return html


def render_pdf_for_job(output_folder: Path, tailored_cv: dict, template_choice: str) -> Path:
    """Fill the chosen CV template and render it as a PDF.
    Writes two files to the output folder:
      - cv_rendered.html (the filled HTML, kept for debugging)
      - cv_output.pdf (the final PDF)
    Returns the path to the PDF.
    """
    template_path = _template_path(template_choice)
    template_html = template_path.read_text(encoding="utf-8")
    filled_html = _fill_template(template_html, tailored_cv)
    output_folder.mkdir(parents=True, exist_ok=True)
    rendered_html_path = output_folder / "cv_rendered.html"
    pdf_path = output_folder / "cv_output.pdf"
    rendered_html_path.write_text(filled_html, encoding="utf-8")
    HTML(filename=str(rendered_html_path)).write_pdf(str(pdf_path))
    return pdf_path
