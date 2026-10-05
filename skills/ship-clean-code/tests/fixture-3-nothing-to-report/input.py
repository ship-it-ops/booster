"""Cursor pagination for list endpoints."""
import base64
import json

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


class InvalidCursor(ValueError):
    pass


def encode_cursor(last_id):
    raw = json.dumps({"after": last_id}).encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(cursor):
    """Return the id to start after, or None for the first page."""
    if cursor is None:
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        after = payload["after"]
    except (ValueError, KeyError, TypeError) as error:
        raise InvalidCursor(cursor) from error
    if not isinstance(after, int) or isinstance(after, bool):
        raise InvalidCursor(cursor)
    return after


def paginate(rows, cursor=None, page_size=DEFAULT_PAGE_SIZE, include_total=False):
    """Return one page of `rows`, which must be sorted by ascending integer `id`.

    `page_size` is clamped to 1..MAX_PAGE_SIZE. `next_cursor` is None on the last page.
    """
    size = max(1, min(page_size, MAX_PAGE_SIZE))
    after = decode_cursor(cursor)
    remaining = [row for row in rows if after is None or row["id"] > after]
    page = remaining[:size]
    has_more = len(remaining) > size
    result = {
        "items": page,
        "next_cursor": encode_cursor(page[-1]["id"]) if has_more else None,
    }
    if include_total:
        result["total"] = len(rows)
    return result
