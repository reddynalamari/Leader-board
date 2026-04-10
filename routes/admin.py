from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.security import generate_password_hash

from models import db
from models.user import Judge, User
from utils.auth import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/dashboard")
@role_required("admin")
def dashboard():
    return render_template("admin/dashboard.html")


@admin_bp.route("/judges", methods=["GET", "POST"])
@role_required("admin")
def manage_judges():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        display_name = request.form.get("display_name", "").strip()
        password = request.form.get("password", "")
        phone = request.form.get("phone", "").strip()
        organization = request.form.get("organization", "").strip()

        if not username or not email or not display_name or not password:
            flash("Username, email, display name, and password are required.", "warning")
            return redirect(url_for("admin.manage_judges"))

        try:
            existing_user = User.query.filter(
                or_(User.username == username, User.email == email)
            ).first()

            if existing_user:
                flash("A user with this username or email already exists.", "warning")
                return redirect(url_for("admin.manage_judges"))

            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role="judge",
                is_active=True,
            )
            Judge(
                user=user,
                display_name=display_name,
                phone=phone or None,
                organization=organization or None,
                is_active=True,
            )

            db.session.add(user)
            db.session.commit()
            flash("Judge created successfully.", "success")
        except IntegrityError:
            db.session.rollback()
            flash("Unable to create judge due to duplicate data.", "danger")
        except SQLAlchemyError as exc:
            db.session.rollback()
            current_app.logger.error("Judge creation failed: %s", exc)
            flash(
                "Judge creation failed. Ensure database schema is applied correctly.",
                "danger",
            )

        return redirect(url_for("admin.manage_judges"))

    try:
        judges = (
            db.session.query(User, Judge)
            .join(Judge, Judge.user_id == User.id)
            .filter(User.role == "judge")
            .order_by(User.id.asc())
            .all()
        )
    except SQLAlchemyError as exc:
        current_app.logger.error("Judge list query failed: %s", exc)
        flash("Unable to load judges. Ensure database schema is applied.", "warning")
        judges = []

    return render_template("admin/judges.html", judges=judges)


@admin_bp.post("/judges/<int:user_id>/delete")
@role_required("admin")
def delete_judge(user_id):
    try:
        user = User.query.filter_by(id=user_id, role="judge").first()
        if not user:
            flash("Judge not found.", "warning")
            return redirect(url_for("admin.manage_judges"))

        db.session.delete(user)
        db.session.commit()
        flash("Judge deleted successfully.", "success")
    except SQLAlchemyError as exc:
        db.session.rollback()
        current_app.logger.error("Judge delete failed: %s", exc)
        flash("Unable to delete judge.", "danger")

    return redirect(url_for("admin.manage_judges"))
