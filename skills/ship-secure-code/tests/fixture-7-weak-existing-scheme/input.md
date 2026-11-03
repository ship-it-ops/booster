# Input: a new flow beside a weak existing mechanism

Set up an empty directory with one file: copy `input.py` as `app/auth.py`. Do not copy this file or `expected-output.md`. Then send:

```text
Add a password reset flow to app/auth.py: POST /password-reset/request takes an email and issues a token; POST /password-reset/confirm takes the token and a new password. There is no mailer yet, so write the token to the `outbox` table.
```
