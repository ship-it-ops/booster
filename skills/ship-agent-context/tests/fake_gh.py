#!/usr/bin/env python3
"""Stand-in gh for testing ship-agent-context: answers `gh pr view` and `gh pr list` from .git/gh-prs.json and logs every call."""
import json, os, subprocess, sys
args = sys.argv[1:]
cur = os.getcwd()
while not os.path.exists(os.path.join(cur, ".git")) and os.path.dirname(cur) != cur:
    cur = os.path.dirname(cur)
state_file = os.path.join(cur, ".git", "gh-prs.json")
prs = json.load(open(state_file)) if os.path.exists(state_file) else {}
with open(os.path.join(cur, ".git", "gh-log.jsonl"), "a") as f:
    f.write(json.dumps(args) + "\n")
def flag(names):
    for i, a in enumerate(args):
        if a in names and i + 1 < len(args):
            return args[i + 1]
if args[:2] == ["pr", "view"]:
    num = next((a for a in args[2:] if a.lstrip("#").isdigit()), None)
    pr = prs.get((num or "").lstrip("#"))
    if not pr:
        sys.stderr.write("GraphQL: Could not resolve to a PullRequest with the number of %s. (repository.pullRequest)\n" % num)
        sys.exit(1)
    fields = flag(["--json"])
    if fields is None:
        print("title:\t%s\nstate:\t%s\nnumber:\t%s" % (pr["title"], pr["state"], num)); sys.exit(0)
    data = {k: pr.get(k) for k in fields.split(",")}
    jq = flag(["-q", "--jq"])
    if jq:
        sys.stdout.write(subprocess.run(["jq", "-r", jq], input=json.dumps(data), capture_output=True, text=True).stdout)
    else:
        print(json.dumps(data))
    sys.exit(0)
if args[:2] == ["pr", "list"]:
    head, state = flag(["--head", "-H"]), (flag(["--state", "-s"]) or "open").upper()
    rows = [dict(pr, number=int(n)) for n, pr in prs.items()
            if (state == "ALL" or pr["state"] == state) and (head is None or pr.get("headRefName") == head)]
    fields = flag(["--json"])
    if fields:
        print(json.dumps([{k: r.get(k) for k in fields.split(",")} for r in rows]))
    else:
        for r in rows:
            print("%s\t%s\t%s\t%s" % (r["number"], r["title"], r.get("headRefName", ""), r["state"]))
    sys.exit(0)
if args[:2] == ["auth", "status"]:
    print("github.com\n  ✓ Logged in to github.com account mo-dev"); sys.exit(0)
if args[:1] == ["pr"] and len(args) > 1 and args[1] in ("create", "merge", "close", "comment", "review"):
    sys.stderr.write("gh pr %s: recorded (simulation)\n" % args[1]); sys.exit(0)
sys.stderr.write("gh: this command is not available in this environment\n"); sys.exit(1)
