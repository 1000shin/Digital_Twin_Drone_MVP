#!/usr/bin/env python3
"""
Zero-Token IDE Transcript File Change Watcher Daemon
Monitors file modification time & size of active Antigravity IDE transcripts in ~/.gemini/antigravity/brain/
Automatically triggers sync_ide_tokens.py whenever a change (new prompt/response/conversation) occurs.
Consumes 0 LLM Tokens while waiting!
"""

import os
import sys
import time
import subprocess
from pathlib import Path

ANTIGRAVITY_BRAIN = Path.home() / ".gemini" / "antigravity" / "brain"
SYNC_SCRIPT = Path(__file__).parent / "sync_ide_tokens.py"
CHECK_INTERVAL_SEC = 10  # Check every 10 seconds

def get_latest_transcript():
    """Finds the most recently modified transcript file and its mtime/size."""
    transcripts = []
    brain_dir = str(ANTIGRAVITY_BRAIN)
    if os.path.exists(brain_dir):
        for dp, dn, filenames in os.walk(brain_dir):
            for f in filenames:
                if f == "transcript.jsonl":
                    transcripts.append(os.path.join(dp, f))
    if not transcripts:
        return None, 0, 0
        
    latest_file = max(transcripts, key=os.path.getmtime)
    mtime = os.path.getmtime(latest_file)
    size = os.path.getsize(latest_file)
    return latest_file, mtime, size

def main():
    print(f"🚀 Zero-Token IDE Transcript Watcher Started.")
    print(f"⏱️ Monitoring '{ANTIGRAVITY_BRAIN}' every {CHECK_INTERVAL_SEC}s (0 LLM Tokens used while idle).\n")
    sys.stdout.flush()
    
    last_file = None
    last_mtime = 0
    last_size = 0
    
    while True:
        current_file, current_mtime, current_size = get_latest_transcript()
        
        if current_file:
            # Trigger sync if file path, modification time, or file size changes!
            if current_file != last_file or current_mtime > last_mtime or current_size != last_size:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] ⚡ Detected transcript file change: {Path(current_file).parents[2].name[:8]}...")
                print(f"   --> Triggering sync_ide_tokens.py...")
                sys.stdout.flush()
                
                try:
                    subprocess.run([sys.executable, str(SYNC_SCRIPT)], check=True)
                except Exception as e:
                    print(f"[Watcher Error] Sync failed: {e}", file=sys.stderr)
                    
                last_file = current_file
                last_mtime = current_mtime
                last_size = current_size
                
        time.sleep(CHECK_INTERVAL_SEC)

if __name__ == "__main__":
    main()
