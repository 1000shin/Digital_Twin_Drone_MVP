#!/usr/bin/env python3
"""
Unit tests for Block 4 Mission-Driven Morphological & Sensor Evolution Engine
"""

import unittest
from db_loader import ComponentDB
from morph_evolution import MorphEvolutionEngine

class TestMorphEvolutionEngine(unittest.TestCase):

    def setUp(self):
        self.db = ComponentDB()
        self.engine = MorphEvolutionEngine(self.db)

    def test_evolution_process(self):
        mission_spec = {
            "mission_type": "long_range_survey",
            "max_size_m": 0.8,
            "min_flight_time_min": 15.0,
            "required_sensors": ["s_lidar_2d"]
        }

        best_spec = self.engine.evolve(mission_spec, population_size=20, generations=10)
        self.assertIn("design_id", best_spec)
        self.assertIn("num_arms", best_spec)
        self.assertIn("motor_id", best_spec)

        # Ensure required sensor was mounted
        mounted_sensor_ids = [s["sensor_id"] for s in best_spec["sensors_mount"]]
        self.assertIn("s_lidar_2d", mounted_sensor_ids)

        # Ensure evolved drone is physically flyable
        stats = self.db.calculate_power_and_mass(
            best_spec["num_arms"],
            best_spec["motor_id"],
            best_spec["prop_id"],
            best_spec["battery_id"],
            mounted_sensor_ids
        )
        self.assertGreater(stats["thrust_to_weight_ratio"], 1.0)

if __name__ == "__main__":
    unittest.main()
