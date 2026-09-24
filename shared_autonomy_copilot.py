#!/usr/bin/env python3
"""
Digital Twin Drone MVP - Shared Autonomy Copilot Core
Milestone M2.6: "Human Pilot, AI Assistant Intervention"

Architecture:
- Continuous Dynamic Blending & Virtual Bumper
- Two-Tier Safety Zones: Warning Zone (2.0m ~ 1.2m) & Emergency Zone (< 1.2m)
- Time-To-Collision (TTC) & Approach Vector Analysis
- Preserves Human Escape Maneuvers with zero latency
"""

import math
from enum import Enum
from typing import Dict, Any, List, Tuple, Optional


class CopilotInterventionLevel(str, Enum):
    STANDBY = "STANDBY"        # Free flight, d >= 2.0m, zero intervention (beta = 0.0)
    WARNING = "WARNING"        # Warning zone, 1.2m <= d < 2.0m, velocity damping
    DEFLECTING = "DEFLECTING"  # Emergency zone, d < 1.2m, active APF repulsion & tangential deflection


class SharedAutonomyCopilot:
    """
    協同飛控副駕駛核心運算器 (Shared Autonomy Copilot)
    Implements shared-control blending between human stick commands and AI safety fields.
    """

    def __init__(
        self,
        warning_dist_m: float = 2.0,
        emergency_dist_m: float = 1.2,
        hard_limit_dist_m: float = 0.5,
        ttc_threshold_sec: float = 2.0,
        repulsion_gain: float = 1.4,
        tangential_gain: float = 0.35,
        max_speed_mps: float = 8.0
    ):
        self.warning_dist = warning_dist_m
        self.emergency_dist = emergency_dist_m
        self.hard_limit_dist = hard_limit_dist_m
        self.ttc_threshold = ttc_threshold_sec
        self.k_rep = repulsion_gain
        self.k_tan = tangential_gain
        self.max_speed = max_speed_mps

        # 8-Ray LiDAR relative body angles:
        # [0° front, 45° front-left, 90° left, 135° rear-left,
        #  180° rear, 225° rear-right, 270° right, 315° front-right]
        self.lidar_angles_rad = [
            0.0,
            math.pi / 4.0,
            math.pi / 2.0,
            3.0 * math.pi / 4.0,
            math.pi,
            -3.0 * math.pi / 4.0,
            -math.pi / 2.0,
            -math.pi / 4.0
        ]

    def _get_obstacle_unit_vector(self, angle_rad: float) -> Tuple[float, float]:
        """
        Returns (fwd, right) unit vector pointing toward the obstacle in the drone body horizontal frame.
        Forward is +pitch, Right is +roll.
        angle = 0° (front)       -> (1.0, 0.0)
        angle = 90° (left)       -> (0.0, -1.0)
        angle = 180° (rear)      -> (-1.0, 0.0)
        angle = 270° / -90° (rt) -> (0.0, 1.0)
        """
        fwd = math.cos(angle_rad)
        right = -math.sin(angle_rad)
        return (fwd, right)

    def evaluate(
        self,
        human_action: List[float],
        lidar_ranges: List[float],
        current_velocity: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates proximity and blends human pilot action with AI safety vector.

        Args:
            human_action: [pitch_cmd, roll_cmd, yaw_rate_cmd, throttle_cmd] each in [-1.0, 1.0]
            lidar_ranges: 8-ray LiDAR distances in meters (0 to ~20m)
            current_velocity: Optional [vx, vy, vz] in world or body frame

        Returns:
            Decision dictionary containing:
            - safe_action: [pitch, roll, yaw_rate, throttle]
            - intervention_level: CopilotInterventionLevel
            - beta: Blending weight [0.0, 1.0]
            - min_distance_m: float
            - ttc_sec: float
            - repulsion_vector: [repel_pitch, repel_roll]
            - human_escaped: bool
        """
        cmd_p = max(-1.0, min(1.0, float(human_action[0])))
        cmd_r = max(-1.0, min(1.0, float(human_action[1])))
        cmd_yaw = max(-1.0, min(1.0, float(human_action[2])))
        cmd_climb = max(-1.0, min(1.0, float(human_action[3])))

        # 1. Identify minimum distance and threatening obstacle direction
        if not lidar_ranges or len(lidar_ranges) == 0:
            min_dist = 999.0
            min_idx = 0
        else:
            min_dist = min(lidar_ranges)
            min_idx = lidar_ranges.index(min_dist)

        obs_angle = self.lidar_angles_rad[min_idx % 8]
        obs_fwd, obs_right = self._get_obstacle_unit_vector(obs_angle)

        # 2. Human command projection onto obstacle direction
        # Positive dot product means pilot is pushing INTO the obstacle
        approach_dot = cmd_p * obs_fwd + cmd_r * obs_right

        # Check if human is commanding an escape movement (pointing away)
        human_escaped = approach_dot <= 0.05

        # 3. Estimate Time-To-Collision (TTC)
        approach_speed = max(0.0, approach_dot) * (self.max_speed * 0.6)
        if current_velocity and len(current_velocity) >= 3:
            vel_mag = math.hypot(current_velocity[0], current_velocity[2])
            approach_speed = max(approach_speed, vel_mag * 0.5)

        if approach_speed > 0.1:
            ttc = round(min_dist / approach_speed, 2)
        else:
            ttc = 999.0

        # 4. Multi-Tier Zone Determination
        if min_dist >= self.warning_dist and (ttc > self.ttc_threshold or min_dist >= self.warning_dist * 1.5):
            # Free Flight Zone (Zero intervention)
            level = CopilotInterventionLevel.STANDBY
            beta = 0.0
            damping_factor = 1.0
            safe_p, safe_r = cmd_p, cmd_r
            repel_p, repel_r = 0.0, 0.0

        elif min_dist >= self.emergency_dist or human_escaped:
            # Warning Zone OR Pilot already executing escape maneuver
            level = CopilotInterventionLevel.WARNING
            # Smooth velocity damping factor alpha in [0.4, 0.85]
            norm_w = (min_dist - self.emergency_dist) / max(0.01, (self.warning_dist - self.emergency_dist))
            norm_w = max(0.0, min(1.0, norm_w))
            damping_factor = 0.40 + 0.45 * norm_w
            beta = round(1.0 - damping_factor, 3)

            if human_escaped:
                # If human is maneuvering AWAY from obstacle, do NOT dampen escape input
                safe_p, safe_r = cmd_p, cmd_r
                repel_p, repel_r = 0.0, 0.0
                beta = 0.0
            else:
                # Dampen the approach component while leaving lateral steering intact
                approach_p = approach_dot * obs_fwd
                approach_r = approach_dot * obs_right
                lateral_p = cmd_p - approach_p
                lateral_r = cmd_r - approach_r

                # Scaled approach
                safe_p = lateral_p + approach_p * damping_factor
                safe_r = lateral_r + approach_r * damping_factor
                repel_p = -obs_fwd * (1.0 - damping_factor) * 0.5
                repel_r = -obs_right * (1.0 - damping_factor) * 0.5

        else:
            # Emergency Zone: Immediate deflection and active APF repulsion
            level = CopilotInterventionLevel.DEFLECTING
            norm_e = (min_dist - self.hard_limit_dist) / max(0.01, (self.emergency_dist - self.hard_limit_dist))
            norm_e = max(0.0, min(1.0, norm_e))
            # Blending weight beta ramps up as drone gets closer to hard limit
            beta = round(0.55 + 0.45 * (1.0 - norm_e), 3)

            # Repulsive force points strictly away from obstacle
            repel_magnitude = ((self.emergency_dist - min_dist) / self.emergency_dist) ** 1.4 * self.k_rep
            repel_p = -obs_fwd * repel_magnitude
            repel_r = -obs_right * repel_magnitude

            # Tangential escape deflection (steer along perimeter)
            # Tan vector is orthogonal to obstacle vector: (-obs_right, obs_fwd)
            tan_fwd = -obs_right
            tan_right = obs_fwd
            # Choose sign based on existing pilot lateral bias
            pilot_lateral = cmd_p * tan_fwd + cmd_r * tan_right
            tan_dir = 1.0 if pilot_lateral >= 0.0 else -1.0
            tan_p = tan_fwd * tan_dir * self.k_tan
            tan_r = tan_right * tan_dir * self.k_tan

            if human_escaped:
                # Retain human escape maneuvers with full weight
                safe_p = cmd_p + repel_p * 0.35
                safe_r = cmd_r + repel_r * 0.35
            else:
                # Blend pilot command with active repulsion and tangential slide
                safe_p = (1.0 - beta) * cmd_p + beta * (repel_p + tan_p)
                safe_r = (1.0 - beta) * cmd_r + beta * (repel_r + tan_r)

        # 5. Output Clamping
        safe_p = max(-1.0, min(1.0, round(safe_p, 3)))
        safe_r = max(-1.0, min(1.0, round(safe_r, 3)))

        return {
            "safe_action": [safe_p, safe_r, cmd_yaw, cmd_climb],
            "intervention_level": level.value,
            "beta": beta,
            "min_distance_m": round(min_dist, 2),
            "ttc_sec": ttc,
            "repulsion_vector": [round(repel_p, 3), round(repel_r, 3)],
            "human_escaped": human_escaped
        }
