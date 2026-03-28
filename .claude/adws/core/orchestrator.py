"""Main ADW orchestrator entry point."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from .state import StateManager, WorkflowState, WorkflowStep
from .logging import ADWLogger
from .expert_router import ExpertRouter, ExpertConfig


# Workflow step definitions
WORKFLOW_STEPS = {
    "plan": [
        {"name": "analyze_task", "expert": "auto"},
        {"name": "research_codebase", "expert": "auto"},
        {"name": "design_solution", "expert": "auto"},
        {"name": "create_plan", "expert": "auto"},
    ],
    "build": [
        {"name": "load_plan", "expert": "auto"},
        {"name": "implement", "expert": "auto"},
        {"name": "validate_changes", "expert": "auto"},
    ],
    "review": [
        {"name": "diff_analysis", "expert": "security_audit"},
        {"name": "domain_review", "expert": "auto"},
        {"name": "generate_report", "expert": "auto"},
    ],
    "fix": [
        {"name": "parse_review", "expert": "auto"},
        {"name": "prioritize_issues", "expert": "auto"},
        {"name": "apply_fixes", "expert": "auto"},
        {"name": "verify_fixes", "expert": "auto"},
    ],
}


@dataclass
class OrchestratorConfig:
    """Configuration for ADW orchestrator."""

    workflow_type: Literal["plan", "build", "review", "fix"]
    prompt: str
    session_id: Optional[str] = None
    expert_override: Optional[str] = None
    plan_path: Optional[str] = None  # For build/fix workflows
    review_path: Optional[str] = None  # For fix workflow
    scope: int = 1  # For review workflow (commits to review)
    files: Optional[List[str]] = None  # Relevant files for routing
    base_dir: Optional[Path] = None

    def __post_init__(self):
        if self.session_id is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            self.session_id = f"adw-{self.workflow_type}-{timestamp}"
        if self.base_dir is None:
            # Path: .claude/adws/core/orchestrator.py -> project root
            self.base_dir = Path(__file__).parent.parent.parent.parent


@dataclass
class StepResult:
    """Result of executing a workflow step."""

    success: bool
    output: Dict[str, Any]
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class WorkflowResult:
    """Result of executing a complete workflow."""

    session_id: str
    workflow_type: str
    success: bool
    expert_used: str
    steps_completed: int
    total_steps: int
    output: Dict[str, Any]
    error: Optional[str] = None
    duration_ms: int = 0
    plan_path: Optional[str] = None
    review_path: Optional[str] = None


class Orchestrator:
    """Main ADW orchestrator coordinating workflows and experts."""

    def __init__(self, config: OrchestratorConfig):
        """Initialize orchestrator.

        Args:
            config: Orchestrator configuration
        """
        self.config = config
        self.state_manager = StateManager(
            session_id=config.session_id,
            base_dir=config.base_dir / ".claude" / "adws" / "sessions",
        )
        self.logger = ADWLogger(
            session_id=config.session_id,
            log_dir=config.base_dir / ".claude" / "logs" / "adw",
        )
        self.router = ExpertRouter(
            experts_dir=config.base_dir / ".claude" / "commands" / "experts",
        )
        self._start_time: Optional[float] = None

    def initialize(self) -> WorkflowState:
        """Initialize workflow session.

        Returns:
            Initialized WorkflowState
        """
        # Create workflow steps
        step_defs = WORKFLOW_STEPS.get(self.config.workflow_type, [])
        steps = [
            WorkflowStep(
                name=s["name"],
                expert=s["expert"],
            )
            for s in step_defs
        ]

        # Route to expert if not overridden
        if self.config.expert_override:
            expert_name = self.config.expert_override
            reason = "Explicitly specified"
        else:
            routing = self.router.route(
                prompt=self.config.prompt,
                files=self.config.files,
            )
            expert_name = routing.expert
            reason = routing.reason

            # Log expert selection
            self.logger.log_expert_selected(
                expert=expert_name,
                reason=reason,
                matched_patterns=routing.matched_patterns,
                matched_keywords=routing.matched_keywords,
            )

        # Initialize state
        state = self.state_manager.initialize(
            workflow_type=self.config.workflow_type,
            prompt=self.config.prompt,
            steps=steps,
        )
        state.expert_used = expert_name
        state.plan_path = self.config.plan_path

        # Update step experts based on routing
        for step in state.steps:
            if step.expert == "auto":
                step.expert = expert_name

        self.state_manager.save(state)

        # Log workflow start
        self.logger.log_workflow_start(
            workflow_type=self.config.workflow_type,
            prompt=self.config.prompt,
            steps=[s.name for s in steps],
        )

        return state

    def get_expert_context(self, expert_name: str) -> str:
        """Get expert context for prompts.

        Args:
            expert_name: Name of expert

        Returns:
            Formatted context string
        """
        expert = self.router.load_expert(expert_name)
        if expert:
            return expert.to_prompt_context()
        return ""

    def get_workflow_context(self) -> Dict[str, Any]:
        """Get current workflow context.

        Returns:
            Dictionary with workflow context
        """
        state = self.state_manager.load()
        if not state:
            return {}

        return {
            "session_id": state.session_id,
            "workflow_type": state.workflow_type,
            "prompt": state.prompt,
            "expert": state.expert_used,
            "current_step": state.current_step.name if state.current_step else None,
            "steps_completed": sum(1 for s in state.steps if s.status == "completed"),
            "total_steps": len(state.steps),
            "context": state.context,
            "plan_path": state.plan_path,
        }

    def mark_step_started(self, step_index: int) -> None:
        """Mark a step as started.

        Args:
            step_index: Index of step to start
        """
        state = self.state_manager.load()
        if state and 0 <= step_index < len(state.steps):
            step = state.steps[step_index]
            step.start()
            state.status = "running"
            self.state_manager.save(state)

            self.logger.log_step_start(
                step_name=step.name,
                step_index=step_index,
                expert=step.expert,
            )

    def mark_step_completed(
        self,
        step_index: int,
        output: Optional[Dict[str, Any]] = None,
        duration_ms: int = 0,
    ) -> None:
        """Mark a step as completed.

        Args:
            step_index: Index of step to complete
            output: Step output data
            duration_ms: Step duration
        """
        state = self.state_manager.load()
        if state and 0 <= step_index < len(state.steps):
            step = state.steps[step_index]
            step.complete(output)
            self.state_manager.save(state)

            self.logger.log_step_end(
                step_name=step.name,
                step_index=step_index,
                status="completed",
                duration_ms=duration_ms,
                output=output,
            )

    def mark_step_failed(
        self,
        step_index: int,
        error: str,
        duration_ms: int = 0,
    ) -> None:
        """Mark a step as failed.

        Args:
            step_index: Index of failed step
            error: Error message
            duration_ms: Step duration
        """
        state = self.state_manager.load()
        if state and 0 <= step_index < len(state.steps):
            step = state.steps[step_index]
            step.fail(error)
            state.status = "failed"
            self.state_manager.save(state)

            self.logger.log_step_end(
                step_name=step.name,
                step_index=step_index,
                status="failed",
                duration_ms=duration_ms,
            )
            self.logger.log_error(error, {"step": step.name})

    def add_context(self, key: str, value: Any) -> None:
        """Add to workflow context.

        Args:
            key: Context key
            value: Context value
        """
        state = self.state_manager.load()
        if state:
            state.add_context(key, value)
            self.state_manager.save(state)

    def set_plan_path(self, path: str) -> None:
        """Set the plan path in state.

        Args:
            path: Path to plan file
        """
        state = self.state_manager.load()
        if state:
            state.plan_path = path
            self.state_manager.save(state)

    def finalize(self, success: bool, output: Optional[Dict[str, Any]] = None) -> WorkflowResult:
        """Finalize workflow and return result.

        Args:
            success: Whether workflow succeeded
            output: Final output data

        Returns:
            WorkflowResult
        """
        state = self.state_manager.load()
        if not state:
            return WorkflowResult(
                session_id=self.config.session_id,
                workflow_type=self.config.workflow_type,
                success=False,
                expert_used="unknown",
                steps_completed=0,
                total_steps=0,
                output={},
                error="State not found",
            )

        state.status = "completed" if success else "failed"
        self.state_manager.save(state)

        duration_ms = int((time.time() - self._start_time) * 1000) if self._start_time else 0

        self.logger.log_workflow_end(
            status=state.status,
            duration_ms=duration_ms,
            output=output,
        )

        steps_completed = sum(1 for s in state.steps if s.status == "completed")

        return WorkflowResult(
            session_id=state.session_id,
            workflow_type=state.workflow_type,
            success=success,
            expert_used=state.expert_used or "unknown",
            steps_completed=steps_completed,
            total_steps=len(state.steps),
            output=output or {},
            duration_ms=duration_ms,
            plan_path=state.plan_path,
        )

    def start(self) -> None:
        """Start timing the workflow."""
        self._start_time = time.time()

    @classmethod
    def create(
        cls,
        workflow_type: str,
        prompt: str,
        **kwargs,
    ) -> "Orchestrator":
        """Factory method to create and initialize an orchestrator.

        Args:
            workflow_type: Type of workflow
            prompt: User's prompt
            **kwargs: Additional config options

        Returns:
            Initialized Orchestrator
        """
        config = OrchestratorConfig(
            workflow_type=workflow_type,
            prompt=prompt,
            **kwargs,
        )
        orchestrator = cls(config)
        orchestrator.initialize()
        orchestrator.start()
        return orchestrator
