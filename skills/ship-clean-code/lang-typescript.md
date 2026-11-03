# TypeScript and JavaScript: what is easy to miss

`tsconfig.json` (above all `strict`, `strictNullChecks`, `noUncheckedIndexedAccess`, `target`), the ESLint and formatter configuration, and the framework in use decide what is available and what is convention. Check them before suggesting syntax or flagging style. In plain JavaScript, the type-related points become "what does this value turn out to be at run time".

Places worth a second look, because the defect reads as normal code. A match is a reason to look again, not a finding: it becomes one when you can say what goes wrong here.

- **Async callbacks nobody awaits.** `array.forEach(async ...)` returns before the work is done; `map(async ...)` without `Promise.all` yields promises, not values; an `async` function passed where a synchronous callback is expected (event handlers, `filter`, `sort`) is not awaited and its rejection is unhandled.
- **Floating promises**: a call to an async function with no `await`, `return` or `.catch`. The error vanishes and ordering is lost.
- **How concurrent work is combined.** `Promise.all` where one failure must not discard the other results (`allSettled`); `Promise.all` over a list whose size the caller controls, with nothing bounding it; sequential `await` in a loop only where the caller has a deadline and the calls are independent.
- **`fetch` treated as failing on HTTP errors.** It resolves on 404 and 500; `response.ok` has to be checked. `response.json()` on an error body then throws something unrelated.
- **`||` for defaults** when `0`, `""` or `false` are valid: use `??`. The same for `if (value)` used as a presence check.
- **`any`, `as` and `!`** that silence the compiler at exactly the point where data enters from outside (JSON, `localStorage`, query strings, another service). The type then claims something nobody checked. `unknown` plus a check is the alternative. An `as` on a literal or a test fixture is not the same problem.
- **`==` across types**, where coercion changes the answer. Between two values known to be the same type it is style, and the linter's business.
- **`catch (e)` used as if `e` were an `Error`**, and errors re-thrown as new errors without `cause`.
- **Shallow copies treated as deep.** Spread and `Object.assign` share nested objects; state "copies" in reducers and React state then mutate the original.
- **`sort()`, `reverse()` and `splice()` mutate in place**; default `sort()` compares as strings.
- **Stale closures in React**: an effect or callback that reads state or props missing from its dependency list; an effect that subscribes, sets a timer or starts a request with no clean-up; derived state copied into `useState` that then drifts from its source.
- **Listeners, timers and subscriptions** added with nothing removing them.
- **Parsing that accepts more than it should.** `parseInt("12abc")` is `12` and `map(parseInt)` passes the index as the radix; `Number("")` is `0`; `new Date("2026-03-01")` is UTC while `new Date("2026-03-01T00:00")` is local, and other formats vary by engine; months count from zero.
- **Object keys from untrusted input** used to index a plain object (`obj[key]` reaching `__proto__` or `constructor`); `for...in` over an object that has inherited keys.
- **Exhaustiveness.** A `switch` over a union with no `never` check silently ignores a new variant.

Not findings on their own: `null` versus `undefined` where the project is consistent, a missing explicit return type on an internal function, `function` versus arrow, a component longer than a screen that reads clearly, barrel files, import order.
