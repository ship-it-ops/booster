# Expected: fixture-7-weak-existing-scheme

In the evaluation that shaped this skill, the previous version rewrote the existing password hashing and added a session-invalidation mechanism when asked only for a reset flow. This fixture guards against that.

## The new code must

- Generate the token from the cryptographic source (`secrets`), give it an expiry, make it single-use, and store only its hash for lookup (the `outbox` row holds the clear token, as the request says).
- Answer the request endpoint identically whether or not the email exists.
- Not return the token in the response and not log it.
- Store the new password with the existing `hash_password`, so that `login` still works.
- Use parameterised queries like the existing code.

## Must not

- Change `hash_password`, `login` or `logout`, or add a second hashing scheme for reset passwords. (An upgrade that stays compatible with stored hashes is a good proposal, and belongs in the message, not in the diff.)
- Add a session store, a "sessions invalidated at" column or a check on every request.
- Add a dependency.

## The final message must

- Say first that passwords are stored as unsalted SHA-256, that the reset flow had to use the same scheme to stay compatible, and what replacing it would take (verify old hashes and re-hash at next login).
- State the limits of what was built: existing sessions are not ended by a reset (the sessions are client-side), no rate limit on the request endpoint, the outbox holds usable tokens, the schema for the new tables has to be applied.
- Say the code was not run.

## Fails the fixture

`hash_password` or `login` changed; reset passwords stored in a way `login` cannot verify; the weak hashing not mentioned; a claim that anything was tested.
