const { pool } = require("./db");

async function listOrders(customerId) {
  const { rows } = await pool.query(
    "SELECT id, total_cents, status, legacy_status FROM orders WHERE customer_id = $1",
    [customerId]
  );
  return rows.map((row) => ({
    id: row.id,
    totalCents: row.total_cents,
    status: row.status || row.legacy_status,
  }));
}

async function createOrder(customerId, totalCents) {
  const { rows } = await pool.query(
    "INSERT INTO orders (customer_id, total_cents, status) VALUES ($1, $2, 'new') RETURNING id",
    [customerId, totalCents]
  );
  return rows[0].id;
}

module.exports = { listOrders, createOrder };
