from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from ui.services import job_index


def create_app():
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    app = Flask(__name__)

    from ui.routes import (
        dashboard,
        pipeline,
        jobs,
        content,
        prompts,
        cv_templates,
        settings,
        cluster_admin,
    )

    app.register_blueprint(dashboard.bp)
    app.register_blueprint(pipeline.bp)
    app.register_blueprint(cluster_admin.bp)
    app.register_blueprint(jobs.bp)
    app.register_blueprint(content.bp)
    app.register_blueprint(prompts.bp)
    app.register_blueprint(cv_templates.bp)
    app.register_blueprint(settings.bp)

    @app.context_processor
    def inject_topbar_counters():
        try:
            return {"topbar_counters": job_index.get_counters()}
        except Exception:
            return {"topbar_counters": {"to_review": 0, "approved": 0, "pdf_ready": 0}}

    return app
