#!/usr/bin/env python3
"""
Unit tests for Block 5 End-to-End Digital Twin Orchestration Pipeline
"""

import unittest
from pathlib import Path
from run_mvp_pipeline import DigitalTwinPipeline

class TestDigitalTwinPipeline(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = Path(__file__).parent
        self.pipeline = DigitalTwinPipeline(self.workspace_dir)

    def test_end_to_end_pipeline(self):
        mission_spec = {
            "mission_type": "unit_test_inspection",
            "max_size_m": 0.60,
            "min_flight_time_min": 10.0,
            "required_sensors": ["s_depth_cam"]
        }

        report = self.pipeline.run_pipeline(mission_spec)
        self.assertEqual(report["status"], "SUCCESS")
        self.assertIn("evolved_drone_spec", report)
        self.assertTrue(Path(report["generated_files"]["sdf"]).exists())
        self.assertGreater(report["telemetry_log_frames"], 0)

if __name__ == "__main__":
    unittest.main()
