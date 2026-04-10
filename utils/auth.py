import hmac
from functools import wraps

from flask import abort
from flask_login import UserMixin, current_user, login_required
from werkzeug.security import check_password_hash

from config import Config
from models import db
from models.user import User


class AdminSessionUser(UserMixin):
    def __init__(self, username):
        self.username = username
        self.role = "admin"

    def get_id(self):
        return f"admin:{self.username}"


def authenticate_admin(username, password):
    if not Config.ADMIN_USERNAME:
        return None

    normalized_username = (username or "").strip()
    if not hmac.compare_digest(normalized_username, Config.ADMIN_USERNAME):
        return None

    if Config.ADMIN_PASSWORD_HASH:
        is_valid_password = check_password_hash(Config.ADMIN_PASSWORD_HASH, password)
    else:
        admin_password = Config.ADMIN_PASSWORD or ""
        is_valid_password = hmac.compare_digest(password or "", admin_password)

    if not is_valid_password:
        return None

    return AdminSessionUser(Config.ADMIN_USERNAME)


def load_session_user(user_id):
    if not user_id:
        return None

    if str(user_id).startswith("admin:"):
        session_username = str(user_id).split(":", 1)[1]
        if Config.ADMIN_USERNAME and hmac.compare_digest(session_username, Config.ADMIN_USERNAME):
            return AdminSessionUser(session_username)
        return None

    raw_user_id = str(user_id)
    if raw_user_id.startswith("judge:"):
        raw_user_id = raw_user_id.split(":", 1)[1]

    try:
        user = db.session.get(User, int(raw_user_id))
    except (TypeError, ValueError):
        return None

    if not user or not user.is_active:
        return None

    if user.role != "judge":
        return None

    judge_profile = user.judge_profile
    if judge_profile and not judge_profile.is_active:
        return None

    return user


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(*args, **kwargs):
            if getattr(current_user, "role", None) not in allowed_roles:
                abort(403)

            return view_func(*args, **kwargs)

        return wrapped

    return decorator
