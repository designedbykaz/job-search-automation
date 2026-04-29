from flask import Blueprint, render_template, request

from ui.services import keyword_overrides, scraper_config

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

KEYWORD_PANEL = {
    "id": "keyword-cluster-panel",
    "textarea_id": "keyword-cluster-textarea",
    "feedback_id": "keyword-cluster-feedback",
    "edited_badge_id": "keyword-cluster-edited-badge",
    "reset_wrapper_id": "keyword-cluster-reset-wrapper",
    "save_url_endpoint": "pipeline.save_keyword_overrides",
    "reset_url_endpoint": "pipeline.reset_keyword_overrides",
    "form_field": "keyword_json_text",
}


def _scraper_panel_context() -> dict:
    text, is_edited = scraper_config.get_text()
    return {"panel": SCRAPER_PANEL, "text": text, "is_edited": is_edited}


def _keyword_panel_context() -> dict:
    text, is_edited = keyword_overrides.get_text()
    return {"panel": KEYWORD_PANEL, "text": text, "is_edited": is_edited}


@bp.route("/")
def index():
    scrapers = [
        {"id": 1, "name": "Indeed UK", "enabled": True, "status": "healthy"},
        {"id": 2, "name": "NHS Jobs", "enabled": True, "status": "healthy"},
        {"id": 3, "name": "Civil Service Jobs", "enabled": False, "status": "untested"},
    ]
    clusters = [
        {"id": 1, "name": "nhs_healthcare", "enabled": True, "keywords": 80},
        {"id": 2, "name": "ux_design", "enabled": True, "keywords": 25},
        {"id": 3, "name": "product_management", "enabled": True, "keywords": 42},
        {"id": 4, "name": "user_research", "enabled": True, "keywords": 31},
        {"id": 5, "name": "service_design", "enabled": False, "keywords": 18},
        {"id": 6, "name": "digital_delivery", "enabled": True, "keywords": 36},
        {"id": 7, "name": "design_systems", "enabled": False, "keywords": 22},
    ]
    date_ranges = ["Since last run", "Last 24 hours", "Last 7 days", "Last 30 days"]
    modes = ["Full run (scrape + tailor)", "Scrape only"]
    return render_template(
        "pipeline/index.html",
        active_nav="run",
        scrapers=scrapers,
        clusters=clusters,
        date_ranges=date_ranges,
        modes=modes,
        scraper_panel_ctx=_scraper_panel_context(),
        keyword_panel_ctx=_keyword_panel_context(),
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


@bp.route("/config/keywords", methods=["POST"])
def save_keyword_overrides():
    text = request.form.get(KEYWORD_PANEL["form_field"], "")
    ok, error, warnings = keyword_overrides.save(text)
    return render_template(
        "pipeline/_panel_save_feedback.html",
        panel=KEYWORD_PANEL,
        success=ok,
        error=error,
        warnings=warnings,
    )


@bp.route("/config/keywords/reset", methods=["POST"])
def reset_keyword_overrides():
    keyword_overrides.reset()
    return render_template(
        "pipeline/_keyword_cluster_panel.html",
        **_keyword_panel_context(),
    )
