"""Read/write helpers for a job's CV template choice.

Convention: each job output folder may contain ``cv_template_choice.json``
with a single field ``{"template": "a"|"b"|"c"}``. If the file is missing or
malformed, the choice defaults to ``"a"``. The file is consumed by both the
Flask UI (for preview and button state) and the v1 ``render_approved.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

CHOICE_NAME = "cv_template_choice.json"
VALID = ("a", "b", "c")
DEFAULT = "a"


def get_choice(output_folder: str | Path) -> str:
    path = Path(output_folder) / CHOICE_NAME
    if not path.is_file():
        return DEFAULT
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return DEFAULT
    choice = str(data.get("template", DEFAULT)).lower()
    return choice if choice in VALID else DEFAULT


def set_choice(output_folder: str | Path, choice: str) -> str:
    normalised = str(choice).lower()
    if normalised not in VALID:
        raise ValueError(
            f"template choice must be one of {VALID}, got {choice!r}"
        )
    folder = Path(output_folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / CHOICE_NAME
    path.write_text(
        json.dumps({"template": normalised}, indent=2) + "\n",
        encoding="utf-8",
    )
    return normalised
