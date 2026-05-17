import json
from pathlib import Path

from flask import Blueprint, Response, abort, current_app, jsonify, redirect, render_template, request, send_file, url_for

from pipeline.tailor import tailor_cv

from ui.services import (
    activity_log,
    cv_template_choice,
    job_index,
    preview,
    sheets,
    tailored_cv,
)

bp = Blueprint("jobs", __name__, url_prefix="/jobs")

REPO_ROOT = Path(__file__).resolve().parents[2]


def _resolved_output_folder(output_folder: str | None) -> Path | None:
    if not output_folder or not str(output_folder).strip():
        return None
    p = Path(output_folder.strip())
    if not p.is_absolute():
        p = REPO_ROOT / p
    return p


def _output_folder_usable(output_folder: str) -> bool:
    p = _resolved_output_folder(output_folder)
    return p is not None and p.is_dir()


def _output_path_str(output_folder: str) -> str:
    p = _resolved_output_folder(output_folder)
    return str(p) if p else ""


def _has_usable_tailored_cv(output_folder: str) -> bool:
    if not _output_folder_usable(output_folder):
        return False
    folder = _resolved_output_folder(output_folder)
    if folder is None:
        return False
    original = folder / tailored_cv.ORIGINAL_NAME
    return original.is_file() or tailored_cv.has_edit(folder)


def _normalize_job(job: dict) -> dict:
    """Index entries use sheet_row; templates expect row, description list."""
    import re
    out = dict(job)
    if "row" not in out:
        out["row"] = out.get("sheet_row")
    desc = out.get("description")
    if not desc:
        out["description"] = []
    elif isinstance(desc, str):
        parts = [p.strip() for p in re.split(r"\n+", desc) if p.strip()]
        out["description"] = parts if parts else []
    return out


def _get_job(row: int) -> dict:
    job = job_index.get_job_by_row(row)
    if job is None:
        abort(404)
    return _normalize_job(job)


def _job_from_request_for_row(row: int) -> dict:
    """Prefer output_folder from the request when it resolves to a usable folder (no Sheets read)."""
    out = (request.values.get("output_folder") or "").strip()
    if out and _output_folder_usable(out):
        return _normalize_job({"row": row, "output_folder": out})
    return _get_job(row)


def _cv_detail_context(job: dict) -> dict:
    out = (job.get("output_folder") or "").strip()
    folder_usable = _output_folder_usable(out)
    show_cv_editor = _has_usable_tailored_cv(out)
    path_str = _output_path_str(out)

    data: dict = {}
    is_edited = False
    cv_json_text = ""
    preview_html = ""

    if show_cv_editor:
        data, is_edited = tailored_cv.read_preferred(path_str)
        cv_json_text = json.dumps(data, indent=2, ensure_ascii=False)
        selected_template = cv_template_choice.get_choice(path_str)
        preview_html = preview.render_preview_html(
            path_str,
            data=data,
            job_id=job["row"],
            template_choice=selected_template,
        )
    else:
        selected_template = (
            cv_template_choice.get_choice(path_str)
            if folder_usable
            else "a"
        )

    templates = ["a", "b", "c"]
    return {
        "templates": templates,
        "selected_template": selected_template,
        "cv_json_text": cv_json_text,
        "is_edited": is_edited,
        "preview_html": preview_html,
        "folder_usable": folder_usable,
        "show_cv_editor": show_cv_editor,
    }


def _render_detail(job: dict):
    ctx = _cv_detail_context(job)
    return render_template(
        "jobs/_detail.html",
        job=job,
        **ctx,
    )


@bp.route("/")
def index():
    status = request.args.get("status", "all")
    search = request.args.get("q", "").strip().lower()
    sheet_configured = sheets.is_configured()
    rows = job_index.list_jobs(
        status_filter=status if status != "all" else None,
        search=search if search else None,
    )
    rows = [_normalize_job(j) for j in rows]
    statuses = [
        ("all", "All statuses"),
        ("to_review", "To review"),
        ("approved", "Approved"),
        ("pdf_ready", "PDF Ready"),
    ]
    return render_template(
        "jobs/index.html",
        active_nav="jobs",
        jobs=rows,
        selected_status=status,
        search=search,
        statuses=statuses,
        sheet_configured=sheet_configured,
    )


