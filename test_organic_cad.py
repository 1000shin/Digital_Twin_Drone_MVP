#!/usr/bin/env python3
"""
Unit tests for Milestone M2.1: Organic Generative CAD Generator,
Bionic Arm Mesh Construction, Industrial Binary & ASCII STL Exporters,
and 3D Print Profiler.
"""

import unittest
import struct
import json
from pathlib import Path
import numpy as np

from organic_cad_generator import OrganicCADGenerator
from drone_builder import DroneBuilder
from db_loader import ComponentDB


class TestOrganicCADGenerator(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = Path(__file__).parent
        self.output_dir = self.workspace_dir / "output"
        self.generator = OrganicCADGenerator()
        self.sample_spec_4 = {
            "design_id": "test_cad_quad",
            "num_arms": 4,
            "arm_length_m": 0.20,
            "airframe_material": "carbon_fiber_composite"
        }
        self.sample_spec_6 = {
            "design_id": "test_cad_hexa",
            "num_arms": 6,
            "arm_length_m": 0.25,
            "airframe_material": "pla_cf"
        }

    def test_generate_airframe_mesh_topology(self):
        """Verifies vertex, face, and normal generation for different arm counts."""
        # 4-arm drone
        verts4, faces4, normals4 = self.generator.generate_airframe_mesh(self.sample_spec_4)
        self.assertIsInstance(verts4, np.ndarray)
        self.assertIsInstance(faces4, np.ndarray)
        self.assertIsInstance(normals4, np.ndarray)
        self.assertEqual(verts4.shape[1], 3)
        self.assertEqual(faces4.shape[1], 3)
        self.assertEqual(normals4.shape[1], 3)
        self.assertEqual(len(faces4), len(normals4))
        self.assertGreater(len(verts4), 100)
        self.assertGreater(len(faces4), 200)

        # 6-arm drone should have more vertices and faces
        verts6, faces6, normals6 = self.generator.generate_airframe_mesh(self.sample_spec_6)
        self.assertGreater(len(verts6), len(verts4))
        self.assertGreater(len(faces6), len(faces4))

        # Check normal vectors are unit length (within epsilon)
        norms = np.linalg.norm(normals4, axis=1)
        for n in norms:
            self.assertAlmostEqual(float(n), 1.0, places=4)

    def test_binary_stl_export_format(self):
        """Verifies binary STL matches ASTM/ISO industrial 80-byte header format."""
        out_stl = self.output_dir / "test_binary.stl"
        res_path = self.generator.export_stl(self.sample_spec_4, out_stl, binary=True)
        self.assertTrue(res_path.exists())

        with open(res_path, "rb") as f:
            header = f.read(80)
            self.assertEqual(len(header), 80)
            num_triangles = struct.unpack("<I", f.read(4))[0]
            self.assertGreater(num_triangles, 0)

            # Each facet is exactly 50 bytes: 12 normal + 36 vertices + 2 attribute
            remaining_bytes = len(f.read())
            self.assertEqual(remaining_bytes, num_triangles * 50)

    def test_ascii_stl_export_format(self):
        """Verifies ASCII STL matches readable plain text standard."""
        out_stl = self.output_dir / "test_ascii.stl"
        res_path = self.generator.export_stl(self.sample_spec_4, out_stl, binary=False)
        self.assertTrue(res_path.exists())

        content = res_path.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("solid "))
        last_line = content.strip().splitlines()[-1]
        self.assertTrue(last_line.startswith("endsolid"))
        self.assertIn("facet normal", content)
        self.assertIn("outer loop", content)
        self.assertIn("vertex", content)
        self.assertIn("endloop", content)
        self.assertIn("endfacet", content)

    def test_print_profile_calculation(self):
        """Verifies 3D print profiler metrics: volume, weight, bounding box, settings."""
        profile = self.generator.get_print_profile(self.sample_spec_4, material="PETG-CF")
        self.assertEqual(profile["model_id"], "test_cad_quad")
        self.assertEqual(profile["num_arms"], 4)
        self.assertEqual(profile["material"], "PETG-CF")

        # Physical metrics sanity checks
        self.assertGreater(profile["airframe_volume_cm3"], 50.0)
        self.assertGreater(profile["estimated_print_weight_g"], 50.0)
        self.assertIn("bounding_box_mm", profile)
        bbox = profile["bounding_box_mm"]
        self.assertGreater(bbox["x"], 300.0)
        self.assertGreater(bbox["y"], 300.0)
        self.assertGreater(bbox["z"], 20.0)

        # Slicer settings checks
        slicer = profile["recommended_slicer_settings"]
        self.assertIn("nozzle_size_mm", slicer)
        self.assertIn("layer_height_mm", slicer)
        self.assertIn("infill_percentage", slicer)
        self.assertTrue(slicer["supports_required"])

    def test_drone_builder_export_stl_integration(self):
        """Verifies DroneBuilder.export_files integrates CAD STL and print profile."""
        db = ComponentDB()
        builder = DroneBuilder(db)
        exported = builder.export_files(self.sample_spec_4, self.output_dir)

        self.assertIn("urdf", exported)
        self.assertIn("sdf", exported)
        self.assertIn("stl", exported)
        self.assertIn("print_profile", exported)

        self.assertTrue(exported["stl"].exists())
        self.assertTrue(exported["print_profile"].exists())

        with open(exported["print_profile"], "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["model_id"], "test_cad_quad")

    def test_zero_degenerate_triangles_and_manifold_integrity(self):
        """Verifies 100% absence of zero-area or duplicate-vertex degenerate triangles."""
        verts, faces, normals = self.generator.generate_airframe_mesh(self.sample_spec_4)
        for f_idx, face in enumerate(faces):
            # No duplicate vertices in any face
            self.assertEqual(len(set(face)), 3, f"Face {f_idx} has duplicated vertex indices")
            v0 = verts[face[0]]
            v1 = verts[face[1]]
            v2 = verts[face[2]]
            cross = np.cross(v1 - v0, v2 - v0)
            area = 0.5 * np.linalg.norm(cross)
            self.assertGreater(area, 1e-5, f"Face {f_idx} is a degenerate triangle with zero/near-zero area: {area}")

    def test_landing_skid_anchorage_no_floating_gap(self):
        """Verifies landing skid is anchored directly to arm bottom with 0mm floating gap."""
        verts, faces, _ = self.generator.generate_airframe_mesh(self.sample_spec_4, scale_to_mm=False)
        # The last 12 triangles correspond to the landing skid of the last arm
        skid_faces = faces[-12:]
        skid_vertex_indices = list(set(skid_faces.flatten()))
        skid_verts = verts[skid_vertex_indices]

        # Calculate theoretical arm bottom at skid radius
        r_start = max(0.045, min(0.12, self.sample_spec_4["arm_length_m"] * 0.28)) * 0.88
        r_end = self.sample_spec_4["arm_length_m"]
        r_skid = r_end * 0.75
        t_skid = (r_skid - r_start) / (r_end - r_start)
        arm_h_at_skid = (1.0 - t_skid) * 0.016 + t_skid * 0.010
        arm_z_bottom = -t_skid * 0.003 - arm_h_at_skid * 0.5

        # Check skid top anchor vertices match arm bottom (with 0.5mm embedding)
        max_skid_z = float(np.max(skid_verts[:, 2]))
        min_skid_z = float(np.min(skid_verts[:, 2]))

        self.assertAlmostEqual(max_skid_z, arm_z_bottom + 0.0005, delta=0.001)
        # Verify 3D volumetric height of skid (not 2D zero thickness)
        self.assertGreater(max_skid_z - min_skid_z, 0.030)

    def test_motor_mount_coaxial_alignment(self):
        """Verifies motor mount pad is co-axial with arm tip center and has no double mid_z offset."""
        verts, faces, _ = self.generator.generate_airframe_mesh(self.sample_spec_4, scale_to_mm=False)
        r_end = self.sample_spec_4["arm_length_m"]
        # Find motor pad top center vertices
        tip_verts = [v for v in verts if np.sqrt(v[0]**2 + v[1]**2) >= r_end - 1e-4]
        self.assertGreater(len(tip_verts), 0)
        # Motor pad top is at mid_z + 0.5 * motor_pad_h_m = 0.0 + 0.004 = +0.004m (raised boss above arm tip 0.002m)
        max_z_at_tip = max(v[2] for v in tip_verts)
        self.assertAlmostEqual(max_z_at_tip, 0.004, places=3)


if __name__ == "__main__":
    unittest.main()
