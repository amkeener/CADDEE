#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Aggregate learnings from various sources into daily insights.

Sources:
- Git commits (last 24 hours)
- Session summaries
- ADW workflow states
- Feedback entries

Outputs:
- .claude/learning/daily-insights/{date}.yaml
- .claude/learning/submodules/{submodule}/{date}.yaml

Usage:
    aggregate_learnings.py [--days N] [--submodule NAME] [--dry-run]
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import yaml


# Known submodules
SUBMODULES = [
    "diagnostics-service",
    "frontend-2.0-anchor-planner",
    "location-service",
    "node-service",
    "wakecap-app-api",
]

# Domain detection patterns
DOMAIN_PATTERNS = {
    "react_frontend": [r"\.tsx?$", r"components?/", r"pages?/", r"hooks?/"],
    "api_integration": [r"services?/", r"api/", r"\.dto\.ts", r"controller"],
    "testing": [r"\.test\.", r"\.spec\.", r"__tests__", r"playwright/"],
    "arcgis": [r"arcgis", r"esri", r"layers?/", r"map"],
    "rf_analysis": [r"rssi", r"rf[-_]", r"signal", r"heatmap"],
    "data_analysis": [r"analysis", r"health", r"metrics", r"kpi"],
    "database": [r"migrations?/", r"\.sql$", r"prisma", r"typeorm"],
    "ci_cd": [r"\.github/", r"\.gitlab", r"Dockerfile", r"docker-compose"],
    "code_quality": [r"\.eslint", r"\.prettier", r"lint", r"format"],
}


@dataclass
class DailyInsight:
    """Daily aggregated insights."""
    date: str
    submodule: Optional[str] = None

    # From git commits
    commits_analyzed: int = 0
    domains_from_commits: list[str] = field(default_factory=list)
    hot_files: list[str] = field(default_factory=list)
    commit_types: dict[str, int] = field(default_factory=dict)

    # From session summaries
    sessions_analyzed: int = 0
    total_duration_minutes: int = 0
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)

    # From ADW states
    workflows_used: dict[str, int] = field(default_factory=dict)
    experts_used: dict[str, int] = field(default_factory=dict)
    expert_outcomes: dict[str, dict[str, int]] = field(default_factory=dict)

    # From feedback
    feedback_entries: int = 0
    positive_feedback: int = 0
    negative_feedback: int = 0

    # Derived insights
    insights: list[str] = field(default_factory=list)
    patterns_discovered: list[dict[str, Any]] = field(default_factory=list)
    errors_cataloged: list[dict[str, Any]] = field(default_factory=list)


