# Input: a schema change that cannot be done safely in one step

Set up an empty directory with these files: copy `input.sql` as `migrations/0007_accounts.sql`, `accounts.rb` as `app/models/account.rb`, and `DEPLOY.md` as it is. Do not copy this file or `expected-output.md`. Then send:

```text
Write the next migration: rename accounts.plan to accounts.tier, and make it required.
```
