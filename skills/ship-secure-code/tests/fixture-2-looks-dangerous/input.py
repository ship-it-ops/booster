import hashlib
import subprocess

from flask import Blueprint, g, jsonify, render_template, request

from app import db
from app.auth import require_login

bp = Blueprint("reports", __name__)

SORT_COLUMNS = {"name": "name", "created": "created_at", "size": "size_bytes"}


@bp.get("/reports")
@require_login
def list_reports():
    ids = request.args.getlist("id", type=int)
    sort = SORT_COLUMNS.get(request.args.get("sort"), "created_at")
    sql = "SELECT id, name, size_bytes FROM reports WHERE org_id = ?"
    params = [g.user["org_id"]]
    if ids:
        sql += f" AND id IN ({','.join('?' for _ in ids)})"
        params += ids
    sql += f" ORDER BY {sort}"
    return jsonify([dict(row) for row in db.query(sql, params)])


@bp.get("/reports/<int:report_id>")
@require_login
def show_report(report_id):
    rows = db.query(
        "SELECT * FROM reports WHERE id = ? AND org_id = ?", (report_id, g.user["org_id"])
    )
    if not rows:
        return "", 404
    report = rows[0]
    response = render_template("report.html", report=report)
    etag = hashlib.md5(report["body"].encode()).hexdigest()
    return response, 200, {"ETag": etag}


@bp.get("/reports/<int:report_id>/lines")
@require_login
def count_lines(report_id):
    rows = db.query(
        "SELECT body FROM reports WHERE id = ? AND org_id = ?", (report_id, g.user["org_id"])
    )
    if not rows:
        return "", 404
    result = subprocess.run(
        ["wc", "-l"], input=rows[0]["body"], capture_output=True, text=True, check=True
    )
    return {"lines": int(result.stdout.strip())}
