"""Tests for ui.services.cluster_search."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ui.services import cluster_search, clusters


@pytest.fixture
def clusters_env(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(clusters, "_repo_root", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def cluster_search_env(monkeypatch):
    state: dict = {
        "scrape_keywords": [],
        "rebuild_calls": 0,
        "sync_calls": 0,
        "sync_update_status": None,
        "log_calls": 0,
        "log_result": (0, 0),
        "list_jobs_result": [{"slug": "a"}],
    }

    def fake_scrape(keywords):
        state["scrape_keywords"] = list(keywords)
        kw = keywords[0] if keywords else "missing"
        return [
            {
                "title": f"{kw} specialist",
                "employer": "Acme",
                "url": f"http://example.com/{hash(kw) % 10000}",
                "source": "govuk",
            }
        ]

    def fake_log(jobs):
        state["log_calls"] += 1
        logged, errors = state["log_result"]
        if callable(logged):
            return logged(jobs)
        return logged, errors

    def fake_rebuild():
        state["rebuild_calls"] += 1
        return {"total_jobs_found": 1, "new_jobs": 1, "missing_from_disk": []}

    def fake_sync(update_status=True):
        state["sync_calls"] += 1
        state["sync_update_status"] = update_status
        return {"matched": 0, "updated": 0, "unmatched_sheet_rows": []}

    def fake_list_jobs():
        return state["list_jobs_result"]

    def fake_folders(jobs):
        out = []
        for i, job in enumerate(jobs):
            row = dict(job)
            row["output_folder"] = f"outputs/test/job_{i}"
            out.append(row)
        return out

    monkeypatch.setattr(cluster_search, "scrape_govuk_jobs", fake_scrape)
    monkeypatch.setattr(cluster_search, "_log_jobs_counted", fake_log)
    monkeypatch.setattr(cluster_search, "create_output_folders", fake_folders)
    monkeypatch.setattr(cluster_search.job_index, "rebuild_from_disk", fake_rebuild)
    monkeypatch.setattr(cluster_search.job_index, "sync_from_sheet", fake_sync)
    monkeypatch.setattr(cluster_search.job_index, "list_jobs", fake_list_jobs)
    return state


def write_clusters_file(repo_root: Path, clusters_dict: dict) -> None:
    path = repo_root / "config" / "clusters.json"
    path.write_text(
        json.dumps({"version": 1, "clusters": clusters_dict}),
        encoding="utf-8",
    )


def test_run_cluster_search_uses_all_active_when_none_passed(
    clusters_env, cluster_search_env
):
    clusters.create_cluster("Active A", ["alpha kw"], active=True)
    clusters.create_cluster("Inactive", ["hidden kw"], active=False)
    clusters.create_cluster("Active B", ["beta kw"], active=True)

    result = cluster_search.run_cluster_search(cluster_ids=None)

    assert "alpha kw" in cluster_search_env["scrape_keywords"]
    assert "beta kw" in cluster_search_env["scrape_keywords"]
    assert "hidden kw" not in cluster_search_env["scrape_keywords"]
    assert len(result["clusters_used"]) == 2


def test_run_cluster_search_raises_on_empty_list(cluster_search_env):
    with pytest.raises(ValueError, match="cannot be empty"):
        cluster_search.run_cluster_search(cluster_ids=[])


def test_run_cluster_search_raises_on_unknown_cluster_id(clusters_env, cluster_search_env):
    with pytest.raises(ValueError, match="Unknown cluster ID"):
        cluster_search.run_cluster_search(cluster_ids=["CLU_99"])


def test_run_cluster_search_raises_on_clusters_with_no_keywords(
    clusters_env, cluster_search_env
):
    clusters.create_cluster("Empty", [], active=True)
    with pytest.raises(ValueError, match="no keywords"):
        cluster_search.run_cluster_search(cluster_ids=["CLU_1"])


def test_run_cluster_search_builds_keyword_map_from_selected_only(
    clusters_env, cluster_search_env
):
    clusters.create_cluster("One", ["alpha only"], active=True)
    clusters.create_cluster("Two", ["beta only"], active=True)

    result = cluster_search.run_cluster_search(cluster_ids=["CLU_1"])

    assert cluster_search_env["scrape_keywords"] == ["alpha only"]
    assert result["clusters_used"] == ["CLU_1"]


def test_run_cluster_search_returns_correct_summary(
    clusters_env, cluster_search_env
):
    clusters.create_cluster("A", ["match me"], active=True)
    cluster_search_env["log_result"] = (1, 0)
    cluster_search_env["list_jobs_result"] = [{"slug": "a"}, {"slug": "b"}]

    result = cluster_search.run_cluster_search(cluster_ids=["CLU_1"])

    assert result == {
        "scraped": 1,
        "deduplicated": 1,
        "matched": 1,
        "already_indexed": 0,
        "new_jobs": 1,
        "logged_to_sheet": 1,
        "sheet_errors": 0,
        "indexed": 2,
        "clusters_used": ["CLU_1"],
    }


def test_run_cluster_search_handles_sheet_quota_error_gracefully(
    clusters_env, cluster_search_env
):
    clusters.create_cluster("A", ["kw"], active=True)
    cluster_search_env["log_result"] = (0, 1)

    result = cluster_search.run_cluster_search(cluster_ids=["CLU_1"])

    assert result["logged_to_sheet"] == 0
    assert result["sheet_errors"] == 1
    assert result["matched"] == 1


def test_run_cluster_search_continues_after_sheet_error(
    clusters_env, cluster_search_env
):
    clusters.create_cluster("A", ["kw"], active=True)
    cluster_search_env["log_result"] = (0, 1)

    cluster_search.run_cluster_search(cluster_ids=["CLU_1"])

    assert cluster_search_env["rebuild_calls"] == 1


def test_run_cluster_search_maps_sheet_row_without_status_sync(
    clusters_env, cluster_search_env
):
    clusters.create_cluster("A", ["kw"], active=True)

    cluster_search.run_cluster_search(cluster_ids=["CLU_1"])

    assert cluster_search_env["rebuild_calls"] == 1
    assert cluster_search_env["log_calls"] == 1
    # The Sheet is read to map sheet_row onto new entries, but status is UI-owned,
    # so the scrape must call sync with update_status=False.
    assert cluster_search_env["sync_calls"] == 1
    assert cluster_search_env["sync_update_status"] is False


def test_run_cluster_search_skips_jobs_already_in_index(
    clusters_env, cluster_search_env, monkeypatch
):
    # A scraped job whose URL is already in the index is dropped before folders.
    clusters.create_cluster("A", ["match me"], active=True)

    def fake_scrape(keywords):
        return [
            {"title": "match me one", "employer": "A", "url": "http://x/seen", "source": "govuk"},
            {"title": "match me two", "employer": "B", "url": "http://x/new", "source": "govuk"},
        ]

    monkeypatch.setattr(cluster_search, "scrape_govuk_jobs", fake_scrape)
    cluster_search_env["list_jobs_result"] = [
        {"slug": "old", "listing_url": "http://x/seen"}
    ]

    result = cluster_search.run_cluster_search(cluster_ids=["CLU_1"])

    assert result["matched"] == 2
    assert result["already_indexed"] == 1
    assert result["new_jobs"] == 1
