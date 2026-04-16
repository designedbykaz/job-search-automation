# main.py - master orchestration: scrape, dedup, filter, folders, tailor, log

import argparse

from scrapers.govuk import scrape_govuk_jobs

# from scrapers.nhs import scrape_nhs_jobs
# from scrapers.totaljobs import scrape_totaljobs

from pipeline.dedup import deduplicate, filter_by_keywords, create_output_folders
from pipeline.tailor import tailor_cv, tailor_cover_letter
from pipeline.logger import log_jobs
from pathlib import Path
from dotenv import load_dotenv
import json, os

load_dotenv()


def run_pipeline():
    parser = argparse.ArgumentParser(
        description="Job application pipeline"
    )
    parser.add_argument(
        "--mode",
        choices=["full", "scrape", "tailor"],
        default="full",
        help=(
            "full = scrape + tailor + log, "
            "scrape = scrape + log only (no API calls), "
            "tailor = tailor already-scraped jobs only"
        )
    )
    args = parser.parse_args()
    mode = args.mode
    print(f"Running in mode: {mode}")

    # TAILOR-ONLY — load from Sheet instead of scraping
    if mode == "tailor":
        print("Tailor-only mode: loading approved jobs from Google Sheet...")
        print("TODO: implement Sheet-to-jobs loader")
        print("This mode is not yet fully implemented.")
        return

    # STAGE 1 - SCRAPE
    print("Stage 1: Scraping job boards...")
    govuk_jobs = scrape_govuk_jobs()
    # nhs_jobs = scrape_nhs_jobs()
    # totaljobs_jobs = scrape_totaljobs()
    all_jobs = govuk_jobs
    print(f"Total raw results: {len(all_jobs)}")

    # STAGE 2 - DEDUPLICATE AND FILTER
    print("Stage 2: Deduplicating and filtering...")
    unique_jobs = deduplicate(all_jobs)
    filtered_jobs = filter_by_keywords(unique_jobs)
    jobs = create_output_folders(filtered_jobs)
    print(f"Jobs after dedup and filter: {len(jobs)}")

    # STAGE 3 - TAILOR
    if mode in ("full",):
        print("Stage 3: Tailoring CV and cover letter for each job...")
        for job in jobs:
            try:
                output_folder = Path(job["output_folder"])
                tailor_cv(job, output_folder)
                tailor_cover_letter(job, output_folder)
            except Exception as exc:
                print(f"Error tailoring job {job.get('title', '')!r}: {exc}")
    else:
        print("Stage 3: Skipped (scrape-only mode)")

    # STAGE 4 - LOG
    if mode in ("full", "scrape"):
        print("Stage 4: Logging to Google Sheets...")
        log_jobs(jobs)
    else:
        print("Stage 4: Skipped (tailor-only mode)")

    print(
        "Pipeline complete. Review your Google Sheet and approve jobs "
        "before running render_approved.py"
    )


if __name__ == "__main__":
    run_pipeline()
