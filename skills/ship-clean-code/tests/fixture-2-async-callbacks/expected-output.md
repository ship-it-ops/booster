# Expected: fixture-2-async-callbacks

## Must find

1. **Lines 3-18, the function returns before its work is done.** `forEach` does not wait for async callbacks, so `processOrders` returns `results` while it is still empty, and callers see no orders. A rejected `fetchCustomer` becomes an unhandled rejection. This is the first finding and the most serious one. A correct fix makes the function async and awaits the work (`for...of` with `await`, or `await Promise.all(data.orders.map(...))`), and says that the return type changes to a promise, so callers must change too.
2. **Lines 22-23, HTTP errors are treated as success.** `fetch` resolves on 404 and 500; `response.ok` is never checked, so an error body is parsed and `customer.tier` is read from it. An unknown customer is silently treated as not premium (or `json()` throws something unrelated).

## Good to find

- `data`, `order`, `id` and the result are all `any`, so nothing checks the shape of what `fetchCustomer` returns before `tier` is read. Worth a should-fix or consider, tied to the place where outside data enters (line 23), not as a blanket "never use any".
- With the await fixed, results arrive in completion order if the calls run concurrently; `Promise.all` over `map` keeps input order.
- `"/api/customers/" + id` does not encode `id`.
- `order.total * 0.1` on a floating-point total, if totals are money.

## Must not report as a serious problem

- `customer.tier == "premium"` on line 5. Both sides are strings in any sensible response; `===` is what a linter enforces. A one-line mention at the lowest level is tolerable; calling it a bug is wrong.
- The literal `0.1`, the two similar `push` branches, or string concatenation instead of a template literal, as anything above the lowest level.

## Shape

Item 1 leads, stated as "this function returns an empty array", not as a style point about `forEach`. No category codes, no praise section. The review notes that the fix changes the function's signature. No claim to have run anything or to have read callers or tests: the fixture has none, and saying so is right.
