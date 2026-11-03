# Java tests: what is easy to miss

The build (`pom.xml`, `build.gradle`: the JUnit version, Surefire and Failsafe include patterns, the Mockito and assertion libraries present) and the existing tests decide the framework and helpers. Do not add AssertJ, Testcontainers, WireMock, ArchUnit, jqwik, Pitest or anything else the project does not already use, and mention one only when it is the fix for a real finding. Several lines below depend on the JUnit, Mockito and Spring versions: check before reporting.

Places worth a second look, because the test reads as normal and proves nothing. A match is a reason to look again, not a finding: it becomes one when you can say what goes wrong here.

- **A test that never runs.** A method without `@Test`; a JUnit 4 `@Test` in a JUnit 5 build with no vintage engine, or the reverse; a class whose name does not match the Surefire or Gradle include pattern; a private `@Test` method under JUnit 5; a `@ParameterizedTest` whose source supplies no arguments; `@Disabled` / `@Ignore` with no reason.
- **An assertion that is not one.** AssertJ's `assertThat(x)` with no method chained; `assertNotNull(x)` where the value is known; an assertion inside a lambda or thread whose failure never reaches the test.
- **`try { call(); } catch (SomeException e) { }`** with no `fail()` after the call: the test passes when nothing is thrown. `assertThrows` on a block containing several calls, any of which could be the one that throws.
- **Mockito defaults doing the work.** An unstubbed mock returns `null`, `0`, `false` or an empty collection, and the test passes on that default; `verify(mock).method(any())` checks only that a call happened; `when(...)` on the object under test; `@InjectMocks` silently leaving a field `null`; lenient stubs hiding that a stub is never used.
- **Mock returns mock** chains and a mocked value object, where constructing the real one is a line.
- **Static and shared state**: static fields, singletons, a cached Spring context that one test dirties for the next, tests that pass alone and fail together or the reverse, parallel execution over a shared fixture.
- **`@Transactional` on tests** rolling back what production commits, so flush-time constraint failures, lazy-loading outside a session and after-commit hooks never run.
- **A different database in tests** (H2 for PostgreSQL or MySQL) asserting behaviour that differs between them.
- **Time**: `Instant.now()`, `LocalDate.now()` or `new Date()` in the test or the code where the project injects a `Clock`; the default zone or locale; `Thread.sleep` in place of a condition.
- **Order of unordered things**: asserting list equality on `HashMap` / `HashSet` iteration or unordered query results.
- **Weaker or misleading, lowest level**: `assertEquals(actual, expected)` reversed, `assertTrue(a.equals(b))`, `assertEquals` on arrays (compares references) or on `double` without a delta. The test still fails when it should, or fails wrongly; the message misleads.
- **Slice and context tests** (`@SpringBootTest`, `@WebMvcTest`, `@DataJpaTest`) with a `@MockBean` / `@MockitoBean` for the very bean whose behaviour the test claims to check.

Not findings on their own: JUnit 4 in a JUnit 4 project, Hamcrest in place of AssertJ, field injection in tests where the project uses it, `@SpringBootTest` where the project accepts its cost, Mockito at a port the project owns when arguments are verified, test method naming style.
