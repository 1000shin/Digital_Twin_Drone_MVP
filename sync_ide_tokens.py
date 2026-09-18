#!/usr/bin/env python3
"""
Antigravity IDE Transcript Token Synchronizer
Reads active conversation transcripts from ~/.gemini/antigravity/brain/
and syncs token usage into ~/.gemini/antigravity-cli/usage/usage-YYYY-MM-DD.jsonl
WITHOUT altering any official statusline-token.sh or settings.json files.
"""

import json
import os
import glob
import time
from datetime import datetime
from pathlib import Path

ANTIGRAVITY_BRAIN = Path.home() / ".gemini" / "antigravity" / "brain"
CLI_USAGE_DIR = Path.home() / ".gemini" / "antigravity-cli" / "usage"
PROJECT_CWD = "/Users/jasonzheng/Documents/Obsidian workspace/AI agent workspace/Digital_Twin_Drone_MVP"

def get_latest_session():
    """Finds the most recently updated conversation transcript using os.walk."""
    transcripts = []
    brain_dir = str(ANTIGRAVITY_BRAIN)
    if os.path.exists(brain_dir):
        for dp, dn, filenames in os.walk(brain_dir):
            for f in filenames:
                if f == "transcript.jsonl":
                    transcripts.append(os.path.join(dp, f))
    if not transcripts:
        return None, None
    latest_file = max(transcripts, key=os.path.getmtime)
    session_id = Path(latest_file).parents[2].name
    return session_id, latest_file

def parse_transcript_tokens(transcript_file):
    """Parses transcript.jsonl to calculate turns and token estimates."""
    if not os.path.exists(transcript_file):
        return 0, 0, 0, "gemini-3.6-flash"
    
    total_bytes = os.path.getsize(transcript_file)
    turns = 0
    
    with open(transcript_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("type") == "USER_INPUT":
                    turns += 1
            except Exception:
                continue
                
    # Approximate token calculation from transcript payload volume (1 token ≈ 4 chars)
    total_tokens = max(1000, total_bytes // 4)
    input_tokens = int(total_tokens * 0.8)
    output_tokens = int(total_tokens * 0.2)
    
    return turns, input_tokens, output_tokens, "gemini-3.6-flash"

def sync_tokens():
    session_id, transcript_file = get_latest_session()
    if not session_id or not transcript_file:
        print("[IDE Sync] No active conversation transcripts found.")
        return

    turns, input_tokens, output_tokens, model = parse_transcript_tokens(transcript_file)
    total_tokens = input_tokens + output_tokens
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    now_iso = datetime.now().astimezone().isoformat()
    
    CLI_USAGE_DIR.mkdir(parents=True, exist_ok=True)
    jsonl_file = CLI_USAGE_DIR / f"usage-{today_str}.jsonl"
    
    entry = {
        "timestamp": now_iso,
        "session_id": session_id,
        "session_name": "Digital Twin Drone MVP",
        "transcript_path": transcript_file,
        "cwd": PROJECT_CWD,
        "version": "1.0.0",
        "turn_no": turns,
        "model": model,
        "model_id": model,
        "previous_model": "",
        "model_changed": False,
        "tokens": {
            "input": input_tokens,
            "output": output_tokens,
            "cache_read": 0,
            "cache_write": 0,
            "reasoning": 0,
            "total": total_tokens,
            "last_call_input": input_tokens,
            "last_call_output": output_tokens
        },
        "delta_tokens": {
            "input": input_tokens,
            "output": output_tokens,
            "cache_read": 0,
            "cache_write": 0,
            "reasoning": 0,
            "total": total_tokens
        },
        "context": {
            "current_context_tokens": total_tokens,
            "displayed_context_limit": 1000000,
            "current_context_used_percentage": f"{min(100, (total_tokens / 1000000) * 100):.2f}"
        },
        "cost": {
            "total_api_duration_ms": 0,
            "total_duration_ms": 0,
            "total_premium_requests": 0,
            "total_lines_added": 0,
            "total_lines_removed": 0
        }
    }
    
    with open(jsonl_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
    print(f"✅ [IDE Sync] Successfully synced IDE Session '{session_id[:8]}...' ({turns} turns, {total_tokens} tokens) into {jsonl_file.name}")

if __name__ == "__main__":
    sync_tokens()
