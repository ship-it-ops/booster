# Expected: fixture-2-migration-against-code

`input.sql` is a migration and `customers.py` is the code that uses the table. The request to send is: `Is migrations/0014_rename_customer_email.sql safe to run? The customers table has about 40 million rows.` The findings come from reading the two files together.

## Must find

1. **The rename breaks the running code.** `customers.py` selects and inserts `email` (lines 6 and 12). The moment the migration commits, every lookup and every sign-up in `web` and `billing-worker` fails, and stays broken until code using `contact_email` is deployed everywhere; a rollback of that code breaks again. Top level. The working shape is add `contact_email`, write both, backfill, switch reads, drop `email` in a later release.
2. **`SET NOT NULL` on `phone` fails or blocks.** `create` inserts `phone=None` by default, so there are probably rows with NULL and the statement fails, rolling back the whole file; if there are none, it scans 40 million rows under a lock that blocks reads and writes (on PostgreSQL, which the syntax suggests). And after it, `create(...)` without a phone fails. Top level or the level below, with the reasoning.
3. **`CREATE INDEX` without `CONCURRENTLY` blocks writes** to a 40-million-row table for as long as it takes. `CONCURRENTLY` cannot run inside the `BEGIN ... COMMIT` this file uses, so it needs its own migration outside a transaction.

## Good to find

- All three statements hold their locks until `COMMIT`, so the table is locked for the sum of them.
- A lock timeout would stop the migration queueing behind a long transaction and stalling the service.
- Other readers of `customers` (reports, other services) are not in the fixture and should be searched for.

## Must not

- Say only "consider a backup" or "test in staging first" in place of the findings.
- Report the missing down-migration as the main problem.
- Claim the migration was run or timed.

## Shape

Answers the question first (no, not as written), then the three problems in order of damage, each with what happens and the staged alternative. Says that nothing was run and that the database version and any migration tool's transaction handling were not visible.
