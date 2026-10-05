# Vulnerability classes: what is easy to miss, and what a fix that works looks like

Read the sections for what the code touches. Each one lists where a competent reviewer still slips, and the difference between a fix that removes the flaw and one that only moves it. Nothing here is a finding by itself: a finding is a traced path (see `SKILL.md`). Framework behaviour changes between versions; check the version in use before relying on a default.

## Authorization and object access

- The check that is missing is rarely on the main route. Look at the variants: bulk, export, search, count, "copy", "move", attachments, the admin and internal versions, the GraphQL resolver beside the REST handler, the websocket or queue consumer that does the same thing.
- Loading a record by id and then checking ownership is fine; loading by id and never checking is the flaw. A filter on tenant in the query is stronger than a check after loading, because it cannot be forgotten on one branch.
- "404 or 403" matters less than consistency: differing answers for "exists but not yours" and "does not exist" let a caller enumerate ids.
- Mass assignment: a request body copied onto a model or into an update statement lets the caller set fields the form never showed (role, owner, tenant, verified, price). The fix is an explicit list of fields a caller may set, per operation.
- A check in the UI, in a client, or in an earlier request of a multi-step flow is not a check.
- **Fix:** enforce in one declared place per route (the project's guard), scoped to the object; add the filter to the query; deny when the guard is absent.

## Injection into a query

- Bound parameters protect values only. Table and column names, sort order and direction, and operators cannot be bound: they need an allowlist mapped to fixed strings. Limits and offsets can usually be bound; cast them to an integer and cap them.
- An ORM does not help where raw fragments are passed: `raw`, `extra`, `text`, `whereRaw`, `literal`, string-built JPQL or HQL, a native query, a query builder given a user-supplied column or operator.
- Document stores: a request body passed as a filter lets the caller send operators (`{"$ne": null}`, `$where`). Cast to the expected scalar type first.
- `LIKE` patterns: `%` and `_` in user input are not injection, but they change what matches; escape them when the match is a security decision.
- Second order: a value stored safely and later concatenated into a query elsewhere.
- **Fix:** bind every value; map every identifier through an allowlist; never "escape" by hand.

## Commands and processes

- A shell is the flaw: `shell=True`, `system`, `popen`, Node's `child_process.exec`, a single command string handed to `sh -c`. The fix is an argument list with a fixed program. (A call that splits a string into arguments without a shell, such as Java's `Runtime.exec(String)`, allows injected arguments, not shell metacharacters.)
- An argument list still allows option injection: a user-supplied value beginning with `-` becomes a flag (`--output=`, `-o`, `--upload-pack`). Put `--` before user-supplied operands where the program supports it, and validate the value's form.
- Programs that interpret their input (`tar`, `git`, `curl`, `ffmpeg`, `convert`, `pandoc`, `ssh`) have options and input formats that read or write other files or reach the network. Fixing the shell does not fix those.
- Environment variables and the working directory passed to a child process are inputs too.

## Server-side request forgery

