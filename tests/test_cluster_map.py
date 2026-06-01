"""Phase 3 checks for the cluster mapping loader.

The mapping is the personal opinion layer that biases tailoring. Coverage:
defaults layering, unknown and None clusters, fail-soft on missing or malformed
files, type coercion of stray values, and a cloner-safe load of the committed
example file.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline import cluster_map

EXPECTED_KEYS = {
    "default_template",
    "narrative_hint",
    "experience_priority",
    "deprioritise",
    "project_emphasis",
    "skills_emphasis",
    "note",
}


def _write(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_cluster_overrides_defaults(tmp_path):
    f = _write(tmp_path / "m.json", {
        "defaults": {"default_template": "plain", "narrative_hint": "base"},
        "clusters": {"CLU_4": {"default_template": "full", "experience_priority": ["siffa"]}},
    })
    m = cluster_map.get_mapping("CLU_4", path=f)
    assert m["default_template"] == "full"          # cluster wins
    assert m["narrative_hint"] == "base"            # falls back to file defaults
    assert m["experience_priority"] == ["siffa"]
    assert m["deprioritise"] == []                  # falls back to base default


def test_unknown_cluster_returns_defaults(tmp_path):
    f = _write(tmp_path / "m.json", {
        "defaults": {"default_template": "lean"},
        "clusters": {"CLU_4": {"default_template": "full"}},
    })
    m = cluster_map.get_mapping("CLU_999", path=f)
    assert m["default_template"] == "lean"
    assert set(m) == EXPECTED_KEYS


def test_none_cluster_returns_defaults(tmp_path):
    f = _write(tmp_path / "m.json", {"defaults": {"narrative_hint": "x"}, "clusters": {}})
    m = cluster_map.get_mapping(None, path=f)
    assert m["narrative_hint"] == "x"
    assert set(m) == EXPECTED_KEYS


def test_missing_file_is_fail_soft(tmp_path):
    m = cluster_map.get_mapping("CLU_4", path=tmp_path / "does_not_exist.json")
    assert m == {**cluster_map._BASE_DEFAULTS}
    assert set(m) == EXPECTED_KEYS


def test_malformed_file_is_fail_soft(tmp_path):
    bad = tmp_path / "m.json"
    bad.write_text("{not valid json", encoding="utf-8")
    m = cluster_map.get_mapping("CLU_4", path=bad)
    assert set(m) == EXPECTED_KEYS
    assert m["default_template"] == "plain"


def test_stray_and_wrong_typed_values_are_dropped(tmp_path):
    f = _write(tmp_path / "m.json", {
        "clusters": {"CLU_4": {
            "default_template": 123,                       # wrong type, dropped
            "experience_priority": ["siffa", "", 7, "gymfluence"],  # cleaned
            "unknown_field": "ignored",
        }},
    })
    m = cluster_map.get_mapping("CLU_4", path=f)
    assert m["default_template"] == "plain"                # coerced back to base
    assert m["experience_priority"] == ["siffa", "gymfluence"]
    assert "unknown_field" not in m


def test_always_returns_full_shape(tmp_path):
    f = _write(tmp_path / "m.json", {})
    m = cluster_map.get_mapping("CLU_4", path=f)
    assert set(m) == EXPECTED_KEYS


def test_example_file_loads_and_resolves():
    example = Path(__file__).resolve().parents[1] / "config" / "cluster_mappings.example.json"
    m = cluster_map.get_mapping("CLU_1", path=example)
    assert set(m) == EXPECTED_KEYS
    assert m["default_template"] in ("full", "lean", "plain")
    assert isinstance(m["experience_priority"], list)
