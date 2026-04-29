"""Read/save/reset for ``config/scrapers.json`` (per-scraper settings).

Mirrors the convention used by ``ui.services.tailored_cv``:
- A live override file (``scrapers.json``) is gitignored and only exists when
  the operator has saved edits via the Run page panel.
- A committed ``scrapers.example.json`` documents the default shape and is
  shown in the editor whenever the live file is absent.

Reset deletes the live file. The example file is never modified.

Validation is server-side and rejects malformed input with a path-style
error (e.g. ``govuk.request_delay must be a positive number``) so the UI
can show a precise message without re-implementing the schema.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

OVERRIDE_PATH = Path("config") / "scrapers.json"
EXAMPLE_PATH = Path("config") / "scrapers.example.json"

REQUIRED_FIELDS = ("request_delay", "user_agent", "enforce_robots")


def has_edit() -> bool:
    return OVERRIDE_PATH.is_file()


def get_text() -> Tuple[str, bool]:
    """Return ``(pretty_json_text, is_edited)``.

    Reads the live override file when present, falling back to the
    committed example. If neither exists (shouldn't happen in a clean
    checkout), returns an empty object.
    """
    if OVERRIDE_PATH.is_file():
        return _read_pretty(OVERRIDE_PATH), True
    if EXAMPLE_PATH.is_file():
        return _read_pretty(EXAMPLE_PATH), False
    return "{}", False


def validate(text: str) -> Tuple[bool, str | None]:
    """Validate the textarea contents.

    Returns ``(ok, error_message)``. On success ``error_message`` is
    ``None``. Top-level keys whose values are not dicts (e.g. a leading
    ``_readme`` string in the example file) are skipped silently so users
    can keep comments around.
    """
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return False, f"JSON parse error: {exc.msg} (line {exc.lineno}, column {exc.colno})"

    if not isinstance(parsed, dict):
        return False, "Top-level value must be an object."

    for name, settings in parsed.items():
        if not isinstance(settings, dict):
            continue

        for field in REQUIRED_FIELDS:
            if field not in settings:
                return False, f"{name}.{field} is required."

        delay = settings["request_delay"]
        if isinstance(delay, bool) or not isinstance(delay, (int, float)) or delay <= 0:
            return False, f"{name}.request_delay must be a positive number."

        user_agent = settings["user_agent"]
        if not isinstance(user_agent, str) or not user_agent.strip():
            return False, f"{name}.user_agent must be a non-empty string."

        enforce_robots = settings["enforce_robots"]
        if not isinstance(enforce_robots, bool):
            return False, f"{name}.enforce_robots must be true or false."

    return True, None


def save(text: str) -> Tuple[bool, str | None]:
    """Validate then persist ``text`` to ``OVERRIDE_PATH``.

    Re-serialises with 2-space indent so the saved file is normalised
    regardless of whatever whitespace the user submitted.
    """
    ok, error = validate(text)
    if not ok:
        return False, error

    parsed = json.loads(text)
    OVERRIDE_PATH.parent.mkdir(parents=True, exist_ok=True)
    OVERRIDE_PATH.write_text(
        json.dumps(parsed, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return True, None


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
