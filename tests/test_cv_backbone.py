"""Phase 1 structural backbone checks for the CV render path.

Covers the required Phase 1 checks:

1. Jinja2 import works.
2. All three manifests load and validate.
3. A structured sample CV renders in ``full``.
4. The same sample renders in ``lean`` with no projects or leadership.
5. Empty arrays do not produce empty headings.
6. ``cv_tailored_edited.json`` overrides ``cv_tailored.json``.
7. Preview injects the overflow detector after render.
8. WeasyPrint renders the full stub to PDF (skipped if WeasyPrint missing).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline import cv_render, cv_schema, manifest
from ui.services import preview, tailored_cv

FIXTURE = Path(__file__).parent / "fixtures" / "cv_tailored_structured_sample.json"


@pytest.fixture
def sample_cv() -> dict:
    with FIXTURE.open(encoding="utf-8") as f:
        return json.load(f)


def test_jinja2_import_works():
    import jinja2  # noqa: F401

    from jinja2 import Environment, FileSystemLoader, select_autoescape  # noqa: F401


@pytest.mark.parametrize("template_id", ["full", "lean", "plain"])
def test_all_manifests_load_and_validate(template_id):
    m = manifest.load_manifest(template_id)
    assert m["id"] == template_id
    assert isinstance(m["sections"], dict)


def test_load_manifest_rejects_wrong_id():
    with pytest.raises(manifest.ManifestError):
        manifest.load_manifest("does-not-exist")


def test_section_helpers():
    m = manifest.load_manifest("full")
    assert manifest.section_enabled(m, "education") is True
    assert manifest.section_enabled(m, "skill_tags") is False
    assert manifest.section_enabled(m, "unknown-section") is False
    assert manifest.section_max(m, "education") == 3
    assert manifest.section_max(m, "objective") is None
    assert manifest.section_max(m, "objective", default=7) == 7


def test_full_renders_all_structural_sections(sample_cv):
    html = cv_render.render_html(sample_cv, "full")
    assert "Kazbek Kandour" in html
    assert "Education" in html
    assert "Projects" in html
    assert "Leadership Experience" in html
    assert "Work Experience" in html
    assert "Professional Skills" in html


def test_lean_omits_projects_and_leadership(sample_cv):
    html = cv_render.render_html(sample_cv, "lean")
    assert "Work Experience" in html
    assert "Projects" not in html
    assert "Leadership Experience" not in html
    assert "Professional Skills" not in html


def test_empty_arrays_produce_no_headings():
    empty = cv_schema.empty_cv_content()
    empty["identity"]["name"] = "Nobody"
    html = cv_render.render_html(empty, "plain")
    assert "Nobody" in html
    assert "Education" not in html
    assert "Work Experience" not in html
    assert "Projects" not in html
    assert "Objective" not in html


def test_manifest_caps_array_sections(sample_cv):
    # lean caps education to 1; the sample has 3 institutions.
    html = cv_render.render_html(sample_cv, "lean")
    assert "University of Leeds" in html
    assert "Harrow School" not in html


def test_letter_choice_maps_to_template_id(sample_cv):
    assert cv_render.resolve_template_id("a") == "full"
    assert cv_render.resolve_template_id("b") == "lean"
    assert cv_render.resolve_template_id("c") == "plain"
    assert cv_render.resolve_template_id(None) == cv_render.DEFAULT_ID
    assert cv_render.resolve_template_id("nonsense") == cv_render.DEFAULT_ID


def test_autoescape_escapes_html(sample_cv):
    sample_cv["identity"]["name"] = "<script>alert(1)</script>"
    html = cv_render.render_html(sample_cv, "full")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_normalize_coerces_partial_data():
    normalised = cv_schema.normalize_cv_content({"identity": {"name": "X"}})
    assert normalised["identity"]["name"] == "X"
    assert normalised["objective"] == ""
    assert normalised["education"] == []
    assert normalised["languages"] == []


def test_validate_reports_structural_problems():
    problems = cv_schema.validate_cv_content({"education": "not-a-list"})
    assert any("education" in p for p in problems)
    assert cv_schema.validate_cv_content(cv_schema.empty_cv_content()) == []


def test_edited_overrides_original(tmp_path, sample_cv):
    folder = tmp_path / "job"
    folder.mkdir()
    (folder / tailored_cv.ORIGINAL_NAME).write_text(
        json.dumps(sample_cv), encoding="utf-8"
    )
    edited = dict(sample_cv)
    edited["identity"] = dict(sample_cv["identity"])
    edited["identity"]["name"] = "Edited Name Wins"
    (folder / tailored_cv.EDITED_NAME).write_text(
        json.dumps(edited), encoding="utf-8"
    )

    data, is_edited = tailored_cv.read_preferred(folder)
    assert is_edited is True
    assert data["identity"]["name"] == "Edited Name Wins"

    html = preview.render_preview_html(folder)
    assert "Edited Name Wins" in html


def test_preview_injects_overflow_after_render(tmp_path, sample_cv):
    folder = tmp_path / "job"
    folder.mkdir()
    (folder / tailored_cv.ORIGINAL_NAME).write_text(
        json.dumps(sample_cv), encoding="utf-8"
    )

    html = preview.render_preview_html(folder, job_id=42)
    assert "cv-preview-overflow" in html
    # Script must come after the rendered body content, before </body>.
    assert html.index("Kazbek Kandour") < html.index("cv-preview-overflow")
    assert html.rstrip().endswith("</html>")


def test_weasyprint_renders_full_stub(tmp_path, sample_cv):
    weasyprint = pytest.importorskip("weasyprint")
    html = cv_render.render_html(sample_cv, "full")
    html_path = tmp_path / "cv_rendered.html"
    pdf_path = tmp_path / "cv_output.pdf"
    html_path.write_text(html, encoding="utf-8")
    weasyprint.HTML(filename=str(html_path)).write_pdf(str(pdf_path))
    assert pdf_path.is_file()
    assert pdf_path.stat().st_size > 0
