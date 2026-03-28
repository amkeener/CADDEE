#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Process and route daily insights for action.

Workflow:
1. Load recent daily insights
2. Rank insights by complexity (trivial, simple, moderate, complex)
3. Route to appropriate handlers:
   - Trivial/Simple → .claude/learning/pending/{expert}.yaml (auto-improve)
   - Moderate/Complex → project/BACKLOG.md (human prioritization)
4. Update expert feedback files
5. Catalog errors for future reference

Usage:
    process_insights.py [--days N] [--dry-run]
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import yaml


# Complexity estimation heuristics
COMPLEXITY_KEYWORDS = {
    "trivial": ["typo", "whitespace", "comment", "rename", "format"],
    "simple": ["add", "remove", "update", "fix", "small", "minor"],
    "moderate": ["refactor", "optimize", "improve", "enhance", "extend"],
    "complex": ["redesign", "rewrite", "architecture", "breaking", "major"],
}

# Expert mapping for routing
DOMAIN_TO_EXPERT = {
    "react_frontend": "react_frontend",
    "api_integration": "api_integration",
    "testing": "testing",
    "arcgis": "arcgis",
    "rf_analysis": "rf_analysis",
    "data_analysis": "data_analysis",
    "database": "database",
    "ci_cd": "ci_cd",
    "python_tooling": "python_tooling",
    "security_audit": "security_audit",
}


@dataclass
class ProcessedInsight:
    """A processed and ranked insight."""
    id: str
    source: str  # daily-insights or submodule name
    date: str
    content: str
    complexity: str  # trivial, simple, moderate, complex
    domain: Optional[str] = None
    expert: Optional[str] = None
    action_type: str = "pending"  # pending, backlog, error_catalog
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorCatalogEntry:
    """Entry for the error catalog."""
    id: str
    date: str
    submodule: Optional[str]
    domain: str
    error_pattern: str
    fix_pattern: str
    occurrence_count: int = 1
    source_insights: list[str] = field(default_factory=list)


def load_daily_insights(
    learning_dir: Path,
    since_days: int = 7
) -> list[dict[str, Any]]:
    """Load recent daily insights."""
    insights = []
    since = datetime.now() - timedelta(days=since_days)

    # Project-level insights
    daily_dir = learning_dir / "daily-insights"
    if daily_dir.exists():
        for yaml_file in daily_dir.glob("*.yaml"):
            try:
                file_date = datetime.strptime(yaml_file.stem, "%Y-%m-%d")
                if file_date < since:
                    continue

                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                    if data:
                        data["_source"] = "project"
                        data["_file"] = str(yaml_file)
                        insights.append(data)
            except Exception:
                continue

    # Submodule insights
    submodules_dir = learning_dir / "submodules"
    if submodules_dir.exists():
        for submodule_dir in submodules_dir.iterdir():
            if not submodule_dir.is_dir():
                continue

            for yaml_file in submodule_dir.glob("*.yaml"):
                try:
                    file_date = datetime.strptime(yaml_file.stem, "%Y-%m-%d")
                    if file_date < since:
                        continue

                    with open(yaml_file) as f:
                        data = yaml.safe_load(f)
                        if data:
                            data["_source"] = submodule_dir.name
                            data["_file"] = str(yaml_file)
                            insights.append(data)
                except Exception:
                    continue

    return insights


def estimate_complexity(content: str) -> str:
    """Estimate complexity from content."""
    content_lower = content.lower()

    # Check for complexity keywords in order of specificity
    for complexity, keywords in [
        ("complex", COMPLEXITY_KEYWORDS["complex"]),
        ("moderate", COMPLEXITY_KEYWORDS["moderate"]),
        ("simple", COMPLEXITY_KEYWORDS["simple"]),
        ("trivial", COMPLEXITY_KEYWORDS["trivial"]),
    ]:
        for kw in keywords:
            if kw in content_lower:
                return complexity

    # Default based on content length
    if len(content) < 50:
        return "trivial"
    elif len(content) < 150:
        return "simple"
    elif len(content) < 300:
        return "moderate"
    return "complex"


def detect_domain(content: str, hot_files: list[str]) -> Optional[str]:
    """Detect domain from content and file paths."""
    content_lower = content.lower()

    # Check content for domain keywords
    domain_scores: dict[str, int] = {}

    for domain, expert in DOMAIN_TO_EXPERT.items():
        score = 0
        if domain.replace("_", " ") in content_lower:
            score += 3
        if domain.replace("_", "-") in content_lower:
            score += 3
        if expert in content_lower:
            score += 2

        # Check hot files
        for f in hot_files:
            f_lower = f.lower()
            if domain.replace("_", "") in f_lower:
                score += 1
            if expert.replace("_", "") in f_lower:
                score += 1

        if score > 0:
            domain_scores[domain] = score

    if domain_scores:
        return max(domain_scores.items(), key=lambda x: x[1])[0]

    return None


