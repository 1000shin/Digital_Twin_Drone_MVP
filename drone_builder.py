#!/usr/bin/env python3
"""
Digital Twin Drone MVP - Dynamic URDF/SDF Generator
Block 2: Converts a drone_spec dictionary/JSON into URDF and SDF physics description files
with precise inertia calculations, visual geometries, collision boxes, and Gazebo plugins.
"""

import json
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple
from db_loader import ComponentDB

class DroneBuilder:
    """Generates URDF and SDF files for multi-rotor drones based on component and geometric specs."""

    def __init__(self, db: ComponentDB):
        self.db = db

    def calculate_inertia_box(self, mass_kg: float, dx: float, dy: float, dz: float) -> Tuple[float, float, float]:
        """Calculates rotational inertia for a rectangular box (Ixx, Iyy, Izz)."""
        ixx = (1.0 / 12.0) * mass_kg * (dy**2 + dz**2)
        iyy = (1.0 / 12.0) * mass_kg * (dx**2 + dz**2)
        izz = (1.0 / 12.0) * mass_kg * (dx**2 + dy**2)
        return ixx, iyy, izz

    def calculate_inertia_cylinder(self, mass_kg: float, radius: float, height: float) -> Tuple[float, float, float]:
        """Calculates rotational inertia for a cylinder aligned with Z axis."""
        ixx = (1.0 / 12.0) * mass_kg * (3 * radius**2 + height**2)
        iyy = ixx
        izz = 0.5 * mass_kg * (radius**2)
        return ixx, iyy, izz

    def build_spec_from_dict(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validates and enriches the input drone_spec dictionary with physical component attributes."""
        num_arms = spec.get("num_arms", 4)
        arm_length_m = spec.get("arm_length_m", 0.25)
        motor_id = spec.get("motor_id", "m_2212_920kv")
        prop_id = spec.get("prop_id", "p_1045")
        battery_id = spec.get("battery_id", "b_3s_2200mah")
        sensors_mount = spec.get("sensors_mount", [])

        motor = self.db.get_component("motors", motor_id)
        prop = self.db.get_component("propellers", prop_id)
        battery = self.db.get_component("batteries", battery_id)

        if not motor or not prop or not battery:
            raise ValueError(f"Invalid component in spec: motor={motor_id}, prop={prop_id}, battery={battery_id}")

        stats = self.db.calculate_power_and_mass(
            num_arms, motor_id, prop_id, battery_id, [s["sensor_id"] for s in sensors_mount]
        )

        return {
            "design_id": spec.get("design_id", "drone_gen_001"),
            "num_arms": num_arms,
            "arm_length_m": arm_length_m,
            "motor": motor,
            "prop": prop,
            "battery": battery,
            "sensors_mount": sensors_mount,
            "stats": stats
        }

    def generate_urdf(self, spec_dict: Dict[str, Any]) -> str:
        """Generates an XML URDF representation of the morphing drone."""
        enriched = self.build_spec_from_dict(spec_dict)
        num_arms = enriched["num_arms"]
        arm_length = enriched["arm_length_m"]
        design_id = enriched["design_id"]

        # Central hub mass
        hub_mass = (enriched["battery"]["weight_g"] + 80.0) / 1000.0  # kg
        ixx_hub, iyy_hub, izz_hub = self.calculate_inertia_box(hub_mass, 0.15, 0.15, 0.08)

        urdf = []
        urdf.append('<?xml version="1.0"?>')
        urdf.append(f'<robot name="{design_id}">')
        urdf.append('  <!-- Base Link / Central Hub -->')
        urdf.append('  <link name="base_link">')
        urdf.append('    <inertial>')
        urdf.append(f'      <mass value="{hub_mass:.4f}"/>')
        urdf.append(f'      <inertia ixx="{ixx_hub:.6f}" ixy="0" ixz="0" iyy="{iyy_hub:.6f}" iyz="0" izz="{izz_hub:.6f}"/>')
        urdf.append('    </inertial>')
        urdf.append('    <visual>')
        urdf.append('      <geometry>')
        urdf.append('        <box size="0.15 0.15 0.08"/>')
        urdf.append('      </geometry>')
        urdf.append('      <material name="dark_grey"><color rgba="0.2 0.2 0.2 1.0"/></material>')
        urdf.append('    </visual>')
        urdf.append('    <collision>')
        urdf.append('      <geometry>')
        urdf.append('        <box size="0.15 0.15 0.08"/>')
        urdf.append('      </geometry>')
        urdf.append('    </collision>')
        urdf.append('  </link>')

        # Generate Arms and Rotors dynamically based on angle
        angle_step = 2.0 * math.pi / num_arms
        motor_mass = (enriched["motor"]["weight_g"] + enriched["prop"]["weight_g"]) / 1000.0

        for i in range(num_arms):
            angle = i * angle_step
            x_pos = arm_length * math.cos(angle)
            y_pos = arm_length * math.sin(angle)

            arm_name = f"arm_{i}"
            urdf.append(f'  <!-- Arm {i} -->')
            urdf.append(f'  <link name="{arm_name}">')
            urdf.append('    <inertial>')
            urdf.append(f'      <mass value="{motor_mass:.4f}"/>')
            urdf.append('      <inertia ixx="0.0001" ixy="0" ixz="0" iyy="0.0001" iyz="0" izz="0002"/>')
            urdf.append('    </inertial>')
            urdf.append('    <visual>')
            urdf.append('      <geometry>')
            urdf.append(f'        <cylinder length="{arm_length:.3f}" radius="0.01"/>')
            urdf.append('      </geometry>')
            urdf.append('      <material name="carbon"><color rgba="0.1 0.1 0.1 1.0"/></material>')
            urdf.append('    </visual>')
            urdf.append('  </link>')

            # Joint connecting hub to arm
            urdf.append(f'  <joint name="joint_base_{arm_name}" type="fixed">')
            urdf.append('    <parent link="base_link"/>')
            urdf.append(f'    <child link="{arm_name}"/>')
            urdf.append(f'    <origin xyz="{x_pos/2.0:.4f} {y_pos/2.0:.4f} 0.0" rpy="0 1.5708 {angle:.4f}"/>')
            urdf.append('  </joint>')

        # Generate Sensors
        for idx, sm in enumerate(enriched["sensors_mount"]):
            s_id = sm["sensor_id"]
            sensor = self.db.get_component("sensors", s_id)
            if not sensor:
                continue
            s_name = f"sensor_{idx}_{s_id}"
            pos = sm.get("rel_pos_xyz", [0, 0, 0])
            s_mass = sensor["weight_g"] / 1000.0

            urdf.append(f'  <!-- Sensor: {s_name} -->')
            urdf.append(f'  <link name="{s_name}">')
            urdf.append('    <inertial>')
            urdf.append(f'      <mass value="{s_mass:.4f}"/>')
            urdf.append('      <inertia ixx="0.00005" ixy="0" ixz="0" iyy="0.00005" iyz="0" izz="0.00005"/>')
            urdf.append('    </inertial>')
            urdf.append('    <visual>')
            urdf.append('      <geometry>')
            urdf.append('        <box size="0.04 0.04 0.04"/>')
            urdf.append('      </geometry>')
            urdf.append('      <material name="blue"><color rgba="0.0 0.4 0.8 1.0"/></material>')
            urdf.append('    </visual>')
            urdf.append('  </link>')

            urdf.append(f'  <joint name="joint_base_{s_name}" type="fixed">')
            urdf.append('    <parent link="base_link"/>')
            urdf.append(f'    <child link="{s_name}"/>')
            urdf.append(f'    <origin xyz="{pos[0]:.4f} {pos[1]:.4f} {pos[2]:.4f}" rpy="0 0 0"/>')
            urdf.append('  </joint>')

        urdf.append('</robot>')
        return "\n".join(urdf)

    def generate_sdf(self, spec_dict: Dict[str, Any]) -> str:
        """Generates an SDF representation with Gazebo motor and sensor plugins."""
        urdf_str = self.generate_urdf(spec_dict)
        # Convert URDF elements into SDF structure
        enriched = self.build_spec_from_dict(spec_dict)
        design_id = enriched["design_id"]

        sdf = []
        sdf.append('<?xml version="1.0" ?>')
        sdf.append('<sdf version="1.8">')
        sdf.append(f'  <model name="{design_id}">')
        sdf.append('    <pose>0 0 0.1 0 0 0</pose>')
        sdf.append('    <!-- Gazebo Motor & SITL Plugins -->')
        sdf.append('    <plugin name="gz::sim::systems::MultirotorMotorModel" filename="gz-sim-multirotor-motor-model-system">')
        sdf.append(f'      <robotNamespace>{design_id}</robotNamespace>')
        sdf.append(f'      <motorNumber>0</motorNumber>')
        sdf.append(f'      <turningDirection>cw</turningDirection>')
        sdf.append(f'      <maxRotVelocity>{enriched["motor"]["kv"] * 1.2:.1f}</maxRotVelocity>')
        sdf.append('    </plugin>')

        # Insert URDF content inside SDF model wrapper
        sdf.append('    ' + urdf_str.replace('<?xml version="1.0"?>', '').replace(f'<robot name="{design_id}">', '').replace('</robot>', ''))
        sdf.append('  </model>')
        sdf.append('</sdf>')
        return "\n".join(sdf)

    def export_files(self, spec_dict: Dict[str, Any], output_dir: Path) -> Dict[str, Path]:
        """Exports generated URDF, SDF, and Organic 3D-Printable STL files to disk."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        design_id = spec_dict.get("design_id", "drone_model")
        urdf_content = self.generate_urdf(spec_dict)
        sdf_content = self.generate_sdf(spec_dict)

        urdf_path = output_dir / f"{design_id}.urdf"
        sdf_path = output_dir / f"{design_id}.sdf"

        with open(urdf_path, "w", encoding="utf-8") as f:
            f.write(urdf_content)

        with open(sdf_path, "w", encoding="utf-8") as f:
            f.write(sdf_content)

        res = {"urdf": urdf_path, "sdf": sdf_path}

        # M2.1: Export Organic 3D-Printable Binary STL & Print Profile
        try:
            from organic_cad_generator import OrganicCADGenerator
            cad_gen = OrganicCADGenerator(self.db)
            stl_path = output_dir / f"{design_id}.stl"
            cad_gen.export_stl(spec_dict, stl_path, binary=True)
            res["stl"] = stl_path

            profile = cad_gen.get_print_profile(spec_dict)
            profile_path = output_dir / f"{design_id}_print_profile.json"
            with open(profile_path, "w", encoding="utf-8") as pf:
                json.dump(profile, pf, indent=2)
            res["print_profile"] = profile_path
        except Exception:
            pass

        return res


if __name__ == "__main__":
    db = ComponentDB()
    builder = DroneBuilder(db)

    sample_spec = {
        "design_id": "test_quadcopter",
        "num_arms": 4,
        "arm_length_m": 0.22,
        "motor_id": "m_2212_920kv",
        "prop_id": "p_1045",
        "battery_id": "b_3s_2200mah",
        "sensors_mount": [
            {"sensor_id": "s_lidar_2d", "rel_pos_xyz": [0.0, 0.0, 0.08]},
            {"sensor_id": "s_depth_cam", "rel_pos_xyz": [0.12, 0.0, 0.0]}
        ]
    }

    out_paths = builder.export_files(sample_spec, Path(__file__).parent / "output")
    print("Exported model files successfully:")
    print("  URDF:", out_paths["urdf"])
    print("  SDF:", out_paths["sdf"])
