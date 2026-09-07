"""
Base Coding Worker Interface for Loop Engineering.
Allows hot-swapping between worker runtimes:
- Custom CodeAct Agent (Baseline)
- OpenHands Adapter (Spike / Worker)
- Mini-SWE-Agent / Other Future Workers
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class WorkerResult:
    success: bool
    iterations: int
    patch_summary: str
    duration_seconds: float = 0.0
    files_changed: List[str] = field(default_factory=list)
    git_diff: str = ""
    tool_calls: List[str] = field(default_factory=list)
    test_output: str = ""
    tests_passed: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseCodingWorker(ABC):
    """Abstract interface for all coding worker runtimes."""

    @abstractmethod
    def run_task(
        self,
        workspace_root: Path,
        task_instruction: str,
        test_target: Optional[str] = None,
    ) -> WorkerResult:
        """Executes a coding repair task against a workspace root."""
        pass
