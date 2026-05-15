"""Disk-backed job index at outputs/_index.json (Stage 1 data layer)."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALID_STATUSES = frozenset({"to_review", "approved", "pdf_ready", "archived"})
_DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_DEFAULT_INDEX: dict[str, Any] = {
    "version": 1,
    "jobs": [],
    "last_sheet_sync_at": None,
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _index_path() -> Path:
    return _repo_root() / "outputs" / "_index.json"


def _resolved_output_folder(output_folder: str | None) -> Path | None:
    if not output_folder or not str(output_folder).strip():
        return None
    p = Path(output_folder.strip())
    if not p.is_absolute():
        p = _repo_root() / p
    return p


def _atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        if tmp.is_file():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


def _read_index() -> dict:
    path = _index_path()
    if not path.is_file():
        return json.loads(json.dumps(_DEFAULT_INDEX))
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _has_tailored_cv(folder: Path) -> bool:
    return (folder / "cv_tailored.json").is_file()


def _derive_date_found(raw: dict, slug: str) -> str:
    d = raw.get("date")
    if isinstance(d, str) and d.strip():
        return d.strip()
    first = slug.split("/")[0] if slug else ""
    if _DATE_PREFIX_RE.match(first):
        return first
    return ""


def _entry_from_job_json(
    folder: Path,
    slug: str,
    raw: dict,
    old: dict | None,
) -> dict:
    listing_url = raw.get("url") if isinstance(raw.get("url"), str) else ""
    if not listing_url:
        listing_url = ""
    entry = {
        "slug": slug,
        "sheet_row": None,
        "title": str(raw.get("title", "") or ""),
        "employer": str(raw.get("employer", "") or ""),
        "location": str(raw.get("location", "") or ""),
        "date_found": _derive_date_found(raw, slug),
        "closing_date": str(raw.get("closing_date", "") or ""),
        "cluster": str(raw.get("cluster", "") or ""),
        "source": str(raw.get("source", "") or ""),
        "listing_url": listing_url,
        "output_folder": "outputs/" + slug.replace("\\", "/"),
        "status": "to_review",
        "has_tailored_cv": _has_tailored_cv(folder),
    }
    if old:
        if old.get("sheet_row") is not None:
            entry["sheet_row"] = old["sheet_row"]
        if old.get("status") in VALID_STATUSES:
            entry["status"] = old["status"]
    return entry


def list_jobs(status_filter: str | None = None, search: str | None = None) -> list[dict]:
    """Return all jobs from the index, optionally filtered.

    status_filter: one of the valid statuses, or None for all.
    search: case-insensitive substring match on title or employer, or None.
    Returns an empty list if the index file does not exist.
    """
    path = _index_path()
    if not path.is_file():
        return []
    data = _read_index()
    jobs = list(data.get("jobs", []))
    if status_filter is not None:
        want = status_filter.strip()
        jobs = [j for j in jobs if j.get("status") == want]
    if search is not None and search.strip():
        needle = search.strip().lower()
        jobs = [
            j
            for j in jobs
            if needle in str(j.get("title", "")).lower()
            or needle in str(j.get("employer", "")).lower()
        ]
    return jobs


def get_job(slug: str) -> dict | None:
    """Return a single job by slug, or None if not found."""
    if not _index_path().is_file():
        return None
    for j in _read_index().get("jobs", []):
        if j.get("slug") == slug:
            return j
    return None


def get_job_by_row(sheet_row: int) -> dict | None:
    """Return a single job by sheet_row, or None if not found.

    Maintained for compatibility with code that thinks in sheet rows.
    """
    if not _index_path().is_file():
        return None
    for j in _read_index().get("jobs", []):
        if j.get("sheet_row") == sheet_row:
            return j
    return None


def set_status(slug: str, new_status: str) -> bool:
    """Update a job's status in the index file.

    Returns True if updated, False if the slug was not found.
    Raises ValueError if new_status is not a valid status.
    Write must be atomic: write to temp file, then rename.
    """
    if new_status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {new_status!r}")
    data = _read_index()
    found = False
    for j in data.get("jobs", []):
        if j.get("slug") == slug:
            j["status"] = new_status
            found = True
            break
    if not found:
        return False
    _atomic_write_json(_index_path(), data)
    return True


def add_job(job: dict) -> None:
    """Add a new job to the index. Idempotent on slug:
    if a job with the same slug already exists, it is replaced.
    Write must be atomic.
    """
    slug = job.get("slug")
    if not slug or not str(slug).strip():
        raise ValueError("job must include non-empty slug")
    output_folder = job.get("output_folder")
    if not output_folder or not str(output_folder).strip():
        raise ValueError("job must include non-empty output_folder")
    slug = str(slug).strip()
    data = _read_index()
    jobs = list(data.get("jobs", []))
    resolved = _resolved_output_folder(str(output_folder))
    if resolved is None:
        has_cv = False
    else:
        has_cv = _has_tailored_cv(resolved)
    entry = {
        "slug": slug,
        "sheet_row": job.get("sheet_row"),
        "title": str(job.get("title", "") or ""),
        "employer": str(job.get("employer", "") or ""),
        "location": str(job.get("location", "") or ""),
        "date_found": str(job.get("date_found", "") or ""),
        "closing_date": str(job.get("closing_date", "") or ""),
        "cluster": str(job.get("cluster", "") or ""),
        "source": str(job.get("source", "") or ""),
        "listing_url": str(job.get("listing_url", "") or ""),
        "output_folder": str(output_folder).strip().replace("\\", "/"),
        "status": job.get("status") if job.get("status") in VALID_STATUSES else "to_review",
        "has_tailored_cv": has_cv,
    }
    if entry["sheet_row"] is not None:
        entry["sheet_row"] = int(entry["sheet_row"])
    replaced = False
    for i, existing in enumerate(jobs):
        if existing.get("slug") == slug:
            jobs[i] = entry
            replaced = True
            break
    if not replaced:
        jobs.append(entry)
    data["jobs"] = jobs
    data.setdefault("version", 1)
    data.setdefault("last_sheet_sync_at", data.get("last_sheet_sync_at"))
    _atomic_write_json(_index_path(), data)


def rebuild_from_disk() -> dict:
    """Walk the outputs/ folder, read every job.json, rebuild the
    'jobs' array from scratch. Preserves status and sheet_row from
    the existing index if a slug matches; otherwise status defaults
    to 'to_review' and sheet_row to None.

    Returns a summary dict: {
        "total_jobs_found": int,
        "new_jobs": int,
        "missing_from_disk": list[str],  # slugs that were in the
                                          # old index but no longer
                                          # have a folder on disk
    }
    Write must be atomic.
    """
    old = _read_index()
    old_jobs = old.get("jobs", [])
    old_by_slug: dict[str, dict] = {}
    for j in old_jobs:
        s = j.get("slug")
        if isinstance(s, str) and s:
            old_by_slug[s] = j
    outputs_root = _repo_root() / "outputs"
    slug_to_entry: dict[str, dict] = {}
    if not outputs_root.is_dir():
        new_jobs_count = 0
        missing = sorted(old_by_slug.keys())
        out = {
            "version": 1,
            "jobs": [],
            "last_sheet_sync_at": old.get("last_sheet_sync_at"),
        }
        _atomic_write_json(_index_path(), out)
        return {
            "total_jobs_found": 0,
            "new_jobs": new_jobs_count,
            "missing_from_disk": missing,
        }

    for job_json_path in sorted(outputs_root.rglob("job.json")):
        folder = job_json_path.parent
        slug = folder.relative_to(outputs_root).as_posix()
        if slug in slug_to_entry:
            print(
                f"Warning: duplicate slug {slug!r} while rebuilding job index, using last folder",
                file=sys.stderr,
            )
        try:
            raw_text = job_json_path.read_text(encoding="utf-8")
            raw = json.loads(raw_text)
        except json.JSONDecodeError:
            print(
                f"Warning: corrupt job.json at {job_json_path}, skipping",
                file=sys.stderr,
            )
            continue
        except OSError as exc:
            print(
                f"Warning: could not read {job_json_path}: {exc}, skipping",
                file=sys.stderr,
            )
            continue
        if not isinstance(raw, dict):
            print(
                f"Warning: job.json is not an object at {job_json_path}, skipping",
                file=sys.stderr,
            )
            continue
        old_entry = old_by_slug.get(slug)
        entry = _entry_from_job_json(folder, slug, raw, old_entry)
        slug_to_entry[slug] = entry

    seen_slugs = sorted(slug_to_entry.keys())
    new_jobs_count = sum(1 for s in seen_slugs if s not in old_by_slug)
    missing_from_disk = sorted(s for s in old_by_slug if s not in slug_to_entry)
    jobs_list = [slug_to_entry[s] for s in seen_slugs]
    out = {
        "version": 1,
        "jobs": jobs_list,
        "last_sheet_sync_at": old.get("last_sheet_sync_at"),
    }
    _atomic_write_json(_index_path(), out)
    return {
        "total_jobs_found": len(seen_slugs),
        "new_jobs": new_jobs_count,
        "missing_from_disk": missing_from_disk,
    }


def sync_from_sheet() -> dict:
    """Read all jobs from the Google Sheet via sheets.get_jobs(),
    match them to the index by listing_url, and update status and
    sheet_row on the matched index entries. Does not add or remove
    jobs from the index.

    Returns a summary dict: {
        "matched": int,
        "updated": int,
        "unmatched_sheet_rows": list[int],  # sheet rows not found
                                              # in the index
    }
    Sets last_sheet_sync_at to the current ISO timestamp.
    Write must be atomic.
    """
    from ui.services import sheets

    index = _read_index()
    url_to_entry: dict[str, dict] = {}
    for j in index.get("jobs", []):
        url = j.get("listing_url")
        if isinstance(url, str) and url.strip():
            url_to_entry[url.strip()] = j
    sheet_jobs = sheets.get_jobs()
    matched = 0
    updated = 0
    unmatched: list[int] = []
    for sj in sheet_jobs:
        row = sj.get("row")
        url = sj.get("listing_url")
        if not isinstance(url, str) or not url.strip():
            if isinstance(row, int):
                unmatched.append(row)
            continue
        url = url.strip()
        entry = url_to_entry.get(url)
        if entry is None:
            if isinstance(row, int):
                unmatched.append(row)
            continue
        matched += 1
        new_status = sj.get("status")
        new_row = sj.get("row")
        changed = False
        if entry.get("sheet_row") != new_row:
            entry["sheet_row"] = new_row
            changed = True
        if entry.get("status") != new_status:
            entry["status"] = new_status
            changed = True
        if changed:
            updated += 1
    index["last_sheet_sync_at"] = datetime.now(timezone.utc).isoformat()
    _atomic_write_json(_index_path(), index)
    return {
        "matched": matched,
        "updated": updated,
        "unmatched_sheet_rows": sorted(unmatched),
    }
