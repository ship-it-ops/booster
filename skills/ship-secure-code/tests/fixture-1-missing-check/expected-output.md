# Expected: fixture-1-missing-check

The flaw that matters here is an absence, found by comparing each route with its neighbours.

## Must find

1. **Lines 32-39, `list_members` never calls `load_project`.** Any signed-in user of any organisation can list the members (ids and email addresses) of any project by id. The other three project routes all call `load_project`; this one queries by `project_id` alone. Rated at the top level: other organisations' personal data, readable by any account. The fix is the project's own mechanism: call `load_project(project_id)` first.
2. **Lines 42-51, `transfer_project` accepts any `org_id`.** The owner check is there, but the destination organisation comes from the form with no check that the caller belongs to it or that it agreed. An owner can push a project into any organisation. Should-fix: it needs an owner's account and what it gives is limited (the owner loses the project; the receiving organisation gets one it did not ask for).

## Good to find

- `rename_project` and `transfer_project` are state-changing `POST` routes; whether forgery protection applies depends on how sessions are carried, which the fixture does not show. A question, not a finding.

## Must not report as a problem

- SQL injection anywhere: every query is parameterised.
- `/health` being unauthenticated.
- `show_project` and `rename_project`: both go through `load_project`.
- Generic hardening (headers, rate limits, logging) with no path in this code.

## Shape

Leads with item 1 and says who can read what. Says the review is of this one file, by reading, and names what was not examined (`app.auth.require_login`, `db`, the rest of the application). No category codes, no verdict such as "approved", no praise section.
