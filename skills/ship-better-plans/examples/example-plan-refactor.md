---
type: plan
status: active
approval: approved
created: 2026-09-21
updated: 2026-09-22
author: claude-opus-5-5
tags: [refactor, payments, extract-module]
importance: core
plan_format: 2
base: main@b7d02f3
---

# Plan: extract payment logic out of OrderService

<!-- Example of form and level of detail for a refactor planned in ultra mode. Do not reuse its decisions or task breakdown. It passes `lint_plan.py --no-paths` (the repository it describes is fictional). Note the strictly sequential order, the first task settling the plan's riskiest assumption, and the sections marked N/A with a reason. -->

## Summary
Move the payment-provider calls out of `OrderService` into a `PaymentGateway` module with a typed interface, without changing behaviour. The work is a strangler extraction: pin current behaviour with characterization tests first, then move one operation at a time, each step behind green tests. The biggest risk is behaviour that no test covers, which is why the first task closes that gap before anything moves. Done when `OrderService` no longer imports the provider SDK and the full suite passes with no test edited.

## Context
- **Problem:** `OrderService` (1,800 lines) mixes order state with payment-provider calls, so a change to one can break the other.
- **Why now:** three of the last five payment bugs were regressions caused by unrelated order changes.
- **Request:** "Pull the payment code out of OrderService into its own module. No behaviour changes."

## Success criteria
- SC-1: `OrderService` depends only on a `PaymentGateway` interface; the provider SDK is imported in one adapter file. (stated)
- SC-2: behaviour is unchanged: the existing suite and the new characterization tests pass before and after every step, with no test edited. (stated)

