import os

from dotenv import load_dotenv

load_dotenv()


def _normalize_database_url(url):
    if not url:
        return url
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.getenv("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    REQUIRED_ENV_VARS = ("DATABASE_URL", "ADMIN_USERNAME")


def validate_required_environment():
    missing = [name for name in Config.REQUIRED_ENV_VARS if not os.getenv(name)]
    if not (Config.ADMIN_PASSWORD or Config.ADMIN_PASSWORD_HASH):
        missing.append("ADMIN_PASSWORD or ADMIN_PASSWORD_HASH")

    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(
            f"Missing required environment variable(s): {missing_text}. "
            "Create Leader-board/.env with the required values."
        )
