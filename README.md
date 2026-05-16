

---

# Job Search Automation Pipeline

A local web app for scraping UK job listings, reviewing them in a fast browser UI, and rendering tailored CVs for the ones worth applying to.

## What it does

Scrapes UK job boards (currently findajob.dwp.gov.uk), filters results by keyword or freeform search terms, and stores them on disk and in a Google Sheet. You review jobs in a local browser, approve the ones you want to apply to, and render tailored CV PDFs for each one using the Claude API.

The Sheet is the canonical approval log, mobile-friendly and editable from anywhere. The local disk is the source of truth for what jobs exist and their content. UI reads happen from disk (fast); writes go to both disk and Sheet.

## Architecture at a glance

- **Scrape**: pulls jobs via `scrapers/govuk.py`
- **Disk**: each job lives in `outputs/{YYYY-MM-DD}/{slug}/job.json`, indexed in `outputs/_index.json`
- **Sheet**: each job is also appended as a row for mobile access
- **UI**: Flask + Bootstrap 5 + HTMX, reads from the disk index on every page load (never the Sheet)
- **Activity log**: `outputs/_activity.json` tracks scrape and approval events for the dashboard feed
- **CV tailoring**: per-job Claude API calls produce JSON the user can edit, then render to PDF via WeasyPrint

When you approve a job in the UI, the disk index updates instantly and the Sheet is updated in the background. If the Sheet write fails, the UI stays approved and a warning is logged.

## Setup

Requires Python 3.12.

1. Clone the repo and create the virtual environment:

```
python -m venv ui/.venv
ui\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

```

1. Copy `.env.example` to `.env` and fill in your values:

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
APIFY_API_TOKEN=your_apify_token_here
GOOGLE_SHEETS_ID=your_google_sheet_id_here
GOOGLE_CREDENTIALS_PATH=google_credentials.json

```

1. Place your Google service account credentials JSON file at the path specified by `GOOGLE_CREDENTIALS_PATH`. The service account needs edit access to the target Sheet.
2. (Optional, for CV tailoring) Copy the `.example` files under `content/` and `prompts/` and fill in your details.

## Running the app

Start the web UI:

```
ui\.venv\Scripts\Activate.ps1
python -m ui.run

```

Open http://127.0.0.1:5000 in your browser.

### Terminal commands

Full pipeline (scrape, dedup, filter, tailor, log):

```
python main.py --mode full

```

Scrape only (no API spend):

```
python main.py --mode scrape

```

Render PDFs for approved jobs:

```
python render_approved.py

```

Rebuild the disk index from scratch (one-off utility):

```
python -m scripts.build_job_index

```

## Project structure

```
job-pipeline/
  main.py                  v1 orchestrator
  render_approved.py       Renders approved CVs to PDF
  scrapers/                Job board scrapers
  pipeline/                Dedup, keyword filter, tailoring, sheet logging
  config/                  Keyword clusters and scraper settings
  content/                 CV content (gitignored)
  prompts/                 Claude prompts (gitignored)
  templates/               CV HTML templates for WeasyPrint
  outputs/                 Scraped jobs and indexes (gitignored)
  ui/                      Flask web app
    routes/                Page routes
    services/              Disk index, activity log, sheets, preview
    templates/             Jinja2 templates
    static/                Bootstrap, HTMX, custom JS and CSS
  scripts/                 One-off utilities
  tests/                   Pytest suite

```

## What works today

- Open search scrape (freeform terms from the Run page)
- Fast browser UI for reviewing jobs
- Approve action with instant UI update and Sheet write-through
- Live activity feed on the Dashboard
- CV tailoring via `main.py`
- PDF rendering via `render_approved.py`

## Coming next

- Render PDF button wired in the UI
- Cluster search Run pipeline triggered from the UI
- Plain text CV template option
- Archive feature with a recycle bin

## Testing

```
python -m pytest tests/ -v

```

Tests cover the disk-based job index and the activity log services.

## License

Personal project, all rights reserved.

