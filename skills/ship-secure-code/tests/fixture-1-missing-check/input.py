from flask import Blueprint, abort, g, jsonify, request

from app import db
from app.auth import require_login

bp = Blueprint("projects", __name__)


def load_project(project_id):
    rows = db.query(
        "SELECT * FROM projects WHERE id = ? AND org_id = ?", (project_id, g.user["org_id"])
    )
    if not rows:
        abort(404)
    return rows[0]


@bp.get("/projects/<int:project_id>")
@require_login
def show_project(project_id):
    return jsonify(dict(load_project(project_id)))


@bp.post("/projects/<int:project_id>/rename")
@require_login
def rename_project(project_id):
    load_project(project_id)
    db.query("UPDATE projects SET name = ? WHERE id = ?", (request.form["name"], project_id))
    return "", 204


@bp.get("/projects/<int:project_id>/members")
@require_login
def list_members(project_id):
    rows = db.query(
        "SELECT u.id, u.email FROM members m JOIN users u ON u.id = m.user_id WHERE m.project_id = ?",
        (project_id,),
    )
    return jsonify([dict(row) for row in rows])


@bp.post("/projects/<int:project_id>/transfer")
@require_login
def transfer_project(project_id):
    project = load_project(project_id)
    if project["owner_id"] != g.user["id"]:
        abort(403)
    db.query(
        "UPDATE projects SET org_id = ? WHERE id = ?", (request.form["org_id"], project_id)
    )
    return "", 204


@bp.get("/health")
def health():
    return {"ok": True}
