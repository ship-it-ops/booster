import os
import subprocess
import tempfile

import requests
from flask import Blueprint, abort, g, jsonify, request, send_file

from teamdocs import db
from teamdocs.auth import require_doc_access, require_login

bp = Blueprint("integrations", __name__)

EXPORT_FORMATS = ("pdf", "docx", "html")


@bp.post("/docs/import")
@require_login
def import_doc():
    """Create a document from the text at a URL the user supplies."""
    url = request.get_json()["url"]
    if "localhost" in url or "127.0.0.1" in url:
        abort(400)
    fetched = requests.get(url, timeout=10)
    cursor = db.execute(
        "INSERT INTO documents (team_id, owner_id, title, body) VALUES (?, ?, ?, ?)",
        (g.user["team_id"], g.user["id"], url, fetched.text),
    )
    return jsonify(id=cursor.lastrowid), 201


@bp.get("/docs/<int:doc_id>/export")
@require_doc_access
def export_doc(doc_id):
    fmt = request.args.get("format", "pdf")
    workdir = tempfile.mkdtemp()
    source = os.path.join(workdir, "doc.md")
    with open(source, "w") as handle:
        handle.write(g.doc["body"])
    target = os.path.join(workdir, f"doc.{fmt}")
    subprocess.run(f"pandoc {source} -o {target}", shell=True, check=True)
    return send_file(target)


@bp.get("/docs/<int:doc_id>/export/formats")
@require_doc_access
def export_formats(doc_id):
    version = subprocess.run(["pandoc", "--version"], capture_output=True, text=True, check=True)
    return jsonify(formats=EXPORT_FORMATS, pandoc=version.stdout.splitlines()[0])


@bp.post("/docs/<int:doc_id>/copy")
@require_login
def copy_doc(doc_id):
    """Copy a document into the caller's team."""
    rows = db.query("SELECT title, body FROM documents WHERE id = ?", (doc_id,))
    if not rows:
        abort(404)
    cursor = db.execute(
        "INSERT INTO documents (team_id, owner_id, title, body) VALUES (?, ?, ?, ?)",
        (g.user["team_id"], g.user["id"], rows[0]["title"], rows[0]["body"]),
    )
    return jsonify(id=cursor.lastrowid), 201
