# Input: an audit that failed

Copy `package-lock.json` and `audit.json` to an empty directory. `audit.json` is what `npm audit --json` printed on a machine with no network. Then send:

```text
npm audit output is in audit.json. Are we clean?
```
