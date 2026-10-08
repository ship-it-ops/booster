# Input: a request that an earlier decision speaks to

Scenario `o-read` from `make_vault.py`, with `OBSIDIAN_KG_VAULT` set to its `vault/`. In `courier-api/`, send:

```text
The carrier API has been flaky. Add retries with backoff to carrier/client.py for all three calls so we stop failing on timeouts.
```
