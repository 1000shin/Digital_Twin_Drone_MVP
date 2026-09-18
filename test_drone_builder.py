#!/usr/bin/env python3
"""
Unit tests for Block 2 Dynamic URDF/SDF Generator
"""

import unittest
import os
from pathlib import Path
from db_loader import ComponentDB
from drone_builder import DroneBuilder

class TestDroneBuilder(unittest.TestCase):

    def setUp(self):
        self.db = ComponentDB()
        self.builder = DroneBuilder(self.db)
        self.output_dir = Path(__file__).parent / "test_output"

    def test_urdf_generation(self):
        sample_spec = {
            "design_id": "test_hexacopter",
            "num_arms": 6,
            "arm_length_m": 0.35,
            "motor_id": "m_4114_340kv",
            "prop_id": "p_1555",
            "battery_id": "b_6s_5000mah",
            "sensors_mount": [
                {"sensor_id": "s_lidar_2d", "rel_pos_xyz": [0.0, 0.0, 0.1]}
            ]
        }
        urdf_str = self.builder.generate_urdf(sample_spec)
        self.assertIn('<robot name="test_hexacopter">', urdf_str)
        self.assertIn('<link name="arm_5">', urdf_str, "Should contain arm_5 for a 6-arm drone")
        self.assertIn('<link name="sensor_0_s_lidar_2d">', urdf_str)

    def test_sdf_export(self):
        sample_spec = {
            "design_id": "test_export_quad",
            "num_arms": 4,
            "arm_length_m": 0.20,
            "motor_id": "m_1806_2300kv",
            "prop_id": "p_0504",
            "battery_id": "b_3s_1500mah",
            "sensors_mount": []
        }
        paths = self.builder.export_files(sample_spec, self.output_dir)
        self.assertTrue(paths["urdf"].exists())
        self.assertTrue(paths["sdf"].exists())
        self.assertGreater(os.path.getsize(paths["sdf"]), 500)

if __name__ == "__main__":
    unittest.main()
