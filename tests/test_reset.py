"""Tests for ui.services.reset.clear_all (the clear-all orchestrator)."""

from __future__ import annotations

import json

import pytest

from ui.services import job_index, reset


@pytest.fixture
def reset_env(tmp_path, monkeypatch):
    (tmp_path / "outputs").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(job_index, "_repo_root", lambda: tmp_path)
    return tmp_path


def _seed_index(repo_root, jobs):
    path = repo_root / "outputs" / "_index.json"
    path.write_text(
        json.dumps({"version": 1, "jobs": jobs, "last_sheet_sync_at": None}),
        encoding="utf-8",
    )


def test_clear_all_clears_index_and_folders(reset_env):
    (reset_env / "outputs" / "2026-06-01" / "job_a").mkdir(parents=True)
    _seed_index(reset_env, [{"slug": "2026-06-01/job_a", "listing_url": "u"}])

    summary = reset.clear_all(with_sheet=False)

    assert summary["index_cleared"] == 1
    assert summary["folders_removed"] == 1
    assert summary["sheet_cleared"] is None
    assert summary["sheet_error"] is None
    assert job_index.list_jobs() == []
    assert not (reset_env / "outputs" / "2026-06-01").exists()


def test_clear_all_with_sheet_unconfigured_reports_not_blocks(reset_env, monkeypatch):
    _seed_index(reset_env, [{"slug": "x", "listing_url": "u"}])
    monkeypatch.setattr("ui.services.sheets.is_configured", lambda: False)

    summary = reset.clear_all(with_sheet=True)

    # Local clear still happened; Sheet skipped with a reason.
    assert summary["index_cleared"] == 1
    assert summary["sheet_cleared"] is None
    assert "not configured" in summary["sheet_error"]


def test_clear_all_with_sheet_configured_wipes_sheet(reset_env, monkeypatch):
    _seed_index(reset_env, [{"slug": "x", "listing_url": "u"}])
    monkeypatch.setattr("ui.services.sheets.is_configured", lambda: True)
    monkeypatch.setattr("ui.services.sheets.clear_data_rows", lambda: {"cleared": 7})

    summary = reset.clear_all(with_sheet=True)

    assert summary["sheet_cleared"] == 7
    assert summary["sheet_error"] is None


def test_clear_all_sheet_failure_does_not_block_local_clear(reset_env, monkeypatch):
    _seed_index(reset_env, [{"slug": "x", "listing_url": "u"}])
    monkeypatch.setattr("ui.services.sheets.is_configured", lambda: True)

    def boom():
        raise RuntimeError("sheet down")

    monkeypatch.setattr("ui.services.sheets.clear_data_rows", boom)

    summary = reset.clear_all(with_sheet=True)

    assert summary["index_cleared"] == 1  # local clear still succeeded
    assert summary["sheet_cleared"] is None
    assert "sheet down" in summary["sheet_error"]
