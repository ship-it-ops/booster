# Two reviews in the default format

These show tone and proportion for a plain "review this" with no other instructions. When a caller asks for another format, use theirs.

## A change with real problems

The request: "Review my branch before I open the pull request." The branch adds retry to a webhook sender. The project's `CONTRIBUTING.md` says delivery functions return a `DeliveryResult` and never raise, and `ruff` is configured.

```diff
@@ notify/webhooks.py
 34  def deliver(client, endpoint, event):
 35 -    response = client.post(endpoint.url, json=event.payload)
 36 -    return DeliveryResult(ok=response.status < 300, status=response.status)
 35 +    for attempt in range(MAX_ATTEMPTS):
 36 +        try:
 37 +            response = client.post(endpoint.url, json=event.payload)
 38 +        except Exception:
 39 +            continue
 40 +        if response.status < 500:
 41 +            break
 42 +        time.sleep(2 ** attempt)
 43 +    return DeliveryResult(ok=response.status < 300, status=response.status)
```

The review:

> Not ready: when every attempt fails to connect, `deliver` raises instead of returning a result. One thing must be fixed, two should be, and one is yours to decide.
>
> **must-fix**
>
> - `notify/webhooks.py:43` — if `client.post` raises on every attempt, `response` is never assigned and line 43 raises `UnboundLocalError`. Its caller, `dispatch_pending` (`notify/queue.py:61`), relies on `deliver` never raising and would stop processing the rest of the batch. Traced by reading both functions; nothing was run. Return `DeliveryResult(ok=False, status=None)` after the loop when no response was received.
>
> **should-fix**
>
> - `notify/webhooks.py:37` — a timeout after the receiver has already processed the request is retried with an identical body, so the receiver sees the event twice. Nothing in the payload lets it tell (I read `Event.payload` in `notify/events.py:12-30`: no id). Send the existing `event.id` as an idempotency header, or retry only on connection errors raised before the request was sent.
> - `notify/webhooks.py:38-39` — `except Exception: continue` retries on everything, including a `TypeError` from a payload that cannot be serialised, which will fail the same way each time, and it skips the back-off on line 42, so connection failures retry immediately. Catch the client's transport error, and sleep before the next attempt.
>
> **consider**
>
> - `notify/webhooks.py:42` — `time.sleep` blocks the worker for several seconds per failing endpoint. Fine if this runs in the queue worker only; worth a comment saying so.
>
> Already there, not part of this change: `dispatch_pending` marks an event as sent before calling `deliver` (`notify/queue.py:58`), so a crash in between loses it. Worth its own fix.
>
> Read `git diff main...HEAD` (one file) and the two functions named above; judged against `CONTRIBUTING.md`; nothing was run.

What to notice: the opening answers the question that was asked. Each finding says what happens, to whom, and how it was confirmed, and the confirmation here is reading, said plainly. Severity follows the consequence: the crash is certain on a reachable path, while the duplicate delivery needs a timeout at the wrong moment. The review covers the change; the one older problem is a single labelled line, not a finding. Nothing is said about names, the loop's shape or the literal `2`, because nothing there would mislead anyone.

## A file with nothing wrong

The request: "Can you review `ratelimit.py`?"

```python
 1  """Fixed-window rate limiter backed by the shared cache."""
 2  WINDOW_SECONDS = 60
 3
 4
 5  def allow(cache, clock, key, limit):
 6      """Return True if `key` may make another request in the current window."""
 7      window = int(clock.now().timestamp()) // WINDOW_SECONDS
 8      counter_key = f"rl:{key}:{window}"
 9      count = cache.incr(counter_key)
10      if count == 1:
11          cache.expire(counter_key, WINDOW_SECONDS * 2)
12      return count <= limit
```

The review:

> I found nothing that needs changing. I read `ratelimit.py`, its two callers in `api/middleware.py` and `tests/test_ratelimit.py`, and ran that test file.
>
> One thing to know, not to fix: `incr` followed by `expire` is two cache calls, so a process that dies between them leaves a counter with no expiry. The key contains the window number, so such a counter is never read again and only costs memory; the design already makes that harmless.

What to notice: no invented findings, no praise section, and no "consider" items added to fill space. The one remark is there because a careful reader would wonder about it; a review with no remark at all would be just as right.
