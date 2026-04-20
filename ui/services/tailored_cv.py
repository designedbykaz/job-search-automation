"""Read/write helpers for a job's tailored CV JSON.

Convention, shared with the v1 pipeline at the repo root:

- ``cv_tailored.json`` is the immutable Claude output. The UI never writes it.
- ``cv_tailored_edited.json`` only exists when the user has edited the JSON in
  the UI. When present, it overrides the original for display and for PDF
  rendering in ``render_approved.py``.

Reset deletes the edited file; the original is untouched.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

ORIGINAL_NAME = "cv_tailored.json"
EDITED_NAME = "cv_tailored_edited.json"


def has_edit(output_folder: str | Path) -> bool:
    return (Path(output_folder) / EDITED_NAME).is_file()


def read_preferred(output_folder: str | Path) -> Tuple[dict, bool]:
    """Return ``(data, is_edited)``.

    Prefers the edited file, falls back to the original. If neither exists,
    returns ``({}, False)`` so callers can render an empty editor instead of
    crashing.
    """
    folder = Path(output_folder)
    edited = folder / EDITED_NAME
    if edited.is_file():
        with edited.open("r", encoding="utf-8") as f:
            return json.load(f), True

    original = folder / ORIGINAL_NAME
    if original.is_file():
        with original.open("r", encoding="utf-8") as f:
            return json.load(f), False

    return {}, False


def save_edit(output_folder: str | Path, data: dict) -> Path:
    folder = Path(output_folder)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / EDITED_NAME
    target.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return target


def reset_edit(output_folder: str | Path) -> bool:
    edited = Path(output_folder) / EDITED_NAME
    if edited.is_file():
        edited.unlink()
        return True
    return False
