"""Wiring checks for tailor_cv delegating to the three-call engine.

Runs offline: load_json and run_engine are monkeypatched, so no content files
or API access are needed. Confirms tailor_cv reads the per-job template choice,
writes the tailored CV and the fail-soft report, and preserves the raw response
on an engine parse failure.
"""

from __future__ import annotations

import json

import pytest

from pipeline import cluster_map, cv_engine, tailor

FAKE_CV = {"identity": {"name": "Wired"}, "objective": "ok"}
FAKE_REPORT = {"rubric": [], "selection": {}, "gaps": [], "provenance": {}}
JOB = {"title": "Junior Designer", "employer": "Acme", "description": "Design."}


@pytest.fixture(autouse=True)
def _stub_sources(monkeypatch):
    # tailor_cv loads gitignored content and the gitignored mappings file; stub
    # both so tests are cloner-safe and hermetic. _read_cluster_for_folder is
    # left real: for a tmp_path it finds no index match and returns None.
    monkeypatch.setattr(tailor, "load_json", lambda path: {"cv": {}} if "master" in str(path) else {})
    monkeypatch.setattr(cluster_map, "get_mapping", lambda *a, **k: dict(cluster_map._BASE_DEFAULTS))


def test_tailor_cv_writes_cv_and_report(monkeypatch, tmp_path):
    monkeypatch.setattr(cv_engine, "run_engine", lambda *a, **k: (FAKE_CV, FAKE_REPORT))

    result = tailor.tailor_cv(JOB, tmp_path)

    assert result == FAKE_CV
    assert json.loads((tmp_path / "cv_tailored.json").read_text(encoding="utf-8")) == FAKE_CV
    assert json.loads((tmp_path / "cv_tailoring_report.json").read_text(encoding="utf-8")) == FAKE_REPORT


def test_explicit_choice_overrides_cluster_default(monkeypatch, tmp_path):
    (tmp_path / "cv_template_choice.json").write_text('{"template": "b"}', encoding="utf-8")
    monkeypatch.setattr(tailor, "_read_cluster_for_folder", lambda *a, **k: "CLU_X")
    monkeypatch.setattr(
        cluster_map, "get_mapping",
        lambda *a, **k: {**cluster_map._BASE_DEFAULTS, "default_template": "full"},
    )
    seen = {}

    def fake_engine(job, *, base, master_profile, template_id, mapping, vault_dir):
        seen["template_id"] = template_id
        return FAKE_CV, FAKE_REPORT

    monkeypatch.setattr(cv_engine, "run_engine", fake_engine)
    tailor.tailor_cv(JOB, tmp_path)
    assert seen["template_id"] == "lean"  # explicit b wins over cluster's full


def test_template_from_cluster_default_when_no_choice(monkeypatch, tmp_path):
    monkeypatch.setattr(tailor, "_read_cluster_for_folder", lambda *a, **k: "CLU_X")
    monkeypatch.setattr(
        cluster_map, "get_mapping",
        lambda *a, **k: {**cluster_map._BASE_DEFAULTS, "default_template": "full"},
    )
    seen = {}

    def fake_engine(job, *, base, master_profile, template_id, mapping, vault_dir):
        seen["template_id"] = template_id
        seen["mapping"] = mapping
        seen["vault_dir"] = vault_dir
        return FAKE_CV, FAKE_REPORT

    monkeypatch.setattr(cv_engine, "run_engine", fake_engine)
    tailor.tailor_cv(JOB, tmp_path)
    assert seen["template_id"] == "full"  # cluster default applies
    assert seen["mapping"]["default_template"] == "full"  # mapping reaches the engine
    assert seen["vault_dir"] == "profile"  # vault is threaded into the engine


def test_defaults_to_plain_without_choice_or_cluster(monkeypatch, tmp_path):
    # autouse stubs: cluster resolves to None, mapping is base defaults (plain).
    seen = {}

    def fake_engine(job, *, base, master_profile, template_id, mapping, vault_dir):
        seen["template_id"] = template_id
        return FAKE_CV, FAKE_REPORT

    monkeypatch.setattr(cv_engine, "run_engine", fake_engine)
    tailor.tailor_cv(JOB, tmp_path)
    assert seen["template_id"] == "plain"


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


# --- _read_cluster_for_folder (index lookup) -----------------------------


def test_read_cluster_matches_index_entry(tmp_path):
    folder = tmp_path / "job_x"
    folder.mkdir()
    index = tmp_path / "_index.json"
    index.write_text(
        json.dumps({"jobs": {"slug": {"output_folder": str(folder), "cluster": "CLU_4"}}}),
        encoding="utf-8",
    )
    assert tailor._read_cluster_for_folder(folder, index_path=index) == "CLU_4"


def test_read_cluster_supports_jobs_as_list(tmp_path):
    folder = tmp_path / "job_y"
    folder.mkdir()
    index = tmp_path / "_index.json"
    index.write_text(
        json.dumps({"jobs": [{"output_folder": str(folder), "cluster": "CLU_2"}]}),
        encoding="utf-8",
    )
    assert tailor._read_cluster_for_folder(folder, index_path=index) == "CLU_2"


def test_read_cluster_no_match_returns_none(tmp_path):
    index = tmp_path / "_index.json"
    index.write_text(
        json.dumps({"jobs": {"slug": {"output_folder": str(tmp_path / "other"), "cluster": "CLU_4"}}}),
        encoding="utf-8",
    )
    assert tailor._read_cluster_for_folder(tmp_path / "job_x", index_path=index) is None


def test_read_cluster_missing_index_returns_none(tmp_path):
    assert tailor._read_cluster_for_folder(tmp_path, index_path=tmp_path / "nope.json") is None


def test_read_cluster_malformed_index_returns_none(tmp_path):
    bad = tmp_path / "_index.json"
    bad.write_text("{not valid", encoding="utf-8")
    assert tailor._read_cluster_for_folder(tmp_path, index_path=bad) is None
