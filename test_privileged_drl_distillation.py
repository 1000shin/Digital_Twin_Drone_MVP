#!/usr/bin/env python3
"""
Unit Test Suite: Privileged Deep Reinforcement Learning & Teacher-Student Distillation
(FEAT-M2.5.2-PRIVILEGED-DRL-DISTILLATION)

Covers:
1. Privileged 32-dim state structure & student noisy observation.
2. PyTorch Teacher & Student network shapes and forward passes.
3. Numerical equivalence between PyTorch and pure NumPy inference (<= 1e-5).
4. Multi-stage checkpoint archive integrity (0% untrained, 40% half-trained, 100% mastered).
5. Sub-millisecond inference latency benchmark (< 0.1ms).
6. Graceful fallback to APF controller.
7. WebGL HTML Stage Inspector UI & JavaScript functions.
"""

import math
import json
import time
import unittest
from pathlib import Path

import torch
from drone_rl_env import DroneRLEnvironment
from train_privileged_distillation import TeacherPolicy, StudentPolicy
from autonomous_flight_learner import StudentPolicyNumpy, HybridAutonomousPolicy, AutonomousFlightPolicy


class TestPrivilegedDRLDistillation(unittest.TestCase):

    def setUp(self):
        self.env = DroneRLEnvironment(seed=123)
        self.weights_dir = Path(__file__).parent / "output" / "neural_models"
        self.stages_file = self.weights_dir / "student_policy_stages.json"
        self.weights_file = self.weights_dir / "student_policy_weights.json"

    def test_privileged_state_structure(self):
        """AC-1.1: Verify 32-dim privileged ground-truth vector format."""
        self.env.reset()
        priv_state = self.env.get_privileged_state()

        self.assertEqual(len(priv_state), 32, "Privileged state vector must be exactly 32-dimensional")
        for val in priv_state:
            self.assertFalse(math.isnan(val), "Privileged state contains NaN")
            self.assertFalse(math.isinf(val), "Privileged state contains Inf")

        # Verify gate normal orientation (idx 15..17)
        norm_mag = math.sqrt(priv_state[15]**2 + priv_state[16]**2 + priv_state[17]**2)
        self.assertAlmostEqual(norm_mag, 1.0, places=4, msg="Gate normal must be a unit vector")

    def test_student_noisy_observation(self):
        """AC-1.2: Verify student 23-dim observation with Gaussian noise and dropout."""
        self.env.reset()
        clean_obs = self.env.get_student_observation(noise_std=0.0, dropout_prob=0.0)
        self.assertEqual(len(clean_obs), 23, "Student observation must be 23-dimensional")

        # With noise and dropout
        noisy_obs = self.env.get_student_observation(noise_std=0.08, dropout_prob=0.20)
        self.assertEqual(len(noisy_obs), 23)

        # Ensure values stay bounded in reasonable range
        for v in noisy_obs:
            self.assertFalse(math.isnan(v))
            self.assertFalse(math.isinf(v))

    def test_pytorch_networks_and_weight_export(self):
        """AC-2.1 & AC-2.2: Verify PyTorch Teacher and Student architectures."""
        teacher = TeacherPolicy(state_dim=32, action_dim=4, hidden_dim=128)
        student = StudentPolicy(obs_dim=23, action_dim=4, hidden_dim=64)

        dummy_priv = torch.zeros((1, 32), dtype=torch.float32)
        dummy_obs = torch.zeros((1, 23), dtype=torch.float32)

        out_t = teacher(dummy_priv)
        out_s = student(dummy_obs)

        self.assertEqual(out_t.shape, (1, 4))
        self.assertEqual(out_s.shape, (1, 4))

        # Check bounds in [-1.0, 1.0] from Tanh
        self.assertTrue(torch.all(out_t >= -1.0) and torch.all(out_t <= 1.0))
        self.assertTrue(torch.all(out_s >= -1.0) and torch.all(out_s <= 1.0))

        # Check weight dictionary export
        weights = student.export_weights_dict()
        req_keys = ["w1", "b1", "w2", "b2", "w3", "b3"]
        for k in req_keys:
            self.assertIn(k, weights)
        self.assertEqual(len(weights["w1"]), 64)
        self.assertEqual(len(weights["w1"][0]), 23)
        self.assertEqual(len(weights["w3"]), 4)

    def test_numpy_inference_numerical_equivalence(self):
        """AC-3.2: Verify pure NumPy inference matches PyTorch output within 1e-5."""
        student_pt = StudentPolicy(obs_dim=23, action_dim=4, hidden_dim=64)
        weights_dict = student_pt.export_weights_dict()

        student_np = StudentPolicyNumpy(weights_source=weights_dict)

        # Test across multiple random inputs
        for seed in range(5):
            torch.manual_seed(seed)
            sample_in = torch.randn((1, 23), dtype=torch.float32)
            pt_out = student_pt(sample_in).detach().cpu().numpy()[0]

            np_out = student_np.predict(sample_in.numpy()[0].tolist())

            for j in range(4):
                self.assertAlmostEqual(
                    pt_out[j], np_out[j], places=5,
                    msg=f"Discrepancy between PyTorch and NumPy at action index {j}"
                )

    def test_multi_stage_checkpoints_archive(self):
        """AC-2.3: Verify multi-stage archive containing 0% untrained, 40% half-trained, 100% mastered."""
        self.assertTrue(self.stages_file.exists(), f"Stages archive not found at {self.stages_file}")

        with open(self.stages_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("metadata", data)
        self.assertIn("stages", data)

        stages = data["stages"]
        self.assertIn("stage_0_untrained", stages)
        self.assertIn("stage_1_half_trained", stages)
        self.assertIn("stage_2_mastered", stages)

        # Check that stage 0 and stage 2 have different weights
        w0 = stages["stage_0_untrained"]["w1"][0][0]
        w2 = stages["stage_2_mastered"]["w1"][0][0]
        self.assertNotEqual(w0, w2, "Stage 0 and Stage 2 weights should differ after training")

    def test_inference_latency_benchmark(self):
        """AC-3.1 & Non-Functional: Verify inference latency is < 0.1ms (target < 0.05ms)."""
        if self.weights_file.exists():
            student = StudentPolicyNumpy(self.weights_file)
        else:
            student_pt = StudentPolicy(obs_dim=23, action_dim=4, hidden_dim=64)
            student = StudentPolicyNumpy(student_pt.export_weights_dict())

        sample_obs = [0.1 * i for i in range(23)]

        # Warmup
        for _ in range(50):
            student.predict(sample_obs)

        # 1,000 Step Benchmark
        num_runs = 1000
        start = time.perf_counter()
        for _ in range(num_runs):
            student.predict(sample_obs)
        elapsed = time.perf_counter() - start

        avg_latency_ms = (elapsed / num_runs) * 1000.0
        print(f"\n⚡ Measured StudentPolicyNumpy single-step latency: {avg_latency_ms:.4f} ms")
        self.assertLess(avg_latency_ms, 0.10, "Inference latency must be strictly under 0.1ms")

    def test_hybrid_policy_graceful_fallback(self):
        """AC-3.3: Verify HybridAutonomousPolicy gracefully falls back to APF when weights missing."""
        non_existent_path = Path("/tmp/non_existent_weights_xyz123.json")
        policy = HybridAutonomousPolicy(weights_path=non_existent_path)

        self.assertEqual(policy.current_mode, "classical_apf")
        self.assertIsNone(policy.student_policy)

        dummy_obs = [0.0] * 23
        dummy_obs[20] = 5.0 # Rel X
        dummy_obs[22] = -5.0 # Rel Z

        act = policy.predict(dummy_obs)
        self.assertEqual(len(act), 4)
        for a in act:
            self.assertTrue(-1.0 <= a <= 1.0)

    def test_webgl_simulator_stage_integration(self):
        """AC-4.1 & AC-4.2: Verify HTML simulator contains Stage Inspector UI and JS inference."""
        html_file = Path(__file__).parent / "output" / "flight_test_simulator.html"
        self.assertTrue(html_file.exists(), "Simulator HTML file must exist")

        content = html_file.read_text(encoding="utf-8")

        # UI elements
        self.assertIn("btn-stage-0", content)
        self.assertIn("btn-stage-1", content)
        self.assertIn("btn-stage-2", content)
        self.assertIn("ai-stage-badge", content)

        # JS functions
        self.assertIn("function switchAIStage", content)
        self.assertIn("function predictStudentNeural", content)
        self.assertIn("currentStudentStageKey", content)

    def test_simulator_html_stage_1_no_scope_error(self):
        """FIX-M2.5.2-BUG-2: Verify altErr is hoisted before stage_1_half_trained to prevent ReferenceError."""
        html_file = Path(__file__).parent / "output" / "flight_test_simulator.html"
        self.assertTrue(html_file.exists(), "Simulator HTML file must exist")
        content = html_file.read_text(encoding="utf-8")

        # Verify altErr declaration exists before stage_1_half_trained
        alt_err_decl_idx = content.find("const altErr = targetAlt - drone.position.y;")
        stage_1_idx = content.find("currentStudentStageKey === 'stage_1_half_trained'")

        self.assertNotEqual(alt_err_decl_idx, -1, "altErr declaration must exist")
        self.assertNotEqual(stage_1_idx, -1, "stage_1_half_trained branch must exist")
        self.assertLess(alt_err_decl_idx, stage_1_idx, "altErr must be declared before stage_1_half_trained usage")

        # Verify defensive try-catch in neural inference
        self.assertIn("console.warn('Neural inference error:', e)", content)

    def test_simulator_html_approach_navigation_stage(self):
        """FIX-M2.5.2-BUG-1: Verify APPROACH stage exists and aligns with purple circuit entry points."""
        html_file = Path(__file__).parent / "output" / "flight_test_simulator.html"
        self.assertTrue(html_file.exists(), "Simulator HTML file must exist")
        content = html_file.read_text(encoding="utf-8")

        # Verify APPROACH stage in state machine
        self.assertIn("aiNavStage === 'APPROACH'", content)
        self.assertIn("targetGate.x - targetGate.nx * 2.2", content)
        self.assertIn("targetGate.z - targetGate.nz * 2.2", content)
        self.assertIn("AI 門前進門對齊", content)


if __name__ == "__main__":
    unittest.main()