def process_insight_entry(
    insight_text: str,
    source: str,
    date: str,
    hot_files: list[str],
    index: int
) -> ProcessedInsight:
    """Process a single insight entry."""
    insight_id = f"{source}-{date}-{index}"

    complexity = estimate_complexity(insight_text)
    domain = detect_domain(insight_text, hot_files)
    expert = DOMAIN_TO_EXPERT.get(domain) if domain else None

    # Determine action type based on complexity
    if complexity in ["trivial", "simple"]:
        action_type = "pending"
    elif complexity in ["moderate", "complex"]:
        action_type = "backlog"
    else:
        action_type = "pending"

    return ProcessedInsight(
        id=insight_id,
        source=source,
        date=date,
        content=insight_text,
        complexity=complexity,
        domain=domain,
        expert=expert,
        action_type=action_type,
    )


def process_error_entry(
    expert: str,
    outcomes: dict[str, int],
    source: str,
    date: str
) -> Optional[ErrorCatalogEntry]:
    """Process expert outcome data into error catalog entry if needed."""
    failures = outcomes.get("failure", 0) + outcomes.get("failed", 0)
    total = sum(outcomes.values())

    if failures == 0 or total < 2:
        return None

    # Generate error pattern from context
    error_pattern = f"Expert '{expert}' failures in {source}"
    fix_pattern = f"Review {expert} expert configuration and recent task logs"

    return ErrorCatalogEntry(
        id=f"error-{source}-{date}-{expert}",
        date=date,
        submodule=source if source != "project" else None,
        domain=expert,
        error_pattern=error_pattern,
        fix_pattern=fix_pattern,
        occurrence_count=failures,
        source_insights=[f"{source}/{date}"],
    )


def route_to_pending(
    insights: list[ProcessedInsight],
    output_dir: Path,
    dry_run: bool = False
) -> int:
    """Route trivial/simple insights to pending files for auto-improvement."""
    # Group by expert
    by_expert: dict[str, list[ProcessedInsight]] = {}

    for insight in insights:
        if insight.action_type != "pending":
            continue

        expert = insight.expert or "orchestrator"
        if expert not in by_expert:
            by_expert[expert] = []
        by_expert[expert].append(insight)

    # Write to pending files
    count = 0
    pending_dir = output_dir / "pending"

    for expert, expert_insights in by_expert.items():
        file_path = pending_dir / f"{expert}.yaml"

        # Load existing
        existing = []
        if file_path.exists():
            try:
                with open(file_path) as f:
                    existing = yaml.safe_load(f) or []
            except Exception:
                existing = []

        # Add new insights (avoid duplicates)
        existing_ids = {e.get("id") for e in existing if isinstance(e, dict)}
        for insight in expert_insights:
            if insight.id not in existing_ids:
                existing.append(asdict(insight))
                count += 1

        if dry_run:
            print(f"Would write {len(expert_insights)} insights to {file_path}")
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as f:
                yaml.dump(existing, f, default_flow_style=False, sort_keys=False)

    return count


def route_to_backlog(
    insights: list[ProcessedInsight],
    backlog_path: Path,
    dry_run: bool = False
) -> int:
    """Route moderate/complex insights to BACKLOG.md."""
    backlog_insights = [i for i in insights if i.action_type == "backlog"]

    if not backlog_insights:
        return 0

    # Generate backlog entries
    entries = []
    for insight in backlog_insights:
        entry = f"""
### {insight.id}
- **Source**: {insight.source}
- **Date**: {insight.date}
- **Complexity**: {insight.complexity}
- **Domain**: {insight.domain or 'unknown'}
- **Content**: {insight.content}
"""
        entries.append(entry)

    # Append to backlog
    if dry_run:
        print(f"Would append {len(entries)} entries to {backlog_path}")
        for entry in entries:
            print(entry)
    else:
        if not backlog_path.exists():
            backlog_path.parent.mkdir(parents=True, exist_ok=True)
            initial_content = """# Backlog

Items discovered from daily insights that require human prioritization.

## Pending Items

"""
            backlog_path.write_text(initial_content)

        with open(backlog_path, "a") as f:
            f.write(f"\n<!-- Auto-added from process_insights.py on {datetime.now().strftime('%Y-%m-%d')} -->\n")
            for entry in entries:
                f.write(entry)

    return len(entries)


