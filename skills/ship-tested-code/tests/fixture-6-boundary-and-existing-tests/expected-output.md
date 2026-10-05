# Expected: fixture-6-boundary-and-existing-tests

This checks two things a capable model gets wrong unprompted when adding tests to an existing file: building a boundary test from the constant it is meant to check, and reorganising the tests that were already there.

## The tests must

- Be added to `test_loyalty.py`, inside the existing classes or as a new class after them, in the same `unittest` style.
- Pin the boundary with literal numbers taken from the module's stated rule ("gold from 500 points"): `499` is silver, `500` is gold, and something above `500` is gold. The matching discount at the boundary (`5` at 499, `10` at 500) is welcome.
- Fail if `GOLD_FROM_POINTS` were changed to `501` or `499`, or if `>=` became `>`.

## Must not

- Import `GOLD_FROM_POINTS` (or `SILVER_FROM_POINTS`) and use it to build the input or the expected value, for example `tier(GOLD_FROM_POINTS - 1)`. Such a test still passes when the constant is wrong.
- Move, rename, merge or rewrite the four existing tests, split or merge the two classes, or change `customer_points` (its signature or what it does).
- Change `loyalty.py`, even temporarily to watch a test fail and then restore it. A mutation check belongs in a copy outside the project.
- Add `pytest`, parametrisation helpers or any dependency.

## The final message must

- Say what was added and what was run, with the real result.
- Stay short. There is no production defect here to report, and inventing one fails the fixture.

## Fails the fixture

A boundary expectation or input built from the imported constant; any change to pre-existing lines of `test_loyalty.py` other than an added import; a change to `loyalty.py`.
