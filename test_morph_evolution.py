#!/usr/bin/env python3
"""
Unit tests for Block 4 Mission-Driven Morphological & Sensor Evolution Engine
and Evolutionary Change & Lineage Explainability Engine.
"""

import unittest
import json
from pathlib import Path
from db_loader import ComponentDB
from morph_evolution import MorphEvolutionEngine, EvolutionExplainabilityEngine

class TestMorphEvolutionEngine(unittest.TestCase):

    def setUp(self):
        self.db = ComponentDB()
        self.engine = MorphEvolutionEngine(self.db)
        self.tracker = EvolutionExplainabilityEngine(self.db)
        self.test_output_dir = Path(__file__).parent / "test_output"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)

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

    def test_explainability_arm_length_rationale(self):
        """Tests morphological rationale for arm shortening to eliminate size penalty (-300)."""
        mission_spec = {
            "mission_type": "tight_tunnel",
            "max_size_m": 0.60,
            "min_flight_time_min": 10.0,
            "required_sensors": []
        }

        ind_before = {
            "num_arms": 4,
            "arm_length_m": 0.35,  # diameter = 0.35 * 2 + 0.15 = 0.85m (> 0.60m)
            "motor_id": "m_2212_920kv",
            "prop_id": "p_1045",
            "battery_id": "b_3s_2200mah",
            "sensors_mount": []
        }

        ind_after = {
            "num_arms": 4,
            "arm_length_m": 0.22,  # diameter = 0.22 * 2 + 0.15 = 0.59m (<= 0.60m)
            "motor_id": "m_2212_920kv",
            "prop_id": "p_1045",
            "battery_id": "b_3s_2200mah",
            "sensors_mount": []
        }

        analysis = self.tracker.explain_change(ind_before, ind_after, mission_spec, gen=2)
        self.assertEqual(len(analysis["decisions"]), 1)
        decision = analysis["decisions"][0]
        self.assertEqual(decision["component"], "arm_length")
        self.assertEqual(decision["action"], "eliminate_size_penalty")
        self.assertIn("縮短機臂長度", decision["rationale"])
        self.assertIn("消除約束懲罰 (-300)", decision["rationale"])
        self.assertGreater(analysis["fitness_delta"], 250.0)

    def test_explainability_battery_upgrade_rationale(self):
        """Tests morphological rationale for battery upgrade to achieve flight time threshold."""
        mission_spec = {
            "mission_type": "patrol",
            "max_size_m": 1.0,
            "min_flight_time_min": 10.0,
            "required_sensors": ["s_lidar_2d", "s_depth_cam"]
        }

        # With 4 arms and heavy sensors, 3S 1500mah yields flight time ~7.8min (< 10.0min)
        ind_before = {
            "num_arms": 4,
            "arm_length_m": 0.25,
            "motor_id": "m_2212_920kv",
            "prop_id": "p_1045",
            "battery_id": "b_3s_1500mah",
            "sensors_mount": [
                {"sensor_id": "s_lidar_2d", "rel_pos_xyz": [0, 0, 0.05]},
                {"sensor_id": "s_depth_cam", "rel_pos_xyz": [0, 0, 0.05]}
            ]
        }

        ind_after = {
            "num_arms": 4,
            "arm_length_m": 0.25,
            "motor_id": "m_2212_920kv",
            "prop_id": "p_1045",
            "battery_id": "b_6s_5000mah",
            "sensors_mount": [
                {"sensor_id": "s_lidar_2d", "rel_pos_xyz": [0, 0, 0.05]},
                {"sensor_id": "s_depth_cam", "rel_pos_xyz": [0, 0, 0.05]}
            ]
        }

        analysis = self.tracker.explain_change(ind_before, ind_after, mission_spec, gen=3)
        self.assertEqual(len(analysis["decisions"]), 1)
        decision = analysis["decisions"][0]
        self.assertEqual(decision["component"], "battery")
        self.assertEqual(decision["action"], "achieve_flight_time_threshold")
        self.assertIn("升級", decision["rationale"])
        self.assertIn("未達任務門檻", decision["rationale"])
        self.assertIn("獲得續航加成", decision["rationale"])

    def test_explainability_motor_prop_rationale(self):
        """Tests morphological rationale for motor and propeller upgrade for TWR safety & optimal bonus."""
        mission_spec = {
            "mission_type": "heavy_payload",
            "max_size_m": 1.5,
            "min_flight_time_min": 5.0,
            "required_sensors": ["s_lidar_2d", "s_lidar_2d", "s_depth_cam"]
        }

        # 4 small 1806 motors with heavy 6S battery and 2x lidar -> TWR ~1.28 (< 1.5 unsafe)
        ind_before = {
            "num_arms": 4,
            "arm_length_m": 0.30,
            "motor_id": "m_1806_2300kv",
            "prop_id": "p_0504",
            "battery_id": "b_6s_5000mah",
            "sensors_mount": [
                {"sensor_id": "s_lidar_2d", "rel_pos_xyz": [0, 0, 0.05]},
                {"sensor_id": "s_lidar_2d", "rel_pos_xyz": [0, 0, 0.05]},
                {"sensor_id": "s_depth_cam", "rel_pos_xyz": [0, 0, 0.05]}
            ]
        }

        # Upgrade to 2212 motors + 1045 props -> TWR ~2.27 (within 1.8 - 2.8 optimal window)
        ind_after = {
            "num_arms": 4,
            "arm_length_m": 0.30,
            "motor_id": "m_2212_920kv",
            "prop_id": "p_1045",
            "battery_id": "b_6s_5000mah",
            "sensors_mount": [
                {"sensor_id": "s_lidar_2d", "rel_pos_xyz": [0, 0, 0.05]},
                {"sensor_id": "s_lidar_2d", "rel_pos_xyz": [0, 0, 0.05]},
                {"sensor_id": "s_depth_cam", "rel_pos_xyz": [0, 0, 0.05]}
            ]
        }

        analysis = self.tracker.explain_change(ind_before, ind_after, mission_spec, gen=4)
        propulsion_decisions = [d for d in analysis["decisions"] if d["component"] == "propulsion"]
        self.assertEqual(len(propulsion_decisions), 1)
        decision = propulsion_decisions[0]
        self.assertEqual(decision["action"], "twr_safety_and_optimal")
        self.assertIn("更換", decision["rationale"])
        self.assertIn("低於安全下限 (1.5)", decision["rationale"])
        self.assertIn("進入最佳區間 (+30 分)", decision["rationale"])

    def test_evolution_reasoning_and_decisions_integration(self):
        """Tests full evolve pipeline attaches evolution_reasoning_log and morph_decisions."""
        mission_spec = {
            "mission_type": "inspection_test",
            "max_size_m": 0.60,
            "min_flight_time_min": 12.0,
            "required_sensors": ["s_depth_cam"]
        }

        best_spec = self.engine.evolve(
            mission_spec,
            population_size=25,
            generations=12,
            output_dir=self.test_output_dir
        )

        # Check logs and decisions
        self.assertIn("evolution_reasoning_log", best_spec)
        self.assertIn("morph_decisions", best_spec)
        self.assertIn("lineage_trail", best_spec)
        self.assertIn("stats", best_spec)
        self.assertGreater(len(best_spec["evolution_reasoning_log"]), 0)
        self.assertGreater(len(best_spec["morph_decisions"]), 0)
        self.assertGreater(len(best_spec["lineage_trail"]), 0)

        # First entry must be Gen 0 seed
        first_log = best_spec["evolution_reasoning_log"][0]
        self.assertIn("[Gen 0 初始種子奠定]", first_log)

        # Verify structured morph decision schema
        first_decision = best_spec["morph_decisions"][0]
        for key in ["generation", "component", "action", "change", "rationale", "fitness_delta"]:
            self.assertIn(key, first_decision)

        # Check export report files
        report_md = self.test_output_dir / "evolution_lineage_report.md"
        history_json = self.test_output_dir / "evolution_history.json"
        self.assertTrue(report_md.exists())
        self.assertTrue(history_json.exists())

        # Verify JSON is valid and structured
        with open(history_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("mission_spec", data)
        self.assertIn("final_best_spec", data)
        self.assertIn("breakthrough_trail", data)
        self.assertIn("morph_decisions", data)

        # Verify Markdown contains core headings
        with open(report_md, "r", encoding="utf-8") as f:
            md_text = f.read()
        self.assertIn("# 🧬 DEAP 形態演化決策與變遷原因溯源報告", md_text)
        self.assertIn("世代躍遷決策歷史", md_text)
        self.assertIn("形態變革動機日誌", md_text)
        self.assertIn("結構化變更決策矩陣", md_text)

if __name__ == "__main__":
    unittest.main()

