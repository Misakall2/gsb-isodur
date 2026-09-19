"""ISO 8601 duration parsing and datetime arithmetic (stdlib only)."""

import re
from calendar import monthrange
from dataclasses import dataclass
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


class DurationParseError(ValueError):
    """Raised when a string is not a valid ISO 8601 duration."""


@dataclass(frozen=True)
class Duration:
    """An ISO 8601 duration.

    Years/months are calendar units applied with month-end clamping;
    weeks/days/hours/minutes/seconds are exact time units.
    """

    years: int = 0
    months: int = 0
    weeks: int = 0
    days: int = 0
    hours: int = 0
    minutes: int = 0
    seconds: float = 0.0

    @classmethod
    def parse(cls, text):
        if not isinstance(text, str):
            raise DurationParseError("duration must be a string")
        m = _DURATION_RE.match(text.strip())
        if not m:
            raise DurationParseError(f"invalid ISO 8601 duration: {text!r}")
        parts = m.groupdict()
        if not any(parts[k] for k in ("years", "months", "weeks", "days",
                                      "hours", "minutes", "seconds")):
            raise DurationParseError(f"empty duration: {text!r}")
        sign = -1 if parts["sign"] == "-" else 1

        def num(name):
            v = parts[name]
            return float(v.replace(",", ".")) if v else 0.0

        years, months = num("years"), num("months")
        if not (years.is_integer() and months.is_integer()):
            raise DurationParseError(
                f"fractional years/months not supported: {text!r}")
        weeks, days = num("weeks"), num("days")
        if not (weeks.is_integer() and days.is_integer()):
            raise DurationParseError(
                f"fractional weeks/days not supported: {text!r}")
        hours, minutes = num("hours"), num("minutes")
        if not (hours.is_integer() and minutes.is_integer()):
            raise DurationParseError(
                f"fractional hours/minutes not supported: {text!r}")
        return cls(
            years=sign * int(years),
            months=sign * int(months),
            weeks=sign * int(weeks),
            days=sign * int(days),
            hours=sign * int(hours),
            minutes=sign * int(minutes),
            seconds=sign * num("seconds"),
        )

    def _calendar_delta(self):
        return timedelta(
            weeks=self.weeks, days=self.days, hours=self.hours,
            minutes=self.minutes, seconds=self.seconds,
        )


def _shift_months(dt, total_months):
    month_index = dt.year * 12 + (dt.month - 1) + total_months
    year, month0 = divmod(month_index, 12)
    month = month0 + 1
    day = min(dt.day, monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def add_duration(dt, duration):
    """Add a Duration (or ISO 8601 string) to a datetime."""
    if isinstance(duration, str):
        duration = Duration.parse(duration)
    if not isinstance(dt, datetime):
        raise TypeError("dt must be a datetime")
    dt = _shift_months(dt, duration.years * 12 + duration.months)
    return dt + duration._calendar_delta()


def subtract_duration(dt, duration):
    """Subtract a Duration (or ISO 8601 string) from a datetime."""
    if isinstance(duration, str):
        duration = Duration.parse(duration)
    return add_duration(dt, Duration(
        years=-duration.years, months=-duration.months,
        weeks=-duration.weeks, days=-duration.days,
        hours=-duration.hours, minutes=-duration.minutes,
        seconds=-duration.seconds,
    ))
