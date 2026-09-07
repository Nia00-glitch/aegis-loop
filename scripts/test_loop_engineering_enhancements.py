"""
Scientific Validation Suite for Loop Engineering Enhancements:
1. G1: Evidence & Provenance Ledger Verification
2. G2: Regression & Invariant Protection Gate
3. G3: Anti-Gaming / Test Integrity Guard
4. G4: Repairability / Unrepairable Failure Gate
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from src.loops.coding_loop import build_coding_loop, compute_test_file_hash
from src.loops.loop_ledger import summarize_ledger


def test_g1_evidence_ledger():
    """G1: Verify ledger captures complete audit trail with timestamps and state deltas."""
    print("\n--- Testing G1: Evidence & Provenance Ledger ---")
    temp_dir = Path(tempfile.mkdtemp(prefix="test_g1_"))
    try:
        # Create minimal test workspace
        (temp_dir / "test_dummy.py").write_text("def test_ok(): assert True\n", encoding="utf-8")

        loop = build_coding_loop()
        state = loop.invoke({
            "workspace_root": str(temp_dir),
            "task_instruction": "Verify dummy test",
            "test_target": "test_dummy.py",
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
        })

        ledger = state.get("ledger_entries")
        assert ledger is not None, "Ledger entries should not be None"
        assert len(ledger) >= 5, f"Expected at least 5 ledger entries, got {len(ledger)}"

        stages_in_ledger = [e["stage"] for e in ledger]
        print(f"  Stages recorded in ledger: {stages_in_ledger}")
        for entry in ledger:
            assert "timestamp" in entry, f"Missing timestamp in entry {entry}"
            assert "duration_seconds" in entry, f"Missing duration in entry {entry}"
            assert "status" in entry, f"Missing status in entry {entry}"

        summary = summarize_ledger(ledger)
        assert summary["final_status"] == "converged_accepted"
        print(f"  Ledger summary total entries: {summary['total_entries']}, total duration: {summary['total_duration_seconds']}s")
        print("  G1 Ledger: PASSED")
        return True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_g2_regression_gate():
    """G2: Verify reevaluate_stage intercepts regressions and prevents invalid acceptance."""
    print("\n--- Testing G2: Regression Protection Gate ---")
    temp_dir = Path(tempfile.mkdtemp(prefix="test_g2_"))
    try:
        # Visible test passes
        (temp_dir / "test_visible.py").write_text("def test_v(): assert True\n", encoding="utf-8")
        # Regression test FAILS (simulating broken existing functionality)
        (temp_dir / "test_regression.py").write_text("def test_reg(): assert False, 'Regression broken!'\n", encoding="utf-8")

        loop = build_coding_loop()
        state = loop.invoke({
            "workspace_root": str(temp_dir),
            "task_instruction": "Task that causes regression",
            "test_target": "test_visible.py",
            "regression_test_target": "test_regression.py",
            "iteration": 1,
            "max_iterations": 1,  # Set budget to 1 so regression immediately triggers rollback
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
        })

        print(f"  Final status: {state.get('status')}")
        print(f"  Regression detected: {state.get('regression_detected')}")
        print(f"  Rolled back: {state.get('rolled_back')}")

        assert state.get("regression_detected") is True, "Regression should have been detected"
        assert state.get("status") == "regression_rolled_back", f"Expected regression_rolled_back, got {state.get('status')}"
        assert state.get("rolled_back") is True, "Workspace should be rolled back"
        print("  G2 Regression Protection: PASSED")
        return True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_g3_anti_gaming_guard():
    """G3: Verify test integrity guard catches agent tampering with test assertions."""
    print("\n--- Testing G3: Anti-Gaming / Test Integrity Guard ---")
    temp_dir = Path(tempfile.mkdtemp(prefix="test_g3_"))
    try:
        test_file = temp_dir / "test_target.py"
        test_file.write_text("def test_initial(): assert True\n", encoding="utf-8")

        from src.loops.coding_loop import define_stage, verify_stage

        initial_state = {
            "workspace_root": str(temp_dir),
            "task_instruction": "Fix bug",
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

        # 1. Define stage captures baseline hash
        def_res = define_stage(initial_state)
        merged_state = {**initial_state, **def_res}
        assert merged_state.get("test_file_hash") is not None
        print(f"  Initial test file hash captured: {merged_state['test_file_hash'][:12]}...")

        # 2. Simulate agent tampering with test file (e.g. deleting assertion or changing file)
        test_file.write_text("def test_tampered(): pass  # Tampered!\n", encoding="utf-8")

        # 3. Verify stage detects tampering
        ver_res = verify_stage(merged_state)
        print(f"  Verify status: {ver_res.get('status')}")
        print(f"  Test integrity violation: {ver_res.get('test_integrity_violation')}")

        assert ver_res.get("test_integrity_violation") is True, "Integrity violation should be flagged"
        assert ver_res.get("status") == "test_integrity_violation"
        print("  G3 Anti-Gaming Guard: PASSED")
        return True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_g4_repairability_gate():
    """G4: Verify repeated structural failures (e.g. IMPORT_ERROR) trip unrepairable guard."""
    print("\n--- Testing G4: Repairability / Unrepairable Failure Gate ---")
    temp_dir = Path(tempfile.mkdtemp(prefix="test_g4_"))
    try:
        from src.loops.coding_loop import check_verification_decision, failure_stage

        state = {
            "workspace_root": str(temp_dir),
            "task_instruction": "Fix bug",
            "test_target": "tests",
            "iteration": 1,
            "max_iterations": 3,
            "status": "tested",
            "history": [],
            "invariants": [],
            "plan": "",
            "patch_summary": "",
            "test_passed": False,
            "test_output": "ModuleNotFoundError: No module named 'non_existent_package'",
            "failure_attribution": "",
            "remediation_plan": "",
            "git_checkpoint_ref": None,
            "failure_classification_history": ["IMPORT_ERROR"],  # First iteration already failed with IMPORT_ERROR
            "ledger_entries": [],
        }

        # Second iteration fails again with IMPORT_ERROR
        fail_res = failure_stage(state)
        print(f"  Classification: {fail_res.get('failure_classification')}")
        print(f"  Unrepairable flagged: {fail_res.get('unrepairable')}")

        assert fail_res.get("unrepairable") is True, "Repeated IMPORT_ERROR should be marked unrepairable"

        # Check routing decision
        merged_state = {**state, **fail_res}
        decision = check_verification_decision(merged_state)
        print(f"  Verification routing decision: {decision}")
        assert decision == "fail", f"Expected decision 'fail' for unrepairable, got {decision}"

        print("  G4 Repairability Gate: PASSED")
        return True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_all_validation_tests():
    print("=" * 60)
    print("LOOP ENGINEERING CAPABILITY GAP CLOSURE VALIDATION")
    print("=" * 60)
    r1 = test_g1_evidence_ledger()
    r2 = test_g2_regression_gate()
    r3 = test_g3_anti_gaming_guard()
    r4 = test_g4_repairability_gate()

    all_passed = r1 and r2 and r3 and r4
    print("\n" + "=" * 60)
    print(f"ALL ENHANCEMENT TESTS: {'PASSED (4/4)' if all_passed else 'FAILED'}")
    print("=" * 60)
    return all_passed


if __name__ == "__main__":
    run_all_validation_tests()
