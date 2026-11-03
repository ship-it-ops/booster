import os


def load_config():
    return {
        "DATABASE": os.environ.get("TEAMDOCS_DATABASE", "teamdocs.db"),
        "SECRET_KEY": os.environ.get("TEAMDOCS_SECRET_KEY", "dev-secret-change-me"),
        "UPLOAD_DIR": os.environ.get("TEAMDOCS_UPLOAD_DIR", "/var/lib/teamdocs/uploads"),
        "PARTNER_KEY": os.environ.get("TEAMDOCS_PARTNER_KEY"),
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
    }
