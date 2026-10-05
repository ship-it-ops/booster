# Expected: fixture-1-green-and-wrong

`input.py` is the test file (save it as `test_shipping.py` next to `shipping.py`). All six tests pass.

## Must find

1. **Lines 12-13, `test_exactly_at_threshold_pays_shipping` pins a defect.** The docstring on `shipping_cents` says shipping is free when the subtotal is at least the threshold; the code uses `>`, and this test expects a charge at exactly 5000. The review says the production code is wrong (`>` should be `>=`) and that the test should expect `0`.
2. **Lines 19-23, `test_unknown_zone` cannot fail.** If no exception is raised, nothing fails the test. It needs `assertRaises`.
3. **Lines 25-28, `test_free_shipping` cannot fail.** `cost >= 0` is true for every result; it should expect `0`.
4. **Lines 15-17, `test_eu_costs_more` recomputes the answer** with the production constants and formula, so a wrong formula or multiplier passes. The expected value should be the literal `1718`. This also breaks the conventions file ("written out as numbers").
5. **Lines 5, 27 and 30-31, shared state and order.** `RESULTS` is a module-level list filled by one test and counted by another; `test_results_recorded` fails when run alone and tests nothing about shipping.

## Good to find

- No test for `"world"`, for a subtotal just above the threshold being free in a non-domestic zone, or for weight `0`.
- Free shipping applies to every zone; whether that is intended is a question for the author.

## Must not report as a problem

- `unittest` instead of `pytest`, or any suggestion to add a dependency.
- Test naming style, missing assertion messages, the absence of a factory or of parametrisation.
- `test_domestic_parcel` (lines 9-10): it is sound.

## Shape

Leads with the tests that give false confidence (items 1 to 3) and says the answer to "can we trust these" is no. Separates the production defect from the test defects. No category codes, no praise section. No claim to have run anything unless it was run; no change to any file.
