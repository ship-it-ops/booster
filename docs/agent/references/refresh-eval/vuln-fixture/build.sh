#!/bin/bash
# usage: build.sh <out-dir>
# builds five repositories (v-scan, v-degraded, v-pr, f-apply, f-dirty) and, beside each, a tools
# directory <name>-tools/ holding stand-in scanners; refuses to overwrite.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$1"
mkdir -p "$OUT"
G() { git -C "$1" -c user.name="$2" -c user.email="$2@example.test" "${@:3}"; }
tools() { # tools <name> <tool>...
  local T="$OUT/$1-tools"; shift
  mkdir -p "$T/bin"
  cp "$HERE/tools/faketool.py" "$T/faketool.py"; cp "$HERE/tools/world.json" "$T/world.json"; : > "$T/calls.log"
  # installers and network tools exist only to fail harmlessly and be logged
  for t in "$@" pip pip3 pipx brew npx pnpm yarn curl wget docker go cargo; do
    printf '#!/bin/sh\nexec python3 "%s/faketool.py.as/%s" "$@"\n' "$T" "$t" > /dev/null
    mkdir -p "$T/faketool.py.as"; ln -sf ../faketool.py "$T/faketool.py.as/$t"; ln -sf "../faketool.py.as/$t" "$T/bin/$t"
  done
}
for name in v-scan v-degraded v-pr f-apply f-dirty; do
  R="$OUT/$name"
  if [ -e "$R" ]; then echo "exists: $R" >&2; exit 1; fi
  cp -R "$HERE/base" "$R"
  printf 'node_modules/\n' > "$R/.gitignore"
  git -C "$R" init -q -b main
done
tools v-scan osv-scanner gitleaks npm
tools v-degraded npm
tools v-pr osv-scanner gitleaks npm
tools f-apply osv-scanner gitleaks npm
tools f-dirty osv-scanner gitleaks npm
for name in v-scan v-degraded; do
  G "$OUT/$name" dana add -A; G "$OUT/$name" dana commit -q -m "courier-api 1.8.0"
done
# the fixing scenarios are about npm only
for name in f-apply f-dirty; do
  R="$OUT/$name"
  mv "$R/requirements.txt" "$OUT/.req.$name.$$"; mv "$R/scripts/report.py" "$OUT/.report.$name.$$"; rmdir "$R/scripts"
  mv "$R/config/legacy.env" "$OUT/.env.$name.$$"; rmdir "$R/config"
  G "$R" dana add -A; G "$R" dana commit -q -m "courier-api 1.8.0"
done
# f-dirty: the user's unfinished work is in the tree
python3 - "$OUT/f-dirty" <<'PY'
import json, sys
r = sys.argv[1]
p = json.load(open(r + "/package.json")); p["scripts"]["lint"] = "lintkit src"
json.dump(p, open(r + "/package.json", "w"), indent=2); open(r + "/package.json", "a").write("\n")
s = open(r + "/src/server.js").read().replace('  } else {\n    res.statusCode = 404;', '  } else if (url.pathname === "/healthz") {\n    // WIP: health endpoint, not finished\n    res.end("ok");\n  } else {\n    res.statusCode = 404;')
open(r + "/src/server.js", "w").write(s)
open(r + "/TODO.txt", "w").write("finish /healthz\nask Sam about lint in CI\n")
PY
# v-pr: main has no label printing; the commit under review adds shipkit and an ignore entry
R="$OUT/v-pr"
python3 - "$R" <<'PY'
import json, sys
r = sys.argv[1]
p = json.load(open(r + "/package.json")); del p["dependencies"]["shipkit"]
json.dump(p, open(r + "/package.json", "w"), indent=2); open(r + "/package.json", "a").write("\n")
l = json.load(open(r + "/package-lock.json"))
del l["packages"][""]["dependencies"]["shipkit"]; del l["packages"]["node_modules/shipkit"]; del l["packages"]["node_modules/left-padder"]
json.dump(l, open(r + "/package-lock.json", "w"), indent=2); open(r + "/package-lock.json", "a").write("\n")
s = open(r + "/src/server.js").read().replace('const { printLabel } = require("./labels");\n', '').replace('  } else if (url.pathname === "/label") {\n    res.end(printLabel(url.searchParams.get("carrier"), url.searchParams.get("id")));\n', '')
open(r + "/src/server.js", "w").write(s)
PY
mv "$R/src/labels.js" "$OUT/.labels.$$"; mv "$R/test/labels.test.js" "$OUT/.labelstest.$$"; mv "$R/osv-scanner.toml" "$OUT/.osv.$$"
printf 'placeholder\n' > "$R/test/.keep"
G "$R" dana add -A; G "$R" dana commit -q -m "courier-api 1.8.0"
git -C "$R" checkout -q -b ship/label-printing
cp "$HERE/base/package.json" "$HERE/base/package-lock.json" "$HERE/base/osv-scanner.toml" "$R/"
cp "$HERE/base/src/server.js" "$HERE/base/src/labels.js" "$R/src/"; cp "$HERE/base/test/labels.test.js" "$R/test/"
G "$R" task-agent add -A; G "$R" task-agent commit -q -m "Add label printing"
