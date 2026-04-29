"""Per-scraper settings with operator overrides.

Reads ``config/scrapers.json`` (gitignored) when present and merges any
overrides on top of the hardcoded ``DEFAULTS`` below. Invalid JSON or any
other read error falls back silently to the defaults so a malformed override
file never crashes the pipeline at import time.

The override file is written by the v2 UI's "Scraper config" panel on the
Run page. The committed ``config/scrapers.example.json`` documents the
expected shape for users editing the file by hand.
"""

from __future__ import annotations

import json
from pathlib import Path

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

DEFAULTS: dict[str, dict] = {
    "govuk": {
        "request_delay": 1.5,
        "user_agent": _DEFAULT_USER_AGENT,
        "enforce_robots": True,
    },
    "nhs": {
        "request_delay": 1.5,
        "user_agent": _DEFAULT_USER_AGENT,
        "enforce_robots": True,
    },
    "totaljobs": {
        "request_delay": 1.5,
        "user_agent": _DEFAULT_USER_AGENT,
        "enforce_robots": True,
    },
}

OVERRIDE_PATH = Path("config") / "scrapers.json"


def get_scraper_settings(name: str) -> dict:
    """Return settings for the named scraper, with overrides applied.

    Always returns a dict containing at least the keys present in
    ``DEFAULTS[name]`` so callers can index into the result without guards.
    Unknown scraper names return an empty dict.
    """
    base = dict(DEFAULTS.get(name, {}))
    if not OVERRIDE_PATH.is_file():
        return base
    try:
        overrides = json.loads(OVERRIDE_PATH.read_text(encoding="utf-8"))
        if isinstance(overrides, dict) and isinstance(overrides.get(name), dict):
            base.update(overrides[name])
    except Exception:
        pass
    return base
