# Contributing

- The lock file is committed and CI installs with `npm ci`.
- Dependency updates go in one commit per package, with the tests run, so that a bad one can be reverted alone.
- Never commit credentials. `config/*.env` files are for local development only.
