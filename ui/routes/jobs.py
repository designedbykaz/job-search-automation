from flask import Blueprint, abort, render_template, request

bp = Blueprint("jobs", __name__, url_prefix="/jobs")


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
        "description": [
            "Lead the direction of a cross-government design system used by hundreds of service teams.",
            "You will set standards, support contributors, and ensure patterns meet accessibility guidelines.",
        ],
    },
]


SAMPLE_CV_JSON = """{
  "NAME": "Alex Jordan",
  "OBJECTIVE": "Senior product designer with 8 years experience designing accessible healthcare services...",
  "EXP_1_ROLE": "Lead Product Designer",
  "EXP_1_BODY": "Designed patient-facing services for NHS trusts..."
}"""


def _filter_jobs(status):
    if not status or status == "all":
        return JOBS
    return [j for j in JOBS if j["status"] == status]


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
    job = next((j for j in JOBS if j["id"] == job_id), None)
    if job is None:
        abort(404)
    templates = ["A", "B", "C"]
    return render_template(
        "jobs/_detail.html",
        job=job,
        templates=templates,
        selected_template="A",
        cv_json=SAMPLE_CV_JSON,
    )
