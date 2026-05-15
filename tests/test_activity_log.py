"""Tests for ui.services.activity_log."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ui.services import activity_log


@pytest.fixture
def activity_env(tmp_path, monkeypatch):
    (tmp_path / "outputs").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(activity_log, "_repo_root", lambda: tmp_path)
    return tmp_path


def read_log(repo_root: Path) -> dict:
    path = repo_root / "outputs" / "_activity.json"
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_get_recent_returns_empty_when_no_log(activity_env):
    assert activity_log.get_recent() == []


def test_record_scrape_appends_event(activity_env):
    activity_log.record_scrape("open_search", ["waiter"], "Slough", 23)
    data = read_log(activity_env)
    assert len(data["events"]) == 1
    ev = data["events"][0]
    assert ev["type"] == "scrape"
    assert ev["details"]["source"] == "open_search"
    assert ev["details"]["terms"] == ["waiter"]
    assert ev["details"]["location"] == "Slough"
    assert ev["details"]["jobs_added"] == 23
    assert ev["timestamp"].endswith("Z")


def test_record_status_change_appends_event(activity_env):
    activity_log.record_status_change(
        "2026-05-15/govuk_waiter_pizza_hut",
        "Waiter",
        "Pizza Hut",
        "to_review",
        "approved",
    )
    data = read_log(activity_env)
    assert len(data["events"]) == 1
    ev = data["events"][0]
    assert ev["type"] == "status_change"
    d = ev["details"]
    assert d["slug"] == "2026-05-15/govuk_waiter_pizza_hut"
    assert d["title"] == "Waiter"
    assert d["employer"] == "Pizza Hut"
    assert d["from"] == "to_review"
    assert d["to"] == "approved"


def test_get_recent_returns_newest_first(activity_env):
    activity_log.record_scrape("a", [], "L1", 1)
    activity_log.record_scrape("b", [], "L2", 2)
    recent = activity_log.get_recent(10)
    assert len(recent) == 2
    assert recent[0]["details"]["source"] == "b"
    assert recent[1]["details"]["source"] == "a"


def test_get_recent_respects_limit(activity_env):
    for i in range(5):
        activity_log.record_scrape("x", [], "L", i)
    assert len(activity_log.get_recent(3)) == 3


def test_log_truncates_to_max_events(activity_env, monkeypatch):
    monkeypatch.setattr(activity_log, "MAX_EVENTS", 5)
    for i in range(7):
        activity_log.record_scrape("x", [], "L", i)
    data = read_log(activity_env)
    assert len(data["events"]) == 5
    assert [e["details"]["jobs_added"] for e in data["events"]] == [2, 3, 4, 5, 6]


def test_record_scrape_does_not_raise_on_unwritable_path(tmp_path, monkeypatch):
    (tmp_path / "outputs").write_text("not a directory", encoding="utf-8")
    monkeypatch.setattr(activity_log, "_repo_root", lambda: tmp_path)
    activity_log.record_scrape("open_search", [], "L", 1)


def test_record_status_change_does_not_raise_on_unwritable_path(tmp_path, monkeypatch):
    (tmp_path / "outputs").write_text("not a directory", encoding="utf-8")
    monkeypatch.setattr(activity_log, "_repo_root", lambda: tmp_path)
    activity_log.record_status_change("s", "t", "e", "to_review", "approved")


def test_format_relative_time_just_now(monkeypatch):
    fixed = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(activity_log, "_utc_now", lambda: fixed)
    assert activity_log.format_relative_time("2026-06-01T11:59:30Z") == "just now"


def test_format_relative_time_minutes(monkeypatch):
    fixed = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(activity_log, "_utc_now", lambda: fixed)
    assert activity_log.format_relative_time("2026-06-01T11:54:00Z") == "6 minutes ago"
    assert activity_log.format_relative_time("2026-06-01T11:59:00Z") == "1 minute ago"


def test_format_relative_time_hours(monkeypatch):
    fixed = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(activity_log, "_utc_now", lambda: fixed)
    assert activity_log.format_relative_time("2026-06-01T08:00:00Z") == "4 hours ago"
    assert activity_log.format_relative_time("2026-06-01T11:00:00Z") == "1 hour ago"


def test_format_relative_time_days(monkeypatch):
    fixed = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(activity_log, "_utc_now", lambda: fixed)
    assert activity_log.format_relative_time("2026-05-30T12:00:00Z") == "2 days ago"
    assert activity_log.format_relative_time("2026-05-31T12:00:00Z") == "1 day ago"


def test_format_relative_time_old_returns_iso_date(monkeypatch):
    fixed = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(activity_log, "_utc_now", lambda: fixed)
    assert activity_log.format_relative_time("2026-04-15T10:00:00Z") == "2026-04-15"


def test_format_relative_time_invalid_input_returns_input():
    assert activity_log.format_relative_time("not-a-date") == "not-a-date"
