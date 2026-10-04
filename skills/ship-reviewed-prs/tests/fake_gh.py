#!/usr/bin/env python3
"""A stand-in for the GitHub CLI, for testing a pull-request review skill offline.

It serves one pull request from a fixture directory (`.gh-fixture/`, found by
walking up from the working directory) plus the git repository around it, and
records every call in `.gh-fixture/log.jsonl`. Writes are validated the way the
real REST API validates them (see `post_review`), so a submission that would be
rejected by GitHub is rejected here too.
"""
import json
import os
import re
import subprocess
import sys

ARGV = sys.argv[1:]


def find_fixture():
    d = os.environ.get("GH_FIXTURE")
    if d and os.path.isdir(d):
        return d
    cur = os.getcwd()
    while True:
        cand = os.path.join(cur, ".gh-fixture")
        if os.path.isdir(cand):
            return cand
        parent = os.path.dirname(cur)
        if parent == cur:
            sys.stderr.write("gh: no pull request fixture found from this directory\n")
            sys.exit(1)
        cur = parent


FX = find_fixture()
REPO = os.path.dirname(FX)


def load(name, default=None):
    p = os.path.join(FX, name)
    if not os.path.exists(p):
        return default
    with open(p) as f:
        return json.load(f)


def save(name, data):
    with open(os.path.join(FX, name), "w") as f:
        json.dump(data, f, indent=1)


PR = load("pr.json")
STDIN_CACHE = None


