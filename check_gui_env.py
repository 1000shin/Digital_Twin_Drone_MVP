#!/usr/bin/env python3
"""
Digital Twin Drone - GUI Environment Diagnostic & Quick-Launch Helper
"""

import shutil
import subprocess
from pathlib import Path

def main():
    print("\n==========================================================================")
    print("🔍 Digital Twin Drone - 3D GUI & Ground Station Environment Diagnostic")
    print("==========================================================================")

    gz_sim = shutil.which("gz")
    gazebo_classic = shutil.which("gazebo")
    qgc_app = Path("/Applications/QGroundControl.app").exists() or shutil.which("qgroundcontrol") is not None

    print(f"  1. Gazebo Sim 3D Engine (gz):       {'✅ Installed (' + gz_sim + ')' if gz_sim else '❌ Not Found'}")
    print(f"  2. Gazebo Classic (gazebo):         {'✅ Installed (' + gazebo_classic + ')' if gazebo_classic else '❌ Not Found'}")
    print(f"  3. QGroundControl (QGC App):        {'✅ Installed' if qgc_app else '❌ Not Found'}")
    print("==========================================================================")

    if not gz_sim and not gazebo_classic:
        print("\n💡 提示：目前系統尚未安裝 Gazebo 3D 物理渲染視窗 (gz / gazebo)。")
        print("   您可以透過 Homebrew (macOS) 一鍵安裝 Gazebo Sim 3D GUI：")
        print("   👉 macOS 安裝指令： brew install gz-sim")
        print("   👉 Ubuntu 安裝指令：sudo apt install ros-humble-ros-gz")

    if not qgc_app:
        print("\n💡 提示：若需使用無人機地面站 UI（顯示 3D 姿態儀與搖桿）：")
        print("   👉 下載開源 QGroundControl： https://qgroundcontrol.com/")

    print("\n==========================================================================")

if __name__ == "__main__":
    main()
