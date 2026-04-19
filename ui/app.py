from pathlib import Path

from dotenv import load_dotenv
from flask import Flask


def create_app():
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    app = Flask(__name__)

    from ui.routes import dashboard, pipeline, jobs, content, prompts, cv_templates, settings

    app.register_blueprint(dashboard.bp)
    app.register_blueprint(pipeline.bp)
    app.register_blueprint(jobs.bp)
    app.register_blueprint(content.bp)
    app.register_blueprint(prompts.bp)
    app.register_blueprint(cv_templates.bp)
    app.register_blueprint(settings.bp)

    return app
