"""Customer queries. Deployed as part of the `web` and `billing-worker` services."""


def find_by_email(conn, email):
    return conn.execute(
        "SELECT id, name, email, phone FROM customers WHERE email = %s", (email,)
    ).fetchone()


def create(conn, name, email, phone=None):
    return conn.execute(
        "INSERT INTO customers (name, email, phone) VALUES (%s, %s, %s) RETURNING id",
        (name, email, phone),
    ).fetchone()[0]
