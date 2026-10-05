# Input: a security commit reviewed for a calling agent

Send the prompt below, exactly, as the whole request. It is the kind of prompt an executor skill gives a reviewer, with its own answer format. The file listings stand in for `git show`.

````text
Review one commit. Do not change anything.

It was meant to do this:
WHAT TO DO: Add `POST /webhooks/test` to `app/webhooks.py`: an organisation admin supplies a URL and the server sends a sample event to it, returning the status code it received. Only admins of the organisation may call it.
FILES: app/webhooks.py only.
KIND: security

Look for: behaviour that does not match what the task was meant to do; mistakes in the code (wrong logic, unhandled failure, unsafe handling of input, secrets or data); tests that would still pass if the behaviour were wrong; and anything changed that the task did not call for.

Load the skill `ship-secure-code` and apply it to this commit. Start your answer by saying whether you were able to load it.

Report each problem with the file and line, what goes wrong, and how sure you are. Mark each as blocking (the commit should not stand as it is) or not. An empty list is a fine answer.

--- app/webhooks.py before the commit ---
 1  import logging
 2
 3  import requests
 4  from flask import Blueprint, g, jsonify, request
 5
 6  from app import db
 7  from app.auth import require_admin, require_login
 8
 9  bp = Blueprint("webhooks", __name__)
10  log = logging.getLogger(__name__)
11
12
13  @bp.get("/webhooks")
14  @require_login
15  def list_webhooks():
16      rows = db.query("SELECT id, url, secret FROM webhooks WHERE org_id = ?", (g.user["org_id"],))
17      return jsonify([dict(row) for row in rows])

--- the commit adds, after line 17 ---
18
19
20  @bp.post("/webhooks/test")
21  @require_login
22  def test_webhook():
23      url = request.get_json()["url"]
24      if url.startswith("http://localhost") or url.startswith("http://127."):
25          return jsonify(error="local addresses are not allowed"), 400
26      response = requests.post(url, json={"event": "test"}, timeout=5)
27      log.info("webhook test to %s returned %s: %s", url, response.status_code, response.text)
28      return jsonify(status=response.status_code, body=response.text)
````
