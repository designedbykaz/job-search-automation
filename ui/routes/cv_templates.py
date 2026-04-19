from flask import Blueprint, render_template

bp = Blueprint("cv_templates", __name__, url_prefix="/templates")


@bp.route("/")
def index():
    return render_template("cv_templates/index.html", active_nav="templates")
