from flask import Blueprint, render_template, request

from ui.services import open_search, scraper_config

bp = Blueprint("pipeline", __name__, url_prefix="/run")


SCRAPER_PANEL = {
    "id": "scraper-config-panel",
    "textarea_id": "scraper-config-textarea",
    "feedback_id": "scraper-config-feedback",
    "edited_badge_id": "scraper-config-edited-badge",
    "reset_wrapper_id": "scraper-config-reset-wrapper",
    "save_url_endpoint": "pipeline.save_scraper_config",
    "reset_url_endpoint": "pipeline.reset_scraper_config",
    "form_field": "scraper_json_text",
}


def _scraper_panel_context() -> dict:
    text, is_edited = scraper_config.get_text()
    return {"panel": SCRAPER_PANEL, "text": text, "is_edited": is_edited}


@bp.route("/")
def index():
    scrapers = [
        {"name": "GOV.UK Jobs (findajob.dwp.gov.uk)", "enabled": True, "status": "healthy"},
        {"name": "NHS Jobs", "enabled": False, "status": "untested"},
        {"name": "Totaljobs", "enabled": False, "status": "untested"},
    ]
    return render_template(
        "pipeline/index.html",
        active_nav="run",
        scrapers=scrapers,
        scraper_panel_ctx=_scraper_panel_context(),
    )


@bp.route("/config/scrapers", methods=["POST"])
def save_scraper_config():
    text = request.form.get(SCRAPER_PANEL["form_field"], "")
    ok, error = scraper_config.save(text)
    return render_template(
        "pipeline/_panel_save_feedback.html",
        panel=SCRAPER_PANEL,
        success=ok,
        error=error,
        warnings=[],
    )


@bp.route("/config/scrapers/reset", methods=["POST"])
def reset_scraper_config():
    scraper_config.reset()
    return render_template(
        "pipeline/_scraper_config_panel.html",
        **_scraper_panel_context(),
    )


@bp.route("/open-search", methods=["POST"])
def run_open_search():
    raw_terms = request.form.get("terms", "")
    location = request.form.get("location", "").strip()
    terms = [t.strip() for t in raw_terms.splitlines() if t.strip()]
    ok, error, summary = open_search.run_open_search(terms, location)
    return render_template(
        "pipeline/_open_search_result.html",
        success=ok,
        error=error,
        summary=summary,
    )
