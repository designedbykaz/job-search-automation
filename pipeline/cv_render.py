"""Shared Jinja2 render service for structured CVs.

This is the single render path used by every CV output surface:

- ``render_approved.py`` (WeasyPrint PDF for sheet-approved rows)
- ``ui/services/render.py`` (UI "Render PDF" button)
- ``ui/services/preview.py`` (browser live preview)

It loads structured CV JSON, normalises it, applies the chosen template's
manifest (dropping disabled sections and capping array sections to their
``max``), and renders the co-located Jinja2 template.

Template choice mapping is non-invasive: the existing ``cv_template_choice``
service still speaks in ``a``/``b``/``c`` letters. This module maps those to
the new template ids without changing that API.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pipeline import cv_schema
from pipeline.manifest import load_manifest, section_enabled, section_max

LETTER_TO_ID = {"a": "full", "b": "lean", "c": "plain"}
VALID_IDS = ("full", "lean", "plain")
DEFAULT_ID = "plain"

ARRAY_SECTIONS = (
    "education",
    "certifications",
    "projects",
    "leadership",
    "experience",
    "skills_columns",
    "skill_tags",
    "languages",
)
SCALAR_SECTIONS = ("objective",)


def _templates_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "templates"


def resolve_template_id(template_choice_or_id: str | None) -> str:
    """Map a template choice (``a``/``b``/``c`` or ``full``/``lean``/``plain``)
    to a valid template id. Falls back to ``DEFAULT_ID`` for anything unknown.
    """
    if not template_choice_or_id:
        return DEFAULT_ID
    value = str(template_choice_or_id).lower()
    if value in VALID_IDS:
        return value
    return LETTER_TO_ID.get(value, DEFAULT_ID)


def _apply_manifest(cv: dict, manifest: dict) -> dict:
    """Return a copy of ``cv`` with disabled sections removed and array
    sections capped to their manifest ``max``. Scalar sections that are
    disabled are blanked so template conditionals hide them.
    """
    result = dict(cv)

    for section in SCALAR_SECTIONS:
        if not section_enabled(manifest, section):
            result[section] = ""

    for section in ARRAY_SECTIONS:
        if not section_enabled(manifest, section):
            result[section] = []
            continue
        cap = section_max(manifest, section, default=None)
        value = result.get(section)
        if isinstance(value, list) and cap is not None:
            result[section] = value[:cap]

    return result


def _build_environment() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(_templates_dir())),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters.setdefault("join_list", lambda items, sep=", ": sep.join(
        str(i) for i in (items or [])
    ))
    return env


def render_html(cv: dict, template_choice_or_id: str | None) -> str:
    """Render structured CV ``cv`` to HTML using the chosen template.

    ``template_choice_or_id`` accepts the legacy ``a``/``b``/``c`` letters or a
    template id directly. The CV is normalised and trimmed per the template's
    manifest before rendering. Returns the rendered HTML string.
    """
    template_id = resolve_template_id(template_choice_or_id)
    normalised = cv_schema.normalize_cv_content(cv or {})
    manifest = load_manifest(template_id)
    trimmed = _apply_manifest(normalised, manifest)

    context = {"cv": trimmed, "manifest": manifest, **trimmed}

    env = _build_environment()
    template = env.get_template(f"{template_id}/template.html")
    return template.render(**context)
