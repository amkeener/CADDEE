#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

from utils.constants import ensure_session_log_dir

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--chat', action='store_true', help='Copy transcript to chat.json')
        args = parser.parse_args()

        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        # Extract required fields
        session_id = input_data.get("session_id", "unknown")
        stop_hook_active = input_data.get("stop_hook_active", False)

        # Ensure session log directory exists
        log_dir = ensure_session_log_dir(session_id)
        log_path = log_dir / "stop.json"

        # Read existing log data or initialize empty list
        if log_path.exists():
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []

        # Append new data
        log_data.append(input_data)

        # Write back to file with formatting
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)

        # Handle --chat switch
        if args.chat and 'transcript_path' in input_data:
            transcript_path = input_data['transcript_path']
            if os.path.exists(transcript_path):
                # Read .jsonl file and convert to JSON array
                chat_data = []
                try:
                    with open(transcript_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    chat_data.append(json.loads(line))
                                except json.JSONDecodeError:
                                    pass  # Skip invalid lines

                    # Write to session-specific chat.json
                    chat_file = log_dir / 'chat.json'
                    with open(chat_file, 'w') as f:
                        json.dump(chat_data, f, indent=2)
                except Exception:
                    pass  # Fail silently

        # Generate session summary (non-ADW fallback)
        generate_summary_on_stop(input_data, log_dir)

        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)


def generate_summary_on_stop(input_data: dict, log_dir: Path):
    """Generate session summary if transcript exists (non-ADW sessions only)."""
    import time

    session_id = input_data.get("session_id", "")
    transcript_path = input_data.get("transcript_path")

    if not transcript_path or not os.path.exists(transcript_path):
        return

    # Check if ADW already generated summary for this session
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    adw_marker = Path(project_dir) / ".claude/adws/.last_summary_session"
    if adw_marker.exists():
        try:
            marker_session = adw_marker.read_text().strip()
            if marker_session == session_id:
                # ADW handled this session, skip
                return
        except Exception:
            pass

    # Check if summary already exists (from /wrap_up)
    summary_path = Path(project_dir) / "wip_summary.md"
    if summary_path.exists():
        try:
            # Check modification time - if recent (within 5 min), skip
            if time.time() - summary_path.stat().st_mtime < 300:
                return
        except Exception:
            pass

    # Generate summary
    try:
        subprocess.run(
            [
                "python3",
                ".claude/scripts/generate_session_summary.py",
                "--transcript", transcript_path,
                "--output", "wip_summary.md",
            ],
            cwd=project_dir,
            capture_output=True,
            timeout=30,
        )
    except Exception:
        pass  # Fail silently - never block session end


if __name__ == "__main__":
    main()
