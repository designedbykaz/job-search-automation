"""Template manifest loading and validation.

Each CV template directory under ``templates/<id>/`` carries a co-located
``manifest.json`` that declares section visibility and per-section slot caps.
A section value is one of:

- ``false``            section is disabled (hidden)
- ``true``             section is enabled with no cap
- ``{"max": N, ...}``  section is enabled, capped to N items, plus optional
                       flags such as ``show_stack``

The loader is intentionally lightweight: it validates the obvious mistakes and
otherwise tolerates unknown keys so later phases can extend manifests without
breaking the render path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def _templates_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "templates"


def _manifest_path(template_id: str) -> Path:
    return _templates_dir() / template_id / "manifest.json"


class ManifestError(ValueError):
    """Raised when a manifest is missing or structurally invalid."""


def _validate(manifest: dict, template_id: str) -> None:
    if not isinstance(manifest, dict):
        raise ManifestError(
            f"manifest for {template_id!r} must be a JSON object"
        )

    declared_id = manifest.get("id")
    if declared_id != template_id:
        raise ManifestError(
            f"manifest id {declared_id!r} does not match requested "
            f"template id {template_id!r}"
        )

    sections = manifest.get("sections")
    if not isinstance(sections, dict):
        raise ManifestError(
            f"manifest for {template_id!r} must have a 'sections' object"
        )

    for name, value in sections.items():
        if isinstance(value, bool):
            continue
        if isinstance(value, dict):
            if "max" in value:
                max_val = value["max"]
                if not isinstance(max_val, int) or isinstance(max_val, bool) or max_val <= 0:
                    raise ManifestError(
                        f"section {name!r} in {template_id!r} has invalid "
                        f"'max' {max_val!r}; expected a positive integer"
                    )
            continue
        raise ManifestError(
            f"section {name!r} in {template_id!r} must be true, false, or an "
            f"object; got {type(value).__name__}"
        )


def load_manifest(template_id: str) -> dict:
    """Locate, load, and validate the manifest for ``template_id``.

    Raises ``ManifestError`` if the file is missing or structurally invalid.
    """
    path = _manifest_path(template_id)
    if not path.is_file():
        raise ManifestError(
            f"no manifest found for template {template_id!r} at {path}"
        )
    try:
        with path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as exc:
        raise ManifestError(
            f"manifest for {template_id!r} is not valid JSON: {exc}"
        ) from exc

    _validate(manifest, template_id)
    return manifest


def section_enabled(manifest: dict, section: str) -> bool:
    """Return True if ``section`` is enabled in the manifest.

    A section is enabled when its value is ``true`` or a dict. A missing
    section is treated as disabled.
    """
    sections = manifest.get("sections", {})
    value = sections.get(section)
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        return True
    return False


def section_max(
    manifest: dict, section: str, default: Optional[int] = None
) -> Optional[int]:
    """Return the ``max`` cap for ``section``, or ``default`` if none is set.

    Returns ``default`` when the section is disabled, enabled without a cap
    (``true``), or has no ``max`` key.
    """
    sections = manifest.get("sections", {})
    value = sections.get(section)
    if isinstance(value, dict):
        max_val = value.get("max")
        if isinstance(max_val, int) and not isinstance(max_val, bool) and max_val > 0:
            return max_val
    return default
