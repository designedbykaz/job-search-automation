# Job Application Pipeline

A Python-based pipeline that scrapes UK job boards, filters results against a curated keyword list organised by career cluster, logs each job to a Google Sheet, and uses the Anthropic Claude API to produce a tailored CV and cover letter for every match. After a human approves a row in the Sheet, a separate renderer turns the tailored JSON into a print-ready PDF.

It was built to solve a very annoying problem: scanning UK job boards every day and hand-tailoring applications is slow, repetitive, and easy to do badly when tired. This project collapses that work into one command and a short review pass in a spreadsheet. It is at a stable v1, and actively being used.

---

## Running the v2 UI

A separate Flask front-end lives under `ui/` and runs from its own virtual environment at `ui/.venv/`, isolated from the pipeline's dependencies. On Windows (PowerShell), activate it with `ui\.venv\Scripts\Activate.ps1`; on macOS or Linux, use `source ui/.venv/bin/activate`. On a fresh clone, run `pip install -r ui/requirements.txt` inside the activated venv. Start the app with `python -m ui.run` and open `http://127.0.0.1:5000`.

---

## Table of contents

1. [Project overview and purpose](#1-project-overview-and-purpose)
2. [Architecture overview](#2-architecture-overview)
3. [Setup and configuration](#3-setup-and-configuration)
4. [How to run the pipeline](#4-how-to-run-the-pipeline)
5. [Component deep-dives](#5-component-deep-dives)
6. [Content model](#6-content-model)
7. [The Google Sheets tracker](#7-the-google-sheets-tracker)
8. [Current limitations and known issues](#8-current-limitations-and-known-issues)
9. [Roadmap](#9-roadmap)

---

## 1. Project overview and purpose

### 1.1 The problem

UK entry-level jobs for graduates are more competitive than ever thanks to advancements in AI and changing workplace dynamics. Finding a job has become incredibly tedious as most companies also use AI systems to filter through swathes of applications and cv's, so the need to custom-tailor cv's and cover letters is crucial. Additionally, these jobs are fragmented across a long tail of job boards and each listing has a short shelf life. Tailoring a CV and cover letter well for each one takes 20-40 minutes; doing that for 10 jobs a day is unsustainable, trying to do upwards of 30 is soul-crushing. Skipping the tailoring step is worse: generic applications get filtered out before a human ever reads them.

The pipeline attacks the two parts that machines are good at: finding and drafting. The rest is left to a human reviewer, who can decide for themselves **which jobs to apply to.** 

### 1.2 Who this is for

This is not a SaaS product. It is built for a single operator with:

- One CV source of truth (`content/base_cv_content.json`).
- A richer "reservoir" of extra material (`content/master_profile.json`) the model can draw from.
- A Google Sheet that acts as the approval surface.
- A set of Python scripts run from the terminal.

A second person could run it with their own content files; it is not designed for multi-user concurrency.

### 1.3 Current state

Working today:

- `findajob.dwp.gov.uk` scraper (`scrapers/govuk.py`).
- Dedup + keyword filtering + per-job output folder creation.
- Claude-based CV tailoring and cover letter generation.
- Google Sheets logging with URL-based cross-run dedup.
- Manual approval flow and PDF rendering of approved rows.

Stubbed / not yet wired:

- `--mode tailor` is a placeholder (see `[main.py](main.py)` lines 39-43).
- `scrapers/nhs.py` and `scrapers/totaljobs.py` Apify-based scrapers — imports are commented out in `main.py` and the dependency is commented in `requirements.txt`.

---

## 2. Architecture overview

### 2.1 Data flow

```
+------------------+
|  Job boards      |   findajob.dwp.gov.uk today; NHS / Totaljobs planned
+--------+---------+
         |
         v
+------------------+     scrapers/govuk.py
|  Raw job dicts   |     title, employer, location, date, url, description
+--------+---------+
         |
         v
+------------------+     pipeline/dedup.py
|  Dedup + filter  |     (title, employer) key, then keyword substring match
|  + cluster tag   |     tags each job with its cluster (nhs_healthcare, ux_design, ...)
+--------+---------+
         |
         v
+-------------------------------+
|  outputs/YYYY-MM-DD/{slug}/   |   one folder per job
|    job.json                   |
+--------+----------------------+
         |
         v
+------------------+     pipeline/tailor.py   (Anthropic Claude API)
|  Tailored CV     |     cv_tailored.json
|  Tailored CL     |     cover_letter_tailored.json
+--------+---------+
         |
         v
+------------------+     pipeline/logger.py   (gspread)
|  Google Sheet    |     14-column tracker, Status = "To Review"
+--------+---------+
         |
         v
+------------------+
|  Human review    |     set Status = "Approved" in the Sheet
+--------+---------+
         |
         v
+------------------+     render_approved.py   (WeasyPrint)
|  cv_output.pdf   |     written into the same per-job folder
|  Status =        |     flipped to "PDF Ready" in the Sheet
|  "PDF Ready"     |
+------------------+
```

### 2.2 Repo layout

```
job-pipeline/
  main.py                          # orchestrator (scrape + tailor + log)
  render_approved.py               # PDF render for Sheet rows marked Approved
  dev_scripts/                     # manual iteration helpers (see dev_scripts/README.md)
    test_tailor.py
    test_cover_letter.py
    render_test.py
    render_cover_letter_test.py
    render_cv.py
  requirements.txt
  .env.example
  .gitignore

  scrapers/
    govuk.py                       # findajob.dwp.gov.uk scraper (active)
    nhs.py                         # planned (Apify, NHS Jobs)
    totaljobs.py                   # planned (Apify, Totaljobs)

  pipeline/
    dedup.py                       # dedup, keyword filter, per-job folders
    tailor.py                      # Claude API calls for CV + cover letter
    logger.py                      # Google Sheets append + header management

  config/
    keywords.py                    # cluster toggles + keyword lists

  content/
    base_cv_content.example.json   # commit-safe template
    master_profile.example.json    # commit-safe template
    base_cv_content.json           # gitignored; real values
    master_profile.json            # gitignored; real values

  prompts/
    cv_prompt.example.txt          # commit-safe template
    cover_letter_prompt.example.txt
    cv_prompt.txt                  # gitignored; operator's live prompt
    cover_letter_prompt.txt        # gitignored

  templates/
    cv_template.html               # WeasyPrint CV template (A4, DM Sans)
    cover_letter_template.html     # WeasyPrint cover letter template

  outputs/                         # gitignored; one folder per day, per job
    YYYY-MM-DD/
      govuk_title_employer/
        job.json
        cv_tailored.json
        cover_letter_tailored.json
        cv_rendered.html
        cv_output.pdf
```

### 2.3 The four pipeline stages

`run_pipeline()` in `[main.py](main.py)` makes the stage boundaries explicit:

1. **Scrape** — `scrape_govuk_jobs()` returns a flat list of job dicts.
2. **Dedup and filter** — `deduplicate()` → `filter_by_keywords()` → `create_output_folders()`. This last step also writes `job.json` into each folder so downstream tools have a canonical source.
3. **Tailor** — for each surviving job, call `tailor_cv()` then `tailor_cover_letter()`. Skipped in `--mode scrape`.
4. **Log** — append each job as a row in the Google Sheet with Status `To Review`. Skipped in `--mode tailor`.

Each stage only reads from the previous one through plain Python data (lists of dicts) or files on disk (`job.json`). That keeps the stages replaceable: swapping in a new scraper, or replacing the Sheet with a database, does not require changes to the other three.

### 2.4 Why this shape

Two design choices are worth calling out, because they are the ones that define the project.

**Google Sheets instead of a database.** The operator's bottleneck is not storage, it is judgement — deciding which of 30 matches are actually worth applying to. A spreadsheet is the best "approval UI" a one-person project could ask for: mobile-friendly, offline-capable, shareable, and free. It also means the Sheet doubles as the application tracker, with columns for Priority, Applied, and Notes that the human fills in manually.

**Manual approval before PDF render.** Tailored JSON is cheap and reversible; a generated PDF in a per-job folder is not. Gating the render behind an explicit human "Approved" flip keeps the disk clean and forces a review of the tailored text before it is ever sent anywhere.

---

## 3. Setup and configuration

### 3.1 Prerequisites

- Python 3.10+.
- WeasyPrint system dependencies (on Windows, the GTK runtime; on macOS, `brew install pango gdk-pixbuf libffi`; on Linux, the `libpango` / `libcairo` family). WeasyPrint is the reason the install is heavier than it looks.
- A Google Cloud service account with access to the Google Sheets API, and the target Sheet shared with the service account's email.
- An Anthropic API key.

### 3.2 Install dependencies

```bash
pip install -r requirements.txt
```

The runtime dependencies are listed in `[requirements.txt](requirements.txt)`:

- `anthropic` — Claude API client used by `pipeline/tailor.py`.
- `weasyprint` — HTML-to-PDF renderer used by `render_approved.py` and the two `render_*_test.py` helpers.
- `gspread`, `google-auth`, `google-auth-oauthlib` — Google Sheets client and service-account credentials.
- `python-dotenv` — loads `.env` at startup.
- `requests`, `beautifulsoup4` — used by `scrapers/govuk.py`.

`apify-client` is commented out; uncomment it when the NHS / Totaljobs scrapers are wired in.

### 3.3 Environment variables

Copy `[.env.example](.env.example)` to `.env` and fill in real values:

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
APIFY_API_TOKEN=your_apify_token_here
GOOGLE_SHEETS_ID=your_google_sheet_id_here
GOOGLE_CREDENTIALS_PATH=google_credentials.json
```

`.env` and `google_credentials.json` are both gitignored. The Sheets ID is the long string in the middle of a `docs.google.com/spreadsheets/d/<ID>/edit` URL.

### 3.4 Content files

The pipeline reads four operator-owned files at runtime, all gitignored. For each one there is a committed `.example` version showing the expected shape:


| Runtime file                      | Committed template                        | Purpose                                                |
| --------------------------------- | ----------------------------------------- | ------------------------------------------------------ |
| `content/base_cv_content.json`    | `content/base_cv_content.example.json`    | Flat key/value dict, one slot per template placeholder |
| `content/master_profile.json`     | `content/master_profile.example.json`     | Nested "reservoir" Claude draws from                   |
| `prompts/cv_prompt.txt`           | `prompts/cv_prompt.example.txt`           | Prompt template for CV tailoring                       |
| `prompts/cover_letter_prompt.txt` | `prompts/cover_letter_prompt.example.txt` | Prompt template for cover letter drafting              |


The gitignored versions live alongside the examples. First-time setup is essentially: copy each `.example` to the real filename, fill it in, leave the `.example` alone.

### 3.5 Google Sheets setup

1. In Google Cloud, create a service account and enable the Google Sheets API.
2. Download its JSON key and save it next to the project as `google_credentials.json` (or whatever path you point `GOOGLE_CREDENTIALS_PATH` at).
3. Create a Sheet. Copy its ID into `GOOGLE_SHEETS_ID` in `.env`.
4. Share the Sheet with the service account's email (the `client_email` field from the JSON key), giving it Editor access.

The first run of `main.py --mode full` (or `--mode scrape`) calls `ensure_headers()` in `[pipeline/logger.py](pipeline/logger.py)`, which writes the 14-column header row if it is missing. After that you can add formatting, dropdowns, and filters on top without the pipeline disturbing them.

---

## 4. How to run the pipeline

All commands are run from the project root with the virtual environment active.

### 4.1 Full run

```bash
python main.py --mode full
```

Scrapes, dedups, filters, creates per-job folders, calls Claude to tailor CV and cover letter for each match, and logs everything to the Sheet with Status `To Review`. This is the default mode.

### 4.2 Scrape-only

```bash
python main.py --mode scrape
```

Same pipeline minus the Claude calls. Fast and free — use it for reconnaissance, to see what the filter catches before spending API budget.

### 4.3 Tailor-only (stubbed)

```bash
python main.py --mode tailor
```

Intended to load already-approved jobs from the Sheet and only run the tailoring stage against them. **Currently stubbed** — see `[main.py](main.py)` lines 39-43. It prints a TODO and exits.

### 4.4 Render approved CVs

```bash
python render_approved.py
```

Reads every row where `Status == "Approved"`, finds the corresponding `cv_tailored.json` under the stored Output Folder path, fills the HTML template, writes both `cv_rendered.html` and `cv_output.pdf` into that folder, then flips the Sheet's Status cell to `PDF Ready`. Rows with no Output Folder, or a missing `cv_tailored.json`, are skipped with a warning.

### 4.5 Standalone dev scripts

Two scripts exist for iterating on the template or the prompt in isolation:

- `[dev_scripts/render_test.py](dev_scripts/render_test.py)` — renders `outputs/test_single_job/cv_tailored.json` to PDF. Useful when working on `templates/cv_template.html` without running the full pipeline.
- `[dev_scripts/render_cover_letter_test.py](dev_scripts/render_cover_letter_test.py)` — the cover letter equivalent; hard-codes placeholder values for `NAME`, `EMPLOYER`, and `JOB_TITLE` so the template can be reviewed without a real job.

Neither is called by `main.py`. They exist purely as developer ergonomics.

---

## 5. Component deep-dives

### 5.1 Orchestrator — `[main.py](main.py)`

Small on purpose. Its whole job is to call each stage in order and handle the argparse switch.

```python
parser.add_argument(
    "--mode",
    choices=["full", "scrape", "tailor"],
    default="full",
    ...
)
```

The `full` and `scrape` modes share stages 1 and 2; they only diverge on whether stage 3 (tailor) runs. Stage 4 (log) runs for both. The `tailor` mode short-circuits before stage 1.

A handful of design notes worth knowing:

- `scrape_govuk_jobs()` is the only scraper currently wired in. `scrapers.nhs` and `scrapers.totaljobs` imports are commented out, as are the `nhs_jobs = ...` and `totaljobs_jobs = ...` calls inside `run_pipeline()`. When a new scraper is ready, you uncomment three lines and extend `all_jobs`.
- Errors during tailoring for a single job are caught and logged, so one flaky API call cannot kill the run. The `log_jobs()` call at the end still happens.
- The print at the bottom is deliberate: it tells the operator to go review the Sheet, and that `render_approved.py` is a separate step. That message is part of the contract between the pipeline and the human.

### 5.2 Scraper — `[scrapers/govuk.py](scrapers/govuk.py)`

Despite being named `govuk.py`, the scraper actually targets `findajob.dwp.gov.uk` — that's the live job board. The filename is a holdover from when GOV.UK Jobs and the DWP service were (briefly) easier to conflate.

Key constants at the top of the file:

```python
BASE_URL = "https://findajob.dwp.gov.uk"
SEARCH_URL = "https://findajob.dwp.gov.uk/search"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ..."
REQUEST_DELAY = 1.5
```

`REQUEST_DELAY` is enforced with a `time.sleep()` before every job-detail request; the keyword loop also sleeps between search pages. This keeps the scraper polite without needing an async client.

`can_fetch()` reads `/robots.txt` via Python's `urllib.robotparser`. Today it is informational only — it prints a warning if a URL is disallowed but proceeds anyway, on the basis that the scraper runs once or twice a day at low volume. Tightening this to a hard stop is a one-line change.

The flow for each keyword is:

1. `GET /search?q=<keyword>` with the shared `requests.Session`.
2. Parse the HTML and grab every `div.search-result` card.
3. For each card, extract title, employer, location, posted date, URL from the listing DOM.
4. Follow the URL and call `get_job_description()` to fetch the full job body plus a best-effort closing date and contact info (email via regex, phone number as fallback).

Two oddities worth knowing:

- There is a `_extract_listing_fields()` helper near the top with `TODO: Confirm markup` comments. It is **not called** by the active `scrape_govuk_jobs()` path, which parses cards inline. `_extract_listing_fields` is a legacy placeholder from an earlier experiment and can be deleted.
- `get_job_description()` tries `div#job-description` first and falls back to `main`. Robustness comes from the fallback, not from asserting the primary selector exists.

Every returned dict has the same shape: `title`, `employer`, `location`, `date`, `url`, `description`, `closing_date`, `contact_info`, `source`. Downstream stages only rely on these keys.

### 5.3 Deduplication and filtering — `[pipeline/dedup.py](pipeline/dedup.py)`

Three functions, each small enough to hold in your head at once.

`deduplicate(all_jobs)` — within a single run, collapse duplicates where `(title, employer)` match case-insensitively. The first occurrence wins:

```python
key = (job.get("title", "").lower(), job.get("employer", "").lower())
if key not in seen:
    seen.add(key)
    unique.append(job)
```

This is narrower than URL-based dedup on purpose: the same job sometimes gets posted across multiple search results with slightly different URLs, and they still only deserve one row.

`filter_by_keywords(jobs)` — retain only jobs whose title contains at least one entry from the flat `JOB_KEYWORDS` list. It also tags each matched job with its cluster, using a flattened lookup built from `KEYWORDS_BY_CLUSTER`:

```python
keyword_to_cluster = {
    kw.lower(): cluster
    for cluster, keywords in KEYWORDS_BY_CLUSTER.items()
    for kw in keywords
}
```

The cluster tag then flows all the way through to the Sheet's Cluster column, which is what makes filtering by cluster in the UI trivial.

`make_folder_name(job)` — build a safe slug: lowercase, spaces to underscores, only `[a-z0-9_]`, collapse repeated underscores, max 80 characters. Pattern is `{source}_{title}_{employer}`.

`create_output_folders(jobs)` — for each job, create `outputs/YYYY-MM-DD/{slug}/`, set `job["output_folder"]` to the normalised path, and write `job.json` into it. This is the handoff file that `tailor_cv()` and `tailor_cover_letter()` implicitly rely on having around (they actually re-read the job dict from memory, but the file exists for humans and future tools).

### 5.4 Keyword clusters — `[config/keywords.py](config/keywords.py)`

The seven clusters shown below are an **example configuration** shipped in `config/keywords.py`. They reflect one particular job search and are meant as a starting point, not a fixed part of the tool. If you are adopting this pipeline for yourself, expect to replace the cluster names and their contents entirely with groups that match your own target roles and sectors. The toggle mechanism works regardless of which clusters you define or how many.

The keyword list is where most of the project's domain knowledge lives. Rather than one flat list, the shipped configuration splits keywords into seven thematic clusters, each of which can be toggled on or off via a dict at the top of the file:

```python
ACTIVE_CLUSTERS = {
    "nhs_healthcare":        True,
    "ux_design":             True,
    "data_analytics":        True,
    "technical_engineering": True,
    "digital_marketing":     True,
    "project_ops":           True,
    "edtech":                True,
}
```

The clusters and roughly how many keywords each one contains:


| Cluster                 | Approximate count | What it catches (example)                                      |
| ----------------------- | ----------------- | -------------------------------------------------------------- |
| `nhs_healthcare`        | ~80               | Example: UK public healthcare and clinical support roles       |
| `ux_design`             | ~25               | Example: junior / graduate / apprentice product and UX roles   |
| `data_analytics`        | ~30               | Example: entry-level analyst, BI, and reporting roles          |
| `technical_engineering` | ~30               | Example: CAD, manufacturing, R&D, and quality technician roles |
| `digital_marketing`     | ~30               | Example: assistant, executive, and apprentice marketing roles  |
| `project_ops`           | ~30               | Example: project coordinator, PMO, and delivery-support roles  |
| `edtech`                | ~25               | Example: learning design and educational technology roles      |


At import time, `JOB_KEYWORDS` is built as a flat list comprehension over only the active clusters:

```python
JOB_KEYWORDS = [
    keyword
    for cluster_name, keywords in KEYWORDS_BY_CLUSTER.items()
    if ACTIVE_CLUSTERS.get(cluster_name, False)
    for keyword in keywords
]
```

That flat list is what the scraper iterates over. The mapping is what `filter_by_keywords()` uses to tag the cluster. Turning off a cluster therefore both stops it being searched **and** stops any of its keywords being matched on accident.

This toggle is one of the pieces that will transplant cleanly into the planned Flask UI: checkboxes for clusters.

### 5.5 Tailoring — `[pipeline/tailor.py](pipeline/tailor.py)`

Two functions, `tailor_cv()` and `tailor_cover_letter()`, both the same shape:

1. Load `content/base_cv_content.json`, `content/master_profile.json`, and the relevant prompt file.
2. Substitute the placeholders (`{{BASE_CV}}`, `{{MASTER_PROFILE}}`, `{{JOB_TITLE}}`, `{{EMPLOYER}}`, `{{JOB_DESCRIPTION}}`) with JSON-stringified or raw values.
3. Call the Anthropic API:
  ```python
   client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
   message = client.messages.create(
       model="claude-opus-4-6",
       max_tokens=4096,
       messages=[{"role": "user", "content": filled_prompt}],
   )
  ```
4. Strip any stray Markdown code fences with `re.sub(r"` `(?:json)?|` `", "", text)`.
5. `json.loads()` the result.
6. On success, save to `cv_tailored.json` / `cover_letter_tailored.json` inside the job folder. On JSON decode failure, write the raw text to `cv_tailored_raw.txt` (or the cover letter equivalent) and raise — so the operator can always see what the model actually produced.

`tailor_cv()` passes the entire `master_profile["cv"]` subtree into `{{MASTER_PROFILE}}`; `tailor_cover_letter()` passes `master_profile["cover_letter"]`. That is what the split in the master profile JSON exists for — neither prompt ever sees material intended for the other.

One thing to verify before running: the model string `"claude-opus-4-6"` is hard-coded in both functions. If you are running this against a different Claude model, change both constants.

### 5.6 Prompt contracts — `[prompts/cv_prompt.example.txt](prompts/cv_prompt.example.txt)` and `[prompts/cover_letter_prompt.example.txt](prompts/cover_letter_prompt.example.txt)`

The prompt files are the most deliberately designed part of the project. They are not "write a good CV" — they are strict contracts that tell the model what to return, in what shape, under what constraints. If the document is ever short on budget for anything else, it should still read these.

**The CV prompt** contains four named rules worth calling out:

- **PUNCTUATION RULE** — no em dashes or en dashes, ever. The model is explicitly told to use commas, semicolons, colons, parentheses, or periods instead. This is cosmetic consistency across every CV the pipeline produces.
- **DEDUPLICATION RULE** — the Education section and `EXP_3` cover the same university period. `EXP_3_BODY` must not repeat modules or the signature final project. The rule exists because without it the model cheerfully says the same thing twice.
- **APPRENTICESHIP RULE** — if the job title contains `Apprentice`, `Trainee`, or `Pre-Registration`, the OBJECTIVE must explicitly acknowledge that the candidate is seeking a structured learning pathway, not just employment. This materially changes recruiter response rates for training-scheme roles.
- **CRITICAL LENGTH RULE** — total output length must not exceed input length. The model is told, if forced to choose, to stay within length at the cost of tailoring. This is what keeps the CV fitting on one A4 page without post-processing.

**The cover letter prompt** is structurally similar but enforces a four-paragraph JSON contract:

```
NAME, JOB_TITLE, EMPLOYER,
COVER_LETTER_OPENING,
COVER_LETTER_EXPERIENCE,
COVER_LETTER_MOTIVATION,
COVER_LETTER_CLOSING
```

Each of those four paragraph keys has its own rules — the opener is forbidden from starting with "I would like to apply" / "I am writing" and must lead with what the candidate brings; the closing is forbidden from generic boilerplate like "I look forward to hearing from you." The word count is locked to 250-300 across all four paragraphs. The tone is specified as "warm, professional, human. Not stiff. Not sycophantic."

Both prompts end with the same output contract: return only the JSON, no preamble, no explanation, no Markdown code fences. That is what lets `json.loads()` succeed in `tailor.py` nine times out of ten.

### 5.7 Sheets logger — `[pipeline/logger.py](pipeline/logger.py)`

The logger's only job is to append a row per job to the Sheet without creating duplicates across runs.

The schema is a 14-column header written by `ensure_headers()`:

```python
HEADERS = [
    "Date Found", "Job Title", "Employer", "Location", "Cluster", "Source",
    "Closing Date", "Priority", "Contact Info", "Job URL", "Output Folder",
    "Status", "Applied", "Notes",
]
```

`ensure_headers()` only writes row 1 if it is missing or doesn't match; manual formatting on the rest of the sheet is never touched.

Dedup across runs is URL-based:

```python
existing_urls = set(sheet.col_values(10))  # Column J = Job URL
```

Column J is the Job URL column. Reading it once at the start of the run is a single API call; each new job is then a constant-time set check. New URLs are appended and added to the in-memory set so that duplicates within the same batch are also caught.

Every append is followed by `time.sleep(0.5)` to stay inside Google Sheets' per-minute quota on a service account. For runs of ~30 jobs this is fine; at 200+ jobs it becomes the main cost and should be replaced with `sheet.append_rows()` in a single batched call.

Row content maps directly from the job dict, with `Priority`, `Applied`, and `Notes` left as empty strings because they are the operator's columns.

### 5.8 Approved-row renderer — `[render_approved.py](render_approved.py)`

The second half of the pipeline. Running it opens the same Sheet, pulls every row with `Status == "Approved"`, and for each one:

1. Read `Output Folder` from the row — if missing, warn and skip.
2. Open `{output_folder}/cv_tailored.json` — if missing, warn and skip.
3. Run `fill_template(tailored_cv_dict)`, which opens `templates/cv_template.html` and does `html.replace("{{KEY}}", value)` for every key/value in the JSON. Lists are joined with `", "`. Any `{{...}}` placeholder left over after the pass is printed as a warning — so you notice immediately if the tailored JSON is missing a key.
4. Write `cv_rendered.html` and `cv_output.pdf` into the same folder.
5. Find the matching Sheet row by Job URL (using `_find_row_and_status_col`) and flip its Status cell to `PDF Ready`.

That final status flip is the pipeline's only write to an already-logged row. It's enough to close the loop — the operator can filter the Sheet on `Status = PDF Ready` to find everything ready to send.

The cover letter is **not** rendered by this script. Today the cover letter JSON lives next to the CV JSON as data only; the `dev_scripts/render_cover_letter_test.py` script exists to render it manually while iterating on the template. Wiring cover letter rendering into `render_approved.py` is a small, obvious next step.

### 5.9 Templates — `[templates/cv_template.html](templates/cv_template.html)` and `[templates/cover_letter_template.html](templates/cover_letter_template.html)`

Two WeasyPrint-targeted HTML files. Both use DM Sans, A4 page size, 8mm margins, and neutral black / grey typography with hairline dividers. Everything is inline `<style>` because WeasyPrint does not need a build step.

The placeholder contract is intentionally simple: every `{{KEY}}` in the HTML is replaced with the matching value from the tailored JSON. That keeps the renderer code boring (one `str.replace` per key) and the template readable as a designer's document, not a programmer's one.

The CV template expects the same keys as `base_cv_content.json`: `NAME`, `CURRENT_POSITION`, `OBJECTIVE`, `EDU_`*, `CERTIFICATIONS`, `EXP_1_`* through `EXP_7_*`, `SKILL_*`, `SOFT_SKILL_1..3`, `LANG_1..3`, `EMAIL`, `PHONE`, `LINKEDIN`. Missing keys show as a literal `{{KEY}}` in the PDF — which is why the warning in `render_approved.py` matters.

The cover letter template expects `NAME`, `JOB_TITLE`, `EMPLOYER`, and the four paragraph keys produced by the cover letter prompt.

---

## 6. Content model

### 6.1 `base_cv_content.json` — the flat source of truth

Flat key/value. One entry per template placeholder. It is the "what the CV says by default" file.

Why flat? Because the CV template is flat: each field on the page corresponds to exactly one key. Nesting would mean writing a path-walker in the renderer, for zero gain. A few representative keys:

```
NAME, CURRENT_POSITION, OBJECTIVE,
EDU_INSTITUTION, EDU_DATES, EDU_DEGREE, EDU_MODULES, EDU_PROJECT, EDU_EXTRA,
EXP_1_ROLE, EXP_1_COMPANY, EXP_1_DATE, EXP_1_BODY,
...
SKILL_SOFTWARE, SKILL_TECHNICAL, SKILL_DETAIL, SKILL_AI,
SOFT_SKILL_1, SOFT_SKILL_2, SOFT_SKILL_3,
LANG_1, LANG_2, LANG_3,
EMAIL, PHONE, LINKEDIN
```

The committed template is `content/base_cv_content.example.json`. Copy it to `content/base_cv_content.json` and fill in. The tailoring step reads both files and returns a JSON object with the **same keys** — the CV prompt enforces that explicitly.

### 6.2 `master_profile.json` — the reservoir

Nested on purpose. It is the **extra** material Claude is allowed to draw from when something in the base CV can be strengthened for a particular role.

The keys shown below are **illustrative** — they reflect the convention used in the committed `[content/master_profile.example.json](content/master_profile.example.json)`. Every key in the reservoir is fully customisable; add, remove, or rename buckets to fit your own background. The pipeline never looks at the inner key names, only at the two top-level buckets `cv` and `cover_letter`.

It is split at the top level into those two buckets:

```
cv:
  personal_profile, personal_motivations, education, certifications,
  technical_skills, soft_skills, languages, projects, experience,
  character_and_values, sector_relevance, additional_context
cover_letter:
  personal_story, motivations_and_values, personal_context,
  professional_philosophy, transferable_angles, company_specific_angles,
  additional_reservoir
```

`personal_context` is an optional bucket for background material that is relevant to particular applications; leave it empty or delete it if it doesn't apply to you.

`tailor_cv()` only ever sees `master_profile["cv"]`; `tailor_cover_letter()` only ever sees `master_profile["cover_letter"]`. This matters because material from the cover letter reservoir — personal stories, motivations — shouldn't leak into a CV, and vice versa. The split is enforced at the call site in `[pipeline/tailor.py](pipeline/tailor.py)`, not by trusting the model to do the right thing.

### 6.3 Prompt files — how composition works

Both prompt files contain five placeholder markers that `tailor.py` fills in at runtime:


| Placeholder           | Filled with                                                   |
| --------------------- | ------------------------------------------------------------- |
| `{{BASE_CV}}`         | `json.dumps(base_cv, indent=2)` — the whole flat CV dict      |
| `{{MASTER_PROFILE}}`  | `json.dumps(master_profile["cv"])` or `[...]["cover_letter"]` |
| `{{JOB_TITLE}}`       | `job["title"]`                                                |
| `{{EMPLOYER}}`        | `job.get("employer", "")`                                     |
| `{{JOB_DESCRIPTION}}` | `job.get("description", "")`                                  |


Because the substitution is dumb `str.replace`, the placeholders must appear exactly once and must not collide with any other `{{...}}` text in the prompt.

---

## 7. The Google Sheets tracker

### 7.1 Column reference


| #   | Column        | Written by             | What it is                                                |
| --- | ------------- | ---------------------- | --------------------------------------------------------- |
| A   | Date Found    | Pipeline               | `date.today()` at logging time                            |
| B   | Job Title     | Pipeline               | Scraped title                                             |
| C   | Employer      | Pipeline               | Scraped employer                                          |
| D   | Location      | Pipeline               | Scraped location                                          |
| E   | Cluster       | Pipeline               | Cluster tag from `filter_by_keywords()`                   |
| F   | Source        | Pipeline               | Scraper name (`govuk`)                                    |
| G   | Closing Date  | Pipeline (best effort) | Regex-extracted from the job page                         |
| H   | Priority      | **Human**              | Free-form; typically `High` / `Med` / `Low`               |
| I   | Contact Info  | Pipeline (best effort) | Email via regex, phone as fallback                        |
| J   | Job URL       | Pipeline               | Canonical URL — used as the dedup key across runs         |
| K   | Output Folder | Pipeline               | Path to `outputs/YYYY-MM-DD/{slug}/`                      |
| L   | Status        | Mixed                  | `To Review` → `Approved` (human) → `PDF Ready` (pipeline) |
| M   | Applied       | **Human**              | Date the application was actually sent                    |
| N   | Notes         | **Human**              | Anything the operator wants to remember                   |


### 7.2 Status lifecycle

```
To Review    (written by logger on row creation)
    |
    v  (human reviews, decides to apply)
Approved
    |
    v  (render_approved.py)
PDF Ready
    |
    v  (human sends the application)
Applied column filled
```

Any other string in the Status column is ignored by both `log_jobs()` (which only ever writes `To Review`) and `render_approved.py` (which only reads `Approved`). That means you can use values like `Rejected`, `Interview`, `Offer`, `Ghosted` freely for your own tracking without confusing the pipeline.

### 7.3 Dedup across runs

Column J (Job URL) is the de-facto primary key. `log_jobs()` reads the full column at the start of a run, skips any job whose URL is already present, and adds new URLs to the in-memory set so within-batch duplicates also get caught.

This means: as long as the scraper produces a stable URL for a listing, running the pipeline twice a day is idempotent in the Sheet — you only ever see new rows.

---

## 8. Current limitations and known issues

- **Tailor-only mode is stubbed.** `[main.py](main.py)` exits with a TODO print when `--mode tailor` is passed. Loading approved rows from the Sheet is not yet wired.
- **Only one scraper is active.** The two Apify-based scrapers (`scrapers/nhs.py`, `scrapers/totaljobs.py`) are planned but not committed; the `apify-client` dependency is commented out in `[requirements.txt](requirements.txt)`.
- **Selector fragility on findajob.dwp.gov.uk.** The inline parser in `scrape_govuk_jobs()` relies on DOM classes (`div.search-result`, `h3.govuk-heading-s a.govuk-link`, `ul.govuk-list.search-result-details`) that the DWP can change without notice.
- **Model configurable via `CLAUDE_MODEL` environment variable.** Both Claude calls in `[pipeline/tailor.py](pipeline/tailor.py)` use `os.getenv("CLAUDE_MODEL", "claude-opus-4-6")`. Defaults to `claude-opus-4-6` if not set; set `CLAUDE_MODEL` in `.env` to use a different model identifier.
- **No retry or backoff.** Anthropic rate limits, Google Sheets quota errors, and flaky scraper requests all bubble up and are caught at the per-job level at best. Exponential backoff in `tailor.py` and `logger.py` would be a one-afternoon improvement.
- **Robots.txt enforcement.** `can_fetch()` returns `False` when `robots.txt` disallows a URL; `get_job_description()` skips the fetch and returns `None`, and `scrape_govuk_jobs()` skips that listing without appending it. If `robots.txt` cannot be read, the scraper defaults to allowed (same as before).
- **Single CV template.** Every cluster gets the same layout. A UX role might want a more visual CV than a Pharmacy Assistant role — see roadmap.
- **Cover letters are generated but not auto-rendered.** `render_approved.py` only writes CV PDFs today. Cover letter PDFs require running `dev_scripts/render_cover_letter_test.py` manually.
- **WeasyPrint install weight on Windows.** The PDF renderer needs a GTK runtime on Windows; this is the slowest part of first-time setup.

---

## 9. Roadmap

- **NHS Jobs + Totaljobs scrapers via Apify.** Stubs already exist as commented imports in `[main.py](main.py)`; the dep is already commented into `[requirements.txt](requirements.txt)`. Each one returns the same dict shape as `scrape_govuk_jobs()` and gets concatenated into `all_jobs`.
- **Cluster-specific CV templates.** `KEYWORDS_BY_CLUSTER` already tags every job with its cluster, and `job["cluster"]` is carried all the way to the renderer. The natural extension is a `templates/cv_template_{cluster}.html` lookup in `fill_template()` — e.g. a more visual layout for `ux_design` and a more clinical one for `nhs_healthcare`.
- **Flask UI as the approval surface.** The Google Sheet is the minimum viable review UI. A Flask app reading the same per-job folder as a source of truth, with Approve / Render buttons that call the existing Python functions directly, would let the operator skip the Sheet round-trip entirely. The cluster toggles in `config/keywords.py` would become the configuration screen.
- **Location filtering.** The `location` field is already captured and logged; filtering jobs by it (e.g. "only within 30 miles of X") would live in `pipeline/dedup.py` as a third pass after `filter_by_keywords()`.
- **Tailor-only mode.** Load rows where `Status == "Approved"` but no `cv_tailored.json` exists yet, and run only stage 3 against them. Useful when the operator approved in bulk and wants to tailor in a batch.
- **Auto-render cover letter PDFs.** Extend `render_approved.py` to also call a `fill_template()` pass on `cover_letter_template.html` + `cover_letter_tailored.json`, writing `cover_letter_output.pdf` next to the CV.
- **Retry / backoff on API calls.** `anthropic` and `gspread` both raise on 429 today. Wrap the calls in a small retry helper with jitter.

