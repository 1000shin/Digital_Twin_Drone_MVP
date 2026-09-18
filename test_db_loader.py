#!/usr/bin/env python3
"""
Unit tests for Block 1 Component Database & Loader
"""

import unittest
from db_loader import ComponentDB

class TestComponentDB(unittest.TestCase):

    def setUp(self):
        self.db = ComponentDB()

    def test_database_loading(self):
        motors = self.db.list_components("motors")
        self.assertGreater(len(motors), 0, "Motors list should not be empty")

        sensors = self.db.list_components("sensors")
        self.assertGreater(len(sensors), 0, "Sensors list should not be empty")

    def test_get_component(self):
        motor = self.db.get_component("motors", "m_2212_920kv")
        self.assertIsNotNone(motor, "Motor 'm_2212_920kv' should be found")
        self.assertEqual(motor["kv"], 920)

        invalid = self.db.get_component("motors", "non_existent_id")
        self.assertIsNone(invalid, "Non-existent component should return None")

    def test_power_and_mass_calculation(self):
        stats = self.db.calculate_power_and_mass(
            num_arms=4,
            motor_id="m_2212_920kv",
            prop_id="p_1045",
            battery_id="b_3s_2200mah",
            sensor_ids=["s_lidar_2d"]
        )
        self.assertIn("total_mass_g", stats)
        self.assertIn("thrust_to_weight_ratio", stats)
        self.assertGreater(stats["thrust_to_weight_ratio"], 1.0, "Thrust-to-weight ratio should be > 1.0 for valid flight")

if __name__ == "__main__":
    unittest.main()
