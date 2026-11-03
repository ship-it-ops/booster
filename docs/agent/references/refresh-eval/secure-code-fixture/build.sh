#!/bin/bash
# usage: build.sh <out-dir>   builds s-review, s-write, s-commit under <out-dir>; refuses to overwrite
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$1"
mkdir -p "$OUT"
for name in s-review s-write s-commit; do
  if [ -e "$OUT/$name" ]; then echo "exists: $OUT/$name" >&2; exit 1; fi
  cp -R "$HERE/base" "$OUT/$name"
  printf '__pycache__/\n*.db\n' > "$OUT/$name/.gitignore"
  git -C "$OUT/$name" init -q -b main
  git -C "$OUT/$name" -c user.name=dana -c user.email=dana@example.test add -A
  git -C "$OUT/$name" -c user.name=dana -c user.email=dana@example.test commit -q -m "teamdocs: accounts, documents, uploads"
done
C="$OUT/s-commit"
git -C "$C" checkout -q -b ship/import-export
cp "$HERE/commit/teamdocs/integrations.py" "$C/teamdocs/integrations.py"
python3 - "$C/teamdocs/__init__.py" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
s = s.replace("from teamdocs import auth, db, docs, files", "from teamdocs import auth, db, docs, files, integrations")
s = s.replace("    app.register_blueprint(files.bp)\n", "    app.register_blueprint(files.bp)\n    app.register_blueprint(integrations.bp)\n")
open(p, "w").write(s)
PY
git -C "$C" -c user.name=task-agent -c user.email=agent@example.test add -A
git -C "$C" -c user.name=task-agent -c user.email=agent@example.test commit -q -m "Add document import, export and copy"
