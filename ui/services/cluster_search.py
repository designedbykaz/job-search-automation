"""Cluster-based GOV.UK scrape: selected clusters, dedup, filter, Sheet, index."""

from __future__ import annotations

import time
from datetime import date
from typing import Any

from pipeline.dedup import create_output_folders, deduplicate, filter_by_keywords
from pipeline.logger import ensure_headers, get_sheet
from scrapers.govuk import scrape_govuk_jobs

from ui.services import clusters, job_index, pipeline_state

try:
    import gspread
except ImportError:
    gspread = None  # type: ignore


def _log_jobs_counted(jobs: list[dict]) -> tuple[int, int]:
    """Append jobs to the Sheet as a downstream log; return (logged, errors).

    No dedup here. The index is the source of truth and already deduped these
    jobs before their folders were created, so the Sheet is just a secondary
    mirror of what was added; a Sheet failure never affects the index.
    """
    sheet = get_sheet()
    ensure_headers(sheet)
    logged = 0
    errors = 0
    for job in jobs:
        try:
            job_url = job.get("url", "")
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


def _filter_unseen(jobs: list[dict], known_urls: set[str]) -> list[dict]:
    """Drop jobs whose listing URL is already in the index (cross-run dedup).

    The local index is the source of truth for what has been seen, so an empty
    index (e.g. just after a clear) means nothing is filtered and every listing
    is taken as new. Jobs with no URL cannot be matched and are kept.
    """
    unseen: list[dict] = []
    for job in jobs:
        url = job.get("url", "")
        if url and url in known_urls:
            print(f"[cluster_search] Skipping (already in index): {job.get('title')}")
            continue
        unseen.append(job)
    return unseen


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
    pipeline_state.set_running()
    try:
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

        # Cross-run dedup against the local index (the source of truth), by
        # listing URL. An empty index means nothing is skipped, so a clear
        # resets dedup automatically.
        known_urls = {
            j.get("listing_url", "")
            for j in job_index.list_jobs()
            if j.get("listing_url")
        }
        new_jobs = _filter_unseen(matched_jobs, known_urls)
        already_indexed = matched - len(new_jobs)
        print(
            f"[cluster_search] {already_indexed} already in index, "
            f"{len(new_jobs)} new."
        )

        print("[cluster_search] Creating output folders for new jobs...")
        new_jobs = create_output_folders(new_jobs)

        # The Sheet is now a downstream log only; failures never touch the index.
        print("[cluster_search] Logging new jobs to Sheet...")
        try:
            logged_to_sheet, sheet_errors = _log_jobs_counted(new_jobs)
        except Exception as exc:
            logged_to_sheet = 0
            sheet_errors = len(new_jobs)
            print(f"[cluster_search] Sheet logging failed entirely: {exc}")

        if sheet_errors:
            print(
                f"[cluster_search] Sheet errors: {sheet_errors} "
                "(jobs still on disk and in index)."
            )

        # Disk -> index (local source of truth). Then map sheet_row onto the new
        # entries from the Sheet WITHOUT pulling status: the UI actions are keyed
        # on the sheet row, but the index, not the Sheet, owns status.
        print("[cluster_search] Rebuilding index from disk...")
        job_index.rebuild_from_disk()
        try:
            job_index.sync_from_sheet(update_status=False)
        except Exception as exc:
            print(f"[cluster_search] sheet_row sync skipped: {exc}")
        indexed = len(job_index.list_jobs())

        print(
            f"[cluster_search] Done. {len(new_jobs)} new of {matched} matched, "
            f"{sheet_errors} failed Sheet write."
        )

        summary = {
            "scraped": scraped,
            "deduplicated": deduplicated,
            "matched": matched,
            "already_indexed": already_indexed,
            "new_jobs": len(new_jobs),
            "logged_to_sheet": logged_to_sheet,
            "sheet_errors": sheet_errors,
            "indexed": indexed,
            "clusters_used": clusters_used,
        }
        pipeline_state.set_idle(f"{len(new_jobs)} new jobs")
        return summary
    except Exception as exc:
        pipeline_state.set_error(str(exc))
        raise
