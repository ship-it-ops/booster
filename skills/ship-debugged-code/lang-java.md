# Java: evidence without a debugger, and causes that mislead

Read this when the cause is not evident from the code and one run. A match is a place to look, not a diagnosis: confirm it the way `SKILL.md` describes. Use the build tool and test framework the project already has (its `mvnw` or `gradlew` wrapper when present); flags differ between JDK versions.

## Getting evidence

- The whole stack trace, to the last `Caused by:`. The last cause is usually the origin; the top is where it was wrapped. Current JDKs say which reference was null in a `NullPointerException` message.
- One test: `./mvnw -Dtest=ClassName#method test` or `./gradlew test --tests 'ClassName.method'`. In a multi-module Maven build add `-pl <module>`. Gradle skips a test task whose inputs have not changed: when repeating a run, add `--rerun` (7.6 or later) or `cleanTest`. Read the report files when the console output is truncated.
- A hang or deadlock: `jcmd <pid> Thread.print` (or `jstack <pid>`) on a local process you started prints every thread's stack and reports deadlocks.
- Timing and memory: `System.nanoTime()` around a section; Java Flight Recorder with `-XX:StartFlightRecording=duration=30s,filename=<outside the repo>` or `jcmd <pid> JFR.start`, read with `jfr summary`; `jcmd <pid> GC.class_histogram` before and after a repeated operation. A recording contains environment variables: keep it out of the repository and out of your answer.
- Never start a process with a suspended debug agent (`suspend=y`): it waits for a client that will not connect. Never attach to a process you did not start.

## Causes that look like something else

- **`==` on boxed numbers and strings:** `Integer` values from -128 to 127 are cached, so the comparison works in tests with small numbers and fails with real ones.
- **Visibility between threads:** a field read in a loop on one thread and written on another without `volatile` or a lock; it works with logging added and fails without.
- **Shared mutable state:** a static field, a singleton bean with instance fields, a non-thread-safe object shared between threads, a collection returned by reference and modified by the caller.
- **Test order and shared fixtures:** static state, a database not rolled back, a Spring context cached between test classes with a bean that one test changed.
- **An exception swallowed or replaced:** an empty `catch`, a `finally` that throws or returns, a wrapped exception whose cause was dropped.
- **Time:** `LocalDate.now()` and `LocalDateTime.now()` read the machine's zone, which differs in CI. A `Date` is an instant; only its formatting uses the zone.
- **The classpath:** two versions of a library, or a different one at run time than at compile time (`./mvnw dependency:tree`, `./gradlew dependencies`); a `NoSuchMethodError` almost always means this.
