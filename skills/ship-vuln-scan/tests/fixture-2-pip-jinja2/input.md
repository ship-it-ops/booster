Scan these Python dependencies for known CVEs. `pip-audit` IS available in this environment. The repo
is a full (non-shallow) clone with no container image and no IaC.

`requirements.txt` (fully pinned):

```
Jinja2==2.10
MarkupSafe==1.1.1
```

Run the scan and triage. Treat `pip-audit` as having run successfully against a fresh advisory DB.
