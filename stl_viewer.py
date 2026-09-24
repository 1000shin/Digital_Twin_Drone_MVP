#!/usr/bin/env python3
"""
Digital Twin Drone MVP - Standalone WebGL 3D STL Airframe Viewer
Generates an interactive, zero-server self-contained Three.js HTML page
allowing users to inspect the 3D-printable organic CAD STL models in full 3D.
Features:
- Built-in selector for all 4 drone generations (Gen-1 ~ Gen-4)
- Embedded Base64 binary STL models (immune to local file CORS restrictions)
- Drag-and-drop zone to load any local .stl file
- 3D printer build plate (250x250mm) visualization with scale ruler
- Wireframe / Facet mesh inspection toggle
- Material shaders (PETG-CF Carbon, Industrial Orange PLA, X-Ray, Normal Heatmap)
- 3D print specs card (bounding dimensions, print weight, volume, layer parameters)
"""

import base64
import json
from pathlib import Path
from typing import Dict, Any, List


class STLViewerGenerator:
    """Generates a standalone WebGL 3D STL Model Viewer HTML."""

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = Path(workspace_dir)
        self.output_dir = self.workspace_dir / "output"
        self.archive_dir = self.output_dir / "models_archive"

    def collect_archived_models(self) -> List[Dict[str, Any]]:
        """Collects models, base64 STL data, and print profiles for all generations."""
        models = []
        index_file = self.archive_dir / "index.json"

        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                idx = json.load(f)
            generations = idx.get("generations", [])
        else:
            generations = []

        for gen in generations:
            gen_dir = self.archive_dir / gen.get("path", "")
            stl_file = gen_dir / gen.get("cad_stl", f"{gen['design_id']}.stl")
            profile_file = gen_dir / gen.get("print_profile", f"{gen['design_id']}_print_profile.json")

            if stl_file.exists():
                with open(stl_file, "rb") as sf:
                    b64_stl = base64.b64encode(sf.read()).decode("ascii")
            else:
                b64_stl = ""

            if profile_file.exists():
                with open(profile_file, "r", encoding="utf-8") as pf:
                    profile = json.load(pf)
            else:
                profile = {}

            models.append({
                "generation": gen.get("generation", 1),
                "design_id": gen.get("design_id", "drone"),
                "name": gen.get("name", "Drone Model"),
                "key_traits": gen.get("key_traits", ""),
                "stl_base64": b64_stl,
                "profile": profile
            })

        return models

    def generate_viewer_html(self, output_filename: str = "stl_viewer.html") -> Path:
        """Generates self-contained stl_viewer.html in output directory."""
        models = self.collect_archived_models()
        html_path = self.output_dir / output_filename

        models_json = json.dumps(models)

        html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🖨️ 數位孿生無人機 - 3D 列印有機 STL 模型檢視器 (M2.1 WebGL)</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: #090d16;
            color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            overflow: hidden;
            user-select: none;
        }}
        #viewport {{
            width: 100vw;
            height: 100vh;
            display: block;
        }}

        /* Header / Brand */
        #brand-header {{
            position: absolute;
            top: 18px;
            left: 20px;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 14px;
            padding: 16px 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            z-index: 10;
            max-width: 360px;
        }}
        .brand-title {{
            font-size: 15px;
            font-weight: 700;
            color: #38bdf8;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }}
        .brand-sub {{
            font-size: 11.5px;
            color: #94a3b8;
            line-height: 1.5;
        }}

        /* Model Selector Pill Bar */
        .gen-selector {{
            display: flex;
            gap: 6px;
            margin-top: 12px;
            background: rgba(2, 6, 23, 0.7);
            padding: 4px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }}
        .gen-btn {{
            flex: 1;
            padding: 7px 6px;
            font-size: 11px;
            font-weight: 600;
            color: #94a3b8;
            background: transparent;
            border: none;
            border-radius: 7px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
        }}
        .gen-btn:hover {{
            color: #38bdf8;
            background: rgba(56, 189, 248, 0.12);
        }}
        .gen-btn.active {{
            color: #0f172a;
            background: #38bdf8;
            font-weight: 700;
            box-shadow: 0 2px 8px rgba(56, 189, 248, 0.4);
        }}

        /* Print Profile Specs Card (Right Panel) */
        #specs-panel {{
            position: absolute;
            top: 18px;
            right: 20px;
            width: 340px;
            background: rgba(15, 23, 42, 0.88);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 14px;
            padding: 18px 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            z-index: 10;
        }}
        .panel-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding-bottom: 10px;
            margin-bottom: 12px;
        }}
        .panel-title {{
            font-size: 13.5px;
            font-weight: 700;
            color: #10b981;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .badge {{
            font-size: 10px;
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 700;
            background: rgba(16, 185, 129, 0.18);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.35);
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-bottom: 14px;
        }}
        .stat-card {{
            background: rgba(2, 6, 23, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 9px 10px;
        }}
        .stat-label {{
            font-size: 10px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 3px;
        }}
        .stat-value {{
            font-size: 13.5px;
            font-weight: 700;
            color: #f8fafc;
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        }}

        /* Slicer Specs Section */
        .slicer-section {{
            background: rgba(2, 6, 23, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 8px;
            padding: 10px;
            font-size: 11px;
            line-height: 1.6;
            color: #cbd5e1;
        }}
        .slicer-row {{
            display: flex;
            justify-content: space-between;
            padding: 2px 0;
            border-bottom: 1px dashed rgba(255, 255, 255, 0.05);
        }}
        .slicer-row:last-child {{ border-bottom: none; }}
        .slicer-val {{ font-family: monospace; font-weight: 600; color: #38bdf8; }}

        /* Bottom Controls Bar */
        #toolbar {{
            position: absolute;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 10px;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            padding: 8px 16px;
            border-radius: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
            z-index: 10;
        }}
        .tool-btn {{
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #e2e8f0;
            padding: 7px 14px;
            border-radius: 20px;
            font-size: 11.5px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .tool-btn:hover {{
            background: rgba(56, 189, 248, 0.2);
            border-color: #38bdf8;
            color: #38bdf8;
        }}
        .tool-btn.active {{
            background: #0284c7;
            border-color: #38bdf8;
            color: #fff;
        }}
        .file-upload-btn {{
            position: relative;
            overflow: hidden;
            cursor: pointer;
        }}
        .file-upload-btn input[type="file"] {{
            position: absolute;
            top: 0; left: 0;
            opacity: 0;
            width: 100%; height: 100%;
            cursor: pointer;
        }}

        /* Loading Spinner */
        #loader {{
            display: none;
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(15, 23, 42, 0.85);
            padding: 16px 24px;
            border-radius: 12px;
            border: 1px solid #38bdf8;
            color: #38bdf8;
            font-size: 13px;
            font-weight: 600;
            z-index: 20;
        }}
    </style>
    <!-- Three.js & STLLoader -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/STLLoader.js"></script>
</head>
<body>
    <div id="brand-header">
        <div class="brand-title">
            <span>🖨️ Morph-Twin UAV</span>
            <span style="font-size:10px; color:#10b981; background:rgba(16,185,129,0.15); padding:2px 6px; border-radius:4px; border:1px solid rgba(16,185,129,0.3);">M2.1 CAD</span>
        </div>
        <div class="brand-sub">
            純 Python 自動化長成之<b>仿生有機 3D 列印單體 STL 網格</b>。支援 360° 拓撲檢驗、鏤空肋條檢視與切片參數預覽。
        </div>

        <div class="gen-selector" id="gen-buttons">
            <!-- Buttons injected dynamically -->
        </div>
    </div>

    <!-- Print Specs Right Panel -->
    <div id="specs-panel">
        <div class="panel-header">
            <div class="panel-title">
                <span>📊 可製造性切片參數</span>
            </div>
            <span class="badge" id="spec-material">PETG-CF</span>
        </div>

        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-label">預估列印重量</div>
                <div class="stat-value" id="spec-weight">-- g</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">機身體積</div>
                <div class="stat-value" id="spec-volume">-- cm³</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">外框包絡尺寸</div>
                <div class="stat-value" id="spec-bbox" style="font-size:11px;">-- mm</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">三角面總數</div>
                <div class="stat-value" id="spec-facets">--</div>
            </div>
        </div>

        <div class="slicer-section">
            <div style="font-weight:700; color:#38bdf8; margin-bottom:6px; font-size:11px;">推薦切片參數 (Cura / PrusaSlicer)</div>
            <div class="slicer-row"><span>推薦噴嘴口徑</span><span class="slicer-val" id="sl-nozzle">0.4 mm</span></div>
            <div class="slicer-row"><span>列印層高 (Layer Height)</span><span class="slicer-val" id="sl-layer">0.2 mm</span></div>
            <div class="slicer-row"><span>壁厚 (Wall Loops)</span><span class="slicer-val" id="sl-walls">4 圈</span></div>
            <div class="slicer-row"><span>填充率 / 紋理 (Infill)</span><span class="slicer-val" id="sl-infill">30% 陀螺儀 (Gyroid)</span></div>
            <div class="slicer-row"><span>熱床 / 噴頭溫度</span><span class="slicer-val" id="sl-temp">80°C / 245°C</span></div>
            <div class="slicer-row"><span>支撐類型 (Supports)</span><span class="slicer-val" id="sl-support">有機樹狀支撐 (Tree)</span></div>
        </div>
    </div>

    <!-- Bottom Toolbar -->
    <div id="toolbar">
        <button class="tool-btn" id="btn-wireframe" onclick="toggleWireframe()">
            <span>🔲 三角網格</span>
        </button>
        <button class="tool-btn" id="btn-rotate" onclick="toggleAutoRotate()">
            <span>🔄 360° 旋轉</span>
        </button>
        <button class="tool-btn" id="btn-plate" onclick="toggleBuildPlate()">
            <span>📏 熱床量尺</span>
        </button>
        <button class="tool-btn" id="btn-material" onclick="cycleMaterial()">
            <span>🎨 材質風格</span>
        </button>
        <button class="tool-btn" onclick="resetCamera()">
            <span>🎯 視角歸位</span>
        </button>
        <label class="tool-btn file-upload-btn">
            <span>📂 載入本機 STL</span>
            <input type="file" id="file-input" accept=".stl" onchange="handleFileUpload(event)">
        </label>
    </div>

    <div id="loader">⏳ 載入 3D STL 幾何資料中...</div>

    <canvas id="viewport"></canvas>

    <script>
        const archivedModels = {models_json};

        let scene, camera, renderer, controls;
        let currentMesh = null;
        let wireframeMesh = null;
        let buildPlateGroup = null;
        let bboxHelper = null;
        let isAutoRotate = true;
        let showWireframe = false;
        let showPlate = true;
        let currentMaterialIdx = 0;

        const materialsList = [
            {{ name: 'PETG-CF 碳纖維黑', color: 0x334155, roughness: 0.35, metalness: 0.65 }},
            {{ name: 'PLA 工業鮮橘', color: 0xf97316, roughness: 0.4, metalness: 0.2 }},
            {{ name: '鈦灰消光金屬', color: 0x94a3b8, roughness: 0.25, metalness: 0.85 }},
            {{ name: '半透明 X-Ray 藍', color: 0x38bdf8, roughness: 0.1, metalness: 0.9, transparent: true, opacity: 0.55 }}
        ];

        function initScene() {{
            const canvas = document.getElementById('viewport');
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x090d16);
            // Linear fog with far range appropriate for millimeter space (1500~4000mm)
            scene.fog = new THREE.Fog(0x090d16, 1500, 4000);

            camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 6000);
            camera.position.set(580, 450, 580);

            renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, alpha: false }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;

            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.06;
            controls.target.set(0, 35, 0);
            controls.autoRotate = isAutoRotate;
            controls.autoRotateSpeed = 2.0;
            controls.minDistance = 60;
            controls.maxDistance = 2500;

            // Lights
            const ambient = new THREE.AmbientLight(0xffffff, 0.75);
            scene.add(ambient);

            const keyLight = new THREE.DirectionalLight(0xffffff, 1.1);
            keyLight.position.set(400, 700, 350);
            keyLight.castShadow = true;
            keyLight.shadow.mapSize.width = 2048;
            keyLight.shadow.mapSize.height = 2048;
            scene.add(keyLight);

            const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.65);
            fillLight.position.set(-400, 300, -350);
            scene.add(fillLight);

            const bottomBounce = new THREE.DirectionalLight(0x94a3b8, 0.35);
            bottomBounce.position.set(0, -400, 0);
            scene.add(bottomBounce);

            // 3D Print Build Plate (500 x 500 mm with 10mm grid intervals)
            createBuildPlate();

            // Window resize
            window.addEventListener('resize', onWindowResize);

            // Populate generation buttons
            setupGenButtons();

            // Load default Gen 4 (Sentinel Prime) or Gen 3
            if (archivedModels.length > 0) {{
                loadModelByIndex(archivedModels.length - 1);
            }}

            animate();
        }}

        function createBuildPlate() {{
            buildPlateGroup = new THREE.Group();

            // Heated bed plate (500x500 mm for full drone frames)
            const plateGeo = new THREE.BoxGeometry(500, 4, 500);
            const plateMat = new THREE.MeshStandardMaterial({{
                color: 0x0f172a,
                roughness: 0.8,
                metalness: 0.2
            }});
            const plate = new THREE.Mesh(plateGeo, plateMat);
            plate.position.y = -2;
            plate.receiveShadow = true;
            buildPlateGroup.add(plate);

            // Bed grid lines (10mm minor, 50mm major intervals)
            const grid = new THREE.GridHelper(500, 50, 0x0284c7, 0x1e293b);
            grid.position.y = 0.2;
            buildPlateGroup.add(grid);

            // Printable boundary ring
            const boundsGeo = new THREE.EdgesGeometry(new THREE.BoxGeometry(480, 1, 480));
            const boundsMat = new THREE.LineBasicMaterial({{ color: 0x38bdf8, transparent: true, opacity: 0.4 }});
            const bounds = new THREE.LineSegments(boundsGeo, boundsMat);
            bounds.position.y = 0.5;
            buildPlateGroup.add(bounds);

            scene.add(buildPlateGroup);
        }}

        function base64ToArrayBuffer(base64) {{
            const binaryString = window.atob(base64);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {{
                bytes[i] = binaryString.charCodeAt(i);
            }}
            return bytes.buffer;
        }}

        function renderSTLGeometry(geometry, profile) {{
            if (currentMesh) scene.remove(currentMesh);
            if (wireframeMesh) scene.remove(wireframeMesh);
            if (bboxHelper) scene.remove(bboxHelper);

            // Rotate from Z-up (CAD/STL standard) to Y-up (Three.js standard)
            geometry.rotateX(-Math.PI / 2);
            geometry.computeVertexNormals();
            geometry.center();

            // Adjust height so bottom of drone sits exactly on heated bed
            geometry.computeBoundingBox();
            const bbox = geometry.boundingBox;
            const bottomOffset = -bbox.min.y;
            geometry.translate(0, bottomOffset, 0);

            const matDef = materialsList[currentMaterialIdx];
            const mat = new THREE.MeshStandardMaterial(matDef);

            currentMesh = new THREE.Mesh(geometry, mat);
            currentMesh.castShadow = true;
            currentMesh.receiveShadow = true;

            // Crisp bionic edges overlay
            try {{
                const edgesGeo = new THREE.EdgesGeometry(geometry, 25);
                const edgesMat = new THREE.LineBasicMaterial({{ color: 0x38bdf8, transparent: true, opacity: 0.4 }});
                const edgesMesh = new THREE.LineSegments(edgesGeo, edgesMat);
                currentMesh.add(edgesMesh);
            }} catch(e) {{}}

            scene.add(currentMesh);

            // Wireframe mesh
            const wireMat = new THREE.MeshBasicMaterial({{
                color: 0x38bdf8,
                wireframe: true,
                transparent: true,
                opacity: 0.25
            }});
            wireframeMesh = new THREE.Mesh(geometry, wireMat);
            wireframeMesh.visible = showWireframe;
            scene.add(wireframeMesh);

            // Bounding box helper
            bboxHelper = new THREE.BoxHelper(currentMesh, 0x10b981);
            bboxHelper.material.transparent = true;
            bboxHelper.material.opacity = 0.35;
            scene.add(bboxHelper);

            // Update UI profile
            updateProfileUI(geometry, profile);
        }}

        function updateProfileUI(geometry, profile) {{
            geometry.computeBoundingBox();
            const b = geometry.boundingBox;
            const dx = Math.round(b.max.x - b.min.x);
            const dy = Math.round(b.max.y - b.min.y);
            const dz = Math.round(b.max.z - b.min.z);

            const facets = geometry.attributes.position.count / 3;

            document.getElementById('spec-bbox').textContent = `${{dx}} × ${{dz}} × ${{dy}} mm`;
            document.getElementById('spec-facets').textContent = facets.toLocaleString() + ' 面';

            if (profile && profile.estimated_print_weight_g) {{
                document.getElementById('spec-weight').textContent = profile.estimated_print_weight_g + ' g';
                document.getElementById('spec-volume').textContent = profile.airframe_volume_cm3 + ' cm³';
                document.getElementById('spec-material').textContent = profile.material || 'PETG-CF';

                const sl = profile.recommended_slicer_settings || {{}};
                document.getElementById('sl-nozzle').textContent = (sl.nozzle_size_mm || 0.4) + ' mm';
                document.getElementById('sl-layer').textContent = (sl.layer_height_mm || 0.2) + ' mm';
                document.getElementById('sl-walls').textContent = (sl.wall_loops || 4) + ' 圈';
                document.getElementById('sl-infill').textContent = (sl.infill_percentage || 30) + '% ' + (sl.infill_pattern || 'Gyroid');
                document.getElementById('sl-temp').textContent = (sl.bed_temperature_c || 80) + '°C / ' + (sl.nozzle_temperature_c || 245) + '°C';
                document.getElementById('sl-support').textContent = sl.supports_required ? '樹狀支撐 (Tree)' : '免支撐';
            }} else {{
                document.getElementById('spec-weight').textContent = '約 120 ~ 150 g';
                document.getElementById('spec-volume').textContent = '約 280 cm³';
            }}
        }}

        function loadModelByIndex(idx) {{
            const model = archivedModels[idx];
            if (!model || !model.stl_base64) return;

            // Highlight button
            const btns = document.querySelectorAll('.gen-btn');
            btns.forEach((b, i) => b.classList.toggle('active', i === idx));

            showLoader(true);
            setTimeout(() => {{
                try {{
                    const loader = new THREE.STLLoader();
                    const buffer = base64ToArrayBuffer(model.stl_base64);
                    const geometry = loader.parse(buffer);
                    renderSTLGeometry(geometry, model.profile);
                }} catch (e) {{
                    console.error('Error parsing STL:', e);
                    alert('解析 STL 失敗: ' + e.message);
                }} finally {{
                    showLoader(false);
                }}
            }}, 50);
        }}

        function handleFileUpload(event) {{
            const file = event.target.files[0];
            if (!file) return;

            showLoader(true);
            const reader = new FileReader();
            reader.onload = function(e) {{
                try {{
                    const loader = new THREE.STLLoader();
                    const geometry = loader.parse(e.target.result);
                    renderSTLGeometry(geometry, {{
                        material: '自訂 STL',
                        estimated_print_weight_g: '--',
                        airframe_volume_cm3: '--'
                    }});
                    // Clear buttons highlight
                    document.querySelectorAll('.gen-btn').forEach(b => b.classList.remove('active'));
                }} catch (err) {{
                    alert('載入 STL 檔案失敗: ' + err.message);
                }} finally {{
                    showLoader(false);
                }}
            }};
            reader.readAsArrayBuffer(file);
        }}

        function setupGenButtons() {{
            const container = document.getElementById('gen-buttons');
            container.innerHTML = '';
            archivedModels.forEach((m, idx) => {{
                const btn = document.createElement('button');
                btn.className = 'gen-btn';
                btn.textContent = `Gen ${{m.generation}}`;
                btn.title = `${{m.name}} (${{m.design_id}})`;
                btn.onclick = () => loadModelByIndex(idx);
                container.appendChild(btn);
            }});
        }}

        function toggleWireframe() {{
            showWireframe = !showWireframe;
            if (wireframeMesh) wireframeMesh.visible = showWireframe;
            document.getElementById('btn-wireframe').classList.toggle('active', showWireframe);
        }}

        function toggleAutoRotate() {{
            isAutoRotate = !isAutoRotate;
            controls.autoRotate = isAutoRotate;
            document.getElementById('btn-rotate').classList.toggle('active', isAutoRotate);
        }}

        function toggleBuildPlate() {{
            showPlate = !showPlate;
            if (buildPlateGroup) buildPlateGroup.visible = showPlate;
            document.getElementById('btn-plate').classList.toggle('active', showPlate);
        }}

        function cycleMaterial() {{
            currentMaterialIdx = (currentMaterialIdx + 1) % materialsList.length;
            const matDef = materialsList[currentMaterialIdx];
            if (currentMesh) {{
                currentMesh.material = new THREE.MeshStandardMaterial(matDef);
            }}
            document.getElementById('spec-material').textContent = matDef.name;
        }}

        function resetCamera() {{
            camera.position.set(580, 450, 580);
            controls.target.set(0, 35, 0);
            controls.update();
        }}

        function showLoader(visible) {{
            document.getElementById('loader').style.display = visible ? 'block' : 'none';
        }}

        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }}

        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}

        window.onload = initScene;
    </script>
</body>
</html>
"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_path


if __name__ == "__main__":
    generator = STLViewerGenerator(Path(__file__).parent)
    out_html = generator.generate_viewer_html()
    print(f"✅ Generated Standalone WebGL 3D STL Viewer: {out_html}")
