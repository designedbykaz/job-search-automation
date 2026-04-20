import json
from pathlib import Path

from flask import Blueprint, abort, render_template, request

from ui.services import tailored_cv

bp = Blueprint("jobs", __name__, url_prefix="/jobs")


SAMPLE_OUTPUTS_ROOT = Path(__file__).resolve().parent.parent / "sample_outputs"


JOBS = [
    {
        "id": 1,
        "title": "Senior Product Designer",
        "employer": "NHS Digital",
        "location": "Leeds",
        "cluster": "ux_design",
        "status": "to_review",
        "closing_date": "2026-05-02",
        "date_found": "2026-04-18",
        "listing_url": "https://example.com/jobs/1",
        "output_folder": str(SAMPLE_OUTPUTS_ROOT / "job_01"),
        "description": [
            "We are looking for an experienced Senior Product Designer to join our digital team working on critical healthcare services used by millions across the UK.",
            "You will lead design work across multiple product areas, working closely with user researchers, product managers, and developers to create accessible, user-centered services that meet the needs of patients and healthcare professionals.",
            "The role requires someone with strong interaction design skills, experience working within government or healthcare contexts, and a deep understanding of accessibility requirements.",
        ],
    },
    {
        "id": 2,
        "title": "UX Researcher",
        "employer": "Department for Education",
        "location": "London",
        "cluster": "user_research",
        "status": "to_review",
        "closing_date": "2026-04-28",
        "date_found": "2026-04-18",
        "listing_url": "https://example.com/jobs/2",
        "output_folder": str(SAMPLE_OUTPUTS_ROOT / "job_02"),
        "description": [
            "Join our user research team to shape how teachers, learners, and school leaders interact with education services.",
            "You will plan and run mixed-methods research, synthesise findings, and work with designers and policy colleagues to turn insights into service improvements.",
        ],
    },
    {
        "id": 3,
        "title": "Service Designer",
        "employer": "HMRC",
        "location": "Manchester",
        "cluster": "service_design",
        "status": "approved",
        "closing_date": "2026-05-10",
        "date_found": "2026-04-18",
        "listing_url": "https://example.com/jobs/3",
        "output_folder": str(SAMPLE_OUTPUTS_ROOT / "job_03"),
        "description": [
            "Design end-to-end services for taxpayers and agents, working across channels and teams.",
            "You will map current-state services, identify friction, and prototype improvements that are testable with real users.",
        ],
    },
    {
        "id": 4,
        "title": "Product Manager",
        "employer": "Home Office",
        "location": "London",
        "cluster": "product_management",
        "status": "to_review",
        "closing_date": "2026-04-25",
        "date_found": "2026-04-18",
        "listing_url": "https://example.com/jobs/4",
        "output_folder": str(SAMPLE_OUTPUTS_ROOT / "job_04"),
        "description": [
            "Own the roadmap for a cross-cutting internal platform used by frontline staff.",
            "You will set priorities, work with designers and engineers, and measure impact against clear outcomes.",
        ],
    },
    {
        "id": 5,
        "title": "Interaction Designer",
        "employer": "DVLA",
        "location": "Swansea",
        "cluster": "ux_design",
        "status": "approved",
        "closing_date": "2026-05-05",
        "date_found": "2026-04-17",
        "listing_url": "https://example.com/jobs/5",
        "output_folder": str(SAMPLE_OUTPUTS_ROOT / "job_05"),
        "description": [
            "Design interactions for high-volume transactional services used by millions of citizens every year.",
            "The role balances accessibility, simplicity, and regulatory constraints.",
        ],
    },
    {
        "id": 6,
        "title": "Clinical Systems Designer",
        "employer": "NHS England",
        "location": "Remote",
        "cluster": "nhs_healthcare",
        "status": "to_review",
        "closing_date": "2026-05-12",
        "date_found": "2026-04-17",
        "listing_url": "https://example.com/jobs/6",
        "output_folder": str(SAMPLE_OUTPUTS_ROOT / "job_06"),
        "description": [
            "Work with clinicians to design systems that support safe, efficient care delivery.",
            "You will translate complex clinical workflows into usable digital tools.",
        ],
    },
    {
        "id": 7,
        "title": "Head of User Research",
        "employer": "Ministry of Justice",
        "location": "London",
        "cluster": "user_research",
        "status": "rendered",
        "closing_date": "2026-04-30",
        "date_found": "2026-04-16",
        "listing_url": "https://example.com/jobs/7",
        "output_folder": str(SAMPLE_OUTPUTS_ROOT / "job_07"),
        "description": [
            "Lead a multidisciplinary research function across several service areas.",
            "You will grow the team, set research strategy, and advocate for user needs at senior levels.",
        ],
    },
    {
        "id": 8,
        "title": "Design System Lead",
        "employer": "GDS",
        "location": "London",
        "cluster": "design_systems",
        "status": "approved",
        "closing_date": "2026-05-08",
        "date_found": "2026-04-16",
        "listing_url": "https://example.com/jobs/8",
        "output_folder": str(SAMPLE_OUTPUTS_ROOT / "job_08"),
        "description": [
            "Lead the direction of a cross-government design system used by hundreds of service teams.",
            "You will set standards, support contributors, and ensure patterns meet accessibility guidelines.",
        ],
    },
]


