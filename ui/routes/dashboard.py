from flask import Blueprint, render_template

from ui.services import activity_log

bp = Blueprint("dashboard", __name__)

_STATUS_ACTION_LABELS = {
    "to_review": "Marked for review",
    "approved": "Approved",
    "pdf_ready": "PDF rendered",
}


def _status_change_action(to_status: str) -> str:
    if to_status in _STATUS_ACTION_LABELS:
        return _STATUS_ACTION_LABELS[to_status]
    if not to_status:
        return "Updated"
    return to_status.replace("_", " ").capitalize()


def _activity_items_from_log() -> list[dict]:
    items: list[dict] = []
    for event in activity_log.get_recent(10):
        if not isinstance(event, dict):
            continue
        event_type = event.get("type")
        details = event.get("details") or {}
        if not isinstance(details, dict):
            details = {}
        timestamp = event.get("timestamp", "")
        time_str = activity_log.format_relative_time(str(timestamp))

        if event_type == "scrape":
            jobs_added = details.get("jobs_added", 0)
            terms = details.get("terms") or []
            if not isinstance(terms, list):
                terms = []
            location = str(details.get("location", "") or "").strip()
            term_str = ", ".join(str(t) for t in terms)
            if location:
                detail = f"{term_str} ({location})" if term_str else f"({location})"
            else:
                detail = term_str
            items.append(
                {
                    "action": f"Open search: {jobs_added} jobs added",
                    "detail": detail,
                    "time": time_str,
                }
            )
        elif event_type == "status_change":
            to_status = str(details.get("to", "") or "")
            title = str(details.get("title", "") or "")
            employer = str(details.get("employer", "") or "")
            items.append(
                {
                    "action": _status_change_action(to_status),
                    "detail": f"{title} at {employer}",
                    "time": time_str,
                }
            )
    return items


@bp.route("/")
def index():
    status = {
        "state": "idle",
        "label": "Pipeline idle",
        "detail": "Last run completed 2 hours ago",
    }
    try:
        activity = _activity_items_from_log()
    except Exception:
        activity = []
    return render_template(
        "dashboard.html",
        active_nav="dashboard",
        status=status,
        activity=activity,
    )
