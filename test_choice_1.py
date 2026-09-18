#!/usr/bin/env python3
"""
Unit tests for Phase 3 Choice 1: Foxglove Studio Layout & Telemetry Bridge
"""

import unittest
import json
from pathlib import Path
from foxglove_bridge import FoxgloveStreamer

class TestChoice1Foxglove(unittest.TestCase):

    def setUp(self):
        self.workspace = Path(__file__).parent
        self.output = self.workspace / "output"
        self.streamer = FoxgloveStreamer(self.output)

    def test_layout_json_exists(self):
        layout_path = self.workspace / "foxglove_layout.json"
        self.assertTrue(layout_path.exists())

        with open(layout_path, "r", encoding="utf-8") as f:
            layout_data = json.load(f)

        self.assertIn("configById", layout_data)
        self.assertIn("layout", layout_data)

    def test_foxglove_stream_export(self):
        sample_history = [
            {"timestamp": 100.0, "armed": True, "mode": "OFFBOARD", "position": {"x": 1.0, "y": 2.0, "z": 3.0}, "attitude": {"roll": 0, "pitch": 0, "yaw": 90}, "battery": {"voltage_v": 11.5, "remaining_pct": 90}}
        ]
        log_path = self.streamer.export_foxglove_log(sample_history, "unit_test_session")
        self.assertTrue(log_path.exists())

        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(len(data["frames"]), 1)
        self.assertIn("topic_pose", data["frames"][0])
        self.assertIn("topic_pointcloud", data["frames"][0])

if __name__ == "__main__":
    unittest.main()