## Non-goals
- Changing the payment provider or its SDK version.
- Touching the database schema.
- Fixing known payment bugs (tracked separately; the tests pin today's behaviour, bugs included).

## Constraints
- Zero behaviour change.
- Every step must be revertable on its own.

## Facts and assumptions
- F-1: all provider calls go through four private methods of `OrderService` (`chargeCard`, `refundCharge`, `voidAuthorization`, `fetchPaymentStatus`), lines 1204 to 1398 — `src/orders/OrderService.ts:1204`
- F-2: nothing outside `OrderService` calls those four methods — ran: `grep -rnE "chargeCard|refundCharge|voidAuthorization|fetchPaymentStatus" src` → matches only in `src/orders/OrderService.ts`
- F-3: `OrderService` is constructed by the DI container in one place — `src/container.ts:88`
- F-4: the provider SDK is imported only in `OrderService` — `src/orders/OrderService.ts:7`
- F-5: the payment methods are 61% covered, and refund after partial capture has no test — ran: `npm test -- --coverage` → 388 passed; uncovered lines listed for 1204–1398
- A-1: characterization tests can pin the untested paths using the provider's recorded-response sandbox in `test/support/providerSandbox.ts` — if wrong: the untested paths cannot be moved safely — settled by: T1 (spike), which stops for the user if any path cannot be pinned

## Approach
| Option | Meets the success criteria? | Effort | Main risk | Reversibility | Verdict |
|--------|-----------------------------|--------|-----------|---------------|---------|
| A. Strangler extraction, one operation per step | Yes | M | Untested behaviour (F-5) | Each step reverts alone | chosen |
| B. Write `PaymentGateway` fresh and switch over in one change | SC-1 yes; SC-2 cannot be shown step by step | M | One large change with no safe midpoint | All or nothing | rejected because a failure cannot be traced to a single move |

- **Chosen:** A — **deciding factor:** SC-2 has to hold after every step, and only A gives a green checkpoint between steps.
- **Builds on:** the DI registration pattern in `src/container.ts` and the recorded-response helpers in `test/support/providerSandbox.ts`.

## Risks and rollback
| Risk | Why it matters | Handled by | How we would notice |
|------|----------------|------------|---------------------|
| A moved method behaves differently on an untested path | A silent payment regression | T1 characterization tests | T1's tests fail in the step that caused it |
| Hidden coupling: a payment method reads order state mid-flow | The adapter cannot be a straight move | T2 passes that state as explicit arguments | Compile errors in T2 |

- **Rollback:** the executor commits each task separately; revert the step that failed. Nothing changes at runtime, so no flag is needed.
- **Migration:** N/A — no data, state or schema changes.

## Specification

### Requirements
- FR-1: characterization tests pin the current behaviour of charge, refund, void and status, including refund after partial capture, provider timeout and reuse of an idempotency key (SC-2)
- FR-2: a `PaymentGateway` interface with `charge`, `refund`, `void` and `status`, typed inputs, outputs and errors, and a `ProviderPaymentGateway` adapter that is the only importer of the provider SDK (SC-1)
- FR-3: `OrderService` receives a `PaymentGateway` through its constructor and calls it for all four operations (SC-1)
- FR-4: the four private payment methods and the SDK import are removed from `OrderService` (SC-1)

### Acceptance criteria
- AC-1 (FR-1): the characterization suite passes against the unmodified `OrderService`, and the coverage report lists no uncovered line between 1204 and 1398 of `src/orders/OrderService.ts` — verify: `npm test -- test/characterization/payments.test.ts --coverage`
- AC-2 (FR-2): the adapter passes the same recorded-response cases as the characterization suite — verify: `npm test -- src/payments/ProviderPaymentGateway.test.ts`
- AC-3 (FR-3, SC-2): after each move the full suite passes and no existing test file has changed — verify: `npm test` passes and `git diff --name-only main -- test "src/**/*.test.ts"` lists only the two test files this plan adds (`test/characterization/payments.test.ts` and `src/payments/ProviderPaymentGateway.test.ts`)
- AC-4 (FR-4): the SDK is imported by exactly one file — verify: `grep -rl "from '@provider/sdk'" src | wc -l` prints 1

### Non-functional targets
N/A — a behaviour-preserving refactor; performance, security and observability are unchanged by design, and AC-3 is the check that nothing moved.

### Interfaces and data shapes
- `interface PaymentGateway { charge(input: ChargeInput): Promise<ChargeResult>; refund(input: RefundInput): Promise<RefundResult>; void(authorizationId: string): Promise<void>; status(paymentId: string): Promise<PaymentStatus> }` in `src/payments/PaymentGateway.ts`.
- `ChargeInput { orderId, amountMinor, currency, paymentMethodId, idempotencyKey }` → `ChargeResult { paymentId, authorizationId, capturedMinor }`. `RefundInput { paymentId, amountMinor, idempotencyKey }` → `RefundResult { refundId, refundedMinor }`. `PaymentStatus` is the existing union in `src/orders/types.ts`.
- Errors: `PaymentDeclinedError`, `PaymentTimeoutError`, `PaymentProviderError`, each wrapping the provider's error code. `OrderService` already throws these today, so callers see no change.

### Edge cases
| Case | Expected behaviour | Covered by |
|------|--------------------|------------|
| Refund after partial capture | Same amounts and provider calls as today | AC-1 |
| Provider timeout during charge | Same `PaymentTimeoutError` and no order state change | AC-1 |
| Idempotency key reused | Same single charge as today | AC-1 |
| Concurrent refund and void on one payment | Out of scope because today's behaviour is a known bug tracked separately; the tests pin it as it is | AC-1 |

## Verification
- **Setup:** `npm ci`. The provider sandbox replays recorded responses, so no network or credentials are needed.
- **Commands:** build `npm run build` · test `npm test` · lint `npm run lint` — defined in `package.json`
- **Baseline:** `npm test -- --coverage` → 388 passed before this work (F-5).
- **Final check:** SC-1 by AC-4 and by `OrderService`'s constructor signature. SC-2 by AC-3 on the final commit, with `test/characterization/payments.test.ts` unchanged since T1.

## Tasks

### Conventions for every task
- Run `npm ci` first in a fresh checkout.
- No behaviour changes. If a test has to be edited to pass, stop and report instead.
- `npm run build` and `npm test` pass before a task is reported done.

### T1 — Characterization tests for the payment paths
- **Depends on:** none
- **Covers:** FR-1, AC-1
- **Files:** `test/characterization/payments.test.ts` (new)
- **Do:** Pin what `OrderService` does today for charge, refund, void and status, driving it through its public methods with the recorded-response helpers in `test/support/providerSandbox.ts`. Cover the happy paths plus refund after partial capture, provider timeout, and reuse of an idempotency key. Assert on the provider calls made and on the resulting order state. Do not change `OrderService`. This task is also a spike: if a path cannot be pinned with the sandbox, stop and report which one, and the plan does not continue until the user has decided what to do about it.
- **Verify:** `npm test -- test/characterization/payments.test.ts --coverage` → passes, and the report lists no uncovered line between 1204 and 1398 of `src/orders/OrderService.ts`
- **Kind:** test · **Size:** M · **Reversibility:** safe

### T2 — PaymentGateway interface and provider adapter
- **Depends on:** T1
- **Covers:** FR-2, AC-2
- **Files:** `src/payments/PaymentGateway.ts` (new), `src/payments/ProviderPaymentGateway.ts` (new), `src/payments/ProviderPaymentGateway.test.ts` (new), `src/container.ts` (modify)
- **Do:** In `src/payments/PaymentGateway.ts` define `interface PaymentGateway` with `charge(input: ChargeInput): Promise<ChargeResult>`, `refund(input: RefundInput): Promise<RefundResult>`, `void(authorizationId: string): Promise<void>` and `status(paymentId: string): Promise<PaymentStatus>`, where `ChargeInput` is `{ orderId, amountMinor, currency, paymentMethodId, idempotencyKey }`, `ChargeResult` is `{ paymentId, authorizationId, capturedMinor }`, `RefundInput` is `{ paymentId, amountMinor, idempotencyKey }`, `RefundResult` is `{ refundId, refundedMinor }`, and `PaymentStatus` is the existing union in `src/orders/types.ts`. Implement `ProviderPaymentGateway` by copying the bodies of `chargeCard`, `refundCharge`, `voidAuthorization` and `fetchPaymentStatus` from `src/orders/OrderService.ts` (lines 1204 to 1398), turning the order state they read into the explicit input fields above and throwing the same `PaymentDeclinedError`, `PaymentTimeoutError` and `PaymentProviderError` they throw today. Register the adapter in `src/container.ts` following the registration pattern used there. Test the adapter with the recorded responses in `test/support/providerSandbox.ts`. Do not modify `OrderService` in this task.
- **Verify:** `npm test -- src/payments/ProviderPaymentGateway.test.ts` → passes
- **Kind:** code · **Size:** M · **Reversibility:** safe

### T3 — Route charge through the gateway
- **Depends on:** T2
- **Covers:** FR-3, AC-3
- **Files:** `src/orders/OrderService.ts` (modify), `src/container.ts` (modify)
- **Do:** Add a `PaymentGateway` constructor parameter (from `src/payments/PaymentGateway.ts`) to `OrderService` and pass the registered adapter from `src/container.ts`. Replace the call to the private `chargeCard` with `gateway.charge`, mapping the arguments to `ChargeInput`. Leave `chargeCard` in place, unused; a later task removes it. Edit no test.
- **Verify:** `npm test` → passes; `git diff --name-only main -- test "src/**/*.test.ts"` → lists only the two test files this plan adds
- **Kind:** code · **Size:** S · **Reversibility:** safe

### T4 — Route refund and void through the gateway
- **Depends on:** T3
- **Covers:** FR-3, AC-3
- **Files:** `src/orders/OrderService.ts` (modify)
- **Do:** In `OrderService`, replace the calls to the private `refundCharge` and `voidAuthorization` with `gateway.refund` and `gateway.void` on the `PaymentGateway` the constructor already receives. Leave the private methods in place, unused; a later task removes them. Edit no test.
- **Verify:** `npm test` → passes; `git diff --name-only main -- test "src/**/*.test.ts"` → lists only the two test files this plan adds
- **Kind:** code · **Size:** S · **Reversibility:** safe

### T5 — Route status through the gateway
- **Depends on:** T4
- **Covers:** FR-3, AC-3
- **Files:** `src/orders/OrderService.ts` (modify)
- **Do:** In `OrderService`, replace the call to the private `fetchPaymentStatus` with `gateway.status` on the `PaymentGateway` the constructor already receives. Leave the private method in place, unused; the next task removes it. Edit no test.
- **Verify:** `npm test` → passes; `git diff --name-only main -- test "src/**/*.test.ts"` → lists only the two test files this plan adds
- **Kind:** code · **Size:** S · **Reversibility:** safe

### T6 — Remove the old payment methods and the SDK import
- **Depends on:** T5
- **Covers:** FR-4, AC-4
- **Files:** `src/orders/OrderService.ts` (modify)
- **Do:** Delete the now-unused private methods `chargeCard`, `refundCharge`, `voidAuthorization` and `fetchPaymentStatus` and the `@provider/sdk` import from `OrderService`. Nothing else calls them. Edit no test.
- **Verify:** `npm run build` → passes; `npm test` → passes; `grep -rl "from '@provider/sdk'" src | wc -l` → prints 1
- **Kind:** code · **Size:** S · **Reversibility:** safe

### Execution order
- Sequential: T1 → T2 → T3 → T4 → T5 → T6

No parallel work: T3 to T6 all edit `OrderService.ts`, and each step needs the one before it to be green.

## Open questions
None. The one unknown (A-1) is settled by T1 before anything moves.

## Audit
Ultra. Reviewers: executor, grounding, adversary, scope, tests. Two review rounds (the second confirmed nothing new), then one recheck of the revised plan: all findings resolved, nothing new.

- [blocker, adversary] the first draft moved code before pinning behaviour, with 61% coverage (F-5) → fixed: T1 added ahead of everything, with a coverage bar in AC-1.
- [major, tests] "tests pass" was the only check, and a moved method could pass by having its test edited → fixed: AC-3 and the conventions forbid editing tests, and each Verify checks that none changed.
- [major, executor] T3 changed `OrderService`'s constructor without updating `src/container.ts`, so the build would fail between tasks → fixed: T3 now owns that edit.
- [major, executor] T2's card pointed at "the interface section", which a task agent does not receive → fixed: the interface is written out in the card.
- [minor, scope] dropped a proposed `PaymentGatewayFactory`; one adapter needs no factory.
- [dropped by verification] "idempotency keys are not handled": refuted, the existing code passes them through and AC-1 pins that.

## Status
Approved by the user on 2026-09-22. Next: `/ship-execute docs/agent/plans/extract-payment-logic-out-of-orderservice.md solo`. Nothing blocked.

## Related
- `[orderservice-payment-regressions](../investigations/orderservice-payment-regressions.md)` — the incidents that motivated this
