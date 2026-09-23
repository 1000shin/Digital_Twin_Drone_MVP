#!/usr/bin/env python3
"""
Unit tests for AI Autonomous Flight Pipeline, RL Environment,
Parametric Potential Field Policy, WebGL Autopilot UI, and Gen-4 Model Lineage.
"""

import unittest
import json
import math
from pathlib import Path

from drone_rl_env import DroneRLEnvironment, ObstaclePillar, FlightGate
from autonomous_flight_learner import AutonomousFlightPolicy, AutonomousFlightLearner
from flight_test_sim import WebGLFlightSimulator

class TestAIAutonomousPipeline(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = Path(__file__).parent
        self.output_dir = self.workspace_dir / "output"
        self.archive_dir = self.output_dir / "models_archive"

    def test_drone_rl_environment_reset_and_step(self):
        """Verifies 23-dim observation and 4-dim action space dynamics."""
        env = DroneRLEnvironment(seed=123)
        obs = env.reset()
        self.assertEqual(len(obs), 23)

        # Observation normalization sanity check
        for val in obs:
            self.assertIsInstance(val, float)
            self.assertFalse(math.isnan(val))

        # Action step: [pitch, roll, yaw, climb]
        action = [0.2, -0.1, 0.05, 0.5]
        next_obs, reward, terminated, truncated, info = env.step(action)
        self.assertEqual(len(next_obs), 23)
        self.assertIsInstance(reward, float)
        self.assertIsInstance(terminated, bool)
        self.assertIsInstance(truncated, bool)
        self.assertIn("collided", info)
        self.assertIn("gate_idx", info)
        self.assertIn("min_lidar_m", info)

    def test_rl_env_lidar_and_collision(self):
        """Verifies 8-ray LiDAR sensing and collision boundary penalty."""
        env = DroneRLEnvironment(seed=42)
        env.reset()
        lidar = env._compute_lidar()
        self.assertEqual(len(lidar), 8)
        for r in lidar:
            self.assertGreater(r, 0.0)
            self.assertLessEqual(r, 12.0)

        # Force out of bounds collision
        env.pos[0] = 25.0
        _, rew, term, _, info = env.step([0.0, 0.0, 0.0, 0.0])
        self.assertTrue(term)
        self.assertTrue(info["collided"])
        self.assertLess(rew, -50.0)

    def test_autonomous_flight_policy_predict(self):
        """Verifies policy produces clamped 4-dim actions and avoids obstacle."""
        policy = AutonomousFlightPolicy()
        # Normal observation
        obs = [0.0] * 23
        obs[12:20] = [1.0] * 8  # 12m lidar
        obs[20] = 0.5          # target at +10m X
        obs[22] = -0.5         # target at -10m Z

        action = policy.predict(obs)
        self.assertEqual(len(action), 4)
        for cmd in action:
            self.assertGreaterEqual(cmd, -1.0)
            self.assertLessEqual(cmd, 1.0)

    def test_webgl_simulator_ai_autopilot_elements(self):
        """Verifies WebGL simulator HTML includes AI Autopilot HUD badges and key bindings."""
        sim = WebGLFlightSimulator(self.output_dir)
        html_path = self.output_dir / "flight_test_simulator.html"
        self.assertTrue(html_path.exists())

        content = html_path.read_text(encoding="utf-8")
        self.assertIn("ai-autopilot-section", content)
        self.assertIn('id="ai-status-badge"', content)
        self.assertIn('id="btn-ai-toggle"', content)
        self.assertIn('id="ai-target-gate"', content)
        self.assertIn('id="ai-confidence"', content)
        self.assertIn('id="ai-reward"', content)
        self.assertIn("toggleAIAutopilot()", content)
        self.assertIn("KeyP", content)
        self.assertIn("trajectoryLine", content)
        self.assertIn("aiGates", content)

    def test_generation_4_models_archive(self):
        """Verifies Gen-4 Sentinel Prime 3D models and lineage archive index."""
        gen4_dir = self.archive_dir / "gen_04_sentinel_prime_v4"
        self.assertTrue(gen4_dir.exists())

        urdf_file = gen4_dir / "evolved_sentinel_prime_v4.urdf"
        sdf_file = gen4_dir / "evolved_sentinel_prime_v4.sdf"
        spec_file = gen4_dir / "model_spec.json"
        meta_file = gen4_dir / "METADATA.md"

        self.assertTrue(urdf_file.exists())
        self.assertTrue(sdf_file.exists())
        self.assertTrue(spec_file.exists())
        self.assertTrue(meta_file.exists())

        # Check spec JSON contents
        with open(spec_file, "r", encoding="utf-8") as f:
            spec = json.load(f)
        self.assertEqual(spec["generation"], 4)
        self.assertEqual(spec["design_id"], "evolved_sentinel_prime_v4")
        self.assertEqual(spec["physical_specifications"]["num_arms"], 4)
        self.assertEqual(spec["physical_specifications"]["arm_length_m"], 0.165)
        self.assertEqual(spec["physical_specifications"]["frame_diagonal_span_m"], 0.38)
        self.assertEqual(spec["physical_specifications"]["duct_bumper_thickness_mm"], 2.5)

        # Check master archive index
        index_file = self.archive_dir / "index.json"
        self.assertTrue(index_file.exists())
        with open(index_file, "r", encoding="utf-8") as f:
            idx = json.load(f)
        self.assertEqual(idx["generations_count"], 4)
        self.assertEqual(len(idx["generations"]), 4)
        self.assertEqual(idx["generations"][3]["design_id"], "evolved_sentinel_prime_v4")

if __name__ == "__main__":
    unittest.main()
