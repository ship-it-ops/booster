const { fetchLabel, format } = require("shipkit");

const CARRIER_URLS = { dhl: "https://labels.dhl.example", ups: "https://labels.ups.example" };

function printLabel(carrier, id) {
  const url = CARRIER_URLS[carrier];
  if (!url) throw new Error("unknown carrier");
  return format(fetchLabel(url, id).slice(0, 4096), { width: 40 });
}

module.exports = { printLabel };
