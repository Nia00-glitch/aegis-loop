"""
OpenHands Integration Spike: Controlled Evaluation on Ledger Reconciliation Task.
Compares OpenHandsAdapter vs CustomCodeActAdapter under identical starting conditions.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

from benchmarks.repo_benchmark import scaffold_task_ledger
from src.coding_agent.custom_adapter import CustomCodeActAdapter
from src.coding_agent.openhands_adapter import OpenHandsAdapter
from src.coding_agent.tools import run_test_suite
from src.loops.coding_loop import build_coding_loop


def run_spike_task(worker_type: str = "openhands") -> Dict[str, Any]:
    temp_dir = Path(tempfile.mkdtemp(prefix=f"spike_{worker_type}_"))
    try:
        # Initialize real git repo
        os.system(f"git -C {temp_dir} init -q")
        os.system(f"git -C {temp_dir} config user.email test@example.com")
        os.system(f"git -C {temp_dir} config user.name 'Spike Runner'")

        spec = scaffold_task_ledger(temp_dir)
        os.system(f"git -C {temp_dir} add .")
        os.system(f"git -C {temp_dir} commit -m 'Initial defective state' -q")

        loop = build_coding_loop()

        t_start = time.time()
        state = loop.invoke({
            "workspace_root": str(temp_dir),
            "task_instruction": spec["instruction"],
            "test_target": spec["visible_test"],
            "iteration": 1,
            "max_iterations": 2,
            "status": "started",
            "history": [],
            "invariants": [],
            "plan": "",
            "patch_summary": "",
            "test_passed": False,
            "test_output": "",
            "failure_attribution": "",
            "remediation_plan": "",
            "git_checkpoint_ref": None,
            "worker_runtime": worker_type,
        })
        duration = round(time.time() - t_start, 2)

        # Post-run evaluation
        vis_res = run_test_suite(temp_dir, spec["visible_test"])
        reg_res = run_test_suite(temp_dir, spec["regression_test"])

        # Hidden tests evaluation
        hidden_path = temp_dir / spec["hidden_test_path"]
        hidden_path.write_text(spec["hidden_test_code"], encoding="utf-8")
        hid_res = run_test_suite(temp_dir, spec["hidden_test_path"])

        # Capture git diff
        diff_res = os.popen(f"git -C {temp_dir} diff HEAD~1").read()

        return {
            "worker_type": worker_type,
            "final_status": state.get("status"),
            "test_passed": state.get("test_passed", False),
            "visible_tests_passed": vis_res.success,
            "regression_tests_passed": reg_res.success,
            "hidden_tests_passed": hid_res.success,
            "overall_success": vis_res.success and reg_res.success and hid_res.success,
            "iterations": state.get("iteration", 1),
            "history": state.get("history", []),
            "duration_seconds": duration,
            "patch_summary": state.get("patch_summary", ""),
            "failure_attribution": state.get("failure_attribution", ""),
            "git_diff": diff_res[:1500],
            "test_output": vis_res.output[:800],
            "rolled_back": state.get("rolled_back", False),
            "no_progress_detected": state.get("no_progress_detected", False),
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    print("=" * 70)
    print("OPENHANDS INTEGRATION SPIKE EVALUATION")
    print("=" * 70)

    print("\n[1/3] Running Task via OpenHandsAdapter...")
    oh_result = run_spike_task(worker_type="openhands")
    print(f"OpenHands Result: {'PASS' if oh_result['overall_success'] else 'FAIL'} | Time: {oh_result['duration_seconds']}s")
    print(f"Visible: {oh_result['visible_tests_passed']} | Reg: {oh_result['regression_tests_passed']} | Hid: {oh_result['hidden_tests_passed']}")
    print(f"Status: {oh_result['final_status']}")
    print(f"History: {' -> '.join(oh_result['history'])}")
    print(f"Patch Summary: {oh_result['patch_summary']}")

    print("\n[2/3] Running Task via CustomCodeActAdapter (Baseline)...")
    custom_result = run_spike_task(worker_type="custom")
    print(f"Custom Baseline Result: {'PASS' if custom_result['overall_success'] else 'FAIL'} | Time: {custom_result['duration_seconds']}s")
    print(f"Visible: {custom_result['visible_tests_passed']} | Reg: {custom_result['regression_tests_passed']} | Hid: {custom_result['hidden_tests_passed']}")
    print(f"Status: {custom_result['final_status']}")
    print(f"History: {' -> '.join(custom_result['history'])}")
    print(f"Patch Summary: {custom_result['patch_summary']}")

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "openhands": oh_result,
        "custom_baseline": custom_result,
    }

    report_path = Path(__file__).resolve().parents[1] / "benchmarks" / "openhands_spike_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved OpenHands Spike Report to: {report_path}")


if __name__ == "__main__":
    main()
