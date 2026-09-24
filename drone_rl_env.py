#!/usr/bin/env python3
"""
Digital Twin Drone - Standard 6-DOF Reinforcement Learning Environment (Gymnasium-Compatible)
Pure Python implementation (Standard Library only: math, random, typing, dataclasses).
Simulates Collision Arena 3D flight dynamics, 8-ray LiDAR perception, gates, and reward functions.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional

@dataclass
class ObstaclePillar:
    x: float
    z: float
    radius: float = 0.55
    height: float = 6.0

@dataclass
class FlightGate:
    gate_id: int
    x: float
    y: float
    z: float
    width: float = 4.0
    height: float = 3.5

class DroneRLEnvironment:
    """
    Standard Gym-style 6-DOF Drone Autonomous Navigation & Obstacle Avoidance Environment.
    State observation: 23-dim continuous vector
    Action space: 4-dim continuous vector [-1.0, 1.0] -> [Pitch, Roll, Yaw_Rate, Throttle]
    """

    def __init__(self, seed: Optional[int] = 42):
        if seed is not None:
            random.seed(seed)

        # Physical Constants & Gen-3 Drone Specs
        self.mass = 0.880                # kg
        self.arm_length = 0.18           # m
        self.drone_radius = 0.21         # m (Ducted Shield outer boundary)
        self.gravity = 9.81              # m/s^2
        self.dt = 0.05                   # 20Hz control step
        self.max_tilt = 0.70             # rad (~40.1 deg)
        self.thrust_mult = 15.5          # m/s^2 horizontal acceleration authority
        self.max_episode_steps = 600     # 30 seconds at 20Hz

        # World Scenario: Collision Arena
        self.pillars = [
            ObstaclePillar(3.0, 3.0),
            ObstaclePillar(-3.0, 3.0),
            ObstaclePillar(3.0, -3.0),
            ObstaclePillar(-3.0, -3.0),
            ObstaclePillar(7.0, 7.0),
            ObstaclePillar(-7.0, -7.0)
        ]

        self.gates = [
            FlightGate(1, 0.0, 3.0, -7.0),
            FlightGate(2, 8.5, 4.0, 0.0),
            FlightGate(3, 0.0, 5.5, 8.5),
            FlightGate(4, -8.5, 3.5, 0.0)
        ]

        # 8-Direction LiDAR Angles in Drone Body Frame
        self.lidar_angles = [
            0.0,                # 0: Front
            math.pi / 4.0,      # 1: Front-Right
            math.pi / 2.0,      # 2: Right
            3.0 * math.pi / 4.0,# 3: Rear-Right
            math.pi,            # 4: Rear
            -3.0 * math.pi / 4.0,# 5: Rear-Left
            -math.pi / 2.0,     # 6: Left
            -math.pi / 4.0      # 7: Front-Left
        ]
        self.lidar_range_max = 12.0

        # Dynamic State Variables
        self.pos = [0.0, 0.20, 0.0]      # x, y (altitude), z
        self.vel = [0.0, 0.0, 0.0]
        self.pitch = 0.0
        self.roll = 0.0
        self.yaw = 0.0
        self.ang_vel = [0.0, 0.0, 0.0]
        self.current_step = 0
        self.current_gate_idx = 0
        self.prev_gate_dist = 0.0
        self.lap_count = 0
        self.collision_occurred = False
        self.collision_object = ""

    def reset(self, initial_pos: Optional[List[float]] = None) -> List[float]:
        """Resets the environment to start a new episode."""
        if initial_pos is not None:
            self.pos = list(initial_pos)
        else:
            # Slight random jitter around starting pad
            self.pos = [random.uniform(-0.3, 0.3), 1.2, random.uniform(-0.3, 0.3)]

        self.vel = [0.0, 0.0, 0.0]
        self.pitch = 0.0
        self.roll = 0.0
        self.yaw = random.uniform(-0.2, 0.2)
        self.ang_vel = [0.0, 0.0, 0.0]
        self.current_step = 0
        self.current_gate_idx = 0
        self.lap_count = 0
        self.collision_occurred = False
        self.collision_object = ""

        target_gate = self.gates[self.current_gate_idx]
        self.prev_gate_dist = self._dist_to_gate(target_gate)
        return self._get_observation()

    def step(self, action: List[float]) -> Tuple[List[float], float, bool, bool, Dict[str, Any]]:
        """
        Executes one action step (20Hz).
        Action: [cmd_pitch, cmd_roll, cmd_yaw_rate, cmd_climb] in [-1.0, 1.0]
        Returns: (obs, reward, terminated, truncated, info)
        """
        self.current_step += 1
        cmd_p = max(-1.0, min(1.0, action[0]))
        cmd_r = max(-1.0, min(1.0, action[1]))
        cmd_yaw = max(-1.0, min(1.0, action[2]))
        cmd_climb = max(-1.0, min(1.0, action[3]))

        prev_pitch = self.pitch
        prev_roll = self.roll
        prev_yaw = self.yaw

        # 1. Attitude Dynamics (80ms convergence interpolation)
        target_pitch = cmd_p * self.max_tilt
        target_roll = cmd_r * self.max_tilt
        self.pitch += (target_pitch - self.pitch) * 0.25
        self.roll += (target_roll - self.roll) * 0.25
        self.yaw += cmd_yaw * 0.08
        # Wrap yaw to [-pi, pi]
        self.yaw = (self.yaw + math.pi) % (2 * math.pi) - math.pi

        # Update body angular velocity vector [wx, wy, wz] in rad/s
        self.ang_vel = [
            round((self.pitch - prev_pitch) / self.dt, 4),
            round((cmd_yaw * 0.08) / self.dt, 4),
            round((self.roll - prev_roll) / self.dt, 4)
        ]

        # 2. Lift & Thrust Vectoring (World Frame)
        tilt_magnitude = math.sqrt(self.pitch**2 + self.roll**2)
        tilt_comp = 1.0 / max(math.cos(min(tilt_magnitude, self.max_tilt)), 0.50)
        throttle_acc = cmd_climb * 6.0
        nominal_lift = (self.gravity + throttle_acc) * tilt_comp

        # Body thrust unit vector along local UP projected via Yaw, Pitch, Roll
        # Local UP (0, 1, 0) rotated by Pitch(X) then Yaw(Y)
        # thrust_x approx -sin(roll)*cos(yaw) - sin(pitch)*sin(yaw)
        # thrust_z approx -sin(pitch)*cos(yaw) + sin(roll)*sin(yaw)
        sin_p = math.sin(self.pitch)
        cos_p = math.cos(self.pitch)
        sin_r = math.sin(self.roll)
        cos_r = math.cos(self.roll)
        sin_y = math.sin(self.yaw)
        cos_y = math.cos(self.yaw)

        # Simplified 3D thrust projection
        tx = -sin_r * cos_y + sin_p * sin_y
        tz = sin_p * cos_y + sin_r * sin_y
        ty = cos_p * cos_r

        # Vertical velocity update
        self.vel[1] += (nominal_lift * ty - self.gravity) * self.dt
        # Horizontal velocity update
        self.vel[0] += (tx * self.thrust_mult) * self.dt
        self.vel[2] += (tz * self.thrust_mult) * self.dt

        # Active leveling drag damping
        has_input = (abs(cmd_p) > 0.05 or abs(cmd_r) > 0.05)
        drag_h = 0.978 if has_input else 0.935
        self.vel[0] *= drag_h
        self.vel[2] *= drag_h
        self.vel[1] *= 0.95

        # Update Position
        self.pos[0] += self.vel[0] * self.dt
        self.pos[1] += self.vel[1] * self.dt
        self.pos[2] += self.vel[2] * self.dt

        # 3. Collision Checks
        terminated = False
        collision_penalty = 0.0

        # Ground collision
        if self.pos[1] <= 0.08:
            self.pos[1] = 0.08
            if abs(self.vel[1]) > 1.2 or self.current_step > 5:
                self.collision_occurred = True
                self.collision_object = "地面 (Ground)"
                terminated = True
                collision_penalty = -150.0

        # Ceiling / Out of arena bounds
        if self.pos[1] > 11.0 or abs(self.pos[0]) > 19.0 or abs(self.pos[2]) > 19.0:
            self.collision_occurred = True
            self.collision_object = "競技場外邊界 (Boundary)"
            terminated = True
            collision_penalty = -100.0

        # Pillar collisions
        for idx, pillar in enumerate(self.pillars):
            dist_2d = math.hypot(self.pos[0] - pillar.x, self.pos[2] - pillar.z)
            if dist_2d <= (pillar.radius + self.drone_radius) and self.pos[1] <= pillar.height:
                self.collision_occurred = True
                self.collision_object = f"立體立柱 #{idx+1}"
                terminated = True
                collision_penalty = -200.0
                break

        # 4. Target Gate Navigation & Progress Reward
        target_gate = self.gates[self.current_gate_idx]
        curr_gate_dist = self._dist_to_gate(target_gate)
        progress_reward = (self.prev_gate_dist - curr_gate_dist) * 15.0
        self.prev_gate_dist = curr_gate_dist

        # Gate Passing Check
        gate_reward = 0.0
        passed_gate = False
        if curr_gate_dist < 1.35 and not terminated:
            passed_gate = True
            gate_reward = 120.0
            self.current_gate_idx = (self.current_gate_idx + 1) % len(self.gates)
            if self.current_gate_idx == 0:
                self.lap_count += 1
                gate_reward += 300.0 # Full circuit completion bonus!
            new_target = self.gates[self.current_gate_idx]
            self.prev_gate_dist = self._dist_to_gate(new_target)

        # 5. Proximity Penalty from 8-Ray LiDAR
        lidar_readings = self._compute_lidar()
        min_lidar_dist = min(lidar_readings)
        proximity_penalty = 0.0
        if min_lidar_dist < 0.9:
            proximity_penalty = -3.5 * (0.9 - min_lidar_dist)

        # 6. Stability & Survival Bonus
        alive_bonus = 0.25
        stability_bonus = 0.15 if tilt_magnitude < 0.40 else -0.1

        # Total Step Reward
        step_reward = (
            progress_reward
            + gate_reward
            + collision_penalty
            + proximity_penalty
            + alive_bonus
            + stability_bonus
        )

        truncated = (self.current_step >= self.max_episode_steps)

        obs = self._get_observation()
        info = {
            "step": self.current_step,
            "gate_idx": self.current_gate_idx,
            "passed_gate": passed_gate,
            "laps": self.lap_count,
            "collided": self.collision_occurred,
            "hit_object": self.collision_object,
            "min_lidar_m": min_lidar_dist,
            "gate_distance_m": curr_gate_dist,
            "speed_mps": math.sqrt(self.vel[0]**2 + self.vel[1]**2 + self.vel[2]**2),
            "privileged_state": self.get_privileged_state(),
            "student_obs": self.get_student_observation()
        }

        return obs, step_reward, terminated, truncated, info

    def _dist_to_gate(self, gate: FlightGate) -> float:
        """Euclidean distance to the center of a flight gate."""
        return math.sqrt((self.pos[0] - gate.x)**2 + (self.pos[1] - gate.y)**2 + (self.pos[2] - gate.z)**2)

    def _compute_lidar(self) -> List[float]:
        """Calculates 8-ray 2D LiDAR distances against pillars in the drone's body heading frame."""
        readings = []
        for rel_angle in self.lidar_angles:
            # Ray angle in world coordinates
            ray_yaw = self.yaw + rel_angle
            ray_dx = math.sin(ray_yaw)
            ray_dz = -math.cos(ray_yaw)

            min_hit_dist = self.lidar_range_max

            # Check boundary walls (+-20m)
            if ray_dx > 0.001:
                t = (20.0 - self.pos[0]) / ray_dx
                if 0 < t < min_hit_dist: min_hit_dist = t
            elif ray_dx < -0.001:
                t = (-20.0 - self.pos[0]) / ray_dx
                if 0 < t < min_hit_dist: min_hit_dist = t

            if ray_dz > 0.001:
                t = (20.0 - self.pos[2]) / ray_dz
                if 0 < t < min_hit_dist: min_hit_dist = t
            elif ray_dz < -0.001:
                t = (-20.0 - self.pos[2]) / ray_dz
                if 0 < t < min_hit_dist: min_hit_dist = t

            # Check cylindrical pillars (Ray-circle intersection)
            for pillar in self.pillars:
                # Vector from drone to pillar center
                oc_x = pillar.x - self.pos[0]
                oc_z = pillar.z - self.pos[2]

                # Project onto ray direction
                t_closest = oc_x * ray_dx + oc_z * ray_dz
                if t_closest > 0:
                    perp_sq = (oc_x**2 + oc_z**2) - t_closest**2
                    r_sq = pillar.radius**2
                    if perp_sq < r_sq:
                        half_chord = math.sqrt(r_sq - perp_sq)
                        t_hit = t_closest - half_chord
                        if 0 < t_hit < min_hit_dist:
                            min_hit_dist = t_hit

            readings.append(max(0.05, min_hit_dist))
        return readings

    def _get_observation(self) -> List[float]:
        """
        Builds 23-dimensional normalized continuous state vector:
        [x/20, y/10, z/20, vx/10, vy/10, vz/10, pitch, roll, yaw/pi, wx, wy, wz,
         lidar_0..7/12, rel_dx/20, rel_dy/10, rel_dz/20]
        """
        target_gate = self.gates[self.current_gate_idx]
        rel_x = target_gate.x - self.pos[0]
        rel_y = target_gate.y - self.pos[1]
        rel_z = target_gate.z - self.pos[2]

        lidar = self._compute_lidar()

        obs = [
            self.pos[0] / 20.0,
            self.pos[1] / 10.0,
            self.pos[2] / 20.0,
            self.vel[0] / 10.0,
            self.vel[1] / 10.0,
            self.vel[2] / 10.0,
            self.pitch,
            self.roll,
            self.yaw / math.pi,
            self.ang_vel[0],
            self.ang_vel[1],
            self.ang_vel[2]
        ]
        # 8 LiDAR normalized rays
        for ray_d in lidar:
            obs.append(min(1.0, ray_d / self.lidar_range_max))

        # Target relative position
        obs.append(rel_x / 20.0)
        obs.append(rel_y / 10.0)
        obs.append(rel_z / 20.0)

        return obs

    def get_privileged_state(self) -> List[float]:
        """
        Builds 32-dimensional privileged ground-truth state vector for Teacher Policy:
        - [0:12]: Kinematics (pos/20, vel/10, pitch, roll, yaw/pi, ang_vel)
        - [12:15]: Relative vector to target gate center [dx/20, dy/10, dz/20]
        - [15:18]: Target gate 3D normal vector [nx, ny, nz]
        - [18]: Distance to target gate [dist/20]
        - [19:31]: Exact relative 2D positions of all 6 obstacle pillars [(px-x)/20, (pz-z)/20]
        - [31]: Distance to closest pillar [min_dist/20]
        """
        target_gate = self.gates[self.current_gate_idx]
        rel_x = target_gate.x - self.pos[0]
        rel_y = target_gate.y - self.pos[1]
        rel_z = target_gate.z - self.pos[2]
        gate_dist = math.sqrt(rel_x**2 + rel_y**2 + rel_z**2)

        # Gate normal orientation
        gate_normals = [
            [0.0, 0.0, 1.0],   # Gate 1
            [-1.0, 0.0, 0.0],  # Gate 2
            [0.0, 0.0, -1.0],  # Gate 3
            [1.0, 0.0, 0.0]    # Gate 4
        ]
        gnorm = gate_normals[self.current_gate_idx % len(gate_normals)]

        state = [
            self.pos[0] / 20.0,
            self.pos[1] / 10.0,
            self.pos[2] / 20.0,
            self.vel[0] / 10.0,
            self.vel[1] / 10.0,
            self.vel[2] / 10.0,
            self.pitch,
            self.roll,
            self.yaw / math.pi,
            self.ang_vel[0],
            self.ang_vel[1],
            self.ang_vel[2],
            rel_x / 20.0,
            rel_y / 10.0,
            rel_z / 20.0,
            gnorm[0],
            gnorm[1],
            gnorm[2],
            min(1.0, gate_dist / 20.0)
        ]

        # 6 Pillars relative positions
        min_p_dist = 999.0
        for pillar in self.pillars:
            p_dx = (pillar.x - self.pos[0]) / 20.0
            p_dz = (pillar.z - self.pos[2]) / 20.0
            d_sq = (pillar.x - self.pos[0])**2 + (pillar.z - self.pos[2])**2
            dist = math.sqrt(d_sq)
            if dist < min_p_dist:
                min_p_dist = dist
            state.append(p_dx)
            state.append(p_dz)

        state.append(min(1.0, min_p_dist / 20.0))
        return state

    def get_student_observation(self, noise_std: float = 0.03, dropout_prob: float = 0.02) -> List[float]:
        """
        Builds 23-dimensional deployable sensory observation with real-world sensor noise:
        - 12D Kinematics with slight IMU measurement jitter
        - 8D LiDAR normalized range with Gaussian noise & beam dropouts
        - 3D Relative target gate center
        """
        raw_obs = self._get_observation()
        if noise_std <= 0.0 and dropout_prob <= 0.0:
            return raw_obs

        noisy_obs = list(raw_obs)
        # Add slight IMU noise to velocities (idx 3..5) and angular rates (idx 9..11)
        for i in [3, 4, 5, 9, 10, 11]:
            noisy_obs[i] += random.gauss(0.0, noise_std * 0.2)

        # Add range noise and dropout to 8 LiDAR rays (idx 12..19)
        for i in range(12, 20):
            if random.random() < dropout_prob:
                noisy_obs[i] = 1.0 # Echo loss/dropout
            else:
                val = noisy_obs[i] + random.gauss(0.0, noise_std)
                noisy_obs[i] = max(0.0, min(1.0, val))

        return noisy_obs