def catalog_errors(
    errors: list[ErrorCatalogEntry],
    output_dir: Path,
    dry_run: bool = False
) -> int:
    """Add errors to the error catalog."""
    if not errors:
        return 0

    # Group by domain/submodule
    catalog_path = output_dir / "error-catalog.yaml"

    # Load existing catalog
    existing: dict[str, Any] = {}
    if catalog_path.exists():
        try:
            with open(catalog_path) as f:
                existing = yaml.safe_load(f) or {}
        except Exception:
            existing = {}

    # Add new errors
    count = 0
    for error in errors:
        key = error.domain or "general"
        if key not in existing:
            existing[key] = []

        # Check for duplicates (same pattern)
        existing_patterns = [e.get("error_pattern") for e in existing[key]]
        if error.error_pattern not in existing_patterns:
            existing[key].append(asdict(error))
            count += 1
        else:
            # Update occurrence count
            for e in existing[key]:
                if e.get("error_pattern") == error.error_pattern:
                    e["occurrence_count"] = e.get("occurrence_count", 1) + error.occurrence_count
                    break

    if dry_run:
        print(f"Would catalog {count} new errors to {catalog_path}")
    else:
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        with open(catalog_path, "w") as f:
            yaml.dump(existing, f, default_flow_style=False, sort_keys=False)

    return count


def update_expert_feedback(
    insights: list[ProcessedInsight],
    output_dir: Path,
    dry_run: bool = False
) -> int:
    """Update expert feedback files based on insights."""
    # Group insights by expert
    by_expert: dict[str, list[ProcessedInsight]] = {}

    for insight in insights:
        if not insight.expert:
            continue
        if insight.expert not in by_expert:
            by_expert[insight.expert] = []
        by_expert[insight.expert].append(insight)

    # Update feedback files
    count = 0
    feedback_dir = output_dir / "feedback"

    today = datetime.now().strftime("%Y-%m-%d")

    for expert, expert_insights in by_expert.items():
        # Create feedback entry
        feedback_entry = {
            "date": today,
            "expert": expert,
            "insights_count": len(expert_insights),
            "complexity_breakdown": {},
            "domains": list(set(i.domain for i in expert_insights if i.domain)),
        }

        for insight in expert_insights:
            c = insight.complexity
            feedback_entry["complexity_breakdown"][c] = feedback_entry["complexity_breakdown"].get(c, 0) + 1

        # Append to expert feedback file
        file_path = feedback_dir / f"{expert}-feedback.yaml"

        existing = []
        if file_path.exists():
            try:
                with open(file_path) as f:
                    existing = yaml.safe_load(f) or []
            except Exception:
                existing = []

        existing.append(feedback_entry)
        count += 1

        if dry_run:
            print(f"Would update feedback for expert '{expert}' at {file_path}")
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as f:
                yaml.dump(existing, f, default_flow_style=False, sort_keys=False)

    return count


def main():
    parser = argparse.ArgumentParser(
        description="Process and route daily insights"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days of insights to process (default: 7)"
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
    learning_dir = base_path / ".claude/learning"
    backlog_path = base_path / "project/BACKLOG.md"

    print(f"Processing insights from {learning_dir}")
    print(f"Looking back {args.days} day(s)")

    # Load daily insights
    daily_insights = load_daily_insights(learning_dir, args.days)
    print(f"Loaded {len(daily_insights)} daily insight files")

    # Process each insight file
    all_processed: list[ProcessedInsight] = []
    all_errors: list[ErrorCatalogEntry] = []

    for insight_data in daily_insights:
        source = insight_data.get("_source", "unknown")
        date = insight_data.get("date", "unknown")
        hot_files = insight_data.get("hot_files", [])

        # Process text insights
        for idx, text in enumerate(insight_data.get("insights", [])):
            processed = process_insight_entry(text, source, date, hot_files, idx)
            all_processed.append(processed)

        # Process expert outcomes for errors
        for expert, outcomes in insight_data.get("expert_outcomes", {}).items():
            error = process_error_entry(expert, outcomes, source, date)
            if error:
                all_errors.append(error)

    print(f"Processed {len(all_processed)} insights")
    print(f"Found {len(all_errors)} potential error patterns")

    # Route insights
    pending_count = route_to_pending(all_processed, learning_dir, args.dry_run)
    print(f"Routed {pending_count} trivial/simple insights to pending files")

    backlog_count = route_to_backlog(all_processed, backlog_path, args.dry_run)
    print(f"Routed {backlog_count} moderate/complex insights to backlog")

    # Catalog errors
    error_count = catalog_errors(all_errors, learning_dir, args.dry_run)
    print(f"Cataloged {error_count} new error patterns")

    # Update expert feedback
    feedback_count = update_expert_feedback(all_processed, learning_dir, args.dry_run)
    print(f"Updated feedback for {feedback_count} experts")

    # Summary
    print("\n--- Summary ---")
    print(f"Total insights processed: {len(all_processed)}")
    print(f"  → Pending (auto-improve): {pending_count}")
    print(f"  → Backlog (human review): {backlog_count}")
    print(f"Errors cataloged: {error_count}")
    print(f"Expert feedback updated: {feedback_count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
