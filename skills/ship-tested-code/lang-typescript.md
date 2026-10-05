# TypeScript and JavaScript tests: what is easy to miss

The runner and its configuration (`jest.config.*`, `vitest.config.*`, `playwright.config.*`, the `test` script in `package.json`), the setup files and the existing tests decide the framework and helpers. Do not add MSW, Testing Library, `fast-check`, fake-timer libraries or anything else the project does not already use, and mention one only when it is the fix for a real finding. Runner behaviour differs between Jest and Vitest and between versions: check before reporting.

Places worth a second look, because the test reads as normal and proves nothing. A match is a reason to look again, not a finding: it becomes one when you can say what goes wrong here.

- **A promise the test does not wait for.** `expect(promise).resolves...` or `.rejects...` without `await` or `return`; an `async` callback inside `forEach`; a `.then` chain not returned. The test ends before the assertion runs and passes. `expect.assertions(n)` or `expect.hasAssertions()` catches it where the project uses them.
- **`expect(value)` with no matcher**, and a matcher referenced without calling it (`.toBeTruthy` with no parentheses): nothing is asserted.
- **`try { await call(); } catch (e) { expect(e)... }`** with nothing failing the test when no error is thrown.
- **Matchers weaker than they read.** `toBeTruthy` / `toBeDefined` on an object that always exists; `toEqual` ignoring `undefined` properties and class identity where `toStrictEqual` was meant; `toHaveBeenCalled()` with no arguments checked; `toMatchObject` with an empty or near-empty object.
- **`it.only`, `describe.only`, `fit`, `it.skip`, `xit`, `it.todo`** left in: the rest of the file silently stops running, or the test never ran.
- **Module mocks.** `jest.mock` / `vi.mock` is hoisted above imports and replaces the whole module, sometimes including the function under test; an automock returns `undefined` from everything and the test passes on that default; mocks, spies and `mockReturnValue` not reset between tests, so one test's stub answers the next.
- **Fake timers** enabled and never restored, or real time awaited while timers are faked (the test hangs or passes without the callback having run); `setTimeout` in a test in place of a condition.
- **Snapshots** nobody could tell from wrong: large rendered trees, snapshots regenerated with `-u` in the same change as a behaviour change, obsolete snapshots, snapshots containing dates, ids or random values.
- **Testing Library queries used for absence.** `getBy*` throws before the assertion (use `queryBy*` for "not there"); `findBy*` not awaited; side effects inside `waitFor`.
- **Module-level state** shared across tests in one file (a singleton store, a cache, an in-memory database), and across files when the runner reuses the module registry.
- **`done` callbacks**: `done` never called on the failure path, or an assertion throwing inside a callback after the test has already finished.
- **Type-only confidence.** A test that compiles because of `as any` or `@ts-ignore` on the value under test and asserts nothing about its shape at run time.
- **Time and locale**: `new Date()` in the test or the code, `toLocaleString` output asserted as a literal, time-zone-dependent date arithmetic.

Not findings on their own: Jest in place of Vitest or the reverse, `fireEvent` in a project that uses it throughout, `jest.fn()` stubs at a module boundary when arguments are asserted, enzyme-era tests left as they are, `describe` nesting depth, test file location.
