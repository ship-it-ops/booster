import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
    team_id INTEGER NOT NULL, is_admin INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY, team_id INTEGER NOT NULL, owner_id INTEGER NOT NULL,
    title TEXT NOT NULL, body TEXT NOT NULL, archived INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def connection():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def query(sql, params=()):
    return connection().execute(sql, params).fetchall()


def execute(sql, params=()):
    conn = connection()
    cursor = conn.execute(sql, params)
    conn.commit()
    return cursor


def init_app(app):
    with app.app_context():
        connection().executescript(SCHEMA)

    @app.teardown_appcontext
    def close(_error):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()
