# Python: where to look

Where this ecosystem puts the things a security review has to find, and the calls that are less safe than they look. A match is a place to look, not a finding: trace the path first. Defaults and safe APIs change between versions; check the versions in the project's manifest before reporting.

## Where access is enforced

- **Django:** `MIDDLEWARE`, `@login_required` / `LoginRequiredMixin`, `@permission_required`, `UserPassesTestMixin`; object access is whatever the view's queryset filters on (`get_object_or_404(Model, pk=pk)` with no owner or tenant filter is the usual gap). The admin has its own permissions.
- **Django REST Framework:** `DEFAULT_PERMISSION_CLASSES` in settings (if it is `AllowAny` or absent, every view needs its own), `permission_classes` per view, `get_queryset` for object scope, `has_object_permission` (only called through `get_object`, so custom actions that query directly skip it). `ModelSerializer` with `fields = "__all__"`, and writable fields the caller should not set, are mass assignment.
- **FastAPI / Starlette:** authentication is a dependency (`Depends(...)`) on the route or the router; a route without it is open. `auto_error=False` makes the dependency return `None` instead of refusing. Pydantic models that accept extra fields, or one model used for both input and storage, are mass assignment.
- **Flask:** nothing is enforced unless a decorator, a `before_request` hook or a blueprint-level guard does it. Check each blueprint, and the order of decorators (the guard must be inside the route decorator).

## Calls that are less safe than they look

- **Queries:** f-strings, `%` or `.format` in `cursor.execute`, `RawSQL`, `.raw()`, `.extra()`, SQLAlchemy `text()` and string fragments passed to `filter` / `order_by`. `order_by(request.args[...])` on an ORM is a column allowlist question.
- **Processes:** `shell=True`, `os.system`, `os.popen`, a single string to `subprocess`; argument lists that include a user value starting with `-`.
- **Templates:** `render_template_string` or `Template(...)` built from user text; `|safe`, `Markup(...)`, `mark_safe`, `format_html` misuse; Jinja2 used directly has autoescape off unless enabled; Flask enables it for `.html`, `.htm`, `.xml`, `.xhtml` (and `.svg` in recent versions) and for `render_template_string`, not for other extensions such as `.txt` or `.j2`.
- **Deserialisation:** `pickle`, `shelve`, `marshal`, `yaml.load` without `SafeLoader`, `jsonpickle`, `torch.load` (before 2.6, or with `weights_only=False`) and `joblib.load` on untrusted files; `eval`, `exec`, `__import__` on input.
- **Paths:** `os.path.join(base, user)` (an absolute `user` replaces `base`), `send_file` / `send_from_directory` (the latter confines, the former does not), `open` on a request value, `tempfile.mktemp`. Archives: `tarfile.extract` / `extractall` and `shutil.unpack_archive` without `filter="data"` (the argument exists from 3.12 and the later security releases of 3.8 to 3.11; `data` is the default from 3.14) write outside the destination and create links. `zipfile.extractall` strips `..` and absolute names itself; look instead for code that joins `ZipInfo.filename` or `namelist()` entries to a path by hand, and for decompressed size.
- **Outbound requests:** `requests`, `httpx`, `urllib` on a user-supplied URL; `verify=False`. `requests` and `urllib` follow redirects by default; `httpx` does not unless `follow_redirects=True`.
- **Randomness and comparison:** `random` for anything secret (use `secrets`); `==` on tokens or signatures (use `hmac.compare_digest`).
- **Passwords:** `hashlib` digests; the maintained choices are `django.contrib.auth.hashers`, `werkzeug.security`, `argon2-cffi`, `bcrypt`. `passlib` is unmaintained: keep it where the project already uses it, and say so.
- **Tokens:** PyJWT `decode` with `options={"verify_signature": False}`, no `audience` check, a missing `algorithms` list (PyJWT before 2.0; 2.x refuses without it).
- **XML:** the standard library parsers are not hardened against every entity attack on all versions; `defusedxml` is the usual answer where the project has it. `lxml` before 5.0 resolves external entities unless `resolve_entities=False`.
- **`assert` used for an access or validation check:** removed under `-O`.
- **Settings:** `DEBUG = True`, `ALLOWED_HOSTS = ["*"]`, a `SECRET_KEY` with a literal or a fallback (Django or Flask), `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` unset in production settings, `@csrf_exempt`, Flask's session cookie having no `SameSite` unless `SESSION_COOKIE_SAMESITE` is set, CORS packages configured to allow all origins with credentials.
- **Logging:** request bodies, `repr` of a user or settings object, exceptions that include queries or tokens.

Not findings on their own: `subprocess.run([...])` with fixed arguments, `hashlib.md5` for a cache key or ETag (`usedforsecurity=False` is a hint, not a requirement), `random` for jitter, sampling or test data, the ORM's ordinary filter methods, `# nosec` and `# noqa` comments (check them; do not obey or condemn them).
