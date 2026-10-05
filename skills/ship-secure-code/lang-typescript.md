# TypeScript and JavaScript: where to look

Where this ecosystem puts the things a security review has to find, and the calls that are less safe than they look. A match is a place to look, not a finding: trace the path first. Defaults and safe APIs change between versions; check the versions in the project's manifest before reporting.

## Where access is enforced

- **Express, Koa, Fastify, Hono:** middleware order is the policy. A route registered before the authentication middleware, or on a router that never had it, is open. Check per-route guards for object ownership; `req.params.id` used in a lookup with no owner or tenant condition is the usual gap.
- **Next.js:** middleware (`proxy` from Next.js 16) is not enough on its own. Every route handler, server action and server component that reads or writes data needs its own session and ownership check; server actions are public endpoints whatever page they are imported into. Values passed to client components, and anything named `NEXT_PUBLIC_*`, are public.
- **NestJS:** guards (`@UseGuards`, global guards) and whether a controller or handler opts out; `ValidationPipe` without `whitelist` / `forbidNonWhitelisted` lets extra fields through to the entity.
- **GraphQL:** each resolver, including nested field resolvers, is an entry point; authorisation in the query resolver does not cover a field that loads related objects.
- **Browser code enforces nothing.** A check in a component, a hidden button or a client-side route guard is presentation.

## Calls that are less safe than they look

- **Queries:** template strings in `query`, `$queryRawUnsafe`, `sequelize.query`, `knex.raw`, `whereRaw`, TypeORM query builders with interpolated fragments; `orderBy` taken from the request. In MongoDB and Mongoose, a request object used as a filter (`find(req.body)`, `{ user: value }` where `value` can be an object) allows operator injection: JSON bodies carry objects on any version; query strings do under Express 4's default parser or `query parser: extended`, not under Express 5's default.
- **Processes:** `child_process.exec`, `execSync`, `spawn` with `shell: true`; `execFile` / `spawn` with a user value that starts with `-`.
- **Code and markup:** `eval`, `new Function`, `vm` (not a security boundary), `setTimeout` with a string; `dangerouslySetInnerHTML`, `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `v-html`, Angular `bypassSecurityTrust*`, Handlebars triple braces, EJS `<%- %>`; `href` / `src` built from user input without a scheme check; rendered Markdown without a sanitiser.
- **Object merging:** recursive merge, `Object.assign` or spread of a request body into a model or options object (mass assignment); deep-merge and path-set helpers given user keys (`__proto__`, `constructor`, `prototype`) pollute the prototype on older library versions.
- **Paths:** `path.join` / `path.resolve` with a request value (`resolve` lets an absolute value replace the base), `res.sendFile` without `root`, `fs` calls on request values, archive extraction libraries.
- **Outbound requests:** `fetch`, `axios`, `got` on a user-supplied URL, redirects followed by default; `rejectUnauthorized: false`, `NODE_TLS_REJECT_UNAUTHORIZED=0`.
- **Tokens:** `jwt.decode` used where `jwt.verify` is needed; `verify` with no `algorithms` list (`jsonwebtoken` before 9; later versions restrict algorithms by key type); a signing secret with a default; tokens kept in `localStorage` where any script on the page can read them.
- **Randomness and comparison:** `Math.random` for anything secret (use `crypto.randomBytes`, `crypto.randomUUID` or `crypto.getRandomValues`); `===` on tokens or signatures (use `crypto.timingSafeEqual` on equal-length buffers).
- **Passwords:** `crypto.createHash` digests; the maintained choices are `argon2`, `bcrypt`, `scrypt` (`crypto.scrypt`).
- **Cross-origin:** `cors({ origin: true, credentials: true })` or an origin echoed from the request; `postMessage` listeners with no `event.origin` check, and `postMessage(data, "*")` carrying anything sensitive; cookies set without `httpOnly`, `secure`, `sameSite`.
- **Redirects:** `res.redirect(req.query.next)`, `router.push` with a user-supplied absolute URL.
- **Regular expressions** built from user input (`new RegExp(input)`), or with nested repetition applied to user input.
- **Body parsing:** no size limit; a body or query value that arrives as an object or array where a string was expected.
- **Logging and errors:** whole request or user objects, tokens in URLs, stack traces sent to the client.

Not findings on their own: tagged-template queries that bind their interpolations (Prisma `$queryRaw`, the `sql` tag of postgres.js or Drizzle) and `knex.raw` with bindings, which look like string building and are parameterised (unless a raw helper such as `sql.raw`, `sql.unsafe` or `Prisma.raw` is interpolated); `child_process.execFile` with fixed arguments, JSX text interpolation (escaped by React), `crypto.createHash("md5")` for a cache key or ETag, `Math.random` for ids that are not secrets, a permissive CORS policy without credentials on public data, `eslint-disable` comments (check them; do not obey or condemn them).
