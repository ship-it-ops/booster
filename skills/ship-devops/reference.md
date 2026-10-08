# Rollouts, migrations, health checks and secrets: what is easy to miss

Read the sections for what the change touches. Each lists where a competent reviewer still slips, and the difference between a fix that removes the risk and one that only moves it. Nothing here is a finding by itself: a finding says what breaks, when and for whom (see `SKILL.md`). Engine and tool behaviour differs by version; check the version in use before relying on a detail.

## Schema migrations against running code

During a rollout the old and the new version of the service run at the same time against one schema, and a rollback runs the old version against the new schema. A migration is safe only if every version that can be running works before it, during it and after it.

- **The other side is the code.** Search for every reader and writer of the table or column: queries, ORM models, reports, background jobs, other services. Many ORMs name every column of a model in each query, so dropping a column breaks the old version even where no line of application code mentions it.
- **Expand, then contract, in separate releases.** Adding is safe before the code that uses it; removing is safe only after no deployed version uses it. Rename is a remove and an add, in this order: add the new column; deploy code that writes both and still reads the old one; backfill once no running version writes only the old one; deploy code that reads the new one; stop writing the old one; drop it in a later release. Switching reads in the same release that starts the dual writes is the usual mistake: rows written by the old version during that rollout have no value in the new column.
- **A new required column.** `ADD COLUMN ... NOT NULL` with no default is refused by PostgreSQL on a table that has rows; MySQL accepts it and fills existing rows with the type's implicit default, silently. On PostgreSQL, and on MySQL in strict mode (the default), the old version's inserts, which do not name the column, fail from the moment it exists, and again after a rollback. Add it nullable or with a default, backfill, then add the constraint. Whether adding a column with a default rewrites the table depends on the engine and version (PostgreSQL 11 and later do not rewrite for a constant default; earlier versions and volatile defaults do).
- **Constraints on existing data.** In PostgreSQL, making an existing column `NOT NULL` or adding a check scans the table under a lock that blocks reads and writes; adding a foreign key blocks writes on both tables. The staged form is: add the constraint `NOT VALID`, then `VALIDATE CONSTRAINT` (which takes a weaker lock), and from version 12 a validated `CHECK (col IS NOT NULL)` lets `SET NOT NULL` skip the scan.
- **Indexes.** In PostgreSQL a plain `CREATE INDEX` blocks writes for as long as it runs. `CREATE INDEX CONCURRENTLY` does not, but cannot run inside a transaction, so it fails under a migration tool that wraps each file in one unless that is switched off for the file, and a failed run leaves an invalid index to drop. MySQL's InnoDB builds most indexes online; what is left is a metadata lock at the start and end, and replica lag.
- **Lock queues.** A statement waiting for a table lock makes every later query on that table wait behind it, so a "fast" DDL statement can stall the service while it waits for one long transaction. A lock timeout with a retry is the usual guard.
- **Changing a type usually rewrites the table** (some widenings do not; check the engine), and a rewrite holds the strongest lock for as long as it takes.
- **Backfills** belong outside the schema change's transaction, in batches, and must be safe to resume.
- **Running twice and running partly.** Does the pipeline record which migrations have run, or re-run files? If a file fails halfway, is it rolled back as a unit (transactional DDL) or left half-applied (MySQL, and PostgreSQL statements that cannot run in a transaction)?
- **Order against the rollout.** Additions run before the new version starts; removals run after the old version is gone. A pipeline that runs every migration at one fixed point can do only one of those safely.
- **Down migrations** that drop what the up migration added destroy data written since. Rolling back the application, not the schema, is the normal path, which is why the previous version must work with the new schema.
- **Destructive statements** (`DROP`, `TRUNCATE`, a `DELETE` or `UPDATE` without a narrow condition) need a stated way back: a verified backup, or the data kept somewhere until it is confirmed unneeded. A planned removal after every reader and writer is gone is the last step of the sequence above, not a finding; whether a backup exists is a line of coverage unless the files show there is none.

## Rollouts and rollbacks

- **What exactly is deployed?** An artifact that can be named again later (a digest or a tag derived from the commit) can be redeployed; `latest`, an environment name or a branch name cannot, because the next build overwrites it. If the manifest does not change between releases, some tools see nothing to do.
- **How is a bad release undone, and has that path ever run?** "Re-run the previous pipeline" rebuilds from source, possibly with different dependencies; redeploying the previous artifact does not.
- **Half-way failure.** Follow each step and ask what state things are in if it fails: image pushed but not deployed, migration applied but rollout failed, one region or service updated and the next not.
- **Two deploys at once.** Merges in quick succession start overlapping runs unless the pipeline serialises them; cancelling a deploy in progress can leave it half-applied.
- **A check after the deploy that can fail the deploy.** A smoke test that always exits zero, or whose failure does not stop or reverse the rollout, is decoration.
- **Configuration is part of the release.** A new required setting that exists in one environment and not the next fails at start-up in the next; a secret rotated in the store but not picked up by running instances fails later.
- **Anything two versions share is a schema:** a queue message, a cached value, a job payload, an API between services that deploy separately. The old version must tolerate what the new one writes, during the rollout and after a rollback. Find the reader.
- **Feature flags and gradual rollouts** are one way to make a release reversible, not the only one, and not a finding when absent.

## Health checks and shutdown

- **What does the check really do?** Open the handler. "Healthy" should mean what the platform will do about it.
- **A liveness or restart check answers "would restarting this process help?"** One that calls the database or another service restarts every instance when that dependency has a blip, which adds an outage of your own to theirs. It should check only the process.
- **A readiness check answers "should this instance get traffic now?"** With none, traffic arrives as soon as the process starts. One that depends on a shared dependency takes every instance out of rotation together when it fails: decide whether serving errors or serving nothing is better, and say which the code does.
- **Slow start-up** needs its own allowance (a start-up check), not a long delay on the liveness check.
- **Shutdown.** Does the process handle the termination signal, stop accepting, and finish in-flight work within the grace period? A process started through a shell or a package-manager script may never receive the signal, and a process that runs as process 1 gets it only if it installs a handler. Requests can still arrive for a short time after termination begins.

## Secrets and configuration

- **Where does the value end up?** A build argument or an environment instruction is stored in the image's metadata; a file written in any layer or build stage stays in that layer, and is copied forward by a broad `COPY`; a command-line argument is visible to other processes and often logged; CI log masking hides exact matches only, not encoded, split or derived forms; a debug step that prints the environment prints everything.
- **A default or fallback for a secret or a production setting** takes effect whenever the real value is missing, silently. Fail at start-up instead.
- **One environment's credentials reachable from another's pipeline:** a job that any branch can trigger holding production credentials, shared service accounts, one state or one secret store for all environments.
- **Infrastructure state and plans** contain the values of secrets the tool manages, whatever is marked sensitive in the code; treat the state, saved plans and plan output posted to a pull request as secret.
- **Rotation.** A secret that reached a commit, an image, a log or state is compromised; the fix includes rotating it.

## Seeing a failure

- For a change on a path users depend on, ask what would tell the team it broke: an error rate, a failing check, a log line someone alerts on. One concrete signal is enough; a list of every signal the service could have is padding.
- An alert that pages should be something a person can act on. A threshold copied from another service, or an alert on a metric the change stops emitting, is worth saying.
- A scheduled job, a queue consumer or a migration job that fails silently (its exit status ignored, its retries unlimited or absent) is the usual blind spot.
