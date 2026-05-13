from flask import Blueprint, render_template

from ui.services import sheets

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    status = {
        "state": "idle",
        "label": "Pipeline idle",
        "detail": "Last run completed 2 hours ago",
    }
    counters_data = sheets.get_counters()
    counters = [
        {"value": counters_data["to_review"], "label": "Awaiting review"},
        {"value": counters_data["approved"], "label": "Approved, unrendered"},
        {"value": counters_data["pdf_ready"], "label": "Rendered"},
    ]
    activity = [
        {"action": "Pipeline run completed", "detail": "18 jobs scraped, 12 matched", "time": "2 hours ago"},
        {"action": "CV rendered", "detail": "Senior Product Designer at NHS Digital", "time": "5 hours ago"},
        {"action": "CV rendered", "detail": "UX Researcher at Department for Education", "time": "5 hours ago"},
        {"action": "Prompt edited", "detail": "CV tailoring prompt updated", "time": "1 day ago"},
        {"action": "Pipeline run completed", "detail": "24 jobs scraped, 15 matched", "time": "1 day ago"},
        {"action": "Template uploaded", "detail": "Template B replaced", "time": "3 days ago"},
    ]
    return render_template(
        "dashboard.html",
        active_nav="dashboard",
        status=status,
        counters=counters,
        activity=activity,
    )
