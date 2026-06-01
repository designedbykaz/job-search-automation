"""Wiring checks for tailor_cv delegating to the three-call engine.

Runs offline: load_json and run_engine are monkeypatched, so no content files
or API access are needed. Confirms tailor_cv reads the per-job template choice,
writes the tailored CV and the fail-soft report, and preserves the raw response
on an engine parse failure.
"""

from __future__ import annotations

import json

import pytest

from pipeline import cv_engine, tailor

FAKE_CV = {"identity": {"name": "Wired"}, "objective": "ok"}
FAKE_REPORT = {"rubric": [], "selection": {}, "gaps": [], "provenance": {}}
JOB = {"title": "Junior Designer", "employer": "Acme", "description": "Design."}


@pytest.fixture(autouse=True)
def _stub_sources(monkeypatch):
    # tailor_cv loads gitignored content; stub it so tests are cloner-safe.
    monkeypatch.setattr(tailor, "load_json", lambda path: {"cv": {}} if "master" in str(path) else {})


def test_tailor_cv_writes_cv_and_report(monkeypatch, tmp_path):
    monkeypatch.setattr(cv_engine, "run_engine", lambda *a, **k: (FAKE_CV, FAKE_REPORT))

    result = tailor.tailor_cv(JOB, tmp_path)

    assert result == FAKE_CV
    assert json.loads((tmp_path / "cv_tailored.json").read_text(encoding="utf-8")) == FAKE_CV
    assert json.loads((tmp_path / "cv_tailoring_report.json").read_text(encoding="utf-8")) == FAKE_REPORT


def test_tailor_cv_passes_template_choice_to_engine(monkeypatch, tmp_path):
    (tmp_path / "cv_template_choice.json").write_text('{"template": "b"}', encoding="utf-8")
    seen = {}

    def fake_engine(job, *, base, master_profile, template_id):
        seen["template_id"] = template_id
        return FAKE_CV, FAKE_REPORT

    monkeypatch.setattr(cv_engine, "run_engine", fake_engine)
    tailor.tailor_cv(JOB, tmp_path)
    assert seen["template_id"] == "lean"  # b -> lean


def test_tailor_cv_defaults_to_plain_without_choice(monkeypatch, tmp_path):
    seen = {}

    def fake_engine(job, *, base, master_profile, template_id):
        seen["template_id"] = template_id
        return FAKE_CV, FAKE_REPORT

    monkeypatch.setattr(cv_engine, "run_engine", fake_engine)
    tailor.tailor_cv(JOB, tmp_path)
    assert seen["template_id"] == "plain"  # default c -> plain


def test_tailor_cv_preserves_raw_on_parse_failure(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise cv_engine.EngineParseError("synthesis", "RAW MODEL TEXT")

    monkeypatch.setattr(cv_engine, "run_engine", boom)
    with pytest.raises(ValueError, match="synthesis"):
        tailor.tailor_cv(JOB, tmp_path)

    raw = (tmp_path / "cv_tailored_raw.txt").read_text(encoding="utf-8")
    assert raw == "RAW MODEL TEXT"
    assert not (tmp_path / "cv_tailored.json").exists()


def test_tailor_cv_report_failure_does_not_block_cv(monkeypatch, tmp_path):
    monkeypatch.setattr(cv_engine, "run_engine", lambda *a, **k: (FAKE_CV, FAKE_REPORT))

    real_save = tailor.save_json

    def flaky_save(data, filepath):
        if str(filepath).endswith("cv_tailoring_report.json"):
            raise OSError("disk full")
        return real_save(data, filepath)

    monkeypatch.setattr(tailor, "save_json", flaky_save)
    # Primary CV write must still succeed despite the report write failing.
    result = tailor.tailor_cv(JOB, tmp_path)
    assert result == FAKE_CV
    assert (tmp_path / "cv_tailored.json").exists()