@bp.route("/<int:row>")
def detail(row):
    return redirect(url_for("jobs.index"), code=302)


@bp.route("/<int:row>/cv-sections", methods=["GET"])
def cv_sections(row):
    """Disk-only CV + template markup for the job detail pane (no Google Sheets read)."""
    if row < 2:
        abort(404)
    output_folder = (request.args.get("output_folder") or "").strip()
    job = {"row": row, "output_folder": output_folder}
    ctx = _cv_detail_context(job)
    return render_template("jobs/_detail_cv_sections.html", job=job, **ctx)


@bp.route("/<int:row>/approve", methods=["POST"])
def approve(row):
    raw = job_index.get_job_by_row(row)
    if raw is None:
        abort(404)
    job = _normalize_job(raw)
    try:
        index_ok = job_index.set_status(job["slug"], "approved")
    except ValueError:
        return render_template(
            "jobs/_action_row.html",
            job=job,
            approve_error="Could not update the index. Try again or check the logs.",
        )
    if not index_ok:
        return render_template(
            "jobs/_action_row.html",
            job=job,
            approve_error="Could not update the index. Try again or check the logs.",
        )
    sheet_ok = sheets.approve_job(row)
    if not sheet_ok:
        current_app.logger.warning(
            "Approve: index updated for row %s but Sheet write failed. The index is the source of truth, "
            "sheet will need a manual sync later.",
            row,
        )
    activity_log.record_status_change(
        slug=job["slug"],
        title=job.get("title", ""),
        employer=job.get("employer", ""),
        from_status=job.get("status", "to_review"),
        to_status="approved",
    )
    output_folder_path = _resolved_output_folder(job.get("output_folder", ""))
    if output_folder_path is not None and output_folder_path.is_dir():
        job_for_tailor = {
            "title": job.get("title", ""),
            "employer": job.get("employer", ""),
            "description": job.get("description", "") if isinstance(job.get("description"), str) else "\n\n".join(job.get("description") or []),
        }
        try:
            tailor_cv(job_for_tailor, output_folder_path)
        except Exception as exc:
            current_app.logger.warning(
                "Approve: tailoring failed for row %s (%s). Job is approved but no cv_tailored.json was written. Cause: %s",
                row,
                job.get("slug", ""),
                exc,
            )
    raw_updated = job_index.get_job_by_row(row)
    updated = _normalize_job(raw_updated or {**job, "status": "approved"})
    return render_template("jobs/_action_row.html", job=updated, approve_error=None)


@bp.route("/<int:row>/render", methods=["POST"])
def render(row):
    raw = job_index.get_job_by_row(row)
    if raw is None:
        abort(404)
    job = _normalize_job(raw)
    output_folder_path = _resolved_output_folder(job.get("output_folder", ""))
    if output_folder_path is None or not output_folder_path.is_dir():
        return render_template(
            "jobs/_action_row.html",
            job=job,
            render_error="Cannot render. Output folder is missing.",
        )
    tailored_data, _ = tailored_cv.read_preferred(str(output_folder_path))
    if not tailored_data:
        return render_template(
            "jobs/_action_row.html",
            job=job,
            render_error="Cannot render. No tailored CV found. Try re-approving to retrigger tailoring.",
        )
    template_choice = cv_template_choice.get_choice(str(output_folder_path))
    try:
        from ui.services.render import render_pdf_for_job

        render_pdf_for_job(output_folder_path, tailored_data, template_choice)
    except Exception as exc:
        current_app.logger.warning(
            "Render: failed for row %s (%s). Cause: %s",
            row,
            job.get("slug", ""),
            exc,
        )
        return render_template(
            "jobs/_action_row.html",
            job=job,
            render_error="Render failed. Check the server logs for details.",
        )
    try:
        job_index.set_status(job["slug"], "pdf_ready")
    except ValueError:
        pass
    sheet_ok = sheets.mark_pdf_ready(row)
    if not sheet_ok:
        current_app.logger.warning(
            "Render: index updated for row %s but Sheet write failed. The index is the source of truth, "
            "sheet will need a manual sync later.",
            row,
        )
    activity_log.record_status_change(
        slug=job["slug"],
        title=job.get("title", ""),
        employer=job.get("employer", ""),
        from_status=job.get("status", "approved"),
        to_status="pdf_ready",
    )
    raw_updated = job_index.get_job_by_row(row)
    updated = _normalize_job(raw_updated or {**job, "status": "pdf_ready"})
    return render_template("jobs/_action_row.html", job=updated, render_error=None)


