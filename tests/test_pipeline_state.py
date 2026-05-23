"""Tests for ui.services.pipeline_state."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ui.services import pipeline_state


@pytest.fixture
def pipeline_state_env(tmp_path, monkeypatch):
    (tmp_path / "outputs").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(pipeline_state, "_repo_root", lambda: tmp_path)
    return tmp_path


def read_state(repo_root: Path) -> dict:
    path = repo_root / "outputs" / "_pipeline_state.json"
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_get_state_returns_default_when_no_file(pipeline_state_env):
    state = pipeline_state.get_state()
    assert state == dict(pipeline_state._DEFAULT_STATE)


def test_get_state_fills_missing_keys_from_default(pipeline_state_env):
    path = pipeline_state_env / "outputs" / "_pipeline_state.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "state": "error"}, f)
    state = pipeline_state.get_state()
    assert state["state"] == "error"
    assert state["last_run_finished"] == ""
    assert state["last_run_summary"] == ""
    assert state["detail"] == ""


def test_set_running_writes_running_state(pipeline_state_env):
    pipeline_state.set_running()
    data = read_state(pipeline_state_env)
    assert data["state"] == "running"
    assert data["detail"] == ""


def test_set_running_preserves_previous_last_run(pipeline_state_env):
    pipeline_state.set_idle("5 jobs matched")
    before = read_state(pipeline_state_env)
    pipeline_state.set_running()
    data = read_state(pipeline_state_env)
    assert data["state"] == "running"
    assert data["last_run_finished"] == before["last_run_finished"]
    assert data["last_run_summary"] == before["last_run_summary"]


def test_set_idle_stamps_timestamp_and_summary(pipeline_state_env):
    pipeline_state.set_idle("12 jobs matched")
    data = read_state(pipeline_state_env)
    assert data["state"] == "idle"
    assert data["last_run_summary"] == "12 jobs matched"
    assert data["last_run_finished"].endswith("Z")


def test_set_idle_clears_detail(pipeline_state_env):
    pipeline_state.set_error("Something broke")
    pipeline_state.set_idle("recovered")
    data = read_state(pipeline_state_env)
    assert data["state"] == "idle"
    assert data["detail"] == ""


def test_set_error_stores_detail(pipeline_state_env):
    pipeline_state.set_error("cluster_ids cannot be empty")
    data = read_state(pipeline_state_env)
    assert data["state"] == "error"
    assert data["detail"] == "cluster_ids cannot be empty"


def test_set_error_preserves_last_run_finished(pipeline_state_env):
    pipeline_state.set_idle("3 jobs matched")
    finished = read_state(pipeline_state_env)["last_run_finished"]
    summary = read_state(pipeline_state_env)["last_run_summary"]
    pipeline_state.set_error("Sheet failed")
    data = read_state(pipeline_state_env)
    assert data["last_run_finished"] == finished
    assert data["last_run_summary"] == summary
    assert data["state"] == "error"


def test_setters_are_failsoft_on_write_error(pipeline_state_env, monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(pipeline_state, "_atomic_write_json", boom)
    pipeline_state.set_running()
    pipeline_state.set_idle("summary")
    pipeline_state.set_error("detail")
