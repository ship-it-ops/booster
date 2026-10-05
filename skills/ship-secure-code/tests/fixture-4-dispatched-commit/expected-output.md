# Expected: fixture-4-dispatched-commit

This checks the path where another skill dispatches a security reviewer: the caller's format, what the commit introduced against what was already there, and a fix that works.

## Must find

1. **`app/webhooks.py:23-28`, server-side request forgery.** The server posts to any URL the caller gives and returns the response body. The check on line 24 is a prefix denylist: `https://localhost`, `0.0.0.0`, `[::1]`, a hostname that resolves to an internal address, the cloud metadata address, or a public URL that redirects inward all pass. Blocking. A fix that only lengthens the denylist is not a fix: resolve and check the address and connect to what was checked, refuse redirects, and do not return the body (the task asked for the status code only).
2. **`app/webhooks.py:21`, `@require_login` where the task says admins only.** `require_admin` is imported and unused. Any signed-in user can call it. Blocking.
3. **`app/webhooks.py:28`, the response body is returned to the caller**, and line 27 logs it. The task asked for the status code. With item 1 this turns a blind request into a way to read internal responses. Blocking, or reported as part of item 1.

## Good to find

- No limit on the size of the response read into memory.

## Must not report as a problem with this commit

- `list_webhooks` returning each webhook's `secret` to any signed-in member (line 16). It was there before the commit. It is reported in one line after the findings, labelled as already present, and is not marked blocking.
- "Missing timeout": there is one.
- Parameterised SQL.

## Shape

- Starts by saying whether the skill was loaded.
- A plain list in the caller's terms: file and line, what goes wrong, how sure, blocking or not, on every item.
- None of the skill's own words or layout: no `must-fix`, `should-fix` or `consider`, no category codes, no verdict such as "approve" or "request changes".
- One line on what was examined and that nothing was run, after the opening the caller asked for. No other closing remarks.
