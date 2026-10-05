# Expected: fixture-2-mock-heavy

## Must find

1. **Lines 31-41, the test checks only that eight mocks were called.** No argument and no result is asserted, so it passes if the wrong amount is charged, the wrong order is saved, or the customer is charged before stock is reserved. It tests the wiring, not checkout.
2. **Nothing but the happy path.** No test for stock unavailable, a declined payment, or a save that fails after a successful charge. These are the cases where a checkout loses money, and the review names them.

## Good to find

- `mockPricer.calculate` returns `99.99`: a floating-point price, if amounts are money.
- All collaborators are typed `any`, so a renamed method on a real collaborator would not break this test.
- The test name "processes checkout" says nothing about what should be true afterwards.

## Must not report as a serious problem

- Vitest, `vi.fn()` or `beforeEach` as such. Recommending MSW, a factory library or another runner is wrong: nothing shows the project has them.
- "Magic values" such as `"ch_123"` or `42`.
- The number of constructor parameters of `CheckoutService` (a production-design point, not a test defect; one line at most).

## Shape

The review says plainly that this test would pass on a broken checkout and what to assert instead, using what the file already has: check the arguments to `charge` and `save`, or use simple hand-written fakes and assert on what they hold. It does not rewrite the suite in another style. The source of `CheckoutService` is not in the fixture; a good review says it judged the test without it.
