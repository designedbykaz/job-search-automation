# dev_scripts

Manual iteration helpers used while working on prompts, CV/cover-letter
templates, or the tailoring code in isolation.

These scripts are **not** part of the production pipeline. None of them are
imported or invoked by `main.py`, `render_approved.py`, or the `ui/` Flask
app. They exist purely for one-off, by-hand iteration.

## Invocation

Always run from the repo root:

```bash
python dev_scripts/<script_name>.py
```

The two scripts that import from `pipeline/` (`test_tailor.py` and
`test_cover_letter.py`) include a small `sys.path` shim at the top so
this invocation works without setting `PYTHONPATH`.

## Scripts

- `test_tailor.py` — calls `pipeline.tailor.tailor_cv` against a single
  hardcoded test job. Writes `cv_tailored.json` to
  `outputs/test_single_job/`. Hits the Anthropic API.
- `test_cover_letter.py` — same shape as above for cover letters. Calls
  `pipeline.tailor.tailor_cover_letter`. Hits the Anthropic API.
- `render_test.py` — renders `outputs/test_single_job/cv_tailored.json`
  to PDF using a CV template. Run `test_tailor.py` first.
- `render_cover_letter_test.py` — renders
  `outputs/test_single_job/cover_letter_tailored.json` to PDF using
  `templates/cover_letter_template.html`. Run `test_cover_letter.py`
  first. Hard-codes placeholder values for `NAME`, `EMPLOYER`, and
  `JOB_TITLE` so the template can be reviewed without a real job.
- `render_cv.py` — fills `content/base_cv_content.json` into a CV
  template and writes the result to `outputs/cv_output.pdf`. Predates
  the tailoring pipeline; useful only when iterating on the base CV
  content or template.
