#!/usr/bin/env python3
"""
Digital Twin Drone - Interactive 3D Mesh & Environment Visualizer
Generates an interactive WebGL (Three.js) HTML 3D viewer allowing users to inspect the 3D appearance
of the evolved drone (motors, propellers, wings, sensors) and the 3D test space (obstacles, wind, walls).
"""

import json
from pathlib import Path
from typing import Dict, Any

class Interactive3DViewer:
    """Generates an interactive 3D WebGL viewer for drone meshes & test space environments."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_3d_scene(
        self,
        drone_spec: Dict[str, Any],
        world_spec: Dict[str, Any],
        filename: str = "interactive_3d_scene.html"
    ) -> Path:
        """Builds a standalone Three.js WebGL HTML 3D visualization file."""
        html_path = self.output_dir / filename

        num_arms = drone_spec.get("num_arms", 4)
        arm_length = drone_spec.get("arm_length_m", 0.25)
        is_vtol = drone_spec.get("aircraft_type") == "vtol_tilt_rotor"
        wingspan = drone_spec.get("wingspan_m", 1.10)
        wing_chord = drone_spec.get("wing_chord_m", 0.22)
        sensors = drone_spec.get("sensors_mount", [])
        obstacles = world_spec.get("obstacles", [])

        html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>🚁 數位孿生無人機與 3D 測試場景 3D 檢視器</title>
    <style>
        body {{ margin: 0; padding: 0; overflow: hidden; background: #111; font-family: sans-serif; color: #fff; }}
        #info-panel {{
            position: absolute; top: 15px; left: 15px;
            background: rgba(0, 0, 0, 0.85); padding: 18px 22px;
            border-radius: 12px; border: 1px solid #334;
            max-width: 360px; line-height: 1.6; font-size: 14px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}
        .badge {{ background: #00aaee; color: #fff; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
        .badge-vtol {{ background: #ff4466; }}
        #controls-hint {{
            position: absolute; bottom: 15px; left: 50%; transform: translateX(-50%);
            background: rgba(0,0,0,0.7); padding: 8px 18px; border-radius: 20px; font-size: 13px; color: #ccc;
        }}
    </style>
    <!-- Three.js and OrbitControls CDN -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
    <div id="info-panel">
        <h2 style="margin-top:0; font-size:18px; color:#40c4ff;">🚁 數位孿生 3D 模型與測試空間</h2>
        <div><span class="badge {'badge-vtol' if is_vtol else ''}">{'VTOL 傾轉旋翼機' if is_vtol else f'{num_arms} 軸多旋翼無人機'}</span></div>
        <hr style="border-color:#334; margin:12px 0;">
        <div><b>機身幾何</b>：{'翼展 ' + str(wingspan) + 'm, 翼弦 ' + str(wing_chord) + 'm' if is_vtol else f'{num_arms} 軸, 臂長 {arm_length}m'}</div>
        <div><b>馬達型號</b>：{drone_spec.get('motor_id', 'm_2212')}</div>
        <div><b>電池規格</b>：{drone_spec.get('battery_id', 'b_3s_2200mah')}</div>
        <div><b>掛載感測器</b>：{len(sensors)} 個 (包含 360° LiDAR / 深度相機)</div>
        <div><b>測試場景障礙物</b>：{len(obstacles)} 個剛體物件</div>
    </div>

    <div id="controls-hint">🖱️ 滑鼠左鍵旋轉 | 右鍵平移 | 滾輪縮放 (3D Orbit Control)</div>

    <script>
        // 1. Setup Three.js Scene, Camera, Renderer
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x12141c);
        scene.fog = new THREE.FogExp2(0x12141c, 0.03);

        const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 100);
        camera.position.set(2.5, 2.0, 2.5);

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        document.body.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;

        // 2. Lights & Ground Grid
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(5, 10, 7);
        dirLight.castShadow = true;
        scene.add(dirLight);

        const gridHelper = new THREE.GridHelper(20, 20, 0x40c4ff, 0x223344);
        scene.add(gridHelper);

        // 3. Build Drone 3D Group
        const droneGroup = new THREE.Group();
        droneGroup.position.set(0, 0.6, 0);

        // Central Hub / Fuselage
        const hubGeo = new THREE.BoxGeometry(0.3, 0.1, 0.2);
        const hubMat = new THREE.MeshStandardMaterial({{ color: 0x22252a, metalness: 0.8, roughness: 0.2 }});
        const hubMesh = new THREE.Mesh(hubGeo, hubMat);
        hubMesh.castShadow = true;
        droneGroup.add(hubMesh);

        // Top Battery Pack
        const batGeo = new THREE.BoxGeometry(0.18, 0.08, 0.12);
        const batMat = new THREE.MeshStandardMaterial({{ color: 0xffaa00 }});
        const batMesh = new THREE.Mesh(batGeo, batMat);
        batMesh.position.set(0, 0.09, 0);
        droneGroup.add(batMesh);

        {"// VTOL Main Wings" if is_vtol else "// Multi-rotor Arms"}
        {"const wingGeo = new THREE.BoxGeometry(" + str(wing_chord) + ", 0.03, " + str(wingspan) + "); const wingMat = new THREE.MeshStandardMaterial({ color: 0x00aaff, roughness: 0.3 }); const wingMesh = new THREE.Mesh(wingGeo, wingMat); wingMesh.position.set(0, 0.02, 0); droneGroup.add(wingMesh);" if is_vtol else ""}

        // Generate Motor Arms & Rotors
        const numArms = {num_arms};
        const armLength = {arm_length};
        for (let i = 0; i < numArms; i++) {{
            const angle = (i * 2 * Math.PI) / numArms;
            const x = armLength * Math.cos(angle);
            const z = armLength * Math.sin(angle);

            // Carbon Fiber Arm Cylinder
            const armGeo = new THREE.CylinderGeometry(0.015, 0.015, armLength);
            const armMat = new THREE.MeshStandardMaterial({{ color: 0x111111, roughness: 0.5 }});
            const armMesh = new THREE.Mesh(armGeo, armMat);
            armMesh.position.set(x / 2, 0, z / 2);
            armMesh.rotation.z = Math.PI / 2;
            armMesh.rotation.y = -angle;
            droneGroup.add(armMesh);

            // Red Motor Mount
            const motorGeo = new THREE.CylinderGeometry(0.03, 0.03, 0.04);
            const motorMat = new THREE.MeshStandardMaterial({{ color: 0xee2233, metalness: 0.9 }});
            const motorMesh = new THREE.Mesh(motorGeo, motorMat);
            motorMesh.position.set(x, 0.02, z);
            droneGroup.add(motorMesh);

            // Semi-transparent Spinning Propeller Disk
            const propGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.005, 32);
            const propMat = new THREE.MeshStandardMaterial({{ color: 0x40c4ff, transparent: true, opacity: 0.4 }});
            const propMesh = new THREE.Mesh(propGeo, propMat);
            propMesh.position.set(x, 0.04, z);
            droneGroup.add(propMesh);
        }}

        // Sensors (2D LiDAR & Depth Camera)
        const lidarGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.05);
        const lidarMat = new THREE.MeshStandardMaterial({{ color: 0x00e676 }});
        const lidarMesh = new THREE.Mesh(lidarGeo, lidarMat);
        lidarMesh.position.set(0, 0.16, 0);
        droneGroup.add(lidarMesh);

        scene.add(droneGroup);

        // 4. Build Test Environment Obstacles
        const obstaclesData = {json.dumps(obstacles)};
        obstaclesData.forEach((obs, idx) => {{
            const pos = obs.pos || [2, 0, 1];
            const size = obs.size || [0.5, 0.5, 2];
            let obsGeo;
            if (obs.type === 'cylinder') {{
                obsGeo = new THREE.CylinderGeometry(size[0], size[0], size[2], 32);
            }} else {{
                obsGeo = new THREE.BoxGeometry(size[0], size[2], size[1]);
            }}
            const obsMat = new THREE.MeshStandardMaterial({{ color: 0xff5252, roughness: 0.4 }});
            const obsMesh = new THREE.Mesh(obsGeo, obsMat);
            obsMesh.position.set(pos[0], pos[2] / 2, pos[1]);
            obsMesh.castShadow = true;
            scene.add(obsMesh);
        }});

        // 5. Animation Loop
        function animate() {{
            requestAnimationFrame(animate);
            droneGroup.rotation.y += 0.005; // Slow rotation for 360 preview
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();

        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});
    </script>
</body>
</html>
"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_path


if __name__ == "__main__":
    output = Path(__file__).parent / "output"
    viewer = Interactive3DViewer(output)

    sample_drone = {
        "aircraft_type": "vtol_tilt_rotor",
        "wingspan_m": 1.35,
        "wing_chord_m": 0.22,
        "num_arms": 6,
        "arm_length_m": 0.28,
        "motor_id": "m_2212_920kv",
        "battery_id": "b_6s_5000mah",
        "sensors_mount": [{"sensor_id": "s_lidar_2d"}, {"sensor_id": "s_depth_cam"}]
    }

    sample_world = {
        "obstacles": [
            {"type": "cylinder", "pos": [2.5, 0.5, 1.5], "size": [0.4, 0.4, 3.0]},
            {"type": "box", "pos": [4.0, -1.5, 1.0], "size": [1.0, 1.0, 2.0]}
        ]
    }

    html_file = viewer.generate_html_3d_scene(sample_drone, sample_world, "view_3d_scene.html")
    print("Generated Interactive 3D HTML Viewer File:", html_file)
