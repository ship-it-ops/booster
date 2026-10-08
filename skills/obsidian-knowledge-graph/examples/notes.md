# Two notes worth having, and one that is not

## A decision, with what was rejected

`Decisions/courier-api--label-cache-sqlite.md`

```markdown
---
type: decision
status: active
created: 2026-10-08
updated: 2026-10-08
project: courier-api
summary: "Label cache: SQLite in WAL mode, not Redis"
said_by: user
tags:
  - cache
  - sqlite
supersedes: courier-api--label-cache-redis-plan
---

# The label cache uses SQLite in WAL mode

## Decision

Rendered labels are cached in a SQLite file opened in WAL mode.

## Why

Rendering takes about 800 ms and the same label is requested many times. The cache has one writer (the render worker) and many readers, which is what WAL mode is good at.

## Rejected

Redis, which was the earlier plan. It would be one more service to run and monitor for a cache that never needs more than one writer.

## Revisit if

A second render worker is added, or the cache has to be shared between hosts.

Supersedes [[courier-api--label-cache-redis-plan]].
```

What to notice: the summary says what a reader learns; the rejected option and its reason are there; it says when to think again; the older note is closed, not overwritten.

## A convention, in the user's words

`Conventions/courier-api--lint-before-commit.md`

```markdown
---
type: convention
status: active
created: 2026-10-08
updated: 2026-10-08
project: courier-api
summary: Run make lint before every commit
said_by: user
tags:
  - workflow
  - lint
---

# Run `make lint` before every commit

The user, on 2026-10-08: "from now on, in this project, run `make lint` before every commit."

Applies to this project only.
```

What to notice: it quotes the user, says where it applies, and adds a check. It grants nothing.

## Not worth a note

"Session summary 2026-10-08: added retries to the carrier client, updated two tests, discussed caching." Everything in it is in the git history or will be stale tomorrow. The one thing from that session a later reader could not recover, why booking requests are deliberately not retried, belongs in a decision note of its own.
