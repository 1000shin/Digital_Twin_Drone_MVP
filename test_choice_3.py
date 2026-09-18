#!/usr/bin/env python3
"""
Unit tests for Phase 3 Choice 3: Native PX4 SITL & 3D GUI Simulation Bridge
"""

import unittest
from pathlib import Path
from px4_sitl_bridge import PX4SITLBridge

class TestChoice3PX4SITL(unittest.TestCase):

    def setUp(self):
        self.workspace = Path(__file__).parent
        self.output = self.workspace / "output"
        self.bridge = PX4SITLBridge(self.workspace)

    def test_system_check(self):
        status = self.bridge.check_system_installations()
        self.assertIn("gazebo_sim", status)
        self.assertIn("px4_sitl", status)
        self.assertIn("qgroundcontrol", status)

    def test_gui_simulation_launch(self):
        sample_sdf = self.output / "evolved_confined_space.sdf"
        sample_world = self.output / "world_bridge_confined_inspection.world"

        res = self.bridge.launch_gui_simulation(sample_sdf, sample_world)
        self.assertIn("pid", res)
        self.assertEqual(res["mavlink_offboard_port"], 14540)
        self.assertEqual(res["qgroundcontrol_port"], 14550)

if __name__ == "__main__":
    unittest.main()
