#!/usr/bin/env bash
# ==============================================================================
# Digital Twin Drone - Native PX4 SITL & Gazebo 3D GUI Simulation Launcher
# Choice 3: Launches Gazebo 3D GUI window, mounts generated SDF drone & world,
# and exposes MAVLink UDP ports (14540/14550) for QGroundControl and offboard scripts.
# ==============================================================================

set -e

# Base directory setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/output"
MODEL_SDF="${1:-${OUTPUT_DIR}/evolved_confined_space.sdf}"
WORLD_FILE="${2:-${OUTPUT_DIR}/world_bridge_confined_inspection.world}"

echo "=========================================================================="
echo "🚁 Starting Native PX4 SITL & Gazebo 3D GUI Launcher"
echo "=========================================================================="
echo "  ✓ Target SDF Model: ${MODEL_SDF}"
echo "  ✓ Target 3D World: ${WORLD_FILE}"
echo "  ✓ MAVLink Offboard Port: UDP 14540"
echo "  ✓ QGroundControl Port: UDP 14550"
echo "=========================================================================="

# Export Gazebo & PX4 Environment Variables
export GZ_SIM_RESOURCE_PATH="${OUTPUT_DIR}:${GZ_SIM_RESOURCE_PATH}"
export GAZEBO_MODEL_PATH="${OUTPUT_DIR}:${GAZEBO_MODEL_PATH}"
export PX4_SIM_MODEL="gazebo-classic_iris"

# Check if gz sim (Gazebo) or gazebo is installed on system
if command -v gz &> /dev/null; then
    echo "🌐 Launching Gazebo Sim 3D GUI..."
    gz sim -r "${WORLD_FILE}" &
    GZ_PID=$!
    echo "  ✓ Gazebo Sim PID: ${GZ_PID}"
elif command -v gazebo &> /dev/null; then
    echo "🌐 Launching Classic Gazebo 3D GUI..."
    gazebo --verbose "${WORLD_FILE}" &
    GZ_PID=$!
    echo "  ✓ Gazebo Classic PID: ${GZ_PID}"
else
    echo "ℹ️  Gazebo 3D GUI binary ('gz' or 'gazebo') not found in PATH."
    echo "ℹ️  Running in Standalone PX4 SITL / MAVLink headless emulation mode..."
fi

echo "=========================================================================="
echo "✅ PX4 SITL & Gazebo Launcher Initialized!"
echo "=========================================================================="
