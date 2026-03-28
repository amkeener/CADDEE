"""JSONL logging for ADW workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional


@dataclass
class ADWLogEntry:
    """A single log entry for ADW events."""

    timestamp: str
    session_id: str
    event_type: Literal[
        "workflow_start",
        "workflow_end",
        "step_start",
        "step_end",
        "expert_selected",
        "expert_call",
        "context_added",
        "error",
        "info",
    ]
    data: Dict[str, Any]

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> ADWLogEntry:
        """Create from JSON string."""
        return cls(**json.loads(json_str))


class ADWLogger:
    """JSONL logger for ADW workflow events."""

    def __init__(
        self,
        session_id: str,
        log_dir: Optional[Path] = None,
    ):
        """Initialize ADW logger.

        Args:
            session_id: Unique session identifier
            log_dir: Base directory for logs (default: logs/adw)
        """
        self.session_id = session_id
        self.log_dir = log_dir or Path("logs/adw")
        self.session_log_dir = self.log_dir / session_id
        self.workflow_log = self.session_log_dir / "workflow.jsonl"
        self.expert_log = self.session_log_dir / "expert_calls.jsonl"

        # Ensure directories exist
        self.session_log_dir.mkdir(parents=True, exist_ok=True)

    def _write_entry(self, log_file: Path, entry: ADWLogEntry) -> None:
        """Write a log entry to file.

        Args:
            log_file: Path to log file
            entry: Log entry to write
        """
        with open(log_file, "a") as f:
            f.write(entry.to_json() + "\n")

    def log_event(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> ADWLogEntry:
        """Log a workflow event.

        Args:
            event_type: Type of event
            data: Event data

        Returns:
            Created log entry
        """
        entry = ADWLogEntry(
            timestamp=datetime.utcnow().isoformat(),
            session_id=self.session_id,
            event_type=event_type,
            data=data or {},
        )
        self._write_entry(self.workflow_log, entry)
        return entry

    def log_workflow_start(
        self,
        workflow_type: str,
        prompt: str,
        steps: List[str],
    ) -> ADWLogEntry:
        """Log workflow start.

        Args:
            workflow_type: Type of workflow
            prompt: User's prompt
            steps: List of step names
        """
        return self.log_event("workflow_start", {
            "workflow_type": workflow_type,
            "prompt": prompt,
            "steps": steps,
        })

    def log_workflow_end(
        self,
        status: str,
        duration_ms: Optional[int] = None,
        output: Optional[Dict[str, Any]] = None,
    ) -> ADWLogEntry:
        """Log workflow end.

        Args:
            status: Final status (completed, failed)
            duration_ms: Total duration in milliseconds
            output: Final output data
        """
        return self.log_event("workflow_end", {
            "status": status,
            "duration_ms": duration_ms,
            "output": output,
        })

    def log_step_start(
        self,
        step_name: str,
        step_index: int,
        expert: str,
    ) -> ADWLogEntry:
        """Log step start.

        Args:
            step_name: Name of the step
            step_index: Index in workflow
            expert: Expert handling this step
        """
        return self.log_event("step_start", {
            "step_name": step_name,
            "step_index": step_index,
            "expert": expert,
        })

    def log_step_end(
        self,
        step_name: str,
        step_index: int,
        status: str,
        duration_ms: Optional[int] = None,
        output: Optional[Dict[str, Any]] = None,
    ) -> ADWLogEntry:
        """Log step end.

        Args:
            step_name: Name of the step
            step_index: Index in workflow
            status: Step status (completed, failed)
            duration_ms: Step duration in milliseconds
            output: Step output data
        """
        return self.log_event("step_end", {
            "step_name": step_name,
            "step_index": step_index,
            "status": status,
            "duration_ms": duration_ms,
            "output": output,
        })

    def log_expert_selected(
        self,
        expert: str,
        reason: str,
        matched_patterns: Optional[List[str]] = None,
        matched_keywords: Optional[List[str]] = None,
    ) -> ADWLogEntry:
        """Log expert selection.

        Args:
            expert: Selected expert name
            reason: Why this expert was selected
            matched_patterns: File patterns that matched
            matched_keywords: Keywords that matched
        """
        return self.log_event("expert_selected", {
            "expert": expert,
            "reason": reason,
            "matched_patterns": matched_patterns or [],
            "matched_keywords": matched_keywords or [],
        })

    def log_expert_call(
        self,
        expert: str,
        action: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
    ) -> ADWLogEntry:
        """Log expert invocation (to separate expert_calls.jsonl).

        Args:
            expert: Expert name
            action: Action performed
            input_data: Input to expert
            output_data: Output from expert
            duration_ms: Duration in milliseconds
        """
        entry = ADWLogEntry(
            timestamp=datetime.utcnow().isoformat(),
            session_id=self.session_id,
            event_type="expert_call",
            data={
                "expert": expert,
                "action": action,
                "input": input_data,
                "output": output_data,
                "duration_ms": duration_ms,
            },
        )
        self._write_entry(self.expert_log, entry)
        return entry

    def log_error(
        self,
        error: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ADWLogEntry:
        """Log an error.

        Args:
            error: Error message
            context: Additional context
        """
        return self.log_event("error", {
            "error": error,
            "context": context or {},
        })

    def log_info(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> ADWLogEntry:
        """Log informational message.

        Args:
            message: Info message
            data: Additional data
        """
        return self.log_event("info", {
            "message": message,
            **(data or {}),
        })

    def read_workflow_log(self) -> List[ADWLogEntry]:
        """Read all workflow log entries.

        Returns:
            List of log entries
        """
        if not self.workflow_log.exists():
            return []

        entries = []
        with open(self.workflow_log, "r") as f:
            for line in f:
                if line.strip():
                    entries.append(ADWLogEntry.from_json(line))
        return entries

    def read_expert_log(self) -> List[ADWLogEntry]:
        """Read all expert call log entries.

        Returns:
            List of log entries
        """
        if not self.expert_log.exists():
            return []

        entries = []
        with open(self.expert_log, "r") as f:
            for line in f:
                if line.strip():
                    entries.append(ADWLogEntry.from_json(line))
        return entries
