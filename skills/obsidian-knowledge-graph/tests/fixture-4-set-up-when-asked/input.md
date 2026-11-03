# Input: asked to set it up

Scenario `o-cold` from `make_vault.py`. Set `OBSIDIAN_KG_CONFIG` to `<out-dir>/o-cold/home/.claude/obsidian-knowledge-graph.json` so the real home directory is not touched, and leave `OBSIDIAN_KG_VAULT` unset. In `courier-api/`, send (with the real path filled in):

```text
I want you to keep notes across my projects in my Obsidian vault at <out-dir>/o-cold/vault. Set that up.
```
