# TypeScript and JavaScript: evidence without a debugger, and causes that mislead

Read this when the cause is not evident from the code and one run. A match is a place to look, not a diagnosis: confirm it the way `SKILL.md` describes. Use the runner and tools the project already has; flags differ between Node versions and between Jest, Vitest and the built-in runner.

## Getting evidence

- The whole error, including `error.cause` and, for an `AggregateError`, its `errors`.
- A stack that ends in compiled output needs source maps: `node --enable-source-maps`. Longer async stacks: `--stack-trace-limit=50`.
- `node --trace-warnings` and `--trace-uncaught` show where a warning or an uncaught error was raised. An unhandled rejection already ends the process on current Node; test runners intercept it and report it their own way.
- One test, alone: the runner's name filter (`-t`, `--test-name-pattern`), and its serial mode (`--runInBand` in Jest, `--no-file-parallelism` in Vitest) when order or shared state is suspected. A script that runs through `turbo` or `nx` may replay a cached result: call the runner directly when repeating a test.
- A hang: Jest `--detectOpenHandles`, Vitest `--reporter=hanging-process`; anywhere, print `process.getActiveResourcesInfo()` before exit. A timer or socket that was never closed is the usual cause.
- Timing and memory: `performance.now()`, `process.memoryUsage()` before and after a repeated operation, `node --cpu-prof --cpu-prof-dir=<outside the repo>`, `--heap-prof --heap-prof-dir=<outside the repo>`.
- Never start a run with `--inspect-brk`: it waits for a client that will not connect. A `debugger;` statement does nothing without one; remove it before you finish.

## Causes that look like something else

- **A promise nobody awaited:** the function returns before the work is done, and a test passes because its assertion ran after the test ended. An `async` callback given to `forEach` is never awaited.
- **State shared between tests or requests:** module-level variables, a singleton, a mock not restored, fake timers left installed, environment variables set and not reset. Modules are cached between tests in one file and, depending on the runner, across files.
- **Types that are not checked at run time:** an `as` cast, `any`, or a JSON response typed by assertion can hold anything. The compiler's opinion is not evidence about the value: log `typeof` and the value.
- **Ordering assumptions between asynchronous steps** that happen to hold locally: two requests, a timer and a promise, an event emitted before the listener is attached.
- **Dates:** local time differs between a laptop and CI, and `new Date(string)` parses differently by format.
- **A stale build:** the test runs compiled output that was not rebuilt, or a different copy of a dependency than the one in the lock file (`npm ls <name>`).
