"""Open search: ad hoc GOV.UK job queries from the Run page."""

from __future__ import annotations

from typing import Any

from pipeline.dedup import deduplicate
from pipeline.logger import log_jobs
from scrapers.govuk import scrape_govuk_jobs


def run_open_search(terms: list[str], location: str) -> tuple[bool, str | None, dict[str, Any]]:
    """Validate, scrape, dedup, tag, log. Returns (ok, error, summary_dict)."""
    stripped = [t.strip() for t in terms if t and t.strip()]
    if not stripped:
        return False, "Enter at least one search term.", {}

    warnings: list[str] = []
    valid_terms: list[str] = []
    for t in stripped:
        if len(t) < 2:
            warnings.append(f'Ignored term shorter than 2 characters: "{t}"')
        else:
            valid_terms.append(t)

    if not valid_terms:
        return (
            False,
            "No valid search terms left after removing terms shorter than 2 characters.",
            {},
        )

    loc = location.strip()
    queries = [f"{term} {loc}".strip() for term in valid_terms]

    jobs = scrape_govuk_jobs(keywords=queries)
    unique_jobs = deduplicate(jobs)
    found = len(unique_jobs)
    for job in unique_jobs:
        job["cluster"] = "open_search"

    log_jobs(unique_jobs)

    summary: dict[str, Any] = {
        "found": found,
        "unique": len(unique_jobs),
        "term_count": len(valid_terms),
        "warnings": warnings,
    }
    return True, None, summary
