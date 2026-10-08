const test = require("node:test");
const assert = require("node:assert");

test("labels: unknown carrier is rejected", () => {
  const { printLabel } = require("../src/labels");
  assert.throws(() => printLabel("nope", "1"));
});
