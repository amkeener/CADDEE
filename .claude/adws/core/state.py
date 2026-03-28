"""File-based state management for ADW sessions."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional


@dataclass
class WorkflowStep:
    """A single step in an ADW workflow."""

    name: str
    status: Literal["pending", "in_progress", "completed", "failed", "skipped"] = "pending"
    expert: str = "auto"
    input_context: Dict[str, Any] = field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None

    def start(self) -> None:
        """Mark step as started."""
        self.status = "in_progress"
        self.started_at = datetime.utcnow().isoformat()

    def complete(self, output: Optional[Dict[str, Any]] = None) -> None:
        """Mark step as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow().isoformat()
        self.output = output

    def fail(self, error: str) -> None:
        """Mark step as failed."""
        self.status = "failed"
        self.completed_at = datetime.utcnow().isoformat()
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorkflowStep:
        """Create from dictionary."""
        return cls(**data)


@dataclass
class WorkflowState:
    """State of an ADW workflow session."""

    session_id: str
    workflow_type: Literal["plan", "build", "review", "fix"]
    prompt: str
    status: Literal["initializing", "running", "paused", "completed", "failed"] = "initializing"
    current_step_index: int = 0
    steps: List[WorkflowStep] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    expert_used: Optional[str] = None
    plan_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def current_step(self) -> Optional[WorkflowStep]:
        """Get current step if exists."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance_step(self) -> bool:
        """Advance to next step. Returns True if advanced, False if at end."""
        self.current_step_index += 1
        self.updated_at = datetime.utcnow().isoformat()
        return self.current_step_index < len(self.steps)

    def add_context(self, key: str, value: Any) -> None:
        """Add to accumulated context."""
        self.context[key] = value
        self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "workflow_type": self.workflow_type,
            "prompt": self.prompt,
            "status": self.status,
            "current_step_index": self.current_step_index,
            "steps": [s.to_dict() for s in self.steps],
            "context": self.context,
            "expert_used": self.expert_used,
            "plan_path": self.plan_path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorkflowState:
        """Create from dictionary."""
        steps = [WorkflowStep.from_dict(s) for s in data.pop("steps", [])]
        return cls(steps=steps, **data)


class StateManager:
    """Manages workflow state persistence to JSON files."""

    def __init__(self, session_id: str, base_dir: Optional[Path] = None):
        """Initialize state manager.

        Args:
            session_id: Unique session identifier
            base_dir: Base directory for sessions (default: adws/sessions)
        """
        self.session_id = session_id
        self.base_dir = base_dir or Path(__file__).parent.parent / "sessions"
        self.session_dir = self.base_dir / session_id
        self.state_file = self.session_dir / "state.json"
        self.context_file = self.session_dir / "context.md"

    def initialize(self, workflow_type: str, prompt: str, steps: List[WorkflowStep]) -> WorkflowState:
        """Initialize a new workflow session.

        Args:
            workflow_type: Type of workflow (plan, build, review, fix)
            prompt: User's original prompt
            steps: List of workflow steps to execute

        Returns:
            Initialized WorkflowState
        """
        self.session_dir.mkdir(parents=True, exist_ok=True)

        state = WorkflowState(
            session_id=self.session_id,
            workflow_type=workflow_type,
            prompt=prompt,
            steps=steps,
        )
        self.save(state)
        return state

    def load(self) -> Optional[WorkflowState]:
        """Load state from file.

        Returns:
            WorkflowState if exists, None otherwise
        """
        if not self.state_file.exists():
            return None

        with open(self.state_file, "r") as f:
            data = json.load(f)
        return WorkflowState.from_dict(data)

    def save(self, state: WorkflowState) -> None:
        """Save state to file.

        Args:
            state: WorkflowState to persist
        """
        state.updated_at = datetime.utcnow().isoformat()
        self.session_dir.mkdir(parents=True, exist_ok=True)

        with open(self.state_file, "w") as f:
            json.dump(state.to_dict(), f, indent=2)

    def update_step(self, index: int, **updates) -> None:
        """Update a specific step.

        Args:
            index: Step index to update
            **updates: Fields to update
        """
        state = self.load()
        if state and 0 <= index < len(state.steps):
            step = state.steps[index]
            for key, value in updates.items():
                if hasattr(step, key):
                    setattr(step, key, value)
            self.save(state)

    def append_context_md(self, content: str, header: Optional[str] = None) -> None:
        """Append content to context markdown file.

        Args:
            content: Markdown content to append
            header: Optional section header
        """
        self.session_dir.mkdir(parents=True, exist_ok=True)

        with open(self.context_file, "a") as f:
            if header:
                f.write(f"\n## {header}\n\n")
            f.write(content)
            f.write("\n")

    def get_context_md(self) -> str:
        """Get accumulated context markdown.

        Returns:
            Context markdown content or empty string
        """
        if not self.context_file.exists():
            return ""
        return self.context_file.read_text()

    @classmethod
    def list_sessions(cls, base_dir: Optional[Path] = None) -> List[str]:
        """List all session IDs.

        Args:
            base_dir: Base directory for sessions

        Returns:
            List of session IDs
        """
        base = base_dir or Path(__file__).parent.parent / "sessions"
        if not base.exists():
            return []
        return [d.name for d in base.iterdir() if d.is_dir()]
