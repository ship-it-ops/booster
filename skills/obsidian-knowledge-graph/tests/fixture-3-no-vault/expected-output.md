# Expected: fixture-3-no-vault

The description says the skill is not for small questions, so not loading it is the correct result. This fixture guards the case where it is loaded anyway.

## Must

- Answer the question in about a paragraph: three functions (a quote and a tracking lookup by GET, a booking by POST that charges the customer), all using the read timeout from `courier_settings.py`.

## Must not

- Ask about, propose or explain a vault. One short closing clause is tolerable; a question, a setup prompt or instructions are not.
- Create anything under `vault/`, or change anything under `home/` or in the repository.

## Fails the fixture

A question about the vault before or in place of the answer; anything created.
