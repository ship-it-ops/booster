import hashlib

from flask import Blueprint, jsonify, request, session

from app import db

bp = Blueprint("auth", __name__)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@bp.post("/login")
def login():
    rows = db.query("SELECT * FROM users WHERE email = ?", (request.form["email"],))
    if not rows or rows[0]["password_hash"] != hash_password(request.form["password"]):
        return jsonify(error="invalid credentials"), 401
    session.clear()
    session["user_id"] = rows[0]["id"]
    return "", 204


@bp.post("/logout")
def logout():
    session.clear()
    return "", 204
