#!/usr/bin/env python3
"""
Taskboard Zero-Token Watcher Daemon
Monitors dashi-taskboard via taskctl CLI every 5 minutes.
Uses 0 LLM tokens when no TODO tasks are present.
"""

import json
import subprocess
import time
import sys
from pathlib import Path

PROJECT_ID = "digital-twin-drone-mvp"
CHECK_INTERVAL_SEC = 300  # 5 minutes

def check_taskboard_todo():
    try:
        res = subprocess.run(
            ["taskctl", "issue", "list", "--json"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(res.stdout)
        tasks = data.get("tasks", [])
        
        todo_tasks = [
            t for t in tasks 
            if t.get("projectId") == PROJECT_ID and t.get("status") == "todo" and not t.get("archivedAt")
        ]
        return todo_tasks
    except Exception as e:
        print(f"[Watcher Error] Failed to query taskctl: {e}", file=sys.stderr)
        return []

def main():
    print(f"🚀 Taskboard Zero-Token Watcher Started for project: '{PROJECT_ID}'")
    print(f"⏱️ Check interval: {CHECK_INTERVAL_SEC}s. Zero LLM tokens consumed while idle.\n")
    
    while True:
        todos = check_taskboard_todo()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        if todos:
            print(f"[{timestamp}] 🔔 FOUND {len(todos)} TODO TASK(S):")
            for t in todos:
                print(f"  - [{t.get('identifier', 'N/A')}] {t.get('title')}")
            print("  --> Triggering Agent Execution...")
        else:
            print(f"[{timestamp}] 💤 Idle: 0 TODO tasks in '{PROJECT_ID}'. Sleeping {CHECK_INTERVAL_SEC}s... (0 LLM Tokens)")
            
        sys.stdout.flush()
        time.sleep(CHECK_INTERVAL_SEC)

if __name__ == "__main__":
    main()
