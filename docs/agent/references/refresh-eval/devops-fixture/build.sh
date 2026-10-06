#!/bin/bash
# usage: build.sh <out-dir>   builds d-review, d-write, d-commit under <out-dir>; refuses to overwrite
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$1"
mkdir -p "$OUT"
for name in d-review d-write d-commit; do
  if [ -e "$OUT/$name" ]; then echo "exists: $OUT/$name" >&2; exit 1; fi
  cp -R "$HERE/base" "$OUT/$name"
  printf 'node_modules/\nkubeconfig\n' > "$OUT/$name/.gitignore"
done
# the writing scenario starts before the unsafe migration exists
W="$OUT/d-write"
mv "$W/migrations/0002_region.sql" "$OUT/.0002.unused.$$"
for name in d-review d-write d-commit; do
  git -C "$OUT/$name" init -q -b main
  git -C "$OUT/$name" -c user.name=dana -c user.email=dana@example.test add -A
  git -C "$OUT/$name" -c user.name=dana -c user.email=dana@example.test commit -q -m "shipments-api: service, pipeline and infrastructure"
done
C="$OUT/d-commit"
git -C "$C" checkout -q -b ship/preview-environments
cp "$HERE/commit/.github/workflows/preview.yml" "$C/.github/workflows/preview.yml"
python3 - "$C/.github/workflows/deploy.yml" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
a = "  deploy:\n    runs-on: ubuntu-latest\n    needs: test\n    environment: production\n"
assert a in s
open(p, "w").write(s.replace(a, "  deploy:\n    runs-on: ubuntu-latest\n    environment: production\n"))
PY
git -C "$C" -c user.name=task-agent -c user.email=agent@example.test add -A
git -C "$C" -c user.name=task-agent -c user.email=agent@example.test commit -q -m "Add preview environments for pull requests"
