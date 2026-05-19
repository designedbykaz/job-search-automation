"""Cluster-based GOV.UK scrape: selected clusters, dedup, filter, Sheet, index."""

from __future__ import annotations

import time
from datetime import date
from typing import Any

from pipeline.dedup import create_output_folders, deduplicate, filter_by_keywords
from pipeline.logger import ensure_headers, get_sheet
from scrapers.govuk import scrape_govuk_jobs

from ui.services import clusters, job_index

try:
    import gspread
except ImportError:
    gspread = None  # type: ignore


def _log_jobs_counted(jobs: list[dict]) -> tuple[int, int]:
    """Append jobs to the Sheet; return (logged_count, error_count)."""
    sheet = get_sheet()
    ensure_headers(sheet)
    existing_urls = set(sheet.col_values(10))
    logged = 0
    errors = 0
    for job in jobs:
        try:
            job_url = job.get("url", "")
            if job_url and job_url in existing_urls:
                print(
                    f"[cluster_search] Skipping duplicate: {job.get('title')} "
                    "already in Sheet"
                )
                continue
            sheet.append_row([
                str(date.today()),
                job.get("title", ""),
                job.get("employer", ""),
                job.get("location", ""),
                job.get("cluster", ""),
                job.get("source", ""),
                job.get("closing_date", ""),
                "",
                job.get("contact_info", ""),
                job_url,
                job.get("output_folder", ""),
                "To Review",
                "",
                "",
            ])
            existing_urls.add(job_url)
            logged += 1
            print(
                f"[cluster_search] Logged: {job.get('title')} at {job.get('employer')}"
            )
            time.sleep(0.5)
        except Exception as exc:
            errors += 1
            if gspread is not None and isinstance(exc, gspread.exceptions.APIError):
                status = getattr(getattr(exc, "response", None), "status_code", None)
                if status == 429:
                    print(
                        "[cluster_search] Sheet quota exceeded (429) for "
                        f"'{job.get('title', '')}'"
                    )
                else:
                    print(
                        f"[cluster_search] Sheet API error ({status}) for "
                        f"'{job.get('title', '')}': {exc}"
                    )
            else:
                print(
                    f"[cluster_search] Error logging job '{job.get('title', '')}' at "
                    f"'{job.get('employer', '')}': {exc}"
                )
    return logged, errors


def _resolve_clusters(cluster_ids: list[str] | None) -> list[dict]:
    if cluster_ids is None:
        return clusters.list_clusters(active_only=True)
    if cluster_ids == []:
        raise ValueError(
            "cluster_ids cannot be empty; pass None to use all active clusters"
        )
    resolved: list[dict] = []
    for cluster_id in cluster_ids:
        cluster_obj = clusters.get_cluster(cluster_id)
        if cluster_obj is None:
            raise ValueError(f"Unknown cluster ID: {cluster_id}")
        resolved.append(cluster_obj)
    resolved.sort(key=lambda c: _cluster_sort_key(str(c.get("id", ""))))
    return resolved


def _cluster_sort_key(cluster_id: str) -> tuple:
    if cluster_id.startswith("CLU_"):
        try:
            return (0, int(cluster_id[4:]), cluster_id)
        except ValueError:
            pass
    return (1, 0, cluster_id)


def _build_keywords_and_map(
    resolved_clusters: list[dict],
) -> tuple[list[str], dict[str, str]]:
    keyword_list: list[str] = []
    seen_keywords: set[str] = set()
    cluster_map: dict[str, str] = {}

    for cluster_obj in resolved_clusters:
        cluster_id = str(cluster_obj.get("id", ""))
        for kw in cluster_obj.get("keywords", []):
            if not isinstance(kw, str):
                continue
            if kw not in seen_keywords:
                seen_keywords.add(kw)
                keyword_list.append(kw)
            key = kw.lower()
            if key not in cluster_map:
                cluster_map[key] = cluster_id

    if not keyword_list:
        raise ValueError("Selected clusters contain no keywords")

    return keyword_list, cluster_map


def run_cluster_search(
    cluster_ids: list[str] | None = None,
    location: str | None = None,
) -> dict[str, Any]:
    """
    Run a cluster-based scrape.

    Parameters:
        cluster_ids: list of CLU_N IDs to scrape. If None, scrape all active
            clusters. If an empty list, raise ValueError.
        location: optional location filter to pass to the scraper. If None,
            the scraper's default behaviour applies (no location filter).

    Returns a dict with the result summary.
    """
    resolved = _resolve_clusters(cluster_ids)
    clusters_used = [str(c.get("id", "")) for c in resolved if c.get("id")]
    keyword_list, cluster_map = _build_keywords_and_map(resolved)

    loc = (location or "").strip()
    if loc:
        keyword_list = [f"{kw} {loc}".strip() for kw in keyword_list]

    print(
        f"[cluster_search] Scraping with {len(keyword_list)} keywords "
        f"across {len(clusters_used)} clusters..."
    )

    scraped_jobs = scrape_govuk_jobs(keywords=keyword_list)
    scraped = len(scraped_jobs)
    print(f"[cluster_search] Scraped {scraped} raw results.")

    deduped = deduplicate(scraped_jobs)
    deduplicated = len(deduped)
    print(f"[cluster_search] After dedup: {deduplicated} unique jobs.")

    matched_jobs = filter_by_keywords(deduped, cluster_map)
    matched = len(matched_jobs)
    print(f"[cluster_search] After filter: {matched} matched jobs.")

    print("[cluster_search] Creating output folders...")
    matched_jobs = create_output_folders(matched_jobs)

    print("[cluster_search] Logging to Sheet...")
    try:
        logged_to_sheet, sheet_errors = _log_jobs_counted(matched_jobs)
    except Exception as exc:
        logged_to_sheet = 0
        sheet_errors = len(matched_jobs)
        print(f"[cluster_search] Sheet logging failed entirely: {exc}")

    if sheet_errors:
        print(
            f"[cluster_search] Sheet errors: {sheet_errors} "
            "(jobs still on disk and in index)."
        )

    print("[cluster_search] Rebuilding index...")
    job_index.rebuild_from_disk()
    job_index.sync_from_sheet()
    indexed = len(job_index.list_jobs())

    print(
        f"[cluster_search] Done. {matched} jobs scraped, "
        f"{sheet_errors} failed Sheet write."
    )

    return {
        "scraped": scraped,
        "deduplicated": deduplicated,
        "matched": matched,
        "logged_to_sheet": logged_to_sheet,
        "sheet_errors": sheet_errors,
        "indexed": indexed,
        "clusters_used": clusters_used,
    }
