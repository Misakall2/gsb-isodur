import unittest
from datetime import datetime, timedelta, timezone

from isoduration import (
    Duration,
    DurationParseError,
    add_duration,
    subtract_duration,
)


class TestParse(unittest.TestCase):
    def test_full_duration(self):
        d = Duration.parse("P1Y2M3DT4H5M6S")
        self.assertEqual(d, Duration(1, 2, 0, 3, 4, 5, 6.0))

    def test_weeks(self):
        self.assertEqual(Duration.parse("P12W").weeks, 12)

    def test_fractional_seconds(self):
        self.assertAlmostEqual(Duration.parse("PT0.5S").seconds, 0.5)
        self.assertAlmostEqual(Duration.parse("PT1,25S").seconds, 1.25)

    def test_negative(self):
        d = Duration.parse("-P1Y2M")
        self.assertEqual((d.years, d.months), (-1, -2))

    def test_invalid(self):
        for bad in ["", "P", "PT", "hello", "1Y", "P1Y2Q", "PT1H2", "P1.5Y"]:
            with self.assertRaises(DurationParseError, msg=bad):
                Duration.parse(bad)


class TestArithmetic(unittest.TestCase):
    def test_cross_month(self):
        dt = datetime(2024, 1, 15, 10, 0, 0)
        self.assertEqual(add_duration(dt, "P1M"), datetime(2024, 2, 15, 10))
        self.assertEqual(add_duration(dt, "P40D"), datetime(2024, 2, 24, 10))

    def test_month_end_clamping(self):
        dt = datetime(2024, 1, 31)
        self.assertEqual(add_duration(dt, "P1M"), datetime(2024, 2, 29))
        dt = datetime(2023, 1, 31)
        self.assertEqual(add_duration(dt, "P1M"), datetime(2023, 2, 28))

    def test_leap_day(self):
        dt = datetime(2024, 2, 29, 12, 0)
        self.assertEqual(add_duration(dt, "P1Y"), datetime(2025, 2, 28, 12))
        self.assertEqual(add_duration(dt, "P4Y"), datetime(2028, 2, 29, 12))

    def test_weeks_and_days_mixed(self):
        dt = datetime(2024, 3, 1)
        self.assertEqual(add_duration(dt, "P2W3D"), datetime(2024, 3, 18))

    def test_negative_duration(self):
        dt = datetime(2024, 3, 15, 8, 30)
        self.assertEqual(add_duration(dt, "-P1M10D"), datetime(2024, 2, 5, 8, 30))
        self.assertEqual(subtract_duration(dt, "P1M10D"),
                         datetime(2024, 2, 5, 8, 30))

    def test_subtract_roundtrip(self):
        dt = datetime(2024, 6, 15, 9, 0)
        self.assertEqual(subtract_duration(add_duration(dt, "P3DT4H"), "P3DT4H"), dt)

    def test_time_components(self):
        dt = datetime(2024, 1, 1, 23, 30)
        self.assertEqual(add_duration(dt, "PT1H30M"), datetime(2024, 1, 2, 1, 0))
        self.assertEqual(add_duration(dt, "PT0.5S"),
                         datetime(2024, 1, 1, 23, 30, 0, 500000))

    def test_timezone_preserved(self):
        tz = timezone(timedelta(hours=8))
        dt = datetime(2024, 1, 31, 10, 0, tzinfo=tz)
        result = add_duration(dt, "P1Y1M1DT1H")
        self.assertEqual(result.tzinfo, tz)
        self.assertEqual(result.utcoffset(), timedelta(hours=8))
        self.assertEqual(result.replace(tzinfo=None),
                         datetime(2025, 3, 1, 11, 0))

    def test_duration_object_accepted(self):
        dt = datetime(2024, 1, 1)
        d = Duration.parse("P1W")
        self.assertEqual(add_duration(dt, d), datetime(2024, 1, 8))


if __name__ == "__main__":
    unittest.main()
