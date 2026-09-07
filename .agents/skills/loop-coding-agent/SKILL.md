---
name: loop-coding-agent
description: Autonomous coding agent runtime integrated with Loop Engineering and OmniRoute. Use this skill when executing complex coding tasks, bug fixes, multi-file edits, or self-repair loops with verified test contracts.
---

# Loop Engineering Autonomous Coding Agent

This skill guides the invocation, execution, and verification of the Loop Engineering Coding Agent stack powered by OmniRoute.

## Architecture

```text
Antigravity
    ↓
Loop Engineering Controller (src/loops/coding_loop.py)
    ↓
CodeAct Coding Agent (src/coding_agent/agent.py)
    ↓
OmniRoute Model Gateway (http://localhost:20128/v1)
    ↓
Adaptive Combos (coder, planner, debugger, reviewer, fast)
    ↓
Tools (Filesystem, Terminal, Pytest, Git Checkpoints)
```

## Running a Coding Loop Task

To run a task through the Loop Engineering coding loop:

```python
from pathlib import Path
from src.loops.coding_loop import build_coding_loop

loop = build_coding_loop()
result = loop.invoke({
    "workspace_root": str(Path(".").resolve()),
    "task_instruction": "Fix bug in calculation module",
    "test_target": "tests/test_calculator.py",
    "iteration": 1,
    "max_iterations": 3,
    "status": "started",
    "history": [],
    "invariants": [],
    "plan": "",
    "patch_summary": "",
    "test_passed": False,
    "test_output": "",
    "failure_attribution": "",
    "remediation_plan": "",
    "checkpoint_id": None
})

print(f"Status: {result['status']}")
print(f"Pass: {result['test_passed']}")
```

## OmniRoute Combo Controls

- Check status: `omniroute status`
- Check active combos: `omniroute combo list`
- Test connection: `python scripts/test_omniroute_live.py`
