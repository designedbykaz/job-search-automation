"""Render the tailored CV HTML used by the Jobs detail-pane live preview.

The live preview is browser-rendered HTML, not a PDF, so what this module
produces will differ slightly from WeasyPrint's PDF output (font rendering,
@page rules). That gap is expected and tolerated; the overflow badge flags the
only constraint that matters at the editing stage.

Why not import ``fill_template`` from ``render_approved``? That module pulls
in ``gspread`` and ``weasyprint`` at import time. Keeping the preview path
independent means the UI can boot without those dependencies installed.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from ui.services import cv_template_choice, tailored_cv

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "templates"


def _template_path(choice: str) -> Path:
    normalised = choice.lower() if choice else "a"
    if normalised not in cv_template_choice.VALID:
        normalised = cv_template_choice.DEFAULT
    return TEMPLATES_DIR / f"cv_template_{normalised}.html"


def _fill(template_html: str, data: dict) -> str:
    html = template_html
    for key, value in data.items():
        placeholder = "{{" + str(key) + "}}"
        if isinstance(value, list):
            rendered = ", ".join(str(item) for item in value)
        else:
            rendered = "" if value is None else str(value)
        html = html.replace(placeholder, rendered)
    html = re.sub(r"{{[^}]+}}", "", html)
    return html


_OVERFLOW_SCRIPT = """
<script>
(function () {
  var THRESHOLD = 1063;
  var JOB_ID = __JOB_ID__;
  function report() {
    try {
      var overflow = document.body.scrollHeight > THRESHOLD;
      window.parent.postMessage(
        { type: "cv-preview-overflow", jobId: JOB_ID, overflow: overflow },
        "*"
      );
    } catch (e) { /* ignore */ }
  }
  if (document.readyState === "complete") {
    report();
  } else {
    window.addEventListener("load", report);
  }
  window.addEventListener("resize", report);
})();
</script>
"""


def _inject_overflow_script(html: str, job_id: Optional[int]) -> str:
    if job_id is None:
        return html
    script = _OVERFLOW_SCRIPT.replace("__JOB_ID__", str(int(job_id)))
    if "</body>" in html:
        return html.replace("</body>", script + "</body>", 1)
    return html + script


def render_preview_html(
    output_folder: str | Path,
    data: Optional[dict] = None,
    job_id: Optional[int] = None,
    template_choice: Optional[str] = None,
) -> str:
    """Fill the chosen template and return a complete HTML document.

    If ``data`` is None, the preferred tailored CV on disk is used (edited
    overrides original). If ``template_choice`` is None, the choice file in
    the output folder is consulted, defaulting to "a".
    """
    if data is None:
        data, _ = tailored_cv.read_preferred(output_folder)
    if template_choice is None:
        template_choice = cv_template_choice.get_choice(output_folder)

    path = _template_path(template_choice)
    template_html = path.read_text(encoding="utf-8")
    filled = _fill(template_html, data or {})
    return _inject_overflow_script(filled, job_id)
