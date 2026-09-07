from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.coding_agent.prompts import CODER_SYSTEM_PROMPT
from src.coding_agent.tools import (
    ToolResult,
    git_checkpoint,
    git_rollback,
    patch_file,
    read_file,
    run_terminal_command,
    run_test_suite,
    write_file,
)
from src.core.model_router import router

logger = logging.getLogger(__name__)


@dataclass
class AgentTurn:
    turn_index: int
    thought: str
    action: Dict[str, Any]
    result: ToolResult


@dataclass
class CodingSessionResult:
    success: bool
    iterations: int
    patch_summary: str
    turns: List[AgentTurn] = field(default_factory=list)
    initial_checkpoint: Optional[str] = None
    tests_passed: bool = False
    error: Optional[str] = None

    def get_handover_summary(self) -> Dict[str, Any]:
        """Extracts minimal, decision-relevant state for macro-iteration handover."""
        files_read: List[str] = []
        files_modified: List[str] = []
        tests_run: List[str] = []
        for turn in self.turns:
            act = turn.action.get("action", "")
            if act == "read_file":
                p = turn.action.get("path")
                if p and p not in files_read:
                    files_read.append(p)
            elif act in ("write_file", "patch_file"):
                p = turn.action.get("path")
                if p and p not in files_modified:
                    files_modified.append(p)
            elif act == "run_tests":
                t = turn.action.get("test_target", "tests")
                res_str = "Passed" if turn.result.success else "Failed"
                tests_run.append(f"{t}: {res_str}")

        outcome = "Completed" if self.success else (self.error or "Incomplete")
        return {
            "micro_turns_used": self.iterations,
            "outcome": outcome,
            "files_inspected": files_read,
            "files_modified": files_modified,
            "tests_run": tests_run,
            "last_thought": self.turns[-1].thought[:200] if self.turns else None,
        }


