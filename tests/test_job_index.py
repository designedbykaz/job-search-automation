"""Tests for ui.services.job_index."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ui.services import job_index


@pytest.fixture
def index_env(tmp_path, monkeypatch):
    (tmp_path / "outputs").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(job_index, "_repo_root", lambda: tmp_path)
    return tmp_path


def make_job_folder(repo_root: Path, slug: str, **fields) -> Path:
    """Create outputs/{slug}/job.json with given fields."""
    folder = repo_root / "outputs"
    for part in slug.split("/"):
        folder = folder / part
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "job.json").write_text(json.dumps(fields), encoding="utf-8")
    return folder


def write_index(repo_root: Path, jobs: list, last_sheet_sync_at=None):
    path = repo_root / "outputs" / "_index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": 1,
        "jobs": jobs,
        "last_sheet_sync_at": last_sheet_sync_at,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def job_entry(slug: str, **overrides) -> dict:
    e = {
        "slug": slug,
        "sheet_row": None,
        "title": "T",
        "employer": "E",
        "location": "",
        "date_found": "",
        "closing_date": "",
        "cluster": "",
        "source": "",
        "listing_url": "",
        "output_folder": f"outputs/{slug}",
        "status": "to_review",
        "has_tailored_cv": False,
    }
    e.update(overrides)
    return e


def test_list_jobs_returns_empty_when_no_index_file(index_env):
    assert job_index.list_jobs() == []


def test_reset_index_clears_jobs_and_backs_up(index_env):
    write_index(index_env, [job_entry("a"), job_entry("b")])
    result = job_index.reset_index()
    assert result["cleared"] == 2
    assert job_index.list_jobs() == []
    # The pre-clear index is preserved as a backup with its jobs intact.
    backup = index_env / "outputs" / "_index.json.bak"
    assert backup.is_file()
    assert len(json.loads(backup.read_text(encoding="utf-8"))["jobs"]) == 2


def test_reset_index_no_existing_file_is_safe(index_env):
    result = job_index.reset_index()
    assert result["cleared"] == 0
    assert result["backup"] is None
    assert job_index.list_jobs() == []


def test_clear_output_folders_removes_subdirs_keeps_files(index_env):
    outputs = index_env / "outputs"
    (outputs / "2026-06-01" / "job_a").mkdir(parents=True)
    (outputs / "2026-06-01" / "job_a" / "cv_output.pdf").write_text("x", encoding="utf-8")
    (outputs / "test_single_job").mkdir()
    write_index(index_env, [job_entry("2026-06-01/job_a")])
    (outputs / "_activity.json").write_text("{}", encoding="utf-8")

    result = job_index.clear_output_folders()

    assert result["removed"] == 2  # the date dir and test_single_job
    assert not (outputs / "2026-06-01").exists()
    assert not (outputs / "test_single_job").exists()
    # Top-level files are kept.
    assert (outputs / "_index.json").is_file()
    assert (outputs / "_activity.json").is_file()


def test_clear_output_folders_no_outputs_dir_is_safe(tmp_path, monkeypatch):
    monkeypatch.setattr(job_index, "_repo_root", lambda: tmp_path)  # no outputs/ dir
    assert job_index.clear_output_folders() == {"removed": 0}


def test_sync_from_sheet_update_status_false_maps_row_keeps_status(index_env, monkeypatch):
    from ui.services import sheets

    write_index(index_env, [job_entry("a", listing_url="http://x/1", status="approved")])
    monkeypatch.setattr(
        sheets, "get_jobs",
        lambda status_filter=None: [{"row": 5, "listing_url": "http://x/1", "status": "to_review"}],
    )

    job_index.sync_from_sheet(update_status=False)

    job = job_index.get_job("a")
    assert job["sheet_row"] == 5         # sheet_row is mapped (UI needs it)
    assert job["status"] == "approved"   # status is NOT pulled from the Sheet


def test_sync_from_sheet_default_still_updates_status(index_env, monkeypatch):
    from ui.services import sheets

    write_index(index_env, [job_entry("a", listing_url="http://x/1", status="approved")])
    monkeypatch.setattr(
        sheets, "get_jobs",
        lambda status_filter=None: [{"row": 5, "listing_url": "http://x/1", "status": "to_review"}],
    )

    job_index.sync_from_sheet()  # default update_status=True (migration behaviour)

    assert job_index.get_job("a")["status"] == "to_review"


def test_list_jobs_returns_all_jobs(index_env):
    write_index(
        index_env,
        [
            job_entry("a/one", title="Alpha"),
            job_entry("b/two", title="Beta"),
        ],
    )
    assert len(job_index.list_jobs()) == 2


def test_list_jobs_filters_by_status(index_env):
    write_index(
        index_env,
        [
            job_entry("a", status="to_review"),
            job_entry("b", status="approved"),
        ],
    )
    names = {j["slug"] for j in job_index.list_jobs(status_filter="approved")}
    assert names == {"b"}


def test_list_jobs_filters_by_search_case_insensitive(index_env):
    write_index(
        index_env,
        [
            job_entry("x", title="Senior WAITER", employer="Co"),
            job_entry("y", title="Clerk", employer="acme corp"),
        ],
    )
    by_title = job_index.list_jobs(search="waiter")
    assert len(by_title) == 1 and by_title[0]["slug"] == "x"
    by_emp = job_index.list_jobs(search="ACME")
    assert len(by_emp) == 1 and by_emp[0]["slug"] == "y"


def test_list_jobs_combines_status_and_search_filters(index_env):
    write_index(
        index_env,
        [
            job_entry("a", title="Waiter Acme", status="approved"),
            job_entry("b", title="Waiter Beta", status="to_review"),
            job_entry("c", title="Clerk Acme", status="approved"),
        ],
    )
    rows = job_index.list_jobs(status_filter="approved", search="waiter")
    assert len(rows) == 1 and rows[0]["slug"] == "a"


def test_get_job_returns_match(index_env):
    write_index(index_env, [job_entry("2025/x", title="Waiter")])
    j = job_index.get_job("2025/x")
    assert j is not None and j["title"] == "Waiter"


def test_get_job_returns_none_for_missing_slug(index_env):
    write_index(index_env, [job_entry("a")])
    assert job_index.get_job("missing") is None


def test_get_job_by_row_returns_match(index_env):
    write_index(index_env, [job_entry("a", sheet_row=42)])
    j = job_index.get_job_by_row(42)
    assert j is not None and j["slug"] == "a"


def test_set_status_updates_index_file(index_env):
    write_index(index_env, [job_entry("a")])
    assert job_index.set_status("a", "approved")
    data = json.loads((index_env / "outputs" / "_index.json").read_text(encoding="utf-8"))
    assert data["jobs"][0]["status"] == "approved"


def test_set_status_raises_on_invalid_status(index_env):
    write_index(index_env, [job_entry("a")])
    with pytest.raises(ValueError):
        job_index.set_status("a", "bogus")


def test_set_status_returns_false_for_missing_slug(index_env):
    write_index(index_env, [job_entry("a")])
    before = (index_env / "outputs" / "_index.json").read_bytes()
    assert job_index.set_status("gone", "approved") is False
    assert (index_env / "outputs" / "_index.json").read_bytes() == before


def test_add_job_appends_new_job(index_env):
    make_job_folder(index_env, "n1", title="N1", employer="E", url="http://x")
    job_index.add_job(
        {
            "slug": "n1",
            "output_folder": "outputs/n1",
            "title": "N1",
            "employer": "E",
            "listing_url": "http://x",
        }
    )
    assert len(job_index.list_jobs()) == 1


def test_add_job_replaces_existing_slug(index_env):
    make_job_folder(index_env, "s", title="One", employer="E", url="http://x")
    job_index.add_job(
        {
            "slug": "s",
            "output_folder": "outputs/s",
            "title": "One",
            "employer": "E",
        }
    )
    job_index.add_job(
        {
            "slug": "s",
            "output_folder": "outputs/s",
            "title": "Two",
            "employer": "E",
        }
    )
    rows = job_index.list_jobs()
    assert len(rows) == 1 and rows[0]["title"] == "Two"


def test_rebuild_from_disk_creates_entries_from_job_json(index_env):
    make_job_folder(
        index_env,
        "2025-11-01/govuk_waiter_pizza",
        title="Waiter",
        employer="Pizza Hut",
        location="Slough",
        date="2025-11-01",
        closing_date="2025-11-15",
        contact_info="c@x",
        source="govuk",
        url="https://example.com/job",
        cluster="hospitality",
    )
    summary = job_index.rebuild_from_disk()
    assert summary["total_jobs_found"] == 1
    j = job_index.get_job("2025-11-01/govuk_waiter_pizza")
    assert j is not None
    assert j["title"] == "Waiter"
    assert j["employer"] == "Pizza Hut"
    assert j["listing_url"] == "https://example.com/job"
    assert j["date_found"] == "2025-11-01"
    assert j["cluster"] == "hospitality"


def test_rebuild_from_disk_preserves_status_from_existing_index(index_env):
    write_index(
        index_env,
        [
            job_entry(
                "2025/a",
                status="approved",
                sheet_row=9,
                listing_url="http://u",
            )
        ],
    )
    make_job_folder(
        index_env,
        "2025/a",
        title="T",
        employer="E",
        url="http://u",
    )
    job_index.rebuild_from_disk()
    j = job_index.get_job("2025/a")
    assert j["status"] == "approved" and j["sheet_row"] == 9


def test_rebuild_from_disk_flags_jobs_missing_from_disk(index_env):
    write_index(index_env, [job_entry("gone"), job_entry("here")])
    make_job_folder(index_env, "here", title="H", employer="E", url="http://h")
    summary = job_index.rebuild_from_disk()
    assert "gone" in summary["missing_from_disk"]
    assert summary["total_jobs_found"] == 1


def test_rebuild_from_disk_skips_folders_without_job_json(index_env):
    (index_env / "outputs" / "empty_only").mkdir(parents=True)
    make_job_folder(index_env, "ok", title="O", employer="E", url="http://o")
    summary = job_index.rebuild_from_disk()
    assert summary["total_jobs_found"] == 1


def test_rebuild_from_disk_skips_corrupt_job_json(index_env, capsys):
    folder = make_job_folder(index_env, "bad", title="x")
    (folder / "job.json").write_text("{ not json", encoding="utf-8")
    make_job_folder(index_env, "ok", title="O", employer="E", url="http://o")
    summary = job_index.rebuild_from_disk()
    assert summary["total_jobs_found"] == 1
    err = capsys.readouterr().err
    assert "corrupt" in err.lower() or "Warning" in err


def test_rebuild_from_disk_sets_has_tailored_cv_correctly(index_env):
    f1 = make_job_folder(index_env, "with_cv", title="A", employer="E", url="http://a")
    (f1 / "cv_tailored.json").write_text("{}", encoding="utf-8")
    make_job_folder(index_env, "no_cv", title="B", employer="E", url="http://b")
    job_index.rebuild_from_disk()
    assert job_index.get_job("with_cv")["has_tailored_cv"] is True
    assert job_index.get_job("no_cv")["has_tailored_cv"] is False


def test_atomic_write_does_not_corrupt_on_partial_failure(index_env, monkeypatch):
    write_index(index_env, [job_entry("a")])
    before = (index_env / "outputs" / "_index.json").read_text(encoding="utf-8")

    def boom(*_a, **_k):
        raise RuntimeError("simulated")

    monkeypatch.setattr(job_index.json, "dump", boom)
    with pytest.raises(RuntimeError, match="simulated"):
        job_index.set_status("a", "approved")
    after = (index_env / "outputs" / "_index.json").read_text(encoding="utf-8")
    assert before == after


def test_get_counters_returns_zero_when_empty(index_env):
    write_index(index_env, [])
    assert job_index.get_counters() == {"to_review": 0, "approved": 0, "pdf_ready": 0}


def test_get_counters_tallies_by_status(index_env):
    write_index(
        index_env,
        [
            {"slug": "a", "status": "to_review"},
            {"slug": "b", "status": "to_review"},
            {"slug": "c", "status": "approved"},
            {"slug": "d", "status": "pdf_ready"},
            {"slug": "e", "status": "archived"},
        ],
    )
    counters = job_index.get_counters()
    assert counters == {"to_review": 2, "approved": 1, "pdf_ready": 1}


def test_delete_job_removes_entry_from_index(index_env):
    write_index(
        index_env,
        [
            {"slug": "a", "title": "A", "output_folder": "outputs/a"},
            {"slug": "b", "title": "B", "output_folder": "outputs/b"},
        ],
    )
    assert job_index.delete_job("a") is True
    jobs = job_index.list_jobs()
    assert len(jobs) == 1
    assert jobs[0]["slug"] == "b"


def test_delete_job_removes_folder_from_disk(index_env, tmp_path):
    folder = tmp_path / "outputs" / "x"
    folder.mkdir(parents=True)
    (folder / "job.json").write_text("{}", encoding="utf-8")
    write_index(
        index_env,
        [
            {"slug": "x", "title": "X", "output_folder": "outputs/x"},
        ],
    )
    assert job_index.delete_job("x") is True
    assert not folder.exists()


def test_delete_job_returns_false_for_missing_slug(index_env):
    write_index(index_env, [])
    assert job_index.delete_job("nonexistent") is False


def test_delete_job_succeeds_when_folder_already_gone(index_env):
    write_index(
        index_env,
        [
            {"slug": "ghost", "title": "Ghost", "output_folder": "outputs/ghost"},
        ],
    )
    assert job_index.delete_job("ghost") is True
    assert len(job_index.list_jobs()) == 0


def test_delete_job_does_not_delete_paths_outside_outputs(index_env, tmp_path):
    rogue_folder = tmp_path / "rogue_data"
    rogue_folder.mkdir()
    canary = rogue_folder / "important.txt"
    canary.write_text("DO NOT DELETE", encoding="utf-8")
    write_index(
        index_env,
        [
            {"slug": "rogue", "title": "Rogue", "output_folder": "rogue_data"},
        ],
    )
    job_index.delete_job("rogue")
    assert rogue_folder.exists()
    assert canary.exists()
