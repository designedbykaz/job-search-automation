"""Disk-backed keyword clusters at config/clusters.json (Stage 1 data layer)."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_CLUSTER_ID_RE = re.compile(r"^CLU_(\d+)$")

_DEFAULT_CLUSTERS: dict[str, Any] = {
    "version": 1,
    "clusters": {},
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _clusters_path() -> Path:
    return _repo_root() / "config" / "clusters.json"


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


def _read_file() -> dict:
    path = _clusters_path()
    if not path.is_file():
        return json.loads(json.dumps(_DEFAULT_CLUSTERS))
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError("clusters.json root must be an object")
    clusters = data.get("clusters")
    if clusters is None:
        data["clusters"] = {}
    elif not isinstance(clusters, dict):
        raise TypeError("clusters.json 'clusters' must be an object")
    data.setdefault("version", 1)
    return data


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _next_id(existing_ids: list[str]) -> str:
    max_n = 0
    for cid in existing_ids:
        m = _CLUSTER_ID_RE.match(cid)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"CLU_{max_n + 1}"


def _sort_key(cluster_id: str) -> tuple:
    m = _CLUSTER_ID_RE.match(cluster_id)
    if m:
        return (0, int(m.group(1)), cluster_id)
    return (1, 0, cluster_id)


def _normalize_keywords(keywords: list[str]) -> list[str]:
    out: list[str] = []
    for kw in keywords:
        if not isinstance(kw, str):
            continue
        stripped = kw.strip()
        if stripped:
            out.append(stripped)
    return out


def _cluster_with_id(cluster_id: str, record: dict) -> dict:
    return {"id": cluster_id, **record}


def _write_clusters(data: dict) -> None:
    _atomic_write_json(_clusters_path(), data)


def list_clusters(active_only: bool = False) -> list[dict]:
    """Return all clusters as a list of dicts. Each dict includes the 'id' field
    in addition to the stored fields (label, keywords, active, created_at).
    Sorted by id numeric component ascending (CLU_1, CLU_2, ...).
    """
    data = _read_file()
    clusters = data.get("clusters", {})
    if not isinstance(clusters, dict):
        return []
    rows: list[dict] = []
    for cluster_id, record in clusters.items():
        if not isinstance(record, dict):
            continue
        if active_only and not record.get("active"):
            continue
        rows.append(_cluster_with_id(cluster_id, record))
    rows.sort(key=lambda r: _sort_key(str(r.get("id", ""))))
    return rows


def get_cluster(cluster_id: str) -> dict | None:
    """Return a single cluster by ID, or None if not found.
    The returned dict includes the 'id' field.
    """
    data = _read_file()
    clusters = data.get("clusters", {})
    if not isinstance(clusters, dict):
        return None
    record = clusters.get(cluster_id)
    if not isinstance(record, dict):
        return None
    return _cluster_with_id(cluster_id, record)


def create_cluster(label: str, keywords: list[str], active: bool = True) -> dict:
    """Create a new cluster with a freshly assigned ID (next available CLU_N).
    Strips whitespace from label and from each keyword. Lowercases nothing
    (display labels keep their case; keywords keep theirs for now).
    Raises ValueError if label is empty after stripping.
    Returns the created cluster dict including its assigned id.
    """
    stripped_label = label.strip()
    if not stripped_label:
        raise ValueError("label must not be empty")
    normalized_keywords = _normalize_keywords(keywords)
    data = _read_file()
    clusters = data.setdefault("clusters", {})
    if not isinstance(clusters, dict):
        raise TypeError("clusters.json 'clusters' must be an object")
    cluster_id = _next_id(list(clusters.keys()))
    record = {
        "label": stripped_label,
        "keywords": normalized_keywords,
        "active": active,
        "created_at": _now_iso(),
    }
    clusters[cluster_id] = record
    data["version"] = data.get("version", 1)
    _write_clusters(data)
    return _cluster_with_id(cluster_id, record)


def update_cluster(
    cluster_id: str,
    label: str | None = None,
    keywords: list[str] | None = None,
    active: bool | None = None,
) -> bool:
    """Update one or more fields of an existing cluster. Only fields that are
    not None are touched. Returns True if updated, False if cluster_id not found.
    Raises ValueError if label is provided but is empty after stripping.
    """
    data = _read_file()
    clusters = data.get("clusters", {})
    if not isinstance(clusters, dict):
        return False
    record = clusters.get(cluster_id)
    if not isinstance(record, dict):
        return False
    changed = False
    if label is not None:
        stripped_label = label.strip()
        if not stripped_label:
            raise ValueError("label must not be empty")
        record["label"] = stripped_label
        changed = True
    if keywords is not None:
        record["keywords"] = _normalize_keywords(keywords)
        changed = True
    if active is not None:
        record["active"] = active
        changed = True
    if changed:
        _write_clusters(data)
    return True


def delete_cluster(cluster_id: str) -> bool:
    """Delete a cluster. Returns True if removed, False if not found."""
    data = _read_file()
    clusters = data.get("clusters", {})
    if not isinstance(clusters, dict):
        return False
    if cluster_id not in clusters:
        return False
    del clusters[cluster_id]
    _write_clusters(data)
    return True


def get_active_keywords() -> list[str]:
    """Convenience for scrapers. Returns a flat list of all keywords from all
    active clusters. Duplicate keywords (appearing in multiple clusters) are
    deduplicated, preserving first appearance order.
    """
    seen: set[str] = set()
    out: list[str] = []
    for cluster in list_clusters(active_only=True):
        for kw in cluster.get("keywords", []):
            if not isinstance(kw, str):
                continue
            if kw in seen:
                continue
            seen.add(kw)
            out.append(kw)
    return out


def get_keyword_to_cluster_map() -> dict[str, str]:
    """Convenience for tagging. Returns a dict mapping lowercased keyword to
    cluster_id. If a keyword appears in multiple active clusters, the first
    cluster (by ID order) wins. Only active clusters are included.
    """
    mapping: dict[str, str] = {}
    for cluster in list_clusters(active_only=True):
        cluster_id = str(cluster.get("id", ""))
        for kw in cluster.get("keywords", []):
            if not isinstance(kw, str):
                continue
            key = kw.lower()
            if key not in mapping:
                mapping[key] = cluster_id
    return mapping
