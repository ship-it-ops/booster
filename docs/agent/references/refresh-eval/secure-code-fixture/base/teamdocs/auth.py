import functools
import hashlib
import logging

from flask import Blueprint, abort, g, jsonify, redirect, request, session

from teamdocs import db

bp = Blueprint("auth", __name__)
log = logging.getLogger(__name__)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@bp.before_app_request
def load_user():
    g.user = None
    user_id = session.get("user_id")
    if user_id is not None:
        rows = db.query("SELECT * FROM users WHERE id = ?", (user_id,))
        g.user = rows[0] if rows else None


def require_login(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            abort(401)
        return view(*args, **kwargs)

    return wrapped


def require_doc_access(view):
    """The document named by `doc_id` must belong to the caller's team."""

    @functools.wraps(view)
    @require_login
    def wrapped(doc_id, *args, **kwargs):
        rows = db.query("SELECT * FROM documents WHERE id = ?", (doc_id,))
        if not rows or rows[0]["team_id"] != g.user["team_id"]:
            abort(404)
        g.doc = rows[0]
        return view(doc_id, *args, **kwargs)

    return wrapped


@bp.post("/login")
def login():
    email = request.form["email"]
    password = request.form["password"]
    log.info("login attempt email=%s password=%s", email, password)
    rows = db.query("SELECT * FROM users WHERE email = ?", (email,))
    if not rows or rows[0]["password_hash"] != hash_password(password):
        return jsonify(error="invalid credentials"), 401
    session.clear()
    session["user_id"] = rows[0]["id"]
    return redirect(request.args.get("next", "/"))


@bp.post("/logout")
def logout():
    session.clear()
    return "", 204
