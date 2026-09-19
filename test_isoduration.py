import unittest
from datetime import datetime, timedelta, timezone

from isoduration import (
    Duration, DurationError, add_duration, parse_duration, sub_duration,
)


class TestParse(unittest.TestCase):
    def test_full(self):
        d = parse_duration("P1Y2M3DT4H5M6S")
        self.assertEqual(d, Duration(1, 2, 0, 3, 4, 5, 6))

    def test_weeks(self):
        self.assertEqual(parse_duration("P12W"), Duration(weeks=12))

    def test_fractional_seconds(self):
        self.assertEqual(parse_duration("PT0.5S").seconds, 0.5)
        self.assertEqual(parse_duration("PT1,25S").seconds, 1.25)

    def test_negative(self):
        self.assertEqual(parse_duration("-P1DT2H"), Duration(days=-1, hours=-2))

    def test_invalid(self):
        for bad in ["", "P", "PT", "1Y", "P1Y2Q", "P1D2Y", "P1Y-", "hello",
                    "P1.5Y", "PT1H0.5M", None, 42]:
            with self.assertRaises(DurationError, msg=repr(bad)):
                parse_duration(bad)


class TestArithmetic(unittest.TestCase):
    def test_cross_month_clamp(self):
        # Jan 31 + 1 month -> Feb 28/29, not Mar 3
        self.assertEqual(add_duration(datetime(2023, 1, 31), "P1M"),
                         datetime(2023, 2, 28))
        self.assertEqual(add_duration(datetime(2024, 1, 31), "P1M"),
                         datetime(2024, 2, 29))

    def test_leap_day(self):
        self.assertEqual(add_duration(datetime(2024, 2, 29), "P1D"),
                         datetime(2024, 3, 1))
        # 2024-02-29 + P1Y -> 2025-02-28 (no Feb 29 in 2025)
        self.assertEqual(add_duration(datetime(2024, 2, 29), "P1Y"),
                         datetime(2025, 2, 28))
        self.assertEqual(add_duration(datetime(2024, 2, 29), "P4Y"),
                         datetime(2028, 2, 29))

    def test_weeks_and_days(self):
        self.assertEqual(add_duration(datetime(2024, 1, 1), "P2W3D"),
                         datetime(2024, 1, 18))

    def test_time_parts(self):
        self.assertEqual(add_duration(datetime(2024, 3, 1, 23, 30), "PT1H30M"),
                         datetime(2024, 3, 2, 1, 0))
        self.assertEqual(add_duration(datetime(2024, 3, 1), "P3DT4H"),
                         datetime(2024, 3, 4, 4))

    def test_fractional_seconds(self):
        self.assertEqual(add_duration(datetime(2024, 1, 1, 0, 0, 0), "PT1.5S"),
                         datetime(2024, 1, 1, 0, 0, 1, 500000))

    def test_negative_duration(self):
        self.assertEqual(add_duration(datetime(2024, 3, 15, 12), "-P1DT2H"),
                         datetime(2024, 3, 14, 10))
        self.assertEqual(sub_duration(datetime(2024, 3, 31), "P1M"),
                         datetime(2024, 2, 29))
        self.assertEqual(sub_duration(datetime(2024, 1, 10), "P1Y2M"),
                         datetime(2022, 11, 10))

    def test_sub_negative_roundtrip(self):
        start = datetime(2024, 2, 29, 8, 0)
        self.assertEqual(sub_duration(add_duration(start, "P1DT6H"), "P1DT6H"),
                         start)

    def test_timezone_preserved(self):
        tz = timezone(timedelta(hours=8))
        dt = datetime(2024, 1, 31, 10, 0, tzinfo=tz)
        out = add_duration(dt, "P1M")
        self.assertEqual(out, datetime(2024, 2, 29, 10, 0, tzinfo=tz))
        self.assertIs(out.tzinfo, tz)
        self.assertEqual(out.utcoffset(), timedelta(hours=8))

    def test_accepts_duration_object(self):
        self.assertEqual(add_duration(datetime(2024, 1, 1), Duration(days=5)),
                         datetime(2024, 1, 6))


if __name__ == "__main__":
    unittest.main()
