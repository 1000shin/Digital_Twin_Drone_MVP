#!/usr/bin/env python3
"""
Digital Twin Drone - PX4 SITL & 3D GUI Native Launcher Bridge
Choice 3: Connects generated SDF models & Gazebo worlds to native PX4 SITL firmware daemon,
providing QGroundControl telemetry routing (UDP 14550) and 3D visual rendering.
"""

import subprocess
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional

class PX4SITLBridge:
    """Bridge for launching native PX4 SITL firmware and 3D Gazebo GUI windows."""

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = Path(workspace_dir)
        self.output_dir = self.workspace_dir / "output"

    def check_system_installations(self) -> Dict[str, bool]:
        """Checks availability of native simulation binaries (Gazebo, PX4, QGroundControl)."""
        return {
            "gazebo_sim": shutil.which("gz") is not None or shutil.which("gazebo") is not None,
            "px4_sitl": shutil.which("px4") is not None,
            "qgroundcontrol": shutil.which("qgroundcontrol") is not None or Path("/Applications/QGroundControl.app").exists()
        }

    def prepare_environment(self, sdf_model_path: Path, world_path: Path) -> Dict[str, str]:
        """Prepares environment variables for PX4 and Gazebo."""
        env_vars = {
            "GZ_SIM_RESOURCE_PATH": str(self.output_dir),
            "GAZEBO_MODEL_PATH": str(self.output_dir),
            "PX4_SIM_MODEL": "gazebo-classic_iris"
        }
        return env_vars

    def launch_gui_simulation(self, sdf_model_path: Path, world_path: Path, run_bg: bool = True) -> Dict[str, Any]:
        """Launches the bash launcher script for 3D GUI & PX4 SITL."""
        script_path = self.workspace_dir / "launch_simulation.sh"
        if not script_path.exists():
            raise FileNotFoundError(f"Launcher script missing at: {script_path}")

        cmd = [str(script_path), str(sdf_model_path), str(world_path)]
        print(f"\n🚀 Invoking PX4 SITL & 3D GUI Launcher: {' '.join(cmd)}")

        status = self.check_system_installations()
        print(f"  ✓ System Gazebo 3D Engine: {'Found' if status['gazebo_sim'] else 'Emulated (Headless)'}")
        print(f"  ✓ Native PX4 SITL Binary:   {'Found' if status['px4_sitl'] else 'Emulated (MAVLink)'}")
        print(f"  ✓ QGroundControl Station:   {'Found' if status['qgroundcontrol'] else 'Listening on UDP 14550'}")

        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.2)

        return {
            "pid": proc.pid,
            "script": str(script_path),
            "model": str(sdf_model_path),
            "world": str(world_path),
            "mavlink_offboard_port": 14540,
            "qgroundcontrol_port": 14550,
            "system_status": status
        }


if __name__ == "__main__":
    workspace = Path(__file__).parent
    output = workspace / "output"
    bridge = PX4SITLBridge(workspace)

    sample_sdf = output / "evolved_confined_space.sdf"
    sample_world = output / "world_bridge_confined_inspection.world"

    res = bridge.launch_gui_simulation(sample_sdf, sample_world)
    print("\nBridge Launch Result Summary:", res)
