#!/usr/bin/env python3
"""
Unit test for WebGL 3D Flight Simulator In-Engine Actual Flight Verification
Executes verify_webgl_flight.js to assert 0 collisions, 100% integrity, and multi-gate clearance.
"""

import json
import subprocess
import unittest
from pathlib import Path


class TestWebGLActualFlight(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = Path(__file__).parent
        self.output_dir = self.workspace_dir / "output"
        self.script_path = self.workspace_dir / "verify_webgl_flight.js"
        self.dataset_path = self.output_dir / "training_datasets" / "webgl_actual_flight_trajectory.json"
        self.report_path = self.output_dir / "flight_audit_reports" / "webgl_actual_flight_audit.md"

    def test_webgl_in_engine_flight_zero_collision(self):
        """Validates that running flight_test_simulator.html achieves 0 collisions and >=4 gates cleared."""
        self.assertTrue(self.script_path.exists(), "verify_webgl_flight.js must exist")

        res = subprocess.run(
            ["node", str(self.script_path)],
            cwd=str(self.workspace_dir),
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"Flight verification failed with error:\n{res.stderr}\n{res.stdout}")

        self.assertTrue(self.dataset_path.exists(), "Trajectory dataset JSON must be exported")
        self.assertTrue(self.report_path.exists(), "Audit report markdown must be exported")

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data.get("metadata", {})
        self.assertEqual(meta.get("collision_count"), 0, "Autonomous flight must have 0 collisions")
        self.assertEqual(meta.get("final_integrity"), 100, "Structural integrity must remain 100%")
        self.assertGreaterEqual(meta.get("gates_crossed", 0), 4, "Must clear at least 4 gates (1 full circuit)")
        self.assertEqual(meta.get("verdict"), "PASSED_ZERO_COLLISION")


if __name__ == "__main__":
    unittest.main()
