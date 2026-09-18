#!/usr/bin/env python3
"""
Digital Twin Drone MVP - Mission-Driven Morphological & Sensor Evolution Engine
Block 4: Given a mission_spec.json (constraints & goals), uses an evolutionary optimization loop
to search for the best drone configuration (num_arms, arm_length, motor, prop, battery, sensors)
and outputs a valid drone_spec.json.
"""

import random
import json
from typing import Dict, Any, List
from db_loader import ComponentDB

class MorphEvolutionEngine:
    """Evolutionary engine that morphs drones according to mission requirements."""

    def __init__(self, db: ComponentDB):
        self.db = db
        self.motors = [m["id"] for m in db.list_components("motors")]
        self.props = [p["id"] for p in db.list_components("propellers")]
        self.batteries = [b["id"] for b in db.list_components("batteries")]
        self.sensors = [s["id"] for s in db.list_components("sensors")]

    def generate_random_individual(self, required_sensors: List[str]) -> Dict[str, Any]:
        """Generates a random candidate drone configuration."""
        num_arms = random.choice([4, 6, 8])
        arm_length_m = round(random.uniform(0.15, 0.45), 2)
        motor_id = random.choice(self.motors)
        prop_id = random.choice(self.props)
        battery_id = random.choice(self.batteries)

        sensors_mount = []
        # Mount required sensors
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
        required_sensors = mission_spec.get("required_sensors", [])

        # Calculate diagonal diameter
        total_diameter = (ind["arm_length_m"] * 2.0) + 0.15

        # Check physical feasibility
        try:
            stats = self.db.calculate_power_and_mass(
                ind["num_arms"],
                ind["motor_id"],
                ind["prop_id"],
                ind["battery_id"],
                [s["sensor_id"] for s in ind["sensors_mount"]]
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

        # Thrust-to-weight ratio bonus (optimal around 2.0 - 2.5)
        if 1.8 <= twr <= 2.8:
            fitness += 30.0

        # Efficiency bonus: penalty for unnecessarily heavy frame
        fitness -= stats["total_mass_g"] * 0.02

        return fitness

    def evolve(self, mission_spec: Dict[str, Any], population_size: int = 30, generations: int = 20) -> Dict[str, Any]:
        """Runs the evolutionary optimization loop to find the best configuration."""
        required_sensors = mission_spec.get("required_sensors", [])
        population = [self.generate_random_individual(required_sensors) for _ in range(population_size)]

        best_ind = None
        best_score = -999999.0

        for gen in range(generations):
            # Evaluate population
            scored_pop = []
            for ind in population:
                score = self.evaluate_fitness(ind, mission_spec)
                scored_pop.append((score, ind))

                if score > best_score:
                    best_score = score
                    best_ind = ind

            # Sort by score descending
            scored_pop.sort(key=lambda x: x[0], reverse=True)

            # Select top 50% for next generation
            survivors = [item[1] for item in scored_pop[:population_size // 2]]

            # Breed & Mutate next generation
            new_pop = list(survivors)
            while len(new_pop) < population_size:
                parent = random.choice(survivors)
                child = dict(parent)
                # Mutate random attribute
                mutation_choice = random.choice(["arm_length", "motor", "prop", "battery"])
                if mutation_choice == "arm_length":
                    child["arm_length_m"] = round(max(0.12, child["arm_length_m"] + random.uniform(-0.05, 0.05)), 2)
                elif mutation_choice == "motor":
                    child["motor_id"] = random.choice(self.motors)
                elif mutation_choice == "prop":
                    child["prop_id"] = random.choice(self.props)
                elif mutation_choice == "battery":
                    child["battery_id"] = random.choice(self.batteries)

                new_pop.append(child)

            population = new_pop

        if best_ind is None:
            best_ind = self.generate_random_individual(required_sensors)

        best_ind["design_id"] = f"evolved_{mission_spec.get('mission_type', 'drone')}"
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

    best_spec = engine.evolve(mission, population_size=40, generations=25)
    print("Evolved Drone Spec Result:")
    print(json.dumps(best_spec, indent=2))