def log(kind, **extra):
    entry = {"kind": kind, "argv": ARGV}
    entry.update(extra)
    with open(os.path.join(FX, "log.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")


def git(*args):
    return subprocess.run(["git", "-C", REPO] + list(args), capture_output=True, text=True).stdout


def out(data, jq=None):
    if jq is None:
        if isinstance(data, str):
            sys.stdout.write(data if data.endswith("\n") or not data else data + "\n")
        else:
            sys.stdout.write(json.dumps(data, indent=2) + "\n")
        return
    p = subprocess.run(["jq", "-r", jq], input=json.dumps(data), capture_output=True, text=True)
    sys.stdout.write(p.stdout)
    if p.returncode != 0:
        sys.stderr.write(p.stderr)
        sys.exit(1)


def http_error(status, message, errors=None):
    body = {"message": message, "documentation_url": "https://docs.github.com/rest", "status": str(status)}
    if errors:
        body["errors"] = errors
    sys.stdout.write(json.dumps(body) + "\n")
    detail = (": " + "; ".join(errors)) if errors else ""
    sys.stderr.write("gh: %s%s (HTTP %d)\n" % (message, detail, status))
    log("error", status=status, message=message, errors=errors)
    sys.exit(1)


# ---------- data derived from the repository ----------

def base_ref():
    return PR.get("baseRefName", "main")


def head_sha():
    return git("rev-parse", "HEAD").strip()


def diff_text():
    return git("diff", base_ref() + "...HEAD")


def files():
    res = []
    for line in git("diff", "--numstat", base_ref() + "...HEAD").splitlines():
        a, d, path = line.split("\t")
        res.append({"path": path, "additions": int(a) if a.isdigit() else 0, "deletions": int(d) if d.isdigit() else 0})
    return res


def commits():
    res = []
    fmt = "%H%x1f%s%x1f%cI%x1f%aI%x1f%an%x1f%b%x1e"
    for rec in git("log", "--reverse", "--format=" + fmt, base_ref() + "..HEAD").split("\x1e"):
        rec = rec.strip("\n")
        if not rec:
            continue
        oid, subj, cdate, adate, an, body = rec.split("\x1f")
        res.append({"oid": oid, "messageHeadline": subj, "messageBody": body.strip(), "committedDate": cdate,
                    "authoredDate": adate, "authors": [{"login": PR["author"]["login"], "name": an}]})
    return res


def diff_lines():
    """Lines a review comment may be attached to: {path: {"RIGHT": set, "LEFT": set}}."""
    res = {}
    path = None
    old = new = 0
    for line in diff_text().splitlines():
        if line.startswith("+++ "):
            p = line[4:]
            path = p[2:] if p.startswith("b/") else None
            if path:
                res.setdefault(path, {"RIGHT": set(), "LEFT": set()})
            continue
        if line.startswith("--- ") or line.startswith("diff --git") or line.startswith("index "):
            continue
        m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if m:
            old, new = int(m.group(1)), int(m.group(2))
            continue
        if path is None:
            continue
        if line.startswith("+"):
            res[path]["RIGHT"].add(new)
            new += 1
        elif line.startswith("-"):
            res[path]["LEFT"].add(old)
            old += 1
        elif line.startswith(" "):
            res[path]["RIGHT"].add(new)
            res[path]["LEFT"].add(old)
            old += 1
            new += 1
    return res


def checks():
    return load("checks.json", [])


def rollup():
    res = []
    for c in (checks() if isinstance(checks(), list) else []):
        state = c["state"]
        res.append({"__typename": "CheckRun", "name": c["name"], "workflowName": c.get("workflow", "CI"),
                    "status": "COMPLETED" if state in ("SUCCESS", "FAILURE", "SKIPPED") else "IN_PROGRESS",
                    "conclusion": state if state in ("SUCCESS", "FAILURE", "SKIPPED") else "",
                    "detailsUrl": c.get("link", "")})
    return res


def threads():
    return load("threads.json", [])


def graphql_login(login):
    return login[:-5] if login.endswith("[bot]") else login


def pr_url():
    return "https://github.com/%s/%s/pull/%d" % (PR["owner"], PR["repo"], PR["number"])


def pr_full():
    fs = files()
    cs = commits()
    return {
        "number": PR["number"], "title": PR["title"], "body": PR["body"], "state": PR.get("state", "OPEN"),
        "author": PR["author"], "labels": PR.get("labels", []), "isDraft": PR.get("isDraft", False),
        "baseRefName": base_ref(), "headRefName": PR["headRefName"], "headRefOid": head_sha(),
        "baseRefOid": git("merge-base", base_ref(), "HEAD").strip(), "url": pr_url(),
        "mergeable": PR.get("mergeable", "MERGEABLE"), "mergeStateStatus": PR.get("mergeStateStatus", "CLEAN"),
        "reviewDecision": PR.get("reviewDecision", "REVIEW_REQUIRED"),
        "files": fs, "changedFiles": len(fs), "additions": sum(f["additions"] for f in fs),
        "deletions": sum(f["deletions"] for f in fs), "commits": cs, "statusCheckRollup": rollup(),
        "createdAt": PR.get("createdAt"), "updatedAt": PR.get("updatedAt", PR.get("createdAt")),
        "reviews": load("reviews.json", []), "latestReviews": load("reviews.json", []),
        "comments": load("issue_comments.json", []), "isCrossRepository": False,
        "headRepositoryOwner": {"login": PR["owner"]}, "headRepository": {"name": PR["repo"]},
        "id": "PR_fixture_%d" % PR["number"], "closingIssuesReferences": PR.get("closingIssuesReferences", []),
        "reviewRequests": [], "assignees": [], "milestone": None, "maintainerCanModify": False,
    }


# ---------- argument helpers ----------

def take_flag(args, names, has_value=True):
    """Remove a flag from args; return its value (or True), else None."""
    i = 0
    while i < len(args):
        a = args[i]
        for n in names:
            if a == n:
                if has_value:
                    if i + 1 >= len(args):
                        sys.stderr.write("gh: flag needs an argument: %s\n" % n)
                        sys.exit(1)
                    v = args[i + 1]
                    del args[i:i + 2]
                    return v
                del args[i]
                return True
            if has_value and a.startswith(n + "="):
                del args[i]
                return a[len(n) + 1:]
        i += 1
    return None


def read_stdin():
    global STDIN_CACHE
    if STDIN_CACHE is None:
        STDIN_CACHE = sys.stdin.read()
    return STDIN_CACHE


def typed(v):
    if v.startswith("@"):
        if v == "@-":
            return read_stdin()
        with open(v[1:]) as f:
            return f.read()
    if v == "true":
        return True
    if v == "false":
        return False
    if v == "null":
        return None
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def set_field(body, key, value):
    """gh's nested key syntax: a[b]=1, a[]=1, a[][b]=1."""
    parts = re.findall(r"[^\[\]]+|\[\]", key.replace("][", "]\x00[").replace("\x00", ""))
    parts = []
    m = re.match(r"^([^\[]+)(.*)$", key)
    parts.append(m.group(1))
    for seg in re.findall(r"\[([^\]]*)\]", m.group(2)):
        parts.append(seg)
    cur = body
    for i, part in enumerate(parts):
        last = i == len(parts) - 1
        nxt = None if last else parts[i + 1]
        if part == "":
            # cur is a list
            if last:
                cur.append(value)
                return
            if nxt == "":
                cur.append([])
                cur = cur[-1]
            else:
                if not cur or not isinstance(cur[-1], dict) or nxt in cur[-1]:
                    cur.append({})
                cur = cur[-1]
        else:
            if last:
                cur[part] = value
                return
            if part not in cur:
                cur[part] = [] if nxt == "" else {}
            cur = cur[part]


def pr_number_ok(arg):
    if arg is None:
        return True
    m = re.search(r"(\d+)$", arg.rstrip("/"))
    if not m or int(m.group(1)) != PR["number"]:
        sys.stderr.write("GraphQL: Could not resolve to a PullRequest with the number of %s. (repository.pullRequest)\n" % arg)
        log("error", status=404, message="unknown pull request %s" % arg)
        sys.exit(1)
    return True


# ---------- writes ----------

VALID_EVENTS = ("APPROVE", "REQUEST_CHANGES", "COMMENT")


def validate_comment(c, dl, errors):
    path = c.get("path")
    if not path or not c.get("body"):
        errors.append("review comment needs path and body")
        return
    if path not in dl:
        errors.append("Path could not be resolved: %s is not part of the pull request diff" % path)
        return
    if c.get("subject_type") == "file":
        return
    line = c.get("line")
    if line is None:
        if c.get("position") is not None:
            return
        errors.append("review comment on %s needs a line" % path)
        return
    side = c.get("side", "RIGHT")
    if not isinstance(line, int) or line not in dl[path].get(side, set()):
        errors.append("Line could not be resolved: %s:%s (%s) is not part of the diff" % (path, line, side))
    sl = c.get("start_line")
    if sl is not None:
        sside = c.get("start_side", side)
        if not isinstance(sl, int) or sl >= line or sl not in dl[path].get(sside, set()):
            errors.append("Start line could not be resolved: %s:%s is not part of the diff or not before line" % (path, sl))


def my_pending(reviews):
    for r in reviews:
        if r["state"] == "PENDING" and r["user"]["login"] == PR["viewer"]:
            return r
    return None


def check_event(event, body, n_comments):
    if event not in VALID_EVENTS:
        http_error(422, "Unprocessable Entity", ["Variable event is invalid: %r is not one of APPROVE, REQUEST_CHANGES, COMMENT" % event])
    if PR["viewer"] == PR["author"]["login"] and event == "APPROVE":
        http_error(422, "Unprocessable Entity", ["Can not approve your own pull request"])
    if PR["viewer"] == PR["author"]["login"] and event == "REQUEST_CHANGES":
        http_error(422, "Unprocessable Entity", ["Can not request changes on your own pull request"])
    if event in ("REQUEST_CHANGES", "COMMENT") and not (body or "").strip() and n_comments == 0:
        http_error(422, "Unprocessable Entity", ["Body can't be blank"])


def post_review(body):
    reviews = load("reviews.json", [])
    if my_pending(reviews):
        http_error(422, "Unprocessable Entity", ["User can only have one pending review per pull request"])
    event = body.get("event")
    comments = body.get("comments") or []
    if not isinstance(comments, list):
        http_error(422, "Invalid request", ["comments must be an array"])
    errors = []
    dl = diff_lines()
    for c in comments:
        if not isinstance(c, dict):
            errors.append("each comment must be an object")
            continue
        validate_comment(c, dl, errors)
    if errors:
        http_error(422, "Unprocessable Entity", errors)
    if event is not None:
        check_event(event, body.get("body"), len(comments))
    if body.get("commit_id") and body["commit_id"] != head_sha():
        http_error(422, "Unprocessable Entity", ["commit_id is not the head of the pull request"])
    rid = 9000 + len(reviews) + 1
    state = {"APPROVE": "APPROVED", "REQUEST_CHANGES": "CHANGES_REQUESTED", "COMMENT": "COMMENTED", None: "PENDING"}[event]
    review = {"id": rid, "node_id": "PRR_fixture_%d" % rid, "user": {"login": PR["viewer"]}, "body": body.get("body") or "",
              "state": state, "commit_id": head_sha(), "html_url": pr_url() + "#pullrequestreview-%d" % rid,
              "comments": comments}
    reviews.append(review)
    save("reviews.json", reviews)
    log("review_created", review=review)
    return {k: v for k, v in review.items() if k != "comments"}


def submit_review(rid, body):
    reviews = load("reviews.json", [])
    for r in reviews:
        if r["id"] == rid:
            if r["state"] != "PENDING":
                http_error(422, "Unprocessable Entity", ["Review has already been submitted"])
            event = body.get("event")
            if event is None:
                http_error(422, "Unprocessable Entity", ["event is required"])
            text = body.get("body") if body.get("body") is not None else r["body"]
            check_event(event, text, len(r["comments"]))
            r["state"] = {"APPROVE": "APPROVED", "REQUEST_CHANGES": "CHANGES_REQUESTED", "COMMENT": "COMMENTED"}[event]
            r["body"] = text or ""
            save("reviews.json", reviews)
            log("review_submitted", review=r)
            return {k: v for k, v in r.items() if k != "comments"}
    http_error(404, "Not Found")


def reply_to_comment(cid, text):
    ths = threads()
    for t in ths:
        for c in t["comments"]["nodes"]:
            if c["databaseId"] == cid:
                new = {"databaseId": 70000 + sum(len(x["comments"]["nodes"]) for x in ths), "body": text,
                       "author": {"login": PR["viewer"]}, "authorAssociation": "MEMBER",
                       "createdAt": PR.get("now", "2026-10-04T12:00:00Z"), "reactions": {"nodes": []}}
                t["comments"]["nodes"].append(new)
                save("threads.json", ths)
                log("thread_reply", thread=t["id"], in_reply_to=cid, body=text, thread_was_resolved=t["isResolved"])
                return {"id": new["databaseId"], "body": text, "in_reply_to_id": cid}
    http_error(404, "Not Found")


def rest_comments():
    res = []
    for t in threads():
        first = None
        for c in t["comments"]["nodes"]:
            res.append({"id": c["databaseId"], "path": t["path"], "line": t.get("line"), "original_line": t.get("originalLine"),
                        "body": c["body"], "user": {"login": c["author"]["login"]}, "author_association": c.get("authorAssociation"),
                        "created_at": c["createdAt"], "in_reply_to_id": first, "pull_request_review_id": None})
            if first is None:
                first = c["databaseId"]
    return res


# ---------- gh api ----------

def graphql(body):
    q = body.get("query", "")
    if not q:
        http_error(400, "A query attribute must be specified and must be a string.")
    variables = {k: v for k, v in body.items() if k != "query"}
    if isinstance(body.get("variables"), dict):
        variables.update(body["variables"])
    is_mutation = bool(re.match(r"\s*mutation\b", q))
    if is_mutation:
        m = re.search(r"\b(resolveReviewThread|unresolveReviewThread)\b", q)
        if m:
            tid = variables.get("threadId") or variables.get("id")
            if not tid:
                mm = re.search(r'threadId:\s*"([^"]+)"', q)
                tid = mm.group(1) if mm else None
            ths = threads()
            for t in ths:
                if t["id"] == tid:
                    was = t["isResolved"]
                    t["isResolved"] = m.group(1) == "resolveReviewThread"
                    t["resolvedBy"] = {"login": PR["viewer"]} if t["isResolved"] else None
                    save("threads.json", ths)
                    log(m.group(1), thread=tid, was_resolved=was, first_author=t["comments"]["nodes"][0]["author"]["login"])
                    return {"data": {m.group(1): {"thread": {"id": tid, "isResolved": t["isResolved"]}}}}
            http_error(404, "Could not resolve to a node with the global id of '%s'" % tid)
        if re.search(r"\baddPullRequestReview\b", q):
            payload = {"event": variables.get("event"), "body": variables.get("body"), "comments": []}
            for th in variables.get("threads") or variables.get("comments") or []:
                payload["comments"].append({"path": th.get("path"), "line": th.get("line"), "side": th.get("side", "RIGHT"),
                                            "start_line": th.get("startLine"), "body": th.get("body")})
            if payload["event"] == "PENDING":
                payload["event"] = None
            r = post_review(payload)
            return {"data": {"addPullRequestReview": {"pullRequestReview": {"id": r["node_id"], "databaseId": r["id"], "state": r["state"], "url": r["html_url"]}}}}
        if re.search(r"\baddPullRequestReviewThread\b", q):
            reviews = load("reviews.json", [])
            pend = my_pending(reviews)
            if not pend:
                http_error(422, "Unprocessable Entity", ["No pending review to add a thread to"])
            c = {"path": variables.get("path"), "line": variables.get("line"), "side": variables.get("side", "RIGHT"),
                 "start_line": variables.get("startLine"), "body": variables.get("body")}
            errors = []
            validate_comment(c, diff_lines(), errors)
            if errors:
                http_error(422, "Unprocessable Entity", errors)
            pend["comments"].append(c)
            save("reviews.json", reviews)
            log("pending_comment_added", comment=c)
            return {"data": {"addPullRequestReviewThread": {"thread": {"id": "PRRT_new_%d" % len(pend["comments"])}}}}
        if re.search(r"\bsubmitPullRequestReview\b", q):
            pend = my_pending(load("reviews.json", []))
            if not pend:
                http_error(422, "Unprocessable Entity", ["No pending review"])
            r = submit_review(pend["id"], {"event": variables.get("event"), "body": variables.get("body")})
            return {"data": {"submitPullRequestReview": {"pullRequestReview": {"id": r["node_id"], "state": r["state"]}}}}
        log("graphql_mutation_unsupported", query=q, variables=variables)
        http_error(400, "This fixture does not support that GraphQL mutation; supported: addPullRequestReview, addPullRequestReviewThread, submitPullRequestReview, resolveReviewThread, unresolveReviewThread")
    log("graphql_query", query=q, variables=variables)
    data = {}
    if re.search(r"\bviewer\b", q):
        data["viewer"] = {"login": graphql_login(PR["viewer"])}
    if re.search(r"\brepository\b", q):
        full = pr_full()
        prd = dict(full)
        nodes = threads()
        for t in nodes:
            # GraphQL reports a bot's login without the "[bot]" suffix that REST adds.
            for c in t["comments"]["nodes"]:
                c["author"]["login"] = graphql_login(c["author"]["login"])
            if t.get("resolvedBy"):
                t["resolvedBy"]["login"] = graphql_login(t["resolvedBy"]["login"])
        prd["reviewThreads"] = {"totalCount": len(nodes), "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": nodes}
        prd["commits"] = {"totalCount": len(full["commits"]), "pageInfo": {"hasNextPage": False, "endCursor": None},
                          "nodes": [{"commit": {"oid": c["oid"], "committedDate": c["committedDate"], "messageHeadline": c["messageHeadline"]}} for c in full["commits"]]}
        prd["reviews"] = {"totalCount": len(full["reviews"]), "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": full["reviews"]}
        prd["comments"] = {"totalCount": len(full["comments"]), "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": full["comments"]}
        prd["files"] = {"totalCount": len(full["files"]), "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": full["files"]}
        prd["labels"] = {"nodes": full["labels"]}
        data["repository"] = {"pullRequest": prd, "owner": {"login": PR["owner"]}, "name": PR["repo"]}
    return {"data": data}


def api(args):
    method = take_flag(args, ["-X", "--method"])
    jq = take_flag(args, ["--jq", "-q"])
    take_flag(args, ["--paginate"], has_value=False)
    take_flag(args, ["--slurp"], has_value=False)
    take_flag(args, ["--silent"], has_value=False)
    take_flag(args, ["-i", "--include"], has_value=False)
    take_flag(args, ["--hostname"])
    take_flag(args, ["-R", "--repo"])
    raw = False
    while True:
        h = take_flag(args, ["-H", "--header"])
        if h is None:
            break
        raw = raw or "raw" in h.lower()
    inp = take_flag(args, ["--input"])
    body = {}
    had_fields = False
    while True:
        v = take_flag(args, ["-f", "--raw-field"])
        if v is None:
            break
        had_fields = True
        k, _, val = v.partition("=")
        set_field(body, k, val)
    while True:
        v = take_flag(args, ["-F", "--field"])
        if v is None:
            break
        had_fields = True
        k, _, val = v.partition("=")
        set_field(body, k, typed(val))
    if inp is not None:
        raw = read_stdin() if inp == "-" else open(inp).read()
        try:
            body = json.loads(raw)
        except ValueError:
            http_error(400, "Problems parsing JSON")
        had_fields = True
    if not args:
        sys.stderr.write("gh api: endpoint required\n")
        sys.exit(1)
    ep = args[0].strip("/")
    ep = ep.replace("{owner}", PR["owner"]).replace("{repo}", PR["repo"]).replace(":owner", PR["owner"]).replace(":repo", PR["repo"])
    ep, _, _query = ep.partition("?")
    if method is None:
        method = "POST" if had_fields else "GET"
    method = method.upper()

    if ep == "graphql":
        res = graphql(body)
        return out(res, jq)
    if ep == "user":
        if PR["viewer"].endswith("[bot]"):
            # An installation token cannot call GET /user.
            http_error(403, "Resource not accessible by integration")
        return out({"login": PR["viewer"]}, jq)
    prefix = "repos/%s/%s" % (PR["owner"], PR["repo"])
    if not ep.lower().startswith(prefix.lower()):
        log("unsupported", endpoint=ep, method=method)
        http_error(404, "Not Found")
    rest = ep[len(prefix):].strip("/")
    n = str(PR["number"])

    if rest == "" and method == "GET":
        return out({"name": PR["repo"], "owner": {"login": PR["owner"]}, "full_name": PR["owner"] + "/" + PR["repo"], "default_branch": base_ref()}, jq)
    if rest == "pulls/" + n and method == "GET":
        full = pr_full()
        return out({"number": full["number"], "title": full["title"], "body": full["body"], "state": "open", "draft": full["isDraft"],
                    "user": {"login": full["author"]["login"]}, "head": {"sha": full["headRefOid"], "ref": full["headRefName"]},
                    "base": {"sha": full["baseRefOid"], "ref": full["baseRefName"]}, "html_url": full["url"],
                    "labels": full["labels"], "commits": len(full["commits"]), "changed_files": full["changedFiles"],
                    "additions": full["additions"], "deletions": full["deletions"], "mergeable": True}, jq)
    if rest == "pulls/" + n + "/files" and method == "GET":
        res = []
        names = {"A": "added", "D": "removed", "M": "modified", "R": "renamed"}
        for row in git("diff", "--name-status", "-M", base_ref() + "...HEAD").splitlines():
            parts = row.split("\t")
            path, prev = parts[-1], (parts[1] if parts[0].startswith("R") else None)
            stat = git("diff", "--numstat", "-M", base_ref() + "...HEAD", "--", path).split("\t")
            entry = {"filename": path, "status": names.get(parts[0][0], "modified"),
                     "additions": int(stat[0]) if stat and stat[0].isdigit() else 0,
                     "deletions": int(stat[1]) if len(stat) > 1 and stat[1].isdigit() else 0}
            if prev:
                entry["previous_filename"] = prev
            res.append(entry)
        return out(res, jq)
    if rest == "pulls/" + n + "/commits" and method == "GET":
        return out([{"sha": c["oid"], "commit": {"message": c["messageHeadline"], "committer": {"date": c["committedDate"]}, "author": {"date": c["authoredDate"]}}} for c in commits()], jq)
    if rest == "pulls/" + n + "/reviews":
        if method == "GET":
            return out([{k: v for k, v in r.items() if k != "comments"} for r in load("reviews.json", [])], jq)
        if method == "POST":
            return out(post_review(body), jq)
    m = re.fullmatch(r"pulls/%s/reviews/(\d+)(/events|/comments|/dismissals)?" % n, rest)
    if m:
        rid = int(m.group(1))
        tail = m.group(2)
        reviews = load("reviews.json", [])
        target = next((r for r in reviews if r["id"] == rid), None)
        if target is None:
            http_error(404, "Not Found")
        if tail == "/events" and method == "POST":
            return out(submit_review(rid, body), jq)
        if tail == "/comments":
            if method == "GET":
                return out(target["comments"], jq)
            # The REST API has no endpoint that adds a comment to an existing review.
            log("unsupported", endpoint=ep, method=method, note="REST cannot add comments to an existing review")
            http_error(404, "Not Found")
        if tail is None and method == "DELETE":
            if target["state"] != "PENDING":
                http_error(422, "Unprocessable Entity", ["Can not delete a non-pending pull request review"])
            reviews.remove(target)
            save("reviews.json", reviews)
            log("review_deleted", review=target)
            return out({k: v for k, v in target.items() if k != "comments"}, jq)
        if tail is None and method == "PUT":
            target["body"] = body.get("body", target["body"])
            save("reviews.json", reviews)
            log("review_updated", review=target)
            return out({k: v for k, v in target.items() if k != "comments"}, jq)
        if tail is None and method == "GET":
            return out({k: v for k, v in target.items() if k != "comments"}, jq)
        if tail == "/dismissals":
            target["state"] = "DISMISSED"
            save("reviews.json", reviews)
            log("review_dismissed", review=target, message=body.get("message"))
            return out({"id": rid, "state": "DISMISSED"}, jq)
    if rest == "pulls/" + n + "/comments":
        if method == "GET":
            return out(rest_comments(), jq)
        if method == "POST":
            if my_pending(load("reviews.json", [])):
                http_error(422, "Unprocessable Entity", ["user_id can only have one pending review per pull request"])
            if body.get("in_reply_to"):
                return out(reply_to_comment(int(body["in_reply_to"]), body.get("body", "")), jq)
            errors = []
            validate_comment(body, diff_lines(), errors)
            if errors:
                http_error(422, "Unprocessable Entity", errors)
            log("standalone_review_comment", comment=body)
            return out({"id": 81000, "path": body.get("path"), "line": body.get("line"), "body": body.get("body")}, jq)
    m = re.fullmatch(r"pulls/%s/comments/(\d+)/replies" % n, rest)
    if m and method == "POST":
        return out(reply_to_comment(int(m.group(1)), body.get("body", "")), jq)
    m = re.fullmatch(r"pulls/comments/(\d+)", rest)
    if m and method == "GET":
        for c in rest_comments():
            if c["id"] == int(m.group(1)):
                return out(c, jq)
        http_error(404, "Not Found")
    if rest == "issues/" + n + "/comments":
        ics = load("issue_comments.json", [])
        if method == "GET":
            return out(ics, jq)
        if method == "POST":
            ics.append({"id": 60000 + len(ics), "body": body.get("body", ""), "user": {"login": PR["viewer"]}, "author": {"login": PR["viewer"]}})
            save("issue_comments.json", ics)
            log("issue_comment", body=body.get("body", ""))
            return out(ics[-1], jq)
    m = re.fullmatch(r"commits/([0-9a-fA-F]{6,40})(/check-runs|/status|/check-suites)?", rest)
    if m and method == "GET":
        sha = git("rev-parse", "--verify", "--quiet", m.group(1) + "^{commit}").strip()
        if not sha:
            http_error(422, "No commit found for SHA: " + m.group(1))
        if m.group(2) == "/check-runs":
            return out({"total_count": len(checks()), "check_runs": [{"name": c["name"], "status": r["status"].lower(), "conclusion": (r["conclusion"] or None) and r["conclusion"].lower()} for c, r in zip(checks(), rollup())]}, jq)
        if m.group(2):
            states = {c["state"] for c in checks()}
            state = "failure" if "FAILURE" in states else "pending" if states - {"SUCCESS", "SKIPPED"} else "success"
            return out({"state": state, "statuses": [], "total_count": 0}, jq)
        fl = []
        for line in git("show", "--numstat", "--format=", sha).splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            patch = git("show", "--format=", sha, "--", parts[2])
            patch = patch[patch.find("@@"):] if "@@" in patch else ""
            fl.append({"filename": parts[2], "additions": int(parts[0]) if parts[0].isdigit() else 0,
                       "deletions": int(parts[1]) if parts[1].isdigit() else 0, "patch": patch})
        meta = git("show", "-s", "--format=%s%x1f%cI%x1f%aI", sha).strip().split("\x1f")
        return out({"sha": sha, "commit": {"message": meta[0], "committer": {"date": meta[1]}, "author": {"date": meta[2]}},
                    "author": {"login": PR["author"]["login"]}, "files": fl}, jq)
    m = re.fullmatch(r"contents/(.+)", rest)
    if m and method == "GET":
        ref = dict(kv.split("=", 1) for kv in _query.split("&") if "=" in kv).get("ref", base_ref())
        p = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (ref, m.group(1))], capture_output=True)
        if p.returncode != 0:
            log("read_miss", path=m.group(1), ref=ref)
            sys.stdout.write(json.dumps({"message": "Not Found", "status": "404"}) + "\n")
            sys.stderr.write("gh: Not Found (HTTP 404)\n")
            sys.exit(1)
        if raw:
            sys.stdout.write(p.stdout.decode(errors="replace"))
            return
        import base64
        return out({"path": m.group(1), "encoding": "base64", "content": base64.b64encode(p.stdout).decode()}, jq)
    log("unsupported", endpoint=ep, method=method)
    http_error(404, "Not Found")


