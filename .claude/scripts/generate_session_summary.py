#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Generate session summary from transcript.

Usage:
    generate_session_summary.py --transcript PATH [--output PATH] [--adw-state PATH]

Outputs:
    - wip_summary.md (for /prime) - human readable
    - session-summaries/{date}/{id}.yaml (for learning) - structured
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional
import yaml


@dataclass
class SessionSummary:
    """Summary of a Claude Code session."""
    session_id: str
    date: str
    duration_minutes: int

    # Work done
    commits: list[str] = field(default_factory=list)
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    commands_run: list[str] = field(default_factory=list)

    # Decisions & context
    key_decisions: list[str] = field(default_factory=list)
    errors_encountered: list[str] = field(default_factory=list)

    # Forward-looking
    todos: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    # For learning
    domains_touched: list[str] = field(default_factory=list)
    patterns_used: list[str] = field(default_factory=list)


def parse_transcript(path: Path) -> list[dict]:
    """Parse JSONL transcript into structured messages."""
    messages = []
    try:
        with open(path) as f:
            for line in f:
                if line.strip():
                    try:
                        messages.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception:
        pass
    return messages


def extract_session_metadata(messages: list[dict]) -> dict:
    """Extract session ID, timestamps, duration."""
    first_ts = None
    last_ts = None
    session_id = "unknown"

    for msg in messages:
        ts = msg.get("timestamp") or msg.get("ts")
        if ts:
            try:
                if isinstance(ts, str):
                    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                elif isinstance(ts, (int, float)):
                    parsed = datetime.fromtimestamp(ts / 1000 if ts > 1e12 else ts)
                else:
                    continue

                if first_ts is None:
                    first_ts = parsed
                last_ts = parsed
            except Exception:
                continue

        sid = msg.get("session_id") or msg.get("sessionId")
        if sid:
            session_id = sid

    duration = 0
    if first_ts and last_ts:
        duration = int((last_ts - first_ts).total_seconds() / 60)

    return {
        "session_id": session_id,
        "duration_minutes": max(0, duration),
        "date": datetime.now().strftime("%Y-%m-%d"),
    }


def get_message_content(msg: dict) -> tuple[str, list]:
    """Extract role and content from Claude Code transcript format."""
    message = msg.get("message", {})
    role = message.get("role", msg.get("role", ""))
    content = message.get("content", msg.get("content", []))
    return role, content


def extract_file_changes(messages: list[dict]) -> dict:
    """Extract files created/modified from tool calls."""
    created, modified = [], []

    for msg in messages:
        role, content = get_message_content(msg)

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool = item.get("name", "")
                    inp = item.get("input", {})

                    if tool == "Write":
                        path = inp.get("file_path", "")
                        if path:
                            created.append(path)
                    elif tool == "Edit":
                        path = inp.get("file_path", "")
                        if path:
                            modified.append(path)

    return {
        "created": list(set(created)),
        "modified": list(set(modified)),
    }


def extract_commits(messages: list[dict]) -> list[str]:
    """Extract git commits made during session."""
    commits = []
    patterns = [
        re.compile(r'\[main ([a-f0-9]+)\]'),
        re.compile(r'\[master ([a-f0-9]+)\]'),
        re.compile(r'commit ([a-f0-9]{7,40})'),
        re.compile(r'Created commit ([a-f0-9]+)'),
    ]

    for msg in messages:
        role, content = get_message_content(msg)

        if isinstance(content, str):
            for pattern in patterns:
                matches = pattern.findall(content)
                commits.extend(matches)
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text", "") or item.get("content", "")
                    if isinstance(text, str):
                        for pattern in patterns:
                            matches = pattern.findall(text)
                            commits.extend(matches)

    return list(set(commits))


