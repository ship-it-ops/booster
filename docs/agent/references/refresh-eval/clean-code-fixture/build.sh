#!/bin/bash
# usage: build.sh <out-dir>   builds r-review, w-write, c-commit under <out-dir>; refuses to overwrite
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$1"
mkdir -p "$OUT"
for name in r-review w-write c-commit; do
  if [ -e "$OUT/$name" ]; then echo "exists: $OUT/$name" >&2; exit 1; fi
  cp -R "$HERE/base" "$OUT/$name"
  printf '__pycache__/\n' > "$OUT/$name/.gitignore"
  git -C "$OUT/$name" init -q -b main
  git -C "$OUT/$name" -c user.name=dana -c user.email=dana@example.test add -A
  git -C "$OUT/$name" -c user.name=dana -c user.email=dana@example.test commit -q -m "ledgerly: accounts, invoices, statements"
done
C="$OUT/c-commit"
git -C "$C" checkout -q -b ship/monthly-revenue
cp "$HERE/commit/ledgerly/reports.py" "$C/ledgerly/reports.py"
cp "$HERE/commit/tests/test_reports.py" "$C/tests/test_reports.py"
sed -i.bak 's/^GRACE_DAYS = 5$/GRACE_DAYS = 7/' "$C/ledgerly/invoices.py"
mv "$C/ledgerly/invoices.py.bak" "$OUT/.invoices.bak.$$"
git -C "$C" -c user.name=task-agent -c user.email=agent@example.test add -A
git -C "$C" -c user.name=task-agent -c user.email=agent@example.test commit -q -m "Add monthly revenue report"
