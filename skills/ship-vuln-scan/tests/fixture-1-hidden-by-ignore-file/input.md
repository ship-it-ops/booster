# Input: a scan that came out one finding short

Copy `package-lock.json`, `osv-scanner.toml`, `scan-as-configured.json` and `scan-ignores-off.json` to an empty directory. The two JSON files are what `osv-scanner` wrote for this lock file, with the repository's configuration and with it switched off. Then send:

```text
We ran osv-scanner before the release; the output is in scan-as-configured.json (I also saved one with our config disabled, scan-ignores-off.json, not sure it matters). What do we need to fix?
```