def _seed_sample_output(job: dict) -> None:
    """Write a stub cv_tailored.json for a sample job if none exists.

    Sample data only: replicates the v1 pipeline's output folder layout so the
    save/reset flow has something real to read and write. Never overwrites an
    existing file, so edited or customised fixtures survive server restarts.
    """
    folder = Path(job["output_folder"])
    original = folder / tailored_cv.ORIGINAL_NAME
    if original.is_file():
        return

    stub = {
        "NAME": "Alex Jordan",
        "OBJECTIVE": (
            f"Experienced practitioner applying for the {job['title']} role at "
            f"{job['employer']}. Brings a track record of shipping accessible, "
            "user-centred services in regulated environments."
        ),
        "EXP_1_ROLE": "Lead Practitioner",
        "EXP_1_COMPANY": "Previous Employer",
        "EXP_1_DATE": "Jan 2022 - Present",
        "EXP_1_BODY": (
            "Led cross-functional work on several public-facing services, "
            "partnering with researchers, engineers, and delivery managers."
        ),
        "CLUSTER": job["cluster"],
        "JOB_TITLE": job["title"],
        "EMPLOYER": job["employer"],
    }

    folder.mkdir(parents=True, exist_ok=True)
    original.write_text(
        json.dumps(stub, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _ensure_sample_outputs() -> None:
    for job in JOBS:
        _seed_sample_output(job)


_ensure_sample_outputs()


def _get_job(job_id: int) -> dict:
    job = next((j for j in JOBS if j["id"] == job_id), None)
    if job is None:
        abort(404)
    return job


def _filter_jobs(status):
    if not status or status == "all":
        return JOBS
    return [j for j in JOBS if j["status"] == status]


def _render_detail(job: dict):
    data, is_edited = tailored_cv.read_preferred(job["output_folder"])
    cv_json_text = json.dumps(data, indent=2, ensure_ascii=False)
    templates = ["A", "B", "C"]
    return render_template(
        "jobs/_detail.html",
        job=job,
        templates=templates,
        selected_template="A",
        cv_json_text=cv_json_text,
        is_edited=is_edited,
    )


@bp.route("/")
def index():
    status = request.args.get("status", "all")
    search = request.args.get("q", "").strip().lower()
    rows = _filter_jobs(status)
    if search:
        rows = [j for j in rows if search in j["title"].lower() or search in j["employer"].lower()]
    statuses = [
        ("all", "All statuses"),
        ("to_review", "To review"),
        ("approved", "Approved"),
        ("rendered", "Rendered"),
    ]
    return render_template(
        "jobs/index.html",
        active_nav="jobs",
        jobs=rows,
        selected_status=status,
        search=search,
        statuses=statuses,
    )


@bp.route("/<int:job_id>")
def detail(job_id):
    return _render_detail(_get_job(job_id))


@bp.route("/<int:job_id>/cv-edit", methods=["POST"])
def cv_edit(job_id):
    job = _get_job(job_id)
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

    tailored_cv.save_edit(job["output_folder"], data)
    return render_template(
        "jobs/_cv_save_feedback.html",
        job=job,
        success=True,
    )


@bp.route("/<int:job_id>/cv-edit/reset", methods=["POST"])
def cv_edit_reset(job_id):
    job = _get_job(job_id)
    tailored_cv.reset_edit(job["output_folder"])
    return _render_detail(job)
