#!/usr/bin/env python3
"""
Antigravity IDE Transcript Token Synchronizer
Reads active conversation transcripts from ~/.gemini/antigravity/brain/
and syncs token usage into ~/.gemini/antigravity-cli/usage/usage-YYYY-MM-DD.jsonl
WITHOUT altering any official statusline-token.sh or settings.json files.
"""

import json
import os
from datetime import datetime
from pathlib import Path
import re

ANTIGRAVITY_BRAIN = Path.home() / ".gemini" / "antigravity" / "brain"
CLI_USAGE_DIR = Path.home() / ".gemini" / "antigravity-cli" / "usage"

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
    """Parses transcript.jsonl to calculate turns, token estimates, and detect active model."""
    if not os.path.exists(transcript_file):
        return 0, 0, 0, "gemini-3.6-flash"
    
    total_bytes = os.path.getsize(transcript_file)
    turns = 0
    model = "gemini-3.6-flash"
    
    with open(transcript_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("type") == "USER_INPUT":
                    turns += 1
                
                content = data.get("content", "")
                if isinstance(content, str):
                    # Check for explicit model selection change
                    m_match = re.search(r"Model Selection` from \S+ to Gemini\s+([\d\.]+)\s+([A-Za-z]+)", content)
                    if not m_match:
                        m_match = re.search(r"Gemini\s+([\d\.]+)\s+([A-Za-z]+)", content)
                    if m_match:
                        ver, flavor = m_match.group(1), m_match.group(2).lower()
                        model = f"gemini-{ver}-{flavor}"
            except Exception:
                continue
                
    # Approximate token calculation from transcript payload volume (1 token ≈ 4 chars)
    total_tokens = max(1000, total_bytes // 4)
    input_tokens = int(total_tokens * 0.8)
    output_tokens = int(total_tokens * 0.2)
    
    return turns, input_tokens, output_tokens, model

def clean_topic_summary(raw_text):
    """Extracts a clean and concise topic label from user request."""
    # 1. Dashi task pattern: [DIG-12] -> Dashi 看板任務(DIG-12)
    dashi = re.search(r"\[(DIG-\d+)\]", raw_text)
    if dashi:
        return f"Dashi 看板任務({dashi.group(1)})"
        
    # 2. Check common task domain keywords
    lower = raw_text.lower()
    if any(k in lower for k in ["短影音", "剪輯", "ig短影音", "reels"]):
        return "短影音剪輯"
        
    if "graph view" in lower or "obsidian" in lower:
        return "Obsidian"
        
    if "sync_ide_tokens" in lower:
        return "測試 sync_ide_tokens"

    # 3. Fallback for other generic prompts: clean prompt boilerplate
    cleaned = re.sub(r"^(我現在要|我現在啟動一個新的對話[，,]|目前我|請幫我|幫我|我想|請問|你是一個專業的任務執行 Sub-agent，負責處理\s*)", "", raw_text)
    first_clause = re.split(r"[，,\n\r;；\?？]", cleaned)[0].strip(" ,，.。:：\"'“”")
    return first_clause[:12] if first_clause else "一般對話"

def extract_session_cwd_and_name(transcript_file):
    """Extracts working directory (cwd) and pure session name from transcript.jsonl."""
    cwd = None
    topic_summary = None
    
    if os.path.exists(transcript_file):
        with open(transcript_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                    
                content = data.get("content", "")
                if isinstance(content, str) and not topic_summary:
                    if data.get("type") == "USER_INPUT":
                        req_m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
                        raw_text = req_m.group(1).strip() if req_m else content.strip()
                        topic_summary = clean_topic_summary(raw_text)

                # Look for tool call directories to determine actual working cwd
                for tc in data.get("tool_calls", []):
                    args = tc.get("args", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            pass
                    for k in ["Cwd", "SearchDirectory", "SearchPath", "TargetFile", "AbsolutePath"]:
                        v = args.get(k)
                        if v and isinstance(v, str):
                            v = v.strip("\"'")
                            if os.path.exists(v):
                                cwd = v if os.path.isdir(v) else os.path.dirname(v)
                                break
                    if cwd:
                        break

    if not cwd:
        cwd = os.getcwd()

    if not topic_summary:
        topic_summary = "一般對話"

    session_name = f"AI agent-{topic_summary}"
    return cwd, session_name

TOKEN_INSIGHTS_DB = Path.home() / ".token-usage-insights" / "token_usage_insights.db"

def build_session_entry(session_id, transcript_file, today_str):
    turns, input_tokens, output_tokens, model = parse_transcript_tokens(transcript_file)
    total_tokens = input_tokens + output_tokens
    cwd, session_name = extract_session_cwd_and_name(transcript_file)
    now_iso = datetime.now().astimezone().isoformat()
    
    entry = {
        "timestamp": now_iso,
        "session_id": session_id,
        "session_name": session_name,
        "transcript_path": str(transcript_file),
        "cwd": cwd,
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
    return entry, turns, total_tokens, session_name, model, cwd

def sync_tokens():
    today_str = datetime.now().strftime("%Y-%m-%d")
    CLI_USAGE_DIR.mkdir(parents=True, exist_ok=True)
    jsonl_file = CLI_USAGE_DIR / f"usage-{today_str}.jsonl"
    
    # 1. Gather all sessions updated today
    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    today_sessions = {}
    
    if brain_dir.exists():
        for t_file in brain_dir.glob("*/.system_generated/logs/transcript.jsonl"):
            try:
                mtime_str = datetime.fromtimestamp(t_file.stat().st_mtime).strftime("%Y-%m-%d")
                if mtime_str == today_str:
                    sid = t_file.parents[2].name
                    today_sessions[sid] = t_file
            except Exception:
                continue

    if not today_sessions:
        # Fallback to single latest session
        latest_sid, latest_tf = get_latest_session()
        if latest_sid and latest_tf:
            today_sessions[latest_sid] = Path(latest_tf)

    if not today_sessions:
        print("[IDE Sync] No active conversation transcripts found.")
        return

    # 2. Append latest records and update local DB
    db_updates = []
    with open(jsonl_file, "a", encoding="utf-8") as f:
        for sid, tf in today_sessions.items():
            entry, turns, total_tokens, session_name, model, cwd = build_session_entry(sid, tf, today_str)
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            db_updates.append((session_name, model, model, cwd, sid, today_str))
            print(f"✅ [IDE Sync] Synced Session '{sid[:8]}...' ({session_name} | {model})")

    # 3. If token_usage_insights SQLite DB exists, update session metadata for today
    if TOKEN_INSIGHTS_DB.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(TOKEN_INSIGHTS_DB)
            cur = conn.cursor()
            for update_item in db_updates:
                cur.execute("""
                    UPDATE usage_entries
                    SET session_name = ?, model = ?, model_id = ?, cwd = ?
                    WHERE session_id = ? AND date = ?;
                """, update_item)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[IDE Sync Warning] DB metadata update skipped: {e}")

    # 4. Trigger War Room refresh if accessible
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:3003/api/antigravity/sync", timeout=1)
    except Exception:
        pass

if __name__ == "__main__":
    sync_tokens()
