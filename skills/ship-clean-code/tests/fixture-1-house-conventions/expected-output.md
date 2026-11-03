# Expected: fixture-1-house-conventions

## Must find

1. **Line 18, `>` should be `>=`.** The last units of an item can never be reserved: with 5 available, a request for 5 returns `None`. Serious (wrong result on an ordinary input).
2. **Lines 27-30, the failed save is swallowed.** If `save_reservation` raises, the function still returns the reservation as if it had succeeded, after stock was already taken off `item.available` (line 19). Stock is lost and the caller believes it holds a reservation that was never stored. Serious.
3. **Lines 12 and 17, the mutable default `options={}`.** One dict is shared by every call that omits `options`, it is written to on line 17, and every reservation stores a reference to it, so all of them show the last actor as `reserved_by`. A caller's own dict is modified too.
4. **Lines 44-45, `get_expired` changes stock.** It is named and documented as a query, but returns stock to `available` each time it is called. Calling it twice returns the stock twice; with `include_released=True` it also returns stock for reservations that were already released. Nothing marks a reservation as handled.
5. **Line 24, `time.time()` instead of the clock.** Against the conventions file; the expiry cannot be fixed in a test, and it is compared on line 43 with a time that does come from the clock (line 38).

## Good to find

- `find_item` can return `None` on line 44 (the item was removed), and line 45 then raises.
- `reserve` returns `None` both for an unknown SKU and for insufficient stock, so a caller cannot tell them apart.
- Zero or negative `quantity` is accepted and a negative one adds stock.
- No audit entry is written when the save fails.

## Must not report as a problem

- `find_item` returning `None` (line 9), or `reserve` returning `None` for an unknown SKU. The conventions file says lookups do this.
- The number of parameters of `reserve`. The conventions file explains it.
- The `include_released` boolean parameter as a "flag argument" to be split into two functions. (Reporting what it does to stock, as in item 4, is right.)
- Reservations being plain dicts rather than a class or dataclass.
- The length of `reserve`, missing type hints, or the literal in `f"reserve:{sku}:{quantity}"`.

## Shape

The two serious defects (items 1 and 2) are at the top and rated above the convention breach (item 5). No category codes. No section of praise added for balance. Suggested fixes keep the project's conventions: `None` for not-found, the clock argument, plain dicts. No claim to have run anything or to have read callers or tests: the fixture has none, and saying so is right.
