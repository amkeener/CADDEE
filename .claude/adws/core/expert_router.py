"""Expert routing for ADW workflows."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


@dataclass
class ExpertConfig:
    """Configuration loaded from an expert YAML file."""

    name: str
    description: str
    version: str
    domain: Dict[str, Any]
    file_patterns: List[str]
    keywords: List[str]
    capabilities: List[str]
    guidelines: List[str]
    validation_commands: List[str]
    context_files: List[str]
    domain_id: Optional[str] = None  # Unique ID for unambiguous routing
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> ExpertConfig:
        """Load expert config from YAML file.

        Supports both old format (flat) and new format (with overview section).

        Args:
            yaml_path: Path to expert YAML file

        Returns:
            ExpertConfig instance
        """
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        # Handle new format with 'overview' section
        if "overview" in data:
            overview = data.get("overview", {})
            name = yaml_path.parent.name  # Use directory name as expert name
            description = overview.get("description", "")
            domain = {
                "primary": overview.get("primary_domain", ""),
                "secondary": overview.get("secondary_domains", []),
            }
            # Flatten nested guidelines if present
            guidelines_data = data.get("guidelines", {})
            if isinstance(guidelines_data, dict):
                guidelines = []
                for section_items in guidelines_data.values():
                    if isinstance(section_items, list):
                        guidelines.extend(section_items)
            else:
                guidelines = guidelines_data if isinstance(guidelines_data, list) else []
        else:
            # Old flat format
            name = data.get("name", yaml_path.stem)
            description = data.get("description", "")
            domain = data.get("domain", {})
            guidelines = data.get("guidelines", [])

        # Extract known fields for extra
        known_fields = {
            "name", "description", "version", "domain", "overview",
            "file_patterns", "keywords", "capabilities",
            "guidelines", "validation_commands", "context_files", "domain_id"
        }
        extra = {k: v for k, v in data.items() if k not in known_fields}

        return cls(
            name=name,
            description=description,
            version=data.get("version", "1.0"),
            domain=domain,
            file_patterns=data.get("file_patterns", []),
            keywords=data.get("keywords", []),
            capabilities=data.get("capabilities", []),
            guidelines=guidelines,
            validation_commands=data.get("validation_commands", []),
            context_files=data.get("context_files", []),
            domain_id=data.get("domain_id"),
            extra=extra,
        )

    def to_prompt_context(self) -> str:
        """Convert expert config to prompt context string.

        Returns:
            Formatted string for inclusion in prompts
        """
        lines = [
            f"## Expert: {self.name}",
            f"{self.description}",
            "",
            "### Domain",
            f"Primary: {self.domain.get('primary', 'General')}",
        ]

        secondary = self.domain.get("secondary", [])
        if secondary:
            lines.append("Secondary: " + ", ".join(secondary))

        lines.extend([
            "",
            "### Guidelines",
        ])
        for g in self.guidelines:
            lines.append(f"- {g}")

        lines.extend([
            "",
            "### Validation Commands",
        ])
        for v in self.validation_commands:
            lines.append(f"- `{v}`")

        return "\n".join(lines)


@dataclass
class RoutingResult:
    """Result of expert routing decision."""

    expert: str
    confidence: float  # 0.0 to 1.0
    reason: str
    matched_patterns: List[str] = field(default_factory=list)
    matched_keywords: List[str] = field(default_factory=list)


class ExpertRouter:
    """Routes tasks to appropriate domain experts."""

    # Default expert priority order (fallback chain) - customize for your project
    DEFAULT_PRIORITY = [
        "python_tooling",
        "security_audit",
        "research",
        "orchestrator",
    ]

    def __init__(self, experts_dir: Optional[Path] = None):
        """Initialize expert router.

        Args:
            experts_dir: Directory containing expert subdirectories with expertise.yaml files
        """
        # Default to .claude/commands/experts/ (single source of truth)
        self.experts_dir = experts_dir or Path(__file__).parent.parent.parent / "commands" / "experts"
        self._experts_cache: Dict[str, ExpertConfig] = {}

    def list_experts(self) -> List[str]:
        """List all available expert names.

        Returns:
            List of expert directory names that contain expertise.yaml
        """
        if not self.experts_dir.exists():
            return []
        return [
            d.name for d in self.experts_dir.iterdir()
            if d.is_dir() and (d / "expertise.yaml").exists()
        ]

    def load_expert(self, name: str) -> Optional[ExpertConfig]:
        """Load an expert configuration.

        Args:
            name: Expert directory name

        Returns:
            ExpertConfig if found, None otherwise
        """
        if name in self._experts_cache:
            return self._experts_cache[name]

        # Look for expertise.yaml in the expert's subdirectory
        yaml_path = self.experts_dir / name / "expertise.yaml"
        if not yaml_path.exists():
            return None

        config = ExpertConfig.from_yaml(yaml_path)
        self._experts_cache[name] = config
        return config

    def _match_file_patterns(
        self,
        expert: ExpertConfig,
        files: List[str],
    ) -> List[str]:
        """Find files matching expert's patterns.

        Args:
            expert: Expert configuration
            files: List of file paths to check

        Returns:
            List of matched file paths
        """
        matched = []
        for file_path in files:
            for pattern in expert.file_patterns:
                if fnmatch.fnmatch(file_path, pattern):
                    matched.append(file_path)
                    break
        return matched

    def _match_keywords(
        self,
        expert: ExpertConfig,
        text: str,
    ) -> List[str]:
        """Find keywords from expert that appear in text.

        Args:
            expert: Expert configuration
            text: Text to search

        Returns:
            List of matched keywords
        """
        text_lower = text.lower()
        matched = []
        for keyword in expert.keywords:
            # Match whole words only
            pattern = rf'\b{re.escape(keyword.lower())}\b'
            if re.search(pattern, text_lower):
                matched.append(keyword)
        return matched

    def route(
        self,
        prompt: str,
        files: Optional[List[str]] = None,
        prefer_expert: Optional[str] = None,
        domain_id: Optional[str] = None,
    ) -> RoutingResult:
        """Route a task to the best expert.

        Args:
            prompt: User's prompt/task description
            files: List of relevant file paths
            prefer_expert: Optional preferred expert name override
            domain_id: Optional domain ID for unambiguous routing (e.g., "python-tools-001")

        Returns:
            RoutingResult with selected expert and reasoning
        """
        files = files or []

        # Check for domain_id in prompt (format: @domain-id or [domain-id])
        domain_id_match = re.search(r'[@\[]([a-z]+-[a-z]+-\d+)[\]@]?', prompt.lower())
        if domain_id_match:
            domain_id = domain_id_match.group(1)

        # If domain_id specified, find matching expert
        if domain_id:
            for expert_name in self.list_experts():
                expert = self.load_expert(expert_name)
                if expert and expert.domain_id == domain_id:
                    return RoutingResult(
                        expert=expert_name,
                        confidence=1.0,
                        reason=f"Matched domain_id: {domain_id}",
                    )

        # If explicit preference and expert exists, use it
        if prefer_expert:
            expert = self.load_expert(prefer_expert)
            if expert:
                return RoutingResult(
                    expert=prefer_expert,
                    confidence=1.0,
                    reason="Explicitly requested",
                )

        # Score each expert
        scores: List[Tuple[str, float, RoutingResult]] = []

        for expert_name in self.list_experts():
            if expert_name == "orchestrator":
                continue  # Don't route to orchestrator itself

            expert = self.load_expert(expert_name)
            if not expert:
                continue

            # Calculate score
            matched_patterns = self._match_file_patterns(expert, files)
            matched_keywords = self._match_keywords(expert, prompt)

            # Scoring: patterns are worth more than keywords
            pattern_score = len(matched_patterns) * 2.0
            keyword_score = len(matched_keywords) * 1.0

            # Normalize by total possible matches
            max_pattern_score = max(len(expert.file_patterns), 1) * 2.0
            max_keyword_score = max(len(expert.keywords), 1) * 1.0

            confidence = (pattern_score + keyword_score) / (max_pattern_score + max_keyword_score)
            confidence = min(confidence, 1.0)

            # Build reason
            reasons = []
            if matched_patterns:
                reasons.append(f"files match: {', '.join(matched_patterns[:3])}")
            if matched_keywords:
                reasons.append(f"keywords: {', '.join(matched_keywords[:5])}")

            result = RoutingResult(
                expert=expert_name,
                confidence=confidence,
                reason=" | ".join(reasons) if reasons else "Default fallback",
                matched_patterns=matched_patterns,
                matched_keywords=matched_keywords,
            )

            scores.append((expert_name, confidence, result))

        # Sort by confidence descending
        scores.sort(key=lambda x: x[1], reverse=True)

        # Return best match if confidence > 0
        if scores and scores[0][1] > 0:
            return scores[0][2]

        # Fallback to research expert if no match
        return RoutingResult(
            expert="research",
            confidence=0.1,
            reason="No matching expert found, falling back to research for exploration",
        )

    def route_for_security_review(
        self,
        prompt: str,
        files: Optional[List[str]] = None,
    ) -> List[RoutingResult]:
        """Route for security review (always includes security_audit).

        Args:
            prompt: User's prompt
            files: List of relevant files

        Returns:
            List of RoutingResults, always including security_audit first
        """
        results = []

        # Always include security_audit first for reviews
        security = self.load_expert("security_audit")
        if security:
            results.append(RoutingResult(
                expert="security_audit",
                confidence=1.0,
                reason="Security review always included",
            ))

        # Then add domain-specific expert
        domain_result = self.route(prompt, files)
        if domain_result.expert != "security_audit":
            results.append(domain_result)

        return results

    def create_expert(
        self,
        name: str,
        description: str,
        domain_primary: str,
        file_patterns: List[str],
        keywords: List[str],
    ) -> Path:
        """Create a new expert directory with expertise.yaml.

        Args:
            name: Expert name (underscored)
            description: Brief description
            domain_primary: Primary domain
            file_patterns: File patterns to match
            keywords: Keywords to match

        Returns:
            Path to created expert directory
        """
        # Create expert directory
        expert_dir = self.experts_dir / name
        expert_dir.mkdir(parents=True, exist_ok=True)

        # Build expertise.yaml in new format
        expertise = {
            "overview": {
                "description": description,
                "primary_domain": domain_primary,
                "secondary_domains": [],
                "key_files": [],
            },
            "file_patterns": file_patterns,
            "keywords": keywords,
            "guidelines": [],
            "validation_commands": [],
            "context_files": [],
        }

        # Add header comment and write
        output_path = expert_dir / "expertise.yaml"
        with open(output_path, "w") as f:
            f.write(f"# {name.replace('_', ' ').title()} Expert\n")
            f.write(f"# Last updated: {datetime.now().strftime('%Y-%m-%d')}\n\n")
            yaml.dump(expertise, f, default_flow_style=False, sort_keys=False)

        # Clear cache
        if name in self._experts_cache:
            del self._experts_cache[name]

        return expert_dir
