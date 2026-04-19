from flask import Blueprint, render_template

bp = Blueprint("content", __name__, url_prefix="/content")


@bp.route("/")
def index():
    return render_template("content/index.html", active_nav="content")
