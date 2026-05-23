"""Pipeline run state at outputs/_pipeline_state.json."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_STATE: dict[str, Any] = {
    "version": 1,
    "state": "idle",
    "last_run_finished": "",
    "last_run_summary": "",
    "detail": "",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _state_path() -> Path:
    return _repo_root() / "outputs" / "_pipeline_state.json"


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


def _read_state() -> dict:
    path = _state_path()
    if not path.is_file():
        return json.loads(json.dumps(_DEFAULT_STATE))
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _merge_with_default(data: dict) -> dict:
    merged = json.loads(json.dumps(_DEFAULT_STATE))
    for key in _DEFAULT_STATE:
        if key in data:
            merged[key] = data[key]
    return merged


def get_state() -> dict:
    """Return the current pipeline state dict.

    If the file is missing or cannot be read, return a copy of the
    default state (idle, no last run). Never raises.
    """
    try:
        raw = _read_state()
        if not isinstance(raw, dict):
            return json.loads(json.dumps(_DEFAULT_STATE))
        return _merge_with_default(raw)
    except Exception:
        return json.loads(json.dumps(_DEFAULT_STATE))


def set_running() -> None:
    """Mark the pipeline as running. Preserves last_run_finished and
    last_run_summary from the previous run. Fail-soft: no-ops on error.
    """
    try:
        current = get_state()
        data = _merge_with_default(current)
        data["state"] = "running"
        data["detail"] = ""
        _atomic_write_json(_state_path(), data)
    except Exception:
        pass


def set_idle(summary: str = "") -> None:
    """Mark the pipeline as idle after a successful run. Stamps
    last_run_finished with the current UTC time and stores summary.
    Clears detail. Fail-soft: no-ops on error.
    """
    try:
        data = _merge_with_default(get_state())
        data["state"] = "idle"
        data["last_run_finished"] = _now_iso()
        data["last_run_summary"] = summary
        data["detail"] = ""
        _atomic_write_json(_state_path(), data)
    except Exception:
        pass


def set_error(detail: str = "") -> None:
    """Mark the pipeline as errored. Stores detail as the error message.
    Does not change last_run_finished. Fail-soft: no-ops on error.
    """
    try:
        data = _merge_with_default(get_state())
        data["state"] = "error"
        data["detail"] = detail
        _atomic_write_json(_state_path(), data)
    except Exception:
        pass
