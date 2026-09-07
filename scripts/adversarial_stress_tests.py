"""
Adversarial Empirical Stress Test Suite for Milestone M1 Loop Engineering Governance.
Tests:
1. G3 SHA-256 test hash circumvention:
   - Circumvention A: Directory test target (test_target="tests") bypasses hash check completely.
   - Circumvention B: Deleting test target file bypasses hash check completely.
   - Circumvention C: Tampering with regression test file during iteration 1 is not caught by G3 in verify_stage or reevaluate_stage.
2. G4 Repairability termination analysis:
   - Verifies whether repeated IMPORT_ERROR immediately halts execution at failure_stage, or leaks extra stages (refine/implement).
3. G5.1 Target swap hash baseline timing:
   - Verifies whether swapped regression target hash is established at define_stage or deferred to reevaluate_stage.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.loops.coding_loop import (
    build_coding_loop,
    compute_test_file_hash,
    define_stage,
    verify_stage,
    reevaluate_stage,
    failure_stage,
    check_verification_decision,
)


def test_g3_circumvention_directory_target():
    """Attack 1: When test_target is a directory, G3 computes None and skips verification."""
    print("\n--- Attack 1: G3 Directory Target Bypass ---")
    temp_dir = Path(tempfile.mkdtemp(prefix="adv_g3_dir_"))
    try:
        tests_dir = temp_dir / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        test_file = tests_dir / "test_something.py"
        test_file.write_text("def test_v(): assert True\n", encoding="utf-8")

        initial_state = {
            "workspace_root": str(temp_dir),
            "task_instruction": "Task with directory target",
            "test_target": "tests",  # Target is directory
            "iteration": 1,
            "max_iterations": 3,
            "status": "started",
            "history": [],
            "invariants": [],
            "plan": "",
            "patch_summary": "",
            "test_passed": True,
            "test_output": "",
            "failure_attribution": "",
            "remediation_plan": "",
            "git_checkpoint_ref": None,
            "ledger_entries": [],
        }

        # 1. define_stage captures hash
        def_res = define_stage(initial_state)
        merged = {**initial_state, **def_res}
        captured_hash = merged.get("test_file_hash")
        print(f"  Captured hash for directory target 'tests': {captured_hash}")

        # 2. Tamper with the test file inside directory
        test_file.write_text("def test_something_else(): pass  # TAMPERED!\n", encoding="utf-8")

        # 3. verify_stage
        ver_res = verify_stage(merged)
        violation = ver_res.get("test_integrity_violation")
        status = ver_res.get("status")
        print(f"  Verify integrity violation flagged: {violation}, status: {status}")

        # If violation is False, G3 was successfully bypassed!
        bypassed = (violation is False or violation is None)
        print(f"  [RESULT] G3 Directory Target Bypassed: {bypassed}")
        return bypassed
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_g3_circumvention_file_deletion():
    """Attack 2: When test_target file is deleted by agent, verify_stage skips violation."""
    print("\n--- Attack 2: G3 Test File Deletion Bypass ---")
    temp_dir = Path(tempfile.mkdtemp(prefix="adv_g3_del_"))
    try:
        test_file = temp_dir / "test_target.py"
        test_file.write_text("def test_initial(): assert True\n", encoding="utf-8")

        initial_state = {
            "workspace_root": str(temp_dir),
            "task_instruction": "Task with file target",
            "test_target": "test_target.py",
            "iteration": 1,
            "max_iterations": 3,
            "status": "started",
            "history": [],
            "invariants": [],
            "plan": "",
            "patch_summary": "",
            "test_passed": True,
            "test_output": "",
            "failure_attribution": "",
            "remediation_plan": "",
            "git_checkpoint_ref": None,
            "ledger_entries": [],
        }

        # 1. define_stage captures hash
        def_res = define_stage(initial_state)
        merged = {**initial_state, **def_res}
        init_hash = merged.get("test_file_hash")
        print(f"  Captured initial hash: {init_hash}")
        assert init_hash is not None, "Initial hash should be present for file target"

        # 2. Agent deletes the test file completely
        test_file.unlink()
        assert not test_file.exists(), "Test file should be deleted"

        # 3. verify_stage
        ver_res = verify_stage(merged)
        violation = ver_res.get("test_integrity_violation")
        status = ver_res.get("status")
        print(f"  Verify integrity violation flagged: {violation}, status: {status}")

        bypassed = (violation is False or violation is None)
        print(f"  [RESULT] G3 File Deletion Bypassed: {bypassed}")
        return bypassed
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_g3_circumvention_regression_tampering():
    """Attack 3: Regression test file is modified during iteration 1; G3 never checks it against baseline."""
    print("\n--- Attack 3: G3 Regression Test Tampering Bypass ---")
    temp_dir = Path(tempfile.mkdtemp(prefix="adv_g3_reg_"))
    try:
        vis_file = temp_dir / "test_visible.py"
        vis_file.write_text("def test_v(): assert True\n", encoding="utf-8")

        reg_file = temp_dir / "test_regression.py"
        reg_file.write_text("def test_r(): assert False, 'Initial regression failure'\n", encoding="utf-8")

        initial_state = {
            "workspace_root": str(temp_dir),
            "task_instruction": "Task with regression target",
            "test_target": "test_visible.py",
            "regression_test_target": "test_regression.py",
            "iteration": 1,
            "max_iterations": 3,
            "status": "started",
            "history": [],
            "invariants": [],
            "plan": "",
            "patch_summary": "",
            "test_passed": True,
            "test_output": "",
            "failure_attribution": "",
            "remediation_plan": "",
            "git_checkpoint_ref": None,
            "ledger_entries": [],
        }

        # 1. define_stage captures hash only for visible target
        def_res = define_stage(initial_state)
        merged = {**initial_state, **def_res}
        captured_hash = merged.get("test_file_hash")
        vis_hash = compute_test_file_hash(temp_dir, "test_visible.py")
        assert captured_hash == vis_hash, "Hash should be for visible test"

        # 2. Agent tampers with regression test so it now passes!
        reg_file.write_text("def test_r(): assert True  # Tampered to pass!\n", encoding="utf-8")

        # 3. verify_stage runs
        ver_res = verify_stage(merged)
        assert ver_res.get("test_integrity_violation") is False, "verify_stage does not check regression file"

        # 4. reevaluate_stage runs
        merged2 = {**merged, **ver_res}
        reeval_res = reevaluate_stage(merged2)
        print(f"  reevaluate_stage status: {reeval_res.get('status')}")
        print(f"  regression_detected: {reeval_res.get('regression_detected')}")

        # The tampered regression test passed, so regression_detected is False and status is converged_accepted!
        bypassed = (reeval_res.get("status") == "converged_accepted" and reeval_res.get("regression_detected") is False)
        print(f"  [RESULT] G3 Regression Tampering Bypassed (Tampered test accepted): {bypassed}")
        return bypassed
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_g4_stategraph_leakage():
    """Attack 4: Verify whether StateGraph routes failure_stage directly to rollback or executes refine+implement."""
    print("\n--- Attack 4: G4 StateGraph Stage Leakage Analysis ---")
    # Inspect compiled graph edges
    loop = build_coding_loop()
    # In StateGraph, edges from "failure" node:
    # Let's inspect the graph structure directly
    graph_dict = loop.get_graph()
    
    # Check outgoing edges from 'failure'
    failure_edges = [edge for edge in graph_dict.edges if edge.source == "failure"]
    print(f"  Outgoing edges from 'failure' node: {[e.target for e in failure_edges]}")

    has_refine_edge = any(e.target == "refine" for e in failure_edges)
    has_rollback_edge = any(e.target == "rollback_and_stop" for e in failure_edges)
    
    print(f"  Direct edge to 'refine': {has_refine_edge}")
    print(f"  Direct edge to 'rollback_and_stop': {has_rollback_edge}")

    # If failure only routes to refine unconditionally, unrepairable flag cannot stop the loop immediately!
    leaks_iteration = has_refine_edge and not has_rollback_edge
    print(f"  [RESULT] G4 Leaks Refine & Implement Stages on Unrepairable Error: {leaks_iteration}")
    return leaks_iteration


def run_all_adversarial_tests():
    print("=" * 65)
    print("EMPIRICAL ADVERSARIAL STRESS TESTING SUITE (CHALLENGER 1 - M1)")
    print("=" * 65)
    
    a1 = test_g3_circumvention_directory_target()
    a2 = test_g3_circumvention_file_deletion()
    a3 = test_g3_circumvention_regression_tampering()
    a4 = test_g4_stategraph_leakage()

    print("\n" + "=" * 65)
    print("CHALLENGE TEST SUMMARY:")
    print(f"  Attack 1 (Directory test target bypass): {'CONFIRMED VULNERABILITY' if a1 else 'DEFENDED'}")
    print(f"  Attack 2 (Test file deletion bypass):   {'CONFIRMED VULNERABILITY' if a2 else 'DEFENDED'}")
    print(f"  Attack 3 (Regression tampering bypass):  {'CONFIRMED VULNERABILITY' if a3 else 'DEFENDED'}")
    print(f"  Attack 4 (G4 StateGraph stage leakage): {'CONFIRMED STRUCTURAL DEFECT' if a4 else 'OPTIMAL'}")
    print("=" * 65)


if __name__ == "__main__":
    run_all_adversarial_tests()
