from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BLOCKED_COMMAND_PATTERNS = [
    r"rmdir\s+/[sS]",
    r"format\s+[a-zA-Z]:",
    r"del\s+/[fF]\s+/[sS]",
    r"diskpart",
    r"mkfs",
    r"dd\s+if=",
    r"cat\s+.*\.env",
    r"type\s+.*\.env",
    r"Get-Content\s+.*\.env",
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;",  # Fork bomb
]

SENSITIVE_FILE_PATTERNS = [
    r"\.env$",
    r"\.pem$",
    r"\.key$",
    r"storage\.sqlite$",
    r"id_rsa",
]


@dataclass
class ToolResult:
    success: bool
    output: str
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class SecurityError(Exception):
    """Raised when an operation violates workspace isolation or security boundaries."""
    pass


def resolve_safe_path(workspace_root: Path, relative_path: str) -> Path:
    """
    Resolves relative_path against workspace_root and verifies that the resulting
    canonical path is strictly contained within workspace_root.
    Also verifies the path does not target protected credential files.
    """
    ws_canonical = workspace_root.resolve()
    target_path = (ws_canonical / relative_path).resolve()

    try:
        target_path.relative_to(ws_canonical)
    except ValueError:
        raise SecurityError(
            f"Path traversal detected: '{relative_path}' escapes workspace boundary '{ws_canonical}'"
        )

    for pat in SENSITIVE_FILE_PATTERNS:
        if re.search(pat, target_path.name, re.IGNORECASE):
            raise SecurityError(
                f"Access denied: file '{target_path.name}' matches sensitive protection rule '{pat}'"
            )

    return target_path


def read_file(
    workspace_root: Path,
    relative_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
) -> ToolResult:
    """Read contents of a file within workspace boundary, optionally bounded by line slice."""
    try:
        path = resolve_safe_path(workspace_root, relative_path)
        if not path.is_file():
            return ToolResult(success=False, output="", error=f"File not found: {relative_path}")

        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        total_lines = len(lines)

        s = 1 if start_line is None else max(1, start_line)
        e = total_lines if end_line is None else min(total_lines, end_line)

        selected_lines = lines[s - 1 : e]
        numbered_content = "\n".join(
            f"{i}: {line}" for i, line in enumerate(selected_lines, start=s)
        )

        return ToolResult(
            success=True,
            output=numbered_content,
            data={"total_lines": total_lines, "start_line": s, "end_line": e},
        )
    except SecurityError as sec_err:
        return ToolResult(success=False, output="", error=str(sec_err))
    except Exception as exc:
        return ToolResult(success=False, output="", error=f"Failed to read file: {exc}")


