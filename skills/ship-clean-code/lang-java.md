# Java: what is easy to miss

The language level set in the build (`maven.compiler.release`, `sourceCompatibility`, the toolchain), the frameworks in use, and the project's Checkstyle, Error Prone or SpotBugs configuration decide what is available and what is convention. Check them before suggesting records, sealed types, pattern matching, `var`, virtual threads or `Optional` conventions.

Places worth a second look, because the defect reads as normal code. A match is a reason to look again, not a finding: it becomes one when you can say what goes wrong here.

- **Resources not in try-with-resources**: connections, statements, result sets, streams, `Files.lines` and `Files.list`. They leak on the exception path.
- **`catch (Exception e)` that continues**, `e.printStackTrace()` as the handling, and `catch (InterruptedException e)` that neither restores the interrupt flag nor propagates. Wrapping an exception without passing the cause loses the stack that matters.
- **Exceptions thrown from `finally`, or `return` in `finally`**, which discard the original exception.
- **Unboxing `null`.** An `Integer`, `Long` or `Boolean` from a map, a database row or a JSON field assigned to a primitive or used in arithmetic or a condition.
- **`==` on boxed values and strings.** Works for small integers and interned strings, then fails in production.
- **`equals` without `hashCode`** (or the reverse), and either one depending on mutable fields of an object used as a map key or set member. `equals` in a class hierarchy: `instanceof` and `getClass()` each have a failure mode; note which one the project's value types use, and prefer records or final classes for value types where the language level allows.
- **Returned internal collections and arrays** that callers can mutate, and constructor arguments stored without a copy. `List.of`, `Map.of` and `Collectors.toList()` differ in mutability and in accepting `null`.
- **Modifying a collection while iterating it**; streams with side effects in `map` or `peek`; a stream reused after a terminal operation; parallel streams over shared mutable state.
- **Shared mutable state without a visible discipline**: a non-final static field, a singleton or injected bean with mutable fields, check-then-act on a `ConcurrentHashMap` (`containsKey` then `put`) where `computeIfAbsent` or `merge` is needed, `SimpleDateFormat` and other non-thread-safe classes in fields, double-checked locking without `volatile`.
- **Tasks submitted to an executor whose `Future` is dropped**: the exception is never seen. A `CompletableFuture` chain whose result nobody returns, joins or handles; blocking calls on the common pool; on JDK 21 to 23, blocking inside `synchronized` on a virtual thread, which pins the carrier.
- **`Optional.get()` without a check**, and an `Optional` that can itself be `null`.
- **`BigDecimal`**: constructed from a `double`, compared with `equals` (which is scale-sensitive) where `compareTo` was meant; `double` or `float` for money.
- **Time**: `Date`, `Calendar` and `LocalDateTime` used for instants that cross time zones; the system default zone or locale used implicitly (`toLowerCase()`, `String.format`, `LocalDate.now()`).
- **Transaction and proxy boundaries in Spring and similar**: a `@Transactional` or `@Async` method called from the same class, a checked exception that does not roll back, a lazy association read after the session has closed.
- **Switches over enums or sealed types** with a default branch that hides a new case.

Not findings on their own: field versus constructor injection where the project is consistent, a class with several collaborators, checked versus unchecked exceptions where the project has a policy, getters and setters on a data holder, `null` returns in a code base that uses them consistently, `Optional` as a field or parameter where the project does that.
