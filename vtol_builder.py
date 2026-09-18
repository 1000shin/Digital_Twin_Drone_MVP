#!/usr/bin/env python3
"""
Digital Twin Drone - VTOL & Tilt-Rotor Morphing Aircraft Builder
Phase 3 Choice 2: Generates 3D CAD meshes, URDF, and SDF physics files for Hybrid VTOL & Tilt-Rotor aircraft
featuring dynamic wing airfoils, tilt-servo joints, elevons, and Gazebo Lift-Drag aerodynamic plugins.
"""

import json
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple
from db_loader import ComponentDB
from drone_builder import DroneBuilder

class VTOLBuilder(DroneBuilder):
    """Generates URDF & SDF physics descriptions for Morphing VTOL / Tilt-Rotor aircraft."""

    def generate_vtol_urdf(self, vtol_spec: Dict[str, Any]) -> str:
        """Generates an XML URDF for VTOL aircraft with wing airfoils and tilt servo joints."""
        design_id = vtol_spec.get("design_id", "vtol_morphing_001")
        wingspan_m = vtol_spec.get("wingspan_m", 0.90)
        wing_chord_m = vtol_spec.get("wing_chord_m", 0.20)
        num_tilt_servos = vtol_spec.get("num_tilt_servos", 2)
        num_hover_motors = vtol_spec.get("num_hover_motors", 4)
        motor_id = vtol_spec.get("motor_id", "m_2212_920kv")
        battery_id = vtol_spec.get("battery_id", "b_3s_2200mah")

        battery = self.db.get_component("batteries", battery_id)
        fuselage_mass = (battery["weight_g"] + 150.0) / 1000.0  # kg
        wing_mass = (wingspan_m * wing_chord_m * 180.0) / 1000.0

        ixx, iyy, izz = self.calculate_inertia_box(fuselage_mass, 0.45, 0.12, 0.10)

        urdf = []
        urdf.append('<?xml version="1.0"?>')
        urdf.append(f'<robot name="{design_id}">')
        urdf.append('  <!-- Main Fuselage Body -->')
        urdf.append('  <link name="base_link">')
        urdf.append('    <inertial>')
        urdf.append(f'      <mass value="{fuselage_mass:.4f}"/>')
        urdf.append(f'      <inertia ixx="{ixx:.6f}" ixy="0" ixz="0" iyy="{iyy:.6f}" iyz="0" izz="{izz:.6f}"/>')
        urdf.append('    </inertial>')
        urdf.append('    <visual>')
        urdf.append('      <geometry>')
        urdf.append('        <box size="0.45 0.12 0.10"/>')
        urdf.append('      </geometry>')
        urdf.append('      <material name="white"><color rgba="0.9 0.9 0.9 1.0"/></material>')
        urdf.append('    </visual>')
        urdf.append('    <collision>')
        urdf.append('      <geometry><box size="0.45 0.12 0.10"/></geometry>')
        urdf.append('    </collision>')
        urdf.append('  </link>')

        # Main Wings (Aerodynamic Airfoil Panel)
        urdf.append('  <!-- Main Aerodynamic Wings -->')
        urdf.append('  <link name="main_wing">')
        urdf.append('    <inertial>')
        urdf.append(f'      <mass value="{wing_mass:.4f}"/>')
        urdf.append('      <inertia ixx="0.005" ixy="0" ixz="0" iyy="0.001" iyz="0" izz="0.006"/>')
        urdf.append('    </inertial>')
        urdf.append('    <visual>')
        urdf.append('      <geometry>')
        urdf.append(f'        <box size="{wing_chord_m:.3f} {wingspan_m:.3f} 0.02"/>')
        urdf.append('      </geometry>')
        urdf.append('      <material name="cyan"><color rgba="0.0 0.7 0.9 1.0"/></material>')
        urdf.append('    </visual>')
        urdf.append('  </link>')

        urdf.append('  <joint name="joint_fuselage_wing" type="fixed">')
        urdf.append('    <parent link="base_link"/>')
        urdf.append('    <child link="main_wing"/>')
        urdf.append('    <origin xyz="0.0 0.0 0.02" rpy="0 0 0"/>')
        urdf.append('  </joint>')

        # Tilt-Servo Motor Mounts (Rotates continuously from 0 deg [cruise] to 90 deg [hover])
        for i in range(num_tilt_servos):
            side = 1.0 if i % 2 == 0 else -1.0
            servo_link = f"tilt_servo_{i}"
            urdf.append(f'  <!-- Tilt Servo Motor Mount {i} -->')
            urdf.append(f'  <link name="{servo_link}">')
            urdf.append('    <inertial>')
            urdf.append('      <mass value="0.06"/>')
            urdf.append('      <inertia ixx="0.0001" ixy="0" ixz="0" iyy="0.0001" iyz="0" izz="0.0001"/>')
            urdf.append('    </inertial>')
            urdf.append('    <visual>')
            urdf.append('      <geometry><cylinder length="0.05" radius="0.015"/></geometry>')
            urdf.append('      <material name="red"><color rgba="0.9 0.1 0.1 1.0"/></material>')
            urdf.append('    </visual>')
            urdf.append('  </link>')

            # Revolute Tilt Joint (0 to 1.57 rad)
            urdf.append(f'  <joint name="joint_tilt_{i}" type="revolute">')
            urdf.append('    <parent link="main_wing"/>')
            urdf.append(f'    <child link="{servo_link}"/>')
            urdf.append(f'    <origin xyz="0.10 {side * (wingspan_m/2.2):.3f} 0.0" rpy="0 0 0"/>')
            urdf.append('    <axis xyz="0 1 0"/>')
            urdf.append('    <limit lower="0.0" upper="1.5708" effort="2.0" velocity="3.0"/>')
            urdf.append('  </joint>')

        urdf.append('</robot>')
        return "\n".join(urdf)

    def generate_vtol_sdf(self, vtol_spec: Dict[str, Any]) -> str:
        """Generates an SDF file with Gazebo Lift-Drag aerodynamic system plugins."""
        urdf_str = self.generate_vtol_urdf(vtol_spec)
        design_id = vtol_spec.get("design_id", "vtol_morphing_001")
        wingspan_m = vtol_spec.get("wingspan_m", 0.90)
        wing_chord_m = vtol_spec.get("wing_chord_m", 0.20)
        wing_area = wingspan_m * wing_chord_m

        sdf = []
        sdf.append('<?xml version="1.0" ?>')
        sdf.append('<sdf version="1.8">')
        sdf.append(f'  <model name="{design_id}">')
        sdf.append('    <pose>0 0 0.15 0 0 0</pose>')
        sdf.append('    <!-- Gazebo Lift & Drag Aerodynamic System Plugin -->')
        sdf.append('    <plugin name="gz::sim::systems::LiftDrag" filename="gz-sim-lift-drag-system">')
        sdf.append('      <a0>0.05</a0>')
        sdf.append('      <cla>4.75</cla>')
        sdf.append('      <cda>0.03</cda>')
        sdf.append('      <cma>-1.8</cma>')
        sdf.append('      <alpha_stall>0.33</alpha_stall>')
        sdf.append('      <cla_stall>-3.85</cla_stall>')
        sdf.append('      <cda_stall>2.5</cda_stall>')
        sdf.append('      <cma_stall>0.0</cma_stall>')
        sdf.append(f'      <area>{wing_area:.3f}</area>')
        sdf.append('      <air_density>1.2041</air_density>')
        sdf.append('      <forward>1 0 0</forward>')
        sdf.append('      <upward>0 0 1</upward>')
        sdf.append('      <link_name>main_wing</link_name>')
        sdf.append('    </plugin>')

        sdf.append('    ' + urdf_str.replace('<?xml version="1.0"?>', '').replace(f'<robot name="{design_id}">', '').replace('</robot>', ''))
        sdf.append('  </model>')
        sdf.append('</sdf>')
        return "\n".join(sdf)

    def export_vtol_files(self, vtol_spec: Dict[str, Any], output_dir: Path) -> Dict[str, Path]:
        """Exports generated VTOL URDF and SDF files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        design_id = vtol_spec.get("design_id", "vtol_model")

        urdf_path = output_dir / f"{design_id}.urdf"
        sdf_path = output_dir / f"{design_id}.sdf"

        with open(urdf_path, "w", encoding="utf-8") as f:
            f.write(self.generate_vtol_urdf(vtol_spec))

        with open(sdf_path, "w", encoding="utf-8") as f:
            f.write(self.generate_vtol_sdf(vtol_spec))

        return {"urdf": urdf_path, "sdf": sdf_path}


if __name__ == "__main__":
    db = ComponentDB()
    vtol_builder = VTOLBuilder(db)

    sample_vtol_spec = {
        "design_id": "test_tilt_vtol",
        "wingspan_m": 1.10,
        "wing_chord_m": 0.22,
        "num_tilt_servos": 2,
        "num_hover_motors": 4,
        "motor_id": "m_2212_920kv",
        "battery_id": "b_3s_2200mah"
    }

    out = vtol_builder.export_vtol_files(sample_vtol_spec, Path(__file__).parent / "output")
    print("Exported VTOL Morphing Files:")
    print("  URDF:", out["urdf"])
    print("  SDF:", out["sdf"])
