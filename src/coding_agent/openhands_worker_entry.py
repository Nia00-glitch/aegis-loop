"""
Standalone OpenHands Worker Entry Point.
Executes an OpenHands agent task headlessly against a specified workspace.
Designed to run in an isolated environment (e.g. .openhands_env) without polluting main dependencies.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Ensure UTF-8 I/O
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def run_openhands_task(
    workspace_root: str,
    task_instruction: str,
    model_name: str = "combo/coder",
    base_url: str = "http://127.0.0.1:20128/v1",
    api_key: str = "sk-96ac38503125b798-733820-5d37878f",
    max_turns: int = 10,
) -> dict:
    t_start = time.time()
    events_log = []
    tool_calls = []
    error_msg = None
    success = False

    try:
        from openhands.sdk import LLM, Agent, Tool, LocalWorkspace, LocalConversation
        from openhands.tools.file_editor import FileEditorTool

        # Prefix model for LiteLLM if not present
        effective_model = model_name if model_name.startswith("openai/") else f"openai/{model_name}"

        llm = LLM(
            model=effective_model,
            base_url=base_url,
            api_key=api_key,
        )

        tools = [Tool(name=FileEditorTool.name)]
        agent = Agent(llm=llm, tools=tools)

        workspace_path = Path(workspace_root).resolve()
        workspace = LocalWorkspace(working_dir=workspace_path)

        def event_callback(event):
            ev_str = str(event)
            events_log.append(ev_str)
            if "Tool" in ev_str or "Action" in ev_str or "file_editor" in ev_str:
                tool_calls.append(ev_str[:200])

        # Run with visualizer=None to prevent Windows CP1252 console encoding crashes
        conv = LocalConversation(
            agent=agent,
            workspace=workspace,
            visualizer=None,
            max_iteration_per_run=max_turns,
            callbacks=[event_callback],
        )

        conv.send_message(task_instruction)
        conv.run()

        success = (conv.state.execution_status.value == "finished")
    except Exception as exc:
        error_msg = str(exc)
        success = False

    duration = round(time.time() - t_start, 2)

    # Capture git diff and status in workspace
    git_diff = ""
    changed_files = []
    try:
        diff_res = subprocess.run(
            ["git", "-C", workspace_root, "diff"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        git_diff = diff_res.stdout

        status_res = subprocess.run(
            ["git", "-C", workspace_root, "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in status_res.stdout.splitlines():
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                changed_files.append(parts[1])
    except Exception:
        pass

    return {
        "success": success,
        "duration_seconds": duration,
        "files_changed": changed_files,
        "git_diff": git_diff,
        "tool_calls": tool_calls,
        "events_count": len(events_log),
        "error": error_msg,
    }


def main():
    parser = argparse.ArgumentParser(description="OpenHands Isolated Worker")
    parser.add_argument("--workspace", required=True, help="Workspace root directory")
    parser.add_argument("--task", required=True, help="Task instruction")
    parser.add_argument("--model", default="combo/coder", help="Model name or combo")
    parser.add_argument("--base-url", default="http://127.0.0.1:20128/v1", help="Gateway URL")
    parser.add_argument("--api-key", default="sk-96ac38503125b798-733820-5d37878f", help="API key")
    parser.add_argument("--max-turns", type=int, default=10, help="Max turns")

    args = parser.parse_args()

    result = run_openhands_task(
        workspace_root=args.workspace,
        task_instruction=args.task,
        model_name=args.model,
        base_url=args.base_url,
        api_key=args.api_key,
        max_turns=args.max_turns,
    )

    print("__OPENHANDS_RESULT_START__")
    print(json.dumps(result, indent=2))
    print("__OPENHANDS_RESULT_END__")


if __name__ == "__main__":
    main()
