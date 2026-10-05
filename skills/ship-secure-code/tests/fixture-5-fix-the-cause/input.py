from flask import Blueprint, g, jsonify, request

from app import db
from app.auth import require_login

bp = Blueprint("search", __name__)


@bp.get("/customers")
@require_login
def list_customers():
    sort = request.args.get("sort", "name")
    rows = db.query(
        f"SELECT id, name, city FROM customers WHERE org_id = ? ORDER BY {sort}",
        (g.user["org_id"],),
    )
    return jsonify([dict(row) for row in rows])


@bp.get("/orders")
@require_login
def list_orders():
    sort = request.args.get("sort", "placed_at")
    direction = request.args.get("dir", "asc")
    rows = db.query(
        f"SELECT id, total, placed_at FROM orders WHERE org_id = ? ORDER BY {sort} {direction}",
        (g.user["org_id"],),
    )
    return jsonify([dict(row) for row in rows])


@bp.get("/customers/<int:customer_id>")
@require_login
def show_customer(customer_id):
    rows = db.query("SELECT * FROM customers WHERE id = ?", (customer_id,))
    return jsonify(dict(rows[0])) if rows else ("", 404)
