"""
Custom CodeAct Worker Adapter.
Wraps the baseline custom CodeActCodingAgent behind BaseCodingWorker.
Preserves existing baseline behavior 100% intact.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from src.coding_agent.agent import CodeActCodingAgent
from src.coding_agent.base_worker import BaseCodingWorker, WorkerResult
from src.coding_agent.tools import run_test_suite


class CustomCodeActAdapter(BaseCodingWorker):
    """Wraps the baseline CodeActCodingAgent runtime."""

    def __init__(self, model_role: str = "coder", max_turns: int = 10) -> None:
        self.model_role = model_role
        self.max_turns = max_turns

    def run_task(
        self,
        workspace_root: Path,
        task_instruction: str,
        test_target: Optional[str] = None,
    ) -> WorkerResult:
        t_start = time.time()
        agent = CodeActCodingAgent(
            workspace_root=workspace_root,
            max_turns=self.max_turns,
            model_role=self.model_role,
        )
        res = agent.run_task(task_instruction=task_instruction, test_target=test_target)
        duration = round(time.time() - t_start, 2)

        test_passed = res.tests_passed
        test_out = ""
        if test_target:
            t_res = run_test_suite(workspace_root, test_target)
            test_passed = t_res.success
            test_out = t_res.output

        tool_calls = [f"{t.action.get('action')}" for t in res.turns]

        return WorkerResult(
            success=res.success and (test_passed if test_target else True),
            iterations=res.iterations,
            patch_summary=res.patch_summary,
            duration_seconds=duration,
            tool_calls=tool_calls,
            test_output=test_out,
            tests_passed=test_passed,
            error=res.error,
        )
