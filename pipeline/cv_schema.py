"""Lightweight structured-CV schema helpers.

The new CV contract uses structured JSON with arrays for repeating sections.
This module provides a stable empty shape, a normaliser that coerces partial
or messy data into that shape, and a validator that reports structural issues
without raising.

Design rules:

- Never invent content. Missing values become empty strings or empty lists.
- Drop ``None`` values rather than rendering "None".
- No external dependencies (no Pydantic). Plain dicts and lists only.
"""

from __future__ import annotations

from typing import Any

IDENTITY_FIELDS = ("name", "title", "location", "phone", "email", "linkedin")

STRING_FIELDS = ("objective",)

LIST_OF_STRINGS_FIELDS = ("certifications", "skill_tags", "languages")

EDUCATION_FIELDS = ("institution", "subline", "dates", "qualification")
PROJECT_FIELDS = ("title", "stack")
LEADERSHIP_FIELDS = ("role", "org", "dates")
EXPERIENCE_FIELDS = ("role", "company", "dates")
SKILLS_COLUMN_FIELDS = ("heading",)


def empty_cv_content() -> dict:
    """Return a fresh, fully-shaped empty CV content dict."""
    return {
        "identity": {field: "" for field in IDENTITY_FIELDS},
        "objective": "",
        "education": [],
        "certifications": [],
        "projects": [],
        "leadership": [],
        "experience": [],
        "skills_columns": [],
        "skill_tags": [],
        "languages": [],
    }


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple)):
        return [_as_str(item) for item in value if item is not None]
    return [_as_str(value)]


def _normalize_object_array(
    value: Any, string_fields: tuple[str, ...], bullets_key: str = "bullets"
) -> list[dict]:
    if not isinstance(value, (list, tuple)):
        return []
    result: list[dict] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        item: dict[str, Any] = {
            field: _as_str(entry.get(field)) for field in string_fields
        }
        if bullets_key is not None:
            item[bullets_key] = _as_str_list(entry.get(bullets_key))
        result.append(item)
    return result


def normalize_cv_content(data: dict) -> dict:
    """Coerce ``data`` into the structured CV shape.

    Absent strings become "", absent arrays become [], ``None`` values are
    dropped. Object arrays keep only known string fields plus a normalised
    ``bullets`` (or ``details`` for education) list. Never invents content.
    """
    if not isinstance(data, dict):
        return empty_cv_content()

    result = empty_cv_content()

    identity_in = data.get("identity")
    if isinstance(identity_in, dict):
        result["identity"] = {
            field: _as_str(identity_in.get(field)) for field in IDENTITY_FIELDS
        }

    for field in STRING_FIELDS:
        result[field] = _as_str(data.get(field))

    for field in LIST_OF_STRINGS_FIELDS:
        result[field] = _as_str_list(data.get(field))

    result["education"] = _normalize_object_array(
        data.get("education"), EDUCATION_FIELDS, bullets_key="details"
    )
    result["projects"] = _normalize_object_array(
        data.get("projects"), PROJECT_FIELDS, bullets_key="bullets"
    )
    result["leadership"] = _normalize_object_array(
        data.get("leadership"), LEADERSHIP_FIELDS, bullets_key="bullets"
    )
    result["experience"] = _normalize_object_array(
        data.get("experience"), EXPERIENCE_FIELDS, bullets_key="bullets"
    )
    result["skills_columns"] = _normalize_object_array(
        data.get("skills_columns"), SKILLS_COLUMN_FIELDS, bullets_key="bullets"
    )

    return result


def validate_cv_content(data: dict) -> list[str]:
    """Return a list of human-readable structural problems with ``data``.

    An empty list means the data is structurally sound. This is advisory: it
    never raises and never mutates the input.
    """
    problems: list[str] = []

    if not isinstance(data, dict):
        return ["cv content must be a JSON object"]

    identity = data.get("identity")
    if identity is not None and not isinstance(identity, dict):
        problems.append("identity must be an object")

    if "objective" in data and not isinstance(data["objective"], (str, type(None))):
        problems.append("objective must be a string")

    array_object_sections = {
        "education": EDUCATION_FIELDS,
        "projects": PROJECT_FIELDS,
        "leadership": LEADERSHIP_FIELDS,
        "experience": EXPERIENCE_FIELDS,
        "skills_columns": SKILLS_COLUMN_FIELDS,
    }
    for section in array_object_sections:
        value = data.get(section)
        if value is None:
            continue
        if not isinstance(value, list):
            problems.append(f"{section} must be a list")
            continue
        for i, entry in enumerate(value):
            if not isinstance(entry, dict):
                problems.append(f"{section}[{i}] must be an object")

    for section in LIST_OF_STRINGS_FIELDS:
        value = data.get(section)
        if value is None:
            continue
        if not isinstance(value, list):
            problems.append(f"{section} must be a list")

    return problems
