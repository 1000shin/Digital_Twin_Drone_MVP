#!/usr/bin/env python3
"""
Unit tests for Block 3 MAVLink Autonomous Flight Controller
"""

import unittest
from mavlink_controller import MAVLinkController

class TestMAVLinkController(unittest.TestCase):

    def setUp(self):
        self.controller = MAVLinkController(simulate=True)

    def test_connection_and_arming(self):
        self.assertFalse(self.controller.is_connected)
        self.assertTrue(self.controller.connect())
        self.assertTrue(self.controller.is_connected)

        self.assertTrue(self.controller.arm())
        self.assertTrue(self.controller.is_armed)

    def test_flight_routine(self):
        self.controller.connect()
        self.controller.arm()
        self.controller.takeoff(3.0)

        telem = self.controller.get_telemetry()
        self.assertEqual(telem["position"]["z"], 3.0)

        self.controller.goto_location(10.0, 5.0, 3.0, yaw_deg=90.0)
        telem = self.controller.get_telemetry()
        self.assertEqual(telem["position"]["x"], 10.0)
        self.assertEqual(telem["position"]["y"], 5.0)

        self.controller.land()
        self.assertFalse(self.controller.is_armed)

if __name__ == "__main__":
    unittest.main()
