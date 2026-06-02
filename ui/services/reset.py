"""Clear-all reset: wipe the local job index and job folders, optionally the Sheet.

This is the single orchestration point for resetting the job store, shared by the
CLI (``scripts/clear_job_index.py``) and intended for a future "Clear all" button
in the Flask UI. It returns a structured summary a route can render directly.

Design: the local index and output folders are the source of truth, so a reset
clears both, which also resets the (now index-based) scrape dedup. The Google
Sheet is a downstream mirror, so wiping it is opt-in and its failure never blocks
the local clear.
"""

from __future__ import annotations

from typing import Any

from ui.services import job_index


def clear_all(*, with_sheet: bool = False) -> dict[str, Any]:
    """Reset the job store. Always clears the index and output folders; clears
    the Sheet too when ``with_sheet`` is set.

    Returns a summary:
        {
          "index_cleared": int,        # jobs removed from the index
          "index_backup": str | None,  # path to the index backup
          "folders_removed": int,      # output subfolders deleted
          "sheet_cleared": int | None, # Sheet rows removed, or None if not attempted
          "sheet_error": str | None,   # reason the Sheet wipe was skipped or failed
        }
    """
    index_result = job_index.reset_index()
    folders_result = job_index.clear_output_folders()

    summary: dict[str, Any] = {
        "index_cleared": index_result["cleared"],
        "index_backup": index_result["backup"],
        "folders_removed": folders_result["removed"],
        "sheet_cleared": None,
        "sheet_error": None,
    }

    if with_sheet:
        # Imported lazily so the local clear never depends on gspread/credentials.
        from ui.services import sheets

        if not sheets.is_configured():
            summary["sheet_error"] = "Sheet not configured (credentials/ID missing)"
        else:
            try:
                summary["sheet_cleared"] = sheets.clear_data_rows()["cleared"]
            except Exception as exc:  # noqa: BLE001 - report, never block the local clear
                summary["sheet_error"] = str(exc)

    return summary
