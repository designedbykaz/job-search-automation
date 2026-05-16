"""Google Sheets read/update for the Jobs UI. Does not import pipeline.logger."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
STATUS_COL = 12  # column L


def is_configured() -> bool:
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    if not creds_path or not sheet_id:
        return False
    return Path(creds_path).is_file()


def _open_sheet():
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    path = Path(creds_path) if creds_path else None
    creds = Credentials.from_service_account_file(path, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)
    return spreadsheet.sheet1


def _normalize_status(cell: str) -> str:
    raw = (cell or "").strip().lower()
    if raw == "to review":
        return "to_review"
    if raw == "approved":
        return "approved"
    if raw == "pdf ready":
        return "pdf_ready"
    return "to_review"


def _pad_row(row: list[Any], length: int = 14) -> list[str]:
    cells = [str(c).strip() if c is not None else "" for c in row]
    while len(cells) < length:
        cells.append("")
    return cells[:length]


def _resolved_output_folder(output_folder: str | None) -> Path | None:
    if not output_folder or not str(output_folder).strip():
        return None
    p = Path(output_folder.strip())
    if not p.is_absolute():
        p = REPO_ROOT / p
    return p


def _row_to_job(cells: list[str], row_num: int) -> dict[str, Any]:
    listing_url = cells[9]
    status_internal = _normalize_status(cells[11])
    notes = cells[13]
    output_folder = cells[10]

    description: list[str] = []
    if output_folder and str(output_folder).strip():
        resolved = _resolved_output_folder(output_folder)
        if resolved is not None:
            job_json_path = resolved / "job.json"
            if job_json_path.is_file():
                try:
                    job_data = json.loads(job_json_path.read_text(encoding="utf-8"))
                    raw_desc = job_data.get("description", "")
                    if isinstance(raw_desc, str) and raw_desc.strip():
                        description = [raw_desc.strip()]
                    elif isinstance(raw_desc, list):
                        description = [
                            s for x in raw_desc if (s := str(x).strip())
                        ]
                except Exception:
                    pass

    if not description and notes:
        description = [notes]

    return {
        "row": row_num,
        "title": cells[1],
        "employer": cells[2],
        "location": cells[3],
        "cluster": cells[4],
        "source": cells[5],
        "closing_date": cells[6],
        "date_found": cells[0],
        "listing_url": listing_url,
        "output_folder": output_folder,
        "status": status_internal,
        "priority": cells[7],
        "contact_info": cells[8],
        "applied": cells[12],
        "notes": notes,
        "description": description,
    }


def get_jobs(status_filter: str | None = None) -> list[dict[str, Any]]:
    """Read job rows from the Sheet. Returns empty list if unavailable or on error."""
    if not is_configured():
        return []
    try:
        sheet = _open_sheet()
        values = sheet.get_all_values()
    except Exception as exc:
        print(f"Warning: could not read Google Sheet for Jobs UI: {exc}")
        return []

    jobs: list[dict[str, Any]] = []
    for idx, row in enumerate(values[1:], start=2):
        cells = _pad_row(row)
        if not cells[9]:
            continue
        job = _row_to_job(cells, idx)
        jobs.append(job)

    if not status_filter or status_filter == "all":
        return jobs

    want = status_filter.strip().lower()
    return [j for j in jobs if j["status"] == want]

def approve_job(row: int) -> bool:
    """Set Status column to Approved for this row."""
    if row < 2:
        return False
    if not is_configured():
        return False
    try:
        sheet = _open_sheet()
        sheet.update_cell(row, STATUS_COL, "Approved")
        return True
    except Exception as exc:
        print(f"Warning: could not approve Sheet row {row}: {exc}")
        return False