def get_git_commits(
    repo_path: Path,
    since_days: int = 1
) -> list[dict[str, Any]]:
    """Get recent git commits."""
    since = (datetime.now() - timedelta(days=since_days)).strftime("%Y-%m-%d")

    try:
        result = subprocess.run(
            ["git", "log", f"--since={since}", "--pretty=format:%H|%s|%an|%ai", "--name-only"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return []

        commits = []
        current_commit = None

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            if "|" in line:
                # Commit header
                parts = line.split("|")
                if len(parts) >= 4:
                    current_commit = {
                        "hash": parts[0],
                        "message": parts[1],
                        "author": parts[2],
                        "date": parts[3],
                        "files": [],
                    }
                    commits.append(current_commit)
            elif current_commit:
                # File name
                current_commit["files"].append(line)

        return commits

    except Exception:
        return []


def detect_domains(files: list[str]) -> list[str]:
    """Detect domains from file paths."""
    domains = set()

    for file_path in files:
        for domain, patterns in DOMAIN_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, file_path, re.IGNORECASE):
                    domains.add(domain)
                    break

    return list(domains)


def parse_commit_type(message: str) -> str:
    """Parse conventional commit type."""
    match = re.match(r"^(\w+)(?:\([^)]+\))?:", message)
    if match:
        return match.group(1).lower()
    return "other"


def load_session_summaries(
    base_path: Path,
    since_days: int = 1
) -> list[dict[str, Any]]:
    """Load recent session summaries."""
    summaries = []
    since = datetime.now() - timedelta(days=since_days)

    # Check session-summaries directory
    summary_dir = base_path / ".claude/learning/session-summaries"
    if not summary_dir.exists():
        return summaries

    for date_dir in summary_dir.iterdir():
        if not date_dir.is_dir():
            continue

        try:
            dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
            if dir_date < since:
                continue
        except ValueError:
            continue

        for yaml_file in date_dir.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                    if data:
                        data["_file"] = str(yaml_file)
                        summaries.append(data)
            except Exception:
                continue

    return summaries


def load_adw_states(
    base_path: Path,
    since_days: int = 1
) -> list[dict[str, Any]]:
    """Load recent ADW workflow states."""
    states = []
    since = datetime.now() - timedelta(days=since_days)

    # Check adws/sessions directory
    sessions_dir = base_path / ".claude/adws/sessions"
    if not sessions_dir.exists():
        return states

    for session_dir in sessions_dir.iterdir():
        if not session_dir.is_dir():
            continue

        # Check state.json
        state_file = session_dir / "state.json"
        if not state_file.exists():
            continue

        try:
            mtime = datetime.fromtimestamp(state_file.stat().st_mtime)
            if mtime < since:
                continue

            with open(state_file) as f:
                data = json.load(f)
                data["_session_dir"] = session_dir.name
                states.append(data)
        except Exception:
            continue

    return states


def load_feedback(
    base_path: Path,
    since_days: int = 1
) -> list[dict[str, Any]]:
    """Load recent feedback entries."""
    feedback = []
    since = datetime.now() - timedelta(days=since_days)

    feedback_dir = base_path / ".claude/learning/feedback"
    if not feedback_dir.exists():
        return feedback

    for yaml_file in feedback_dir.glob("*.yaml"):
        try:
            # Check file date from name
            file_date = datetime.strptime(yaml_file.stem, "%Y-%m-%d")
            if file_date < since:
                continue
        except ValueError:
            continue

        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
                if isinstance(data, list):
                    feedback.extend(data)
                elif data:
                    feedback.append(data)
        except Exception:
            continue

    return feedback


def aggregate_for_submodule(
    submodule: str,
    base_path: Path,
    since_days: int = 1
) -> DailyInsight:
    """Aggregate learnings for a specific submodule."""
    today = datetime.now().strftime("%Y-%m-%d")
    insight = DailyInsight(date=today, submodule=submodule)

    submodule_path = base_path / submodule

    # Analyze git commits
    if submodule_path.exists():
        commits = get_git_commits(submodule_path, since_days)
        insight.commits_analyzed = len(commits)

        file_counts: dict[str, int] = {}
        for commit in commits:
            # Track commit types
            commit_type = parse_commit_type(commit.get("message", ""))
            insight.commit_types[commit_type] = insight.commit_types.get(commit_type, 0) + 1

            # Track files
            for f in commit.get("files", []):
                file_counts[f] = file_counts.get(f, 0) + 1

            # Detect domains
            domains = detect_domains(commit.get("files", []))
            for d in domains:
                if d not in insight.domains_from_commits:
                    insight.domains_from_commits.append(d)

        # Hot files (modified 3+ times)
        insight.hot_files = [f for f, count in file_counts.items() if count >= 3]

    # Note: Session summaries and ADW states are typically at project level
    # Submodule-specific data would come from tagged sessions

    return insight


def aggregate_project(
    base_path: Path,
    since_days: int = 1
) -> DailyInsight:
    """Aggregate learnings for the entire project."""
    today = datetime.now().strftime("%Y-%m-%d")
    insight = DailyInsight(date=today)

    # Analyze git commits at project level
    commits = get_git_commits(base_path, since_days)
    insight.commits_analyzed = len(commits)

    file_counts: dict[str, int] = {}
    for commit in commits:
        commit_type = parse_commit_type(commit.get("message", ""))
        insight.commit_types[commit_type] = insight.commit_types.get(commit_type, 0) + 1

        for f in commit.get("files", []):
            file_counts[f] = file_counts.get(f, 0) + 1

        domains = detect_domains(commit.get("files", []))
        for d in domains:
            if d not in insight.domains_from_commits:
                insight.domains_from_commits.append(d)

    insight.hot_files = [f for f, count in file_counts.items() if count >= 3]

    # Load session summaries
    summaries = load_session_summaries(base_path, since_days)
    insight.sessions_analyzed = len(summaries)

    for summary in summaries:
        insight.total_duration_minutes += summary.get("duration_minutes", 0)
        insight.files_created.extend(summary.get("files_created", []))
        insight.files_modified.extend(summary.get("files_modified", []))

    # Deduplicate file lists
    insight.files_created = list(set(insight.files_created))
    insight.files_modified = list(set(insight.files_modified))

    # Load ADW states
    adw_states = load_adw_states(base_path, since_days)
    for state in adw_states:
        workflow_type = state.get("workflow_type", "unknown")
        insight.workflows_used[workflow_type] = insight.workflows_used.get(workflow_type, 0) + 1

        expert = state.get("expert_used", "unknown")
        insight.experts_used[expert] = insight.experts_used.get(expert, 0) + 1

        # Track expert outcomes
        outcome = state.get("outcome", "unknown")
        if expert not in insight.expert_outcomes:
            insight.expert_outcomes[expert] = {}
        insight.expert_outcomes[expert][outcome] = insight.expert_outcomes[expert].get(outcome, 0) + 1

    # Load feedback
    feedback_entries = load_feedback(base_path, since_days)
    insight.feedback_entries = len(feedback_entries)

    for entry in feedback_entries:
        feedback_type = entry.get("type", "").lower()
        if feedback_type in ["positive", "success", "good"]:
            insight.positive_feedback += 1
        elif feedback_type in ["negative", "failure", "bad"]:
            insight.negative_feedback += 1

    # Generate derived insights
    insight.insights = generate_insights(insight)

    return insight


def generate_insights(insight: DailyInsight) -> list[str]:
    """Generate human-readable insights from aggregated data."""
    insights = []

    # Activity level
    if insight.commits_analyzed > 10:
        insights.append(f"High activity: {insight.commits_analyzed} commits analyzed")
    elif insight.commits_analyzed > 0:
        insights.append(f"Normal activity: {insight.commits_analyzed} commits analyzed")

    # Dominant commit types
    if insight.commit_types:
        top_type = max(insight.commit_types.items(), key=lambda x: x[1])
        insights.append(f"Primary work type: {top_type[0]} ({top_type[1]} commits)")

    # Hot files indicator
    if insight.hot_files:
        insights.append(f"Hot files ({len(insight.hot_files)}): Files with high churn may need refactoring")

    # Expert success rates
    for expert, outcomes in insight.expert_outcomes.items():
        total = sum(outcomes.values())
        successes = outcomes.get("success", 0) + outcomes.get("completed", 0)
        if total >= 3:
            rate = successes / total
            if rate < 0.7:
                insights.append(f"Expert '{expert}' has {rate:.0%} success rate - may need review")
            elif rate > 0.9:
                insights.append(f"Expert '{expert}' performing well ({rate:.0%} success rate)")

    # Feedback ratio
    if insight.feedback_entries > 0:
        if insight.negative_feedback > insight.positive_feedback:
            insights.append("More negative than positive feedback - review recent changes")

    return insights


def save_insight(
    insight: DailyInsight,
    output_dir: Path,
    dry_run: bool = False
) -> Path:
    """Save insight to YAML file."""
    if insight.submodule:
        file_path = output_dir / "submodules" / insight.submodule / f"{insight.date}.yaml"
    else:
        file_path = output_dir / "daily-insights" / f"{insight.date}.yaml"

    if dry_run:
        print(f"Would write to: {file_path}")
        print(yaml.dump(asdict(insight), default_flow_style=False))
        return file_path

    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        yaml.dump(asdict(insight), f, default_flow_style=False, sort_keys=False)

    return file_path


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate learnings into daily insights"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of days to analyze (default: 1)"
    )
    parser.add_argument(
        "--submodule",
        help="Specific submodule to analyze (default: all + project)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without writing files"
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Project directory (default: current directory)"
    )
    args = parser.parse_args()

    base_path = Path(args.project_dir).resolve()
    output_dir = base_path / ".claude/learning"

    print(f"Aggregating learnings from {base_path}")
    print(f"Looking back {args.days} day(s)")

    if args.submodule:
        # Single submodule
        if args.submodule not in SUBMODULES:
            print(f"Warning: '{args.submodule}' not in known submodules: {SUBMODULES}")

        insight = aggregate_for_submodule(args.submodule, base_path, args.days)
        path = save_insight(insight, output_dir, args.dry_run)
        print(f"Saved: {path}")

    else:
        # Project-level aggregation
        print("\n--- Project-level aggregation ---")
        project_insight = aggregate_project(base_path, args.days)
        path = save_insight(project_insight, output_dir, args.dry_run)
        print(f"Saved: {path}")

        # Per-submodule aggregation
        for submodule in SUBMODULES:
            submodule_path = base_path / submodule
            if submodule_path.exists():
                print(f"\n--- {submodule} ---")
                insight = aggregate_for_submodule(submodule, base_path, args.days)
                path = save_insight(insight, output_dir, args.dry_run)
                print(f"Saved: {path}")

    print("\nAggregation complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
