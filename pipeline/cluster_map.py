"""Per-cluster mapping: the personal opinion layer for the tailoring engine.

Reads ``config/cluster_mappings.json`` and returns, for a cluster id, the priors
the engine uses to bias tailoring: which template to default to, a narrative
framing hint, and lists of which item identities and skill pools to favour or
push down. The mapping biases the model, it does not lock its decisions.

Every field is optional. A cluster's mapping is merged over the file's
``defaults`` block, which is merged over a hardcoded base so the result always
has every expected key. The loader is fail-soft: a missing or malformed file
yields base defaults and never blocks tailoring.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

# The shape every resolved mapping has, and the floor for missing values.
_BASE_DEFAULTS: dict = {
    "default_template": "plain",
    "narrative_hint": "",
    "experience_priority": [],
    "deprioritise": [],
    "project_emphasis": [],
    "skills_emphasis": [],
    "note": "",
}

_STRING_FIELDS = ("default_template", "narrative_hint", "note")
_LIST_FIELDS = ("experience_priority", "deprioritise", "project_emphasis", "skills_emphasis")


def _default_path() -> Path:
    return Path(__file__).resolve().parents[1] / "config" / "cluster_mappings.json"


def load_mappings(path: Optional[Path] = None) -> dict:
    """Load the raw mappings file, or ``{}`` on any problem (fail-soft)."""
    target = Path(path) if path is not None else _default_path()
    if not target.is_file():
        return {}
    try:
        with target.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _coerce(raw: dict) -> dict:
    """Keep only known fields, coerced to the right type. Drops stray keys."""
    out: dict = {}
    for field in _STRING_FIELDS:
        value = raw.get(field)
        if isinstance(value, str):
            out[field] = value
    for field in _LIST_FIELDS:
        value = raw.get(field)
        if isinstance(value, list):
            out[field] = [str(v) for v in value if isinstance(v, str) and v.strip()]
    return out


def get_mapping(cluster_id: Optional[str], path: Optional[Path] = None) -> dict:
    """Return the resolved mapping for ``cluster_id``.

    Layered: base defaults, then the file's ``defaults`` block, then the
    cluster's own entry. Always returns every key in the base shape. An unknown
    or ``None`` cluster yields the defaults. Never raises.
    """
    data = load_mappings(path)
    file_defaults = data.get("defaults")
    cluster_entry = None
    if cluster_id:
        clusters = data.get("clusters")
        if isinstance(clusters, dict):
            cluster_entry = clusters.get(cluster_id)

    resolved = {field: (list(v) if isinstance(v, list) else v)
                for field, v in _BASE_DEFAULTS.items()}
    if isinstance(file_defaults, dict):
        resolved.update(_coerce(file_defaults))
    if isinstance(cluster_entry, dict):
        resolved.update(_coerce(cluster_entry))
    return resolved
