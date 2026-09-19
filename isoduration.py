"""ISO 8601 duration parsing and datetime arithmetic (stdlib only)."""

import calendar
import re
from datetime import datetime, timedelta

_DURATION_RE = re.compile(
    r"^(?P<sign>[+-])?P"
    r"(?:(?P<years>\d+(?:[.,]\d+)?)Y)?"
    r"(?:(?P<months>\d+(?:[.,]\d+)?)M)?"
    r"(?:(?P<weeks>\d+(?:[.,]\d+)?)W)?"
    r"(?:(?P<days>\d+(?:[.,]\d+)?)D)?"
    r"(?:T"
    r"(?:(?P<hours>\d+(?:[.,]\d+)?)H)?"
    r"(?:(?P<minutes>\d+(?:[.,]\d+)?)M)?"
    r"(?:(?P<seconds>\d+(?:[.,]\d+)?)S)?"
    r")?$"
)

_ORDER = ("years", "months", "weeks", "days", "hours", "minutes", "seconds")


class DurationError(ValueError):
    """Raised when a string is not a valid ISO 8601 duration."""


class Duration:
    """An ISO 8601 duration: calendar part (years/months) + clock part."""

    def __init__(self, years=0, months=0, weeks=0, days=0,
                 hours=0, minutes=0, seconds=0):
        self.years = years
        self.months = months
        self.weeks = weeks
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

    @classmethod
    def parse(cls, text):
        if not isinstance(text, str):
            raise DurationError("duration must be a string")
        m = _DURATION_RE.match(text)
        if not m:
            raise DurationError("invalid ISO 8601 duration: %r" % text)
        raw = m.groupdict()
        sign = -1 if raw.pop("sign") == "-" else 1
        if all(v is None for v in raw.values()):
            raise DurationError("duration has no components: %r" % text)
        values = {}
        seen_fraction = False
        for name in _ORDER:
            v = raw[name]
            if v is None:
                values[name] = 0
                continue
            v = v.replace(",", ".")
            if "." in v:
                if seen_fraction:
                    raise DurationError(
                        "fraction only allowed on smallest unit: %r" % text)
                seen_fraction = True
                values[name] = float(v)
            else:
                if seen_fraction:
                    raise DurationError(
                        "fraction only allowed on smallest unit: %r" % text)
                values[name] = int(v)
        for name in _ORDER:
            if name != "seconds" and isinstance(values[name], float):
                raise DurationError(
                    "fraction only supported on seconds: %r" % text)
        d = cls(**{name: values[name] for name in _ORDER})
        return -d if sign < 0 else d

    def __neg__(self):
        return Duration(-self.years, -self.months, -self.weeks, -self.days,
                        -self.hours, -self.minutes, -self.seconds)

    def __eq__(self, other):
        return isinstance(other, Duration) and vars(self) == vars(other)

    def __repr__(self):
        return "Duration(%r, %r, %r, %r, %r, %r, %r)" % (
            self.years, self.months, self.weeks, self.days,
            self.hours, self.minutes, self.seconds)

    def _clock_delta(self):
        return timedelta(weeks=self.weeks, days=self.days, hours=self.hours,
                         minutes=self.minutes, seconds=self.seconds)


def parse_duration(text):
    """Parse an ISO 8601 duration string into a Duration."""
    return Duration.parse(text)


def _add_months(dt, months):
    total = dt.year * 12 + (dt.month - 1) + months
    year, month0 = divmod(total, 12)
    month = month0 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def add_duration(dt, duration):
    """Add a Duration (or ISO 8601 string) to a datetime.

    Years/months are applied first with month-end clamping, then the
    week/day/time part. tzinfo is preserved.
    """
    if isinstance(duration, str):
        duration = parse_duration(duration)
    if not isinstance(dt, datetime):
        raise TypeError("add_duration requires a datetime")
    dt = _add_months(dt, duration.years * 12 + duration.months)
    return dt + duration._clock_delta()


def sub_duration(dt, duration):
    """Subtract a Duration (or ISO 8601 string) from a datetime."""
    if isinstance(duration, str):
        duration = parse_duration(duration)
    return add_duration(dt, -duration)
