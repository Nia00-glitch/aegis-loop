"""
OpenHands Adapter for Loop Engineering.
Connects the Loop Engineering control plane to the OpenHands SDK worker.
Preserves fallback to custom CodeAct agent upon failure.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.coding_agent.base_worker import BaseCodingWorker, WorkerResult
from src.coding_agent.tools import run_test_suite

logger = logging.getLogger(__name__)

OPENHANDS_PYTHON_CANDIDATES = [
    Path(r"C:\Users\Arsh\.openhands_env\Scripts\python.exe"),
    Path(sys.executable),
]


class OpenHandsAdapter(BaseCodingWorker):
    """
    Adapter implementing BaseCodingWorker using OpenHands SDK.
    Communicates via OmniRoute gateway on port 20128.
    """

    def __init__(
        self,
        model_name: str = "combo/coder",
        base_url: str = "http://127.0.0.1:20128/v1",
        api_key: Optional[str] = None,
        max_turns: int = 10,
        worker_timeout: int = 120,
    ) -> None:
        self.model_name = model_name
        self.base_url = os.environ.get("OMNIROUTE_BASE_URL", base_url)
        self.api_key = api_key or os.environ.get("OPENHANDS_API_KEY") or os.environ.get("OMNIROUTE_API_KEY", "omniroute-local-key")
        self.max_turns = max_turns
        self.worker_timeout = worker_timeout
        self.worker_python = self._locate_openhands_python()

    def _locate_openhands_python(self) -> Path:
        for candidate in OPENHANDS_PYTHON_CANDIDATES:
            if candidate.exists():
                return candidate
        return Path(sys.executable)

    def run_task(
        self,
        workspace_root: Path,
        task_instruction: str,
        test_target: Optional[str] = None,
    ) -> WorkerResult:
        t_start = time.time()
        entry_script = Path(__file__).parent / "openhands_worker_entry.py"

        cmd = [
            str(self.worker_python),
            str(entry_script),
            "--workspace",
            str(workspace_root),
            "--task",
            task_instruction,
            "--model",
            self.model_name,
            "--base-url",
            self.base_url,
            "--api-key",
            self.api_key,
            "--max-turns",
            str(self.max_turns),
        ]

        logger.info("OpenHandsAdapter invoking worker: %s", " ".join(cmd[:4]))

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.worker_timeout,
                encoding="utf-8",
                errors="replace",
            )
            raw_stdout = proc.stdout
            raw_stderr = proc.stderr

            # Parse delimited JSON output from worker
            worker_data = {}
            if "__OPENHANDS_RESULT_START__" in raw_stdout and "__OPENHANDS_RESULT_END__" in raw_stdout:
                payload = raw_stdout.split("__OPENHANDS_RESULT_START__")[1].split("__OPENHANDS_RESULT_END__")[0].strip()
                worker_data = json.loads(payload)
            else:
                worker_data = {
                    "success": False,
                    "error": f"Failed to parse worker output. Stdout: {raw_stdout[-300:]} Stderr: {raw_stderr[-300:]}",
                }

        except subprocess.TimeoutExpired:
            return WorkerResult(
                success=False,
                iterations=1,
                patch_summary="OpenHands worker timed out.",
                duration_seconds=round(time.time() - t_start, 2),
                error="WorkerTimeoutExpired",
            )
        except Exception as exc:
            return WorkerResult(
                success=False,
                iterations=1,
                patch_summary=f"OpenHands execution failure: {exc}",
                duration_seconds=round(time.time() - t_start, 2),
                error=str(exc),
            )

        # Independent verification check
        test_passed = False
        test_out = ""
        if test_target:
            verif_res = run_test_suite(workspace_root, test_target)
            test_passed = verif_res.success
            test_out = verif_res.output

        duration = round(time.time() - t_start, 2)
        overall_success = worker_data.get("success", False) and (test_passed if test_target else True)

        return WorkerResult(
            success=overall_success,
            iterations=1,
            patch_summary=f"OpenHands modified files: {worker_data.get('files_changed', [])}",
            duration_seconds=duration,
            files_changed=worker_data.get("files_changed", []),
            git_diff=worker_data.get("git_diff", ""),
            tool_calls=worker_data.get("tool_calls", []),
            test_output=test_out,
            tests_passed=test_passed,
            error=worker_data.get("error"),
            metadata={
                "events_count": worker_data.get("events_count", 0),
                "worker_python": str(self.worker_python),
                "model": self.model_name,
            },
        )
