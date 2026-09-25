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

        # Privileged Student Multi-Stage Neural Policy (FEAT-M2.5.2)
        stages_path = self.output_dir / "neural_models" / "student_policy_stages.json"
        if stages_path.exists():
            try:
                with open(stages_path, "r", encoding="utf-8") as f:
                    stages_data = json.load(f)
                stages_json_str = json.dumps(stages_data.get("stages", {}))
            except Exception:
                stages_json_str = "{}"
        else:
            stages_json_str = "{}"

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
            min-width: 290px; max-height: calc(100vh - 40px); overflow-y: auto; box-shadow: 0 8px 32px rgba(0,0,0,0.65); z-index: 100;
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

        /* LiDAR & Proximity Sensor HUD Styles */
        .sensor-section {{
            margin-top: 10px; padding: 10px 12px;
            background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(56, 189, 248, 0.35);
            border-radius: 10px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        }}
        .sensor-header {{
            display: flex; align-items: center; justify-content: space-between;
            font-size: 11px; font-weight: 700; color: #38bdf8; margin-bottom: 6px;
        }}
        .sensor-indicator {{
            display: inline-flex; align-items: center; gap: 5px; font-size: 10px; font-weight: bold;
            padding: 1px 6px; border-radius: 4px; background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.35);
        }}
        .sensor-dist-val {{
            font-size: 15px; font-weight: bold; font-family: monospace; color: #4ade80;
        }}
        .sensor-bar-wrap {{
            width: 100%; height: 5px; background: rgba(255, 255, 255, 0.1); border-radius: 3px; overflow: hidden; margin-top: 6px;
        }}
        .sensor-bar-fill {{
            height: 100%; width: 0%; background: #22c55e; transition: width 0.08s ease, background 0.15s ease;
        }}

        /* AI Autopilot HUD Styles */
        .ai-autopilot-section {{
            margin-top: 10px; padding: 10px 12px;
            background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(139, 92, 246, 0.4);
            border-radius: 10px; box-shadow: 0 4px 15px rgba(124, 58, 237, 0.2);
        }}
        .ai-header {{
            display: flex; align-items: center; justify-content: space-between;
            font-size: 11px; font-weight: 700; color: #a78bfa; margin-bottom: 6px;
        }}
        .ai-indicator {{
            display: inline-flex; align-items: center; gap: 5px; font-size: 10px; font-weight: bold;
            padding: 2px 7px; border-radius: 10px; background: rgba(148, 163, 184, 0.15); color: #94a3b8;
        }}
        .ai-indicator.active {{
            background: rgba(139, 92, 246, 0.25); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.5);
        }}
        .ai-dot {{
            width: 7px; height: 7px; border-radius: 50%; background: #94a3b8;
        }}
        .ai-indicator.active .ai-dot {{
            background: #a855f7; animation: blinkAi 0.7s infinite alternate;
        }}
        @keyframes blinkAi {{ 0% {{ opacity: 0.3; transform: scale(0.85); }} 100% {{ opacity: 1; transform: scale(1.25); }} }}
        .btn-ai-start {{
            background: linear-gradient(135deg, #7c3aed, #6d28d9); border: 1px solid #a78bfa; color: #fff;
            box-shadow: 0 2px 8px rgba(124, 58, 237, 0.4);
        }}
        .btn-ai-start:hover {{
            background: linear-gradient(135deg, #8b5cf6, #7c3aed); box-shadow: 0 0 12px rgba(167, 139, 250, 0.6);
        }}
        .btn-ai-stop {{
            background: rgba(245, 158, 11, 0.2); border: 1px solid rgba(245, 158, 11, 0.5); color: #fbbf24;
        }}
        /* Shared Autonomy Copilot HUD Styles (Milestone M2.6) */
        .copilot-section {{
            margin-top: 10px; padding: 10px 12px;
            background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(14, 165, 233, 0.4);
            border-radius: 10px;
        }}
        .copilot-header {{
            display: flex; align-items: center; justify-content: space-between;
            font-size: 11px; font-weight: 700; color: #38bdf8; margin-bottom: 5px;
        }}
        .copilot-indicator {{
            display: inline-flex; align-items: center; gap: 4px; font-size: 10px; font-weight: bold;
            padding: 2px 7px; border-radius: 10px; font-family: monospace;
        }}
        .copilot-standby {{
            background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.35);
        }}
        .copilot-warning {{
            background: rgba(250, 204, 21, 0.2); color: #facc15; border: 1px solid rgba(250, 204, 21, 0.5);
            animation: blinkCopilot 0.6s infinite alternate;
        }}
        .copilot-deflect {{
            background: rgba(244, 63, 94, 0.25); color: #f43f5e; border: 1px solid rgba(244, 63, 94, 0.6);
            animation: blinkCopilot 0.3s infinite alternate;
        }}
        @keyframes blinkCopilot {{ 0% {{ opacity: 0.5; }} 100% {{ opacity: 1; }} }}
        .btn-copilot-active {{
            background: linear-gradient(135deg, #0284c7, #0369a1); border: 1px solid #38bdf8; color: #fff;
            box-shadow: 0 2px 8px rgba(2, 132, 199, 0.4);
        }}
        .btn-copilot-active:hover {{
            background: linear-gradient(135deg, #0ea5e9, #0284c7); box-shadow: 0 0 12px rgba(56, 189, 248, 0.6);
        }}
        .btn-copilot-inactive {{
            background: rgba(100, 116, 139, 0.2); border: 1px solid rgba(100, 116, 139, 0.4); color: #94a3b8;
        }}
        .btn-copilot-inactive:hover {{
            background: rgba(100, 116, 139, 0.35); color: #e2e8f0;
        }}

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

        <!-- Rangefinder / LiDAR Proximity Radar HUD Panel -->
        <div class="sensor-section">
            <div class="sensor-header">
                <span>📡 機載測距雷達 (LiDAR/ToF)</span>
                <span id="sensor-status-badge" class="sensor-indicator">● 在線探測</span>
            </div>
            <div class="hud-row" style="margin-bottom: 2px; align-items: baseline;">
                <span style="color: #cbd5e1;">最近撞擊物:</span>
                <span id="st-nearest-dist" class="sensor-dist-val">-- m</span>
            </div>
            <div class="hud-row" style="font-size: 11px; margin-bottom: 2px;">
                <span style="color: #94a3b8;">目標: <span id="st-nearest-name" style="color:#f8fafc; font-weight:600;">--</span></span>
                <span style="color: #94a3b8;">方位: <span id="st-nearest-dir" style="color:#38bdf8; font-weight:600;">--</span></span>
            </div>
            <div class="sensor-bar-wrap">
                <div id="st-proximity-bar" class="sensor-bar-fill"></div>
            </div>
            <div id="st-proximity-alert" style="display:none; margin-top: 6px; font-size: 11px; text-align: center; color: #ff1744; font-weight: bold; animation: blink 0.4s infinite alternate; background: rgba(255, 23, 68, 0.15); padding: 4px; border-radius: 4px; border: 1px solid rgba(255, 23, 68, 0.4);">
                ⚠️ 近距碰撞預警！請拉開安全間距！
            </div>
        </div>

        <!-- Autonomous AI Flight Autopilot Section -->
        <div class="ai-autopilot-section">
            <div class="ai-header">
                <span>🤖 AI 自主飛行巡弋 (Autopilot)</span>
                <span id="ai-status-badge" class="ai-indicator"><span class="ai-dot"></span><span id="ai-status-text">手動 MANUAL</span></span>
            </div>
            <div class="hud-row" style="font-size: 11px; margin-top: 4px;">
                <span style="color:#94a3b8;">目標航點:</span>
                <span id="ai-target-gate" style="color:#38bdf8; font-weight:bold;">Gate #1</span>
            </div>
            <div class="hud-row" style="font-size: 11px; margin-top: 2px;">
                <span style="color:#94a3b8;">巡航圈數: <span id="ai-laps" style="color:#22c55e; font-weight:bold;">0 圈</span></span>
                <span style="color:#94a3b8;">決策信賴度: <span id="ai-confidence" style="color:#e0e7ff; font-weight:bold;">96.5%</span></span>
            </div>
            <div class="hud-row" style="font-size: 11px; margin-top: 2px;">
                <span style="color:#94a3b8;">累積獎勵分:</span>
                <span id="ai-reward" style="color:#fbbf24; font-weight:bold;">+0.0</span>
            </div>
            <div class="hud-row" style="font-size: 11px; margin-top: 4px; align-items: center;">
                <span style="color:#94a3b8;">🎓 學生策略歷程:</span>
                <span id="ai-stage-badge" style="color:#a855f7; font-weight:bold;">🏆 100% 精通</span>
            </div>
            <div style="display: flex; gap: 4px; margin-top: 4px;">
                <button id="btn-stage-0" class="btn-stage" style="flex:1; font-size:10px; padding:3px 2px; background:#1e293b; border:1px solid #475569; color:#94a3b8; border-radius:3px; cursor:pointer;" onclick="switchAIStage('stage_0_untrained')">🌱 0%初學</button>
                <button id="btn-stage-1" class="btn-stage" style="flex:1; font-size:10px; padding:3px 2px; background:#1e293b; border:1px solid #475569; color:#94a3b8; border-radius:3px; cursor:pointer;" onclick="switchAIStage('stage_1_half_trained')">🌿 40%中級</button>
                <button id="btn-stage-2" class="btn-stage" style="flex:1; font-size:10px; padding:3px 2px; background:#7c3aed; border:1px solid #a855f7; color:#fff; border-radius:3px; cursor:pointer; font-weight:bold;" onclick="switchAIStage('stage_2_mastered')">🏆 100%精通</button>
            </div>
            <div class="hud-btn-row" style="margin-top: 6px;">
                <button id="btn-ai-toggle" class="btn-action btn-ai-start" onclick="toggleAIAutopilot()">🤖 啟動 AI 自主飛行 (P)</button>
            </div>
            <div class="hud-btn-row" style="margin-top: 5px;">
                <button id="btn-test-obstacle" class="btn-action" style="background: linear-gradient(135deg, #dc2626, #b91c1c); border: 1px solid #ef4444; color: #fff; box-shadow: 0 2px 8px rgba(220, 38, 38, 0.4); font-size: 11px;" onclick="toggleTestObstacle()">🚨 插入突發紅色柱子 (避障實測) (O)</button>
            </div>
        </div>

        <!-- Shared Autonomy Copilot HUD Section (Milestone M2.6) -->
        <div class="copilot-section">
            <div class="copilot-header">
                <span>🛡️ AI 協同副駕駛 (Copilot)</span>
                <span id="copilot-status-badge" class="copilot-indicator copilot-standby">● STANDBY</span>
            </div>
            <div class="hud-row" style="font-size: 11px; margin-top: 4px;">
                <span style="color:#94a3b8;">防護狀態:</span>
                <span id="copilot-mode-text" style="color:#38bdf8; font-weight:bold;">待命守護 (STANDBY)</span>
            </div>
            <div class="hud-row" style="font-size: 11px; margin-top: 2px;">
                <span style="color:#94a3b8;">排斥干預強度: <span id="copilot-beta" style="color:#facc15; font-weight:bold;">0.0%</span></span>
                <span style="color:#94a3b8;">TTC 預警: <span id="copilot-ttc" style="color:#e0e7ff; font-weight:bold;">-- s</span></span>
            </div>
            <div class="hud-btn-row" style="margin-top: 6px;">
                <button id="btn-copilot-toggle" class="btn-action btn-copilot-active" onclick="toggleCopilot()">🛡️ 協同副駕駛已啟動 (C)</button>
            </div>
        </div>

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
                <span class="bom-badge">8 大關鍵核心零件 (含 LiDAR)</span>
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
                <div class="bom-item">
                    <div class="bom-item-icon">📡</div>
                    <div class="bom-item-info">
                        <div class="bom-item-name">測距感測器 (360° LiDAR / ToF)</div>
                        <div class="bom-item-spec">TFmini Plus / 8m 激光近距避障與即時測距雷達</div>
                    </div>
                    <div class="bom-item-tag">100Hz Active</div>
                </div>
            </div>
            <div class="bom-footer">
                <div>全備起飛重量: <span class="bom-stat">1295g</span></div>
                <div>推重比 (TWR): <span id="bom-val-twr" class="bom-stat">2.38 : 1</span></div>
            </div>
        </div>
    </div>

    <div id="control-panel">
        <div><span class="key">W</span> <span class="key">S</span> 俯仰 (長按衝刺/短點微調)</div>
        <div><span class="key">A</span> <span class="key">D</span> 翻滾 (長按衝刺/短點微調)</div>
        <div><span class="key">↑</span> <span class="key">↓</span> 油門 (爬升/降落)</div>
        <div><span class="key">Q</span> <span class="key">E</span> / <span class="key">←</span> <span class="key">→</span> 偏航轉向</div>
        <div><span class="key">Space</span> 自動懸停定高</div>
        <div><span class="key">G</span> 錄製/停止</div>
        <div><span class="key">R</span> 維修重置</div>
        <div><span class="key">P</span> AI 自主飛行/手動切換</div>
        <div><span class="key">C</span> AI 協同副駕駛 (防撞守護)</div>
        <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.15); font-size: 10.5px; color: #94a3b8; line-height: 1.4;">
            <span style="color:#ef4444; font-weight:bold;">🔴 左舷紅燈</span> ｜ <span style="color:#22c55e; font-weight:bold;">🟢 右舷綠燈</span><br>
            <span style="color:#f8fafc; font-weight:bold;">⚪ 機頭雙大燈</span> ｜ <span style="color:#f59e0b; font-weight:bold;">🟡 機尾頻閃</span>
        </div>
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

        const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 2000);
        camera.position.set(0, 3, 6);

        const renderer = new THREE.WebGLRenderer({{ antialias: true, logarithmicDepthBuffer: true }});
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

        let currentGrid = null;

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

        // 3D Virtual Bumper Halo (Milestone M2.6 Shared Autonomy Copilot)
        const haloRadius = Math.max(0.45, {arm_length} * 1.35);
        const haloGeo = new THREE.TorusGeometry(haloRadius, 0.02, 16, 64);
        haloGeo.rotateX(Math.PI / 2);
        const haloMat = new THREE.MeshBasicMaterial({{
            color: 0x00e5ff,
            transparent: true,
            opacity: 0.35,
            wireframe: false
        }});
        const copilotHalo = new THREE.Mesh(haloGeo, haloMat);
        copilotHalo.position.set(0, 0.05, 0);
        drone.add(copilotHalo);

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

            // Aviation Navigation Lights (ICAO / FAA Standard: Left/Port = RED, Right/Starboard = GREEN)
            const isLeftSide = (x < -0.01);
            const isRightSide = (x > 0.01);
            const navLightColor = isLeftSide ? 0xef4444 : (isRightSide ? 0x22c55e : (z < 0 ? 0xffffff : 0xf59e0b));
            const navLightEmissive = isLeftSide ? 0xff0022 : (isRightSide ? 0x00ff44 : (z < 0 ? 0xffffff : 0xf59e0b));

            const navLightGeo = new THREE.SphereGeometry(0.024, 16, 16);
            const navLightMat = new THREE.MeshStandardMaterial({{
                color: navLightColor,
                emissive: navLightEmissive,
                emissiveIntensity: 3.5,
                roughness: 0.1
            }});
            const navLightMesh = new THREE.Mesh(navLightGeo, navLightMat);
            navLightMesh.position.set(x * 1.08, 0.03, z * 1.08);
            drone.add(navLightMesh);

            const navPointLight = new THREE.PointLight(navLightEmissive, 0.75, 1.6);
            navPointLight.position.set(x * 1.08, 0.05, z * 1.08);
            drone.add(navPointLight);

            droneArmComponents.push({{
                index: i,
                angle: angle,
                x: x,
                z: z,
                armMesh: armMesh,
                motorMesh: motorMesh,
                propMesh: propMesh,
                navLightMesh: navLightMesh,
                navPointLight: navPointLight,
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

        // Forward Nose Orientation Headlights (Twin High-Power White LEDs)
        const noseHeadlightGeo = new THREE.SphereGeometry(0.018, 16, 16);
        const noseHeadlightMat = new THREE.MeshStandardMaterial({{
            color: 0xffffff,
            emissive: 0xffffff,
            emissiveIntensity: 4.5,
            roughness: 0.1
        }});
        const noseLightL = new THREE.Mesh(noseHeadlightGeo, noseHeadlightMat);
        noseLightL.position.set(-0.05, 0.02, -0.15);
        drone.add(noseLightL);

        const noseLightR = new THREE.Mesh(noseHeadlightGeo, noseHeadlightMat);
        noseLightR.position.set(0.05, 0.02, -0.15);
        drone.add(noseLightR);

        const noseBeam = new THREE.PointLight(0xffffff, 1.8, 4.0);
        noseBeam.position.set(0, 0.02, -0.18);
        drone.add(noseBeam);

        // Aft Tail Beacon (Amber Flashing Beacon)
        const tailBeaconGeo = new THREE.SphereGeometry(0.02, 16, 16);
        const tailBeaconMat = new THREE.MeshStandardMaterial({{
            color: 0xf59e0b,
            emissive: 0xf59e0b,
            emissiveIntensity: 3.5,
            roughness: 0.2
        }});
        const tailBeaconMesh = new THREE.Mesh(tailBeaconGeo, tailBeaconMat);
        tailBeaconMesh.position.set(0, 0.06, 0.13);
        drone.add(tailBeaconMesh);

        const tailBeaconLight = new THREE.PointLight(0xf59e0b, 1.0, 2.0);
        tailBeaconLight.position.set(0, 0.08, 0.13);
        drone.add(tailBeaconLight);

        // LiDAR Sensor Turret & Spinning Scan Ring
        const lidarGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.05);
        const lidarMat = new THREE.MeshStandardMaterial({{ color: 0x0f172a, metalness: 0.9, roughness: 0.2 }});
        const lidarMesh = new THREE.Mesh(lidarGeo, lidarMat);
        lidarMesh.position.set(0, 0.15, 0);
        drone.add(lidarMesh);

        const lidarRingGeo = new THREE.TorusGeometry(0.046, 0.007, 8, 24);
        const lidarRingMat = new THREE.MeshStandardMaterial({{
            color: 0x00e5ff,
            emissive: 0x00e5ff,
            emissiveIntensity: 3.0
        }});
        const lidarScanRing = new THREE.Mesh(lidarRingGeo, lidarRingMat);
        lidarScanRing.rotation.x = Math.PI / 2;
        lidarScanRing.position.set(0, 0.175, 0);
        drone.add(lidarScanRing);

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

        // 3D Laser Raycast Indicator & Obstacle Contact Reticle
        const laserRayGeo = new THREE.BufferGeometry();
        const laserPositions = new Float32Array(6);
        laserRayGeo.setAttribute('position', new THREE.BufferAttribute(laserPositions, 3));
        const laserRayMat = new THREE.LineBasicMaterial({{ color: 0x22c55e, transparent: true, opacity: 0.9, linewidth: 2 }});
        const laserRayLine = new THREE.Line(laserRayGeo, laserRayMat);
        laserRayLine.visible = false;
        scene.add(laserRayLine);

        const laserDotGeo = new THREE.SphereGeometry(0.055, 16, 16);
        const laserDotMat = new THREE.MeshBasicMaterial({{ color: 0x22c55e }});
        const laserDotMesh = new THREE.Mesh(laserDotGeo, laserDotMat);
        laserDotMesh.visible = false;
        scene.add(laserDotMesh);

        // 3D AI Autopilot Trajectory Guidance Corridor
        const trajGeo = new THREE.BufferGeometry();
        const trajPositions = new Float32Array(6);
        trajGeo.setAttribute('position', new THREE.BufferAttribute(trajPositions, 3));
        const trajMat = new THREE.LineBasicMaterial({{ color: 0x00e5ff, transparent: true, opacity: 0.95, linewidth: 4 }});
        const trajectoryLine = new THREE.Line(trajGeo, trajMat);
        trajectoryLine.visible = false;
        trajectoryLine.frustumCulled = false;
        scene.add(trajectoryLine);

        // AI Autopilot Waypoint Circuit Gates with 3D Orientation & Normal Vectors
        const aiGates = [
            {{ id: 1, x: 0.0, y: 3.2, z: -7.0, yaw: 0, nx: 0, nz: -1, label: 'Gate #1' }},
            {{ id: 2, x: 9.0, y: 4.5, z: 0.0, yaw: Math.PI / 2, nx: 1, nz: 0, label: 'Gate #2' }},
            {{ id: 3, x: 0.0, y: 6.0, z: 9.0, yaw: Math.PI, nx: 0, nz: 1, label: 'Gate #3' }},
            {{ id: 4, x: -9.0, y: 3.8, z: 0.0, yaw: -Math.PI / 2, nx: -1, nz: 0, label: 'Gate #4' }}
        ];
        // Outer circuit clearance corners to safely bypass central collision pillars (+-3, +-3)
        const outerCorners = [
            {{ x: 7.0, y: 3.8, z: -9.5, label: 'Corner #1' }},
            {{ x: 11.5, y: 5.2, z: 7.0, label: 'Corner #2' }},
            {{ x: -7.0, y: 4.8, z: 11.5, label: 'Corner #3' }},
            {{ x: -11.5, y: 3.5, z: -7.0, label: 'Corner #4' }}
        ];
        let currentAIGateIndex = 0;
        let aiNavStage = 'APPROACH'; // 'APPROACH' | 'THROUGH' | 'LEADOUT' | 'CORNER'
        let clearedGateId = null;
        let clearedGateCooldownTimer = 0.0;
        let isAIAutopilotActive = false;
        let aiCumulativeReward = 0.0;
        let aiLapsCompleted = 0;
        let aiConfidence = 96.5;

        // Multi-Stage Privileged Distilled Neural Policy (FEAT-M2.5.2)
        const studentStages = __STUDENT_STAGES_PLACEHOLDER__;
        let currentStudentStageKey = 'stage_2_mastered';

        // Global Multi-Gate Closed Circuit Navigation Corridor (Gate 1 -> Corner 1 -> Gate 2 -> Corner 2 -> Gate 3 -> Corner 3 -> Gate 4 -> Corner 4 -> Gate 1)
        const circuitPts = [
            new THREE.Vector3(aiGates[0].x, aiGates[0].y, aiGates[0].z),
            new THREE.Vector3(aiGates[0].x + aiGates[0].nx * 2.2, aiGates[0].y, aiGates[0].z + aiGates[0].nz * 2.2),
            new THREE.Vector3(outerCorners[0].x, outerCorners[0].y, outerCorners[0].z),
            new THREE.Vector3(aiGates[1].x - aiGates[1].nx * 2.2, aiGates[1].y, aiGates[1].z - aiGates[1].nz * 2.2),
            new THREE.Vector3(aiGates[1].x, aiGates[1].y, aiGates[1].z),
            new THREE.Vector3(aiGates[1].x + aiGates[1].nx * 2.2, aiGates[1].y, aiGates[1].z + aiGates[1].nz * 2.2),
            new THREE.Vector3(outerCorners[1].x, outerCorners[1].y, outerCorners[1].z),
            new THREE.Vector3(aiGates[2].x - aiGates[2].nx * 2.2, aiGates[2].y, aiGates[2].z - aiGates[2].nz * 2.2),
            new THREE.Vector3(aiGates[2].x, aiGates[2].y, aiGates[2].z),
            new THREE.Vector3(aiGates[2].x + aiGates[2].nx * 2.2, aiGates[2].y, aiGates[2].z + aiGates[2].nz * 2.2),
            new THREE.Vector3(outerCorners[2].x, outerCorners[2].y, outerCorners[2].z),
            new THREE.Vector3(aiGates[3].x - aiGates[3].nx * 2.2, aiGates[3].y, aiGates[3].z - aiGates[3].nz * 2.2),
            new THREE.Vector3(aiGates[3].x, aiGates[3].y, aiGates[3].z),
            new THREE.Vector3(aiGates[3].x + aiGates[3].nx * 2.2, aiGates[3].y, aiGates[3].z + aiGates[3].nz * 2.2),
            new THREE.Vector3(outerCorners[3].x, outerCorners[3].y, outerCorners[3].z),
            new THREE.Vector3(aiGates[0].x - aiGates[0].nx * 2.2, aiGates[0].y, aiGates[0].z - aiGates[0].nz * 2.2),
            new THREE.Vector3(aiGates[0].x, aiGates[0].y, aiGates[0].z)
        ];
        const circuitGeo = new THREE.BufferGeometry().setFromPoints(circuitPts);
        const circuitMat = new THREE.LineDashedMaterial({{
            color: 0xa855f7,
            dashSize: 1.0,
            gapSize: 0.5,
            transparent: true,
            opacity: 0.65,
            linewidth: 2
        }});
        const circuitLine = new THREE.Line(circuitGeo, circuitMat);
        circuitLine.computeLineDistances();
        circuitLine.visible = false;
        circuitLine.frustumCulled = false;
        scene.add(circuitLine);

        // Shared Autonomy Copilot State (Milestone M2.6)
        let isCopilotActive = true;
        let copilotLevel = 'STANDBY';
        let copilotInterventionBeta = 0.0;
        let copilotTTC = 999.0;

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
                box: new THREE.Box3().setFromObject(obsMesh),
                name: obs.name || '環境障礙柱'
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
                opacity: 0.92,
                depthWrite: true,
                side: THREE.DoubleSide
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

            // Boundary Wireframe Cage Wall Frames
            const cageBox = new THREE.BoxGeometry(40, 12, 40);
            const cageEdge = new THREE.EdgesGeometry(cageBox);
            const cageLine = new THREE.LineSegments(cageEdge, new THREE.LineBasicMaterial({{ color: 0x00e5ff, linewidth: 2 }}));
            cageLine.position.set(0, 6, 0);
            group.add(cageLine);

            // Glowing FPV / Obstacle Course Flight Gates with 3D Rotation Alignment
            const gates = [
                {{ id: 1, pos: [0, 3.2, -7], color: 0x00e5ff, size: [4.5, 3.5], yaw: 0, nx: 0, nz: -1 }},
                {{ id: 2, pos: [9, 4.5, 0], color: 0xf43f5e, size: [4.0, 4.0], yaw: Math.PI / 2, nx: 1, nz: 0 }},
                {{ id: 3, pos: [0, 6.0, 9], color: 0xf59e0b, size: [4.5, 3.5], yaw: Math.PI, nx: 0, nz: 1 }},
                {{ id: 4, pos: [-9, 3.8, 0], color: 0x22c55e, size: [4.0, 4.0], yaw: -Math.PI / 2, nx: -1, nz: 0 }}
            ];

            gates.forEach((g, gIdx) => {{
                const gateGroup = new THREE.Group();
                gateGroup.position.set(g.pos[0], g.pos[1], g.pos[2]);
                gateGroup.rotation.y = g.yaw;

                const postGeo = new THREE.BoxGeometry(0.25, g.size[1], 0.25);
                const postMat = new THREE.MeshStandardMaterial({{ color: g.color, emissive: g.color, emissiveIntensity: 0.6 }});

                const postL = new THREE.Mesh(postGeo, postMat);
                postL.position.set(-g.size[0] / 2, 0, 0);
                gateGroup.add(postL);

                const postR = new THREE.Mesh(postGeo, postMat);
                postR.position.set(g.size[0] / 2, 0, 0);
                gateGroup.add(postR);

                const topGeo = new THREE.BoxGeometry(g.size[0] + 0.25, 0.25, 0.25);
                const topMesh = new THREE.Mesh(topGeo, postMat);
                topMesh.position.set(0, g.size[1] / 2, 0);
                gateGroup.add(topMesh);

                group.add(gateGroup);
                gateGroup.updateMatrixWorld(true);

                postL.geometry.computeBoundingBox();
                postR.geometry.computeBoundingBox();
                topMesh.geometry.computeBoundingBox();

                envObstacles.collision_arena.push({{ mesh: postL, box: new THREE.Box3().setFromObject(postL), name: '穿越門 #' + (gIdx + 1) + ' (左立柱)', gateId: g.id, isGatePost: true }});
                envObstacles.collision_arena.push({{ mesh: postR, box: new THREE.Box3().setFromObject(postR), name: '穿越門 #' + (gIdx + 1) + ' (右立柱)', gateId: g.id, isGatePost: true }});
                envObstacles.collision_arena.push({{ mesh: topMesh, box: new THREE.Box3().setFromObject(topMesh), name: '穿越門 #' + (gIdx + 1) + ' (橫樑)', gateId: g.id, isGateTop: true }});
            }});

            // 6 Cylindrical Collision Pillars with Hazard Stripes
            const pillars = [
                [3, 3], [-3, 3], [3, -3], [-3, -3], [7, 7], [-7, -7]
            ];
            pillars.forEach((p, pIdx) => {{
                const pGeo = new THREE.CylinderGeometry(0.55, 0.55, 6, 24);
                const pMat = new THREE.MeshStandardMaterial({{ color: 0xeab308, roughness: 0.3, metalness: 0.4 }});
                const pMesh = new THREE.Mesh(pGeo, pMat);
                pMesh.position.set(p[0], 3, p[1]);
                pMesh.castShadow = true;
                group.add(pMesh);
                pMesh.geometry.computeBoundingBox();
                envObstacles.collision_arena.push({{ mesh: pMesh, box: new THREE.Box3().setFromObject(pMesh), name: '立體立柱 #' + (pIdx + 1) }});
            }});

            // Inclined Aerobatic Launch Ramp
            const rampGeo = new THREE.BoxGeometry(4, 0.3, 8);
            const rampMat = new THREE.MeshStandardMaterial({{ color: 0x3b82f6, metalness: 0.6 }});
            const rampMesh = new THREE.Mesh(rampGeo, rampMat);
            rampMesh.position.set(0, 1.2, -15);
            rampMesh.rotation.x = 0.28;
            group.add(rampMesh);
            rampMesh.geometry.computeBoundingBox();
            envObstacles.collision_arena.push({{ mesh: rampMesh, box: new THREE.Box3().setFromObject(rampMesh), name: '特技起飛斜坡' }});
        }})();

        // --- Scenario 4: 夜間紅外線巡檢 (Night Thermal/Inspection) ---
        (function buildNightThermal() {{
            const group = envGroups.night_thermal;

            // Midnight Dark Ground with Infrared Grid
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
        let dynamicTestObstacleObj = null;

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
            if (typeof dynamicTestObstacleObj !== 'undefined' && dynamicTestObstacleObj) {{
                activeObstacles.push(dynamicTestObstacleObj);
            }}

            if (typeof circuitLine !== 'undefined' && circuitLine) {{
                circuitLine.visible = (envKey === 'collision_arena' && isAIAutopilotActive);
            }}

            // 3. Update Sky, Fog, and Grid
            scene.background = new THREE.Color(cfg.bg);
            scene.fog.color = new THREE.Color(cfg.fogColor);
            scene.fog.density = cfg.fogDensity;

            if (currentGrid) {{
                scene.remove(currentGrid);
                currentGrid.geometry.dispose();
                if (currentGrid.material) currentGrid.material.dispose();
            }}
            currentGrid = new THREE.GridHelper(50, 50, cfg.gridColor1, cfg.gridColor2);
            currentGrid.position.y = (envKey === 'offshore_wind') ? -0.8 : 0.0;
            scene.add(currentGrid);

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

                // 4. Navigation Light damage
                if (targetArm.navLightMesh) {{
                    targetArm.navLightMesh.material.emissiveIntensity = 0.1;
                }}
                if (targetArm.navPointLight) {{
                    targetArm.navPointLight.intensity = 0;
                }}

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

            // Auto-disengage AI if damage is catastrophic
            const brokenCountNow = droneArmComponents.filter(a => a.isArmBroken || a.isPropBroken).length;
            const intactRatioNow = (numArms - brokenCountNow) / numArms;
            if ((droneStructuralIntegrity <= 20 || intactRatioNow <= 0.5) && isAIAutopilotActive) {{
                disengageAIAutopilot('crash');
            }}
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
            if (keys['ArrowLeft'] || keys['KeyQ']) yaw_cmd -= 1.0;
            if (keys['ArrowRight'] || keys['KeyE']) yaw_cmd += 1.0;

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
                    proximity_sensing: {{
                        nearest_distance_m: Number(latestLiDARReading.dist.toFixed(3)),
                        nearest_object: latestLiDARReading.name,
                        relative_direction: latestLiDARReading.direction
                    }},
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

            // 5. 程式化全自動落盤下載 (Zero-Click Programmatic Auto-Download)
            try {{
                const jsonStr = JSON.stringify(exportPayload, null, 2);
                const blob = new Blob([jsonStr], {{ type: 'application/json' }});
                const downloadUrl = URL.createObjectURL(blob);
                const downloadAnchor = document.createElement('a');
                downloadAnchor.href = downloadUrl;
                downloadAnchor.download = fileNameBase + '.json';
                document.body.appendChild(downloadAnchor);
                downloadAnchor.click();
                document.body.removeChild(downloadAnchor);
                setTimeout(() => URL.revokeObjectURL(downloadUrl), 500);
                console.log('[FlightDataRecorder] Zero-click auto-download triggered:', fileNameBase);
            }} catch(downloadErr) {{
                console.warn('[FlightDataRecorder] Auto-download warning:', downloadErr);
            }}

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
            if (doReset) {{
                if (damagedPartsHistory.length > 0 || (typeof recordedFlightData !== 'undefined' && recordedFlightData.length > 0)) {{
                    flightQuestionnaireHistory.push({{
                        timestamp: new Date().toISOString(),
                        feedback: '飛手快速重置 (跳過心得備註)',
                        notes: '飛手快速重置 (跳過心得備註)',
                        final_integrity: droneStructuralIntegrity,
                        final_position: [Number(drone.position.x.toFixed(3)), Number(drone.position.y.toFixed(3)), Number(drone.position.z.toFixed(3))],
                        damaged_components: [...damagedPartsHistory]
                    }});
                    try {{ saveFlightData(); }} catch(e) {{}}
                }}
                repairAndResetDrone();
            }}
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
            closeResetModal(false);
            try {{
                saveFlightData();
                showToast('💾 飛行數據與問卷已全自動導出落盤，機身維修重置完畢！');
            }} catch(e) {{
                showToast('💾 飛行經驗回饋已儲存，機身維修重置完畢！');
            }}
            repairAndResetDrone();
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

                if (arm.navLightMesh) {{
                    arm.navLightMesh.material.emissiveIntensity = 3.5;
                }}
                if (arm.navPointLight) {{
                    arm.navPointLight.intensity = 0.75;
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
            currentAIGateIndex = 0;
            aiNavStage = 'APPROACH';
            clearedGateId = null;
            clearedGateCooldownTimer = 0.0;

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

            if (typeof isAIAutopilotActive !== 'undefined' && isAIAutopilotActive) {{
                disengageAIAutopilot('reset');
            }}
            currentAIGateIndex = 0;
            aiCumulativeReward = 0.0;
            aiLapsCompleted = 0;

            showToast('✨ 機身結構已 100% 快速修復就緒！');
        }}

        function simulateTestCrash() {{
            const testPos = new THREE.Vector3(armLength * 0.9, 0.05, 0.1).applyMatrix4(drone.matrixWorld);
            applyStructuralDamage(testPos, 3.2, '結構碰撞測試');
            velocity.x = -1.2;
            velocity.y = 0.8;
        }}

        // --- Autonomous AI Autopilot Control Functions ---
        function toggleAIAutopilot() {{
            const brokenCount = droneArmComponents.filter(a => a.isArmBroken || a.isPropBroken).length;
            const isCatastrophic = droneStructuralIntegrity <= 20 || brokenCount >= (numArms / 2);
            if (isCatastrophic) {{
                showToast('❌ 機體損壞過重，無法啟動 AI 自主飛行！');
                return;
            }}
            if (isAIAutopilotActive) {{
                disengageAIAutopilot('user_toggle');
            }} else {{
                engageAIAutopilot();
            }}
        }}

        function engageAIAutopilot() {{
            isAIAutopilotActive = true;
            // Auto-switch to collision arena if currently in a different environment so flight gates are in scene
            if (activeEnvKey !== 'collision_arena') {{
                switchEnvironment('collision_arena');
            }}
            const badge = document.getElementById('ai-status-badge');
            const text = document.getElementById('ai-status-text');
            const btn = document.getElementById('btn-ai-toggle');
            if (badge) badge.className = 'ai-indicator active';
            if (text) text.innerText = 'AI 自主 AUTOPILOT';
            if (btn) {{
                btn.className = 'btn-action btn-ai-stop';
                btn.innerText = '🛑 解除 AI 接管 (P)';
                btn.blur();
            }}
            if (typeof circuitLine !== 'undefined' && circuitLine) {{
                circuitLine.visible = true;
            }}
            if (trajectoryLine) {{
                trajectoryLine.visible = true;
                trajectoryLine.frustumCulled = false;
            }}
            showToast('🤖 AI 自主飛行已啟動：垂直起飛爬升 ➔ 前往 Gate #1 (8向LiDAR避障)');
        }}

        function disengageAIAutopilot(reason = 'user_toggle') {{
            if (!isAIAutopilotActive) return;
            isAIAutopilotActive = false;
            const badge = document.getElementById('ai-status-badge');
            const text = document.getElementById('ai-status-text');
            const btn = document.getElementById('btn-ai-toggle');
            if (badge) badge.className = 'ai-indicator';
            if (text) text.innerText = '手動 MANUAL';
            if (btn) {{
                btn.className = 'btn-action btn-ai-start';
                btn.innerText = '🤖 啟動 AI 自主飛行 (P)';
                btn.blur();
            }}
            if (typeof circuitLine !== 'undefined' && circuitLine) circuitLine.visible = false;
            if (trajectoryLine) trajectoryLine.visible = false;
            if (reason === 'manual_takeover') {{
                showToast('⚠️ 人工接管介入：AI 自主飛行已解除');
            }} else if (reason === 'crash') {{
                showToast('💥 碰撞迫降：AI 自主巡檢終止');
            }} else if (reason !== 'reset') {{
                showToast('🎮 已切換回人工手動飛行模式');
            }}
        }}

        function toggleTestObstacle() {{
            const btn = document.getElementById('btn-test-obstacle');
            if (!dynamicTestObstacleObj) {{
                let posX = 0.35;
                let posY = 2.6;
                let posZ = -3.2;

                if (drone.position.length() > 3.0) {{
                    const fwd = new THREE.Vector3(-Math.sin(yaw), 0, -Math.cos(yaw)).normalize();
                    posX = drone.position.x + fwd.x * 3.6 + 0.15;
                    posY = Math.max(2.2, drone.position.y);
                    posZ = drone.position.z + fwd.z * 3.6;
                }}

                const obsGeo = new THREE.CylinderGeometry(0.45, 0.45, 5.5, 24);
                const obsMat = new THREE.MeshStandardMaterial({{
                    color: 0xef4444,
                    emissive: 0x991b1b,
                    emissiveIntensity: 0.7,
                    roughness: 0.25,
                    metalness: 0.6
                }});
                const mesh = new THREE.Mesh(obsGeo, obsMat);
                mesh.position.set(posX, posY, posZ);
                mesh.castShadow = true;
                mesh.receiveShadow = true;

                const ringGeo = new THREE.TorusGeometry(0.65, 0.04, 8, 24);
                const ringMat = new THREE.MeshBasicMaterial({{ color: 0xfacc15, wireframe: true }});
                const ringTop = new THREE.Mesh(ringGeo, ringMat);
                ringTop.rotation.x = Math.PI / 2;
                ringTop.position.y = 1.6;
                mesh.add(ringTop);
                const ringBot = new THREE.Mesh(ringGeo, ringMat);
                ringBot.rotation.x = Math.PI / 2;
                ringBot.position.y = -1.6;
                mesh.add(ringBot);

                scene.add(mesh);
                mesh.geometry.computeBoundingBox();

                const obsObj = {{
                    mesh: mesh,
                    box: new THREE.Box3().setFromObject(mesh),
                    name: '🚨 突發測試障礙物 (Hazard Pillar)'
                }};
                activeObstacles.push(obsObj);
                dynamicTestObstacleObj = obsObj;

                if (btn) {{
                    btn.innerHTML = '🟢 移除突發障礙物 (恢復航道) (O)';
                    btn.style.background = 'linear-gradient(135deg, #059669, #047857)';
                    btn.style.borderColor = '#10b981';
                    btn.style.boxShadow = '0 2px 8px rgba(16, 185, 129, 0.4)';
                    btn.blur();
                }}
                showToast('🚨 已插入突發障礙柱 (' + posX.toFixed(1) + ', ' + posY.toFixed(1) + ', ' + posZ.toFixed(1) + ')！觀察 8向LiDAR 與神經網絡避障！');
            }} else {{
                scene.remove(dynamicTestObstacleObj.mesh);
                const idx = activeObstacles.indexOf(dynamicTestObstacleObj);
                if (idx !== -1) {{
                    activeObstacles.splice(idx, 1);
                }}
                dynamicTestObstacleObj = null;

                if (btn) {{
                    btn.innerHTML = '🚨 插入突發紅色柱子 (避障實測) (O)';
                    btn.style.background = 'linear-gradient(135deg, #dc2626, #b91c1c)';
                    btn.style.borderColor = '#ef4444';
                    btn.style.boxShadow = '0 2px 8px rgba(220, 38, 38, 0.4)';
                    btn.blur();
                }}
                showToast('✅ 突發障礙物已移除，航道已完全淨空！');
            }}
        }}

        function switchAIStage(stageKey) {{
            currentStudentStageKey = stageKey;
            const badge = document.getElementById('ai-stage-badge');
            const labels = {{
                'stage_0_untrained': '🌱 0% 初學',
                'stage_1_half_trained': '🌿 40% 中級',
                'stage_2_mastered': '🏆 100% 精通'
            }};
            if (badge) badge.innerText = labels[stageKey] || stageKey;

            const stagesList = ['stage_0_untrained', 'stage_1_half_trained', 'stage_2_mastered'];
            stagesList.forEach((k, idx) => {{
                const btn = document.getElementById('btn-stage-' + idx);
                if (btn) {{
                    if (k === stageKey) {{
                        btn.style.background = '#7c3aed';
                        btn.style.borderColor = '#a855f7';
                        btn.style.color = '#fff';
                        btn.style.fontWeight = 'bold';
                    }} else {{
                        btn.style.background = '#1e293b';
                        btn.style.borderColor = '#475569';
                        btn.style.color = '#94a3b8';
                        btn.style.fontWeight = 'normal';
                    }}
                    btn.blur();
                }}
            }});
            showToast('🎓 學生神經網絡已切換至：' + (labels[stageKey] || stageKey));
        }}

        function predictStudentNeural(obs, weights) {{
            if (!weights || !weights.w1 || !weights.w2 || !weights.w3) return null;
            const w1 = weights.w1, b1 = weights.b1;
            const w2 = weights.w2, b2 = weights.b2;
            const w3 = weights.w3, b3 = weights.b3;

            // Layer 1: ReLU(w1 @ obs + b1)
            const h1 = new Float32Array(b1.length);
            for (let j = 0; j < b1.length; j++) {{
                let sum = b1[j];
                const row = w1[j];
                for (let i = 0; i < obs.length; i++) {{
                    sum += row[i] * obs[i];
                }}
                h1[j] = sum > 0 ? sum : 0;
            }}

            // Layer 2: ReLU(w2 @ h1 + b2)
            const h2 = new Float32Array(b2.length);
            for (let j = 0; j < b2.length; j++) {{
                let sum = b2[j];
                const row = w2[j];
                for (let i = 0; i < h1.length; i++) {{
                    sum += row[i] * h1[i];
                }}
                h2[j] = sum > 0 ? sum : 0;
            }}

            // Layer 3: Tanh(w3 @ h2 + b3)
            const out = new Float32Array(b3.length);
            for (let j = 0; j < b3.length; j++) {{
                let sum = b3[j];
                const row = w3[j];
                for (let i = 0; i < h2.length; i++) {{
                    sum += row[i] * h2[i];
                }}
                out[j] = Math.tanh(sum);
            }}
            return out;
        }}

        function toggleCopilot() {{
            isCopilotActive = !isCopilotActive;
            const badge = document.getElementById('copilot-status-badge');
            const modeText = document.getElementById('copilot-mode-text');
            const btn = document.getElementById('btn-copilot-toggle');
            const betaEl = document.getElementById('copilot-beta');
            const ttcEl = document.getElementById('copilot-ttc');

            if (isCopilotActive) {{
                if (btn) {{
                    btn.className = 'btn-action btn-copilot-active';
                    btn.innerText = '🛡️ 協同副駕駛已啟動 (C)';
                    btn.blur();
                }}
                showToast('🛡️ AI 協同副駕駛已啟動：手動主飛 ＋ 雙層防撞守護 (警戒阻尼 / 主動排斥)');
            }} else {{
                if (btn) {{
                    btn.className = 'btn-action btn-copilot-inactive';
                    btn.innerText = '🛡️ 協同副駕駛已停用 (C)';
                    btn.blur();
                }}
                if (badge) {{
                    badge.className = 'copilot-indicator copilot-standby';
                    badge.innerText = '○ OFF';
                }}
                if (modeText) modeText.innerText = '副駕駛已關閉 (OFF)';
                if (betaEl) betaEl.innerText = '0.0%';
                if (ttcEl) ttcEl.innerText = '-- s';
                if (typeof copilotHalo !== 'undefined' && copilotHalo) copilotHalo.visible = false;
                showToast('⚠️ AI 協同副駕駛已停用：當前為純手動無保護模式');
            }}
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

            // Instant Manual Takeover: Any pilot control input cancels AI autopilot
            const manualKeys = ['KeyW', 'KeyS', 'KeyA', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'];
            if (isAIAutopilotActive && manualKeys.includes(e.code)) {{
                disengageAIAutopilot('manual_takeover');
            }}

            keys[e.code] = true;
            if (e.code === 'KeyR' || e.key === 'r' || e.key === 'R') promptResetExperience();
            if (e.code === 'KeyG' || e.key === 'g' || e.key === 'G') toggleRecording();
            if (e.code === 'KeyP' || e.key === 'p' || e.key === 'P') toggleAIAutopilot();
            if (e.code === 'KeyC' || e.key === 'c' || e.key === 'C') toggleCopilot();
            if (e.code === 'KeyO' || e.key === 'o' || e.key === 'O') toggleTestObstacle();
        }});
        window.addEventListener('keyup', (e) => keys[e.code] = false);

        let velocity = new THREE.Vector3(0, 0, 0);
        let rotationSpeed = 0;
        let pitch = 0, roll = 0, yaw = 0;
        let batteryVoltage = 11.80;
        const clock = new THREE.Clock();

        // Progressive Input Shaping (RC Expo / Anti-Burst Smoothing)
        let pitchRamp = 0;
        let rollRamp = 0;
        let latestLiDARReading = {{ dist: 99.0, name: '無障礙物', direction: '周圍', point: new THREE.Vector3() }};
        const _tempObsCenter = new THREE.Vector3();

        // Advanced AI Flight Dynamics State Variables (FEAT-M2.5.3)
        let aiYawRateSmoothed = 0;
        let isTiltedSlitSprint = false;
        let slitSprintRollTarget = 0;
        let slitSprintTimer = 0;

        function updatePhysics() {{
            // Damage evaluation on flight physics (Hoisted to eliminate TDZ ReferenceError)
            const brokenCount = droneArmComponents.filter(a => a.isArmBroken || a.isPropBroken).length;
            const intactRatio = (numArms - brokenCount) / numArms;
            const isCatastrophic = droneStructuralIntegrity <= 15 || intactRatio <= 0.5;

            // Auto-disengage AI autopilot on catastrophic damage
            if (isCatastrophic && isAIAutopilotActive) {{
                disengageAIAutopilot('crash');
            }}

            // Control Authority: AI Autopilot Mode vs Manual Keyboard Controls
            let throttleAcc = 0;
            let rawPitchCmd = 0;
            let rawRollCmd = 0;
            let targetPitch = 0;
            let targetRoll = 0;

            if (clearedGateCooldownTimer > 0) clearedGateCooldownTimer -= 0.016;
            else clearedGateId = null;

            if (isAIAutopilotActive && !isCatastrophic) {{
                const targetGate = aiGates[currentAIGateIndex];
                const targetCorner = outerCorners[currentAIGateIndex];
                const relX = targetGate.x - drone.position.x;
                const relY = targetGate.y - drone.position.y;
                const relZ = targetGate.z - drone.position.z;
                const dist2D = Math.hypot(relX, relZ);
                const dist3D = Math.hypot(relX, relY, relZ);

                // Two-Stage AI Flight Control:
                // Stage 1: Dedicated Vertical Takeoff / Initial Climb Phase (Altitude < 1.6m)
                // Prevents ground-clamp friction and tilt cancellation while leaving the launch pad
                const isTakingOff = drone.position.y < 1.6;

                let leadX, leadZ, targetAlt;

                if (isTakingOff) {{
                    rawPitchCmd = 0;
                    rawRollCmd = 0;
                    targetPitch = 0;
                    targetRoll = 0;
                    rotationSpeed = 0;
                    throttleAcc = 14.5; // High vertical TWR lift-off
                    aiConfidence = 99.2;
                    aiCumulativeReward += 0.02;

                    const text = document.getElementById('ai-status-text');
                    if (text) text.innerText = 'AI 垂直起飛中 (爬升至安全高度)...';
                }} else {{
                    // 1. Gate Normal Crossing & State Machine Check
                    // Relative vector from gate center to drone in horizontal plane
                    const dxFromGate = drone.position.x - targetGate.x;
                    const dzFromGate = drone.position.z - targetGate.z;
                    // Signed distance along gate normal (negative = in front of gate, positive = passed through gate)
                    const signedDot = dxFromGate * targetGate.nx + dzFromGate * targetGate.nz;
                    // Lateral distance from the center line of the gate
                    const lateralDist = Math.hypot(
                        dxFromGate - signedDot * targetGate.nx,
                        dzFromGate - signedDot * targetGate.nz
                    );
                    const vertDist = Math.abs(drone.position.y - targetGate.y);

                    // A gate is cleared when the drone has passed beyond the gate plane (signedDot >= 0.35m)
                    // within the gate lateral aperture and vertical clearance
                    const hasCrossedGate = (signedDot >= 0.35 && lateralDist < 2.2 && vertDist < 2.2) ||
                                           (dist3D < 1.0 && signedDot >= 0.1 && lateralDist < 1.8);

                    // Multi-Stage Sub-corridor Navigation State Machine: APPROACH -> THROUGH -> LEADOUT -> CORNER
                    const approachPtX = targetGate.x - targetGate.nx * 2.2;
                    const approachPtZ = targetGate.z - targetGate.nz * 2.2;
                    const distToApproach = Math.hypot(drone.position.x - approachPtX, drone.position.z - approachPtZ);

                    if (aiNavStage === 'APPROACH') {{
                        // Switch to THROUGH when aligned in pre-gate corridor or close to entry point
                        if (distToApproach < 1.5 || (signedDot >= -2.0 && signedDot <= -0.15 && lateralDist < 2.0 && vertDist < 2.0)) {{
                            aiNavStage = 'THROUGH';
                        }}
                    }} else if (aiNavStage === 'THROUGH') {{
                        if (hasCrossedGate) {{
                            aiNavStage = 'LEADOUT';
                            clearedGateId = targetGate.id;
                            clearedGateCooldownTimer = 3.0;
                            aiCumulativeReward += 150.0;
                        }}
                    }} else if (aiNavStage === 'LEADOUT') {{
                        const leadOutPtX = targetGate.x + targetGate.nx * 2.5;
                        const leadOutPtZ = targetGate.z + targetGate.nz * 2.5;
                        const distToLeadOut = Math.hypot(drone.position.x - leadOutPtX, drone.position.z - leadOutPtZ);
                        if (signedDot >= 2.0 || distToLeadOut < 1.2) {{
                            aiNavStage = 'CORNER';
                        }}
                    }} else if (aiNavStage === 'CORNER') {{
                        const distToCorner = Math.hypot(drone.position.x - targetCorner.x, drone.position.z - targetCorner.z);
                        const nextGateIndex = (currentAIGateIndex + 1) % aiGates.length;
                        if (distToCorner < 2.2) {{
                            currentAIGateIndex = nextGateIndex;
                            aiNavStage = 'APPROACH';
                            if (currentAIGateIndex === 0) {{
                                aiLapsCompleted++;
                                aiCumulativeReward += 400.0;
                                showToast('🏆 AI 順利完成第 ' + aiLapsCompleted + ' 圈全場穿越巡檢！');
                            }}
                        }}
                    }}

                    // 2. Goal Attraction Vector: Multi-stage Waypoint Targets with Smooth Lookahead (Task Group 2)
                    const nextGateIdx = (currentAIGateIndex + 1) % aiGates.length;
                    const nextGateObj = aiGates[nextGateIdx];
                    const nextApproachPtX = nextGateObj.x - nextGateObj.nx * 2.2;
                    const nextApproachPtZ = nextGateObj.z - nextGateObj.nz * 2.2;

                    if (aiNavStage === 'APPROACH') {{
                        leadX = approachPtX;
                        leadZ = approachPtZ;
                        targetAlt = targetGate.y;
                    }} else if (aiNavStage === 'THROUGH') {{
                        const leadDist = 1.6;
                        leadX = targetGate.x + targetGate.nx * leadDist;
                        leadZ = targetGate.z + targetGate.nz * leadDist;
                        targetAlt = targetGate.y;
                    }} else if (aiNavStage === 'LEADOUT') {{
                        const leadOutPtX = targetGate.x + targetGate.nx * 2.8;
                        const leadOutPtZ = targetGate.z + targetGate.nz * 2.8;
                        const distToLeadOut = Math.hypot(drone.position.x - leadOutPtX, drone.position.z - leadOutPtZ);
                        const blendOut = Math.min(1.0, Math.max(0.0, 1.0 - distToLeadOut / 2.8));
                        leadX = (1 - blendOut) * leadOutPtX + blendOut * targetCorner.x;
                        leadZ = (1 - blendOut) * leadOutPtZ + blendOut * targetCorner.z;
                        targetAlt = (1 - blendOut) * targetGate.y + blendOut * targetCorner.y;
                    }} else if (aiNavStage === 'CORNER') {{
                        const distToCorner = Math.hypot(drone.position.x - targetCorner.x, drone.position.z - targetCorner.z);
                        const cornerBlend = Math.min(1.0, Math.max(0.0, 1.0 - distToCorner / 3.2));
                        leadX = (1 - cornerBlend) * targetCorner.x + cornerBlend * nextApproachPtX;
                        leadZ = (1 - cornerBlend) * targetCorner.z + cornerBlend * nextApproachPtZ;
                        targetAlt = (1 - cornerBlend) * targetCorner.y + cornerBlend * nextGateObj.y;
                    }}

                    // Adaptive Velocity Profiling (FEAT-M2.5.3 Task Group 1)
                    let cruiseSpeed = 2.4;
                    if (aiNavStage === 'APPROACH') {{
                        if (distToApproach > 3.0) {{
                            cruiseSpeed = 4.8; // High speed sprint on straightaways
                        }} else {{
                            cruiseSpeed = 2.4; // Smooth gate entry deceleration
                        }}
                    }} else if (aiNavStage === 'THROUGH') {{
                        cruiseSpeed = isTiltedSlitSprint ? 4.8 : 2.2;
                    }} else if (aiNavStage === 'LEADOUT') {{
                        cruiseSpeed = 3.6; // Accelerate out of gate
                    }} else if (aiNavStage === 'CORNER') {{
                        const distToCorner = Math.hypot(drone.position.x - targetCorner.x, drone.position.z - targetCorner.z);
                        if (distToCorner > 3.0) {{
                            cruiseSpeed = 4.2; // Rapid transit to corner
                        }} else {{
                            cruiseSpeed = 2.8; // Smooth coordinated cornering
                        }}
                    }}

                    const text = document.getElementById('ai-status-text');
                    if (aiNavStage === 'APPROACH') {{
                        if (text) text.innerText = 'AI 門前進門對齊 (' + targetGate.label + ' 正面)';
                    }} else if (aiNavStage === 'THROUGH') {{
                        if (text) text.innerText = isTiltedSlitSprint ? '⚡ AI 刀鋒特技加速穿縫 (Knife-Edge Sprint)' : ('AI 航線穿門巡檢 (' + targetGate.label + ')');
                    }} else if (aiNavStage === 'LEADOUT') {{
                        if (text) text.innerText = 'AI 出門走廊導引 (' + targetGate.label + ' 出口)';
                    }} else if (aiNavStage === 'CORNER') {{
                        if (text) text.innerText = 'AI 外環協同轉彎 (' + targetCorner.label + ')';
                    }}

                    const toLeadX = leadX - drone.position.x;
                    const toLeadZ = leadZ - drone.position.z;
                    const leadDist2D = Math.hypot(toLeadX, toLeadZ);

                    let attractX = (leadDist2D > 0.01) ? (toLeadX / leadDist2D) * cruiseSpeed : 0;
                    let attractZ = (leadDist2D > 0.01) ? (toLeadZ / leadDist2D) * cruiseSpeed : 0;

                    // 3. Smart Obstacle Repulsion & Narrow Slit Predictive Check (Task Group 3)
                    let repelX = 0;
                    let repelZ = 0;
                    let detectedNarrowSlit = false;
                    let slitDist = 99.0;
                    let slitRollSign = 1.0;

                    const isApproachingGate = (aiNavStage === 'APPROACH' || aiNavStage === 'THROUGH' || aiNavStage === 'LEADOUT') && dist2D < 3.2 && vertDist < 2.5;

                    activeObstacles.forEach(obs => {{
                        const isTargetGateObs = (obs.gateId === targetGate.id);
                        const isClearedGateObs = (clearedGateId && obs.gateId === clearedGateId);

                        // Smart tunnel filtering for gates:
                        if (isTargetGateObs || isClearedGateObs) {{
                            if (obs.isGateTop) return;

                            // For side posts, apply smooth lateral push toward center if within 1.25m
                            obs.box.getCenter(_tempObsCenter);
                            const dX = drone.position.x - _tempObsCenter.x;
                            const dZ = drone.position.z - _tempObsCenter.z;
                            const d = Math.hypot(dX, dZ);
                            if (d < 1.25 && d > 0.05 && vertDist < 2.2) {{
                                const gRef = isTargetGateObs ? targetGate : (aiGates.find(g => g.id === clearedGateId) || targetGate);
                                const latX = -gRef.nz;
                                const latZ = gRef.nx;
                                const postDotLat = (dX * latX + dZ * latZ);
                                const pushLat = (postDotLat > 0 ? 1 : -1) * Math.pow((1.25 - d) / 1.25, 1.5) * 2.5;
                                repelX += latX * pushLat;
                                repelZ += latZ * pushLat;
                            }}
                            return;
                        }}

                        // Normal obstacle repulsion for pillars, other gates, and ramps
                        obs.box.getCenter(_tempObsCenter);
                        let dX = drone.position.x - _tempObsCenter.x;
                        let dZ = drone.position.z - _tempObsCenter.z;
                        let d = Math.hypot(dX, dZ);
                        const safeDist = 3.2;
                        if (d < safeDist && d > 0.1 && Math.abs(drone.position.y - _tempObsCenter.y) < 3.5) {{
                            // Symmetry breaking perturbation to eliminate APF saddle deadlock
                            if (Math.abs(dX) < 0.08) {{
                                dX += 0.25;
                                d = Math.hypot(dX, dZ);
                            }}
                            const strength = Math.pow((safeDist - d) / safeDist, 1.8) * 2.5;
                            repelX += (dX / d) * strength;
                            repelZ += (dZ / d) * strength;
                        }}

                        // Predictive Slit Feasibility Check in Forward Sector
                        // Note: Only true paired narrow slits (< 1.6m aperture) should trigger knife-edge roll.
                        // Isolated pillars (such as 立體立柱) and dynamic test obstacles must use standard APF deflection!
                        if (obs.isSlitObstacle) {{
                            const toObsX = _tempObsCenter.x - drone.position.x;
                            const toObsZ = _tempObsCenter.z - drone.position.z;
                            const cosY0 = Math.cos(yaw);
                            const sinY0 = Math.sin(yaw);
                            const obsBodyFwd = -toObsX * sinY0 - toObsZ * cosY0;
                            const obsBodyRight = toObsX * cosY0 - toObsZ * sinY0;
                            if (obsBodyFwd > 0.6 && obsBodyFwd < 3.6 && Math.abs(obsBodyRight) < 1.4 && !isApproachingGate) {{
                                detectedNarrowSlit = true;
                                if (obsBodyFwd < slitDist) {{
                                    slitDist = obsBodyFwd;
                                    slitRollSign = (obsBodyRight > 0) ? -1.0 : 1.0;
                                }}
                            }}
                        }}
                    }});

                    // Trigger Knife-Edge Slit Sprint Mode
                    if (detectedNarrowSlit && slitDist < 2.6 && !isTiltedSlitSprint) {{
                        isTiltedSlitSprint = true;
                        slitSprintRollTarget = slitRollSign * 1.0; // ~57.3 deg knife-edge roll
                        slitSprintTimer = 0.95; // ~1 sec sprint to clear narrow gap
                        showToast('⚡ 狹縫可行性預判通過！機身側傾 58° 刀鋒彈射加速穿障 (Knife-Edge Sprint)！');
                    }}

                    if (slitSprintTimer > 0) {{
                        slitSprintTimer -= 0.016;
                        if (slitSprintTimer <= 0) {{
                            isTiltedSlitSprint = false;
                        }}
                    }}

                    // During narrow slit sprint, maintain centering repulsion to avoid wall clipping
                    if (isTiltedSlitSprint) {{
                        repelX *= 0.5;
                        repelZ *= 0.5;
                    }}

                    // Boundary Repulsion
                    if (drone.position.x > 14) repelX -= Math.pow((drone.position.x - 14) / 4, 2) * 3.0;
                    if (drone.position.x < -14) repelX += Math.pow((-14 - drone.position.x) / 4, 2) * 3.0;
                    if (drone.position.z > 14) repelZ -= Math.pow((drone.position.z - 14) / 4, 2) * 3.0;
                    if (drone.position.z < -14) repelZ += Math.pow((-14 - drone.position.z) / 4, 2) * 3.0;

                    let desVx = attractX + repelX;
                    let desVz = attractZ + repelZ;

                    // 4. LiDAR Gate Passage Deadzone Filter
                    if (!isApproachingGate && !isTiltedSlitSprint && latestLiDARReading.dist < 1.4) {{
                        const damp = Math.max(0.4, latestLiDARReading.dist / 1.4);
                        desVx *= damp;
                        desVz *= damp;
                    }}

                    // 5. Project onto Body Frame (World Forward [-sinY, -cosY], World Right [cosY, -sinY])
                    const cosY = Math.cos(yaw);
                    const sinY = Math.sin(yaw);
                    const bodyFwd = -desVx * sinY - desVz * cosY;
                    const bodyRight = desVx * cosY - desVz * sinY;
                    const actualFwd = -velocity.x * sinY - velocity.z * cosY;
                    const actualRight = velocity.x * cosY - velocity.z * sinY;
                    const errFwd = bodyFwd - actualFwd;
                    const errRight = bodyRight - actualRight;

                    // Check if Student Neural Policy is available (FEAT-M2.5.2)
                    let neuralAct = null;
                    if (typeof studentStages !== 'undefined' && studentStages && studentStages[currentStudentStageKey]) {{
                        try {{
                            const obs23 = [
                                drone.position.x / 20.0, drone.position.y / 10.0, drone.position.z / 20.0,
                                velocity.x / 10.0, velocity.y / 10.0, velocity.z / 10.0,
                                pitch, roll, yaw / Math.PI,
                                rotationSpeed * 10.0, 0.0, 0.0
                            ];
                            // 8 LiDAR readings normalized to 12.0m
                            if (typeof droneLiDARReadings !== 'undefined' && droneLiDARReadings && droneLiDARReadings.length === 8) {{
                                for (let r = 0; r < 8; r++) obs23.push(Math.min(1.0, droneLiDARReadings[r].dist / 12.0));
                            }} else {{
                                for (let r = 0; r < 8; r++) obs23.push(Math.min(1.0, latestLiDARReading.dist / 12.0));
                            }}
                            obs23.push(relX / 20.0, relY / 10.0, relZ / 20.0);
                            neuralAct = predictStudentNeural(obs23, studentStages[currentStudentStageKey]);
                        }} catch (e) {{
                            console.warn('Neural inference error:', e);
                            neuralAct = null;
                        }}
                    }}

                    // Common Yaw and Altitude Error (Hoisted for all policy stages)
                    const desiredYaw = Math.atan2(-toLeadX, -toLeadZ);
                    const yawErr = (desiredYaw - yaw + Math.PI) % (2 * Math.PI) - Math.PI;
                    const altErr = targetAlt - drone.position.y;

                    // Second-order S-Curve Yaw Rate Limiter (Task Group 2)
                    let targetRotSpeed = 0;
                    if (!isApproachingGate && latestLiDARReading.dist < 1.8 && (latestLiDARReading.direction.includes('前') || latestLiDARReading.direction.includes('舷'))) {{
                        targetRotSpeed = latestLiDARReading.direction.includes('左') ? -0.07 : 0.07;
                    }} else {{
                        targetRotSpeed = Math.max(-0.09, Math.min(0.09, yawErr * 0.08));
                    }}
                    aiYawRateSmoothed += Math.max(-0.012, Math.min(0.012, targetRotSpeed - aiYawRateSmoothed));
                    rotationSpeed = aiYawRateSmoothed;

                    // Coordinated Banking Turn Angle (Aerodynamic centrifugal tilt)
                    const coordinatedRoll = Math.max(-0.32, Math.min(0.32, (actualFwd * rotationSpeed * 1.6) / 9.81));

                    if (currentStudentStageKey === 'stage_0_untrained' && neuralAct) {{
                        // Stage 0: Untrained random network - chaotic drift, low obstacle awareness
                        rawPitchCmd = Math.max(-0.85, Math.min(0.85, neuralAct[0] * 1.2));
                        rawRollCmd = Math.max(-0.85, Math.min(0.85, neuralAct[1] * 1.2));
                        targetPitch = rawPitchCmd * 0.70;
                        targetRoll = rawRollCmd * 0.70 + coordinatedRoll;
                        throttleAcc = Math.max(-6.0, Math.min(14.0, altErr * 1.8 - velocity.y * 1.2 + neuralAct[3] * 6.0));
                        aiConfidence = 45.0;
                    }} else if (currentStudentStageKey === 'stage_1_half_trained' && neuralAct) {{
                        // Stage 1: Half-trained network - partial obstacle evasion, slight wobble
                        rawPitchCmd = Math.max(-0.75, Math.min(0.75, neuralAct[0] * 0.6 + (-errFwd * 0.45) * 0.4));
                        rawRollCmd = Math.max(-0.75, Math.min(0.75, neuralAct[1] * 0.6 + (-errRight * 0.45) * 0.4));
                        targetPitch = rawPitchCmd * 0.70;
                        targetRoll = rawRollCmd * 0.70 + coordinatedRoll;
                        throttleAcc = Math.max(-6.0, Math.min(14.0, altErr * 2.5 - velocity.y * 1.5 + neuralAct[3] * 3.0));
                        aiConfidence = 78.5;
                    }} else {{
                        // Stage 2: Mastered - full agile APF + neural blend
                        rawPitchCmd = Math.max(-0.95, Math.min(0.95, -errFwd * 0.55));
                        rawRollCmd = Math.max(-0.85, Math.min(0.85, -errRight * 0.50));

                        // Dynamic Max Pitch for Straightaways vs Precision Gates
                        const maxPitchLimit = (aiNavStage === 'APPROACH' && distToApproach > 3.0) ? 0.48 : (isApproachingGate ? 0.20 : 0.38);
                        targetPitch = Math.max(-maxPitchLimit, Math.min(maxPitchLimit, rawPitchCmd * 0.75));

                        // Coordinated Banking Roll + Lateral Evasion
                        targetRoll = Math.max(-0.45, Math.min(0.45, rawRollCmd * 0.70 + coordinatedRoll));

                        // Precision Gate Attitude Leveling Constraint
                        if (isApproachingGate) {{
                            targetPitch = Math.max(-0.20, Math.min(0.20, targetPitch));
                            targetRoll = Math.max(-0.14, Math.min(0.14, targetRoll));
                        }}

                        // Tilted Slit Sprint Override (Task Group 3)
                        if (isTiltedSlitSprint) {{
                            targetRoll = slitSprintRollTarget;
                            targetPitch = -0.32;
                            throttleAcc = Math.max(-2.0, Math.min(14.0, altErr * 3.8 - velocity.y * 1.8));
                            aiConfidence = 99.5;
                        }} else {{
                            // Damped Altitude Hold & Vertical Climb Control
                            throttleAcc = Math.max(-6.0, Math.min(14.0, altErr * 3.8 - velocity.y * 1.8));
                            aiConfidence = isApproachingGate ? 98.8 : Math.max(50.0, Math.min(99.6, 98.5 - (3.0 - Math.min(3.0, latestLiDARReading.dist)) * 12.0));
                        }}
                    }}
                    aiCumulativeReward += 0.05;
                }}

                // Update Dynamic Trajectory Line (Drone position -> Target Lead/Waypoint)
                if (trajectoryLine && trajectoryLine.geometry) {{
                    const posArr = trajectoryLine.geometry.attributes.position.array;
                    posArr[0] = drone.position.x; posArr[1] = drone.position.y; posArr[2] = drone.position.z;
                    posArr[3] = (typeof leadX !== 'undefined') ? leadX : targetGate.x;
                    posArr[4] = (typeof targetAlt !== 'undefined') ? targetAlt : targetGate.y;
                    posArr[5] = (typeof leadZ !== 'undefined') ? leadZ : targetGate.z;
                    trajectoryLine.geometry.attributes.position.needsUpdate = true;
                    trajectoryLine.geometry.computeBoundingSphere();
                    trajectoryLine.frustumCulled = false;
                }}
            }} else {{
                // Manual Keyboard Controls with Expo Input Shaping (Gentle micro-trim on tap, 40.1 deg sprint on hold)
                if (keys['KeyW']) rawPitchCmd -= 1.0;
                if (keys['KeyS']) rawPitchCmd += 1.0;
                if (keys['KeyA']) rawRollCmd += 1.0;
                if (keys['KeyD']) rawRollCmd -= 1.0;

                // Shared Autonomy Copilot Multi-Tier Blending (Milestone M2.6)
                let copilotSafeP = rawPitchCmd;
                let copilotSafeR = rawRollCmd;

                if (isCopilotActive && !isCatastrophic && latestLiDARReading && latestLiDARReading.dist < 2.5 && latestLiDARReading.name !== '地面 (Ground)') {{
                    const curDist = latestLiDARReading.dist;
                    const invQuat = drone.quaternion.clone().invert();
                    const dirVec = latestLiDARReading.point.clone().sub(drone.position);
                    const localDir = dirVec.applyQuaternion(invQuat);
                    const dHz = Math.hypot(localDir.x, localDir.z);

                    if (dHz > 0.01) {{
                        // In body frame: Forward is -localDir.z, Right is +localDir.x
                        const obsFwd = -localDir.z / dHz;
                        const obsRight = localDir.x / dHz;

                        // Pilot command in body frame: KeyW (rawPitchCmd < 0) is forward, KeyD (rawRollCmd < 0) is right
                        const pilotFwd = -rawPitchCmd;
                        const pilotRight = -rawRollCmd;
                        const approachDot = pilotFwd * obsFwd + pilotRight * obsRight;
                        const humanEscaping = approachDot <= 0.05;

                        // Approach speed & TTC
                        const approachSpeed = Math.max(0, approachDot) * 4.8;
                        copilotTTC = approachSpeed > 0.1 ? (curDist / approachSpeed) : 999.0;

                        if (curDist >= 2.0 && (copilotTTC > 2.0 || curDist >= 3.0)) {{
                            copilotLevel = 'STANDBY';
                            copilotInterventionBeta = 0.0;
                        }} else if (curDist >= 1.2) {{
                            copilotLevel = 'WARNING';
                            const normW = Math.max(0, Math.min(1.0, (curDist - 1.2) / 0.8));
                            const damp = 0.40 + 0.60 * normW;
                            copilotInterventionBeta = humanEscaping ? 0.0 : (1.0 - damp);

                            if (!humanEscaping) {{
                                const appFwd = approachDot * obsFwd;
                                const appRight = approachDot * obsRight;
                                const latFwd = pilotFwd - appFwd;
                                const latRight = pilotRight - appRight;
                                const safeFwd = latFwd + appFwd * damp;
                                const safeRight = latRight + appRight * damp;
                                copilotSafeP = -safeFwd;
                                copilotSafeR = -safeRight;
                            }}
                        }} else {{
                            // Emergency Zone: Active APF Repulsion and Tangential Slide Deflection
                            copilotLevel = 'DEFLECTING';
                            const normE = Math.max(0, Math.min(1.0, (curDist - 0.5) / 0.7));
                            copilotInterventionBeta = 0.55 + 0.45 * (1.0 - normE);

                            const repelMag = Math.pow((1.2 - curDist) / 1.2, 1.4) * 1.5;
                            const repelFwd = -obsFwd * repelMag;
                            const repelRight = -obsRight * repelMag;

                            const tanFwd = -obsRight;
                            const tanRight = obsFwd;
                            const pilotLat = pilotFwd * tanFwd + pilotRight * tanRight;
                            const tanDir = pilotLat >= 0 ? 1.0 : -1.0;
                            const tanScale = (1.0 - normE) * 0.35;
                            const tanP = tanFwd * tanDir * tanScale;
                            const tanR = tanRight * tanDir * tanScale;

                            if (humanEscaping) {{
                                copilotSafeP = rawPitchCmd - repelFwd * 0.35;
                                copilotSafeR = rawRollCmd - repelRight * 0.35;
                                copilotInterventionBeta = 0.25;
                            }} else {{
                                const blendedFwd = (1.0 - copilotInterventionBeta) * pilotFwd + copilotInterventionBeta * (repelFwd + tanP);
                                const blendedRight = (1.0 - copilotInterventionBeta) * pilotRight + copilotInterventionBeta * (repelRight + tanR);
                                copilotSafeP = -blendedFwd;
                                copilotSafeR = -blendedRight;

                                velocity.x *= 0.94;
                                velocity.z *= 0.94;
                            }}
                        }}
                    }}
                }} else if (!isCopilotActive) {{
                    copilotLevel = 'OFF';
                    copilotInterventionBeta = 0.0;
                    copilotTTC = 999.0;
                }} else {{
                    copilotLevel = 'STANDBY';
                    copilotInterventionBeta = 0.0;
                    copilotTTC = 999.0;
                }}

                rawPitchCmd = Math.max(-1.0, Math.min(1.0, copilotSafeP));
                rawRollCmd = Math.max(-1.0, Math.min(1.0, copilotSafeR));

                if (keys['ArrowUp']) throttleAcc += 14.0;       // Lift / Up (High TWR)
                if (keys['ArrowDown']) throttleAcc -= 9.0;       // Descend
                if (keys['ArrowLeft'] || keys['KeyQ']) rotationSpeed = 0.08;     // Yaw Left (Agile Rate)
                else if (keys['ArrowRight'] || keys['KeyE']) rotationSpeed = -0.08; // Yaw Right (Agile Rate)
                else rotationSpeed = 0;

                if (rawPitchCmd !== 0) {{
                    pitchRamp = Math.min(1.0, pitchRamp + 0.12);
                }} else {{
                    pitchRamp = Math.max(0, pitchRamp - 0.25);
                }}
                targetPitch = rawPitchCmd * 0.70 * (0.35 + 0.65 * (pitchRamp * pitchRamp));
                if (rawPitchCmd === 0) targetPitch = 0;

                if (rawRollCmd !== 0) {{
                    rollRamp = Math.min(1.0, rollRamp + 0.12);
                }} else {{
                    rollRamp = Math.max(0, rollRamp - 0.25);
                }}
                targetRoll = rawRollCmd * 0.70 * (0.35 + 0.65 * (rollRamp * rollRamp));
                if (rawRollCmd === 0) targetRoll = 0;
            }}

            // Apply damage impact on flight dynamics (using hoisted evaluations)
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
                velocity.x *= 0.88; velocity.z *= 0.88;
                if (drone.position.y > 0.05) velocity.y *= 0.85;
            }}

            // High-Agility Attitude Interpolation (80ms convergence)
            pitch += (targetPitch - pitch) * 0.25;
            roll += (targetRoll - roll) * 0.25;
            yaw += rotationSpeed;

            // Standard Aerospace Attitude Interpolation & Heading Order (Yaw -> Pitch -> Roll)
            drone.rotation.order = 'YXZ';
            drone.rotation.set(pitch, yaw, roll, 'YXZ');

            // True 3D Thrust Vector (Multi-rotor thrust along body local UP [0, 1, 0])
            const thrustVector = new THREE.Vector3(0, 1, 0).applyEuler(drone.rotation);

            // Thrust Vectoring & Tilt Compensation with damage degradation
            const gravity = 9.81;
            const tiltMagnitude = Math.sqrt(pitch * pitch + roll * roll);
            const tiltCompensation = 1.0 / Math.max(Math.cos(Math.min(tiltMagnitude, 0.70)), 0.50);
            const hoverBase = (drone.position.y > 0.055 || throttleAcc > 0) ? 9.81 : 0;
            const nominalLift = (hoverBase + throttleAcc) * tiltCompensation;
            const effectiveLift = nominalLift * (0.15 + 0.85 * intactRatio);

            velocity.y += (effectiveLift * thrustVector.y - gravity) * 0.016;

            // Horizontal thrust components from tilted rotor plane (Exact projection in world frame)
            const windX = currentWind[0];
            const thrustMultiplier = 15.5 * (0.3 + 0.7 * intactRatio);
            velocity.x += (thrustVector.x * thrustMultiplier + windX * 0.2) * 0.016;
            velocity.z += (thrustVector.z * thrustMultiplier) * 0.016;

            // Air Drag & Active Leveling Braking Damping
            const hasDirectionalInput = (rawPitchCmd !== 0 || rawRollCmd !== 0);
            if (!hasDirectionalInput && !isCatastrophic) {{
                // Active Leveling Braking (Neutral stick damping to prevent ice-sliding overshoot)
                velocity.x *= 0.935;
                velocity.z *= 0.935;
            }} else {{
                velocity.x *= 0.978;
                velocity.z *= 0.978;
            }}
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
                    // Bouncing physics with Positional Depenetration (Anti-Stuck Resolution)
                    const minOverlapX = Math.min(droneBox.max.x - obs.box.min.x, obs.box.max.x - droneBox.min.x);
                    const minOverlapY = Math.min(droneBox.max.y - obs.box.min.y, obs.box.max.y - droneBox.min.y);
                    const minOverlapZ = Math.min(droneBox.max.z - obs.box.min.z, obs.box.max.z - droneBox.min.z);
                    const minOverlap = Math.min(minOverlapX, minOverlapY, minOverlapZ);
                    const pushMargin = 0.05;

                    if (minOverlap === minOverlapX) {{
                        const pushDir = (drone.position.x > (obs.box.min.x + obs.box.max.x) / 2) ? 1 : -1;
                        drone.position.x += pushDir * (minOverlapX + pushMargin);
                        velocity.x = -velocity.x * 0.45 + pushDir * 0.6;
                    }} else if (minOverlap === minOverlapZ) {{
                        const pushDir = (drone.position.z > (obs.box.min.z + obs.box.max.z) / 2) ? 1 : -1;
                        drone.position.z += pushDir * (minOverlapZ + pushMargin);
                        velocity.z = -velocity.z * 0.45 + pushDir * 0.6;
                    }} else {{
                        const pushDir = (drone.position.y > (obs.box.min.y + obs.box.max.y) / 2) ? 1 : -1;
                        drone.position.y += pushDir * (minOverlapY + pushMargin);
                        velocity.y = -velocity.y * 0.45 + pushDir * 0.4;
                    }}
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

            // 8. Rangefinder / LiDAR Proximity Sensing & Directional Heading Computation
            let nearestDist = 999.0;
            let nearestPt = new THREE.Vector3();
            let nearestObjName = '無障礙物';
            const dronePos = drone.position.clone();
            const tempPt = new THREE.Vector3();

            // Ground distance check
            const groundDist = Math.max(0, dronePos.y - 0.05);
            if (groundDist < nearestDist) {{
                nearestDist = groundDist;
                nearestPt.set(dronePos.x, 0.02, dronePos.z);
                nearestObjName = '地面 (Ground)';
            }}

            // Check all active scenario obstacles
            activeObstacles.forEach(obs => {{
                obs.box.clampPoint(dronePos, tempPt);
                const d = dronePos.distanceTo(tempPt);
                if (d < nearestDist) {{
                    nearestDist = d;
                    nearestPt.copy(tempPt);
                    nearestObjName = obs.name || '剛體障礙物';
                }}
            }});

            // Calculate relative body direction using inverse quaternion
            const dirVec = nearestPt.clone().sub(dronePos);
            const invQuat = drone.quaternion.clone().invert();
            const localDir = dirVec.clone().applyQuaternion(invQuat);

            let dirLabel = '周圍';
            if (nearestObjName === '地面 (Ground)') {{
                dirLabel = '正下方 ⬇️';
            }} else {{
                const isFront = localDir.z < -0.25;
                const isBack = localDir.z > 0.25;
                const isLeft = localDir.x < -0.25;
                const isRight = localDir.x > 0.25;
                const isAbove = localDir.y > 0.35;
                const isBelow = localDir.y < -0.35;

                if (isAbove) dirLabel = '正上方 ⬆️';
                else if (isBelow) dirLabel = '下方 ⬇️';
                else if (isFront && isLeft) dirLabel = '前偏左 ↖️';
                else if (isFront && isRight) dirLabel = '前偏右 ↗️';
                else if (isBack && isLeft) dirLabel = '後偏左 ↙️';
                else if (isBack && isRight) dirLabel = '後偏右 ↘️';
                else if (isFront) dirLabel = '正前方 ⬆️';
                else if (isBack) dirLabel = '正後方 ⬇️';
                else if (isLeft) dirLabel = '正左舷 ⬅️';
                else if (isRight) dirLabel = '正右舷 ➡️';
                else dirLabel = '近距掠過 ⚡';
            }}

            latestLiDARReading = {{
                dist: nearestDist,
                name: nearestObjName,
                direction: dirLabel,
                point: nearestPt.clone()
            }};

            // Update 3D Laser Ray & Obstacle Contact Reticle
            if (nearestDist <= 12.0 && !isCatastrophic) {{
                laserRayLine.visible = true;
                laserDotMesh.visible = true;

                const sensorWorldPos = new THREE.Vector3(0, 0.16, 0).applyMatrix4(drone.matrixWorld);
                const posArr = laserRayLine.geometry.attributes.position.array;
                posArr[0] = sensorWorldPos.x; posArr[1] = sensorWorldPos.y; posArr[2] = sensorWorldPos.z;
                posArr[3] = nearestPt.x; posArr[4] = nearestPt.y; posArr[5] = nearestPt.z;
                laserRayLine.geometry.attributes.position.needsUpdate = true;

                laserDotMesh.position.copy(nearestPt);

                let rayHex = 0x22c55e;
                if (nearestDist < 0.9) rayHex = 0xff1744;
                else if (nearestDist < 2.0) rayHex = 0xfacc15;

                laserRayMat.color.setHex(rayHex);
                laserDotMat.color.setHex(rayHex);
            }} else {{
                laserRayLine.visible = false;
                laserDotMesh.visible = false;
            }}

            // Update HUD Proximity Telemetry
            const distEl = document.getElementById('st-nearest-dist');
            const nameEl = document.getElementById('st-nearest-name');
            const dirEl = document.getElementById('st-nearest-dir');
            const barEl = document.getElementById('st-proximity-bar');
            const proxAlertEl = document.getElementById('st-proximity-alert');

            if (distEl) {{
                distEl.innerText = nearestDist.toFixed(2) + ' m';
                if (nameEl) nameEl.innerText = nearestObjName;
                if (dirEl) dirEl.innerText = dirLabel;

                const barFillPct = Math.max(0, Math.min(100, ((3.0 - Math.min(3.0, nearestDist)) / 3.0) * 100));
                if (barEl) {{
                    barEl.style.width = barFillPct + '%';
                    if (nearestDist < 0.8) {{
                        distEl.style.color = '#ff1744';
                        barEl.style.background = '#ff1744';
                        if (proxAlertEl) proxAlertEl.style.display = 'block';
                    }} else if (nearestDist < 1.8) {{
                        distEl.style.color = '#facc15';
                        barEl.style.background = '#facc15';
                        if (proxAlertEl) proxAlertEl.style.display = 'none';
                    }} else {{
                        distEl.style.color = '#4ade80';
                        barEl.style.background = '#22c55e';
                        if (proxAlertEl) proxAlertEl.style.display = 'none';
                    }}
                }}
            }}

            // Update AI Autopilot HUD Telemetry
            const gateEl = document.getElementById('ai-target-gate');
            const lapsEl = document.getElementById('ai-laps');
            const confEl = document.getElementById('ai-confidence');
            const rewEl = document.getElementById('ai-reward');
            if (gateEl) gateEl.innerText = aiGates[currentAIGateIndex].label;
            if (lapsEl) lapsEl.innerText = aiLapsCompleted + ' 圈';
            if (confEl) confEl.innerText = aiConfidence.toFixed(1) + '%';
            if (rewEl) rewEl.innerText = (aiCumulativeReward >= 0 ? '+' : '') + aiCumulativeReward.toFixed(1);

            // Update Shared Autonomy Copilot HUD Telemetry (Milestone M2.6)
            const copBadge = document.getElementById('copilot-status-badge');
            const copModeText = document.getElementById('copilot-mode-text');
            const copBeta = document.getElementById('copilot-beta');
            const copTtc = document.getElementById('copilot-ttc');

            if (copBadge) {{
                if (!isCopilotActive) {{
                    copBadge.className = 'copilot-indicator copilot-standby';
                    copBadge.innerText = '○ OFF';
                    if (copModeText) copModeText.innerText = '副駕駛已關閉 (OFF)';
                    if (copBeta) copBeta.innerText = '0.0%';
                    if (copTtc) copTtc.innerText = '-- s';
                }} else if (isAIAutopilotActive) {{
                    copBadge.className = 'copilot-indicator copilot-standby';
                    copBadge.innerText = '🛡️ BACKUP';
                    if (copModeText) copModeText.innerText = 'AI 主飛副駕待命 (BACKUP)';
                    if (copBeta) copBeta.innerText = '0.0%';
                    if (copTtc) copTtc.innerText = '-- s';
                }} else {{
                    if (copilotLevel === 'DEFLECTING') {{
                        copBadge.className = 'copilot-indicator copilot-deflect';
                        copBadge.innerText = '🛡️ DEFLECTING';
                        if (copModeText) copModeText.innerText = '主動避障排斥 (DEFLECTING)';
                    }} else if (copilotLevel === 'WARNING') {{
                        copBadge.className = 'copilot-indicator copilot-warning';
                        copBadge.innerText = '⚠️ WARNING';
                        if (copModeText) copModeText.innerText = '警戒阻尼箝位 (DAMPING)';
                    }} else {{
                        copBadge.className = 'copilot-indicator copilot-standby';
                        copBadge.innerText = '● STANDBY';
                        if (copModeText) copModeText.innerText = '待命守護 (STANDBY)';
                    }}
                    if (copBeta) copBeta.innerText = (copilotInterventionBeta * 100).toFixed(1) + '%';
                    if (copTtc) copTtc.innerText = (copilotTTC > 50.0 || copilotTTC === 999.0) ? '-- s' : copilotTTC.toFixed(1) + ' s';
                }}
            }}

            // Update 3D Copilot Virtual Bumper Halo Visuals
            if (typeof copilotHalo !== 'undefined' && copilotHalo) {{
                if (isCopilotActive && !isCatastrophic) {{
                    copilotHalo.visible = true;
                    if (!isAIAutopilotActive && copilotLevel === 'DEFLECTING') {{
                        copilotHalo.material.color.setHex(0xf43f5e);
                        copilotHalo.material.opacity = 0.85 + 0.15 * Math.sin(performance.now() * 0.02);
                        copilotHalo.scale.set(1.18, 1.18, 1.18);
                    }} else if (!isAIAutopilotActive && copilotLevel === 'WARNING') {{
                        copilotHalo.material.color.setHex(0xfacc15);
                        copilotHalo.material.opacity = 0.55 + 0.15 * Math.sin(performance.now() * 0.01);
                        copilotHalo.scale.set(1.06, 1.06, 1.06);
                    }} else {{
                        copilotHalo.material.color.setHex(0x00e5ff);
                        copilotHalo.material.opacity = 0.25;
                        copilotHalo.scale.set(1.0, 1.0, 1.0);
                    }}
                }} else {{
                    copilotHalo.visible = false;
                }}
            }}
        }}

        // 7. Animation Loop with Real-time Environment FX & Dynamic Particle Lifecycle
        function animate() {{
            requestAnimationFrame(animate);
            const elapsedTime = clock.getElapsedTime();

            // Dynamic Sensor & Beacon Effects
            if (lidarScanRing) {{
                lidarScanRing.rotation.z += 0.08;
            }}
            if (tailBeaconLight) {{
                tailBeaconLight.intensity = (Math.sin(elapsedTime * 9.0) > 0.3 ? 1.4 : 0.1);
            }}

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
        html_content = html_content.replace("__STUDENT_STAGES_PLACEHOLDER__", stages_json_str)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_path


if __name__ == "__main__":
    output = Path(__file__).parent / "output"
    sim = WebGLFlightSimulator(output)

    sample_drone = {
        "design_id": "evolved_agile_confined_v2",
        "aircraft_type": "multirotor",
        "num_arms": 4,
        "arm_length_m": 0.20,
        "motor_id": "m_2212_920kv",
        "prop_id": "p_1045",
        "battery_id": "b_3s_1500mah",
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
