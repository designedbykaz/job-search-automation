from flask import Blueprint, render_template

bp = Blueprint("prompts", __name__, url_prefix="/prompts")


@bp.route("/")
def index():
    return render_template("prompts/index.html", active_nav="prompts")
