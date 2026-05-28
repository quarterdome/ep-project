import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock

import uploader


class UploaderTests(unittest.TestCase):
    def test_iso_to_datetime_with_z(self):
        result = uploader._iso_to_datetime("2025-07-10T21:07:23Z")
        self.assertEqual(result, datetime(2025, 7, 10, 21, 7, 23, tzinfo=timezone.utc))

    def test_iso_to_datetime_with_offset(self):
        result = uploader._iso_to_datetime("2025-07-10T17:07:23-04:00")
        self.assertEqual(result, datetime(2025, 7, 10, 21, 7, 23, tzinfo=timezone.utc))

    def test_build_metric_data_returns_expected_metrics(self):
        records = [
            {
                "measurement": "grid",
                "time": "2025-07-10T21:07:23Z",
                "fields": {
                    "voltage": 248.0,
                    "frequency": 59.9,
                    "power": 307.0,
                    "current": 123.0,
                },
            },
            {
                "measurement": "inverter",
                "time": "2025-07-10T21:07:23Z",
                "fields": {
                    "voltage": 248.0,
                    "current": 10.0,
                    "load_power": 26.0,
                    "whole_home_power": 0,
                    "temperature": 31.4,
                },
            },
            {
                "measurement": "battery",
                "time": "2025-07-10T21:07:23Z",
                "fields": {
                    "voltage": 56.0,
                    "power_charge": 10.0,
                    "power_discharge": 0.0,
                    "current": 5.0,
                    "charge_state": 1.0,
                    "temperature": 27.2,
                },
            },
        ]

        metric_data = uploader.build_metric_data(records)
        self.assertEqual(len(metric_data), 15)
        self.assertEqual(metric_data[0]["MetricName"], "grid_voltage")
        self.assertEqual(metric_data[0]["Value"], 248.0)
        self.assertEqual(metric_data[1]["MetricName"], "grid_frequency")
        self.assertEqual(metric_data[1]["Value"], 59.9)
        self.assertEqual(metric_data[4]["MetricName"], "inverter_voltage")
        self.assertEqual(metric_data[4]["Value"], 248.0)
        self.assertEqual(metric_data[9]["MetricName"], "battery_voltage")
        self.assertEqual(metric_data[9]["Value"], 56.0)
        self.assertEqual(metric_data[-1]["MetricName"], "battery_temperature")
        self.assertEqual(metric_data[-1]["Value"], 27.2)
        expected_timestamp = 1752181643.0
        for item in metric_data:
            self.assertEqual(item["Timestamp"], expected_timestamp)
            self.assertEqual(item["Unit"], "None")

    def test_process_one_json_file_uses_injected_cw_client(self):
        sample_json = {
            "telemetry": [
                {
                    "measurement": "grid",
                    "time": "2025-07-10T21:07:23Z",
                    "fields": {
                        "voltage": 248.0,
                        "frequency": 59.9,
                        "power": 307.0,
                        "current": 123.0,
                    },
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "message_test.json")
            with open(path, "w") as f:
                json.dump(sample_json, f)

            mock_cw = Mock()
            mock_cw.put_metric_data = Mock()

            success, msg = uploader.process_one_json_file(path, cw_client=mock_cw)
            self.assertTrue(success)
            self.assertIn("Published", msg)
            mock_cw.put_metric_data.assert_called_once()
            _, kwargs = mock_cw.put_metric_data.call_args
            self.assertEqual(kwargs["Namespace"], uploader.CLOUDWATCH_NAMESPACE)
            self.assertEqual(len(kwargs["MetricData"]), 4)


if __name__ == "__main__":
    unittest.main()
