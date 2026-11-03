"""Parse durations such as "1h30m" into seconds."""
import re

UNIT_SECONDS = {"h": 3600, "m": 60, "s": 1}
_PART = re.compile(r"(\d+)([hms])")


class InvalidDuration(ValueError):
    pass


def parse_duration(text):
    """Return the number of seconds in `text`, e.g. "1h30m" -> 5400.

    Units are h, m and s, each at most once and in that order. Anything else raises InvalidDuration.
    """
    parts = _PART.findall(text)
    if not parts or "".join(number + unit for number, unit in parts) != text:
        raise InvalidDuration(text)
    units = [unit for _, unit in parts]
    if units != sorted(set(units), key="hms".index):
        raise InvalidDuration(text)
    return sum(int(number) * UNIT_SECONDS[unit] for number, unit in parts)
