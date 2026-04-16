# render_approved.py - render PDFs for sheet rows marked Approved

import json
import os
import re
from pathlib import Path

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from weasyprint import HTML

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheet():
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    path = Path(creds_path) if creds_path else None
    creds = Credentials.from_service_account_file(path, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)
    return spreadsheet.sheet1


def fill_template(tailored_cv_dict):
    template_path = Path("templates") / "cv_template.html"
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    for key, value in tailored_cv_dict.items():
        placeholder = f"{{{{{key}}}}}"
        if isinstance(value, list):
            value_str = ", ".join(str(item) for item in value)
        else:
            value_str = str(value)
        html = html.replace(placeholder, value_str)

    remaining = set(re.findall(r"{{([^}]+)}}", html))
    if remaining:
        print("Warning: Unreplaced placeholders found:")
        for name in sorted(remaining):
            print(f"- {{{{{name}}}}}")

    return html


def render_pdf(html_string, output_folder):
    out = Path(output_folder)
    out.mkdir(parents=True, exist_ok=True)
    rendered_html_path = out / "cv_rendered.html"
    pdf_path = out / "cv_output.pdf"

    with open(rendered_html_path, "w", encoding="utf-8") as f:
        f.write(html_string)

    HTML(filename=str(rendered_html_path)).write_pdf(str(pdf_path))
    print(f"PDF saved: {pdf_path}")
    return pdf_path


def _find_row_and_status_col(sheet, job_url):
    """Return (row_number_1based, status_col_1based) for row matching Job URL, or (None, None)."""
    all_vals = sheet.get_all_values()
    if not all_vals:
        return None, None

    headers = all_vals[0]
    try:
        job_url_idx = headers.index("Job URL")
        status_idx = headers.index("Status")
    except ValueError:
        return None, None

    target = (job_url or "").strip()
    for i, row in enumerate(all_vals[1:], start=2):
        while len(row) <= job_url_idx:
            row.append("")
        if row[job_url_idx].strip() == target:
            return i, status_idx + 1
    return None, None


def render_approved():
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        approved = [
            r for r in records if str(r.get("Status", "")).strip() == "Approved"
        ]
        print(f"Found {len(approved)} approved jobs to render")

        for row in approved:
            try:
                output_folder_raw = row.get("Output Folder", "")
                if not str(output_folder_raw).strip():
                    print(
                        f"Warning: missing Output Folder for "
                        f"{row.get('Job Title', '')!r}; skipping."
                    )
                    continue

                out_path = Path(output_folder_raw)
                tailored_path = out_path / "cv_tailored.json"
                if not tailored_path.is_file():
                    print(
                        f"Warning: no cv_tailored.json at {tailored_path}; skipping."
                    )
                    continue

                with open(tailored_path, "r", encoding="utf-8") as f:
                    tailored = json.load(f)

                html_str = fill_template(tailored)
                render_pdf(html_str, out_path)

                job_url = row.get("Job URL", "")
                row_num, status_col = _find_row_and_status_col(sheet, job_url)
                if row_num is None:
                    print(
                        f"Warning: could not find sheet row for Job URL {job_url!r}; "
                        "Status not updated."
                    )
                else:
                    sheet.update_cell(row_num, status_col, "PDF Ready")

                print(
                    f"Done: {row.get('Job Title', '')} at {row.get('Employer', '')}"
                )
            except Exception as exc:
                print(
                    f"Error processing approved row "
                    f"'{row.get('Job Title', 'unknown')}' "
                    f"at '{row.get('Employer', '')}': {exc}"
                )

        print("All approved CVs rendered.")
    except Exception as exc:
        print(f"render_approved failed: {exc}")


if __name__ == "__main__":
    render_approved()
