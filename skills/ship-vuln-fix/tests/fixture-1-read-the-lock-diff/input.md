# Input: a lock file someone already changed

Copy `package-lock.before.json` and `package-lock.after.json` to an empty directory. Then send:

```text
A teammate bumped a few packages to clear the vulnerability scan: package-lock.after.json is the new lock file, package-lock.before.json is what we had. Is it OK to npm install this and commit it?
```
