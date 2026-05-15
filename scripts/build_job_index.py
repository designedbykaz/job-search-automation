# scripts/build_job_index.py
"""One-shot migration: build outputs/_index.json from existing job folders.

Usage:
    python -m scripts.build_job_index
    python -m scripts.build_job_index --no-sheet-sync

Walks outputs/ for job.json files, builds the index, then optionally
calls sync_from_sheet() to populate sheet_row and status.
"""

from __future__ import annotations

import argparse
import sys

from ui.services import job_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Build outputs/_index.json from disk")
    parser.add_argument(
        "--no-sheet-sync",
        action="store_true",
        help="Skip syncing status from Google Sheet after rebuild",
    )
    args = parser.parse_args()

    try:
        print("Rebuilding job index from disk...")
        summary = job_index.rebuild_from_disk()
        print(f"  total_jobs_found: {summary['total_jobs_found']}")
        print(f"  new_jobs: {summary['new_jobs']}")
        print(f"  missing_from_disk: {summary['missing_from_disk']}")

        if not args.no_sheet_sync:
            print("Syncing status from Google Sheet...")
            try:
                sync_summary = job_index.sync_from_sheet()
                print(f"  matched: {sync_summary['matched']}")
                print(f"  updated: {sync_summary['updated']}")
                print(f"  unmatched_sheet_rows: {sync_summary['unmatched_sheet_rows']}")
            except Exception as exc:
                print(f"  Sheet sync skipped or failed: {exc}", file=sys.stderr)

        path = job_index._index_path()
        count = len(job_index.list_jobs())
        print(f"Index path: {path}")
        print(f"Total jobs in index: {count}")
    except Exception as exc:
        print(f"Rebuild failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