- Any feature that fetches an address the user supplies: imports, webhooks, previews, avatars from a URL, PDF or image renderers that load remote resources, XML with external entities.
- A denylist of strings does not work. Loopback and internal addresses have many spellings (`0.0.0.0`, `[::1]`, decimal and octal forms, IPv4-mapped IPv6), a hostname can resolve to an internal address, a public address can redirect to an internal one, and the name can resolve differently between the check and the request.
- The cloud metadata address (`169.254.169.254` and its IPv6 and hostname forms) is the usual target; so are admin ports of neighbouring services.
- Non-HTTP schemes (`file:`, `gopher:`, `ftp:`) if the client supports them.
- **Fix that works:** an allowlist of hosts where the feature allows it. Otherwise: accept only `http` and `https`; resolve the name, reject private, loopback, link-local and metadata ranges, and connect to the address you checked (through the client's resolver or connection hook, not by rewriting the URL to the address, which breaks certificate checking); do not follow redirects, or re-check each hop; limit the response size and time; do not return the raw response to the caller unless that is the feature. Sending such requests through an egress proxy that enforces this is stronger than doing it in application code.

## File paths, uploads and archives

- Joining a base directory with user input does not confine it: `..` climbs out, and in several path libraries (Python `os.path.join` and `pathlib`, Node `path.resolve`, Java `Path.resolve`, .NET `Path.Combine`) an absolute second argument replaces the base entirely.
- **Fix:** resolve the final path (following symbolic links) and check it is inside the resolved base, comparing by path component (`is_relative_to`, `commonpath`, `Path.startsWith`) and not by string prefix; or look the file up by an identifier that maps to a stored name.
- Archive extraction can write wherever entry names say (`../../`, absolute paths, symbolic links). Libraries differ: some sanitise names themselves, some need a safe mode switched on, some do neither (see the language notes). Where the code builds destination paths from entry names by hand, validate each resolved destination. Decompressed size and entry count are a separate limit.
- Uploads: the name, the declared type and the extension are attacker-controlled. What matters is where the file is stored (outside any directory that is served or executed), under what name (generated), how it is served back (a fixed or sniff-proof content type, as a download when in doubt), size limits, and who may fetch it afterwards. An upload any signed-in user can read by guessing a name is an authorization flaw.
- Temporary files created with predictable names in shared directories.

## Templates, HTML and the browser

- Server-side template injection is user input in the template's source, not in its variables: a string concatenated or formatted into what is then rendered as a template. It usually leads to code execution.
- Auto-escaping covers HTML text and quoted attributes. It does not make a value safe inside a script block, an event-handler attribute, a `style`, an unquoted attribute, or a URL attribute: `javascript:` and `data:` URLs pass straight through escaping. URL attributes need a scheme allowlist.
- "Safe" markers switch escaping off: `|safe`, `Markup`, `mark_safe`, `dangerouslySetInnerHTML`, `v-html`, `innerHTML`, `bypassSecurityTrust*`, triple braces. Each needs its input to be trusted or sanitised by a maintained sanitiser, not by a regular expression.
- Rendered Markdown and rich text are HTML.
- Request forgery depends on how the application authenticates. A cookie the browser attaches automatically needs a defence; a token the script puts in a header mostly does not. On the session cookie, an explicit `SameSite=Lax` stops cross-site `POST` but not top-level `GET`, so state-changing `GET` stays exposed; `Strict` stops both; neither stops requests from sibling subdomains, and `None` stops nothing. Do not count on the browser default: only Chromium-based browsers treat an unset attribute as Lax, and with a short exception for freshly set cookies; frameworks differ in whether they set it. A session-bound token, or an `Origin` / `Sec-Fetch-Site: same-origin` check, covers these.
- A websocket authenticated by cookie needs an `Origin` check at the handshake.
- Cross-origin sharing: reflecting the request's origin together with credentials is the dangerous configuration; `*` without credentials on public data is not.
- Open redirect: a redirect target taken from the request. Allow relative paths on this site only (and reject `//host` and backslash forms), or map a key to a fixed list.

## Deserialisation and parsers

- Formats that can construct arbitrary objects execute code when fed attacker data: Python `pickle` and `yaml.load` without the safe loader, Java native serialisation and libraries with polymorphic typing enabled, PHP `unserialize`, Ruby `Marshal`, .NET `BinaryFormatter`.
- XML parsers that resolve external entities or DTDs read files and make requests; defaults differ by parser and version.
- **Fix:** a data-only format with a schema; safe loaders; entity resolution off.

## Authentication, sessions and tokens

- Passwords: a password hashing function with a per-password salt and a work factor (Argon2id, scrypt, bcrypt, or PBKDF2 with a high iteration count). A plain or salted fast hash (MD5, SHA-1, SHA-256) is not one. Use the framework's hasher, which also handles upgrading parameters.
- Changing a password scheme has to keep existing users able to sign in: verify with the old scheme and re-hash on next successful login, or wrap the old hash. Never a silent incompatible switch.
- Random values that guard anything (session ids, reset tokens, API keys, invitation codes) come from the cryptographic source (`secrets`, `crypto.randomBytes` / `crypto.getRandomValues`, `SecureRandom`), not from `random`, `Math.random` or a timestamp.
- Reset and invitation flows: the link's host comes from configuration, never from the request's `Host` or forwarded headers; the token expires, is single-use, is tied to one account, is stored hashed, is not returned by the API or written to a log; the request step answers identically for known and unknown accounts; completing a reset ends the account's other sessions where the session mechanism can (where it cannot, as with signed client-side sessions, say so and do not build one unasked); the old password or email is not changed by an unauthenticated step without the token.
- Sessions: a new session identifier at login and at privilege change; cookies `HttpOnly`, `Secure`, and a `SameSite` value chosen on purpose; server-side invalidation at logout where sessions are server-side; with signed client-side sessions, say that they cannot be revoked individually.
- Signed tokens (JWT and similar): verify, do not just decode; pin the accepted algorithms; check expiry, audience and issuer; a secret used for signing must not have a default or be guessable; a long-lived token with no revocation is a design weakness worth stating.
- Comparing a MAC, a signature or a secret against attacker-supplied input with `==` leaks timing; use the constant-time comparison. It matters most where the attacker chooses the message being verified. Looking up a high-entropy random token by its hash is fine.
- Limits on login, reset and verification attempts; uniform errors.

## Secrets and sensitive data

- A default or fallback value for a secret (`os.environ.get("KEY", "dev-secret")`) is a hardcoded secret that takes effect whenever the variable is missing. Fail at start-up instead.
- Secrets in URLs end up in logs, history and referrers.
- Logs: credentials, tokens, session ids, full request bodies, personal data. Error responses: stack traces, queries, internal addresses.
- Endpoints that serialise a whole record return fields nobody meant to expose (password hashes, tokens, internal flags). Serialise an explicit list.
- A secret that was ever committed is compromised; the fix includes rotation.
- When reporting one, give the location and the kind, never the value.

## Cryptography

- Encryption without authentication (CBC or CTR alone, ECB anywhere) lets ciphertext be altered; use an authenticated mode (GCM, ChaCha20-Poly1305) through a maintained library's high-level interface.
- A nonce or IV that repeats under the same key breaks GCM and ChaCha20-Poly1305 completely.
- Certificate or hostname verification switched off (`verify=False`, a trust-all manager, `rejectUnauthorized: false`) makes TLS decorative.
- MD5 and SHA-1 are a problem for signatures, integrity against an attacker and passwords; not for cache keys, ETags or deduplication.

## Logic, state and concurrency

- Check-then-act without atomicity: spend a balance, redeem a code, use a single-use token, claim a unique name. Two requests at once both pass the check. The fix is a conditional update, a unique constraint or a lock in the store, not a second check in code.
- Multi-step flows where the server trusts the client to have done the earlier steps (payment before fulfilment, verification before activation).
- Values the client supplies and the server should compute or look up: price, discount, role, user id, tenant id.
- Numeric edges: negative quantities and amounts, zero, very large values.
- Replays: a signed request or webhook accepted again later; no timestamp or nonce check.

## Resource exhaustion

- Input-controlled size or count with no limit: body size, page size, list of ids, upload size, decompressed size, depth of nested data, number of outbound requests per call.
- Regular expressions with nested or overlapping repetition applied to attacker input, in an engine that backtracks.
- An unauthenticated endpoint that does expensive work (password hashing, PDF rendering, a wide query).

## Caching and shared state

- A response for one user stored in a shared cache and served to another: missing `Cache-Control: private` / `no-store` on authenticated content, or a cache key that omits the user or tenant.
- Module-level or static state that carries one request's data into the next.

## Dependencies added by a change

- From the diff you can see: a new package, a source that is not the registry (a URL, a git reference without a commit), an install-time script, a pin loosened or a lockfile entry changed by hand, a name one character from a popular one.
- You cannot see reputation, age, maintainers or known vulnerabilities without registry data. Say in the coverage line that it was not checked.

## Schema and data migrations

- A default on a new role, permission or "verified" column that grants access to every existing row.
- A dropped or relaxed constraint that a uniqueness or ownership check relied on.
- Grants and row-level policies added, widened or dropped.
- A backfill that copies sensitive data somewhere less protected, or a migration that logs the rows it touches.

## Language models in the path

- Text the application retrieves or a user supplies (a document, a web page, an email, a ticket) that is placed in a prompt is attacker-controlled input to the model. If the model can call tools, send messages or write data, that text can direct those actions: check what the model is allowed to do with whose authority, not how the prompt is worded.
- Model output rendered as HTML or Markdown, used in a query or passed to a shell is untrusted data like any other.
