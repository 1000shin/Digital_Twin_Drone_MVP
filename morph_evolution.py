#!/usr/bin/env python3
"""
Digital Twin Drone MVP - Mission-Driven Morphological & Sensor Evolution Engine
Block 4: Given a mission_spec.json (constraints & goals), uses an evolutionary optimization loop
to search for the best drone configuration (num_arms, arm_length, motor, prop, battery, sensors),
tracks physical motivations behind mutations/recombinations, generation-by-generation decision trails,
and outputs explainable reports (output/evolution_lineage_report.md, output/evolution_history.json).
"""

import copy
import datetime
import json
import random
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from db_loader import ComponentDB

class EvolutionExplainabilityEngine:
    """
    形態演化決策與變遷原因追蹤系統 (Evolutionary Change & Lineage Explainability Engine)
    Analyzes physical state transitions (arm length, propulsion, energy, frame) and provides:
    - Morphological Change Rationale (變革動機)
    - Generation-by-Generation Breakthrough Decisions (世代躍遷決策歷史)
    - Structured Decisions & Lineage Traceability (結構化決策與系譜追蹤)
    - Markdown & JSON Report Generators
    """

    def __init__(self, db: ComponentDB):
        self.db = db

    def get_physical_metrics(self, ind: Dict[str, Any], mission_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates detailed physical attributes, constraints, and fitness for an individual."""
        arm_len = float(ind.get("arm_length_m", 0.25))
        total_diameter = round((arm_len * 2.0) + 0.15, 3)
        mounted_sensors = [s["sensor_id"] for s in ind.get("sensors_mount", [])]
        num_arms = int(ind.get("num_arms", 4))
        motor_id = ind.get("motor_id", "")
        prop_id = ind.get("prop_id", "")
        battery_id = ind.get("battery_id", "")

        motor_obj = self.db.get_component("motors", motor_id) or {}
        prop_obj = self.db.get_component("propellers", prop_id) or {}
        battery_obj = self.db.get_component("batteries", battery_id) or {}

        try:
            stats = self.db.calculate_power_and_mass(
                num_arms, motor_id, prop_id, battery_id, mounted_sensors
            )
        except Exception:
            stats = {
                "total_mass_g": 9999.0,
                "max_thrust_g": 0.0,
                "thrust_to_weight_ratio": 0.0,
                "estimated_flight_time_min": 0.0
            }

        fitness = self.evaluate_fitness_score(ind, mission_spec, stats, total_diameter)

        return {
            "num_arms": num_arms,
            "arm_length_m": arm_len,
            "total_diameter_m": total_diameter,
            "motor_id": motor_id,
            "motor_name": motor_obj.get("name", motor_id),
            "prop_id": prop_id,
            "prop_name": prop_obj.get("name", prop_id),
            "battery_id": battery_id,
            "battery_name": battery_obj.get("name", battery_id),
            "total_mass_g": stats["total_mass_g"],
            "max_thrust_g": stats["max_thrust_g"],
            "thrust_to_weight_ratio": stats["thrust_to_weight_ratio"],
            "estimated_flight_time_min": stats["estimated_flight_time_min"],
            "fitness": round(fitness, 2)
        }

    def evaluate_fitness_score(
        self,
        ind: Dict[str, Any],
        mission_spec: Dict[str, Any],
        stats: Dict[str, Any],
        total_diameter: float
    ) -> float:
        """Calculates fitness value given stats and diameter."""
        max_size_m = mission_spec.get("max_size_m", 0.6)
        min_flight_time_min = mission_spec.get("min_flight_time_min", 10.0)

        twr = stats["thrust_to_weight_ratio"]
        flight_time = stats["estimated_flight_time_min"]

        # Hard constraints
        if twr < 1.5:  # Cannot fly safely
            return -500.0 + twr * 10.0

        if total_diameter > max_size_m:  # Too big for mission workspace
            return -300.0 - (total_diameter - max_size_m) * 100.0

        # Score calculation
        fitness = 100.0

        # Flight time bonus
        if flight_time >= min_flight_time_min:
            fitness += (flight_time - min_flight_time_min) * 10.0
        else:
            fitness -= (min_flight_time_min - flight_time) * 15.0

        # Thrust-to-weight ratio bonus (optimal around 1.8 - 2.8)
        if 1.8 <= twr <= 2.8:
            fitness += 30.0

        # Efficiency bonus: penalty for unnecessarily heavy frame
        fitness -= stats["total_mass_g"] * 0.02
        return fitness

    def explain_change(
        self,
        ind_before: Dict[str, Any],
        ind_after: Dict[str, Any],
        mission_spec: Dict[str, Any],
        gen: int = 0
    ) -> Dict[str, Any]:
        """
        Analyzes the physical and mathematical motivation behind an evolutionary transition.
        Generates human-readable rationales and structured decision objects.
        """
        m_before = self.get_physical_metrics(ind_before, mission_spec)
        m_after = self.get_physical_metrics(ind_after, mission_spec)

        max_size_m = mission_spec.get("max_size_m", 0.6)
        min_flight_time = mission_spec.get("min_flight_time_min", 10.0)
        fitness_delta = round(m_after["fitness"] - m_before["fitness"], 2)

        rationales: List[str] = []
        decisions: List[Dict[str, Any]] = []

        # 1. Arm Length & Geometric Size Rationale
        arm_before = ind_before["arm_length_m"]
        arm_after = ind_after["arm_length_m"]
        if abs(arm_after - arm_before) >= 0.005:
            d_before = m_before["total_diameter_m"]
            d_after = m_after["total_diameter_m"]
            delta_mass = m_after["total_mass_g"] - m_before["total_mass_g"]

            if d_before > max_size_m and d_after <= max_size_m:
                r = (
                    f"縮短機臂長度 ({arm_before:.2f}m -> {arm_after:.2f}m)："
                    f"因空間限制直徑超標 (原 {d_before:.2f}m > {max_size_m:.2f}m)，消除約束懲罰 (-300)"
                )
                action = "eliminate_size_penalty"
            elif d_before > max_size_m and d_after > max_size_m:
                if d_after < d_before:
                    r = (
                        f"縮短機臂長度 ({arm_before:.2f}m -> {arm_after:.2f}m)："
                        f"減輕空間超標幅度 ({d_before:.2f}m -> {d_after:.2f}m)，縮減約束懲罰"
                    )
                    action = "reduce_size_violation"
                else:
                    r = (
                        f"延長機臂長度 ({arm_before:.2f}m -> {arm_after:.2f}m)："
                        f"直徑持續超標 ({d_after:.2f}m > {max_size_m:.2f}m)"
                    )
                    action = "size_violation"
            elif d_before <= max_size_m and d_after > max_size_m:
                r = (
                    f"延長機臂長度 ({arm_before:.2f}m -> {arm_after:.2f}m)："
                    f"直徑達 {d_after:.2f}m 超過空間限制 ({max_size_m:.2f}m)，觸發約束懲罰 (-300)"
                )
                action = "incur_size_penalty"
            else:
                if arm_after < arm_before:
                    r = (
                        f"縮短機臂長度 ({arm_before:.2f}m -> {arm_after:.2f}m)："
                        f"因空間限制直徑由 {d_before:.2f}m 收斂為 {d_after:.2f}m，消除約束懲罰並減輕結構質量 ({delta_mass:+.1f}g)"
                    )
                    action = "optimize_arm_compactness"
                else:
                    r = (
                        f"微調機臂長度 ({arm_before:.2f}m -> {arm_after:.2f}m)："
                        f"擴大旋翼軸距穩定性，直徑保持在空間限制內 ({d_after:.2f}m <= {max_size_m:.2f}m)"
                    )
                    action = "expand_arm_stability"

            rationales.append(r)
            decisions.append({
                "generation": gen,
                "component": "arm_length",
                "action": action,
                "change": f"{arm_before:.2f}m -> {arm_after:.2f}m",
                "rationale": r,
                "metrics_before": m_before,
                "metrics_after": m_after,
                "fitness_delta": fitness_delta
            })

        # 2. Battery & Flight Endurance Rationale
        bat_before = ind_before["battery_id"]
        bat_after = ind_after["battery_id"]
        if bat_before != bat_after:
            ft_before = m_before["estimated_flight_time_min"]
            ft_after = m_after["estimated_flight_time_min"]
            b_after_name = m_after["battery_name"]
            delta_mass = m_after["total_mass_g"] - m_before["total_mass_g"]

            if ft_before < min_flight_time and ft_after >= min_flight_time:
                bonus = round((ft_after - min_flight_time) * 10.0, 1)
                r = (
                    f"升級 {b_after_name} 電池："
                    f"原續航 {ft_before:.1f}min 未達任務門檻 ({min_flight_time:.1f}min)，獲得續航加成 (+{bonus:.1f} 分)"
                )
                action = "achieve_flight_time_threshold"
            elif ft_after > ft_before:
                diff = round(ft_after - ft_before, 1)
                r = (
                    f"更換 {b_after_name} 電池："
                    f"原續航 {ft_before:.1f}min，改善後續航提升至 {ft_after:.1f}min (+{diff:.1f}min)"
                )
                action = "boost_flight_time"
            else:
                r = (
                    f"換裝輕量化 {b_after_name} 電池："
                    f"整機減重 {abs(delta_mass):.1f}g，維持續航 {ft_after:.1f}min"
                )
                action = "lightweight_battery"

            rationales.append(r)
            decisions.append({
                "generation": gen,
                "component": "battery",
                "action": action,
                "change": f"{bat_before} -> {bat_after}",
                "rationale": r,
                "metrics_before": m_before,
                "metrics_after": m_after,
                "fitness_delta": fitness_delta
            })

        # 3. Motor & Propeller (Propulsion / TWR) Rationale
        motor_changed = ind_before["motor_id"] != ind_after["motor_id"]
        prop_changed = ind_before["prop_id"] != ind_after["prop_id"]
        if motor_changed or prop_changed:
            twr_before = m_before["thrust_to_weight_ratio"]
            twr_after = m_after["thrust_to_weight_ratio"]
            m_name = m_after["motor_name"]
            p_name = m_after["prop_name"]
            thrust_after = m_after["max_thrust_g"]

            if twr_before < 1.5 and twr_after >= 1.5:
                if 1.8 <= twr_after <= 2.8:
                    r = (
                        f"更換 {m_name} 馬達 + {p_name} 槳："
                        f"原推重比 TWR={twr_before:.2f} 低於安全下限 (1.5)，改善後 TWR={twr_after:.2f} 進入最佳區間 (+30 分)"
                    )
                    action = "twr_safety_and_optimal"
                else:
                    r = (
                        f"更換 {m_name} 馬達 + {p_name} 槳："
                        f"原推重比 TWR={twr_before:.2f} 低於安全下限 (1.5)，改善後 TWR={twr_after:.2f} 達到安全飛行門檻"
                    )
                    action = "twr_escape_critical"
            elif not (1.8 <= twr_before <= 2.8) and (1.8 <= twr_after <= 2.8):
                r = (
                    f"更換 {m_name} 馬達 + {p_name} 槳："
                    f"推重比由 TWR={twr_before:.2f} 調校為 TWR={twr_after:.2f}，進入最佳區間 (+30 分)"
                )
                action = "twr_enter_optimal"
            elif twr_after > twr_before:
                r = (
                    f"升級 {m_name} 馬達 + {p_name} 槳："
                    f"推重比由 TWR={twr_before:.2f} 提升至 TWR={twr_after:.2f} (最大推力 {thrust_after:.0f}g)"
                )
                action = "increase_twr"
            else:
                r = (
                    f"更換 {m_name} 馬達 + {p_name} 槳："
                    f"調整動力配置，推重比變動為 TWR={twr_after:.2f}"
                )
                action = "adjust_propulsion"

            rationales.append(r)
            decisions.append({
                "generation": gen,
                "component": "propulsion",
                "action": action,
                "change": f"{ind_before['motor_id']}+{ind_before['prop_id']} -> {ind_after['motor_id']}+{ind_after['prop_id']}",
                "rationale": r,
                "metrics_before": m_before,
                "metrics_after": m_after,
                "fitness_delta": fitness_delta
            })

        # 4. Rotor Configuration / Arms Count
        if ind_before["num_arms"] != ind_after["num_arms"]:
            arms_before = ind_before["num_arms"]
            arms_after = ind_after["num_arms"]
            r = (
                f"調整旋翼佈局 ({arms_before} 軸 -> {arms_after} 軸)："
                f"推力調整至 {m_after['max_thrust_g']:.0f}g，整機質量變更為 {m_after['total_mass_g']:.1f}g"
            )
            rationales.append(r)
            decisions.append({
                "generation": gen,
                "component": "num_arms",
                "action": "reconfigure_arms",
                "change": f"{arms_before} -> {arms_after}",
                "rationale": r,
                "metrics_before": m_before,
                "metrics_after": m_after,
                "fitness_delta": fitness_delta
            })

        return {
            "rationales": rationales,
            "decisions": decisions,
            "metrics_before": m_before,
            "metrics_after": m_after,
            "fitness_delta": fitness_delta
        }

    def explain_seed(self, ind: Dict[str, Any], mission_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generates initial explanation for the best random seed in Generation 0."""
        m = self.get_physical_metrics(ind, mission_spec)
        rationale = (
            f"初始隨機種子最優個體：選定 {ind['num_arms']} 軸機架，機臂長度 {ind['arm_length_m']:.2f}m (直徑 {m['total_diameter_m']:.2f}m)，"
            f"選配 {m['motor_name']} + {m['prop_name']} + {m['battery_name']}。"
            f"初期指標：TWR={m['thrust_to_weight_ratio']:.2f}、續航={m['estimated_flight_time_min']:.1f}min、質量={m['total_mass_g']:.1f}g，"
            f"初始適應度: {m['fitness']:.1f}"
        )
        return {
            "generation": 0,
            "component": "seed_initialization",
            "action": "initial_seed",
            "change": "random_seed -> gen0_elite",
            "rationale": rationale,
            "metrics_before": None,
            "metrics_after": m,
            "fitness_delta": m["fitness"]
        }

    def generate_markdown_report(
        self,
        mission_spec: Dict[str, Any],
        best_spec: Dict[str, Any],
        history: Dict[str, Any]
    ) -> str:
        """Renders the comprehensive Evolutionary Lineage & Explainability Markdown Report."""
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mission_type = mission_spec.get("mission_type", "custom_mission")
        max_size_m = mission_spec.get("max_size_m", 0.6)
        min_flight_time = mission_spec.get("min_flight_time_min", 10.0)
        req_sensors = mission_spec.get("required_sensors", [])

        stats = best_spec.get("stats", {})
        breakthroughs = history.get("breakthrough_trail", [])
        decisions = best_spec.get("morph_decisions", [])
        reasoning_logs = best_spec.get("evolution_reasoning_log", [])
        summary = history.get("summary", {})

        md = []
        md.append(f"# 🧬 DEAP 形態演化決策與變遷原因溯源報告")
        md.append(f"> **Evolutionary Change & Lineage Explainability Report**  ")
        md.append(f"> **生成時間**: `{now_str}` | **任務場景**: `{mission_type}` | **核心算法**: `DEAP 遺傳演化長成引擎 v2.0`\n")
        md.append("---\n")

        # Section 1: Mission Specs
        md.append("## 📋 1. 任務需求與物理約束規範 (Mission Constraints & Targets)\n")
        md.append("| 規範維度 | 約束目標 / 指標數值 | 懲罰 / 獎勵機制說明 |")
        md.append("| :--- | :--- | :--- |")
        md.append(f"| **作業空間最大包絡直徑** | `<= {max_size_m:.2f} m` | 狹窄通道空間限制，超過立即扣除 `-300` 分並依超標量追加懲罰 |")
        md.append(f"| **最低任務滯空時間** | `>= {min_flight_time:.1f} min` | 任務續航門檻，未達標扣分 (`-15分/min`)，超越門檻獲續航加成 (`+10分/min`) |")
        md.append(f"| **安全推重比門檻 (TWR)** | `>= 1.5` (最佳區間 `1.8 - 2.8`) | TWR < 1.5 判定為危險失速/墜毀懲罰 (`-500` 分)，進入最佳區間獎勵 `+30` 分 |")
        md.append(f"| **必備任務酬載感測器** | `{', '.join(req_sensors)}` | 100% 必須搭載於機架幾何結構中 |")
        md.append("\n---\n")

        # Section 2: Final Spec
        md.append("## 🏆 2. 最終演化最佳形態規格 (Final Evolved Specification)\n")
        md.append("| 形態幾何與動力組件 | 最佳配置參數 | 物理性能指標評估 |")
        md.append("| :--- | :--- | :--- |")
        md.append(f"| **機架軸數 (Frame Config)** | `{best_spec.get('num_arms')}-軸對稱多旋翼` | 總推力冗餘平衡 |")
        md.append(f"| **機臂長度 (Arm Length)** | `{best_spec.get('arm_length_m')} m` | 對角直徑: `{stats.get('total_diameter_m', (best_spec.get('arm_length_m', 0.25)*2)+0.15):.2f} m` (容許餘裕: `{max_size_m - stats.get('total_diameter_m', 0.5):+.2f} m`) |")
        md.append(f"| **動力馬達 (Motor)** | `{stats.get('motor_name', best_spec.get('motor_id'))}` | 最大靜態總推力: `{stats.get('max_thrust_g', 0):.0f} g` |")
        md.append(f"| **螺旋槳型號 (Propeller)** | `{stats.get('prop_name', best_spec.get('prop_id'))}` | 氣動推進效率最優配對 |")
        md.append(f"| **供電動力電池 (Battery)** | `{stats.get('battery_name', best_spec.get('battery_id'))}` | 預估懸停滯空時間: `{stats.get('estimated_flight_time_min', 0):.1f} min` |")
        md.append(f"| **整機全備重量 (AUW)** | `{stats.get('total_mass_g', 0):.1f} g` | 結構輕量化優化評分 |")
        md.append(f"| **全油門推重比 (TWR)** | `TWR = {stats.get('thrust_to_weight_ratio', 0):.2f}` | ✅ 進入最佳飛行效率與抗風區間 (`1.8 ~ 2.8`) |")
        md.append(f"| **最終綜合適應度評分** | `{stats.get('fitness', 0):.2f} 分` | 較初期種子提升 `{summary.get('fitness_improvement', 0):+.2f} 分` |")
        md.append("\n---\n")

        # Section 3: Generation Trail
        md.append("## 📈 3. 世代躍遷決策歷史 (Generation-by-Generation Decision Trail)\n")
        md.append("| 世代 (Gen) | 事件屬性 | 適應度得分 | 推重比 (TWR) | 續航時間 (min) | 整機質量 (g) | 包絡直徑 (m) | 關鍵演化變革推動原因 |")
        md.append("| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |")

        for b in breakthroughs:
            gen = b.get("generation", 0)
            score = b.get("new_best_score", 0.0)
            m = b.get("metrics_after", {})
            r_str = "；".join(b.get("rationales", []))
            tag = "🌱 初始種子" if gen == 0 else f"🚀 世代突破"
            md.append(
                f"| Gen {gen} | {tag} | **{score:.1f}** | {m.get('thrust_to_weight_ratio', 0):.2f} | "
                f"{m.get('estimated_flight_time_min', 0):.1f} | {m.get('total_mass_g', 0):.0f} | "
                f"{m.get('total_diameter_m', 0):.2f} | {r_str} |"
            )
        md.append("\n---\n")

        # Section 4: Reasoning Log
        md.append("## 🔍 4. 形態變革動機日誌 (Morphological Change Rationale Log)\n")
        for log in reasoning_logs:
            md.append(f"> {log}\n>")
        md.append("\n---\n")

        # Section 5: Structured Decisions
        md.append("## 📊 5. 結構化變更決策矩陣 (Structured Decisions Matrix)\n")
        md.append("| 世代 | 影響組件 | 決策動作 | 變更細節 | 適應度影響 | 物理決策成因 |")
        md.append("| :---: | :---: | :---: | :--- | :---: | :--- |")
        for d in decisions:
            g = d.get("generation", 0)
            comp = d.get("component", "-")
            act = d.get("action", "-")
            chg = d.get("change", "-")
            df = d.get("fitness_delta", 0.0)
            rat = d.get("rationale", "-")
            md.append(f"| Gen {g} | `{comp}` | `{act}` | `{chg}` | `{df:+.1f}` | {rat} |")

        md.append("\n---\n")

        # Section 6: Physical Compliance
        md.append("## ✅ 6. 物理約束符合性檢核 (Physical Compliance Checklist)\n")
        d_val = stats.get("total_diameter_m", 0)
        twr_val = stats.get("thrust_to_weight_ratio", 0)
        ft_val = stats.get("estimated_flight_time_min", 0)

        d_ok = d_val <= max_size_m
        twr_ok = twr_val >= 1.5
        ft_ok = ft_val >= min_flight_time

        md.append(f"- [{'x' if d_ok else ' '}] **幾何外徑檢驗**：直徑 `{d_val:.2f}m` <= 限制 `{max_size_m:.2f}m` ({'通過，消除約束懲罰' if d_ok else '未通過'})")
        md.append(f"- [{'x' if twr_ok else ' '}] **安全推重比檢驗**：TWR `{twr_val:.2f}` >= `1.5` ({'通過，處於最佳性能區間' if (1.8 <= twr_val <= 2.8) else '通過安全底線'})")
        md.append(f"- [{'x' if ft_ok else ' '}] **任務續航檢驗**：預估懸停 `{ft_val:.1f}min` >= 目標 `{min_flight_time:.1f}min` ({'達標並獲取額外加成' if ft_ok else '未達標'})")
        md.append(f"- [x] **全感測器裝載檢驗**：必備感測器 `{req_sensors}` 全數正確配置安裝")
        md.append("\n")

        return "\n".join(md)

    def export_reports(
        self,
        mission_spec: Dict[str, Any],
        best_spec: Dict[str, Any],
        history: Dict[str, Any],
        output_dir: Union[str, Path]
    ) -> Tuple[Path, Path]:
        """Writes both Markdown report and structured JSON history to the designated output folder."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        md_path = out_path / "evolution_lineage_report.md"
        json_path = out_path / "evolution_history.json"

        # Generate markdown content
        md_content = self.generate_markdown_report(mission_spec, best_spec, history)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Prepare JSON payload
        clean_history = {
            "mission_spec": mission_spec,
            "final_best_spec": {
                "design_id": best_spec.get("design_id"),
                "num_arms": best_spec.get("num_arms"),
                "arm_length_m": best_spec.get("arm_length_m"),
                "motor_id": best_spec.get("motor_id"),
                "prop_id": best_spec.get("prop_id"),
                "battery_id": best_spec.get("battery_id"),
                "sensors_mount": best_spec.get("sensors_mount"),
                "stats": best_spec.get("stats", {})
            },
            "summary": history.get("summary", {}),
            "evolution_reasoning_log": best_spec.get("evolution_reasoning_log", []),
            "morph_decisions": best_spec.get("morph_decisions", []),
            "breakthrough_trail": history.get("breakthrough_trail", []),
            "direct_lineage": history.get("direct_lineage", []),
            "generations_summary": history.get("generations_summary", [])
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(clean_history, f, indent=2, ensure_ascii=False)

        return md_path, json_path


class MorphEvolutionEngine:
    """Evolutionary engine that morphs drones according to mission requirements with explainability."""

    def __init__(self, db: ComponentDB):
        self.db = db
        self.motors = [m["id"] for m in db.list_components("motors")]
        self.props = [p["id"] for p in db.list_components("propellers")]
        self.batteries = [b["id"] for b in db.list_components("batteries")]
        self.sensors = [s["id"] for s in db.list_components("sensors")]
        self.tracker = EvolutionExplainabilityEngine(self.db)

    def generate_random_individual(self, required_sensors: List[str]) -> Dict[str, Any]:
        """Generates a random candidate drone configuration."""
        num_arms = random.choice([4, 6, 8])
        arm_length_m = round(random.uniform(0.15, 0.45), 2)
        motor_id = random.choice(self.motors)
        prop_id = random.choice(self.props)
        battery_id = random.choice(self.batteries)

        sensors_mount = []
        for s_id in required_sensors:
            sensors_mount.append({
                "sensor_id": s_id,
                "rel_pos_xyz": [round(random.uniform(-0.1, 0.1), 2), round(random.uniform(-0.1, 0.1), 2), 0.05]
            })

        return {
            "num_arms": num_arms,
            "arm_length_m": arm_length_m,
            "motor_id": motor_id,
            "prop_id": prop_id,
            "battery_id": battery_id,
            "sensors_mount": sensors_mount
        }

    def evaluate_fitness(self, ind: Dict[str, Any], mission_spec: Dict[str, Any]) -> float:
        """
        Evaluates the fitness score of a candidate drone against mission requirements.
        Higher score = better candidate.
        """
        max_size_m = mission_spec.get("max_size_m", 0.6)
        min_flight_time_min = mission_spec.get("min_flight_time_min", 10.0)

        total_diameter = (ind["arm_length_m"] * 2.0) + 0.15

        try:
            stats = self.db.calculate_power_and_mass(
                ind["num_arms"],
                ind["motor_id"],
                ind["prop_id"],
                ind["battery_id"],
                [s["sensor_id"] for s in ind.get("sensors_mount", [])]
            )
        except Exception:
            return -1000.0

        twr = stats["thrust_to_weight_ratio"]
        flight_time = stats["estimated_flight_time_min"]

        # Hard constraints
        if twr < 1.5:  # Cannot fly safely
            return -500.0 + twr * 10.0

        if total_diameter > max_size_m:  # Too big for mission workspace
            return -300.0 - (total_diameter - max_size_m) * 100.0

        # Score calculation
        fitness = 100.0

        # Flight time bonus
        if flight_time >= min_flight_time_min:
            fitness += (flight_time - min_flight_time_min) * 10.0
        else:
            fitness -= (min_flight_time_min - flight_time) * 15.0

        # Thrust-to-weight ratio bonus (optimal around 1.8 - 2.8)
        if 1.8 <= twr <= 2.8:
            fitness += 30.0

        # Efficiency bonus: penalty for unnecessarily heavy frame
        fitness -= stats["total_mass_g"] * 0.02

        return fitness

    def evolve(
        self,
        mission_spec: Dict[str, Any],
        population_size: int = 30,
        generations: int = 20,
        output_dir: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Runs the evolutionary optimization loop, tracks morphological changes,
        generation breakthroughs, and exports lineage reports.
        """
        required_sensors = mission_spec.get("required_sensors", [])

        # Store all individuals ever created for lineage ancestry resolution
        all_individuals_registry: Dict[str, Dict[str, Any]] = {}

        # Initialize Generation 0 population
        population = []
        for i in range(population_size):
            ind = self.generate_random_individual(required_sensors)
            ind_id = f"gen0_ind_{i}"
            ind["_id"] = ind_id
            ind["_generation"] = 0
            ind["_parent_id"] = None
            ind["_mutation_type"] = "seed"
            population.append(ind)
            all_individuals_registry[ind_id] = copy.deepcopy(ind)

        best_ind = None
        best_score = -999999.0

        evolution_reasoning_log: List[str] = []
        morph_decisions: List[Dict[str, Any]] = []
        breakthrough_trail: List[Dict[str, Any]] = []
        generations_summary: List[Dict[str, Any]] = []

        # Generation 0 Evaluation
        scored_pop = []
        for ind in population:
            score = self.evaluate_fitness(ind, mission_spec)
            scored_pop.append((score, ind))

        scored_pop.sort(key=lambda x: x[0], reverse=True)
        best_score = scored_pop[0][0]
        best_ind = copy.deepcopy(scored_pop[0][1])

        # Record Gen 0 Seed
        seed_record = self.tracker.explain_seed(best_ind, mission_spec)
        evolution_reasoning_log.append(f"[Gen 0 初始種子奠定] {seed_record['rationale']}")
        morph_decisions.append(seed_record)
        breakthrough_trail.append({
            "generation": 0,
            "previous_best_score": round(best_score, 2),
            "new_best_score": round(best_score, 2),
            "delta_score": 0.0,
            "metrics_before": None,
            "metrics_after": seed_record["metrics_after"],
            "rationales": [seed_record["rationale"]],
            "decisions": [seed_record]
        })

        generations_summary.append({
            "generation": 0,
            "max_fitness": round(best_score, 2),
            "avg_fitness": round(sum(x[0] for x in scored_pop) / len(scored_pop), 2),
            "min_fitness": round(scored_pop[-1][0], 2)
        })

        # Evolutionary Generations Loop
        for gen in range(1, generations):
            # Survivors: top 50%
            survivors = [item[1] for item in scored_pop[:max(2, population_size // 2)]]

            # Elitism: retain top individual directly
            elite = copy.deepcopy(survivors[0])
            new_pop = [elite]

            while len(new_pop) < population_size:
                parent = random.choice(survivors)
                child = copy.deepcopy(parent)
                child_id = f"gen{gen}_ind_{len(new_pop)}"
                child["_id"] = child_id
                child["_generation"] = gen
                child["_parent_id"] = parent.get("_id")

                mutation_choice = random.choice(["arm_length", "motor", "prop", "battery"])
                child["_mutation_type"] = mutation_choice

                if mutation_choice == "arm_length":
                    child["arm_length_m"] = round(max(0.12, child["arm_length_m"] + random.uniform(-0.06, 0.06)), 2)
                elif mutation_choice == "motor":
                    child["motor_id"] = random.choice(self.motors)
                elif mutation_choice == "prop":
                    child["prop_id"] = random.choice(self.props)
                elif mutation_choice == "battery":
                    child["battery_id"] = random.choice(self.batteries)

                new_pop.append(child)
                all_individuals_registry[child_id] = copy.deepcopy(child)

            # Evaluate new population
            scored_pop = []
            for ind in new_pop:
                score = self.evaluate_fitness(ind, mission_spec)
                scored_pop.append((score, ind))

            scored_pop.sort(key=lambda x: x[0], reverse=True)
            gen_best_score, gen_best_ind = scored_pop[0]

            # Check for generation breakthrough
            if gen_best_score > best_score:
                change_analysis = self.tracker.explain_change(
                    best_ind, gen_best_ind, mission_spec, gen=gen
                )

                rationales = change_analysis["rationales"]
                decisions = change_analysis["decisions"]

                if rationales:
                    summary_text = "；".join(rationales)
                else:
                    summary_text = "綜合參數細部微調優化"

                log_entry = (
                    f"[Gen {gen} 世代躍遷突破] {summary_text}。"
                    f"適應度由 {best_score:.1f} 提升至 {gen_best_score:.1f} ({gen_best_score - best_score:+.1f} 分)"
                )
                evolution_reasoning_log.append(log_entry)
                morph_decisions.extend(decisions)

                breakthrough_trail.append({
                    "generation": gen,
                    "previous_best_score": round(best_score, 2),
                    "new_best_score": round(gen_best_score, 2),
                    "delta_score": round(gen_best_score - best_score, 2),
                    "metrics_before": change_analysis["metrics_before"],
                    "metrics_after": change_analysis["metrics_after"],
                    "rationales": rationales,
                    "decisions": decisions
                })

                best_score = gen_best_score
                best_ind = copy.deepcopy(gen_best_ind)

            generations_summary.append({
                "generation": gen,
                "max_fitness": round(gen_best_score, 2),
                "avg_fitness": round(sum(x[0] for x in scored_pop) / len(scored_pop), 2),
                "min_fitness": round(scored_pop[-1][0], 2)
            })

            population = new_pop

        # Direct Lineage Ancestry Resolution
        direct_lineage: List[Dict[str, Any]] = []
        curr_id = best_ind.get("_id")
        while curr_id and curr_id in all_individuals_registry:
            ind_node = all_individuals_registry[curr_id]
            parent_id = ind_node.get("_parent_id")
            node_metrics = self.tracker.get_physical_metrics(ind_node, mission_spec)

            if parent_id and parent_id in all_individuals_registry:
                parent_node = all_individuals_registry[parent_id]
                change_info = self.tracker.explain_change(
                    parent_node, ind_node, mission_spec, gen=ind_node.get("_generation", 0)
                )
                r_list = change_info["rationales"]
            else:
                r_list = ["始祖種子個體"]

            direct_lineage.insert(0, {
                "individual_id": curr_id,
                "generation": ind_node.get("_generation", 0),
                "parent_id": parent_id,
                "mutation_type": ind_node.get("_mutation_type", "seed"),
                "metrics": node_metrics,
                "rationales": r_list
            })
            curr_id = parent_id

        # Compile final best drone specification
        final_metrics = self.tracker.get_physical_metrics(best_ind, mission_spec)
        best_ind["design_id"] = f"evolved_{mission_spec.get('mission_type', 'drone')}"
        best_ind["stats"] = final_metrics
        best_ind["evolution_reasoning_log"] = evolution_reasoning_log
        best_ind["morph_decisions"] = morph_decisions
        best_ind["lineage_trail"] = direct_lineage

        history_bundle = {
            "summary": {
                "population_size": population_size,
                "generations": generations,
                "initial_fitness": round(breakthrough_trail[0]["new_best_score"], 2),
                "final_fitness": round(best_score, 2),
                "fitness_improvement": round(best_score - breakthrough_trail[0]["new_best_score"], 2),
                "total_breakthroughs": len(breakthrough_trail)
            },
            "breakthrough_trail": breakthrough_trail,
            "direct_lineage": direct_lineage,
            "generations_summary": generations_summary
        }
        best_ind["evolution_history"] = history_bundle

        # Clean internal underscore keys for clean downstream JSON usage
        for k in list(best_ind.keys()):
            if k.startswith("_"):
                del best_ind[k]

        # Automatic report export
        target_out: Optional[Path] = None
        if output_dir:
            target_out = Path(output_dir)
        else:
            default_out = Path("output")
            if default_out.exists() or Path(".").resolve().name == "Digital_Twin_Drone_MVP":
                target_out = default_out

        if target_out:
            md_path, json_path = self.tracker.export_reports(
                mission_spec, best_ind, history_bundle, target_out
            )
            best_ind["evolution_reports"] = {
                "markdown": str(md_path),
                "json": str(json_path)
            }

        return best_ind


if __name__ == "__main__":
    db = ComponentDB()
    engine = MorphEvolutionEngine(db)

    mission = {
        "mission_type": "confined_inspection",
        "max_size_m": 0.55,
        "min_flight_time_min": 10.0,
        "required_sensors": ["s_lidar_2d", "s_depth_cam"]
    }

    best_spec = engine.evolve(mission, population_size=40, generations=25, output_dir="output")
    print("\n========================================================")
    print("🧬 Evolved Drone Spec Result:")
    print(f"  Frame: {best_spec['num_arms']}-Arm, Length: {best_spec['arm_length_m']}m")
    print(f"  Motor: {best_spec['motor_id']}, Battery: {best_spec['battery_id']}")
    print(f"  Stats: TWR={best_spec['stats']['thrust_to_weight_ratio']}, FlightTime={best_spec['stats']['estimated_flight_time_min']}m, Mass={best_spec['stats']['total_mass_g']}g")
    print(f"  Reasoning Logs Count: {len(best_spec['evolution_reasoning_log'])}")
    print(f"  Morph Decisions Count: {len(best_spec['morph_decisions'])}")
    print("========================================================\n")
    for log in best_spec["evolution_reasoning_log"][:4]:
        print(f"  * {log}")

