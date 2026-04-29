"""Read/save/reset for ``config/keywords_override.json``.

Override semantics: each top-level key names a cluster from
``config.keywords.KEYWORDS_BY_CLUSTER``; the value is the keyword list that
should replace the default list for that cluster. Clusters not mentioned in
the override file keep their hardcoded defaults.

Validation rejects malformed input, non-string keywords, empty strings,
and case-insensitive duplicates within the same cluster. Cluster names not
present in ``KEYWORDS_BY_CLUSTER`` are returned as warnings (non-blocking)
so an operator can stage a future cluster without losing their work.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

from config.keywords import KEYWORDS_BY_CLUSTER

OVERRIDE_PATH = Path("config") / "keywords_override.json"
EXAMPLE_PATH = Path("config") / "keywords_override.example.json"


def has_edit() -> bool:
    return OVERRIDE_PATH.is_file()


def get_text() -> Tuple[str, bool]:
    """Return ``(pretty_json_text, is_edited)``.

    Reads the live override file when present; otherwise returns ``"{}"``
    so the editor is empty rather than overwhelming the user with the full
    default keyword list.
    """
    if OVERRIDE_PATH.is_file():
        return _read_pretty(OVERRIDE_PATH), True
    return "{}", False


def validate(text: str) -> Tuple[bool, str | None, list[str]]:
    """Validate the textarea contents.

    Returns ``(ok, error_message, warnings)``. ``warnings`` is non-empty
    when the override mentions cluster names that don't exist in the
    pipeline's defaults; these are flagged but accepted.
    """
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return False, f"JSON parse error: {exc.msg} (line {exc.lineno}, column {exc.colno})", []

    if not isinstance(parsed, dict):
        return False, "Top-level value must be an object whose keys are cluster names.", []

    warnings: list[str] = []
    for cluster_name, kw_list in parsed.items():
        if not isinstance(kw_list, list):
            return False, f"{cluster_name} must be an array of strings.", []

        seen: dict[str, str] = {}
        for index, keyword in enumerate(kw_list):
            if not isinstance(keyword, str):
                return (
                    False,
                    f"{cluster_name}[{index}] must be a string.",
                    [],
                )
            stripped = keyword.strip()
            if not stripped:
                return (
                    False,
                    f"{cluster_name}[{index}] is empty.",
                    [],
                )
            normalised = stripped.lower()
            if normalised in seen:
                return (
                    False,
                    f"Duplicate keyword in {cluster_name}: {stripped!r}.",
                    [],
                )
            seen[normalised] = stripped

        if cluster_name not in KEYWORDS_BY_CLUSTER:
            warnings.append(cluster_name)

    return True, None, warnings


def save(text: str) -> Tuple[bool, str | None, list[str]]:
    """Validate then persist ``text`` to ``OVERRIDE_PATH``.

    Returns ``(ok, error_or_none, warnings)``. Warnings are surfaced even
    on success so the caller can show them in the feedback area.
    """
    ok, error, warnings = validate(text)
    if not ok:
        return False, error, warnings

    parsed = json.loads(text)
    OVERRIDE_PATH.parent.mkdir(parents=True, exist_ok=True)
    OVERRIDE_PATH.write_text(
        json.dumps(parsed, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return True, None, warnings


def reset() -> bool:
    if OVERRIDE_PATH.is_file():
        OVERRIDE_PATH.unlink()
        return True
    return False


def _read_pretty(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except Exception:
        return raw
