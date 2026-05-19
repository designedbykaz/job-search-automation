"""Tests for ui.services.clusters."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ui.services import clusters


@pytest.fixture
def clusters_env(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(clusters, "_repo_root", lambda: tmp_path)
    return tmp_path


def write_clusters_file(repo_root: Path, clusters_dict: dict, version: int = 1) -> Path:
    path = repo_root / "config" / "clusters.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"version": version, "clusters": clusters_dict}
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_list_clusters_returns_empty_when_no_file(clusters_env):
    assert clusters.list_clusters() == []


def test_create_cluster_assigns_id_one(clusters_env):
    created = clusters.create_cluster("Alpha", ["kw"])
    assert created["id"] == "CLU_1"


def test_create_cluster_assigns_incrementing_ids(clusters_env):
    clusters.create_cluster("A", ["a"])
    clusters.create_cluster("B", ["b"])
    third = clusters.create_cluster("C", ["c"])
    assert third["id"] == "CLU_3"


def test_create_cluster_strips_label_whitespace(clusters_env):
    created = clusters.create_cluster("  Trimmed  ", ["kw"])
    assert created["label"] == "Trimmed"


def test_create_cluster_raises_on_empty_label(clusters_env):
    with pytest.raises(ValueError):
        clusters.create_cluster("   ", ["kw"])


def test_create_cluster_filters_whitespace_only_keywords(clusters_env):
    created = clusters.create_cluster("L", ["  good  ", "   ", "\t"])
    assert created["keywords"] == ["good"]


def test_create_cluster_returns_full_object_with_timestamp_and_id(clusters_env):
    created = clusters.create_cluster("L", ["kw"], active=False)
    assert created["id"] == "CLU_1"
    assert created["label"] == "L"
    assert created["keywords"] == ["kw"]
    assert created["active"] is False
    assert created["created_at"].endswith("Z")
    assert len(created["created_at"]) == 20


def test_get_cluster_returns_existing(clusters_env):
    clusters.create_cluster("L", ["kw"])
    got = clusters.get_cluster("CLU_1")
    assert got is not None
    assert got["id"] == "CLU_1"
    assert got["label"] == "L"


def test_get_cluster_returns_none_for_missing(clusters_env):
    clusters.create_cluster("L", ["kw"])
    assert clusters.get_cluster("CLU_99") is None


def test_update_cluster_label_only(clusters_env):
    clusters.create_cluster("Old", ["kw"])
    assert clusters.update_cluster("CLU_1", label="New") is True
    assert clusters.get_cluster("CLU_1")["label"] == "New"
    assert clusters.get_cluster("CLU_1")["keywords"] == ["kw"]


def test_update_cluster_keywords_only(clusters_env):
    clusters.create_cluster("L", ["old"])
    assert clusters.update_cluster("CLU_1", keywords=["new", "  x  "]) is True
    assert clusters.get_cluster("CLU_1")["keywords"] == ["new", "x"]


def test_update_cluster_active_flag_only(clusters_env):
    clusters.create_cluster("L", ["kw"], active=True)
    assert clusters.update_cluster("CLU_1", active=False) is True
    assert clusters.get_cluster("CLU_1")["active"] is False


def test_update_cluster_multiple_fields(clusters_env):
    clusters.create_cluster("L", ["old"], active=True)
    assert (
        clusters.update_cluster(
            "CLU_1",
            label="New",
            keywords=["a"],
            active=False,
        )
        is True
    )
    got = clusters.get_cluster("CLU_1")
    assert got["label"] == "New"
    assert got["keywords"] == ["a"]
    assert got["active"] is False


def test_update_cluster_returns_false_for_missing(clusters_env):
    assert clusters.update_cluster("CLU_9", label="X") is False


def test_update_cluster_raises_on_empty_label(clusters_env):
    clusters.create_cluster("L", ["kw"])
    with pytest.raises(ValueError):
        clusters.update_cluster("CLU_1", label="  ")


def test_delete_cluster_removes_entry(clusters_env):
    clusters.create_cluster("L", ["kw"])
    assert clusters.delete_cluster("CLU_1") is True
    assert clusters.get_cluster("CLU_1") is None
    assert clusters.list_clusters() == []


def test_delete_cluster_returns_false_for_missing(clusters_env):
    assert clusters.delete_cluster("CLU_1") is False


def test_list_clusters_active_only_filter(clusters_env):
    clusters.create_cluster("On", ["a"], active=True)
    clusters.create_cluster("Off", ["b"], active=False)
    rows = clusters.list_clusters(active_only=True)
    assert len(rows) == 1
    assert rows[0]["label"] == "On"


def test_list_clusters_sorted_by_id(clusters_env):
    write_clusters_file(
        clusters_env,
        {
            "CLU_10": {
                "label": "Ten",
                "keywords": [],
                "active": True,
                "created_at": "2026-01-01T00:00:00Z",
            },
            "CLU_2": {
                "label": "Two",
                "keywords": [],
                "active": True,
                "created_at": "2026-01-01T00:00:00Z",
            },
        },
    )
    ids = [r["id"] for r in clusters.list_clusters()]
    assert ids == ["CLU_2", "CLU_10"]


def test_get_active_keywords_flat_list(clusters_env):
    clusters.create_cluster("A", ["one", "two"], active=True)
    clusters.create_cluster("B", ["three"], active=True)
    assert clusters.get_active_keywords() == ["one", "two", "three"]


def test_get_active_keywords_excludes_inactive_clusters(clusters_env):
    clusters.create_cluster("On", ["visible"], active=True)
    clusters.create_cluster("Off", ["hidden"], active=False)
    assert clusters.get_active_keywords() == ["visible"]


def test_get_active_keywords_deduplicates(clusters_env):
    clusters.create_cluster("A", ["dup", "unique_a"], active=True)
    clusters.create_cluster("B", ["dup", "unique_b"], active=True)
    assert clusters.get_active_keywords() == ["dup", "unique_a", "unique_b"]


def test_get_keyword_to_cluster_map_lowercases_keys(clusters_env):
    clusters.create_cluster("A", ["Foo Bar"], active=True)
    mapping = clusters.get_keyword_to_cluster_map()
    assert "foo bar" in mapping
    assert mapping["foo bar"] == "CLU_1"


def test_get_keyword_to_cluster_map_excludes_inactive(clusters_env):
    clusters.create_cluster("Off", ["secret"], active=False)
    assert clusters.get_keyword_to_cluster_map() == {}


def test_get_keyword_to_cluster_map_first_active_cluster_wins(clusters_env):
    write_clusters_file(
        clusters_env,
        {
            "CLU_1": {
                "label": "First",
                "keywords": ["Shared"],
                "active": True,
                "created_at": "2026-01-01T00:00:00Z",
            },
            "CLU_2": {
                "label": "Second",
                "keywords": ["shared"],
                "active": True,
                "created_at": "2026-01-01T00:00:00Z",
            },
        },
    )
    mapping = clusters.get_keyword_to_cluster_map()
    assert mapping["shared"] == "CLU_1"
