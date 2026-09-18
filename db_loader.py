#!/usr/bin/env python3
"""
Digital Twin Drone MVP - Component Database Loader
Block 1: Manages component database loading, validation, and property lookup.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

DEFAULT_DB_PATH = Path(__file__).parent / "components_db.json"

class ComponentDB:
    """Interface to load and query the drone component database."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._data: Dict[str, List[Dict[str, Any]]] = {}
        self.load_db()

    def load_db(self) -> None:
        """Loads and parses the components_db.json file."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Component database file not found at: {self.db_path}")

        with open(self.db_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

        # Validate basic keys
        required_categories = ["motors", "propellers", "batteries", "sensors", "materials"]
        for category in required_categories:
            if category not in self._data:
                raise KeyError(f"Missing category '{category}' in component database.")

    def get_component(self, category: str, comp_id: str) -> Optional[Dict[str, Any]]:
        """Finds a component by category and ID."""
        category_list = self._data.get(category, [])
        for comp in category_list:
            if comp.get("id") == comp_id:
                return comp
        return None

    def list_components(self, category: str) -> List[Dict[str, Any]]:
        """Returns all components under a given category."""
        return self._data.get(category, [])

    def calculate_power_and_mass(
        self,
        num_arms: int,
        motor_id: str,
        prop_id: str,
        battery_id: str,
        sensor_ids: List[str]
    ) -> Dict[str, float]:
        """
        Estimates total mass, total thrust, and max flight time for a given configuration.
        """
        motor = self.get_component("motors", motor_id)
        prop = self.get_component("propellers", prop_id)
        battery = self.get_component("batteries", battery_id)

        if not motor or not prop or not battery:
            raise ValueError("Invalid motor, propeller, or battery ID provided.")

        total_motor_weight = motor["weight_g"] * num_arms
        total_prop_weight = prop["weight_g"] * num_arms
        battery_weight = battery["weight_g"]

        total_sensor_weight = 0.0
        total_sensor_power = 0.0
        for s_id in sensor_ids:
            sensor = self.get_component("sensors", s_id)
            if sensor:
                total_sensor_weight += sensor.get("weight_g", 0.0)
                total_sensor_power += sensor.get("power_w", 0.0)

        # Frame mass estimate (rough linear scaling based on arm count)
        estimated_frame_weight_g = 50.0 + (num_arms * 25.0)

        total_mass_g = total_motor_weight + total_prop_weight + battery_weight + total_sensor_weight + estimated_frame_weight_g
        max_total_thrust_g = motor["max_thrust_g"] * num_arms

        thrust_to_weight_ratio = max_total_thrust_g / max(total_mass_g, 1.0)

        # Simple flight time estimation (in minutes)
        # Average power draw at hover: ~1.5x mass in grams divided by thrust efficiency (g/W ~ 6)
        hover_power_w = (total_mass_g / 6.0) + total_sensor_power
        battery_energy_wh = (battery["capacity_mah"] / 1000.0) * battery["voltage_v"]
        estimated_flight_time_min = (battery_energy_wh / max(hover_power_w, 0.1)) * 60.0

        return {
            "total_mass_g": round(total_mass_g, 2),
            "max_thrust_g": round(max_total_thrust_g, 2),
            "thrust_to_weight_ratio": round(thrust_to_weight_ratio, 2),
            "estimated_flight_time_min": round(estimated_flight_time_min, 2)
        }


if __name__ == "__main__":
    db = ComponentDB()
    print(f"Loaded {len(db.list_components('motors'))} motors, "
          f"{len(db.list_components('sensors'))} sensors.")
    stats = db.calculate_power_and_mass(
        num_arms=4,
        motor_id="m_2212_920kv",
        prop_id="p_1045",
        battery_id="b_3s_2200mah",
        sensor_ids=["s_lidar_2d", "s_depth_cam"]
    )
    print("Sample Quadcopter Estimation Stats:", json.dumps(stats, indent=2))
