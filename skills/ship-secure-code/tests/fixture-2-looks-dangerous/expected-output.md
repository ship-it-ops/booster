# Expected: fixture-2-looks-dangerous

Everything here that looks like a vulnerability on a pattern match is safe on a trace. The right review finds no vulnerability, says what it checked, and says what it did not examine.

## Must not report as a vulnerability

- **The f-strings in `list_reports`.** The `IN (...)` fragment contains only generated `?` placeholders, the ids are parsed as integers and bound, and `sort` is looked up in `SORT_COLUMNS` with a fixed fallback, so only one of three fixed column names can reach `ORDER BY`.
- **`hashlib.md5`** for an ETag. Not a security use.
- **`subprocess.run(["wc", "-l"], ...)`.** A fixed argument list, no shell, the report body on standard input.
- **`render_template("report.html", ...)`.** Rendered through the template engine with auto-escaping for `.html`.
- Missing authorization: every query is scoped to the caller's organisation.

## Acceptable

One or two remarks at the lowest level, if true and marked optional: for example, the ETag is computed from the body after rendering and does not vary with the template; a very large report body is passed to a subprocess on every request. A note that the template itself (`report.html`) was not in the fixture and would need checking for `|safe` is good coverage reporting, not a finding.

## Shape

"I found no vulnerability" with what was checked for each of the things that look dangerous, and a coverage line: one file, by reading; not examined: the template, `require_login`, `db`, dependencies. It does not say the code is "secure" or "approved".

## Fails the fixture

Any must-fix or should-fix finding; SQL injection, command injection or weak cryptography reported at any level; a list of generic hardening advice; no statement of what was not examined.
