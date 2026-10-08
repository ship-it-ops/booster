from datetime import datetime, timezone


def now():
    """The current time, in UTC. Tests replace this function."""
    return datetime.now(timezone.utc)
