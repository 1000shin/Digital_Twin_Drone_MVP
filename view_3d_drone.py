#!/usr/bin/env python3
"""
Digital Twin Drone - Interactive 3D Mesh & Environment Visualizer
Generates an interactive WebGL (Three.js) HTML 3D viewer allowing users to inspect the 3D appearance
of the evolved drone (motors, propellers, wings, sensors) and the 3D test space (obstacles, wind, walls).
Includes real-time Scene Environments switcher:
1. Offshore Wind Farm (海面水波/天空盒、巨大風力發電機)
2. Urban City Search & Rescue (建築群、街道障礙、搜救標記)
3. Collision Arena (防撞網格、立體柱體與穿越框)
4. Night Thermal/Inspection (暗黑高對比光影、探照燈、熱成像視角與過熱管線)
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

        try:
            from stl_viewer import STLViewerGenerator
            stl_gen = STLViewerGenerator(self.output_dir.parent if self.output_dir.name == "output" else self.output_dir)
            stl_gen.generate_viewer_html()
        except Exception:
            pass

        num_arms = drone_spec.get("num_arms", 4)
        arm_length = drone_spec.get("arm_length_m", 0.25)
        is_vtol = drone_spec.get("aircraft_type") == "vtol_tilt_rotor"
        wingspan = drone_spec.get("wingspan_m", 1.10)
        wing_chord = drone_spec.get("wing_chord_m", 0.22)
        sensors = drone_spec.get("sensors_mount", [])
        obstacles = world_spec.get("obstacles", [])

        try:
            from organic_cad_generator import OrganicCADGenerator
            cad_gen = OrganicCADGenerator()
            cad_profile = cad_gen.get_print_profile(drone_spec)
        except Exception:
            cad_profile = {
                "bounding_box_mm": {"x": round(arm_length * 2000, 1), "y": round(arm_length * 2000, 1), "z": 80.0},
                "estimated_print_weight_g": 140.0,
                "airframe_volume_cm3": 320.0,
                "material": "PETG-CF",
                "total_triangles": 480
            }

        html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>🚁 數位孿生無人機與 3D 測試場景 3D 檢視器</title>
    <style>
        body {{ margin: 0; padding: 0; overflow: hidden; background: #0c2136; font-family: 'Segoe UI', Tahoma, sans-serif; color: #fff; user-select: none; }}
        #info-panel {{
            position: absolute; top: 15px; left: 15px;
            background: rgba(10, 15, 30, 0.88); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
            padding: 18px 22px; border-radius: 14px; border: 1px solid #1a2a4a;
            max-width: 340px; line-height: 1.6; font-size: 13px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.6); z-index: 100;
        }}
        .badge {{ background: #00e5ff; color: #020617; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }}
        .badge-vtol {{ background: #f43f5e; color: #fff; }}
        #controls-hint {{
            position: absolute; bottom: 15px; left: 50%; transform: translateX(-50%);
            background: rgba(10, 15, 30, 0.85); backdrop-filter: blur(8px);
            padding: 9px 20px; border-radius: 20px; font-size: 12.5px; color: #b0bec5; border: 1px solid #1a2a4a; z-index: 100;
        }}

        /* Environment Selector */
        .env-section {{
            margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(64, 196, 255, 0.2);
        }}
        .env-label-row {{
            font-size: 11px; color: #94a3b8; margin-bottom: 7px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; display: flex; align-items: center; justify-content: space-between;
        }}
        .env-tag {{
            font-size: 10px; padding: 2px 7px; border-radius: 4px; font-weight: 700; transition: all 0.3s;
        }}
        .env-dropdown {{
            width: 100%; background: #0f172a; color: #38bdf8; border: 1px solid #334155; padding: 8px 10px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; outline: none; transition: all 0.2s; box-shadow: inset 0 1px 3px rgba(0,0,0,0.5);
        }}
        .env-dropdown:hover {{ border-color: #00e5ff; }}
        .env-dropdown:focus {{ border-color: #00e5ff; box-shadow: 0 0 8px rgba(0, 229, 255, 0.4); }}
        .env-dropdown option {{ background: #0b1120; color: #e2e8f0; }}

        /* Thermal Vision HUD Panel */
        #thermal-hud {{
            display: none; position: absolute; top: 15px; left: 380px;
            background: rgba(5, 7, 18, 0.9); backdrop-filter: blur(10px);
            border: 1px solid #6366f1; border-radius: 12px; padding: 12px 18px;
            font-family: monospace; font-size: 12px; box-shadow: 0 6px 24px rgba(99, 102, 241, 0.3); z-index: 100;
        }}
        .thermal-bar {{
            width: 130px; height: 10px; border-radius: 4px;
            background: linear-gradient(to right, #000000, #312e81, #7c3aed, #dc2626, #ea580c, #facc15, #ffffff);
            border: 1px solid #475569;
        }}

        /* BOM Drawer / Panel */
        #bom-panel {{
            position: absolute; top: 15px; right: 15px;
            width: 340px;
            background: rgba(10, 15, 30, 0.88); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(0, 229, 255, 0.3); border-radius: 14px;
            box-shadow: 0 12px 36px rgba(0, 0, 0, 0.65), 0 0 15px rgba(0, 229, 255, 0.12);
            color: #e2e8f0; font-family: 'Segoe UI', Tahoma, -apple-system, sans-serif;
            z-index: 1000; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            overflow: hidden;
        }}
        .bom-header {{
            display: flex; align-items: center; justify-content: space-between;
            padding: 12px 18px; cursor: pointer; user-select: none;
            background: rgba(15, 23, 42, 0.85); border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            transition: background 0.2s;
        }}
        .bom-header:hover {{ background: rgba(30, 41, 59, 0.9); }}
        .bom-title {{ font-size: 13.5px; font-weight: 700; color: #00e5ff; letter-spacing: 0.5px; display: flex; align-items: center; gap: 8px; }}
        .bom-icon {{ font-size: 15px; }}
        .bom-toggle-btn {{
            background: rgba(0, 229, 255, 0.12); border: 1px solid rgba(0, 229, 255, 0.35);
            color: #38bdf8; font-size: 11px; font-weight: 600; padding: 4px 9px;
            border-radius: 6px; cursor: pointer; transition: all 0.2s;
        }}
        .bom-toggle-btn:hover {{ background: rgba(0, 229, 255, 0.25); color: #ffffff; }}
        .bom-body {{
            padding: 12px 16px; max-height: 460px; overflow-y: auto;
            transition: max-height 0.35s ease, opacity 0.3s ease, padding 0.35s ease;
        }}
        .bom-body::-webkit-scrollbar {{ width: 5px; }}
        .bom-body::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 4px; }}
        #bom-panel.collapsed .bom-body {{
            max-height: 0; opacity: 0; padding-top: 0; padding-bottom: 0; pointer-events: none;
        }}
        #bom-panel.collapsed {{ width: 290px; border-color: rgba(255, 255, 255, 0.12); }}
        .bom-meta-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-size: 11px; }}
        .bom-badge {{ background: rgba(14, 165, 233, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); padding: 2px 8px; border-radius: 10px; font-weight: 600; }}
        .bom-health {{ color: #4ade80; font-weight: 600; font-size: 11px; }}
        .bom-list {{ display: flex; flex-direction: column; gap: 7px; }}
        .bom-item {{
            display: flex; align-items: center; gap: 9px;
            background: rgba(15, 23, 42, 0.65); border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 7px 10px; border-radius: 8px; transition: all 0.2s;
        }}
        .bom-item:hover {{ background: rgba(30, 41, 59, 0.75); border-color: rgba(0, 229, 255, 0.35); }}
        .bom-item-icon {{ font-size: 15px; width: 22px; text-align: center; flex-shrink: 0; }}
        .bom-item-info {{ flex: 1; min-width: 0; }}
        .bom-item-name {{ font-size: 12px; font-weight: 600; color: #f8fafc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .bom-item-spec {{ font-size: 10.5px; color: #94a3b8; font-family: monospace; margin-top: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .bom-item-tag {{ font-size: 10px; padding: 2px 6px; border-radius: 4px; white-space: nowrap; font-weight: 600; font-family: monospace; background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }}
        .bom-footer {{ display: flex; justify-content: space-between; margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 11px; color: #94a3b8; }}
        .bom-stat {{ color: #f59e0b; font-weight: bold; font-family: monospace; }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
    <div id="info-panel">
        <h2 style="margin-top:0; font-size:16px; color:#40c4ff; margin-bottom:8px;">🚁 數位孿生 3D 模型與測試空間</h2>
        <div><span class="badge {'badge-vtol' if is_vtol else ''}">{'VTOL 傾轉旋翼機' if is_vtol else f'{num_arms} 軸多旋翼無人機'}</span></div>
        <div style="margin-top: 6px;"><b>機身幾何</b>：{'翼展 ' + str(wingspan) + 'm, 翼弦 ' + str(wing_chord) + 'm' if is_vtol else f'{num_arms} 軸, 臂長 {arm_length}m'}</div>
        <div><b>馬達型號</b>：{drone_spec.get('motor_id', 'm_2212')}</div>
        <div><b>電池規格</b>：{drone_spec.get('battery_id', 'b_3s_2200mah')}</div>
        <div><b>掛載感測器</b>：{len(sensors)} 個 (包含 360° LiDAR / 深度相機)</div>
        <div><b>基準場景障礙</b>：{len(obstacles)} 個剛體物件</div>

        <!-- Structural Damage Inspection & Health Section -->
        <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(64, 196, 255, 0.25);">
            <div style="display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 5px;">
                <span>機身結構健康度:</span>
                <span id="cad-integrity" style="color: #4ade80; font-weight: bold;">100% (完好)</span>
            </div>
            <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden; margin-bottom: 8px;">
                <div id="cad-integrity-bar" style="width: 100%; height: 100%; background: #22c55e; transition: all 0.3s;"></div>
            </div>
            <div style="display: flex; gap: 6px;">
                <button id="btn-sim-damage" onclick="simulateCADCrashDamage()" style="flex: 1; background: rgba(239, 68, 68, 0.25); border: 1px solid rgba(239, 68, 68, 0.5); color: #fca5a5; padding: 6px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; cursor: pointer; transition: all 0.2s;">💥 模擬撞擊破損</button>
                <button id="btn-repair-cad" onclick="repairCADModel()" style="flex: 1; background: linear-gradient(135deg, #0284c7, #0369a1); border: 1px solid #38bdf8; color: #fff; padding: 6px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; cursor: pointer; transition: all 0.2s;">🛠️ 修復原狀</button>
            </div>
        </div>

        <!-- M2.1 Organic Generative 3D Print CAD Section -->
        <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(64, 196, 255, 0.25);">
            <div style="display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 5px;">
                <span style="color: #38bdf8; font-weight: bold;">🖨️ 3D 列印有機造型 (M2.1 STL)</span>
                <span id="cad-print-tag" class="badge" style="background: #10b981; color: #fff; font-size: 10px;">可列印 (STL Ready)</span>
            </div>
            <div style="font-size: 11px; color: #94a3b8; line-height: 1.5;">
                <div><b>包絡尺寸</b>: {cad_profile['bounding_box_mm']['x']} × {cad_profile['bounding_box_mm']['y']} × {cad_profile['bounding_box_mm']['z']} mm</div>
                <div><b>耗材預估</b>: {cad_profile['estimated_print_weight_g']}g ({cad_profile['material']}) | 體積: {cad_profile['airframe_volume_cm3']} cm³</div>
                <div><b>幾何特性</b>: 仿生漸變機臂 + 力流鏤空肋條 ({cad_profile['total_triangles']} 三角面)</div>
            </div>
            <div style="margin-top: 8px;">
                <a href="stl_viewer.html" target="_blank" style="display: block; text-align: center; background: linear-gradient(135deg, #10b981, #059669); color: #fff; text-decoration: none; padding: 6px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; border: 1px solid #34d399; box-shadow: 0 2px 8px rgba(16,185,129,0.3);">
                    🖨️ 在 WebGL 檢視 3D 列印 STL 實體 ↗
                </a>
            </div>
        </div>

        <!-- Scene Environments Selector -->
        <div class="env-section">
            <div class="env-label-row">
                <span>🌐 測試情境 (Environment)</span>
                <span id="env-tag" class="env-tag" style="background: rgba(0,229,255,0.2); color:#00e5ff;">離岸風場</span>
            </div>
            <select id="env-select" class="env-dropdown" onchange="switchEnvironment(this.value)">
                <option value="offshore_wind">🌊 離岸風場巡檢 (Offshore Wind Farm)</option>
                <option value="urban_city">🏙️ 城市高樓搜救 (Urban City Search & Rescue)</option>
                <option value="collision_arena">⚡ 碰撞測試場地 (Collision Arena)</option>
                <option value="night_thermal">🌙 夜間紅外線巡檢 (Night Thermal/Inspection)</option>
            </select>
        </div>
    </div>

    <!-- Thermal Vision HUD Overlay -->
    <div id="thermal-hud">
        <div style="color: #a855f7; font-weight: bold; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
            <span>🔥 FLIR LWIR 熱成像 (8-14μm)</span>
            <span style="color: #f43f5e; font-weight: bold;">● LIVE</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            <div class="thermal-bar"></div>
            <span style="font-size: 10px; color: #94a3b8;">15°C ~ 95°C</span>
        </div>
        <div style="font-size: 11px; color: #cbd5e1;">
            焦點溫度: <span id="thermal-spot" style="color: #facc15; font-weight: bold;">84.2°C (變壓器套管過熱)</span>
        </div>
    </div>

    <!-- BOM Drawer / Panel -->
    <div id="bom-panel">
        <div class="bom-header" onclick="toggleBOM()">
            <div class="bom-title">
                <span class="bom-icon">📦</span>
                <span>零件清單 BOM (Bill of Materials)</span>
            </div>
            <button id="bom-toggle-btn" class="bom-toggle-btn" onclick="event.stopPropagation(); toggleBOM();">收合 ▲</button>
        </div>
        <div class="bom-body">
            <div class="bom-meta-bar">
                <span class="bom-badge">7 大關鍵核心零件</span>
                <span id="bom-meta-health" class="bom-health">● 全部就緒 (Nominal)</span>
            </div>
            <div class="bom-list">
                <div class="bom-item">
                    <div class="bom-item-icon">🦴</div>
                    <div class="bom-item-info">
                        <div class="bom-item-name">機體結構 (Carbon Fiber Frame)</div>
                        <div class="bom-item-spec">3K 碳纖維一體成型臂管 / 輕量化抗扭骨架</div>
                    </div>
                    <div id="bom-tag-frame" class="bom-item-tag">正常 (Nominal)</div>
                </div>
                <div class="bom-item">
                    <div class="bom-item-icon">⚡</div>
                    <div class="bom-item-info">
                        <div class="bom-item-name">{num_arms}x 無刷馬達 (Brushless Motors)</div>
                        <div class="bom-item-spec">2212 920KV 航模無刷電機 / 動態平衡</div>
                    </div>
                    <div id="bom-tag-motors" class="bom-item-tag">{num_arms}/{num_arms} 在線</div>
                </div>
                <div class="bom-item">
                    <div class="bom-item-icon">🌀</div>
                    <div class="bom-item-info">
                        <div class="bom-item-name">{num_arms}x 螺旋槳 (Propellers)</div>
                        <div class="bom-item-spec">9450 自鎖快拆高剛性正反槳 (CW/CCW)</div>
                    </div>
                    <div id="bom-tag-props" class="bom-item-tag">校準平衡</div>
                </div>
                <div class="bom-item">
                    <div class="bom-item-icon">🔋</div>
                    <div class="bom-item-info">
                        <div class="bom-item-name">4S 鋰電池 (5200mAh LiPo Battery)</div>
                        <div class="bom-item-spec">14.8V 5200mAh 60C 高倍率動力鋰電池組</div>
                    </div>
                    <div class="bom-item-tag">15.8V (96%)</div>
                </div>
                <div class="bom-item">
                    <div class="bom-item-icon">🧠</div>
                    <div class="bom-item-info">
                        <div class="bom-item-name">Pixhawk 飛行控制器</div>
                        <div class="bom-item-spec">Pixhawk 6C (STM32H753 / 雙冗餘 IMU / PX4)</div>
                    </div>
                    <div class="bom-item-tag">SITL Ready</div>
                </div>
                <div class="bom-item">
                    <div class="bom-item-icon">🛰️</div>
                    <div class="bom-item-info">
                        <div class="bom-item-name">GPS/羅盤模組</div>
                        <div class="bom-item-spec">M10Q 多星定位 (GPS+BDS+Galileo) + IST8310</div>
                    </div>
                    <div class="bom-item-tag">3D Fix (18星)</div>
                </div>
                <div class="bom-item">
                    <div class="bom-item-icon">📷</div>
                    <div class="bom-item-info">
                        <div class="bom-item-name">數位圖傳 (HD VTX/Camera)</div>
                        <div class="bom-item-spec">1080p 60fps 低延遲數位圖傳 / 120° FOV 鏡頭</div>
                    </div>
                    <div class="bom-item-tag">1000mW 穩定</div>
                </div>
            </div>
            <div class="bom-footer">
                <div>全備起飛重量: <span class="bom-stat">1280g</span></div>
                <div>推重比 (TWR): <span id="bom-val-twr" class="bom-stat">2.4 : 1</span></div>
            </div>
        </div>
    </div>

    <div id="controls-hint">🖱️ 滑鼠左鍵旋轉 | 右鍵平移 | 滾輪縮放 (3D Orbit Control)</div>

    <script>
        // 1. Setup Three.js Scene, Camera, Renderer
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0c2136);
        scene.fog = new THREE.FogExp2(0x0c2136, 0.015);

        const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(3.5, 2.5, 3.5);

        const renderer = new THREE.WebGLRenderer({{ antialias: true, logarithmicDepthBuffer: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        document.body.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;

        // Dynamic Lighting System
        const ambientLight = new THREE.AmbientLight(0xbae6fd, 0.65);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xfffbeb, 0.9);
        dirLight.position.set(25, 40, 20);
        dirLight.castShadow = true;
        dirLight.shadow.mapSize.width = 1024;
        dirLight.shadow.mapSize.height = 1024;
        scene.add(dirLight);

        let currentGrid = null;

        // 2. Build Drone 3D Group
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

        // Generate Motor Arms & Rotors & Damage Component Registry
        const numArms = {num_arms};
        const armLength = {arm_length};
        const droneArmComponents = [];
        for (let i = 0; i < numArms; i++) {{
            const angle = (i * 2 * Math.PI) / numArms;
            const x = armLength * Math.cos(angle);
            const z = armLength * Math.sin(angle);

            const armGeo = new THREE.CylinderGeometry(0.015, 0.015, armLength);
            const armMat = new THREE.MeshStandardMaterial({{ color: 0x111111, roughness: 0.5 }});
            const armMesh = new THREE.Mesh(armGeo, armMat);
            armMesh.position.set(x / 2, 0, z / 2);
            armMesh.rotation.z = Math.PI / 2;
            armMesh.rotation.y = -angle;
            droneGroup.add(armMesh);

            const motorGeo = new THREE.CylinderGeometry(0.03, 0.03, 0.04);
            const motorMat = new THREE.MeshStandardMaterial({{ color: 0xee2233, metalness: 0.9 }});
            const motorMesh = new THREE.Mesh(motorGeo, motorMat);
            motorMesh.position.set(x, 0.02, z);
            droneGroup.add(motorMesh);

            const propGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.005, 32);
            const propMat = new THREE.MeshStandardMaterial({{ color: 0x40c4ff, transparent: true, opacity: 0.4 }});
            const propMesh = new THREE.Mesh(propGeo, propMat);
            propMesh.position.set(x, 0.04, z);
            droneGroup.add(propMesh);

            droneArmComponents.push({{
                index: i,
                armMesh: armMesh,
                motorMesh: motorMesh,
                propMesh: propMesh,
                origArmRot: {{ x: armMesh.rotation.x, y: armMesh.rotation.y, z: armMesh.rotation.z }},
                origArmPos: {{ x: armMesh.position.x, y: armMesh.position.y, z: armMesh.position.z }},
                origMotorRot: {{ x: motorMesh.rotation.x, y: motorMesh.rotation.y, z: motorMesh.rotation.z }},
                origMotorPos: {{ x: motorMesh.position.x, y: motorMesh.position.y, z: motorMesh.position.z }}
            }});
        }}

        let isCADModelDamaged = false;
        function simulateCADCrashDamage() {{
            if (isCADModelDamaged) return;
            isCADModelDamaged = true;

            if (droneArmComponents.length > 0) {{
                const arm0 = droneArmComponents[0];
                arm0.armMesh.rotation.x += 0.35;
                arm0.armMesh.rotation.z += 0.25;
                arm0.armMesh.material.color.setHex(0x1a0808);
                arm0.armMesh.material.roughness = 0.95;

                arm0.propMesh.scale.set(0.35, 1.0, 0.38);
                arm0.propMesh.material.color.setHex(0xef4444);
                arm0.propMesh.material.opacity = 0.9;

                arm0.motorMesh.rotation.z += 0.32;
                arm0.motorMesh.material.color.setHex(0x7f1d1d);
            }}

            const intEl = document.getElementById('cad-integrity');
            const intBar = document.getElementById('cad-integrity-bar');
            if (intEl && intBar) {{
                intEl.innerText = '58% (嚴重受損)';
                intEl.style.color = '#f87171';
                intBar.style.width = '58%';
                intBar.style.background = '#ef4444';
            }}

            const bomHealth = document.getElementById('bom-meta-health');
            if (bomHealth) {{
                bomHealth.innerText = '● 結構破損 (Damaged)';
                bomHealth.style.color = '#ef4444';
            }}
            const bomTagFrame = document.getElementById('bom-tag-frame');
            if (bomTagFrame) {{
                bomTagFrame.innerText = '⚠️ 臂管斷裂破損';
                bomTagFrame.style.color = '#ef4444';
                bomTagFrame.style.background = 'rgba(239, 68, 68, 0.2)';
            }}
            const bomTagMotors = document.getElementById('bom-tag-motors');
            if (bomTagMotors) {{
                bomTagMotors.innerText = (numArms - 1) + '/' + numArms + ' 在線';
                bomTagMotors.style.color = '#f87171';
                bomTagMotors.style.background = 'rgba(239, 68, 68, 0.2)';
            }}
            const bomTagProps = document.getElementById('bom-tag-props');
            if (bomTagProps) {{
                bomTagProps.innerText = '❌ 1組槳葉折損';
                bomTagProps.style.color = '#ef4444';
                bomTagProps.style.background = 'rgba(239, 68, 68, 0.2)';
            }}
            const bomTwr = document.getElementById('bom-val-twr');
            if (bomTwr) {{
                bomTwr.innerText = '1.8 : 1';
                bomTwr.style.color = '#ef4444';
            }}
        }}

        function repairCADModel() {{
            isCADModelDamaged = false;
            droneArmComponents.forEach(arm => {{
                arm.armMesh.rotation.set(arm.origArmRot.x, arm.origArmRot.y, arm.origArmRot.z);
                arm.armMesh.position.set(arm.origArmPos.x, arm.origArmPos.y, arm.origArmPos.z);
                arm.armMesh.material.color.setHex(0x111111);
                arm.armMesh.material.roughness = 0.5;

                arm.motorMesh.rotation.set(arm.origMotorRot.x, arm.origMotorRot.y, arm.origMotorRot.z);
                arm.motorMesh.position.set(arm.origMotorPos.x, arm.origMotorPos.y, arm.origMotorPos.z);
                arm.motorMesh.material.color.setHex(0xee2233);

                arm.propMesh.scale.set(1, 1, 1);
                arm.propMesh.material.color.setHex(0x40c4ff);
                arm.propMesh.material.opacity = 0.4;
            }});

            const intEl = document.getElementById('cad-integrity');
            const intBar = document.getElementById('cad-integrity-bar');
            if (intEl && intBar) {{
                intEl.innerText = '100% (完好)';
                intEl.style.color = '#4ade80';
                intBar.style.width = '100%';
                intBar.style.background = '#22c55e';
            }}

            const bomHealth = document.getElementById('bom-meta-health');
            if (bomHealth) {{
                bomHealth.innerText = '● 全部就緒 (Nominal)';
                bomHealth.style.color = '#4ade80';
            }}
            const bomTagFrame = document.getElementById('bom-tag-frame');
            if (bomTagFrame) {{
                bomTagFrame.innerText = '正常 (Nominal)';
                bomTagFrame.style.color = '#4ade80';
                bomTagFrame.style.background = 'rgba(34, 197, 94, 0.15)';
            }}
            const bomTagMotors = document.getElementById('bom-tag-motors');
            if (bomTagMotors) {{
                bomTagMotors.innerText = numArms + '/' + numArms + ' 在線';
                bomTagMotors.style.color = '#4ade80';
                bomTagMotors.style.background = 'rgba(34, 197, 94, 0.15)';
            }}
            const bomTagProps = document.getElementById('bom-tag-props');
            if (bomTagProps) {{
                bomTagProps.innerText = '校準平衡';
                bomTagProps.style.color = '#4ade80';
                bomTagProps.style.background = 'rgba(34, 197, 94, 0.15)';
            }}
            const bomTwr = document.getElementById('bom-val-twr');
            if (bomTwr) {{
                bomTwr.innerText = '2.4 : 1';
                bomTwr.style.color = '#f59e0b';
            }}
        }}

        // Sensors (LiDAR & Depth Camera)
        const lidarGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.05);
        const lidarMat = new THREE.MeshStandardMaterial({{ color: 0x00e676 }});
        const lidarMesh = new THREE.Mesh(lidarGeo, lidarMat);
        lidarMesh.position.set(0, 0.16, 0);
        droneGroup.add(lidarMesh);

        // Drone Searchlight (for Night Thermal / Inspection)
        const droneSpotlight = new THREE.SpotLight(0x67e8f9, 0.0, 25, Math.PI / 4.5, 0.4, 1.2);
        droneSpotlight.position.set(0, -0.05, 0.1);
        const droneSpotlightTarget = new THREE.Object3D();
        droneSpotlightTarget.position.set(0, -6, 10);
        droneGroup.add(droneSpotlight);
        droneGroup.add(droneSpotlightTarget);
        droneSpotlight.target = droneSpotlightTarget;

        scene.add(droneGroup);

        // 3. Multi-Scenario Environments Construction
        const envGroups = {{
            offshore_wind: new THREE.Group(),
            urban_city: new THREE.Group(),
            collision_arena: new THREE.Group(),
            night_thermal: new THREE.Group()
        }};

        const turbineRotors = [];
        let oceanGeo = null;
        let rescueBeacon = null;

        // --- Scenario 1: 離岸風場巡檢 (Offshore Wind Farm) ---
        (function buildOffshoreWind() {{
            const group = envGroups.offshore_wind;

            oceanGeo = new THREE.PlaneGeometry(350, 350, 48, 48);
            const oceanMat = new THREE.MeshStandardMaterial({{
                color: 0x0284c7,
                roughness: 0.15,
                metalness: 0.7,
                transparent: true,
                opacity: 0.92,
                depthWrite: true,
                side: THREE.DoubleSide
            }});
            const oceanMesh = new THREE.Mesh(oceanGeo, oceanMat);
            oceanMesh.rotation.x = -Math.PI / 2;
            oceanMesh.position.y = -0.15;
            group.add(oceanMesh);

            const turbinePositions = [
                [18, -12],
                [-20, 16],
                [4, -30]
            ];

            turbinePositions.forEach((tp) => {{
                const tx = tp[0], tz = tp[1];

                const baseGeo = new THREE.CylinderGeometry(2.4, 2.7, 2.0, 16);
                const baseMat = new THREE.MeshStandardMaterial({{ color: 0xf59e0b, roughness: 0.4 }});
                const baseMesh = new THREE.Mesh(baseGeo, baseMat);
                baseMesh.position.set(tx, 0.85, tz);
                group.add(baseMesh);

                const towerGeo = new THREE.CylinderGeometry(0.45, 0.9, 20, 16);
                const towerMat = new THREE.MeshStandardMaterial({{ color: 0xf8fafc, roughness: 0.3 }});
                const towerMesh = new THREE.Mesh(towerGeo, towerMat);
                towerMesh.position.set(tx, 11.0, tz);
                group.add(towerMesh);

                const nacelleGeo = new THREE.BoxGeometry(1.6, 1.3, 3.2);
                const nacelleMat = new THREE.MeshStandardMaterial({{ color: 0xe2e8f0, roughness: 0.3 }});
                const nacelleMesh = new THREE.Mesh(nacelleGeo, nacelleMat);
                nacelleMesh.position.set(tx, 21.0, tz);
                group.add(nacelleMesh);

                const rotorHub = new THREE.Group();
                rotorHub.position.set(tx, 21.0, tz + 1.7);

                const hubCenterGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.6, 16);
                const hubCenterMat = new THREE.MeshStandardMaterial({{ color: 0x334155 }});
                const hubCenter = new THREE.Mesh(hubCenterGeo, hubCenterMat);
                hubCenter.rotation.x = Math.PI / 2;
                rotorHub.add(hubCenter);

                for (let b = 0; b < 3; b++) {{
                    const bladeAngle = (b * 2 * Math.PI) / 3;
                    const bladeGeo = new THREE.BoxGeometry(0.24, 9.5, 0.08);
                    const bladeMat = new THREE.MeshStandardMaterial({{ color: 0xffffff, roughness: 0.2 }});
                    const bladeMesh = new THREE.Mesh(bladeGeo, bladeMat);
                    bladeMesh.position.set(
                        (9.5 / 2) * Math.sin(bladeAngle),
                        (9.5 / 2) * Math.cos(bladeAngle),
                        0
                    );
                    bladeMesh.rotation.z = -bladeAngle;
                    rotorHub.add(bladeMesh);
                }}

                group.add(rotorHub);
                turbineRotors.push(rotorHub);
            }});

            const buoyGeo = new THREE.CylinderGeometry(0.5, 0.7, 1.4, 12);
            const buoyMat = new THREE.MeshStandardMaterial({{ color: 0xef4444 }});
            const buoy1 = new THREE.Mesh(buoyGeo, buoyMat);
            buoy1.position.set(6, 0.5, 6);
            group.add(buoy1);
        }})();

        // --- Scenario 2: 城市高樓搜救 (Urban City Search & Rescue) ---
        (function buildUrbanCity() {{
            const group = envGroups.urban_city;

            const streetGeo = new THREE.PlaneGeometry(300, 300);
            const streetMat = new THREE.MeshStandardMaterial({{
                color: 0x18181b,
                roughness: 0.95,
                side: THREE.DoubleSide,
                polygonOffset: true,
                polygonOffsetFactor: 1.0,
                polygonOffsetUnits: 1.0
            }});
            const streetMesh = new THREE.Mesh(streetGeo, streetMat);
            streetMesh.rotation.x = -Math.PI / 2;
            streetMesh.position.y = -0.02;
            group.add(streetMesh);

            const buildings = [
                {{ pos: [15, 9, -12], size: [9, 18, 9], color: 0x1e293b }},
                {{ pos: [-16, 12, -10], size: [10, 24, 10], color: 0x0f172a }},
                {{ pos: [0, 11, 24], size: [12, 22, 10], color: 0x1e2230 }},
                {{ pos: [-15, 7, 16], size: [9, 14, 9], color: 0x27272a }},
                {{ pos: [16, 8, 14], size: [8, 16, 11], color: 0x181e28 }},
                {{ pos: [2, 4, -22], size: [14, 8, 8], color: 0x334155 }}
            ];

            buildings.forEach((b, idx) => {{
                const bGeo = new THREE.BoxGeometry(b.size[0], b.size[1], b.size[2]);
                const bMat = new THREE.MeshStandardMaterial({{ color: b.color, roughness: 0.4, metalness: 0.5 }});
                const bMesh = new THREE.Mesh(bGeo, bMat);
                bMesh.position.set(b.pos[0], b.pos[1], b.pos[2]);
                bMesh.castShadow = true;
                group.add(bMesh);

                const numFloors = Math.floor(b.size[1] / 3);
                for (let f = 1; f < numFloors; f++) {{
                    const winGeo = new THREE.BoxGeometry(b.size[0] + 0.08, 0.5, b.size[2] + 0.08);
                    const winMat = new THREE.MeshStandardMaterial({{
                        color: (idx === 2) ? 0xf43f5e : 0x38bdf8,
                        emissive: (idx === 2) ? 0x991b1b : 0x075985,
                        emissiveIntensity: 0.6
                    }});
                    const winMesh = new THREE.Mesh(winGeo, winMat);
                    winMesh.position.set(b.pos[0], b.pos[1] - b.size[1] / 2 + f * 3, b.pos[2]);
                    group.add(winMesh);
                }}

                if (idx === 2) {{
                    const beaconMesh = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.6, 0.6, 1.2, 16),
                        new THREE.MeshStandardMaterial({{ color: 0xef4444, emissive: 0xff0000, emissiveIntensity: 0.9 }})
                    );
                    beaconMesh.position.set(b.pos[0], b.pos[1] + b.size[1] / 2 + 0.6, b.pos[2]);
                    group.add(beaconMesh);

                    rescueBeacon = new THREE.PointLight(0xef4444, 2.5, 25);
                    rescueBeacon.position.copy(beaconMesh.position);
                    group.add(rescueBeacon);
                }}
            }});
        }})();

        // --- Scenario 3: 無人機碰撞測試場地 (Collision Arena) ---
        (function buildCollisionArena() {{
            const group = envGroups.collision_arena;

            const floorGeo = new THREE.PlaneGeometry(100, 100);
            const floorMat = new THREE.MeshStandardMaterial({{
                color: 0x020617,
                roughness: 0.25,
                metalness: 0.8,
                side: THREE.DoubleSide,
                polygonOffset: true,
                polygonOffsetFactor: 1.0,
                polygonOffsetUnits: 1.0
            }});
            const floorMesh = new THREE.Mesh(floorGeo, floorMat);
            floorMesh.rotation.x = -Math.PI / 2;
            floorMesh.position.y = -0.02;
            group.add(floorMesh);

            const cageBox = new THREE.BoxGeometry(40, 12, 40);
            const cageEdge = new THREE.EdgesGeometry(cageBox);
            const cageLine = new THREE.LineSegments(cageEdge, new THREE.LineBasicMaterial({{ color: 0x00e5ff, linewidth: 2 }}));
            cageLine.position.set(0, 6, 0);
            group.add(cageLine);

            const gates = [
                {{ pos: [0, 3.2, -7], color: 0x00e5ff, size: [4.5, 3.5] }},
                {{ pos: [9, 4.5, 0], color: 0xf43f5e, size: [4.0, 4.0] }},
                {{ pos: [0, 6.0, 9], color: 0xf59e0b, size: [4.5, 3.5] }},
                {{ pos: [-9, 3.8, 0], color: 0x22c55e, size: [4.0, 4.0] }}
            ];

            gates.forEach(g => {{
                const postGeo = new THREE.BoxGeometry(0.25, g.size[1], 0.25);
                const postMat = new THREE.MeshStandardMaterial({{ color: g.color, emissive: g.color, emissiveIntensity: 0.6 }});

                const postL = new THREE.Mesh(postGeo, postMat);
                postL.position.set(g.pos[0] - g.size[0]/2, g.pos[1], g.pos[2]);
                group.add(postL);

                const postR = new THREE.Mesh(postGeo, postMat);
                postR.position.set(g.pos[0] + g.size[0]/2, g.pos[1], g.pos[2]);
                group.add(postR);

                const topGeo = new THREE.BoxGeometry(g.size[0] + 0.25, 0.25, 0.25);
                const topMesh = new THREE.Mesh(topGeo, postMat);
                topMesh.position.set(g.pos[0], g.pos[1] + g.size[1]/2, g.pos[2]);
                group.add(topMesh);
            }});

            const pillars = [
                [3, 3], [-3, 3], [3, -3], [-3, -3], [7, 7], [-7, -7]
            ];
            pillars.forEach(p => {{
                const pGeo = new THREE.CylinderGeometry(0.55, 0.55, 6, 24);
                const pMat = new THREE.MeshStandardMaterial({{ color: 0xeab308, roughness: 0.3, metalness: 0.4 }});
                const pMesh = new THREE.Mesh(pGeo, pMat);
                pMesh.position.set(p[0], 3, p[1]);
                pMesh.castShadow = true;
                group.add(pMesh);
            }});
        }})();

        // --- Scenario 4: 夜間紅外線巡檢 (Night Thermal/Inspection) ---
        (function buildNightThermal() {{
            const group = envGroups.night_thermal;

            const nightFloorGeo = new THREE.PlaneGeometry(300, 300);
            const nightFloorMat = new THREE.MeshStandardMaterial({{
                color: 0x050714,
                roughness: 0.9,
                side: THREE.DoubleSide,
                polygonOffset: true,
                polygonOffsetFactor: 1.0,
                polygonOffsetUnits: 1.0
            }});
            const nightFloorMesh = new THREE.Mesh(nightFloorGeo, nightFloorMat);
            nightFloorMesh.rotation.x = -Math.PI / 2;
            nightFloorMesh.position.y = -0.02;
            group.add(nightFloorMesh);

            const xfmrGeo = new THREE.BoxGeometry(5.0, 3.6, 4.0);
            const xfmrMat = new THREE.MeshStandardMaterial({{ color: 0x1e1b4b, roughness: 0.4 }});
            const xfmrMesh = new THREE.Mesh(xfmrGeo, xfmrMat);
            xfmrMesh.position.set(8.0, 1.8, 6.0);
            group.add(xfmrMesh);

            for (let fin = -3; fin <= 3; fin++) {{
                const finGeo = new THREE.BoxGeometry(0.12, 2.6, 3.4);
                const finMat = new THREE.MeshStandardMaterial({{
                    color: 0xef4444,
                    emissive: 0xd97706,
                    emissiveIntensity: 0.85,
                    roughness: 0.3
                }});
                const finMesh = new THREE.Mesh(finGeo, finMat);
                finMesh.position.set(8.0 + fin * 0.55, 1.8, 6.0);
                group.add(finMesh);
            }}

            const pipeGeo = new THREE.CylinderGeometry(0.35, 0.35, 18, 16);
            const pipeMat = new THREE.MeshStandardMaterial({{
                color: 0xef4444,
                emissive: 0xff3b30,
                emissiveIntensity: 0.95,
                roughness: 0.25
            }});
            const pipeMesh = new THREE.Mesh(pipeGeo, pipeMat);
            pipeMesh.rotation.z = Math.PI / 2;
            pipeMesh.position.set(0, 4.5, -6.0);
            group.add(pipeMesh);
        }})();

        // Environment Configurations Matrix
        const ENVIRONMENTS = {{
            offshore_wind: {{
                name: '離岸風場巡檢 (Offshore Wind Farm)',
                tag: '離岸風場',
                badgeColor: '#00e5ff',
                bg: 0x0c2136,
                fogColor: 0x0c2136,
                fogDensity: 0.012,
                ambientColor: 0xbae6fd,
                ambientIntensity: 0.65,
                sunColor: 0xfffbeb,
                sunIntensity: 0.9,
                sunPos: [25, 40, 20],
                showThermalHud: false,
                droneSpotlight: false,
                gridColor1: 0x0284c7,
                gridColor2: 0x082f49
            }},
            urban_city: {{
                name: '城市高樓搜救 (Urban City Search & Rescue)',
                tag: '城市搜救',
                badgeColor: '#f59e0b',
                bg: 0x181e2b,
                fogColor: 0x181e2b,
                fogDensity: 0.018,
                ambientColor: 0xc7d2fe,
                ambientIntensity: 0.5,
                sunColor: 0xfdba74,
                sunIntensity: 0.8,
                sunPos: [30, 25, -20],
                showThermalHud: false,
                droneSpotlight: false,
                gridColor1: 0x64748b,
                gridColor2: 0x334155
            }},
            collision_arena: {{
                name: '碰撞測試場地 (Collision Arena)',
                tag: '碰撞競技場',
                badgeColor: '#ec4899',
                bg: 0x090d16,
                fogColor: 0x090d16,
                fogDensity: 0.016,
                ambientColor: 0xe0e7ff,
                ambientIntensity: 0.6,
                sunColor: 0x38bdf8,
                sunIntensity: 0.85,
                sunPos: [0, 30, 0],
                showThermalHud: false,
                droneSpotlight: false,
                gridColor1: 0x00e5ff,
                gridColor2: 0x1e1b4b
            }},
            night_thermal: {{
                name: '夜間紅外線巡檢 (Night Thermal/Inspection)',
                tag: '夜間紅外線',
                badgeColor: '#a855f7',
                bg: 0x030712,
                fogColor: 0x030712,
                fogDensity: 0.032,
                ambientColor: 0x312e81,
                ambientIntensity: 0.22,
                sunColor: 0x4338ca,
                sunIntensity: 0.25,
                sunPos: [10, 20, 10],
                showThermalHud: true,
                droneSpotlight: true,
                gridColor1: 0x6366f1,
                gridColor2: 0x1e1b4b
            }}
        }};

        let activeEnvKey = 'offshore_wind';

        function switchEnvironment(envKey) {{
            if (!ENVIRONMENTS[envKey]) return;
            const cfg = ENVIRONMENTS[envKey];
            activeEnvKey = envKey;

            // 1. Swap Environment Object Groups
            Object.keys(envGroups).forEach(k => {{
                if (k === envKey) {{
                    scene.add(envGroups[k]);
                }} else {{
                    scene.remove(envGroups[k]);
                }}
            }});

            // 2. Update Sky, Fog, and Grid
            scene.background = new THREE.Color(cfg.bg);
            scene.fog.color = new THREE.Color(cfg.fogColor);
            scene.fog.density = cfg.fogDensity;

            if (currentGrid) {{
                scene.remove(currentGrid);
                currentGrid.geometry.dispose();
                if (currentGrid.material) currentGrid.material.dispose();
            }}
            currentGrid = new THREE.GridHelper(40, 40, cfg.gridColor1, cfg.gridColor2);
            currentGrid.position.y = (envKey === 'offshore_wind') ? -0.8 : 0.0;
            scene.add(currentGrid);

            // 3. Update Lighting System
            ambientLight.color.setHex(cfg.ambientColor);
            ambientLight.intensity = cfg.ambientIntensity;
            dirLight.color.setHex(cfg.sunColor);
            dirLight.intensity = cfg.sunIntensity;
            dirLight.position.set(cfg.sunPos[0], cfg.sunPos[1], cfg.sunPos[2]);

            // 4. Update Drone Spotlight
            droneSpotlight.intensity = cfg.droneSpotlight ? 2.5 : 0.0;

            // 5. Update HUD Badges & Thermal Overlay
            const tagEl = document.getElementById('env-tag');
            if (tagEl) {{
                tagEl.innerText = cfg.tag;
                tagEl.style.color = cfg.badgeColor;
                tagEl.style.background = cfg.badgeColor + '26';
            }}

            const thermalHud = document.getElementById('thermal-hud');
            if (thermalHud) {{
                thermalHud.style.display = cfg.showThermalHud ? 'block' : 'none';
            }}

            const selectEl = document.getElementById('env-select');
            if (selectEl && selectEl.value !== envKey) {{
                selectEl.value = envKey;
            }}
        }}

        // Initialize with Offshore Wind Farm
        switchEnvironment('offshore_wind');

        // 4. Animation Loop
        const clock = new THREE.Clock();

        function animate() {{
            requestAnimationFrame(animate);
            const elapsedTime = clock.getElapsedTime();

            droneGroup.rotation.y += 0.005; // 360 preview rotation

            // Scenario animations
            if (activeEnvKey === 'offshore_wind') {{
                turbineRotors.forEach(r => r.rotation.z += 0.02);
                if (oceanGeo && oceanGeo.attributes.position) {{
                    const pos = oceanGeo.attributes.position;
                    const t = elapsedTime * 1.5;
                    for (let i = 0; i < pos.count; i++) {{
                        const u = pos.getX(i);
                        const v = pos.getY(i);
                        pos.setZ(i, Math.sin(u * 0.15 + t) * 0.2 + Math.cos(v * 0.15 + t * 0.8) * 0.15);
                    }}
                    pos.needsUpdate = true;
                    oceanGeo.computeVertexNormals();
                }}
            }} else if (activeEnvKey === 'urban_city') {{
                if (rescueBeacon) {{
                    rescueBeacon.intensity = 1.8 + Math.sin(elapsedTime * 6.0) * 1.4;
                }}
            }} else if (activeEnvKey === 'night_thermal') {{
                const spotEl = document.getElementById('thermal-spot');
                if (spotEl) {{
                    const temp = (84.2 + Math.sin(elapsedTime * 3.5) * 0.6).toFixed(1);
                    spotEl.innerText = temp + '°C (變壓器套管過熱)';
                }}
            }}

            controls.update();
            renderer.render(scene, camera);
        }}
        animate();

        function toggleBOM() {{
            const panel = document.getElementById('bom-panel');
            const btn = document.getElementById('bom-toggle-btn');
            panel.classList.toggle('collapsed');
            if (panel.classList.contains('collapsed')) {{
                btn.innerText = '展開 ▼';
            }} else {{
                btn.innerText = '收合 ▲';
            }}
        }}

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
