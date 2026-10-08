const http = require("node:http");
const { parse } = require("datefmt");
const { thumbnail } = require("imgsharp");
const { printLabel } = require("./labels");

http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  if (url.pathname === "/pickup") {
    // the date comes straight from the query string
    const when = parse(url.searchParams.get("date"));
    res.end(JSON.stringify({ pickup: when }));
  } else if (url.pathname === "/label") {
    res.end(printLabel(url.searchParams.get("carrier"), url.searchParams.get("id")));
  } else if (url.pathname === "/thumb" && req.method === "POST") {
    const chunks = [];
    for await (const c of req) chunks.push(c);
    res.end(thumbnail(Buffer.concat(chunks), 128));
  } else {
    res.statusCode = 404;
    res.end();
  }
}).listen(process.env.PORT || 8080);
