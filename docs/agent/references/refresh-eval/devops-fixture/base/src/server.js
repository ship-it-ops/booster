const http = require("http");
const { pool } = require("./db");
const { listOrders } = require("./orders");

const server = http.createServer(async (req, res) => {
  if (req.url === "/health") {
    try {
      await pool.query("SELECT 1");
      res.writeHead(200).end("ok");
    } catch (error) {
      res.writeHead(503).end("database unavailable");
    }
    return;
  }
  if (req.url.startsWith("/orders/")) {
    const orders = await listOrders(req.url.split("/")[2]);
    res.writeHead(200, { "Content-Type": "application/json" }).end(JSON.stringify(orders));
    return;
  }
  res.writeHead(404).end();
});

server.listen(process.env.PORT || 8080);
