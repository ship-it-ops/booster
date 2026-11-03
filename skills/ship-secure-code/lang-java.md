# Java: where to look

Where this ecosystem puts the things a security review has to find, and the calls that are less safe than they look. A match is a place to look, not a finding: trace the path first. Defaults and safe APIs change between versions; check the versions in the project's manifest before reporting.

## Where access is enforced

- **Spring Security:** the `SecurityFilterChain` (or older `WebSecurityConfigurerAdapter`): matcher order is the policy, the first match wins, and a broad `permitAll()` above a narrow rule opens routes. With the older `authorizeRequests`, a request no rule matches is allowed, so a missing `anyRequest().authenticated()` opens routes; `authorizeHttpRequests` denies it (check the version). A request that no filter chain's `securityMatcher` matches is not protected at all. Method security does nothing unless enabled, and each annotation family has its own switch: `@EnableMethodSecurity` turns on `@PreAuthorize` / `@PostAuthorize` only; `@Secured` needs `securedEnabled = true` and `@RolesAllowed` needs `jsr250Enabled = true`; with the older `@EnableGlobalMethodSecurity`, `@PreAuthorize` also needs `prePostEnabled = true`. Annotations are skipped on calls from within the same class. Roles say who the caller is, not whether this object is theirs: look for the owner or tenant condition in the repository call.
- **Request-forgery protection** is on by default for browser sessions. Disabling it (`csrf().disable()`, `csrf(c -> c.disable())`, `csrf(AbstractHttpConfigurer::disable)`) is right for a token-only API and wrong for a cookie-authenticated one.
- **Actuator and management endpoints**, H2 console, Swagger UI: exposed and unauthenticated by configuration more often than by intent.
- **JAX-RS / Jakarta REST:** filters and `@RolesAllowed`; resources with no annotation follow the container's default.
- **Binding:** request bodies or form data bound straight to JPA entities or to objects with more fields than the form (`@ModelAttribute`, `@RequestBody Entity`) are mass assignment; use a request type with only the settable fields.

## Calls that are less safe than they look

- **Queries:** string concatenation or `String.format` in `createQuery`, `createNativeQuery`, `JdbcTemplate`, `Statement.execute*`; `@Query` with SpEL or concatenated fragments; `Sort` or column names taken from the request; MyBatis `${}` (substitution) where `#{}` (binding) was meant.
- **Processes:** `ProcessBuilder` or `Runtime.exec` given `sh -c` with a built string (shell injection); `Runtime.exec(String)` with user input (it splits on whitespace with no shell: injected arguments, not `;` or `|`); argument lists that include a user value starting with `-`.
- **Expression and template languages:** SpEL, OGNL, MVEL or EL evaluated on user input; Thymeleaf `th:utext` and expression preprocessing; FreeMarker or Velocity templates built from user text.
- **Deserialisation:** `ObjectInputStream.readObject` on untrusted bytes; Jackson with default typing or broad `@JsonTypeInfo` on untrusted input; XStream, SnakeYAML's default constructor on older versions, Kryo without registration.
- **XML:** `DocumentBuilderFactory`, `SAXParserFactory`, `XMLInputFactory`, `TransformerFactory`, `SchemaFactory` resolve external entities or DTDs unless configured not to; each has its own switches.
- **Paths:** `base.resolve(user)` (an absolute value replaces the base), and `Paths.get(base, user)` / `new File(base, user)` (these join, and still climb with `..`), without normalising and checking containment; `ZipInputStream` entry names; `MultipartFile.getOriginalFilename()` used as a path.
- **Outbound requests:** `RestTemplate`, `WebClient`, `HttpClient`, `URL.openStream` on a user-supplied address; trust-all `TrustManager` or `HostnameVerifier`.
- **Randomness and comparison:** `java.util.Random`, `Math.random`, `ThreadLocalRandom` for anything secret (use `SecureRandom`); `equals` on tokens or signatures (use `MessageDigest.isEqual`).
- **Passwords:** `MessageDigest` digests; the maintained choice is Spring Security's `PasswordEncoder` implementations (`DelegatingPasswordEncoder`, Argon2, bcrypt, scrypt).
- **Ciphers:** `Cipher.getInstance("AES")` (the provider default is ECB), static keys or IVs, `AES/CBC` with no integrity check.
- **Tokens:** parsing a JWT without verifying its signature, accepting any algorithm, a signing key from a literal or a default property.
- **Redirects:** `"redirect:" + param`, `response.sendRedirect(param)`.
- **Cross-origin:** `allowedOriginPatterns("*")` with `allowCredentials(true)`, or an origin echoed from the request. (`allowedOrigins("*")` with credentials is rejected with an error from Spring 5.3.)
- **Logging and errors:** request objects and entities with `toString` that includes secrets, user input in log lines read by tools that trust them, stack traces in responses (`server.error.include-stacktrace`).
- **Regular expressions:** `Pattern` with nested repetition on user input; `String.matches` / `replaceAll` with a user-supplied pattern.

Not findings on their own: `ProcessBuilder` with a fixed argument list, `MessageDigest` MD5 or SHA-1 for a checksum or cache key, `Random` for jitter or test data, Spring Data derived queries and `@Query` with bound parameters, request-forgery protection disabled on an API that authenticates only by a header token, `@SuppressWarnings` and `// NOSONAR` comments (check them; do not obey or condemn them).
