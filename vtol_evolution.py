#!/usr/bin/env python3
"""
Digital Twin Drone - VTOL & Tilt-Rotor Morphing Evolution Engine
Phase 3 Choice 2: Evolutionary algorithm optimizing VTOL wing aspect ratio, aerodynamic Lift-to-Drag (L/D),
servo tilt angles, hover thrust-to-weight ratio, and long-range flight efficiency.
"""

import random
import math
from typing import Dict, Any, List
from db_loader import ComponentDB
from morph_evolution import MorphEvolutionEngine

class VTOLEvolutionEngine(MorphEvolutionEngine):
    """Evolutionary engine for VTOL & Tilt-Rotor morphing aircraft."""

    def generate_random_vtol_individual(self, required_sensors: List[str]) -> Dict[str, Any]:
        """Generates a candidate VTOL hybrid configuration."""
        wingspan_m = round(random.uniform(0.70, 1.60), 2)
        wing_chord_m = round(random.uniform(0.15, 0.30), 2)
        num_tilt_servos = random.choice([2, 4])
        num_hover_motors = random.choice([4, 6])
        motor_id = random.choice(self.motors)
        prop_id = random.choice(self.props)
        battery_id = random.choice(self.batteries)

        sensors_mount = []
        for s_id in required_sensors:
            sensors_mount.append({
                "sensor_id": s_id,
                "rel_pos_xyz": [0.15, 0.0, 0.02]
            })

        return {
            "aircraft_type": "vtol_tilt_rotor",
            "wingspan_m": wingspan_m,
            "wing_chord_m": wing_chord_m,
            "num_tilt_servos": num_tilt_servos,
            "num_hover_motors": num_hover_motors,
            "motor_id": motor_id,
            "prop_id": prop_id,
            "battery_id": battery_id,
            "sensors_mount": sensors_mount
        }

    def evaluate_vtol_fitness(self, ind: Dict[str, Any], mission_spec: Dict[str, Any]) -> float:
        """
        Evaluates VTOL aerodynamic efficiency:
        Lift-to-Drag L/D ratio, hover thrust, stall speed, and battery endurance.
        """
        wingspan = ind["wingspan_m"]
        chord = ind["wing_chord_m"]
        wing_area = wingspan * chord
        aspect_ratio = (wingspan ** 2) / max(0.01, wing_area)

        # Estimate Total Mass
        try:
            stats = self.db.calculate_power_and_mass(
                ind["num_hover_motors"],
                ind["motor_id"],
                ind["prop_id"],
                ind["battery_id"],
                [s["sensor_id"] for s in ind["sensors_mount"]]
            )
        except Exception:
            return -1000.0

        # Wing mass addition
        total_mass_kg = (stats["total_mass_g"] + wing_area * 180.0) / 1000.0
        twr_hover = stats["max_thrust_g"] / max(1.0, total_mass_kg * 1000.0)

        # Aerodynamic Lift-to-Drag Ratio Estimate L/D
        # L/D ~ 0.8 * sqrt(pi * AR * e)
        ld_ratio = 0.8 * math.sqrt(math.pi * aspect_ratio * 0.85)

        # Cruise Power Draw (W) = Mass * g / (L/D) * V_cruise / prop_eff
        # In FW cruise, power is ~65% lower than multirotor hover
        cruise_power_w = (total_mass_kg * 9.81 / max(1.0, ld_ratio)) * 18.0 / 0.70

        battery = self.db.get_component("batteries", ind["battery_id"])
        battery_wh = (battery["capacity_mah"] / 1000.0) * battery["voltage_v"]
        vtol_flight_time_min = (battery_wh / max(1.0, cruise_power_w)) * 60.0

        # Constraints
        if twr_hover < 1.3:  # Cannot VTOL takeoff
            return -500.0

        target_time = mission_spec.get("min_flight_time_min", 15.0)
        max_size = mission_spec.get("max_size_m", 1.50)

        if wingspan > max_size:
            return -400.0 - (wingspan - max_size) * 100.0

        fitness = 150.0
        fitness += (ld_ratio * 15.0)                       # Aerodynamic L/D reward
        fitness += (vtol_flight_time_min - target_time) * 12.0 # Flight time reward
        fitness += (twr_hover * 15.0)                      # VTOL safety margin

        return fitness

    def evolve_vtol(self, mission_spec: Dict[str, Any], population_size: int = 30, generations: int = 20) -> Dict[str, Any]:
        """Runs the evolutionary loop to optimize VTOL morphing geometry."""
        req_sensors = mission_spec.get("required_sensors", [])
        population = [self.generate_random_vtol_individual(req_sensors) for _ in range(population_size)]

        best_ind = None
        best_score = -99999.0

        for gen in range(generations):
            scored = []
            for ind in population:
                score = self.evaluate_vtol_fitness(ind, mission_spec)
                scored.append((score, ind))
                if score > best_score:
                    best_score = score
                    best_ind = ind

            scored.sort(key=lambda x: x[0], reverse=True)
            survivors = [x[1] for x in scored[:population_size // 2]]

            new_pop = list(survivors)
            while len(new_pop) < population_size:
                parent = random.choice(survivors)
                child = dict(parent)
                mut = random.choice(["wingspan", "chord", "motor", "battery"])
                if mut == "wingspan":
                    child["wingspan_m"] = round(max(0.5, child["wingspan_m"] + random.uniform(-0.1, 0.1)), 2)
                elif mut == "chord":
                    child["wing_chord_m"] = round(max(0.12, child["wing_chord_m"] + random.uniform(-0.03, 0.03)), 2)
                elif mut == "motor":
                    child["motor_id"] = random.choice(self.motors)
                elif mut == "battery":
                    child["battery_id"] = random.choice(self.batteries)

                new_pop.append(child)

            population = new_pop

        if best_ind is None:
            best_ind = self.generate_random_vtol_individual(req_sensors)

        best_ind["design_id"] = f"evolved_vtol_{mission_spec.get('mission_type', 'vtol')}"
        return best_ind


if __name__ == "__main__":
    db = ComponentDB()
    vtol_engine = VTOLEvolutionEngine(db)

    sample_mission = {
        "mission_type": "offshore_wind_vtol",
        "max_size_m": 1.40,
        "min_flight_time_min": 25.0,
        "required_sensors": ["s_opt_cam_hd", "s_imu_standard"]
    }

    best_vtol = vtol_engine.evolve_vtol(sample_mission, population_size=35, generations=20)
    print("Evolved VTOL Morphing Aircraft Specification:")
    print(json.dumps(best_vtol, indent=2))
