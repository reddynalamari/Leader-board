from flask import Blueprint, render_template
from flask_login import current_user

from utils.auth import role_required

judge_bp = Blueprint("judge", __name__, url_prefix="/judge")


@judge_bp.get("/dashboard")
@role_required("judge")
def dashboard():
    return render_template("judge/dashboard.html", judge=current_user)
