#!/usr/bin/env python3
"""
Digital Twin Drone - Interactive WebGL 3D Flight Test Simulator
Combines Gazebo .world physics obstacles, motor thrust dynamics, 6-DOF flight physics,
and keyboard controls allowing users to test fly the evolved drone inside their browser.
Includes real-time Scene Environments switcher:
1. Offshore Wind Farm (海面水波/天空盒、巨大風力發電機)
2. Urban City Search & Rescue (建築群、街道障礙、搜救標記)
3. Collision Arena (防撞網格、立體柱體與穿越框)
4. Night Thermal/Inspection (暗黑高對比光影、探照燈、熱成像視角與過熱管線)
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
        """Builds a complete WebGL 3D Flight Test Simulator HTML file with environment switching."""
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
        body {{ margin: 0; padding: 0; overflow: hidden; background: #0b0d14; font-family: 'Segoe UI', Tahoma, sans-serif; color: #fff; user-select: none; }}
        #hud-panel {{
            position: absolute; top: 20px; left: 20px;
            background: rgba(10, 15, 30, 0.88); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
            padding: 20px 24px; border-radius: 16px; border: 1px solid #1a2a4a;
            min-width: 290px; box-shadow: 0 8px 32px rgba(0,0,0,0.65); z-index: 100;
        }}
        .hud-title {{ font-size: 15px; font-weight: bold; color: #00e5ff; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; display: flex; align-items: center; justify-content: space-between; }}
        .hud-row {{ display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 12.5px; font-family: monospace; }}
        .hud-value {{ font-weight: bold; color: #76ff03; }}
        .collision-warn {{ color: #ff1744; font-weight: bold; animation: blink 0.5s infinite alternate; display: none; margin-top: 8px; font-size: 12px; text-align: center; background: rgba(255, 23, 68, 0.15); padding: 5px; border-radius: 6px; border: 1px solid rgba(255, 23, 68, 0.4); }}
        @keyframes blink {{ from {{ opacity: 0.3; }} to {{ opacity: 1; }} }}

        /* Structural Damage & Health Styles */
        .integrity-bar-wrap {{
            width: 100%; height: 8px; background: rgba(255, 255, 255, 0.1); border-radius: 4px; overflow: hidden; margin: 4px 0 10px 0; border: 1px solid rgba(255, 255, 255, 0.15);
        }}
        .integrity-bar-fill {{
            width: 100%; height: 100%; background: #22c55e; transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), background 0.3s;
        }}
        .damage-box {{
            display: none; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.45); border-radius: 8px; padding: 9px 12px; margin-top: 8px; margin-bottom: 8px;
        }}
        .damage-box-header {{
            font-size: 11px; font-weight: bold; color: #f87171; margin-bottom: 5px; display: flex; align-items: center; justify-content: space-between;
        }}
        .damage-badge {{
            background: #ef4444; color: #fff; padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: bold;
        }}
        .damage-item-list {{
            font-size: 11px; color: #fca5a5; font-family: monospace; max-height: 85px; overflow-y: auto; line-height: 1.5;
        }}
        .hud-btn-row {{
            display: flex; gap: 8px; margin-top: 10px;
        }}
        .btn-action {{
            flex: 1; padding: 7px 10px; border-radius: 8px; font-size: 11.5px; font-weight: 700; cursor: pointer; transition: all 0.2s; outline: none; display: flex; align-items: center; justify-content: center; gap: 5px;
        }}
        .btn-repair {{
            background: linear-gradient(135deg, #0284c7, #0369a1); border: 1px solid #38bdf8; color: #fff; box-shadow: 0 2px 10px rgba(2, 132, 199, 0.4);
        }}
        .btn-repair:hover {{ background: linear-gradient(135deg, #0369a1, #0284c7); box-shadow: 0 0 12px rgba(56, 189, 248, 0.6); transform: translateY(-1px); }}
        .btn-test-crash {{
            background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.5); color: #fca5a5;
        }}
        .btn-test-crash:hover {{ background: rgba(239, 68, 68, 0.35); color: #fff; transform: translateY(-1px); }}
        #toast-notice {{
            position: fixed; top: 25px; left: 50%; transform: translateX(-50%);
            background: rgba(15, 23, 42, 0.95); border: 1px solid #38bdf8; color: #e0f2fe;
            padding: 10px 20px; border-radius: 24px; font-size: 13px; font-weight: bold;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.7), 0 0 15px rgba(56, 189, 248, 0.3);
            display: none; z-index: 9999; animation: fadeInOut 2.5s forwards;
        }}
        @keyframes fadeInOut {{ 0% {{ opacity: 0; transform: translate(-50%, -10px); }} 15% {{ opacity: 1; transform: translate(-50%, 0); }} 85% {{ opacity: 1; transform: translate(-50%, 0); }} 100% {{ opacity: 0; transform: translate(-50%, -10px); }} }}

        /* Flight Data Recorder HUD Styles */
        .recorder-section {{
            margin-top: 12px; padding: 10px 12px;
            background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 10px;
        }}
        .recorder-header {{
            display: flex; align-items: center; justify-content: space-between;
            font-size: 11px; font-weight: 700; color: #cbd5e1; margin-bottom: 7px;
        }}
        .rec-indicator {{
            display: inline-flex; align-items: center; gap: 5px; font-size: 10px; font-weight: bold;
            padding: 2px 7px; border-radius: 10px; background: rgba(148, 163, 184, 0.15); color: #94a3b8;
        }}
        .rec-indicator.recording {{
            background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4);
        }}
        .rec-dot {{
            width: 7px; height: 7px; border-radius: 50%; background: #94a3b8;
        }}
        .rec-indicator.recording .rec-dot {{
            background: #ef4444; animation: blinkRec 0.8s infinite alternate;
        }}
        @keyframes blinkRec {{ 0% {{ opacity: 0.2; transform: scale(0.8); }} 100% {{ opacity: 1; transform: scale(1.2); }} }}
        .recorder-stats {{
            display: flex; justify-content: space-between; font-size: 11px; font-family: monospace;
            color: #94a3b8; margin-bottom: 8px;
        }}
        .btn-rec-start {{
            background: linear-gradient(135deg, #dc2626, #b91c1c); border: 1px solid #f87171; color: #fff;
            box-shadow: 0 2px 8px rgba(220, 38, 38, 0.4);
        }}
        .btn-rec-start:hover {{
            background: linear-gradient(135deg, #ef4444, #dc2626); box-shadow: 0 0 12px rgba(248, 113, 113, 0.6);
        }}
        .btn-rec-stop {{
            background: rgba(148, 163, 184, 0.2); border: 1px solid rgba(148, 163, 184, 0.4); color: #cbd5e1;
        }}
        .btn-rec-stop:hover {{
            background: rgba(148, 163, 184, 0.35); color: #fff;
        }}
        .btn-rec-export {{
            background: linear-gradient(135deg, #059669, #047857); border: 1px solid #34d399; color: #fff;
            box-shadow: 0 2px 8px rgba(5, 150, 105, 0.4);
        }}
        .btn-rec-export:hover {{
            background: linear-gradient(135deg, #10b981, #059669); box-shadow: 0 0 12px rgba(52, 211, 153, 0.6);
        }}

        /* Reset Questionnaire Modal Styles */
        #reset-modal-overlay {{
            display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(4, 7, 16, 0.85); backdrop-filter: blur(8px);
            z-index: 10000; align-items: center; justify-content: center;
        }}
        #reset-modal {{
            background: #0f172a; border: 1px solid #38bdf8; border-radius: 16px;
            width: 440px; max-width: 90vw; padding: 22px 24px; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 20px rgba(56, 189, 248, 0.2);
            color: #e2e8f0; font-family: 'Segoe UI', Tahoma, sans-serif;
        }}
        .modal-title {{
            font-size: 15px; font-weight: 700; color: #38bdf8; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;
        }}
        .modal-desc {{
            font-size: 12px; color: #94a3b8; margin-bottom: 14px; line-height: 1.5;
        }}
        .modal-field {{
            margin-bottom: 12px;
        }}
        .modal-label {{
            font-size: 11.5px; font-weight: 600; color: #cbd5e1; margin-bottom: 5px; display: block;
        }}
        .modal-select, .modal-textarea {{
            width: 100%; box-sizing: border-box; background: #0b1120; border: 1px solid #334155;
            color: #f1f5f9; padding: 8px 10px; border-radius: 8px; font-size: 12px; outline: none; transition: border-color 0.2s;
        }}
        .modal-select:focus, .modal-textarea:focus {{
            border-color: #38bdf8; box-shadow: 0 0 8px rgba(56, 189, 248, 0.3);
        }}
        .modal-textarea {{
            resize: vertical; min-height: 55px; font-family: inherit;
        }}
        .modal-btn-row {{
            display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px;
        }}
        .btn-modal-cancel {{
            background: rgba(148, 163, 184, 0.15); border: 1px solid rgba(148, 163, 184, 0.3);
            color: #94a3b8; padding: 7px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer;
        }}
        .btn-modal-cancel:hover {{
            background: rgba(148, 163, 184, 0.25); color: #e2e8f0;
        }}
        .btn-modal-confirm {{
            background: linear-gradient(135deg, #0284c7, #0369a1); border: 1px solid #38bdf8;
            color: #fff; padding: 7px 16px; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer;
            box-shadow: 0 2px 10px rgba(2, 132, 199, 0.4);
        }}
        .btn-modal-confirm:hover {{
            background: linear-gradient(135deg, #0369a1, #0284c7); box-shadow: 0 0 12px rgba(56, 189, 248, 0.6);
        }}

        /* Environment Selector */
        .env-section {{
            margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(0, 229, 255, 0.2);
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
            display: none; position: absolute; top: 20px; left: 360px;
            background: rgba(5, 7, 18, 0.9); backdrop-filter: blur(10px);
            border: 1px solid #6366f1; border-radius: 12px; padding: 12px 18px;
            font-family: monospace; font-size: 12px; box-shadow: 0 6px 24px rgba(99, 102, 241, 0.3); z-index: 100;
        }}
        .thermal-bar {{
            width: 130px; height: 10px; border-radius: 4px;
            background: linear-gradient(to right, #000000, #312e81, #7c3aed, #dc2626, #ea580c, #facc15, #ffffff);
            border: 1px solid #475569;
        }}

        #control-panel {{
            position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
            background: rgba(10, 15, 30, 0.88); backdrop-filter: blur(8px);
            padding: 12px 24px; border-radius: 30px; border: 1px solid #1a2a4a;
            font-size: 12.5px; color: #b0bec5; display: flex; gap: 18px; z-index: 100;
            box-shadow: 0 8px 24px rgba(0,0,0,0.5);
        }}
        .key {{ background: #1e293b; border: 1px solid #334155; color: #38bdf8; padding: 2px 7px; border-radius: 4px; font-weight: bold; font-family: monospace; }}

        /* BOM Drawer / Panel */
        #bom-panel {{
            position: absolute; top: 20px; right: 20px;
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
    <div id="hud-panel">
        <div class="hud-title">
            <span>🚁 數位孿生 3D 試飛 HUD</span>
        </div>
        <div class="hud-row"><span>飛行狀態:</span><span id="st-mode" class="hud-value">OFFBOARD - ARM</span></div>
        <div class="hud-row"><span>高度 (Z):</span><span id="st-alt" class="hud-value">0.00 m</span></div>
        <div class="hud-row"><span>水平速度:</span><span id="st-spd" class="hud-value">0.00 m/s</span></div>
        <div class="hud-row"><span>鋰電池電壓:</span><span id="st-bat" class="hud-value">11.80 V</span></div>
        <div class="hud-row"><span>風場矢量:</span><span id="st-wind" style="color:#e040fb">{wind_xyz[0]} m/s (X)</span></div>
        <div class="hud-row" style="margin-top: 7px;"><span>機身結構完整度:</span><span id="st-integrity" class="hud-value" style="color:#4ade80;">100% (完好)</span></div>
        <div class="integrity-bar-wrap"><div id="st-integrity-bar" class="integrity-bar-fill" style="width: 100%; background: #22c55e;"></div></div>
        <div id="damage-panel" class="damage-box">
            <div class="damage-box-header">
                <span>⚠️ 結構破損監控警示</span>
                <span id="damage-count" class="damage-badge">0 部件受損</span>
            </div>
            <div id="damage-list" class="damage-item-list"></div>
        </div>
        <div id="collision-alert" class="collision-warn">⚠️ 警告：觸發環境障礙物剛體碰撞！</div>
        <div class="hud-btn-row">
            <button id="btn-repair" class="btn-action btn-repair" onclick="promptResetExperience()">🛠️ 維修與重置 (R)</button>
            <button id="btn-crash-test" class="btn-action btn-test-crash" onclick="simulateTestCrash()">💥 撞擊測試</button>
        </div>

        <!-- Flight Data Recorder HUD Panel -->
        <div class="recorder-section">
            <div class="recorder-header">
                <span>📹 遙測示範資料錄製</span>
                <span id="rec-status-badge" class="rec-indicator"><span class="rec-dot"></span><span id="rec-status-text">待命 IDLE</span></span>
            </div>
            <div class="recorder-stats">
                <span>時長: <span id="rec-time" style="color:#38bdf8; font-weight:bold;">00:00.0</span></span>
                <span>樣本: <span id="rec-samples" style="color:#4ade80; font-weight:bold;">0</span> 筆</span>
            </div>
            <div class="hud-btn-row" style="margin-top: 0;">
                <button id="btn-rec-toggle" class="btn-action btn-rec-start" onclick="toggleRecording()">🔴 開始錄製 (G)</button>
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
            <span style="animation: blink 0.8s infinite alternate; color: #f43f5e; font-weight: bold;">● LIVE</span>
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

    <div id="control-panel">
        <div><span class="key">W</span> <span class="key">S</span> 俯仰</div>
        <div><span class="key">A</span> <span class="key">D</span> 翻滾</div>
        <div><span class="key">↑</span> <span class="key">↓</span> 油門</div>
        <div><span class="key">←</span> <span class="key">→</span> 偏航</div>
        <div><span class="key">Space</span> 自動懸停</div>
        <div><span class="key">G</span> 錄製/停止</div>
        <div><span class="key">R</span> 維修重置</div>
    </div>

    <!-- Reset Questionnaire Modal Dialog -->
    <div id="reset-modal-overlay">
        <div id="reset-modal">
            <div class="modal-title">
                <span>📝 飛行經驗回饋</span>
            </div>
            <div class="modal-desc">
                在維修重置無人機之前，請填寫本次飛行心得、操控感受或重置原因。此資訊將自動與飛行控制軌跡及受損數據一併封裝保存為 AI 訓練經驗集。
            </div>
            <div class="modal-field">
                <label class="modal-label">飛行心得與重置原因：</label>
                <textarea id="modal-notes" class="modal-textarea" placeholder="請在此填寫本次飛行心得、操控感受或重置原因..."></textarea>
            </div>
            <div class="modal-btn-row">
                <button class="btn-modal-cancel" onclick="closeResetModal(true)">直接重置 (跳過)</button>
                <button class="btn-modal-confirm" onclick="confirmResetWithFeedback()">確定重置並保存</button>
            </div>
        </div>
    </div>

    <div id="toast-notice"></div>

    <script>
        // 1. Scene, Camera, Renderer Setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0c2136);
        scene.fog = new THREE.FogExp2(0x0c2136, 0.015);

        const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 200);
        camera.position.set(0, 3, 6);

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        document.body.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;

        // Dynamic Lighting System
        const ambientLight = new THREE.AmbientLight(0xbae6fd, 0.65);
        scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xfffbeb, 0.9);
        sunLight.position.set(25, 40, 20);
        sunLight.castShadow = true;
        sunLight.shadow.mapSize.width = 1024;
        sunLight.shadow.mapSize.height = 1024;
        scene.add(sunLight);

        let currentGrid = new THREE.GridHelper(50, 50, 0x0284c7, 0x082f49);
        scene.add(currentGrid);

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

        // Arms & Motors & Structural Damage Component Registry
        const numArms = {num_arms};
        const armLength = {arm_length};
        const propDisks = [];
        const droneArmComponents = [];
        for (let i = 0; i < numArms; i++) {{
            const angle = (i * 2 * Math.PI) / numArms;
            const x = armLength * Math.cos(angle);
            const z = armLength * Math.sin(angle);

            const armGeo = new THREE.CylinderGeometry(0.015, 0.015, armLength);
            const armMat = new THREE.MeshStandardMaterial({{ color: 0x0f172a, roughness: 0.4 }});
            const armMesh = new THREE.Mesh(armGeo, armMat);
            armMesh.position.set(x / 2, 0, z / 2);
            armMesh.rotation.z = Math.PI / 2;
            armMesh.rotation.y = -angle;
            drone.add(armMesh);

            const motorGeo = new THREE.CylinderGeometry(0.03, 0.03, 0.04);
            const motorMat = new THREE.MeshStandardMaterial({{ color: 0xef4444, metalness: 0.5, roughness: 0.3 }});
            const motorMesh = new THREE.Mesh(motorGeo, motorMat);
            motorMesh.position.set(x, 0.02, z);
            drone.add(motorMesh);

            const propGeo = new THREE.CylinderGeometry(0.14, 0.14, 0.005, 32);
            const propMat = new THREE.MeshStandardMaterial({{ color: 0x38bdf8, transparent: true, opacity: 0.5 }});
            const propMesh = new THREE.Mesh(propGeo, propMat);
            propMesh.position.set(x, 0.04, z);
            drone.add(propMesh);

            droneArmComponents.push({{
                index: i,
                angle: angle,
                x: x,
                z: z,
                armMesh: armMesh,
                motorMesh: motorMesh,
                propMesh: propMesh,
                origArmRot: {{ x: armMesh.rotation.x, y: armMesh.rotation.y, z: armMesh.rotation.z }},
                origArmPos: {{ x: armMesh.position.x, y: armMesh.position.y, z: armMesh.position.z }},
                origMotorRot: {{ x: motorMesh.rotation.x, y: motorMesh.rotation.y, z: motorMesh.rotation.z }},
                origMotorPos: {{ x: motorMesh.position.x, y: motorMesh.position.y, z: motorMesh.position.z }},
                isArmBroken: false,
                isPropBroken: false,
                isMotorDamaged: false
            }});

            propDisks.push({{
                mesh: propMesh,
                dir: (i % 2 === 0) ? 1 : -1,
                broken: false,
                index: i
            }});
        }}

        // LiDAR Sensor
        const lidarGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.05);
        const lidarMat = new THREE.MeshStandardMaterial({{ color: 0x22c55e }});
        const lidarMesh = new THREE.Mesh(lidarGeo, lidarMat);
        lidarMesh.position.set(0, 0.16, 0);
        drone.add(lidarMesh);

        // Drone Searchlight (for Night Thermal / Inspection)
        const droneSpotlight = new THREE.SpotLight(0x67e8f9, 0.0, 35, Math.PI / 4.5, 0.4, 1.2);
        droneSpotlight.position.set(0, -0.05, 0.1);
        const droneSpotlightTarget = new THREE.Object3D();
        droneSpotlightTarget.position.set(0, -8, 14);
        drone.add(droneSpotlight);
        drone.add(droneSpotlightTarget);
        droneSpotlight.target = droneSpotlightTarget;

        drone.position.set(0, 0.05, 0);
        scene.add(drone);

        // 3. Base Gazebo .world Obstacles & Bounding Boxes
        const baseObstaclesData = {json.dumps(obstacles)};
        const baseObstacleMeshes = [];

        baseObstaclesData.forEach((obs) => {{
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

            obsMesh.geometry.computeBoundingBox();
            baseObstacleMeshes.push({{
                mesh: obsMesh,
                box: new THREE.Box3().setFromObject(obsMesh)
            }});
        }});

        // 4. Multi-Scenario Environments Construction
        const envGroups = {{
            offshore_wind: new THREE.Group(),
            urban_city: new THREE.Group(),
            collision_arena: new THREE.Group(),
            night_thermal: new THREE.Group()
        }};

        const envObstacles = {{
            offshore_wind: [],
            urban_city: [],
            collision_arena: [],
            night_thermal: []
        }};

        const turbineRotors = [];
        let oceanGeo = null;
        let rescueBeacon = null;

        // --- Scenario 1: 離岸風場巡檢 (Offshore Wind Farm) ---
        (function buildOffshoreWind() {{
            const group = envGroups.offshore_wind;

            // Dynamic Ocean Water Plane
            oceanGeo = new THREE.PlaneGeometry(350, 350, 48, 48);
            const oceanMat = new THREE.MeshStandardMaterial({{
                color: 0x0284c7,
                roughness: 0.15,
                metalness: 0.7,
                transparent: true,
                opacity: 0.92
            }});
            const oceanMesh = new THREE.Mesh(oceanGeo, oceanMat);
            oceanMesh.rotation.x = -Math.PI / 2;
            oceanMesh.position.y = -0.15;
            group.add(oceanMesh);

            // 3 Giant Wind Turbines
            const turbinePositions = [
                [18, -12],
                [-20, 16],
                [4, -30]
            ];

            turbinePositions.forEach((tp) => {{
                const tx = tp[0], tz = tp[1];

                // Yellow Maritime Foundation Platform
                const baseGeo = new THREE.CylinderGeometry(2.4, 2.7, 2.0, 16);
                const baseMat = new THREE.MeshStandardMaterial({{ color: 0xf59e0b, roughness: 0.4 }});
                const baseMesh = new THREE.Mesh(baseGeo, baseMat);
                baseMesh.position.set(tx, 0.85, tz);
                baseMesh.castShadow = true;
                group.add(baseMesh);

                // Tower Mast (Height 20m)
                const towerGeo = new THREE.CylinderGeometry(0.45, 0.9, 20, 16);
                const towerMat = new THREE.MeshStandardMaterial({{ color: 0xf8fafc, roughness: 0.3 }});
                const towerMesh = new THREE.Mesh(towerGeo, towerMat);
                towerMesh.position.set(tx, 11.0, tz);
                towerMesh.castShadow = true;
                group.add(towerMesh);

                // Nacelle
                const nacelleGeo = new THREE.BoxGeometry(1.6, 1.3, 3.2);
                const nacelleMat = new THREE.MeshStandardMaterial({{ color: 0xe2e8f0, roughness: 0.3 }});
                const nacelleMesh = new THREE.Mesh(nacelleGeo, nacelleMat);
                nacelleMesh.position.set(tx, 21.0, tz);
                nacelleMesh.castShadow = true;
                group.add(nacelleMesh);

                // Rotor Hub & 3 Aerodynamic Blades
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
                    bladeMesh.castShadow = true;
                    rotorHub.add(bladeMesh);
                }}

                group.add(rotorHub);
                turbineRotors.push(rotorHub);

                baseMesh.geometry.computeBoundingBox();
                towerMesh.geometry.computeBoundingBox();
                envObstacles.offshore_wind.push({{ mesh: baseMesh, box: new THREE.Box3().setFromObject(baseMesh) }});
                envObstacles.offshore_wind.push({{ mesh: towerMesh, box: new THREE.Box3().setFromObject(towerMesh) }});
            }});

            // Maritime Warning Buoys
            const buoyGeo = new THREE.CylinderGeometry(0.5, 0.7, 1.4, 12);
            const buoyMat = new THREE.MeshStandardMaterial({{ color: 0xef4444 }});
            const buoy1 = new THREE.Mesh(buoyGeo, buoyMat);
            buoy1.position.set(6, 0.5, 6);
            group.add(buoy1);
            buoy1.geometry.computeBoundingBox();
            envObstacles.offshore_wind.push({{ mesh: buoy1, box: new THREE.Box3().setFromObject(buoy1) }});
        }})();

        // --- Scenario 2: 城市高樓搜救 (Urban City Search & Rescue) ---
        (function buildUrbanCity() {{
            const group = envGroups.urban_city;

            // Asphalt Ground Plane
            const streetGeo = new THREE.PlaneGeometry(300, 300);
            const streetMat = new THREE.MeshStandardMaterial({{ color: 0x18181b, roughness: 0.95 }});
            const streetMesh = new THREE.Mesh(streetGeo, streetMat);
            streetMesh.rotation.x = -Math.PI / 2;
            streetMesh.position.y = -0.05;
            group.add(streetMesh);

            // High-Rise City Buildings
            const buildings = [
                {{ pos: [15, 9, -12], size: [9, 18, 9], color: 0x1e293b, label: 'Commercial Tower' }},
                {{ pos: [-16, 12, -10], size: [10, 24, 10], color: 0x0f172a, label: 'Office Plaza' }},
                {{ pos: [0, 11, 24], size: [12, 22, 10], color: 0x1e2230, label: 'Rescue Objective Building' }},
                {{ pos: [-15, 7, 16], size: [9, 14, 9], color: 0x27272a, label: 'Residential Complex' }},
                {{ pos: [16, 8, 14], size: [8, 16, 11], color: 0x181e28, label: 'Hospital Annex' }},
                {{ pos: [2, 4, -22], size: [14, 8, 8], color: 0x334155, label: 'Parking Structure' }}
            ];

            buildings.forEach((b, idx) => {{
                const bGeo = new THREE.BoxGeometry(b.size[0], b.size[1], b.size[2]);
                const bMat = new THREE.MeshStandardMaterial({{ color: b.color, roughness: 0.4, metalness: 0.5 }});
                const bMesh = new THREE.Mesh(bGeo, bMat);
                bMesh.position.set(b.pos[0], b.pos[1], b.pos[2]);
                bMesh.castShadow = true;
                bMesh.receiveShadow = true;
                group.add(bMesh);

                // Horizontal Window Glow Bands
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

                // Search & Rescue Target Rooftop Beacon (on Building 3)
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

                bMesh.geometry.computeBoundingBox();
                envObstacles.urban_city.push({{ mesh: bMesh, box: new THREE.Box3().setFromObject(bMesh) }});
            }});

            // Street Containers & Obstacles
            const containers = [
                {{ pos: [3, 0.7, 5], size: [4, 1.4, 2.2], color: 0x0284c7 }},
                {{ pos: [-4, 0.7, 3], size: [4, 1.4, 2.2], color: 0xf59e0b }},
                {{ pos: [6, 0.7, -4], size: [3.5, 1.4, 2.0], color: 0xef4444 }}
            ];
            containers.forEach(c => {{
                const cGeo = new THREE.BoxGeometry(c.size[0], c.size[1], c.size[2]);
                const cMat = new THREE.MeshStandardMaterial({{ color: c.color, roughness: 0.6 }});
                const cMesh = new THREE.Mesh(cGeo, cMat);
                cMesh.position.set(c.pos[0], c.pos[1], c.pos[2]);
                cMesh.castShadow = true;
                group.add(cMesh);
                cMesh.geometry.computeBoundingBox();
                envObstacles.urban_city.push({{ mesh: cMesh, box: new THREE.Box3().setFromObject(cMesh) }});
            }});
        }})();

        // --- Scenario 3: 無人機碰撞測試場地 (Collision Arena) ---
        (function buildCollisionArena() {{
            const group = envGroups.collision_arena;

            // Reflective Hi-Tech Testing Floor
            const floorGeo = new THREE.PlaneGeometry(100, 100);
            const floorMat = new THREE.MeshStandardMaterial({{ color: 0x020617, roughness: 0.25, metalness: 0.8 }});
            const floorMesh = new THREE.Mesh(floorGeo, floorMat);
            floorMesh.rotation.x = -Math.PI / 2;
            floorMesh.position.y = -0.05;
            group.add(floorMesh);

            // Boundary Wireframe Cage Wall Frames
            const cageBox = new THREE.BoxGeometry(40, 12, 40);
            const cageEdge = new THREE.EdgesGeometry(cageBox);
            const cageLine = new THREE.LineSegments(cageEdge, new THREE.LineBasicMaterial({{ color: 0x00e5ff, linewidth: 2 }}));
            cageLine.position.set(0, 6, 0);
            group.add(cageLine);

            // Glowing FPV / Obstacle Course Flight Gates
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

                postL.geometry.computeBoundingBox();
                postR.geometry.computeBoundingBox();
                topMesh.geometry.computeBoundingBox();
                envObstacles.collision_arena.push({{ mesh: postL, box: new THREE.Box3().setFromObject(postL) }});
                envObstacles.collision_arena.push({{ mesh: postR, box: new THREE.Box3().setFromObject(postR) }});
                envObstacles.collision_arena.push({{ mesh: topMesh, box: new THREE.Box3().setFromObject(topMesh) }});
            }});

            // 6 Cylindrical Collision Pillars with Hazard Stripes
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
                pMesh.geometry.computeBoundingBox();
                envObstacles.collision_arena.push({{ mesh: pMesh, box: new THREE.Box3().setFromObject(pMesh) }});
            }});

            // Inclined Aerobatic Launch Ramp
            const rampGeo = new THREE.BoxGeometry(4, 0.3, 8);
            const rampMat = new THREE.MeshStandardMaterial({{ color: 0x3b82f6, metalness: 0.6 }});
            const rampMesh = new THREE.Mesh(rampGeo, rampMat);
            rampMesh.position.set(0, 1.2, -15);
            rampMesh.rotation.x = 0.28;
            group.add(rampMesh);
            rampMesh.geometry.computeBoundingBox();
            envObstacles.collision_arena.push({{ mesh: rampMesh, box: new THREE.Box3().setFromObject(rampMesh) }});
        }})();

        // --- Scenario 4: 夜間紅外線巡檢 (Night Thermal/Inspection) ---
        (function buildNightThermal() {{
            const group = envGroups.night_thermal;

            // Midnight Dark Ground with Infrared Grid
            const nightFloorGeo = new THREE.PlaneGeometry(300, 300);
            const nightFloorMat = new THREE.MeshStandardMaterial({{ color: 0x050714, roughness: 0.9 }});
            const nightFloorMesh = new THREE.Mesh(nightFloorGeo, nightFloorMat);
            nightFloorMesh.rotation.x = -Math.PI / 2;
            nightFloorMesh.position.y = -0.05;
            group.add(nightFloorMesh);

            // High-Voltage Electrical Substation & Hot Radiators
            const xfmrGeo = new THREE.BoxGeometry(5.0, 3.6, 4.0);
            const xfmrMat = new THREE.MeshStandardMaterial({{ color: 0x1e1b4b, roughness: 0.4 }});
            const xfmrMesh = new THREE.Mesh(xfmrGeo, xfmrMat);
            xfmrMesh.position.set(8.0, 1.8, 6.0);
            xfmrMesh.castShadow = true;
            group.add(xfmrMesh);
            xfmrMesh.geometry.computeBoundingBox();
            envObstacles.night_thermal.push({{ mesh: xfmrMesh, box: new THREE.Box3().setFromObject(xfmrMesh) }});

            // False-Color Thermal Radiator Heat Fins (Hot: 78°C ~ 88°C)
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

            // Overhead Hot Industrial Pipeline (Overheat Warning: 84.6°C)
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
            pipeMesh.castShadow = true;
            group.add(pipeMesh);
            pipeMesh.geometry.computeBoundingBox();
            envObstacles.night_thermal.push({{ mesh: pipeMesh, box: new THREE.Box3().setFromObject(pipeMesh) }});

            // Cold Ambient Support Pillars (15°C Ambient - Deep Blue/Indigo)
            const p1Geo = new THREE.CylinderGeometry(0.3, 0.3, 4.5, 16);
            const p1Mat = new THREE.MeshStandardMaterial({{ color: 0x312e81, emissive: 0x1e1b4b, emissiveIntensity: 0.4 }});
            const p1 = new THREE.Mesh(p1Geo, p1Mat);
            p1.position.set(-8, 2.25, -6.0);
            group.add(p1);
            p1.geometry.computeBoundingBox();
            envObstacles.night_thermal.push({{ mesh: p1, box: new THREE.Box3().setFromObject(p1) }});

            const p2 = new THREE.Mesh(p1Geo, p1Mat);
            p2.position.set(8, 2.25, -6.0);
            group.add(p2);
            p2.geometry.computeBoundingBox();
            envObstacles.night_thermal.push({{ mesh: p2, box: new THREE.Box3().setFromObject(p2) }});

            // High Voltage Lattice Pylon Tower (Height 18m)
            const pylonGeo = new THREE.CylinderGeometry(0.5, 1.2, 18, 4);
            const pylonMat = new THREE.MeshStandardMaterial({{ color: 0x4338ca, wireframe: true }});
            const pylonMesh = new THREE.Mesh(pylonGeo, pylonMat);
            pylonMesh.position.set(-14, 9, 12);
            group.add(pylonMesh);
            pylonMesh.geometry.computeBoundingBox();
            envObstacles.night_thermal.push({{ mesh: pylonMesh, box: new THREE.Box3().setFromObject(pylonMesh) }});
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
                wind: [4.5, 0.8, 0.0],
                windDesc: '4.5 m/s (強海風)',
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
                wind: [2.2, 0.0, 1.2],
                windDesc: '2.2 m/s (街道峽谷亂流)',
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
                wind: [0.0, 0.0, 0.0],
                windDesc: '0.0 m/s (室內無風風洞)',
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
                wind: [1.2, 0.0, 0.0],
                windDesc: '1.2 m/s (夜間微風)',
                showThermalHud: true,
                droneSpotlight: true,
                gridColor1: 0x6366f1,
                gridColor2: 0x1e1b4b
            }}
        }};

        let activeEnvKey = 'offshore_wind';
        let activeObstacles = [];
        let currentWind = [4.5, 0.8, 0.0];

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

            // 2. Update Active Collisions (Base Obstacles + Active Environment Obstacles)
            activeObstacles = baseObstacleMeshes.concat(envObstacles[envKey]);

            // 3. Update Sky, Fog, and Grid
            scene.background = new THREE.Color(cfg.bg);
            scene.fog.color = new THREE.Color(cfg.fogColor);
            scene.fog.density = cfg.fogDensity;

            if (currentGrid) {{
                scene.remove(currentGrid);
                currentGrid.geometry.dispose();
                currentGrid = new THREE.GridHelper(50, 50, cfg.gridColor1, cfg.gridColor2);
                scene.add(currentGrid);
            }}

            // 4. Update Lighting System
            ambientLight.color.setHex(cfg.ambientColor);
            ambientLight.intensity = cfg.ambientIntensity;
            sunLight.color.setHex(cfg.sunColor);
            sunLight.intensity = cfg.sunIntensity;
            sunLight.position.set(cfg.sunPos[0], cfg.sunPos[1], cfg.sunPos[2]);

            // 5. Update Drone Spotlight
            droneSpotlight.intensity = cfg.droneSpotlight ? 3.5 : 0.0;

            // 6. Update Wind Simulation
            currentWind = cfg.wind;
            const windEl = document.getElementById('st-wind');
            if (windEl) {{
                windEl.innerText = cfg.windDesc;
            }}

            // 7. Update HUD Badges & Thermal Overlay
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

        // 5. Dynamic Crash & Structural Damage Simulation System
        let droneStructuralIntegrity = 100;
        let damagedPartsHistory = [];
        let collisionCooldown = 0;
        const CRASH_SPEED_THRESHOLD = 0.95; // m/s threshold for structural damage
        const activeSparks = [];
        const activeDebris = [];
        let cameraShakeTimer = 0;
        let cameraShakeIntensity = 0;

        function showToast(msg) {{
            const toast = document.getElementById('toast-notice');
            if (toast) {{
                toast.innerText = msg;
                toast.style.display = 'block';
                setTimeout(() => {{ toast.style.display = 'none'; }}, 2500);
            }}
        }}

        function triggerDamageFX(impactPos, impactNormal, impactSpeed) {{
            // A. High-temperature Sparks Emitter
            const sparkCount = Math.min(50, Math.floor(20 + impactSpeed * 8));
            const sparkGeo = new THREE.BufferGeometry();
            const sparkPositions = new Float32Array(sparkCount * 3);
            const sparkVelocities = [];

            for (let i = 0; i < sparkCount; i++) {{
                sparkPositions[i * 3] = impactPos.x;
                sparkPositions[i * 3 + 1] = impactPos.y;
                sparkPositions[i * 3 + 2] = impactPos.z;

                const spread = 2.0 + Math.random() * 3.5;
                const v = new THREE.Vector3(
                    (Math.random() - 0.5) * spread + (impactNormal ? impactNormal.x * 2.0 : 0),
                    Math.random() * spread * 0.9 + 1.2,
                    (Math.random() - 0.5) * spread + (impactNormal ? impactNormal.z * 2.0 : 0)
                );
                sparkVelocities.push(v);
            }}
            sparkGeo.setAttribute('position', new THREE.BufferAttribute(sparkPositions, 3));

            const sparkMat = new THREE.PointsMaterial({{
                color: 0xffaa00,
                size: 0.05,
                transparent: true,
                opacity: 1.0,
                blending: THREE.AdditiveBlending
            }});
            const sparkPoints = new THREE.Points(sparkGeo, sparkMat);
            scene.add(sparkPoints);

            activeSparks.push({{
                points: sparkPoints,
                geo: sparkGeo,
                velocities: sparkVelocities,
                life: 1.0,
                decay: 2.0
            }});

            // B. Carbon Fiber Fracture Shards / Debris
            const debrisCount = Math.min(8, Math.floor(4 + impactSpeed * 2));
            const debrisMat = new THREE.MeshStandardMaterial({{ color: 0x18181b, roughness: 0.95 }});
            for (let i = 0; i < debrisCount; i++) {{
                const dGeo = new THREE.BoxGeometry(0.02 + Math.random() * 0.03, 0.008, 0.02 + Math.random() * 0.02);
                const dMesh = new THREE.Mesh(dGeo, debrisMat);
                dMesh.position.copy(impactPos);
                dMesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, 0);
                scene.add(dMesh);

                activeDebris.push({{
                    mesh: dMesh,
                    velocity: new THREE.Vector3(
                        (Math.random() - 0.5) * 3.0,
                        Math.random() * 2.5 + 0.8,
                        (Math.random() - 0.5) * 3.0
                    ),
                    rotVel: new THREE.Vector3(Math.random() * 10, Math.random() * 10, Math.random() * 10),
                    life: 1.0,
                    decay: 0.6
                }});
            }}

            // C. Screen / Camera Shake Impact
            cameraShakeTimer = 0.35;
            cameraShakeIntensity = Math.min(0.28, 0.08 + impactSpeed * 0.04);
        }}

        function applyStructuralDamage(impactPos, impactSpeed, hitObjectName) {{
            // Find closest arm to impact position
            let targetArm = null;
            let minDist = Infinity;
            droneArmComponents.forEach(arm => {{
                const armWorldPos = new THREE.Vector3(arm.x, 0.02, arm.z).applyMatrix4(drone.matrixWorld);
                const d = armWorldPos.distanceTo(impactPos);
                if (d < minDist) {{
                    minDist = d;
                    targetArm = arm;
                }}
            }});

            // Calculate damage reduction based on kinetic energy
            const damagePct = Math.min(45, Math.max(16, Math.floor(impactSpeed * 11)));
            droneStructuralIntegrity = Math.max(0, droneStructuralIntegrity - damagePct);

            let damagedDesc = "";
            if (targetArm) {{
                // 1. Arm deformation & fracture
                targetArm.isArmBroken = true;
                targetArm.armMesh.rotation.x += (Math.random() > 0.5 ? 0.35 : -0.35);
                targetArm.armMesh.rotation.z += (Math.random() > 0.5 ? 0.28 : -0.28);
                targetArm.armMesh.material.color.setHex(0x1a0808); // charred / fractured carbon fiber
                targetArm.armMesh.material.roughness = 0.98;

                // 2. Propeller fracture
                targetArm.isPropBroken = true;
                targetArm.propMesh.scale.set(0.35, 1.0, 0.38); // Blade sheared in half!
                targetArm.propMesh.material.color.setHex(0xef4444);
                targetArm.propMesh.material.opacity = 0.9;
                if (propDisks[targetArm.index]) {{
                    propDisks[targetArm.index].broken = true;
                }}

                // 3. Motor dislodgement
                targetArm.isMotorDamaged = true;
                targetArm.motorMesh.rotation.z += 0.35;
                targetArm.motorMesh.material.color.setHex(0x7f1d1d);

                damagedDesc = '機臂 #' + (targetArm.index + 1) + ' 折損彎曲、旋翼 #' + (targetArm.index + 1) + ' 斷槳失衡';
                if (!damagedPartsHistory.includes(damagedDesc)) {{
                    damagedPartsHistory.push(damagedDesc);
                }}
            }} else {{
                // Body or landing damage
                bodyMesh.material.color.setHex(0x331010);
                damagedDesc = '機身結構/起落架 撞擊受損';
                if (!damagedPartsHistory.includes(damagedDesc)) {{
                    damagedPartsHistory.push(damagedDesc);
                }}
            }}

            // Trigger sparks, debris particles & camera shake
            const normal = drone.position.clone().sub(impactPos).normalize();
            triggerDamageFX(impactPos, normal, impactSpeed);

            // Update HUD & BOM
            updateDamageHUD(damagedDesc, hitObjectName);
        }}

        function updateDamageHUD(lastDamagedDesc, hitObjectName) {{
            const intEl = document.getElementById('st-integrity');
            const intBar = document.getElementById('st-integrity-bar');
            if (intEl && intBar) {{
                intEl.innerText = droneStructuralIntegrity + '% (' + (droneStructuralIntegrity > 75 ? '良好' : (droneStructuralIntegrity > 35 ? '中度受損' : (droneStructuralIntegrity > 0 ? '嚴重結構損壞' : '完全墜毀'))) + ')';
                intBar.style.width = droneStructuralIntegrity + '%';
                if (droneStructuralIntegrity > 70) {{
                    intEl.style.color = '#4ade80';
                    intBar.style.background = '#22c55e';
                }} else if (droneStructuralIntegrity > 35) {{
                    intEl.style.color = '#facc15';
                    intBar.style.background = '#eab308';
                }} else {{
                    intEl.style.color = '#f87171';
                    intBar.style.background = '#ef4444';
                }}
            }}

            // Damage components list panel
            const dmgPanel = document.getElementById('damage-panel');
            const dmgList = document.getElementById('damage-list');
            const dmgCount = document.getElementById('damage-count');
            if (dmgPanel && dmgList && dmgCount) {{
                dmgPanel.style.display = 'block';
                dmgCount.innerText = damagedPartsHistory.length + ' 處結構受損';
                dmgList.innerHTML = damagedPartsHistory.map(item => '<div>❌ ' + item + '</div>').join('');
            }}

            // Update BOM panel components status
            const brokenArms = droneArmComponents.filter(a => a.isArmBroken).length;
            const brokenProps = droneArmComponents.filter(a => a.isPropBroken).length;

            const bomHealth = document.getElementById('bom-meta-health');
            if (bomHealth) {{
                if (droneStructuralIntegrity > 70) {{
                    bomHealth.innerText = '● 局部輕微磨損';
                    bomHealth.style.color = '#facc15';
                }} else {{
                    bomHealth.innerText = '● 結構破損失衡 (Critical)';
                    bomHealth.style.color = '#ef4444';
                }}
            }}

            const bomTagFrame = document.getElementById('bom-tag-frame');
            if (bomTagFrame) {{
                if (brokenArms > 0) {{
                    bomTagFrame.innerText = '⚠️ ' + brokenArms + '處臂管斷裂';
                    bomTagFrame.style.color = '#ef4444';
                    bomTagFrame.style.background = 'rgba(239, 68, 68, 0.2)';
                    bomTagFrame.style.borderColor = 'rgba(239, 68, 68, 0.5)';
                }}
            }}

            const bomTagMotors = document.getElementById('bom-tag-motors');
            if (bomTagMotors) {{
                const intactMotors = numArms - brokenArms;
                bomTagMotors.innerText = intactMotors + '/' + numArms + ' 在線';
                if (intactMotors < numArms) {{
                    bomTagMotors.style.color = '#f87171';
                    bomTagMotors.style.background = 'rgba(239, 68, 68, 0.2)';
                }}
            }}

            const bomTagProps = document.getElementById('bom-tag-props');
            if (bomTagProps) {{
                if (brokenProps > 0) {{
                    bomTagProps.innerText = '❌ ' + brokenProps + '組斷裂折損';
                    bomTagProps.style.color = '#ef4444';
                    bomTagProps.style.background = 'rgba(239, 68, 68, 0.2)';
                }}
            }}

            const bomTwr = document.getElementById('bom-val-twr');
            if (bomTwr) {{
                const intactRatio = (numArms - brokenProps) / numArms;
                const newTwr = Math.max(0.2, (2.4 * intactRatio)).toFixed(1);
                bomTwr.innerText = newTwr + ' : 1';
                if (intactRatio < 0.6) bomTwr.style.color = '#ef4444';
            }}
        }}

        // --- 6. Flight Data Recorder & Experience Questionnaire System ---
        let isRecording = false;
        let recordingStartTime = 0;
        let recordingTimerId = null;
        let recordSampleCount = 0;
        let recordedFlightData = [];
        let flightCollisionsLog = [];
        let flightQuestionnaireHistory = [];
        let currentStepIndex = 0;
        let prevDronePosRec = new THREE.Vector3();
        let prevDroneRotRec = new THREE.Euler();

        function toggleRecording() {{
            if (!isRecording) {{
                startRecording();
            }} else {{
                stopRecording();
            }}
        }}

        function startRecording() {{
            isRecording = true;
            recordSampleCount = 0;
            currentStepIndex = 0;
            recordedFlightData = [];
            recordingStartTime = performance.now();
            prevDronePosRec.copy(drone.position);
            prevDroneRotRec.copy(drone.rotation);

            const badge = document.getElementById('rec-status-badge');
            const txt = document.getElementById('rec-status-text');
            const btnToggle = document.getElementById('btn-rec-toggle');

            if (badge) badge.classList.add('recording');
            if (txt) txt.innerText = '🔴 錄製中 REC';
            if (btnToggle) {{
                btnToggle.innerText = '⏹️ 停止錄製 (G)';
                btnToggle.className = 'btn-action btn-rec-stop';
            }}

            showToast('🔴 飛航遙測與操作示範資料錄製已啟動！(2Hz 採樣)');

            if (recordingTimerId) clearInterval(recordingTimerId);
            // 2Hz sampling rate (500ms interval) for lightweight trajectory logging
            recordingTimerId = setInterval(sampleRecorderStep, 500);
        }}

        function stopRecording() {{
            if (!isRecording) return;
            isRecording = false;
            if (recordingTimerId) {{
                clearInterval(recordingTimerId);
                recordingTimerId = null;
            }}

            const badge = document.getElementById('rec-status-badge');
            const txt = document.getElementById('rec-status-text');
            const btnToggle = document.getElementById('btn-rec-toggle');

            if (badge) badge.classList.remove('recording');
            if (txt) txt.innerText = '待命 IDLE';
            if (btnToggle) {{
                btnToggle.innerText = '🔴 開始錄製 (G)';
                btnToggle.className = 'btn-action btn-rec-start';
            }}

            // 停止錄製時，直接靜默自動保存到本地儲存庫，無需手動下載彈窗
            if (recordedFlightData.length > 0) {{
                saveFlightData();
                showToast('⏹️ 錄製完成！共採集 ' + recordedFlightData.length + ' 筆樣本 (2Hz)，已直接自動保存至訓練集。');
            }} else {{
                showToast('⏹️ 停止錄製（無有效飛行樣本）');
            }}
        }}

        function sampleRecorderStep() {{
            if (!isRecording) return;

            const now = performance.now();
            const elapsedSec = (now - recordingStartTime) / 1000.0;
            const minutes = Math.floor(elapsedSec / 60);
            const seconds = (elapsedSec % 60).toFixed(1);
            const timeStr = String(minutes).padStart(2, '0') + ':' + (seconds < 10 ? '0' : '') + seconds;

            const timeEl = document.getElementById('rec-time');
            const samplesEl = document.getElementById('rec-samples');
            if (timeEl) timeEl.innerText = timeStr;
            if (samplesEl) samplesEl.innerText = recordSampleCount;

            // Compute angular velocity approximations (wx, wy, wz) rad/s (dt = 0.5s for 2Hz)
            const dt = 0.5;
            const wx = Number(((drone.rotation.x - prevDroneRotRec.x) / dt).toFixed(4));
            const wy = Number(((drone.rotation.y - prevDroneRotRec.y) / dt).toFixed(4));
            const wz = Number(((drone.rotation.z - prevDroneRotRec.z) / dt).toFixed(4));
            prevDroneRotRec.copy(drone.rotation);

            // User Control Actions (Normalized command signals)
            let pitch_cmd = 0.0;
            let roll_cmd = 0.0;
            let climb_cmd = 0.0;
            let yaw_cmd = 0.0;

            if (keys['KeyW']) pitch_cmd += 1.0;
            if (keys['KeyS']) pitch_cmd -= 1.0;
            if (keys['KeyA']) roll_cmd -= 1.0;
            if (keys['KeyD']) roll_cmd += 1.0;
            if (keys['ArrowUp']) climb_cmd += 1.0;
            if (keys['ArrowDown']) climb_cmd -= 1.0;
            if (keys['ArrowLeft']) yaw_cmd -= 1.0;
            if (keys['ArrowRight']) yaw_cmd += 1.0;

            const sample = {{
                step: currentStepIndex++,
                timestamp: Number(new Date().toISOString().replace('T', ' ').replace('Z', '').split('.')[0] + '.' + String(Math.floor((now % 1000))).padStart(3, '0')),
                iso_time: new Date().toISOString(),
                state: {{
                    position: [Number(drone.position.x.toFixed(4)), Number(drone.position.y.toFixed(4)), Number(drone.position.z.toFixed(4))],
                    linear_velocity: [Number(velocity.x.toFixed(4)), Number(velocity.y.toFixed(4)), Number(velocity.z.toFixed(4))],
                    attitude_rad: [Number(pitch.toFixed(4)), Number(roll.toFixed(4)), Number(yaw.toFixed(4))],
                    attitude_deg: [Number((pitch * 180 / Math.PI).toFixed(2)), Number((roll * 180 / Math.PI).toFixed(2)), Number((yaw * 180 / Math.PI).toFixed(2))],
                    angular_velocity: [wx, wy, wz],
                    integrity: Number(droneStructuralIntegrity.toFixed(1)),
                    battery_voltage: Number(batteryVoltage.toFixed(2)),
                    damaged_parts: [...damagedPartsHistory]
                }},
                action: {{
                    pitch_cmd: pitch_cmd,
                    roll_cmd: roll_cmd,
                    yaw_cmd: yaw_cmd,
                    climb_cmd: climb_cmd,
                    hover_active: !!keys['Space'],
                    raw_keys: Object.keys(keys).filter(k => keys[k])
                }},
                environment: {{
                    environment_id: activeEnvKey,
                    wind_velocity: [Number(currentWind[0].toFixed(2)), Number(currentWind[1].toFixed(2)), Number(currentWind[2].toFixed(2))],
                    collision_event: activeCollisionThisStep ? {{
                        hit_object: activeCollisionThisStep.object,
                        impact_speed: Number(activeCollisionThisStep.speed.toFixed(2)),
                        impact_point: [
                            Number(activeCollisionThisStep.point.x.toFixed(3)),
                            Number(activeCollisionThisStep.point.y.toFixed(3)),
                            Number(activeCollisionThisStep.point.z.toFixed(3))
                        ]
                    }} : null
                }}
            }};

            recordedFlightData.push(sample);
            recordSampleCount++;
            activeCollisionThisStep = null; // Clear latch after sampling
        }}

        let activeCollisionThisStep = null;

        function saveFlightData() {{
            if (recordedFlightData.length === 0) return null;

            const timestampStr = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
            const fileNameBase = 'flight_training_data_' + timestampStr;

            // 1. Prepare JSON format (Full Dataset with Metadata, 2Hz Sampling)
            const exportPayload = {{
                dataset_name: fileNameBase,
                version: "1.0.0",
                created_at: new Date().toISOString(),
                environment_id: activeEnvKey,
                total_samples: recordedFlightData.length,
                sampling_rate_hz: 2,
                drone_spec: {{
                    num_arms: numArms,
                    arm_length_m: armLength,
                    aircraft_type: isVTOL ? 'vtol_tilt_rotor' : 'multirotor'
                }},
                pilot_questionnaires: flightQuestionnaireHistory,
                trajectory: recordedFlightData
            }};

            // 2. Prepare JSONL format (One sample per line)
            const jsonlLines = recordedFlightData.map(step => JSON.stringify(step)).join('\\n');

            // 3. 直接靜默自動存檔寫入 LocalStorage，無需手動下載彈窗
            try {{
                localStorage.setItem(fileNameBase, JSON.stringify(exportPayload));
                localStorage.setItem('flight_training_data_latest', JSON.stringify(exportPayload));
                localStorage.setItem('flight_training_data_latest_jsonl', jsonlLines);
                console.log('[FlightDataRecorder] Direct auto-save to localStorage complete:', fileNameBase);
            }} catch (e) {{
                console.warn('[FlightDataRecorder] LocalStorage auto-save warning:', e);
            }}

            // 4. 嘗試背景呼叫後端 API 靜默保存 (若環境有支援)
            try {{
                fetch('/api/save_training_dataset', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ filename: fileNameBase, json_data: exportPayload, jsonl_data: jsonlLines }})
                }}).catch(() => {{}});
            }} catch(e) {{}}

            return exportPayload;
        }}

        // 提供相容方法名稱
        function autoSaveFlightData() {{
            return saveFlightData();
        }}
        function exportFlightData() {{
            return saveFlightData();
        }}

        // --- Questionnaire Dialog Handling ---
        function promptResetExperience() {{
            // Pause any ongoing key presses while modal is opened
            Object.keys(keys).forEach(k => keys[k] = false);

            const overlay = document.getElementById('reset-modal-overlay');
            if (overlay) {{
                overlay.style.display = 'flex';
                const notesEl = document.getElementById('modal-notes');
                if (notesEl) {{
                    notesEl.focus();
                }}
            }} else {{
                repairAndResetDrone();
            }}
        }}

        function closeResetModal(doReset = true) {{
            const overlay = document.getElementById('reset-modal-overlay');
            if (overlay) overlay.style.display = 'none';
            if (doReset) repairAndResetDrone();
        }}

        function confirmResetWithFeedback() {{
            const notesEl = document.getElementById('modal-notes');
            const feedbackText = notesEl ? notesEl.value.trim() : '';

            const feedbackEntry = {{
                timestamp: new Date().toISOString(),
                feedback: feedbackText,
                notes: feedbackText,
                final_integrity: droneStructuralIntegrity,
                final_position: [Number(drone.position.x.toFixed(3)), Number(drone.position.y.toFixed(3)), Number(drone.position.z.toFixed(3))],
                damaged_components: [...damagedPartsHistory]
            }};

            flightQuestionnaireHistory.push(feedbackEntry);
            if (isRecording) {{
                // Latch questionnaire into flight recorder as an event marker
                recordedFlightData.push({{
                    step: currentStepIndex++,
                    timestamp: performance.now(),
                    event_type: "pilot_feedback",
                    data: feedbackEntry
                }});
            }}

            if (notesEl) notesEl.value = '';
            closeResetModal(true);
            showToast('💾 飛行經驗回饋已儲存，機身維修重置完畢！');
        }}

        function repairAndResetDrone() {{
            droneStructuralIntegrity = 100;
            damagedPartsHistory = [];
            collisionCooldown = 0;

            // 1. Reset all arms, motors, propellers
            droneArmComponents.forEach(arm => {{
                arm.isArmBroken = false;
                arm.isPropBroken = false;
                arm.isMotorDamaged = false;

                arm.armMesh.rotation.set(arm.origArmRot.x, arm.origArmRot.y, arm.origArmRot.z);
                arm.armMesh.position.set(arm.origArmPos.x, arm.origArmPos.y, arm.origArmPos.z);
                arm.armMesh.material.color.setHex(0x0f172a);
                arm.armMesh.material.roughness = 0.4;

                arm.motorMesh.rotation.set(arm.origMotorRot.x, arm.origMotorRot.y, arm.origMotorRot.z);
                arm.motorMesh.position.set(arm.origMotorPos.x, arm.origMotorPos.y, arm.origMotorPos.z);
                arm.motorMesh.material.color.setHex(0xef4444);

                arm.propMesh.scale.set(1, 1, 1);
                arm.propMesh.material.color.setHex(0x38bdf8);
                arm.propMesh.material.opacity = 0.5;

                if (propDisks[arm.index]) {{
                    propDisks[arm.index].broken = false;
                }}
            }});

            // Reset main body
            bodyMesh.material.color.setHex(0x1e293b);
            bodyMesh.material.roughness = 0.2;

            // 2. Clear all active particles
            activeSparks.forEach(sp => {{
                scene.remove(sp.points);
                sp.geo.dispose();
                sp.points.material.dispose();
            }});
            activeSparks.length = 0;

            activeDebris.forEach(db => {{
                scene.remove(db.mesh);
                db.mesh.geometry.dispose();
                db.mesh.material.dispose();
            }});
            activeDebris.length = 0;

            cameraShakeTimer = 0;

            // 3. Reset Drone Flight State
            drone.position.set(0, 0.05, 0);
            velocity.set(0, 0, 0);
            pitch = 0; roll = 0; yaw = 0;
            rotationSpeed = 0;
            batteryVoltage = 11.80;

            // 4. Reset HUD & Alerts
            const alertEl = document.getElementById('collision-alert');
            if (alertEl) alertEl.style.display = 'none';

            const dmgPanel = document.getElementById('damage-panel');
            if (dmgPanel) dmgPanel.style.display = 'none';

            const intEl = document.getElementById('st-integrity');
            const intBar = document.getElementById('st-integrity-bar');
            if (intEl && intBar) {{
                intEl.innerText = '100% (完好)';
                intEl.style.color = '#4ade80';
                intBar.style.width = '100%';
                intBar.style.background = '#22c55e';
            }}

            const modeEl = document.getElementById('st-mode');
            if (modeEl) {{
                modeEl.innerText = 'OFFBOARD - ARM';
                modeEl.style.color = '#76ff03';
            }}

            // 5. Reset BOM
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
                bomTagFrame.style.borderColor = 'rgba(34, 197, 94, 0.3)';
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

            showToast('✨ 機身結構已 100% 快速修復就緒！');
        }}

        function simulateTestCrash() {{
            const testPos = new THREE.Vector3(armLength * 0.9, 0.05, 0.1).applyMatrix4(drone.matrixWorld);
            applyStructuralDamage(testPos, 3.2, '結構碰撞測試');
            velocity.x = -1.2;
            velocity.y = 0.8;
        }}

        // 7. Physics & Flight Dynamics (Harmonized 6-DOF Physics)
        const keys = {{}};
        window.addEventListener('keydown', (e) => {{
            // Ignore flight keys if modal questionnaire is open
            const overlay = document.getElementById('reset-modal-overlay');
            if (overlay && overlay.style.display === 'flex') {{
                if (e.code === 'Escape') closeResetModal(false);
                return;
            }}

            keys[e.code] = true;
            if (e.code === 'KeyR') promptResetExperience();
            if (e.code === 'KeyG') toggleRecording();
        }});
        window.addEventListener('keyup', (e) => keys[e.code] = false);

        let velocity = new THREE.Vector3(0, 0, 0);
        let rotationSpeed = 0;
        let pitch = 0, roll = 0, yaw = 0;
        let batteryVoltage = 11.80;
        const clock = new THREE.Clock();

        function updatePhysics() {{
            // Keyboard Controls
            let throttleAcc = 0;
            let targetPitch = 0, targetRoll = 0;

            if (keys['ArrowUp']) throttleAcc += 12.0;       // Lift / Up
            if (keys['ArrowDown']) throttleAcc -= 8.0;       // Descend
            if (keys['KeyW']) targetPitch = -0.30;           // Pitch Forward
            if (keys['KeyS']) targetPitch = 0.30;            // Pitch Backward
            if (keys['KeyA']) targetRoll = 0.30;             // Roll Left
            if (keys['KeyD']) targetRoll = -0.30;            // Roll Right
            if (keys['ArrowLeft']) rotationSpeed = 0.04;     // Yaw Left
            else if (keys['ArrowRight']) rotationSpeed = -0.04; // Yaw Right
            else rotationSpeed = 0;

            // Damage impact on flight physics
            const brokenCount = droneArmComponents.filter(a => a.isArmBroken || a.isPropBroken).length;
            const intactRatio = (numArms - brokenCount) / numArms;
            const isCatastrophic = droneStructuralIntegrity <= 20 || intactRatio <= 0.5;

            if (isCatastrophic) {{
                // Loss of control: spin and tumble
                rotationSpeed += 0.15;
                roll += 0.09;
                pitch += 0.07;
                throttleAcc = -5.0; // loss of thrust
                const modeEl = document.getElementById('st-mode');
                if (modeEl) {{
                    modeEl.innerText = '❌ 結構損壞 - 失控翻滾墜毀';
                    modeEl.style.color = '#ef4444';
                }}
            }} else if (brokenCount > 0) {{
                // Mechanical imbalance torque from broken arms
                droneArmComponents.forEach(arm => {{
                    if (arm.isPropBroken || arm.isArmBroken) {{
                        targetRoll -= (arm.x / armLength) * 0.28;
                        targetPitch += (arm.z / armLength) * 0.28;
                    }}
                }});
                // Violent tremor / vibration
                const tremor = brokenCount * 0.035;
                pitch += (Math.random() - 0.5) * tremor;
                roll += (Math.random() - 0.5) * tremor;
                const modeEl = document.getElementById('st-mode');
                if (modeEl) {{
                    modeEl.innerText = '⚠️ 推力失衡 - 機體震顫 (DEGRADED)';
                    modeEl.style.color = '#facc15';
                }}
            }}

            if (keys['Space'] && !isCatastrophic) {{ // Hover mode
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

            // Thrust Vectoring & Gravity (9.81 m/s^2) with damage degradation
            const gravity = 9.81;
            const nominalLift = (drone.position.y > 0.05 ? 9.81 : 0) + throttleAcc;
            const effectiveLift = nominalLift * (0.15 + 0.85 * intactRatio);

            velocity.y += (effectiveLift - gravity) * 0.016;

            // Thrust Vector Calculation
            const forwardZ = Math.sin(pitch) * Math.cos(yaw) - Math.sin(roll) * Math.sin(yaw);
            const forwardX = Math.sin(pitch) * Math.sin(yaw) + Math.sin(-roll) * Math.cos(yaw);

            const windX = currentWind[0];
            const thrustMultiplier = 15.0 * (0.3 + 0.7 * intactRatio);
            velocity.x += (forwardX * thrustMultiplier + windX * 0.2) * 0.016;
            velocity.z += (forwardZ * thrustMultiplier) * 0.016;

            // Air Drag Damping
            velocity.x *= 0.98;
            velocity.z *= 0.98;
            velocity.y *= 0.95;

            // Update Drone Position & Smooth Camera Tracking
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
            propDisks.forEach(p => {{
                if (!p.broken) {{
                    p.mesh.rotation.y += 0.4 * p.dir;
                }} else {{
                    p.mesh.rotation.y += 0.05 * p.dir; // Stalled/wobbling broken prop
                }}
            }});

            // Collision Detection with Active Environment Obstacles & Stress Reactions
            const droneBox = new THREE.Box3().setFromObject(drone);
            let colliding = false;
            const currentSpeed = Math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2);

            if (collisionCooldown > 0) collisionCooldown -= 0.016;

            activeObstacles.forEach(obs => {{
                if (droneBox.intersectsBox(obs.box)) {{
                    colliding = true;
                    if (collisionCooldown <= 0 && currentSpeed >= CRASH_SPEED_THRESHOLD) {{
                        collisionCooldown = 0.4;
                        const contactPt = new THREE.Vector3();
                        obs.box.clampPoint(drone.position, contactPt);
                        activeCollisionThisStep = {{
                            object: '剛體障礙物',
                            speed: currentSpeed,
                            point: contactPt.clone()
                        }};
                        flightCollisionsLog.push({{
                            step: currentStepIndex,
                            timestamp: performance.now(),
                            ...activeCollisionThisStep
                        }});
                        applyStructuralDamage(contactPt, currentSpeed, '剛體障礙物');
                    }}
                    velocity.negate().multiplyScalar(0.45); // Bouncing physics
                }}
            }});

            // Hard ground crash check
            if (drone.position.y <= 0.06 && Math.abs(velocity.y) > 2.0 && collisionCooldown <= 0) {{
                colliding = true;
                collisionCooldown = 0.5;
                const groundPt = drone.position.clone();
                groundPt.y = 0.02;
                activeCollisionThisStep = {{
                    object: '地面猛烈觸地',
                    speed: Math.abs(velocity.y),
                    point: groundPt.clone()
                }};
                flightCollisionsLog.push({{
                    step: currentStepIndex,
                    timestamp: performance.now(),
                    ...activeCollisionThisStep
                }});
                applyStructuralDamage(groundPt, Math.abs(velocity.y), '地面猛烈觸地');
                velocity.y = Math.abs(velocity.y) * 0.35;
            }}

            const alertEl = document.getElementById('collision-alert');
            if (alertEl) {{
                alertEl.style.display = colliding ? 'block' : 'none';
            }}

            // Update HUD Telemetry
            const speed = Math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2).toFixed(2);
            document.getElementById('st-alt').innerText = drone.position.y.toFixed(2) + ' m';
            document.getElementById('st-spd').innerText = speed + ' m/s';
            if (drone.position.y > 0.1) {{
                batteryVoltage = Math.max(10.2, batteryVoltage - 0.0003);
                document.getElementById('st-bat').innerText = batteryVoltage.toFixed(2) + ' V';
            }}
        }}

        // 7. Animation Loop with Real-time Environment FX & Dynamic Particle Lifecycle
        function animate() {{
            requestAnimationFrame(animate);
            const elapsedTime = clock.getElapsedTime();

            // Scenario-specific dynamic animations
            if (activeEnvKey === 'offshore_wind') {{
                turbineRotors.forEach(r => r.rotation.z += 0.025);
                if (oceanGeo && oceanGeo.attributes.position) {{
                    const pos = oceanGeo.attributes.position;
                    const t = elapsedTime * 1.8;
                    for (let i = 0; i < pos.count; i++) {{
                        const u = pos.getX(i);
                        const v = pos.getY(i);
                        pos.setZ(i, Math.sin(u * 0.15 + t) * 0.25 + Math.cos(v * 0.15 + t * 0.8) * 0.18);
                    }}
                    pos.needsUpdate = true;
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

            // Camera Shake on Heavy Impact
            if (cameraShakeTimer > 0) {{
                cameraShakeTimer -= 0.016;
                const shakeX = (Math.random() - 0.5) * cameraShakeIntensity;
                const shakeY = (Math.random() - 0.5) * cameraShakeIntensity;
                camera.position.x += shakeX;
                camera.position.y += shakeY;
            }}

            // Update Sparks Particle Life & Physics
            const dt = 0.016;
            for (let i = activeSparks.length - 1; i >= 0; i--) {{
                const sp = activeSparks[i];
                sp.life -= dt * sp.decay;
                if (sp.life <= 0) {{
                    scene.remove(sp.points);
                    sp.geo.dispose();
                    sp.points.material.dispose();
                    activeSparks.splice(i, 1);
                    continue;
                }}
                sp.points.material.opacity = Math.max(0, sp.life);
                const posArr = sp.geo.attributes.position.array;
                for (let j = 0; j < sp.velocities.length; j++) {{
                    const v = sp.velocities[j];
                    v.y -= 9.8 * dt; // gravity
                    posArr[j * 3] += v.x * dt;
                    posArr[j * 3 + 1] += v.y * dt;
                    posArr[j * 3 + 2] += v.z * dt;
                    if (posArr[j * 3 + 1] < 0.02) {{
                        posArr[j * 3 + 1] = 0.02;
                        v.y *= -0.3; // ground bounce
                    }}
                }}
                sp.geo.attributes.position.needsUpdate = true;
            }}

            // Update Carbon Fiber Debris Physics
            for (let i = activeDebris.length - 1; i >= 0; i--) {{
                const db = activeDebris[i];
                db.life -= dt * db.decay;
                if (db.life <= 0) {{
                    scene.remove(db.mesh);
                    db.mesh.geometry.dispose();
                    db.mesh.material.dispose();
                    activeDebris.splice(i, 1);
                    continue;
                }}
                db.velocity.y -= 9.8 * dt;
                db.mesh.position.addScaledVector(db.velocity, dt);
                db.mesh.rotation.x += db.rotVel.x * dt;
                db.mesh.rotation.y += db.rotVel.y * dt;
                if (db.mesh.position.y < 0.02) {{
                    db.mesh.position.y = 0.02;
                    db.velocity.y *= -0.4;
                    db.velocity.x *= 0.7;
                    db.velocity.z *= 0.7;
                }}
            }}

            updatePhysics();
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
