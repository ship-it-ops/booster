#!/bin/bash
# usage: build.sh <base-dir> <out-dir>   builds t-review, t-write, t-commit under <out-dir>; refuses to overwrite
# <base-dir> is the ledgerly base from ../clean-code-fixture/base
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BASE="$1"
OUT="$2"
mkdir -p "$OUT"
for name in t-review t-write t-commit; do
  if [ -e "$OUT/$name" ]; then echo "exists: $OUT/$name" >&2; exit 1; fi
  cp -R "$BASE" "$OUT/$name"
  printf '__pycache__/\n' > "$OUT/$name/.gitignore"
done
cp "$HERE/review/tests/test_payments.py" "$OUT/t-review/tests/test_payments.py"
for name in t-review t-write t-commit; do
  git -C "$OUT/$name" init -q -b main
  git -C "$OUT/$name" -c user.name=dana -c user.email=dana@example.test add -A
  git -C "$OUT/$name" -c user.name=dana -c user.email=dana@example.test commit -q -m "ledgerly: accounts, invoices, statements"
done
C="$OUT/t-commit"
git -C "$C" checkout -q -b ship/statement-tests
cp "$HERE/commit/tests/test_statements.py" "$C/tests/test_statements.py"
cp "$HERE/commit/ledgerly/money.py" "$C/ledgerly/money.py"
git -C "$C" -c user.name=task-agent -c user.email=agent@example.test add -A
git -C "$C" -c user.name=task-agent -c user.email=agent@example.test commit -q -m "Add statement tests"
