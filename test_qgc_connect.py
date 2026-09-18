#!/usr/bin/env python3
"""
MAVLink v2 UDP Broadcaster to connect QGroundControl on 127.0.0.1:14550 without MAVLink v1 warnings.
"""

import socket
import struct
import time

def crc_accumulate(buf: bytes, crc: int = 0xFFFF) -> int:
    for b in buf:
        tmp = b ^ (crc & 0xFF)
        tmp = (tmp ^ (tmp << 4)) & 0xFF
        crc = (crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)
    return crc & 0xFFFF

def build_mavlink2_packet(sysid: int, compid: int, seq: int, msgid: int, payload: bytes, crc_extra: int) -> bytes:
    """Builds a standard MAVLink v2 binary packet (0xFD STX header)."""
    incompat_flags = 0
    compat_flags = 0
    msgid_bytes = struct.pack('<I', msgid)[:3]
    header = struct.pack('<BBBBBBB', 0xFD, len(payload), incompat_flags, compat_flags, seq & 0xFF, sysid, compid) + msgid_bytes
    buf_to_crc = header[1:] + payload + bytes([crc_extra])
    crc = crc_accumulate(buf_to_crc, 0xFFFF)
    return header + payload + struct.pack('<H', crc)

def encode_heartbeat(seq: int, armed: bool = True) -> bytes:
    custom_mode = 0x00060000  # PX4 OFFBOARD Main Mode
    mav_type = 2
    autopilot = 12
    base_mode = 209 if armed else 81
    payload = struct.pack('<IBBBBB', custom_mode, mav_type, autopilot, base_mode, 4, 3)
    return build_mavlink2_packet(1, 1, seq, 0, payload, 50)

def encode_sys_status(seq: int) -> bytes:
    sensors = 0xFFFFFFFF
    load = 200
    voltage = 11800  # 11.8V
    current = 1500   # 15A
    battery_remaining = 95
    payload = struct.pack('<IIIHHhHHHHHHb', sensors, sensors, sensors, load, voltage, current, 0, 0, 0, 0, 0, 0, battery_remaining)
    return build_mavlink2_packet(1, 1, seq, 1, payload, 124)

def encode_global_position_int(seq: int, lat=250330000, lon=121565000, alt=10000, relative_alt=3000, vx=0, vy=0, vz=0, hdg=9000) -> bytes:
    boot_ms = int(time.time() * 1000) & 0xFFFFFFFF
    payload = struct.pack('<IiiiihhhH', boot_ms, lat, lon, alt, relative_alt, vx, vy, vz, hdg)
    return build_mavlink2_packet(1, 1, seq, 33, payload, 104)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.05)
    dest = ("127.0.0.1", 14550)
    print(f"Broadcasting MAVLink v2 telemetry to QGroundControl at {dest[0]}:{dest[1]}...")

    seq = 0
    while True:
        try:
            sock.sendto(encode_heartbeat(seq, armed=True), dest)
            sock.sendto(encode_sys_status(seq), dest)
            sock.sendto(encode_global_position_int(seq), dest)
            seq = (seq + 1) % 256
        except Exception:
            pass
        time.sleep(0.15)

if __name__ == "__main__":
    main()
