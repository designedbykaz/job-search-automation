from flask import Blueprint, render_template

bp = Blueprint("pipeline", __name__, url_prefix="/run")


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
    )
