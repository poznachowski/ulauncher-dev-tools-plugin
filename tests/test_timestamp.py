import unittest
import datetime
from timestamp_utils import unix_to_utc_local_strings, datestr_to_unix


class TimestampUtilsTests(unittest.TestCase):
    def test_unix_to_utc_local_strings_deterministic_utc(self):
        # 1700000000 -> 2023-11-14 22:13:20 UTC
        utc_str, local_str = unix_to_utc_local_strings(1700000000)
        self.assertEqual(utc_str, "2023-11-14 22:13:20.000 UTC")

        # Local depends on environment; compute expected prefix using the current TZ
        expected_local_prefix = datetime.datetime.fromtimestamp(1700000000).astimezone().strftime("%Y-%m-%d %H:%M:%S")
        self.assertTrue(
            local_str.startswith(expected_local_prefix),
            f"Unexpected local string: {local_str} (expected to start with {expected_local_prefix})"
        )

    def test_datestr_to_unix_uses_local_time(self):
        # Compute expected value using the same environment to avoid TZ flakiness
        date_str = "2023-11-14 22:13:20"
        expected = int(datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").timestamp())
        self.assertEqual(datestr_to_unix(date_str), expected)

    def test_datestr_to_unix_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            datestr_to_unix("2023/11/14 22:13:20")

        with self.assertRaises(ValueError):
            datestr_to_unix("not a date")

    def test_iso_instant_z_no_fraction(self):
        from timestamp_utils import iso_instant_to_unix_millis
        iso = "2011-12-03T10:15:30Z"
        expected_ms = int(datetime.datetime(2011, 12, 3, 10, 15, 30, tzinfo=datetime.timezone.utc).timestamp() * 1000)
        self.assertEqual(iso_instant_to_unix_millis(iso), expected_ms)

    def test_iso_instant_z_with_zero_fraction(self):
        from timestamp_utils import iso_instant_to_unix_millis
        iso = "2007-12-03T10:15:30.00Z"
        expected_ms = int(datetime.datetime(2007, 12, 3, 10, 15, 30, tzinfo=datetime.timezone.utc).timestamp() * 1000)
        self.assertEqual(iso_instant_to_unix_millis(iso), expected_ms)

    def test_iso_instant_z_with_millis_fraction(self):
        from timestamp_utils import iso_instant_to_unix_millis
        iso = "2011-12-03T10:15:30.123Z"
        base = datetime.datetime(2011, 12, 3, 10, 15, 30, tzinfo=datetime.timezone.utc)
        expected_ms = int(base.timestamp() * 1000) + 123
        self.assertEqual(iso_instant_to_unix_millis(iso), expected_ms)

    def test_iso_instant_offset_plus_00(self):
        from timestamp_utils import iso_instant_to_unix_millis
        iso = "2011-12-03T10:15:30+00:00"
        expected_ms = int(datetime.datetime(2011, 12, 3, 10, 15, 30, tzinfo=datetime.timezone.utc).timestamp() * 1000)
        self.assertEqual(iso_instant_to_unix_millis(iso), expected_ms)

    def test_iso_instant_invalid_raises(self):
        from timestamp_utils import iso_instant_to_unix_millis
        with self.assertRaises(Exception):
            iso_instant_to_unix_millis("not-an-iso-instant")  # space, no TZ


if __name__ == "__main__":
    unittest.main()
