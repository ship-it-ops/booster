import hashlib
import subprocess

from flask import Blueprint, g, jsonify, render_template, render_template_string, request

from teamdocs import db
from teamdocs.auth import require_doc_access, require_login

bp = Blueprint("docs", __name__)

EDITABLE_FIELDS = ("title", "body", "archived")


@bp.get("/docs")
@require_login
def list_docs():
    ids = request.args.getlist("id", type=int)
    if ids:
        placeholders = ",".join("?" for _ in ids)
        rows = db.query(
            f"SELECT id, title FROM documents WHERE team_id = ? AND id IN ({placeholders})",
            (g.user["team_id"], *ids),
        )
    else:
        rows = db.query("SELECT id, title FROM documents WHERE team_id = ?", (g.user["team_id"],))
    return jsonify([dict(row) for row in rows])


@bp.get("/docs/search")
@require_login
def search_docs():
    term = request.args.get("q", "")
    sort = request.args.get("sort", "updated_at")
    rows = db.query(
        f"SELECT id, title FROM documents WHERE team_id = ? AND title LIKE ? ORDER BY {sort}",
        (g.user["team_id"], f"%{term}%"),
    )
    return jsonify([dict(row) for row in rows])


@bp.get("/docs/<int:doc_id>")
@require_doc_access
def get_doc(doc_id):
    response = jsonify(dict(g.doc))
    response.set_etag(hashlib.md5(g.doc["body"].encode()).hexdigest())
    return response


@bp.get("/docs/<int:doc_id>/view")
@require_doc_access
def view_doc(doc_id):
    return render_template("doc.html", title=g.doc["title"], body=g.doc["body"])


@bp.get("/docs/<int:doc_id>/print")
@require_doc_access
def print_doc(doc_id):
    return render_template_string("<h1>" + g.doc["title"] + "</h1><pre>{{ body }}</pre>", body=g.doc["body"])


@bp.patch("/docs/<int:doc_id>")
@require_doc_access
def update_doc(doc_id):
    changes = request.get_json()
    assignments = ", ".join(f"{field} = ?" for field in changes)
    db.execute(f"UPDATE documents SET {assignments} WHERE id = ?", (*changes.values(), doc_id))
    return "", 204


@bp.delete("/docs/<int:doc_id>")
@require_login
def delete_doc(doc_id):
    db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    return "", 204


@bp.get("/docs/<int:doc_id>/wordcount")
@require_doc_access
def word_count(doc_id):
    result = subprocess.run(["wc", "-w"], input=g.doc["body"], capture_output=True, text=True, check=True)
    return jsonify(words=int(result.stdout.strip()))
