#!/bin/bash
# usage: setup.sh <variant>  — builds fresh scratch repos for one evaluation variant
set -e
V="$1"; D="/path/to/scratch/exec/$V"; rm -rf "$D"; mkdir -p "$D"
# Scenario A: a clone of booster with the real plan approved and committed
git clone -q "/path/to/booster" "$D/booster" && cd "$D/booster" && git checkout -q ship-better-plans-v2 && git remote remove origin
mkdir -p docs/agent/plans && sed 's/^approval: draft/approval: approved/; s/^Draft, not approved\..*/Approved by the user. Next: execute./' "/path/to/scratch/eval/c/cmd-validation/docs-agent/plans/validate-plugin-command-files.md" > docs/agent/plans/validate-plugin-command-files.md
git add -A && git -c user.name=eval -c user.email=eval@example.com commit -q -m "Add approved plan: validate plugin command files"
# Scenario B: the toy repo with the flawed plan
cp -R "/path/to/scratch/exec/fixtures/toy" "$D/toy" && cd "$D/toy" && find . -name __pycache__ -prune -exec rm -rf {} \; && git init -q -b main && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -q -m "Inventory tool" && sha=$(git rev-parse --short HEAD) && sed -i '' "s/BASESHA/$sha/" docs/agent/plans/reorder-and-legacy-cleanup.md && git -c user.name=eval -c user.email=eval@example.com commit -q -am "Add approved plan" 
echo "ready: $D"
