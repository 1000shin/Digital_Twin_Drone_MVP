#!/usr/bin/env python3
"""
Digital Twin Drone - Sensor Coverage Simulator
Phase 2: Calculates 3D Field of View (FOV) coverage, overlap ratios, and blind spots
for sensor configurations mounted on evolved drones.
"""

import math
from typing import Dict, Any, List

class SensorCoverageSimulator:
    """Calculates spatial coverage metrics for LiDAR and camera sensors."""

    def calculate_sensor_coverage(
        self,
        sensors_mount: List[Dict[str, Any]],
        sensor_db_lookup: Dict[str, Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Computes total FOV coverage (in steradians / degrees) and blind spot ratio.
        """
        if not sensors_mount:
            return {"total_fov_deg": 0.0, "coverage_ratio": 0.0, "blind_spot_ratio": 1.0}

        total_fov = 0.0
        active_sensors_count = 0

        for sm in sensors_mount:
            s_id = sm.get("sensor_id")
            sensor_info = sensor_db_lookup.get(s_id, {})
            fov_deg = sensor_info.get("fov_deg", 60.0)

            total_fov += fov_deg
            active_sensors_count += 1

        # Normalized sphere coverage estimate (360 deg horizontal x 180 deg vertical max = 360)
        coverage_ratio = min(1.0, total_fov / 360.0)
        blind_spot_ratio = round(1.0 - coverage_ratio, 2)

        return {
            "sensor_count": active_sensors_count,
            "total_fov_deg": round(total_fov, 1),
            "coverage_ratio": round(coverage_ratio, 2),
            "blind_spot_ratio": blind_spot_ratio
        }

if __name__ == "__main__":
    sim = SensorCoverageSimulator()
    sample_mount = [
        {"sensor_id": "s_lidar_2d"},
        {"sensor_id": "s_depth_cam"}
    ]
    db_lookup = {
        "s_lidar_2d": {"fov_deg": 360.0},
        "s_depth_cam": {"fov_deg": 87.0}
    }
    metrics = sim.calculate_sensor_coverage(sample_mount, db_lookup)
    print("Sensor Coverage Metrics:", metrics)
