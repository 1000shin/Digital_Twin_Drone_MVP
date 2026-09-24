#!/usr/bin/env python3
"""
Unit tests for Milestone M2.6: SharedAutonomyCopilot
Verifies:
- Free flight zero-intervention transparency (AC-1.3)
- Warning zone smooth velocity damping (AC-2.1)
- Emergency zone APF repulsion & tangential deflection (AC-2.2)
- Escape maneuver 100% preservation (AC-2.1)
- Continuous dynamic blending bounds and low latency
"""

import unittest
import time
from shared_autonomy_copilot import SharedAutonomyCopilot, CopilotInterventionLevel


class TestSharedAutonomyCopilot(unittest.TestCase):
    def setUp(self):
        self.copilot = SharedAutonomyCopilot(
            warning_dist_m=2.0,
            emergency_dist_m=1.2,
            hard_limit_dist_m=0.5,
            ttc_threshold_sec=2.0
        )

    def test_free_flight_zero_intervention(self):
        """Verifies beta=0.0 and 100% stick passthrough when obstacles are far away (>2.0m)."""
        human_cmd = [0.8, -0.5, 0.2, 0.1]
        far_lidar = [5.0, 6.0, 4.5, 7.0, 8.0, 5.5, 6.2, 7.1]
        
        decision = self.copilot.evaluate(human_cmd, far_lidar)
        
        self.assertEqual(decision["intervention_level"], CopilotInterventionLevel.STANDBY.value)
        self.assertEqual(decision["beta"], 0.0)
        self.assertEqual(decision["safe_action"], human_cmd)
        self.assertEqual(decision["repulsion_vector"], [0.0, 0.0])

    def test_warning_zone_smooth_damping(self):
        """Verifies warning zone (1.5m) dampens forward approach stick while keeping lateral inputs."""
        # Pilot pushes full forward (pitch = 1.0) into front obstacle (0° LiDAR = 1.5m)
        human_cmd = [1.0, 0.3, 0.0, 0.0]
        warning_lidar = [1.5, 4.0, 5.0, 5.0, 5.0, 5.0, 5.0, 4.0]
        
        decision = self.copilot.evaluate(human_cmd, warning_lidar)
        
        self.assertEqual(decision["intervention_level"], CopilotInterventionLevel.WARNING.value)
        self.assertGreater(decision["beta"], 0.0)
        self.assertLess(decision["beta"], 1.0)
        
        # Forward pitch must be dampened (less than 1.0)
        safe_action = decision["safe_action"]
        self.assertLess(safe_action[0], 1.0)
        self.assertGreater(safe_action[0], 0.3)
        # Lateral roll (0.3) should be preserved
        self.assertAlmostEqual(safe_action[1], 0.3, places=2)

    def test_emergency_zone_active_repulsion(self):
        """Verifies emergency zone (0.8m) generates strong negative repulsion to block crash."""
        # Pilot pushes aggressively forward (pitch = 1.0) into front obstacle (0.8m)
        human_cmd = [1.0, 0.0, 0.0, 0.0]
        emergency_lidar = [0.8, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0]
        
        decision = self.copilot.evaluate(human_cmd, emergency_lidar)
        
        self.assertEqual(decision["intervention_level"], CopilotInterventionLevel.DEFLECTING.value)
        self.assertGreater(decision["beta"], 0.5)
        
        # Pitch should be heavily clamped or reversed into backward push
        safe_action = decision["safe_action"]
        self.assertLess(safe_action[0], 0.2)
        # Repulsion vector should oppose obstacle direction (negative pitch)
        self.assertLess(decision["repulsion_vector"][0], 0.0)

    def test_escape_maneuver_preservation(self):
        """Verifies pilot escape input (pulling back from front obstacle) is NOT dampened."""
        # Obstacle in front at 0.9m (Emergency zone), but pilot commands backward pitch (-0.8)
        human_cmd = [-0.8, 0.0, 0.0, 0.0]
        emergency_lidar = [0.9, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0]
        
        decision = self.copilot.evaluate(human_cmd, emergency_lidar)
        
        self.assertTrue(decision["human_escaped"])
        # Escape command must remain strongly backward (at least <= -0.8)
        self.assertLessEqual(decision["safe_action"][0], -0.8)

    def test_low_latency_inference(self):
        """Verifies single-step copilot calculation completes well under 1.0 ms."""
        human_cmd = [0.5, 0.5, 0.0, 0.0]
        lidar = [1.1, 2.0, 3.0, 4.0, 5.0, 4.0, 3.0, 2.0]
        
        t0 = time.perf_counter()
        for _ in range(500):
            self.copilot.evaluate(human_cmd, lidar)
        t_elapsed = (time.perf_counter() - t0) / 500.0
        
        # Must be well under 1.0ms (0.001s)
        self.assertLess(t_elapsed, 0.0005)

    def test_mavlink_controller_copilot_integration(self):
        """Verifies MAVLinkController can enable copilot and filter commands."""
        from mavlink_controller import MAVLinkController
        controller = MAVLinkController(simulate=True)
        self.assertFalse(controller.copilot_enabled)

        controller.enable_copilot(self.copilot)
        self.assertTrue(controller.copilot_enabled)

        # Dangerously close forward command (0.8m)
        res = controller.apply_copilot_safety_filter([1.0, 0.0, 0.0, 0.0], [0.8] + [5.0]*7)
        self.assertEqual(res["intervention_level"], CopilotInterventionLevel.DEFLECTING.value)
        self.assertLess(res["safe_action"][0], 0.2)

        controller.disable_copilot()
        self.assertFalse(controller.copilot_enabled)

    def test_copilot_tangential_deflection(self):
        """Verifies emergency zone generates lateral deflection when slight stick bias exists."""
        # Pilot pushes forward-right towards a dead-ahead obstacle at 0.7m
        human_cmd = [1.0, 0.2, 0.0, 0.0]
        lidar = [0.7] + [4.0] * 7  # 0.7m dead ahead

        decision = self.copilot.evaluate(human_cmd, lidar)
        self.assertEqual(decision["intervention_level"], CopilotInterventionLevel.DEFLECTING.value)
        # Safe roll should assist moving rightwards away from the obstacle contour
        self.assertGreater(decision["safe_action"][1], 0.0)

    def test_copilot_decision_fields(self):
        """Verifies all required schema fields exist in the decision payload."""
        human_cmd = [0.5, -0.3, 0.1, 0.2]
        lidar = [1.6] + [5.0] * 7
        res = self.copilot.evaluate(human_cmd, lidar)

        required_keys = [
            "safe_action", "intervention_level", "beta",
            "min_distance_m", "ttc_sec", "repulsion_vector", "human_escaped"
        ]
        for key in required_keys:
            self.assertIn(key, res)

    def test_webgl_simulator_copilot_integration(self):
        """Verifies WebGL simulator HTML includes Copilot HUD, 3D halo, and key handlers."""
        from pathlib import Path
        html_path = Path(__file__).parent / "output" / "flight_test_simulator.html"
        self.assertTrue(html_path.exists(), "flight_test_simulator.html must exist")
        html_content = html_path.read_text(encoding="utf-8")

        self.assertIn("copilot-section", html_content)
        self.assertIn("copilot-status-badge", html_content)
        self.assertIn("btn-copilot-toggle", html_content)
        self.assertIn("toggleCopilot", html_content)
        self.assertIn("copilotHalo", html_content)
        self.assertIn("KeyC", html_content)


if __name__ == "__main__":
    unittest.main()
