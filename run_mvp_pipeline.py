#!/usr/bin/env python3
"""
Digital Twin Drone MVP - End-to-End Orchestration Pipeline
Block 5: Orchestrates Mission Spec -> Morph Evolution -> URDF/SDF Building -> MAVLink SITL Autonomous Flight -> Telemetry Report Export.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any

from db_loader import ComponentDB
from morph_evolution import MorphEvolutionEngine
from drone_builder import DroneBuilder
from mavlink_controller import MAVLinkController

class DigitalTwinPipeline:
    """End-to-End Orchestration pipeline for digital twin drones."""

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = Path(workspace_dir)
        self.output_dir = self.workspace_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.db = ComponentDB(self.workspace_dir / "components_db.json")
        self.evolution_engine = MorphEvolutionEngine(self.db)
        self.builder = DroneBuilder(self.db)
        self.mavlink = MAVLinkController(simulate=True)

    def run_pipeline(self, mission_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the full digital twin workflow from prompt to flight telemetry."""
        print(f"\n========================================================")
        print(f"🚀 Starting Digital Twin Pipeline for Mission: {mission_spec.get('mission_type')}")
        print(f"========================================================")

        # Stage 1: Morph Evolution
        print("\n[Stage 1/4] Morphing & Evolving Drone Configuration...")
        evolved_spec = self.evolution_engine.evolve(mission_spec, population_size=30, generations=15)
        print(f"  ✓ Evolved Shape: {evolved_spec['num_arms']}-arm frame, arm_length={evolved_spec['arm_length_m']}m")
        print(f"  ✓ Selected Motor: {evolved_spec['motor_id']}, Battery: {evolved_spec['battery_id']}")

        # Stage 2: Dynamic CAD & URDF/SDF Generation
        print("\n[Stage 2/4] Generating Physics-Accurate URDF & SDF Models...")
        model_paths = self.builder.export_files(evolved_spec, self.output_dir)
        print(f"  ✓ URDF Exported: {model_paths['urdf'].name}")
        print(f"  ✓ SDF Exported:  {model_paths['sdf'].name}")

        # Stage 3: MAVLink Autonomous SITL Flight Execution
        print("\n[Stage 3/4] Executing MAVLink Autonomous Offboard Flight...")
        self.mavlink.connect()
        self.mavlink.arm()
        self.mavlink.takeoff(target_altitude_m=2.5)

        # Execute waypoints based on mission type
        waypoints = [
            (2.0, 2.0, 2.5, 0.0),
            (2.0, -2.0, 2.5, 90.0),
            (0.0, 0.0, 2.5, 180.0)
        ]
        for wp in waypoints:
            self.mavlink.goto_location(*wp)
            time.sleep(0.05)

        self.mavlink.land()
        telemetry = self.mavlink.telemetry_history

        # Stage 4: Digital Twin Telemetry & Report Export
        print("\n[Stage 4/4] Exporting Digital Twin Summary & Telemetry Log...")
        report = {
            "timestamp": time.time(),
            "mission_spec": mission_spec,
            "evolved_drone_spec": evolved_spec,
            "drone_stats": evolved_spec.get("stats", {}),
            "generated_files": {
                "urdf": str(model_paths["urdf"]),
                "sdf": str(model_paths["sdf"])
            },
            "telemetry_log_frames": len(telemetry),
            "status": "SUCCESS"
        }

        report_path = self.output_dir / f"digital_twin_report_{evolved_spec['design_id']}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(f"  ✓ Digital Twin Session Report: {report_path.name}")
        print(f"========================================================")
        print(f"✅ Digital Twin End-to-End MVP Completed Successfully!")
        print(f"========================================================\n")
        return report


if __name__ == "__main__":
    current_dir = Path(__file__).parent
    pipeline = DigitalTwinPipeline(current_dir)

    sample_mission = {
        "mission_type": "bridge_structure_inspection",
        "max_size_m": 0.50,
        "min_flight_time_min": 12.0,
        "required_sensors": ["s_lidar_2d", "s_depth_cam"]
    }

    pipeline.run_pipeline(sample_mission)
