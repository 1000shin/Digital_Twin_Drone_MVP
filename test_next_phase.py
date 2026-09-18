#!/usr/bin/env python3
"""
Unit tests for Phase 2 Environment, Sensor Simulation, and CLI
"""

import unittest
from pathlib import Path
from world_builder import WorldBuilder
from sensor_sim import SensorCoverageSimulator
from db_loader import ComponentDB

class TestPhase2Features(unittest.TestCase):

    def setUp(self):
        self.output_dir = Path(__file__).parent / "test_output"

    def test_world_builder(self):
        builder = WorldBuilder(self.output_dir)
        world_file = builder.export_world(
            world_name="test_wind_world",
            wind_velocity_xyz=(4.0, 2.0, 0.0),
            obstacles=[{"type": "box", "pos": [1.0, 1.0, 1.0], "size": [0.5, 0.5, 1.0]}]
        )
        self.assertTrue(world_file.exists())

        with open(world_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('name="test_wind_world"', content)
        self.assertIn('gz-sim-wind-system', content)
        self.assertIn('obstacle_0_box', content)

    def test_sensor_coverage_simulator(self):
        sim = SensorCoverageSimulator()
        db = ComponentDB()
        sensor_lookup = {s["id"]: s for s in db.list_components("sensors")}

        mounts = [{"sensor_id": "s_lidar_2d"}, {"sensor_id": "s_depth_cam"}]
        metrics = sim.calculate_sensor_coverage(mounts, sensor_lookup)

        self.assertEqual(metrics["sensor_count"], 2)
        self.assertGreater(metrics["total_fov_deg"], 360.0)
        self.assertEqual(metrics["coverage_ratio"], 1.0)
        self.assertEqual(metrics["blind_spot_ratio"], 0.0)

if __name__ == "__main__":
    unittest.main()
