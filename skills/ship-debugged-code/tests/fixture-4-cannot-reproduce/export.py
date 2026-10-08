import logging
from datetime import date, datetime, timedelta, timezone

log = logging.getLogger("export")


def yesterday_range():
    """The UTC range covering yesterday."""
    day = date.today() - timedelta(days=1)
    start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


def fetch_rows(db, start, end):
    try:
        return db.query("SELECT * FROM orders WHERE created_at >= %s AND created_at < %s", (start, end), timeout=30)
    except TimeoutError:
        return []


def run(db, out):
    start, end = yesterday_range()
    rows = fetch_rows(db, start, end)
    for row in rows:
        out.write(",".join(str(v) for v in row) + "\n")
    log.info("export finished")
