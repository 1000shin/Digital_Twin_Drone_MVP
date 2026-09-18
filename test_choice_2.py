#!/usr/bin/env python3
"""
Unit tests for Phase 3 Choice 2: VTOL & Tilt-Rotor Morphing Aircraft Builder & Evolution Engine
"""

import unittest
from pathlib import Path
from db_loader import ComponentDB
from vtol_builder import VTOLBuilder
from vtol_evolution import VTOLEvolutionEngine

class TestChoice2VTOL(unittest.TestCase):

    def setUp(self):
        self.workspace = Path(__file__).parent
        self.output = self.workspace / "test_output"
        self.db = ComponentDB()
        self.vtol_builder = VTOLBuilder(self.db)
        self.vtol_engine = VTOLEvolutionEngine(self.db)

    def test_vtol_model_export(self):
        sample_vtol = {
            "design_id": "test_vtol_unit",
            "wingspan_m": 1.20,
            "wing_chord_m": 0.25,
            "num_tilt_servos": 2,
            "num_hover_motors": 4,
            "motor_id": "m_2212_920kv",
            "battery_id": "b_3s_2200mah"
        }
        paths = self.vtol_builder.export_vtol_files(sample_vtol, self.output)
        self.assertTrue(paths["urdf"].exists())
        self.assertTrue(paths["sdf"].exists())

        with open(paths["sdf"], "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('gz-sim-lift-drag-system', content, "SDF should contain Gazebo Lift-Drag plugin")
        self.assertIn('main_wing', content)
        self.assertIn('tilt_servo_0', content)

    def test_vtol_evolution(self):
        mission_spec = {
            "mission_type": "long_range_offshore_vtol",
            "max_size_m": 1.50,
            "min_flight_time_min": 20.0,
            "required_sensors": ["s_opt_cam_hd"]
        }
        best_vtol = self.vtol_engine.evolve_vtol(mission_spec, population_size=20, generations=10)
        self.assertIn("wingspan_m", best_vtol)
        self.assertIn("wing_chord_m", best_vtol)
        self.assertGreater(best_vtol["wingspan_m"], 0.5)

if __name__ == "__main__":
    unittest.main()
