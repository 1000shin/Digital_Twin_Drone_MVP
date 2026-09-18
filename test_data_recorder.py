#!/usr/bin/env python3
"""
Unit tests for WebGL 3D Flight Data Recorder & Pilot Reset Questionnaire System (DIG-12)
Validates state-action trajectory logging, 20Hz sampling fields, imitation learning datasets,
and prompt questionnaire schema.
"""

import unittest
import json
from pathlib import Path
from flight_test_sim import WebGLFlightSimulator

class TestFlightDataRecorder(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = Path(__file__).parent
        self.output_dir = self.workspace_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.datasets_dir = self.output_dir / "training_datasets"
        self.datasets_dir.mkdir(parents=True, exist_ok=True)

        self.sample_drone = {
            "aircraft_type": "vtol_tilt_rotor",
            "wingspan_m": 1.25,
            "wing_chord_m": 0.22,
            "num_arms": 6,
            "arm_length_m": 0.26,
            "motor_id": "m_2212_920kv",
            "battery_id": "b_3s_2200mah",
            "sensors_mount": [{"sensor_id": "s_lidar_2d"}, {"sensor_id": "s_depth_cam"}]
        }

        self.sample_world = {
            "wind_velocity_xyz": [2.5, 0.5, 0.0],
            "obstacles": [
                {"type": "cylinder", "pos": [2.5, 0.5, 1.5], "size": [0.4, 0.4, 3.0]},
                {"type": "box", "pos": [4.0, -1.5, 1.0], "size": [1.0, 1.0, 2.0]}
            ]
        }

    def test_flight_recorder_html_elements_and_ui(self):
        """Verifies HUD controls, G shortcut, record indicators, and questionnaire modal."""
        sim = WebGLFlightSimulator(self.output_dir)
        test_file = "test_recorder_sim.html"
        html_path = sim.generate_simulator_html(self.sample_drone, self.sample_world, test_file)
        self.assertTrue(html_path.exists())

        content = html_path.read_text(encoding="utf-8")

        # 1. Check Recorder UI Controls & HUD
        self.assertIn('recorder-section', content)
        self.assertIn('id="rec-status-badge"', content)
        self.assertIn('id="rec-status-text"', content)
        self.assertIn('id="rec-time"', content)
        self.assertIn('id="rec-samples"', content)
        self.assertIn('id="btn-rec-toggle"', content)
        self.assertIn('id="btn-rec-export"', content)
        self.assertIn('toggleRecording()', content)
        self.assertIn('exportFlightData()', content)

        # 2. Check Keyboard Shortcuts
        self.assertIn("KeyG", content)
        self.assertIn("KeyR", content)
        self.assertIn(">G</span> 錄製/停止", content)

        # 3. Check Reset Questionnaire Modal
        self.assertIn('id="reset-modal-overlay"', content)
        self.assertIn('id="reset-modal"', content)
        self.assertIn('id="modal-reset-reason"', content)
        self.assertIn('id="modal-handling-rating"', content)
        self.assertIn('id="modal-notes"', content)
        self.assertIn('promptResetExperience', content)
        self.assertIn('confirmResetWithFeedback', content)
        self.assertIn('closeResetModal', content)

        # 4. Check State-Action Fields
        self.assertIn("sampleRecorderStep", content)
        self.assertIn("pitch_cmd", content)
        self.assertIn("roll_cmd", content)
        self.assertIn("yaw_cmd", content)
        self.assertIn("climb_cmd", content)
        self.assertIn("linear_velocity", content)
        self.assertIn("attitude_rad", content)
        self.assertIn("angular_velocity", content)
        self.assertIn("integrity", content)
        self.assertIn("collision_event", content)
        self.assertIn("activeCollisionThisStep", content)

        # Clean up
        if html_path.exists():
            html_path.unlink()

    def test_sample_training_dataset_format_integrity(self):
        """Verifies that generated imitation learning dataset has matching JSON & JSONL schemas."""
        sample_json_path = self.datasets_dir / "flight_training_data_sample.json"
        sample_jsonl_path = self.datasets_dir / "flight_training_data_sample.jsonl"

        self.assertTrue(sample_json_path.exists(), "Sample JSON dataset must exist in output/training_datasets/")
        self.assertTrue(sample_jsonl_path.exists(), "Sample JSONL dataset must exist in output/training_datasets/")

        # Verify JSON
        with open(sample_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("dataset_name", data)
        self.assertIn("sampling_rate_hz", data)
        self.assertEqual(data["sampling_rate_hz"], 20)
        self.assertIn("trajectory", data)
        self.assertGreater(len(data["trajectory"]), 0)

        step_zero = data["trajectory"][0]
        self.assertIn("step", step_zero)
        self.assertIn("timestamp", step_zero)
        self.assertIn("state", step_zero)
        self.assertIn("action", step_zero)
        self.assertIn("environment", step_zero)

        state = step_zero["state"]
        self.assertIn("position", state)
        self.assertEqual(len(state["position"]), 3)
        self.assertIn("linear_velocity", state)
        self.assertEqual(len(state["linear_velocity"]), 3)
        self.assertIn("attitude_rad", state)
        self.assertEqual(len(state["attitude_rad"]), 3)
        self.assertIn("angular_velocity", state)
        self.assertEqual(len(state["angular_velocity"]), 3)
        self.assertIn("integrity", state)
        self.assertIn("battery_voltage", state)

        action = step_zero["action"]
        self.assertIn("pitch_cmd", action)
        self.assertIn("roll_cmd", action)
        self.assertIn("yaw_cmd", action)
        self.assertIn("climb_cmd", action)

        env = step_zero["environment"]
        self.assertIn("environment_id", env)
        self.assertIn("wind_velocity", env)

        # Check questionnaire section
        self.assertIn("pilot_questionnaires", data)

        # Verify JSONL lines
        with open(sample_jsonl_path, "r", encoding="utf-8") as f:
            lines = [json.loads(line.strip()) for line in f if line.strip()]

        self.assertGreaterEqual(len(lines), 1)
        self.assertIn("state", lines[0])
        self.assertIn("action", lines[0])

if __name__ == "__main__":
    unittest.main()