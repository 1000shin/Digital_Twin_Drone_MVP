#!/usr/bin/env python3
"""
Unit tests for WebGL 3D Flight Simulator & Interactive 3D Viewer Scene Environments Switching
"""

import unittest
from pathlib import Path
from flight_test_sim import WebGLFlightSimulator
from view_3d_drone import Interactive3DViewer

class TestWebGLEnvironments(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = Path(__file__).parent
        self.output_dir = self.workspace_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

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

    def tearDown(self):
        for f in ["test_flight_simulator.html", "test_3d_scene.html"]:
            p = self.output_dir / f
            if p.exists():
                p.unlink()

    def test_flight_simulator_html_generation(self):
        sim = WebGLFlightSimulator(self.output_dir)
        html_file = sim.generate_simulator_html(self.sample_drone, self.sample_world, "test_flight_simulator.html")
        self.assertTrue(html_file.exists())

        content = html_file.read_text(encoding="utf-8")
        self.assertIn('id="env-select"', content)
        self.assertIn('value="offshore_wind"', content)
        self.assertIn('value="urban_city"', content)
        self.assertIn('value="collision_arena"', content)
        self.assertIn('value="night_thermal"', content)

        self.assertIn("離岸風場巡檢", content)
        self.assertIn("城市高樓搜救", content)
        self.assertIn("碰撞測試場地", content)
        self.assertIn("夜間紅外線巡檢", content)

        self.assertIn("switchEnvironment", content)
        self.assertIn("turbineRotors", content)
        self.assertIn("oceanGeo", content)
        self.assertIn("rescueBeacon", content)
        self.assertIn("thermal-hud", content)
        self.assertIn("droneSpotlight", content)
        self.assertIn("activeObstacles", content)

    def test_interactive_3d_viewer_html_generation(self):
        viewer = Interactive3DViewer(self.output_dir)
        html_file = viewer.generate_html_3d_scene(self.sample_drone, self.sample_world, "test_3d_scene.html")
        self.assertTrue(html_file.exists())

        content = html_file.read_text(encoding="utf-8")
        self.assertIn('id="env-select"', content)
        self.assertIn('value="offshore_wind"', content)
        self.assertIn('value="urban_city"', content)
        self.assertIn('value="collision_arena"', content)
        self.assertIn('value="night_thermal"', content)
        self.assertIn("switchEnvironment", content)
        self.assertIn("thermal-hud", content)

    def test_flight_simulator_damage_simulation_system(self):
        """Validates that flight test simulator generates all crash and structural damage mechanics."""
        sim = WebGLFlightSimulator(self.output_dir)
        html_file = sim.generate_simulator_html(self.sample_drone, self.sample_world, "test_flight_simulator.html")
        self.assertTrue(html_file.exists())

        content = html_file.read_text(encoding="utf-8")

        # 1. Damage & Integrity HUD & Health Indicators
        self.assertIn('id="st-integrity"', content)
        self.assertIn('id="st-integrity-bar"', content)
        self.assertIn('id="damage-panel"', content)
        self.assertIn('id="damage-list"', content)
        self.assertIn('id="damage-count"', content)
        self.assertIn('id="btn-repair"', content)
        self.assertIn('id="btn-crash-test"', content)

        # 2. BOM Component Status Integration
        self.assertIn('id="bom-meta-health"', content)
        self.assertIn('id="bom-tag-frame"', content)
        self.assertIn('id="bom-tag-motors"', content)
        self.assertIn('id="bom-tag-props"', content)
        self.assertIn('id="bom-val-twr"', content)

        # 3. Component Tracking & Physics Imbalance
        self.assertIn("droneArmComponents", content)
        self.assertIn("CRASH_SPEED_THRESHOLD", content)
        self.assertIn("applyStructuralDamage", content)
        self.assertIn("updateDamageHUD", content)
        self.assertIn("repairAndResetDrone", content)
        self.assertIn("simulateTestCrash", content)
        self.assertIn("intactRatio", content)
        self.assertIn("isCatastrophic", content)

        # 4. Particle FX (Sparks & Carbon Fiber Debris)
        self.assertIn("activeSparks", content)
        self.assertIn("activeDebris", content)
        self.assertIn("triggerDamageFX", content)
        self.assertIn("cameraShakeTimer", content)

    def test_interactive_3d_viewer_damage_inspection(self):
        """Validates that interactive 3D viewer supports CAD structural damage preview and reset."""
        viewer = Interactive3DViewer(self.output_dir)
        html_file = viewer.generate_html_3d_scene(self.sample_drone, self.sample_world, "test_3d_scene.html")
        self.assertTrue(html_file.exists())

        content = html_file.read_text(encoding="utf-8")

        self.assertIn('id="cad-integrity"', content)
        self.assertIn('id="cad-integrity-bar"', content)
        self.assertIn('id="btn-sim-damage"', content)
        self.assertIn('id="btn-repair-cad"', content)
        self.assertIn("simulateCADCrashDamage", content)
        self.assertIn("repairCADModel", content)
        self.assertIn('id="bom-tag-frame"', content)
        self.assertIn('id="bom-tag-props"', content)

if __name__ == "__main__":
    unittest.main()