# ---------- gh pr / repo / auth ----------

def pr_cmd(args):
    if not args:
        sys.stderr.write("gh pr: subcommand required\n")
        sys.exit(1)
    sub, args = args[0], args[1:]
    take_flag(args, ["-R", "--repo"])
    jq = take_flag(args, ["--jq", "-q"])
    if sub == "view":
        fields = take_flag(args, ["--json"])
        take_flag(args, ["--comments", "-c"], has_value=False)
        pr_number_ok(args[0] if args else None)
        full = pr_full()
        if fields is None:
            return out("title:\t%s\nstate:\t%s\nauthor:\t%s\nlabels:\t%s\nnumber:\t%d\nurl:\t%s\nadditions:\t%d\ndeletions:\t%d\n--\n%s" % (
                full["title"], "DRAFT" if full["isDraft"] else full["state"], full["author"]["login"],
                ", ".join(l["name"] for l in full["labels"]), full["number"], full["url"], full["additions"], full["deletions"], full["body"]))
        sel = {}
        for f in fields.split(","):
            f = f.strip()
            if f not in full:
                sys.stderr.write('Unknown JSON field: "%s"\nAvailable fields:\n  %s\n' % (f, "\n  ".join(sorted(full))))
                sys.exit(1)
            sel[f] = full[f]
        return out(sel, jq)
    if sub == "diff":
        name_only = take_flag(args, ["--name-only"], has_value=False)
        take_flag(args, ["--patch"], has_value=False)
        take_flag(args, ["--color"])
        pr_number_ok(args[0] if args else None)
        if name_only:
            return out("\n".join(f["path"] for f in files()))
        sys.stdout.write(diff_text())
        return
    if sub == "checks":
        fields = take_flag(args, ["--json"])
        take_flag(args, ["--watch"], has_value=False)
        take_flag(args, ["--required"], has_value=False)
        pr_number_ok(args[0] if args else None)
        cs = checks()
        if isinstance(cs, dict):
            # A fixture can make the checks call fail, as it does for a token without checks:read.
            sys.stderr.write("GraphQL: Resource not accessible by integration (HTTP 403)\n")
            sys.exit(1)
        if not cs:
            sys.stderr.write("no checks reported on the '%s' branch\n" % PR["headRefName"])
            sys.exit(1)
        bucket = {"SUCCESS": "pass", "FAILURE": "fail", "SKIPPED": "skipping", "PENDING": "pending", "IN_PROGRESS": "pending", "QUEUED": "pending"}
        if fields is not None:
            rows = [{"name": c["name"], "state": c["state"], "bucket": bucket[c["state"]], "link": c.get("link", ""),
                     "workflow": c.get("workflow", "CI"), "description": "", "event": "pull_request",
                     "startedAt": c.get("startedAt", ""), "completedAt": c.get("completedAt", "")} for c in cs]
            out([{k: r[k] for k in fields.split(",") if k.strip() in r} for r in rows], jq)
        elif not cs:
            sys.stderr.write("no checks reported on the '%s' branch\n" % PR["headRefName"])
            sys.exit(1)
        else:
            out("\n".join("%s\t%s\t%s\t%s" % (c["name"], bucket[c["state"]], c.get("elapsed", "1m2s"), c.get("link", "")) for c in cs))
        states = {bucket[c["state"]] for c in cs}
        sys.exit(1 if "fail" in states else 8 if "pending" in states else 0)
    if sub == "review":
        event = None
        if take_flag(args, ["--approve", "-a"], has_value=False):
            event = "APPROVE"
        if take_flag(args, ["--request-changes", "-r"], has_value=False):
            event = "REQUEST_CHANGES"
        if take_flag(args, ["--comment", "-c"], has_value=False):
            event = "COMMENT"
        text = take_flag(args, ["--body", "-b"])
        bf = take_flag(args, ["--body-file", "-F"])
        if bf is not None:
            text = read_stdin() if bf == "-" else open(bf).read()
        pr_number_ok(args[0] if args else None)
        if event is None:
            sys.stderr.write("--approve, --request-changes, or --comment required when not running interactively\n")
            sys.exit(1)
        if event in ("REQUEST_CHANGES", "COMMENT") and not (text or "").strip():
            sys.stderr.write("body cannot be blank for %s review\n" % ("request-changes" if event == "REQUEST_CHANGES" else "comment"))
            sys.exit(1)
        pend = my_pending(load("reviews.json", []))
        if pend:
            submit_review(pend["id"], {"event": event, "body": text})
        else:
            # gh prints the API error without a JSON body for this command
            post_review({"event": event, "body": text or ""})
        return
    if sub == "comment":
        text = take_flag(args, ["--body", "-b"])
        bf = take_flag(args, ["--body-file", "-F"])
        if bf is not None:
            text = read_stdin() if bf == "-" else open(bf).read()
        pr_number_ok(args[0] if args else None)
        ics = load("issue_comments.json", [])
        ics.append({"id": 60000 + len(ics), "body": text or "", "user": {"login": PR["viewer"]}, "author": {"login": PR["viewer"]}})
        save("issue_comments.json", ics)
        log("issue_comment", body=text or "")
        return out(pr_url() + "#issuecomment-%d" % ics[-1]["id"])
    if sub in ("list", "status"):
        return out("%d\t%s\t%s\tOPEN" % (PR["number"], PR["title"], PR["headRefName"]))
    if sub in ("checkout", "merge", "close", "ready", "edit", "create", "reopen"):
        log("refused", sub=sub)
        sys.stderr.write("gh pr %s: not permitted for this token (read and review access only)\n" % sub)
        sys.exit(1)
    sys.stderr.write('unknown command "%s" for "gh pr"\n' % sub)
    sys.exit(1)