def generate_markdown(summary: SessionSummary) -> str:
    """Generate human-readable markdown for /prime."""
    lines = [
        f"# Session Summary",
        f"**Date:** {summary.date}",
        f"**Session:** {summary.session_id[:8] if len(summary.session_id) > 8 else summary.session_id}",
        f"**Duration:** ~{summary.duration_minutes} min",
        "",
    ]

    if summary.commits:
        lines.append("## Commits")
        for c in summary.commits[:10]:
            lines.append(f"- `{c[:8]}`")
        lines.append("")

    if summary.files_created:
        lines.append("## Files Created")
        for f in summary.files_created[:15]:
            lines.append(f"- `{f}`")
        lines.append("")

    if summary.files_modified:
        lines.append("## Files Modified")
        for f in summary.files_modified[:15]:
            lines.append(f"- `{f}`")
        lines.append("")

    if summary.key_decisions:
        lines.append("## Key Decisions")
        for d in summary.key_decisions:
            lines.append(f"- {d}")
        lines.append("")

    if summary.errors_encountered:
        lines.append("## Errors Encountered")
        for e in summary.errors_encountered[:5]:
            lines.append(f"- `{e}`")
        lines.append("")

    if summary.todos:
        lines.append("## Open TODOs")
        for t in summary.todos:
            lines.append(f"- [ ] {t}")
        lines.append("")

    if summary.next_steps:
        lines.append("## Next Steps")
        for n in summary.next_steps:
            lines.append(f"- {n}")
        lines.append("")

    if summary.domains_touched:
        lines.append("## Domains Touched")
        lines.append(f"- {', '.join(summary.domains_touched)}")
        lines.append("")

    return "\n".join(lines)


def generate_yaml(summary: SessionSummary) -> str:
    """Generate structured YAML for learning pipeline."""
    return yaml.dump(asdict(summary), default_flow_style=False, sort_keys=False)


def load_adw_state(path: Optional[str]) -> Optional[dict]:
    """Load ADW workflow state if provided."""
    if not path:
        return None
    state_path = Path(path)
    if not state_path.exists():
        return None
    try:
        with open(state_path) as f:
            return json.load(f)
    except Exception:
        return None


def enrich_with_adw(summary: SessionSummary, adw_state: dict) -> SessionSummary:
    """Enrich summary with ADW workflow details."""
    expert = adw_state.get("expert_used")
    if expert:
        summary.patterns_used.append(f"expert:{expert}")

    workflow_type = adw_state.get("workflow_type", "")
    if workflow_type:
        summary.patterns_used.append(f"workflow:{workflow_type}")

    plan_path = adw_state.get("plan_path")
    if plan_path:
        summary.next_steps.append(f"Plan: {plan_path}")

    for step in adw_state.get("steps", []):
        if step.get("status") == "completed":
            step_name = step.get("name", "unknown")
            summary.commands_run.append(f"adw:{step_name}")

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Generate session summary from transcript"
    )
    parser.add_argument(
        "--transcript",
        required=True,
        help="Path to transcript JSONL"
    )
    parser.add_argument(
        "--output",
        default="wip_summary.md",
        help="Output markdown path (default: wip_summary.md)"
    )
    parser.add_argument(
        "--yaml-dir",
        default=".claude/learning/session-summaries",
        help="Directory for YAML summaries"
    )
    parser.add_argument(
        "--no-yaml",
        action="store_true",
        help="Skip YAML output"
    )
    parser.add_argument(
        "--adw-state",
        help="Path to ADW state.json (optional)"
    )
    args = parser.parse_args()

    transcript_path = Path(args.transcript)
    if not transcript_path.exists():
        print(f"Transcript not found: {transcript_path}", file=sys.stderr)
        return 1

    messages = parse_transcript(transcript_path)
    if not messages:
        print("No messages in transcript", file=sys.stderr)
        return 0

    metadata = extract_session_metadata(messages)
    files = extract_file_changes(messages)

    summary = SessionSummary(
        session_id=metadata["session_id"],
        date=metadata["date"],
        duration_minutes=metadata["duration_minutes"],
        commits=extract_commits(messages),
        files_created=files["created"],
        files_modified=files["modified"],
        commands_run=[],
        key_decisions=[],
        errors_encountered=[],
        todos=[],
        next_steps=[],
        domains_touched=[],
        patterns_used=[],
    )

    adw_state = load_adw_state(args.adw_state)
    if adw_state:
        summary = enrich_with_adw(summary, adw_state)

    md_content = generate_markdown(summary)

    output_path = Path(args.output)
    output_path.write_text(md_content)
    print(f"Wrote: {output_path}")

    if not args.no_yaml:
        yaml_dir = Path(args.yaml_dir) / metadata["date"]
        yaml_dir.mkdir(parents=True, exist_ok=True)
        session_short = metadata["session_id"][:8] if len(metadata["session_id"]) > 8 else metadata["session_id"]
        yaml_path = yaml_dir / f"{session_short}.yaml"
        yaml_path.write_text(generate_yaml(summary))
        print(f"Wrote: {yaml_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
