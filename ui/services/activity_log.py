"""Append-only activity log at outputs/_activity.json."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_EVENTS = 100

_DEFAULT_LOG: dict[str, Any] = {"version": 1, "events": []}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _log_path() -> Path:
    return _repo_root() / "outputs" / "_activity.json"


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


def _read_log() -> dict:
    path = _log_path()
    if not path.is_file():
        return json.loads(json.dumps(_DEFAULT_LOG))
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _append(event: dict) -> None:
    data = _read_log()
    events = data.get("events", [])
    if not isinstance(events, list):
        events = []
    events.append(event)
    events = events[-MAX_EVENTS:]
    data["version"] = 1
    data["events"] = events
    _atomic_write_json(_log_path(), data)


def record_scrape(source: str, terms: list[str], location: str, jobs_added: int) -> None:
    """Append a scrape event to the activity log. Silently no-ops on error."""
    try:
        _append(
            {
                "type": "scrape",
                "timestamp": _now_iso(),
                "details": {
                    "source": source,
                    "terms": terms,
                    "location": location,
                    "jobs_added": jobs_added,
                },
            }
        )
    except Exception:
        pass


def record_status_change(
    slug: str,
    title: str,
    employer: str,
    from_status: str,
    to_status: str,
) -> None:
    """Append a status change event to the activity log. Silently no-ops on error."""
    try:
        _append(
            {
                "type": "status_change",
                "timestamp": _now_iso(),
                "details": {
                    "slug": slug,
                    "title": title,
                    "employer": employer,
                    "from": from_status,
                    "to": to_status,
                },
            }
        )
    except Exception:
        pass


def get_recent(limit: int = 10) -> list[dict]:
    """Return the most recent events, newest first, up to `limit` entries.

    Returns an empty list if the log file does not exist or cannot be read.
    """
    try:
        path = _log_path()
        if not path.is_file():
            return []
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        events = data.get("events", [])
        if not isinstance(events, list):
            return []
        tail = events[-limit:] if limit > 0 else []
        return list(reversed(tail))
    except Exception:
        return []


def _parse_utc_timestamp(iso_timestamp: str) -> datetime | None:
    try:
        s = iso_timestamp.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def format_relative_time(iso_timestamp: str) -> str:
    """Format an ISO UTC timestamp as a human relative time.

    Returns 'just now', 'X minutes ago', 'X hours ago', 'X days ago' for
    times within 30 days, or an ISO date (YYYY-MM-DD) for older times.
    Returns the input unchanged if parsing fails.
    """
    try:
        parsed = _parse_utc_timestamp(iso_timestamp)
        if parsed is None:
            return iso_timestamp
        now = _utc_now()
        if parsed > now:
            return "just now"
        delta = now - parsed
        total_seconds = int(delta.total_seconds())
        if total_seconds < 60:
            return "just now"
        minutes = total_seconds // 60
        if total_seconds < 3600:
            return (
                f"{minutes} minute ago"
                if minutes == 1
                else f"{minutes} minutes ago"
            )
        hours = total_seconds // 3600
        if total_seconds < 86400:
            return (
                f"{hours} hour ago" if hours == 1 else f"{hours} hours ago"
            )
        days = total_seconds // 86400
        if days < 30:
            return f"{days} day ago" if days == 1 else f"{days} days ago"
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return iso_timestamp