@bp.route("/<int:row>/download", methods=["GET"])
def download_pdf(row):
    job = job_index.get_job_by_row(row)
    if job is None:
        abort(404)
    output_folder_path = _resolved_output_folder(job.get("output_folder", ""))
    if output_folder_path is None or not output_folder_path.is_dir():
        abort(404)
    pdf_path = output_folder_path / "cv_output.pdf"
    if not pdf_path.is_file():
        abort(404)
    slug_tail = (job.get("slug", "") or "cv_output").split("/")[-1]
    download_name = f"{slug_tail}.pdf"
    return send_file(
        str(pdf_path),
        as_attachment=True,
        download_name=download_name,
        mimetype="application/pdf",
    )


@bp.route("/<int:row>/delete", methods=["POST"])
def delete_job_route(row):
    job = job_index.get_job_by_row(row)
    if job is None:
        abort(404)
    slug = job.get("slug")
    if not slug:
        abort(404)
    removed = job_index.delete_job(slug)
    if not removed:
        return jsonify({"ok": False, "error": "not found"}), 404
    return jsonify({"ok": True, "row": row})


@bp.route("/<int:row>/cv-edit", methods=["POST"])
def cv_edit(row):
    job = _job_from_request_for_row(row)
    if not _output_folder_usable(job["output_folder"]):
        return render_template(
            "jobs/_cv_save_feedback.html",
            job=job,
            success=False,
            error="Output folder is missing. Cannot save edits.",
        )
    json_text = request.form.get("json_text", "")
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        return render_template(
            "jobs/_cv_save_feedback.html",
            job=job,
            success=False,
            error=str(exc),
        )

    path_str = _output_path_str(job["output_folder"])
    tailored_cv.save_edit(path_str, data)
    return render_template(
        "jobs/_cv_save_feedback.html",
        job=job,
        success=True,
    )


@bp.route("/<int:row>/cv-edit/reset", methods=["POST"])
def cv_edit_reset(row):
    job = _get_job(row)
    tailored_cv.reset_edit(_output_path_str(job["output_folder"]))
    return _render_detail(job)


@bp.route("/<int:row>/preview/content", methods=["GET", "POST"])
def preview_content(row):
    """Return a complete HTML document for the preview iframe."""
    out = (request.values.get("output_folder") or "").strip()
    if out and _output_folder_usable(out):
        path_str = _output_path_str(out)
    else:
        job = _get_job(row)
        path_str = _output_path_str(job["output_folder"])
        if not path_str or not _output_folder_usable(job["output_folder"]):
            return Response(
                '<!DOCTYPE html><html><body><p class="text-muted small">No preview available.</p></body></html>',
                mimetype="text/html",
            )

    selected_template = cv_template_choice.get_choice(path_str)

    data = None
    if request.method == "POST":
        json_text = request.form.get("json_text", "")
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError:
            data = None

    html = preview.render_preview_html(
        path_str,
        data=data,
        job_id=row,
        template_choice=selected_template,
    )
    return Response(html, mimetype="text/html")


@bp.route("/<int:row>/template", methods=["POST"])
def set_template(row):
    job = _job_from_request_for_row(row)
    if not _output_folder_usable(job["output_folder"]):
        return jsonify({"ok": False, "error": "no output folder"}), 400
    choice = (request.form.get("template") or "").lower()
    try:
        saved = cv_template_choice.set_choice(_output_path_str(job["output_folder"]), choice)
    except ValueError:
        return jsonify({"ok": False, "error": "invalid template"}), 400
    return jsonify({"ok": True, "template": saved})
