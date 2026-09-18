#!/usr/bin/env python3
"""
Digital Twin Drone - Interactive WebGL 3D Flight Test Simulator
Combines Gazebo .world physics obstacles, motor thrust dynamics, 6-DOF flight physics,
and keyboard controls allowing users to test fly the evolved drone inside their browser.
"""

import json
from pathlib import Path
from typing import Dict, Any

class WebGLFlightSimulator:
    """Generates an interactive 3D WebGL Flight Test Simulator with Gazebo world collisions."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_simulator_html(
        self,
        drone_spec: Dict[str, Any],
        world_spec: Dict[str, Any],
        filename: str = "flight_test_simulator.html"
    ) -> Path:
        """Builds a complete WebGL 3D Flight Test Simulator HTML file."""
        html_path = self.output_dir / filename

        num_arms = drone_spec.get("num_arms", 4)
        arm_length = drone_spec.get("arm_length_m", 0.25)
        is_vtol = drone_spec.get("aircraft_type") == "vtol_tilt_rotor"
        wingspan = drone_spec.get("wingspan_m", 1.10)
        wing_chord = drone_spec.get("wing_chord_m", 0.22)
        sensors = drone_spec.get("sensors_mount", [])
        obstacles = world_spec.get("obstacles", [])
        wind_xyz = world_spec.get("wind_velocity_xyz", [0.0, 0.0, 0.0])

        html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>🚁 數位孿生無人機 3D WebGL 試飛模擬器</title>
    <style>
        body {{ margin: 0; padding: 0; overflow: hidden; background: #0b0d14; font-family: 'Segoe UI', Tahoma, sans-serif; color: #fff; }}
        #hud-panel {{
            position: absolute; top: 20px; left: 20px;
            background: rgba(10, 15, 30, 0.85); backdrop-filter: blur(10px);
            padding: 20px 25px; border-radius: 16px; border: 1px solid #1a2a4a;
            min-width: 280px; box-shadow: 0 8px 32px rgba(0,0,0,0.6);
        }}
        .hud-title {{ font-size: 16px; font-weight: bold; color: #00e5ff; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; }}
        .hud-row {{ display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13px; font-family: monospace; }}
        .hud-value {{ font-weight: bold; color: #76ff03; }}
        .collision-warn {{ color: #ff1744; font-weight: bold; animation: blink 0.5s infinite alternate; display: none; }}
        @keyframes blink {{ from {{ opacity: 0.3; }} to {{ opacity: 1; }} }}
        #control-panel {{
            position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
            background: rgba(10, 15, 30, 0.85); backdrop-filter: blur(8px);
            padding: 12px 24px; border-radius: 30px; border: 1px solid #1a2a4a;
            font-size: 13px; color: #b0bec5; display: flex; gap: 20px;
        }}
        .key {{ background: #1e293b; border: 1px solid #334155; color: #38bdf8; padding: 2px 7px; border-radius: 4px; font-weight: bold; font-family: monospace; }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
    <div id="hud-panel">
        <div class="hud-title">🚁 數位孿生 3D 試飛 HUD</div>
        <div class="hud-row"><span>飛行狀態:</span><span id="st-mode" class="hud-value">OFFBOARD - ARM</span></div>
        <div class="hud-row"><span>高度 (Z):</span><span id="st-alt" class="hud-value">0.00 m</span></div>
        <div class="hud-row"><span>水平速度:</span><span id="st-spd" class="hud-value">0.00 m/s</span></div>
        <div class="hud-row"><span>鋰電池電壓:</span><span id="st-bat" class="hud-value">11.80 V</span></div>
        <div class="hud-row"><span>風場矢量:</span><span id="st-wind" style="color:#e040fb">{wind_xyz[0]}m/s (X)</span></div>
        <div id="collision-alert" class="collision-warn">⚠️ 警告：觸發 Gazebo 障礙物剛體碰撞！</div>
    </div>

    <div id="control-panel">
        <div><span class="key">W</span> <span class="key">S</span> 俯仰 (前後)</div>
        <div><span class="key">A</span> <span class="key">D</span> 翻滾 (左右)</div>
        <div><span class="key">↑</span> <span class="key">↓</span> 油門 (升降)</div>
        <div><span class="key">←</span> <span class="key">→</span> 偏航 (旋轉)</div>
        <div><span class="key">Space</span> 自動懸停</div>
    </div>

    <script>
        // 1. Scene, Camera, Renderer Setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0a0c14);
        scene.fog = new THREE.FogExp2(0x0a0c14, 0.025);

        const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 100);
        camera.position.set(0, 3, 6);

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        document.body.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;

        // Lights
        scene.add(new THREE.AmbientLight(0xffffff, 0.6));
        const sun = new THREE.DirectionalLight(0xffffff, 0.8);
        sun.position.set(10, 20, 10);
        sun.castShadow = true;
        scene.add(sun);

        // Ground Grid
        const grid = new THREE.GridHelper(40, 40, 0x00e5ff, 0x1e293b);
        scene.add(grid);

        // 2. Build Drone 3D Mesh Group
        const drone = new THREE.Group();

        // Main Body
        const bodyGeo = new THREE.BoxGeometry(0.3, 0.1, 0.2);
        const bodyMat = new THREE.MeshStandardMaterial({{ color: 0x1e293b, metalness: 0.8, roughness: 0.2 }});
        const bodyMesh = new THREE.Mesh(bodyGeo, bodyMat);
        drone.add(bodyMesh);

        // Battery
        const batGeo = new THREE.BoxGeometry(0.18, 0.08, 0.12);
        const batMat = new THREE.MeshStandardMaterial({{ color: 0xfbbf24 }});
        const batMesh = new THREE.Mesh(batGeo, batMat);
        batMesh.position.set(0, 0.09, 0);
        drone.add(batMesh);

        {"const wingGeo = new THREE.BoxGeometry(" + str(wing_chord) + ", 0.03, " + str(wingspan) + "); const wingMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8 }); const wingMesh = new THREE.Mesh(wingGeo, wingMat); wingMesh.position.set(0, 0.02, 0); drone.add(wingMesh);" if is_vtol else ""}

        // Arms & Motors
        const numArms = {num_arms};
        const armLength = {arm_length};
        const propDisks = [];
        for (let i = 0; i < numArms; i++) {{
            const angle = (i * 2 * Math.PI) / numArms;
            const x = armLength * Math.cos(angle);
            const z = armLength * Math.sin(angle);

            const armGeo = new THREE.CylinderGeometry(0.015, 0.015, armLength);
            const armMat = new THREE.MeshStandardMaterial({{ color: 0x0f172a }});
            const armMesh = new THREE.Mesh(armGeo, armMat);
            armMesh.position.set(x / 2, 0, z / 2);
            armMesh.rotation.z = Math.PI / 2;
            armMesh.rotation.y = -angle;
            drone.add(armMesh);

            const motorGeo = new THREE.CylinderGeometry(0.03, 0.03, 0.04);
            const motorMat = new THREE.MeshStandardMaterial({{ color: 0xef4444 }});
            const motorMesh = new THREE.Mesh(motorGeo, motorMat);
            motorMesh.position.set(x, 0.02, z);
            drone.add(motorMesh);

            const propGeo = new THREE.CylinderGeometry(0.14, 0.14, 0.005, 32);
            const propMat = new THREE.MeshStandardMaterial({{ color: 0x38bdf8, transparent: true, opacity: 0.5 }});
            const propMesh = new THREE.Mesh(propGeo, propMat);
            propMesh.position.set(x, 0.04, z);
            drone.add(propMesh);

            // Store propeller reference & motor direction (CW / CCW)
            propDisks.push({{
                mesh: propMesh,
                dir: (i % 2 === 0) ? 1 : -1
            }});
        }}

        // LiDAR Sensor
        const lidarGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.05);
        const lidarMat = new THREE.MeshStandardMaterial({{ color: 0x22c55e }});
        const lidarMesh = new THREE.Mesh(lidarGeo, lidarMat);
        lidarMesh.position.set(0, 0.16, 0);
        drone.add(lidarMesh);

        drone.position.set(0, 0.05, 0);
        scene.add(drone);

        // 3. Load Gazebo .world Obstacles & Bounding Boxes
        const obstaclesData = {json.dumps(obstacles)};
        const obstacleMeshes = [];

        obstaclesData.forEach((obs) => {{
            const pos = obs.pos || [2, 0, 1];
            const size = obs.size || [0.5, 0.5, 2];
            let obsGeo;
            if (obs.type === 'cylinder') {{
                obsGeo = new THREE.CylinderGeometry(size[0], size[0], size[2], 32);
            }} else {{
                obsGeo = new THREE.BoxGeometry(size[0], size[2], size[1]);
            }}
            const obsMat = new THREE.MeshStandardMaterial({{ color: 0xf43f5e, roughness: 0.3 }});
            const obsMesh = new THREE.Mesh(obsGeo, obsMat);
            obsMesh.position.set(pos[0], pos[2] / 2, pos[1]);
            obsMesh.castShadow = true;
            scene.add(obsMesh);

            // Bounding Box for Physics Collision Detection
            obsMesh.geometry.computeBoundingBox();
            obstacleMeshes.push({{
                mesh: obsMesh,
                box: new THREE.Box3().setFromObject(obsMesh)
            }});
        }});

        // 4. Physics & Flight Dynamics (Harmonized 6-DOF Physics)
        const keys = {{}};
        window.addEventListener('keydown', (e) => keys[e.code] = true);
        window.addEventListener('keyup', (e) => keys[e.code] = false);

        let velocity = new THREE.Vector3(0, 0, 0);
        let rotationSpeed = 0;
        let pitch = 0, roll = 0, yaw = 0;
        let batteryVoltage = 11.80;

        const windX = {wind_xyz[0]};

        function updatePhysics() {{
            // Keyboard Controls
            let throttleAcc = 0;
            let targetPitch = 0, targetRoll = 0;

            if (keys['ArrowUp']) throttleAcc += 12.0;       // Lift / Up
            if (keys['ArrowDown']) throttleAcc -= 8.0;       // Descend
            if (keys['KeyW']) targetPitch = -0.30;           // Pitch Forward (Nose tilts down)
            if (keys['KeyS']) targetPitch = 0.30;            // Pitch Backward (Nose tilts up)
            if (keys['KeyA']) targetRoll = 0.30;             // Roll Left (Left wing tilts down) -> moves LEFT (-X)
            if (keys['KeyD']) targetRoll = -0.30;            // Roll Right (Right wing tilts down) -> moves RIGHT (+X)
            if (keys['ArrowLeft']) rotationSpeed = 0.04;     // Yaw Left
            else if (keys['ArrowRight']) rotationSpeed = -0.04; // Yaw Right
            else rotationSpeed = 0;

            if (keys['Space']) {{ // Hover mode
                targetPitch = 0; targetRoll = 0;
                velocity.x *= 0.92; velocity.z *= 0.92;
                if (drone.position.y > 0.05) velocity.y *= 0.9;
            }}

            // Smooth Attitude Interpolation
            pitch += (targetPitch - pitch) * 0.1;
            roll += (targetRoll - roll) * 0.1;
            yaw += rotationSpeed;

            drone.rotation.x = pitch;
            drone.rotation.z = roll;
            drone.rotation.y = yaw;

            // Thrust Vectoring & Gravity (9.81 m/s^2)
            const gravity = 9.81;
            const liftForce = (drone.position.y > 0.05 ? 9.81 : 0) + throttleAcc;

            velocity.y += (liftForce - gravity) * 0.016;

            // Corrected Thrust Vector Calculation:
            // Pitch Forward (-pitch > 0) -> pushes -Z (Forward)
            // Roll Left (roll > 0) -> pushes -X (Left across screen)
            const forwardZ = Math.sin(pitch) * Math.cos(yaw) - Math.sin(roll) * Math.sin(yaw);
            const forwardX = Math.sin(pitch) * Math.sin(yaw) + Math.sin(-roll) * Math.cos(yaw);

            velocity.x += (forwardX * 15.0 + windX * 0.2) * 0.016;
            velocity.z += (forwardZ * 15.0) * 0.016;

            // Air Drag Damping
            velocity.x *= 0.98;
            velocity.z *= 0.98;
            velocity.y *= 0.95;

            // Update Drone Position & Smooth Camera Tracking preserving 360 Orbit Controls
            const prevDronePos = drone.position.clone();
            drone.position.addScaledVector(velocity, 0.016);
            if (drone.position.y < 0.05) {{
                drone.position.y = 0.05;
                velocity.y = 0;
            }}
            const moveDelta = drone.position.clone().sub(prevDronePos);
            camera.position.add(moveDelta);
            controls.target.copy(drone.position);

            // Spin Propellers in CW / CCW Motor Directions
            propDisks.forEach(p => p.mesh.rotation.y += 0.4 * p.dir);

            // Collision Detection with Gazebo Obstacles
            const droneBox = new THREE.Box3().setFromObject(drone);
            let colliding = false;
            obstacleMeshes.forEach(obs => {{
                if (droneBox.intersectsBox(obs.box)) {{
                    colliding = true;
                    velocity.negate().multiplyScalar(0.5); // Bouncing physics
                }}
            }});

            document.getElementById('collision-alert').style.display = colliding ? 'block' : 'none';

            // Update HUD
            const speed = Math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2).toFixed(2);
            document.getElementById('st-alt').innerText = drone.position.y.toFixed(2) + ' m';
            document.getElementById('st-spd').innerText = speed + ' m/s';
            if (drone.position.y > 0.1) {{
                batteryVoltage = Math.max(10.2, batteryVoltage - 0.0003);
                document.getElementById('st-bat').innerText = batteryVoltage.toFixed(2) + ' V';
            }}
        }}

        function animate() {{
            requestAnimationFrame(animate);
            updatePhysics();
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
    sim = WebGLFlightSimulator(output)

    sample_drone = {
        "aircraft_type": "vtol_tilt_rotor",
        "wingspan_m": 1.25,
        "wing_chord_m": 0.22,
        "num_arms": 6,
        "arm_length_m": 0.26,
        "motor_id": "m_2212_920kv",
        "battery_id": "b_3s_2200mah",
        "sensors_mount": [{"sensor_id": "s_lidar_2d"}, {"sensor_id": "s_depth_cam"}]
    }

    sample_world = {
        "wind_velocity_xyz": [2.5, 0.5, 0.0],
        "obstacles": [
            {"type": "cylinder", "pos": [2.5, 0.5, 1.5], "size": [0.4, 0.4, 3.0]},
            {"type": "box", "pos": [4.0, -1.5, 1.0], "size": [1.0, 1.0, 2.0]}
        ]
    }

    html_file = sim.generate_simulator_html(sample_drone, sample_world, "flight_test_simulator.html")
    print("Generated Fixed WebGL 3D Flight Test Simulator File:", html_file)