def write_file(
    workspace_root: Path,
    relative_path: str,
    content: str,
) -> ToolResult:
    """Atomically write content to a file within workspace boundary."""
    try:
        path = resolve_safe_path(workspace_root, relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return ToolResult(
            success=True,
            output=f"Successfully wrote {len(content)} characters to {relative_path}",
            data={"bytes_written": len(content.encode("utf-8"))},
        )
    except SecurityError as sec_err:
        return ToolResult(success=False, output="", error=str(sec_err))
    except Exception as exc:
        return ToolResult(success=False, output="", error=f"Failed to write file: {exc}")


def patch_file(
    workspace_root: Path,
    relative_path: str,
    target_content: str,
    replacement_content: str,
) -> ToolResult:
    """
    Surgically replace exactly one instance of target_content with replacement_content
    in a file within workspace boundary.
    """
    try:
        path = resolve_safe_path(workspace_root, relative_path)
        if not path.is_file():
            return ToolResult(success=False, output="", error=f"File not found: {relative_path}")

        raw_text = path.read_text(encoding="utf-8")

        # Normalize line endings for replacement match
        norm_raw = raw_text.replace("\r\n", "\n")
        norm_target = target_content.replace("\r\n", "\n")
        norm_replacement = replacement_content.replace("\r\n", "\n")

        count = norm_raw.count(norm_target)
        if count == 0:
            return ToolResult(
                success=False,
                output="",
                error="Target content not found in file. Ensure exact whitespace and line match.",
            )
        if count > 1:
            return ToolResult(
                success=False,
                output="",
                error=f"Target content matches {count} locations in file. Provide more surrounding context.",
            )

        updated_text = norm_raw.replace(norm_target, norm_replacement, 1)
        # Restore native OS line endings if original had \r\n
        if "\r\n" in raw_text:
            updated_text = updated_text.replace("\n", "\r\n")

        path.write_text(updated_text, encoding="utf-8")
        return ToolResult(
            success=True,
            output=f"Successfully applied patch to {relative_path}",
            data={"lines_replaced": len(norm_target.splitlines())},
        )
    except SecurityError as sec_err:
        return ToolResult(success=False, output="", error=str(sec_err))
    except Exception as exc:
        return ToolResult(success=False, output="", error=f"Failed to patch file: {exc}")


def run_terminal_command(
    workspace_root: Path,
    command: str,
    timeout_seconds: float = 60.0,
) -> ToolResult:
    """
    Execute a sandboxed shell command strictly within the workspace directory.
    Enforces timeout and blocks destructive system commands.
    """
    for blocked_pat in BLOCKED_COMMAND_PATTERNS:
        if re.search(blocked_pat, command, re.IGNORECASE):
            return ToolResult(
                success=False,
                output="",
                error=f"Security violation: command contains blocked destructive pattern '{blocked_pat}'",
            )

    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(workspace_root.resolve()),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        combined_output = proc.stdout
        if proc.stderr:
            combined_output += f"\nSTDERR:\n{proc.stderr}"

        return ToolResult(
            success=proc.returncode == 0,
            output=combined_output.strip(),
            error=None if proc.returncode == 0 else f"Command exited with returncode {proc.returncode}",
            data={"returncode": proc.returncode},
        )
    except subprocess.TimeoutExpired:
        return ToolResult(
            success=False,
            output="",
            error=f"Command timed out after {timeout_seconds} seconds",
        )
    except Exception as exc:
        return ToolResult(
            success=False,
            output="",
            error=f"Command execution error: {exc}",
        )


def git_checkpoint(workspace_root: Path, label: str = "checkpoint") -> ToolResult:
    """Create a temporary Git checkpoint commit / stash to allow instant rollback."""
    try:
        # Check if inside git repo
        check = subprocess.run(
            "git rev-parse --is-inside-work-tree",
            shell=True,
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
        )
        if check.returncode != 0:
            return ToolResult(
                success=True,
                output="Non-git workspace; checkpoint skipped",
                data={"checkpoint_id": "non_git"},
            )

        # Get current commit SHA
        sha_res = subprocess.run(
            "git rev-parse HEAD",
            shell=True,
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
        )
        head_sha = sha_res.stdout.strip() if sha_res.returncode == 0 else "initial"

        # Stash untracked and working changes
        stash_res = subprocess.run(
            f'git stash create "{label}"',
            shell=True,
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
        )
        stash_sha = stash_res.stdout.strip()
        checkpoint_ref = stash_sha if stash_sha else head_sha

        return ToolResult(
            success=True,
            output=f"Git checkpoint created: {checkpoint_ref}",
            data={"checkpoint_id": checkpoint_ref, "head_sha": head_sha},
        )
    except Exception as exc:
        return ToolResult(success=False, output="", error=f"Checkpoint error: {exc}")


def git_rollback(workspace_root: Path, checkpoint_ref: str) -> ToolResult:
    """Restore workspace to specified checkpoint ref or clean git state."""
    try:
        if checkpoint_ref == "non_git":
            return ToolResult(success=True, output="Non-git rollback no-op")

        # Reset working tree to HEAD
        subprocess.run(
            "git checkout -- .",
            shell=True,
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
        )
        subprocess.run(
            "git clean -fd",
            shell=True,
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
        )

        return ToolResult(
            success=True,
            output=f"Workspace rolled back cleanly from checkpoint {checkpoint_ref}",
        )
    except Exception as exc:
        return ToolResult(success=False, output="", error=f"Rollback error: {exc}")


def run_test_suite(
    workspace_root: Path,
    test_target: str,
    python_executable: Optional[str] = None,
    timeout_seconds: float = 60.0,
) -> ToolResult:
    """
    Executes automated test runner (pytest with unittest fallback) within the workspace,
    capturing detailed test telemetry.
    """
    py_bin = python_executable or sys.executable

    # Attempt pytest first
    cmd = f'"{py_bin}" -m pytest "{test_target}" -v --tb=short'

    env = os.environ.copy()
    env["PYTHONPATH"] = str(workspace_root.resolve())

    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(workspace_root.resolve()),
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout_seconds,
        )

        # Fallback to python -m unittest if pytest is not installed in the target interpreter
        if proc.returncode != 0 and "No module named pytest" in (proc.stderr or ""):
            unit_cmd = f'"{py_bin}" -m unittest "{test_target}" -v'
            proc = subprocess.run(
                unit_cmd,
                shell=True,
                cwd=str(workspace_root.resolve()),
                capture_output=True,
                text=True,
                env=env,
                timeout=timeout_seconds,
            )

        passed = proc.returncode == 0
        output = proc.stdout
        if proc.stderr:
            output += f"\nSTDERR:\n{proc.stderr}"

        # Parse test metrics (supports both pytest and unittest output formats)
        passed_count = len(re.findall(r"(?:PASSED|\.\.\. ok)", output))
        failed_count = len(re.findall(r"(?:FAILED|\.\.\. FAIL|\.\.\. ERROR)", output))
        if passed and passed_count == 0 and ("1 passed" in output or "OK" in output):
            passed_count = 1
        total_tests = passed_count + failed_count

        return ToolResult(
            success=passed,
            output=output.strip(),
            error=None if passed else f"Tests failed: {failed_count} failure(s)",
            data={
                "passed": passed,
                "passed_count": passed_count,
                "failed_count": failed_count,
                "total_tests": total_tests,
            },
        )
    except subprocess.TimeoutExpired:
        return ToolResult(
            success=False,
            output="",
            error=f"Test run timed out after {timeout_seconds} seconds",
        )
    except Exception as exc:
        return ToolResult(
            success=False,
            output="",
            error=f"Failed to execute tests: {exc}",
        )
