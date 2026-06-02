"""Clear the job store for a fresh-scrape clean slate.

Usage:
    python -m scripts.clear_job_index                # clear index + output folders
    python -m scripts.clear_job_index --with-sheet   # also wipe the Sheet's data rows

Clears the local index (backing it up to outputs/_index.json.bak) and deletes
every job output folder under outputs/. Because scrape dedup is now index-based,
this also resets dedup, so the next scrape treats all listings as new. Pass
--with-sheet to also delete every data row from the Google Sheet (header kept).

Destructive: deleting the output folders removes tailored CVs and PDFs. This is
the CLI counterpart of the planned "Clear all" button in the UI; both call
ui.services.reset.clear_all.
"""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

load_dotenv()  # GOOGLE_CREDENTIALS_PATH / GOOGLE_SHEETS_ID for the optional Sheet wipe

from ui.services import reset


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clear the local job index and output folders, optionally the Sheet."
    )
    parser.add_argument(
        "--with-sheet",
        action="store_true",
        help="Also delete all data rows from the Google Sheet (keeps the header).",
    )
    args = parser.parse_args()

    summary = reset.clear_all(with_sheet=args.with_sheet)

    print(f"Cleared {summary['index_cleared']} job(s) from the index.")
    if summary["index_backup"]:
        print(f"Index backup: {summary['index_backup']}")
    print(f"Removed {summary['folders_removed']} output folder(s).")

    if args.with_sheet:
        if summary["sheet_error"]:
            print(f"Sheet not wiped: {summary['sheet_error']} (local clear still done).")
        else:
            print(f"Cleared {summary['sheet_cleared']} data row(s) from the Sheet (header kept).")


if __name__ == "__main__":
    main()
