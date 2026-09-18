#!/usr/bin/env python3
"""
Digital Twin Drone - Interactive CLI Entrypoint
Phase 2: Allows users to run pre-defined or custom mission prompts, trigger morphological evolution,
build 3D SDF physics models, generate Gazebo worlds with wind/obstacles, and simulate MAVLink SITL flight.
"""

import sys
import json
import time
from pathlib import Path

from db_loader import ComponentDB
from morph_evolution import MorphEvolutionEngine
from drone_builder import DroneBuilder
from mavlink_controller import MAVLinkController
from world_builder import WorldBuilder
from sensor_sim import SensorCoverageSimulator
from px4_sitl_bridge import PX4SITLBridge
from foxglove_bridge import FoxgloveStreamer

def main():
    print("\n==========================================================================")
    print("🚁 Digital Twin Drone Generative & Autonomous Simulation Environment")
    print("==========================================================================")

    workspace_dir = Path(__file__).parent
    output_dir = workspace_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load databases
    db = ComponentDB(workspace_dir / "components_db.json")
    with open(workspace_dir / "mission_profiles.json", "r", encoding="utf-8") as f:
        missions_data = json.load(f)["missions"]

    print("\n📋 Available Preset Missions:")
    for idx, m in enumerate(missions_data):
        print(f"  [{idx + 1}] {m['name']} ({m['id']})")
        print(f"      - Description: {m['description']}")

    # Default to Mission 1 if run non-interactively
    selected_idx = 0
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        selected_idx = int(sys.argv[1]) - 1

    mission = missions_data[max(0, min(selected_idx, len(missions_data) - 1))]
    print(f"\n🎯 Selected Mission: {mission['name']}")

    # 1. Evolve Drone / VTOL
    is_vtol = mission.get("mission_type") == "vtol_tilt_rotor"
    if is_vtol:
        print("\n🛩️ [Choice 2] Evolving VTOL Morphing Wing & Tilt-Rotor Aircraft...")
        from vtol_evolution import VTOLEvolutionEngine
        from vtol_builder import VTOLBuilder
        vtol_engine = VTOLEvolutionEngine(db)
        evolved_spec = vtol_engine.evolve_vtol(mission, population_size=40, generations=20)
        print(f"  ✓ VTOL Wingspan:   {evolved_spec['wingspan_m']}m, Wing Chord: {evolved_spec['wing_chord_m']}m")
        print(f"  ✓ Tilt Servos:     {evolved_spec['num_tilt_servos']}x 0-90° Servos")
        print(f"  ✓ Selected Motor:  {evolved_spec['motor_id']}")
    else:
        print("\n🧬 [1/5] Evolving Morphological Frame & Sensor Configuration...")
        engine = MorphEvolutionEngine(db)
        evolved_spec = engine.evolve(mission, population_size=40, generations=20)
        print(f"  ✓ Frame Structure: {evolved_spec['num_arms']}-Arm Frame, Arm Length: {evolved_spec['arm_length_m']}m")
        print(f"  ✓ Selected Motor:  {evolved_spec['motor_id']}")

    print(f"  ✓ Selected Prop:   {evolved_spec['prop_id']}")
    print(f"  ✓ Selected Battery: {evolved_spec['battery_id']}")

    # 2. Sensor Coverage Evaluation
    print("\n📡 [2/5] Evaluating Sensor Field of View (FOV) & Coverage...")
    sensor_sim = SensorCoverageSimulator()
    sensor_db_lookup = {s["id"]: s for s in db.list_components("sensors")}
    coverage_metrics = sensor_sim.calculate_sensor_coverage(evolved_spec["sensors_mount"], sensor_db_lookup)
    print(f"  ✓ Active Sensors:   {coverage_metrics['sensor_count']}")
    print(f"  ✓ Total FOV:        {coverage_metrics['total_fov_deg']}°")
    print(f"  ✓ Coverage Ratio:   {coverage_metrics['coverage_ratio'] * 100:.1f}% (Blind Spot: {coverage_metrics['blind_spot_ratio'] * 100:.1f}%)")

    # 3. Build URDF & SDF Physics Models
    print("\n🛠️ [3/5] Building URDF & SDF 3D Physics Mesh Models...")
    if is_vtol:
        vtol_builder = VTOLBuilder(db)
        model_paths = vtol_builder.export_vtol_files(evolved_spec, output_dir)
    else:
        builder = DroneBuilder(db)
        model_paths = builder.export_files(evolved_spec, output_dir)

    print(f"  ✓ Exported URDF: {model_paths['urdf'].name}")
    print(f"  ✓ Exported SDF:  {model_paths['sdf'].name}")

    # 4. Build Gazebo World with Wind & Obstacles
    print("\n🌍 [4/5] Generating Gazebo 3D World (Wind & Obstacles)...")
    world_builder = WorldBuilder(output_dir)
    world_file = world_builder.export_world(
        world_name=f"world_{mission['id']}",
        wind_velocity_xyz=mission.get("wind_velocity_xyz", [0, 0, 0]),
        obstacles=mission.get("obstacles", [])
    )
    print(f"  ✓ Exported Gazebo World: {world_file.name}")

    # 5. MAVLink SITL Autonomous Flight Simulation
    print("\n✈️ [5/5] Executing MAVLink Autonomous SITL Flight...")
    mavlink = MAVLinkController(simulate=True)
    mavlink.connect()
    mavlink.arm()
    mavlink.takeoff(target_altitude_m=3.0)
    mavlink.goto_location(x=4.0, y=2.0, z=3.0, yaw_deg=45.0)
    mavlink.goto_location(x=0.0, y=0.0, z=3.0, yaw_deg=180.0)
    mavlink.land()

    # 6. Native PX4 SITL & 3D GUI Launcher Bridge
    print("\n🖥️ [Choice 3] Initializing Native PX4 SITL & Gazebo 3D GUI Bridge...")
    sitl_bridge = PX4SITLBridge(workspace_dir)
    bridge_res = sitl_bridge.launch_gui_simulation(model_paths['sdf'], world_file)
    print(f"  ✓ Native 3D GUI Process PID: {bridge_res['pid']}")
    print(f"  ✓ Offboard MAVLink Port: UDP {bridge_res['mavlink_offboard_port']}")
    print(f"  ✓ QGroundControl Port: UDP {bridge_res['qgroundcontrol_port']}")

    # 7. Foxglove Studio Dashboard Export (Choice 1)
    print("\n📊 [Choice 1] Exporting Foxglove Studio 3D Dashboard Telemetry Stream...")
    foxglove_streamer = FoxgloveStreamer(output_dir)
    foxglove_log_path = foxglove_streamer.export_foxglove_log(mavlink.telemetry_history, mission['id'])
    print(f"  ✓ Foxglove Studio 3D Stream Log: {foxglove_log_path.name}")
    print(f"  ✓ Foxglove Studio Layout Config: foxglove_layout.json")

    print(f"  ✓ QGroundControl Live Stream Active on UDP 14550 for 15s...")

    # Keep telemetry stream alive for QGC display
    time.sleep(15.0)

    # 8. Interactive 3D WebGL Mesh & Environment Viewer
    print("\n🎨 [3D Viewer] Generating Interactive 3D Mesh & Test Space Viewer...")
    from view_3d_drone import Interactive3DViewer
    from flight_test_sim import WebGLFlightSimulator

    interactive_viewer = Interactive3DViewer(output_dir)
    html_3d_path = interactive_viewer.generate_html_3d_scene(evolved_spec, mission, f"view_3d_{mission['id']}.html")
    print(f"  ✓ Interactive 3D Scene WebGL HTML: {html_3d_path.name}")

    # 9. WebGL 3D Flight Test Simulator (Keyboard Flight Control + Gazebo World Collisions)
    flight_sim = WebGLFlightSimulator(output_dir)
    sim_html_path = flight_sim.generate_simulator_html(evolved_spec, mission, f"flight_sim_{mission['id']}.html")
    print(f"  🎮 [WebGL Flight Test] 3D Keyboard Flight Simulator: {sim_html_path.name}")
    print(f"  👉 Open Flight Simulator in Browser: file://{sim_html_path.resolve()}")

    # Save Session Summary
    summary = {
        "mission": mission,
        "evolved_spec": evolved_spec,
        "coverage_metrics": coverage_metrics,
        "world_file": str(world_file),
        "sdf_model": str(model_paths["sdf"]),
        "telemetry_frames": len(mavlink.telemetry_history),
        "bridge_status": bridge_res
    }
    summary_path = output_dir / f"session_summary_{mission['id']}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n==========================================================================")
    print(f"✅ Digital Twin Execution Completed Successfully!")
    print(f"📊 Session Summary Saved To: {summary_path.name}")
    print(f"==========================================================================\n")

if __name__ == "__main__":
    main()
