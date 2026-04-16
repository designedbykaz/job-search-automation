# logger.py - append job rows to Google Sheets tracker

import gspread
from google.oauth2.service_account import Credentials
import os, json, time
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HEADERS = [
    "Date Found",
    "Job Title",
    "Employer",
    "Location",
    "Cluster",
    "Source",
    "Closing Date",
    "Priority",
    "Contact Info",
    "Job URL",
    "Output Folder",
    "Status",
    "Applied",
    "Notes",
]


def get_sheet():
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    path = Path(creds_path) if creds_path else None
    creds = Credentials.from_service_account_file(path, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)
    return spreadsheet.sheet1


def ensure_headers(sheet):
    """If row 1 is missing or not HEADERS, write HEADERS to row 1."""
    try:
        row1 = sheet.row_values(1)
    except Exception as exc:
        print(f"Warning: could not read row 1 for header check: {exc}")
        row1 = []

    if row1 == HEADERS:
        return

    try:
        try:
            sheet.update(range_name="A1:N1", values=[HEADERS])
        except TypeError:
            sheet.update("A1:N1", [HEADERS])
    except Exception as exc:
        print(f"Error writing header row to sheet: {exc}")
        raise


def log_jobs(jobs):
    sheet = get_sheet()
    ensure_headers(sheet)
    existing_urls = set(sheet.col_values(10))  # Column J = Job URL, read once
    logged = 0
    for job in jobs:
        try:
            job_url = job.get("url", "")
            if job_url and job_url in existing_urls:
                print(f"Skipping duplicate: {job.get('title')} — already in Sheet")
                continue
            sheet.append_row([
                str(date.today()),
                job.get("title", ""),
                job.get("employer", ""),
                job.get("location", ""),
                job.get("cluster", ""),
                job.get("source", ""),
                job.get("closing_date", ""),
                "",                          # Priority — set manually
                job.get("contact_info", ""),
                job_url,
                job.get("output_folder", ""),
                "To Review",
                "",                          # Applied — set manually
                "",                          # Notes — set manually
            ])
            existing_urls.add(job_url)       # catch within-batch duplicates
            logged += 1
            print(f"Logged: {job.get('title')} at {job.get('employer')}")
            time.sleep(0.5)
        except Exception as exc:
            print(
                f"Error logging job '{job.get('title', '')}' at "
                f"'{job.get('employer', '')}': {exc}"
            )
            continue
    print(f"Logged {logged} jobs to Google Sheets")
