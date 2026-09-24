#!/usr/bin/env python3
"""
Privileged Deep Reinforcement Learning & Teacher-Student Distillation Trainer
(FEAT-M2.5.2-PRIVILEGED-DRL-DISTILLATION)

Framework:
1. Teacher Policy: Trained on 32-dim privileged ground-truth state (perfect kinematics & true obstacle coordinates).
2. Student Policy: 23-dim deployable sensor observations (8-ray LiDAR with noise/dropout & IMU noise).
3. Distillation: DAgger / Policy Distillation transfer learning.
4. Multi-Stage Checkpoints: Saves Stage 0 (0% untrained), Stage 1 (40% half-trained), Stage 2 (100% mastered).
5. Weight Exporter: Exports pure JSON weight matrices for zero-dependency NumPy & Three.js runtime.
"""

import os
import sys
import math
import json
import time
import argparse
from typing import Dict, Any, List, Tuple

import torch
import torch.nn as nn
import torch.optim as optim

from drone_rl_env import DroneRLEnvironment


# ==========================================
# 1. Neural Network Architectures
# ==========================================

class TeacherPolicy(nn.Module):
    """
    Privileged Teacher Policy Network.
    Input: 32-dim privileged state (full kinematics, exact gate normal, exact 6 pillar vectors).
    Output: 4-dim flight control action [-1.0, 1.0] -> [pitch, roll, yaw_rate, throttle].
    """
    def __init__(self, state_dim: int = 32, action_dim: int = 4, hidden_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
            nn.Tanh()
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        return self.net(state)


class StudentPolicy(nn.Module):
    """
    Deployable Student Policy Network.
    Input: 23-dim sensory observation (8-ray LiDAR with noise, IMU readings, relative gate target).
    Output: 4-dim flight control action [-1.0, 1.0] -> [pitch, roll, yaw_rate, throttle].
    """
    def __init__(self, obs_dim: int = 23, action_dim: int = 4, hidden_dim: int = 64):
        super().__init__()
        self.fc1 = nn.Linear(obs_dim, hidden_dim)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(hidden_dim, action_dim)
        self.tanh = nn.Tanh()

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        x = self.relu1(self.fc1(obs))
        x = self.relu2(self.fc2(x))
        return self.tanh(self.fc3(x))

    def export_weights_dict(self) -> Dict[str, Any]:
        """Exports weights and biases as serializable Python lists for pure NumPy / JS."""
        return {
            "w1": self.fc1.weight.detach().cpu().numpy().tolist(),
            "b1": self.fc1.bias.detach().cpu().numpy().tolist(),
            "w2": self.fc2.weight.detach().cpu().numpy().tolist(),
            "b2": self.fc2.bias.detach().cpu().numpy().tolist(),
            "w3": self.fc3.weight.detach().cpu().numpy().tolist(),
            "b3": self.fc3.bias.detach().cpu().numpy().tolist()
        }


# ==========================================
# 2. Privileged Expert Guidance & Distillation
# ==========================================

class PrivilegedExpertSupervisor:
    """
    Analytical / High-Fidelity Privileged Expert to supervise Teacher Policy
    using full 3D ground truth knowledge (Pillar centers, Gate corridor, Wind vector).
    """
    def __init__(self, env: DroneRLEnvironment):
        self.env = env

    def compute_optimal_privileged_action(self, priv_state: List[float]) -> List[float]:
        """
        Calculates optimal continuous 4D vector:
        1. Attractive acceleration to current gate center.
        2. Non-linear repulsive acceleration from true 3D pillar cylinders.
        3. Orthogonal tangential glide deflection to avoid deadlocks.
        """
        # Unpack state: pos = priv_state[0:3] * [20, 10, 20]
        # rel_gate = priv_state[12:15] * [20, 10, 20]
        pos_x = priv_state[0] * 20.0
        pos_y = priv_state[1] * 10.0
        pos_z = priv_state[2] * 20.0

        rel_gx = priv_state[12] * 20.0
        rel_gy = priv_state[13] * 10.0
        rel_gz = priv_state[14] * 20.0

        target_dist = math.sqrt(rel_gx**2 + rel_gz**2)
        if target_dist < 1e-4:
            target_dist = 1e-4

        # Gate attraction unit vector
        att_x = rel_gx / target_dist
        att_z = rel_gz / target_dist

        # Compute Repulsion from 6 pillars (dx = priv_state[19, 21, ...], dz = priv_state[20, 22, ...])
        rep_x = 0.0
        rep_z = 0.0
        tan_x = 0.0
        tan_z = 0.0

        for i in range(6):
            p_dx = priv_state[19 + i*2] * 20.0
            p_dz = priv_state[20 + i*2] * 20.0
            p_dist = math.sqrt(p_dx**2 + p_dz**2)

            # Safety clearance: 1.8m
            if 0.001 < p_dist < 2.0:
                inv_d = (2.0 - p_dist) / 2.0
                rep_strength = math.exp(inv_d * 2.2)
                # Drone to pillar is (p_dx, p_dz), so repulsive from pillar to drone is (-p_dx, -p_dz)
                dir_x = -p_dx / p_dist
                dir_z = -p_dz / p_dist
                rep_x += dir_x * rep_strength * 1.5
                rep_z += dir_z * rep_strength * 1.5

                # Tangential deflection (cross product in 2D)
                # If approaching pillar, deflect perpendicular to line connecting drone & pillar
                tan_x += -dir_z * rep_strength * 0.8
                tan_z += dir_x * rep_strength * 0.8

        # Desired horizontal heading vector
        total_fx = att_x * 0.8 + rep_x + tan_x
        total_fz = att_z * 0.8 + rep_z + tan_z

        # Pitch controls forward/backward (Z axis: -z is pitch forward in this body convention)
        cmd_pitch = max(-1.0, min(1.0, -total_fz * 0.7))
        # Roll controls right/left (X axis: +x is roll right)
        cmd_roll = max(-1.0, min(1.0, total_fx * 0.7))

        # Yaw rate to align heading with motion
        desired_yaw = math.atan2(total_fx, -total_fz)
        curr_yaw = priv_state[8] * math.pi
        yaw_err = desired_yaw - curr_yaw
        while yaw_err > math.pi: yaw_err -= 2.0 * math.pi
        while yaw_err < -math.pi: yaw_err += 2.0 * math.pi
        cmd_yaw = max(-1.0, min(1.0, yaw_err * 0.8))

        # Altitude / Throttle command
        cmd_throttle = max(-1.0, min(1.0, rel_gy * 0.9))

        return [cmd_pitch, cmd_roll, cmd_yaw, cmd_throttle]


# ==========================================
# 3. Multi-Stage Trainer & Distiller
# ==========================================

def train_and_distill(
    total_episodes: int = 50,
    lr: float = 1e-3,
    output_dir: str = "output/neural_models",
    device_name: str = "auto"
) -> Dict[str, Any]:
    """
    Main training loop for Teacher-Student distillation.
    Saves:
    1. Stage 0 (0% untrained)
    2. Stage 1 (40% half-trained)
    3. Stage 2 (100% mastered)
    """
    if device_name == "auto":
        if torch.backends.mps.is_available():
            device = torch.device("mps")
        elif torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")
    else:
        device = torch.device(device_name)

    print(f"🚀 Initializing Privileged Teacher-Student Trainer on device: {device}")
    os.makedirs(output_dir, exist_ok=True)

    env = DroneRLEnvironment(seed=42)
    expert = PrivilegedExpertSupervisor(env)

    teacher = TeacherPolicy(state_dim=32, action_dim=4, hidden_dim=128).to(device)
    student = StudentPolicy(obs_dim=23, action_dim=4, hidden_dim=64).to(device)

    optimizer_teacher = optim.Adam(teacher.parameters(), lr=lr)
    optimizer_student = optim.Adam(student.parameters(), lr=lr)
    criterion = nn.MSELoss()

    # Capture Stage 0 Checkpoint (Untrained baseline)
    stage_0_weights = student.export_weights_dict()
    stage_1_weights = None
    stage_2_weights = None

    stage_1_ep = int(total_episodes * 0.40) # e.g. Episode 20

    print(f"📊 Training Schedule: {total_episodes} Episodes | Stage 1 Checkpoint at Ep {stage_1_ep}")
    start_time = time.time()

    total_steps = 0
    total_gates = 0
    loss_history = []

    for ep in range(1, total_episodes + 1):
        env.reset()
        ep_loss = 0.0
        ep_steps = 0
        ep_gates = 0

        # Dynamic DAgger exploration parameter: beta goes from 0.0 (expert only) to 0.85 (student controls)
        beta_student = min(0.85, (ep / total_episodes) * 0.95)

        for step in range(300):
            ep_steps += 1
            total_steps += 1

            priv_state = env.get_privileged_state()
            student_obs = env.get_student_observation(noise_std=0.03, dropout_prob=0.02)

            # Compute Ground-Truth Expert Action
            expert_action = expert.compute_optimal_privileged_action(priv_state)

            # Convert to Tensors
            t_priv = torch.tensor(priv_state, dtype=torch.float32, device=device).unsqueeze(0)
            t_obs = torch.tensor(student_obs, dtype=torch.float32, device=device).unsqueeze(0)
            t_expert = torch.tensor(expert_action, dtype=torch.float32, device=device).unsqueeze(0)

            # 1. Train Teacher to align with expert ground truth
            optimizer_teacher.zero_grad()
            teacher_act = teacher(t_priv)
            loss_t = criterion(teacher_act, t_expert)
            loss_t.backward()
            optimizer_teacher.step()

            # 2. Distill Teacher Knowledge to Student Policy (DAgger / MSE loss)
            optimizer_student.zero_grad()
            student_act = student(t_obs)
            # Student learns from Teacher's outputs
            loss_s = criterion(student_act, teacher_act.detach())
            loss_s.backward()
            optimizer_student.step()

            ep_loss += loss_s.item()

            # DAgger Blended Execution in Environment
            s_act_np = student_act.squeeze(0).detach().cpu().numpy()
            t_act_np = teacher_act.squeeze(0).detach().cpu().numpy()
            blended_act = (beta_student * s_act_np + (1.0 - beta_student) * t_act_np).tolist()

            _, reward, terminated, truncated, info = env.step(blended_act)

            if info.get("passed_gate", False):
                ep_gates += 1
                total_gates += 1

            if terminated or truncated:
                break

        avg_loss = ep_loss / max(1, ep_steps)
        loss_history.append(avg_loss)

        # Checkpoint Stage 1 (40% Half-Trained)
        if ep == stage_1_ep:
            stage_1_weights = student.export_weights_dict()
            print(f"  🌿 [Stage 1 Checkpoint Captured] Ep {ep}/{total_episodes} - Distill Loss: {avg_loss:.4f}")

        if ep % 10 == 0 or ep == total_episodes:
            print(f"  [Ep {ep:02d}/{total_episodes:02d}] Steps: {ep_steps:3d} | Gates: {ep_gates} | Distill Loss: {avg_loss:.5f} | Student Beta: {beta_student:.2f}")

    elapsed = time.time() - start_time
    fps = total_steps / max(1e-4, elapsed)

    # Capture Stage 2 Checkpoint (100% Mastered)
    stage_2_weights = student.export_weights_dict()
    if stage_1_weights is None:
        stage_1_weights = stage_2_weights

    # Export Multi-Stage Archive
    stages_payload = {
        "metadata": {
            "version": "1.0",
            "model_type": "privileged_teacher_student_mlp",
            "feature_id": "FEAT-M2.5.2-PRIVILEGED-DRL-DISTILLATION",
            "timestamp": time.time(),
            "total_episodes": total_episodes,
            "total_steps": total_steps,
            "total_gates_passed": total_gates,
            "final_distill_loss": loss_history[-1] if loss_history else 0.0,
            "training_time_sec": round(elapsed, 3),
            "sim_fps": round(fps, 1),
            "device": str(device),
            "stages_info": {
                "stage_0_untrained": "Initial random exploration weights (0% trained, high collision rate)",
                "stage_1_half_trained": f"Midway distillation weights at ep {stage_1_ep} (40% trained)",
                "stage_2_mastered": f"Final mastered policy at ep {total_episodes} (100% trained, agile collision avoidance)"
            }
        },
        "stages": {
            "stage_0_untrained": stage_0_weights,
            "stage_1_half_trained": stage_1_weights,
            "stage_2_mastered": stage_2_weights
        }
    }

    stages_path = os.path.join(output_dir, "student_policy_stages.json")
    with open(stages_path, "w", encoding="utf-8") as f:
        json.dump(stages_payload, f, indent=2)

    # Export Default Mastered Weights for Zero-Dependency Runtime
    default_weights_path = os.path.join(output_dir, "student_policy_weights.json")
    with open(default_weights_path, "w", encoding="utf-8") as f:
        json.dump(stage_2_weights, f, indent=2)

    print("\n" + "="*60)
    print("✅ Privileged Teacher-Student Distillation Complete!")
    print(f"⏱️ Training Elapsed: {elapsed:.2f}s ({fps:.1f} steps/s)")
    print(f"📦 Saved Multi-Stage Checkpoints: {stages_path}")
    print(f"📦 Saved Runtime Mastered Weights: {default_weights_path}")
    print("="*60 + "\n")

    return stages_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and Distill Privileged Drone Obstacle Avoidance Policy")
    parser.add_argument("--episodes", type=int, default=50, help="Total training episodes (default: 50)")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate (default: 0.001)")
    parser.add_argument("--output_dir", type=str, default="output/neural_models", help="Output directory for weights")
    parser.add_argument("--device", type=str, default="auto", help="Compute device: auto, cpu, mps, cuda")

    args = parser.parse_args()
    train_and_distill(
        total_episodes=args.episodes,
        lr=args.lr,
        output_dir=args.output_dir,
        device_name=args.device
    )