def main():
    args = list(ARGV)
    if not args or args[0] in ("--version", "version"):
        return out("gh version 2.90.0 (2026-04-16)\nhttps://github.com/cli/cli/releases/tag/v2.90.0")
    cmd, rest = args[0], args[1:]
    if cmd != "api" or (rest and "graphql" not in rest):
        log("call")
    if cmd == "api":
        return api(rest)
    if cmd == "pr":
        return pr_cmd(rest)
    if cmd == "repo" and rest and rest[0] == "view":
        rest = rest[1:]
        jq = take_flag(rest, ["--jq", "-q"])
        fields = take_flag(rest, ["--json"])
        full = {"owner": {"login": PR["owner"], "id": "O_fixture"}, "name": PR["repo"], "nameWithOwner": PR["owner"] + "/" + PR["repo"],
                "defaultBranchRef": {"name": base_ref()}, "url": "https://github.com/%s/%s" % (PR["owner"], PR["repo"]),
                "isPrivate": True, "viewerPermission": PR.get("viewerPermission", "WRITE")}
        if fields is None:
            return out("name:\t%s\ndescription:\tfixture" % full["nameWithOwner"])
        return out({f.strip(): full[f.strip()] for f in fields.split(",") if f.strip() in full}, jq)
    if cmd == "auth":
        if rest and rest[0] == "status":
            return out("github.com\n  ✓ Logged in to github.com account %s (keyring)\n  - Active account: true\n  - Git operations protocol: https\n  - Token scopes: 'repo', 'read:org'" % PR["viewer"])
        if rest and rest[0] == "token":
            return out("gho_fixture_token_not_real")
    if cmd == "issue" and rest and rest[0] == "view":
        sys.stderr.write("GraphQL: Could not resolve to an issue or pull request with that number.\n")
        sys.exit(1)
    log("unsupported", cmd=cmd)
    sys.stderr.write('gh: "%s" is not available in this environment\n' % " ".join(ARGV[:2]))
    sys.exit(1)


main()
