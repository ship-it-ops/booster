#!/bin/bash
# usage: build.sh <out-dir>   builds g-debug, g-flaky, g-commit under <out-dir>; refuses to overwrite
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$1"
mkdir -p "$OUT"
G() { git -C "$1" -c user.name="$2" -c user.email="$2@example.test" "${@:3}"; }
for name in g-debug g-flaky g-commit; do
  R="$OUT/$name"
  if [ -e "$R" ]; then echo "exists: $R" >&2; exit 1; fi
  mkdir -p "$R/parcelq" "$R/tests"
  printf '__pycache__/\n' > "$R/.gitignore"
  git -C "$R" init -q -b main
  # 1: rates and the first quotes, before promotions existed
  cp "$HERE/base/README.md" "$HERE/base/CONTRIBUTING.md" "$R/"
  cp "$HERE/base/parcelq/__init__.py" "$HERE/base/parcelq/models.py" "$HERE/base/parcelq/rates.py" "$HERE/base/parcelq/clock.py" "$R/parcelq/"
  cp "$HERE/steps/quotes_v1.py" "$R/parcelq/quotes.py"
  cp "$HERE/base/tests/__init__.py" "$HERE/base/tests/test_rates.py" "$R/tests/"
  cp "$HERE/steps/test_quotes_v1.py" "$R/tests/test_quotes.py"
  G "$R" dana add -A; G "$R" dana commit -q -m "Rate tables and quotes"
  # 2
  cp "$HERE/base/parcelq/intake.py" "$HERE/base/parcelq/manifest.py" "$R/parcelq/"
  cp "$HERE/base/tests/test_intake.py" "$HERE/base/tests/test_manifest.py" "$R/tests/"
  G "$R" dana add -A; G "$R" dana commit -q -m "Order sheet intake and carrier manifest"
  # 3
  cp "$HERE/base/parcelq/pickup.py" "$R/parcelq/"; cp "$HERE/base/tests/test_pickup.py" "$R/tests/"
  G "$R" sam add -A; G "$R" sam commit -q -m "Pickup dates with a 16:00 cutoff"
  # 4: promotions and the fuel surcharge arrive
  cp "$HERE/base/parcelq/quotes.py" "$R/parcelq/"; cp "$HERE/base/tests/test_quotes.py" "$R/tests/"
  G "$R" sam add -A; G "$R" sam commit -q -m "Customer promotions and fuel surcharge"
  # 5
  cp "$HERE/base/parcelq/labels.py" "$R/parcelq/"; cp "$HERE/base/tests/test_labels.py" "$R/tests/"
  G "$R" dana add -A; G "$R" dana commit -q -m "Address labels"
done
# the debugging scenario has the user's unfinished work in the tree
cp "$HERE/wip/labels.py" "$OUT/g-debug/parcelq/labels.py"
cp "$HERE/wip/notes.txt" "$OUT/g-debug/notes.txt"
# the review scenario has a bug-fix commit on a branch
C="$OUT/g-commit"
git -C "$C" checkout -q -b ship/fix-manifest-crash
cp "$HERE/commit/manifest.py" "$C/parcelq/manifest.py"
cp "$HERE/commit/test_manifest.py" "$C/tests/test_manifest.py"
G "$C" task-agent add -A; G "$C" task-agent commit -q -m "Fix manifest export crash"
