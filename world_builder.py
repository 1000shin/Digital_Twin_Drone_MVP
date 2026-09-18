#!/usr/bin/env python3
"""
Digital Twin Drone - Gazebo World & Environment Generator
Phase 2: Generates customized 3D Gazebo SDF world files containing wind fields,
obstacles, lighting, and environmental boundaries for digital twin testing.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple

class WorldBuilder:
    """Generates Gazebo Sim SDF World files with physics parameters and obstacles."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_world_sdf(
        self,
        world_name: str = "digital_twin_world",
        wind_velocity_xyz: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        obstacles: List[Dict[str, Any]] = None
    ) -> str:
        """Builds an SDF 1.8 XML world specification with gravity, wind, and obstacles."""
        if obstacles is None:
            obstacles = []

        sdf = []
        sdf.append('<?xml version="1.0" ?>')
        sdf.append('<sdf version="1.8">')
        sdf.append(f'  <world name="{world_name}">')
        sdf.append('    <!-- Physics Engine Configuration -->')
        sdf.append('    <physics name="default_physics" default="true" type="dart">')
        sdf.append('      <max_step_size>0.001</max_step_size>')
        sdf.append('      <real_time_factor>1.0</real_time_factor>')
        sdf.append('      <real_time_update_rate>1000</real_time_update_rate>')
        sdf.append('    </physics>')

        # Wind system plugin
        sdf.append('    <!-- Environmental Wind Plugin -->')
        sdf.append('    <plugin name="gz::sim::systems::Wind" filename="gz-sim-wind-system">')
        sdf.append('      <horizontal>')
        sdf.append(f'        <magnitude>{(wind_velocity_xyz[0]**2 + wind_velocity_xyz[1]**2)**0.5:.2f}</magnitude>')
        sdf.append(f'        <direction>{wind_velocity_xyz[0]:.2f} {wind_velocity_xyz[1]:.2f} 0</direction>')
        sdf.append('      </horizontal>')
        sdf.append('    </plugin>')

        # Ground Plane & Sun Light
        sdf.append('    <!-- Sun Light -->')
        sdf.append('    <light type="directional" name="sun">')
        sdf.append('      <cast_shadows>true</cast_shadows>')
        sdf.append('      <pose>0 0 10 0 0 0</pose>')
        sdf.append('      <diffuse>0.8 0.8 0.8 1</diffuse>')
        sdf.append('      <direction>-0.5 0.1 -0.9</direction>')
        sdf.append('    </light>')

        sdf.append('    <!-- Ground Plane -->')
        sdf.append('    <model name="ground_plane">')
        sdf.append('      <static>true</static>')
        sdf.append('      <link name="link">')
        sdf.append('        <collision name="collision">')
        sdf.append('          <geometry><plane><normal>0 0 1</normal><size>100 100</size></plane></geometry>')
        sdf.append('        </collision>')
        sdf.append('        <visual name="visual">')
        sdf.append('          <geometry><plane><normal>0 0 1</normal><size>100 100</size></plane></geometry>')
        sdf.append('          <material><ambient>0.8 0.8 0.8 1</ambient></material>')
        sdf.append('        </visual>')
        sdf.append('      </link>')
        sdf.append('    </model>')

        # Add obstacle models (boxes/cylinders)
        for idx, obs in enumerate(obstacles):
            obs_type = obs.get("type", "box")
            pos = obs.get("pos", [2.0, 0.0, 1.0])
            size = obs.get("size", [0.5, 0.5, 2.0])
            obs_name = f"obstacle_{idx}_{obs_type}"

            sdf.append(f'    <!-- Obstacle: {obs_name} -->')
            sdf.append(f'    <model name="{obs_name}">')
            sdf.append('      <static>true</static>')
            sdf.append(f'      <pose>{pos[0]:.2f} {pos[1]:.2f} {pos[2]:.2f} 0 0 0</pose>')
            sdf.append('      <link name="link">')
            sdf.append('        <collision name="collision">')
            sdf.append('          <geometry>')
            if obs_type == "box":
                sdf.append(f'            <box><size>{size[0]} {size[1]} {size[2]}</size></box>')
            else:
                sdf.append(f'            <cylinder><radius>{size[0]}</radius><length>{size[2]}</length></cylinder>')
            sdf.append('          </geometry>')
            sdf.append('        </collision>')
            sdf.append('        <visual name="visual">')
            sdf.append('          <geometry>')
            if obs_type == "box":
                sdf.append(f'            <box><size>{size[0]} {size[1]} {size[2]}</size></box>')
            else:
                sdf.append(f'            <cylinder><radius>{size[0]}</radius><length>{size[2]}</length></cylinder>')
            sdf.append('          </geometry>')
            sdf.append('          <material><ambient>0.8 0.2 0.2 1</ambient></material>')
            sdf.append('        </visual>')
            sdf.append('      </link>')
            sdf.append('    </model>')

        sdf.append('  </world>')
        sdf.append('</sdf>')
        return "\n".join(sdf)

    def export_world(
        self,
        world_name: str = "digital_twin_world",
        wind_velocity_xyz: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        obstacles: List[Dict[str, Any]] = None
    ) -> Path:
        """Exports the Gazebo world file to disk."""
        content = self.generate_world_sdf(world_name, wind_velocity_xyz, obstacles)
        file_path = self.output_dir / f"{world_name}.world"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path

if __name__ == "__main__":
    builder = WorldBuilder(Path(__file__).parent / "output")
    world_file = builder.export_world(
        world_name="inspection_tunnel",
        wind_velocity_xyz=(3.5, 1.0, 0.0),
        obstacles=[
            {"type": "cylinder", "pos": [3.0, 1.0, 1.5], "size": [0.4, 0.4, 3.0]},
            {"type": "box", "pos": [5.0, -2.0, 1.0], "size": [1.0, 1.0, 2.0]}
        ]
    )
    print("Exported Gazebo World File:", world_file)
