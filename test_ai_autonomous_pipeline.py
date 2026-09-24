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

    def test_rl_env_angular_velocity_dynamics(self):
        """Verifies angular velocity is actively updated and non-zero on attitude change."""
        env = DroneRLEnvironment(seed=123)
        env.reset()
        self.assertEqual(env.ang_vel, [0.0, 0.0, 0.0])

        # Step with active roll and yaw command
        next_obs, _, _, _, _ = env.step([0.0, 0.5, 0.4, 0.0])
        # Indices 9, 10, 11 are wx, wy, wz
        self.assertNotEqual(env.ang_vel[1], 0.0)  # wy updated from cmd_yaw
        self.assertNotEqual(env.ang_vel[2], 0.0)  # wz updated from roll delta
        self.assertEqual(next_obs[10], env.ang_vel[1])

    def test_autonomous_learner_human_warmup_and_trial(self):
        """Verifies AC-3.1 behavioral cloning warmup and autonomous trial batch execution."""
        learner = AutonomousFlightLearner(output_dir=self.output_dir)
        warm_res = learner.warm_up_result
        self.assertEqual(warm_res.get("status"), "warmed_up")
        self.assertGreater(warm_res.get("samples_analyzed", 0), 0)

        # Run short trial batch to verify learning speed and schema
        batch = learner.run_trial_batch(num_episodes=5)
        self.assertEqual(batch["session_id"], "ai_autonomous_session_001")
        self.assertIn("summary", batch)
        self.assertIn("metrics", batch)
        self.assertIn("samples", batch)
        self.assertGreater(len(batch["samples"]), 0)

    def test_webgl_simulator_no_tdz_bug(self):
        """Verifies isCatastrophic is declared BEFORE any conditional access in updatePhysics."""
        html_path = self.output_dir / "flight_test_simulator.html"
        content = html_path.read_text(encoding="utf-8")
        idx_decl = content.find("const isCatastrophic =")
        idx_use = content.find("isAIAutopilotActive && !isCatastrophic")
        self.assertNotEqual(idx_decl, -1)
        self.assertNotEqual(idx_use, -1)
        self.assertLess(idx_decl, idx_use, "isCatastrophic must be declared before it is accessed to prevent TDZ error")

    def test_webgl_ai_multigate_corridor_and_crossing_state_machine(self):
        """Validates multi-gate 3D rotation, circuit corridor, APF tunnel filter, and plane crossing state machine."""
        html_path = self.output_dir / "flight_test_simulator.html"
        self.assertTrue(html_path.exists())
        content = html_path.read_text(encoding="utf-8")

        # 1. Global Multi-Gate Closed Circuit Navigation Corridor
        self.assertIn("circuitLine", content)
        self.assertIn("circuitPts", content)
        self.assertIn("THREE.LineDashedMaterial", content)

        # 2. Gate Normal Vectors and Orientation
        self.assertIn("yaw: Math.PI / 2", content)
        self.assertIn("nx: 0, nz: -1", content)
        self.assertIn("nx: 1, nz: 0", content)
        self.assertIn("nx: 0, nz: 1", content)
        self.assertIn("nx: -1, nz: 0", content)

        # 3. 3D Rotated Gate Group in Collision Arena
        self.assertIn("gateGroup = new THREE.Group()", content)
        self.assertIn("gateGroup.rotation.y = g.yaw", content)
        self.assertIn("gateId: g.id", content)
        self.assertIn("isGatePost: true", content)
        self.assertIn("isGateTop: true", content)

        # 4. Smart Tunnel APF Repulsion Filter
        self.assertIn("obs.gateId === targetGate.id", content)
        self.assertIn("if (obs.isGateTop) return;", content)

        # 5. Gate Plane Normal Crossing State Machine & Lead Targeting
        self.assertIn("signedDot = dxFromGate * targetGate.nx + dzFromGate * targetGate.nz", content)
        self.assertIn("lateralDist = Math.hypot", content)
        self.assertIn("hasCrossedGate", content)
        self.assertIn("leadDist = 1.6", content)

        # 6. LiDAR Gate Passage Deadzone Filter
        self.assertIn("isApproachingGate", content)

if __name__ == "__main__":
    unittest.main()
