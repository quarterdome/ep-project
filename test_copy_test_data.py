import os
import tempfile
import unittest
from datetime import datetime, timezone

from copy_test_data import (
    parse_time,
    extract_timestamp_from_filename,
    get_sorted_source_files,
    get_first_timestamp_from_sorted_files,
)


class ParseTimeTests(unittest.TestCase):
    def test_parse_iso8601_basic(self):
        result = parse_time("2025-07-21T17:39:59Z")
        self.assertEqual(result, datetime(2025, 7, 21, 17, 39, 59, tzinfo=timezone.utc))

    def test_parse_iso8601_no_offset(self):
        result = parse_time("2025-07-21T10:40:00")
        self.assertEqual(result, datetime(2025, 7, 21, 10, 40, 0))

    def test_parse_filename_style_timestamp(self):
        result = parse_time("2025-07-21T10-40-00")
        self.assertEqual(result, datetime(2025, 7, 21, 10, 40, 0))

    def test_parse_iso8601_fractional_seconds(self):
        result = parse_time("2025-07-21T10:40:00.123Z")
        self.assertEqual(result, datetime(2025, 7, 21, 10, 40, 0, 123000, tzinfo=timezone.utc))

    def test_parse_epoch_seconds(self):
        result = parse_time("1650000000")
        self.assertEqual(result, datetime.utcfromtimestamp(1650000000))

    def test_invalid_timestamp_raises(self):
        with self.assertRaises(ValueError):
            parse_time("not-a-timestamp")

    def test_invalid_epoch_raises(self):
        with self.assertRaises(ValueError):
            parse_time("1650000000abc")

class ExtractTimestampFromFilenameTests(unittest.TestCase):
    def test_extract_timestamp_from_filename(self):
        result = extract_timestamp_from_filename("message_2025-07-21T10-40-00.json")
        self.assertEqual(result, datetime(2025, 7, 21, 10, 40, 0))

    def test_invalid_filename_returns_none(self):
        result = extract_timestamp_from_filename("invalid_message_name.json")
        self.assertIsNone(result)


class SortedFilesTests(unittest.TestCase):
    def test_get_sorted_source_files_orders_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filenames = [
                "message_2025-07-21T10-41-00.json",
                "message_2025-07-21T10-40-00.json",
                "message_2025-07-21T10-42-00.json",
            ]
            for fname in filenames:
                open(os.path.join(tmpdir, fname), 'w').close()

            result = get_sorted_source_files(tmpdir)
            self.assertEqual(result, [
                "message_2025-07-21T10-40-00.json",
                "message_2025-07-21T10-41-00.json",
                "message_2025-07-21T10-42-00.json",
            ])


class SourceStartTimeTests(unittest.TestCase):
    def test_get_first_timestamp_from_sorted_files(self):
        filenames = [
            "message_2025-07-21T10-40-00.json",
            "message_2025-07-21T10-41-00.json",
        ]

        result = get_first_timestamp_from_sorted_files(filenames)
        self.assertEqual(result, datetime(2025, 7, 21, 10, 40, 0))

    def test_get_first_timestamp_from_sorted_files_skips_invalid_files(self):
        filenames = [
            "invalid.json",
            "message_2025-07-21T10-41-00.json",
        ]

        result = get_first_timestamp_from_sorted_files(filenames)
        self.assertEqual(result, datetime(2025, 7, 21, 10, 41, 0))


if __name__ == "__main__":
    unittest.main()
