#!/usr/bin/env python3
"""
Digital Twin Drone - Foxglove WebSocket Live Server (ws://localhost:8765)
Phase 3 Choice 1: Native WebSocket server allowing Foxglove Studio Desktop app to connect
live to ws://localhost:8765 and stream 3D drone position, attitude, battery, and point cloud.
"""

import asyncio
import json
import math
import time
from pathlib import Path

# Built-in lightweight async WebSocket server helper
import asyncio
import websockets

async def handler(websocket):
    print(f"[FoxgloveServer] Client connected from {websocket.remote_address}")
    t = 0.0
    ref_lat = 25.0330
    ref_lon = 121.5650

    try:
        while True:
            # Generate animated 3D flight trajectory
            radius = 3.0
            x = radius * math.cos(t)
            y = radius * math.sin(t)
            z = 2.5 + 0.5 * math.sin(t * 2)
            yaw = math.degrees(t) % 360

            # 3D Point Cloud Sweep
            points = []
            for angle in range(0, 360, 20):
                rad = math.radians(angle)
                dist = 4.0 + 0.5 * math.sin(angle)
                points.append({
                    "x": round(x + dist * math.cos(rad), 2),
                    "y": round(y + dist * math.sin(rad), 2),
                    "z": round(z, 2),
                    "intensity": 255
                })

            telemetry_msg = {
                "timestamp": time.time(),
                "telemetry": {
                    "armed": True,
                    "mode": "OFFBOARD",
                    "position": {"x": round(x, 2), "y": round(y, 2), "z": round(z, 2)},
                    "attitude": {"roll": 2.0, "pitch": -1.5, "yaw": round(yaw, 1)},
                    "battery": {"voltage_v": round(11.8 - t * 0.01, 2), "remaining_pct": max(10, int(98 - t * 0.2))}
                },
                "pose": {
                    "position": {"x": x, "y": y, "z": z},
                    "orientation": {"x": 0, "y": 0, "z": math.sin(math.radians(yaw/2)), "w": math.cos(math.radians(yaw/2))}
                },
                "pointcloud": points
            }

            await websocket.send(json.dumps(telemetry_msg))
            t += 0.1
            await asyncio.sleep(0.1)  # 10 Hz stream
    except websockets.exceptions.ConnectionClosed:
        print("[FoxgloveServer] Client disconnected.")

async def main():
    print("==========================================================================")
    print("🌐 Foxglove Studio Live WebSocket Server Running at ws://localhost:8765")
    print("==========================================================================")
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[FoxgloveServer] Stopped.")