class CodeActCodingAgent:
    """
    Autonomous CodeAct-style coding agent runtime.
    Interacts with workspace files and tests via OmniRoute model gateway.
    """

    def __init__(
        self,
        workspace_root: Path,
        max_turns: int = 15,
        model_role: str = "coder",
    ) -> None:
        self.workspace_root = workspace_root.resolve()
        self.max_turns = max_turns
        self.model_role = model_role

    def _clean_json_response(self, text: str) -> Dict[str, Any]:
        """Extract and parse valid JSON object from model output."""
        cleaned = text.strip()
        # Strip markdown code blocks if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Try direct parse
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Try finding first balanced JSON object { ... }
        match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Model did not return valid JSON action: {text[:300]}")

    def execute_tool_action(self, action_dict: Dict[str, Any]) -> ToolResult:
        """Executes the tool action specified by the model."""
        action = action_dict.get("action", "")

        if action == "read_file":
            return read_file(
                workspace_root=self.workspace_root,
                relative_path=action_dict.get("path", ""),
                start_line=action_dict.get("start_line"),
                end_line=action_dict.get("end_line"),
            )
        elif action == "write_file":
            return write_file(
                workspace_root=self.workspace_root,
                relative_path=action_dict.get("path", ""),
                content=action_dict.get("content", ""),
            )
        elif action == "patch_file":
            return patch_file(
                workspace_root=self.workspace_root,
                relative_path=action_dict.get("path", ""),
                target_content=action_dict.get("target", ""),
                replacement_content=action_dict.get("replacement", ""),
            )
        elif action == "run_command":
            return run_terminal_command(
                workspace_root=self.workspace_root,
                command=action_dict.get("command", ""),
            )
        elif action == "run_tests":
            return run_test_suite(
                workspace_root=self.workspace_root,
                test_target=action_dict.get("test_target", "tests"),
            )
        elif action == "finish":
            return ToolResult(
                success=True,
                output="Agent declared task complete.",
                data={"explanation": action_dict.get("explanation", "")},
            )
        else:
            return ToolResult(
                success=False,
                output="",
                error=f"Unknown tool action: '{action}'. Allowed: read_file, write_file, patch_file, run_command, run_tests, finish",
            )

    def run_task(
        self,
        task_instruction: str,
        test_target: Optional[str] = None,
    ) -> CodingSessionResult:
        """
        Runs the autonomous coding cycle against task_instruction.
        Checkpoints workspace prior to mutations.
        """
        checkpoint = git_checkpoint(self.workspace_root, label="pre_coding_checkpoint")
        checkpoint_id = checkpoint.data.get("checkpoint_id") if checkpoint.data else None

        conversation: List[Dict[str, str]] = [
            {"role": "system", "content": CODER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"WORKSPACE: {self.workspace_root}\nTASK: {task_instruction}\nTEST_TARGET: {test_target or 'tests'}\nBegin by reading the relevant files and running the test target to observe the initial failure.",
            },
        ]

        turns: List[AgentTurn] = []
        tests_passed = False

        for turn_idx in range(1, self.max_turns + 1):
            logger.info("Running CodeAct turn %d/%d", turn_idx, self.max_turns)

            try:
                response = router.execute_with_fallback(
                    role=self.model_role,
                    messages=conversation,
                    temperature=0.0,
                )
            except Exception as exc:
                logger.error("Model execution failed on turn %d: %s", turn_idx, exc)
                return CodingSessionResult(
                    success=False,
                    iterations=turn_idx,
                    patch_summary=f"Model routing failure: {exc}",
                    turns=turns,
                    initial_checkpoint=checkpoint_id,
                    error=str(exc),
                )

            raw_reply = response.content
            conversation.append({"role": "assistant", "content": raw_reply})

            try:
                action_dict = self._clean_json_response(raw_reply)
            except Exception as parse_err:
                feedback = f"ERROR: Invalid JSON format. Output exactly one JSON action. Details: {parse_err}"
                conversation.append({"role": "user", "content": feedback})
                turns.append(
                    AgentTurn(
                        turn_index=turn_idx,
                        thought=raw_reply,
                        action={"action": "invalid_json"},
                        result=ToolResult(success=False, output="", error=str(parse_err)),
                    )
                )
                continue

            tool_res = self.execute_tool_action(action_dict)
            turns.append(
                AgentTurn(
                    turn_index=turn_idx,
                    thought=raw_reply,
                    action=action_dict,
                    result=tool_res,
                )
            )

            # Check if tests were executed and passed
            if action_dict.get("action") == "run_tests" and tool_res.success:
                tests_passed = True

            # If agent declares finish
            if action_dict.get("action") == "finish":
                # If a test target was specified, verify tests one final time independently
                if test_target:
                    final_test = run_test_suite(self.workspace_root, test_target)
                    tests_passed = final_test.success
                    if not final_test.success:
                        feedback = f"Task cannot finish because tests are still failing:\n{final_test.output}\nPlease repair the failures."
                        conversation.append({"role": "user", "content": feedback})
                        continue

                return CodingSessionResult(
                    success=tests_passed if test_target else True,
                    iterations=turn_idx,
                    patch_summary=action_dict.get("explanation", "Task completed."),
                    turns=turns,
                    initial_checkpoint=checkpoint_id,
                    tests_passed=tests_passed,
                )

            # Feed tool execution result back to the model
            feedback = (
                f"TOOL RESULT ({action_dict.get('action')}):\n"
                f"Success: {tool_res.success}\n"
                f"Output:\n{tool_res.output}\n"
            )
            if tool_res.error:
                feedback += f"Error:\n{tool_res.error}\n"

            conversation.append({"role": "user", "content": feedback})

        # Max turns reached without finish
        return CodingSessionResult(
            success=False,
            iterations=self.max_turns,
            patch_summary="Maximum turn budget reached without convergence.",
            turns=turns,
            initial_checkpoint=checkpoint_id,
            tests_passed=tests_passed,
            error="BudgetExhausted",
        )
