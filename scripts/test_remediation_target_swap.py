"""
Deterministic Validation Suite for Remediation Target Swapping in Loop Engineering:
1. Discrete Unit Test: Verify reevaluate_stage detects regression and swaps test_target to regression target.
2. Dual Verification Test: Verify reevaluate_stage verifies both regression target and original visible target before acceptance.
3. End-to-End Loop Integration Test: Full StateGraph run where injected regression is detected, target is swapped, repair is executed, and task converges cleanly.
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
    reevaluate_stage,
)
from src.loops.loop_ledger import summarize_ledger


def test_discrete_target_swapping():
    """Test 1: Verify discrete target swapping mechanics in reevaluate_stage."""
    print("\n--- Test 1: Discrete Remediation Target Swapping ---")
    temp_dir = Path(tempfile.mkdtemp(prefix="test_swap_discrete_"))
    try:
        # Create visible test (passing)
        visible_file = temp_dir / "test_visible.py"
        visible_file.write_text("def test_visible(): assert True\n", encoding="utf-8")

        # Create regression test (failing)
        regression_file = temp_dir / "test_regression.py"
        regression_file.write_text("def test_regression(): assert False, 'Injected regression!'\n", encoding="utf-8")

        initial_state = {
            "workspace_root": str(temp_dir),
            "task_instruction": "Task with regression",
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

        # Step 1: define_stage captures initial baseline and stores original_test_target
        def_res = define_stage(initial_state)
        state_after_def = {**initial_state, **def_res}

        assert state_after_def.get("original_test_target") == "test_visible.py", "original_test_target must be preserved"
        assert state_after_def.get("test_target") == "test_visible.py", "active test_target must be test_visible.py"
        print("  define_stage: original_test_target successfully captured.")

        # Step 2: reevaluate_stage runs with failing regression
        reeval_res = reevaluate_stage(state_after_def)
        state_after_reeval = {**state_after_def, **reeval_res}

        print(f"  reevaluate_stage status: {state_after_reeval.get('status')}")
        print(f"  regression_detected: {state_after_reeval.get('regression_detected')}")
        print(f"  target_swapped: {state_after_reeval.get('target_swapped')}")
        print(f"  active test_target: {state_after_reeval.get('test_target')}")

        assert state_after_reeval.get("regression_detected") is True, "Regression must be detected"
        assert state_after_reeval.get("target_swapped") is True, "target_swapped must be True"
        assert state_after_reeval.get("test_target") == "test_regression.py", "test_target must be swapped to regression target"
        assert state_after_reeval.get("original_test_target") == "test_visible.py", "original_test_target must remain unchanged"

        # Verify hash was updated to the regression file hash
        expected_hash = compute_test_file_hash(temp_dir, "test_regression.py")
        assert state_after_reeval.get("test_file_hash") == expected_hash, "test_file_hash must match regression file"

        # Verify ledger recorded target_swapped
        ledger = state_after_reeval.get("ledger_entries", [])
        last_entry = ledger[-1]
        assert last_entry.get("target_swapped") is True, "Ledger must record target_swapped=True"
        assert last_entry.get("extra", {}).get("active_target") == "test_regression.py"

        print("  Discrete target swapping mechanics: PASSED")
        return True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_dual_verification_convergence():
    """Test 2: Verify dual verification in reevaluate_stage before final acceptance."""
    print("\n--- Test 2: Dual Verification (Regression + Visible Target) ---")
    temp_dir = Path(tempfile.mkdtemp(prefix="test_dual_verif_"))
    try:
        visible_file = temp_dir / "test_visible.py"
        visible_file.write_text("def test_visible(): assert True\n", encoding="utf-8")

        regression_file = temp_dir / "test_regression.py"
        regression_file.write_text("def test_regression(): assert True\n", encoding="utf-8")

        state = {
            "workspace_root": str(temp_dir),
            "task_instruction": "Task post-remediation",
            "test_target": "test_regression.py",  # Currently swapped to regression target
            "original_test_target": "test_visible.py",
            "regression_test_target": "test_regression.py",
            "iteration": 2,
            "max_iterations": 3,
            "status": "tested",
            "history": ["DEFINE", "PLAN", "IMPLEMENT", "TEST", "VERIFY", "RE-EVALUATE", "FAILURE", "REFINE", "IMPLEMENT", "TEST", "VERIFY"],
            "invariants": [],
            "plan": "",
            "patch_summary": "Fixed regression",
            "test_passed": True,
            "test_output": "1 passed",
            "failure_attribution": "",
            "remediation_plan": "",
            "git_checkpoint_ref": None,
            "ledger_entries": [],
        }

        # Case A: Both pass -> should converge and restore original test target
        reeval_res = reevaluate_stage(state)
        assert reeval_res.get("status") == "converged_accepted", f"Expected converged_accepted, got {reeval_res.get('status')}"
        assert reeval_res.get("regression_detected") is False, "regression_detected should be False"
        assert reeval_res.get("test_target") == "test_visible.py", "test_target should be restored to original_test_target"
        print("  Case A (Both Pass -> Converged Accepted): PASSED")

        # Case B: Regression fixed but visible test regressed!
        visible_file.write_text("def test_visible(): assert False, 'Visible broke during regression fix!'\n", encoding="utf-8")
        reeval_res_b = reevaluate_stage(state)
        assert reeval_res_b.get("status") == "regression_detected", "Should detect visible regression"
        assert reeval_res_b.get("regression_detected") is True
        assert reeval_res_b.get("test_target") == "test_visible.py", "Should swap back to visible test target"
        print("  Case B (Collateral Regression in Visible Test Intercepted): PASSED")

        print("  Dual verification convergence: PASSED")
        return True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_e2e_remediation_target_swap_repair():
    """Test 3: End-to-End full loop execution with injected regression and target swap repair."""
    print("\n--- Test 3: End-to-End Loop Integration with Target Swap Repair ---")
    temp_dir = Path(tempfile.mkdtemp(prefix="test_e2e_swap_"))
    try:
        # Initialize Git
        os.system(f'git -C "{temp_dir}" init -q')
        os.system(f'git -C "{temp_dir}" config user.email test@example.com')
        os.system(f'git -C "{temp_dir}" config user.name "Test Runner"')

        # Create source module
        src_dir = temp_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "__init__.py").write_text("", encoding="utf-8")
        
        # models.py has flawed default fee = 5.0 (causes test_regression to fail)
        (src_dir / "models.py").write_text("""class Account:
    def __init__(self, balance: float, fee: float = 5.0):
        self.balance = balance
        self.fee = fee  # Flawed default! Breaks regression test which expects fee == 0.0
""", encoding="utf-8")

        (src_dir / "service.py").write_text("""from src.models import Account

def process_withdrawal(acc: Account, amount: float) -> float:
    # Visible requirement: balance - amount - fee
    return acc.balance - amount - acc.fee
""", encoding="utf-8")

        # Create tests
        tests_dir = temp_dir / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / "__init__.py").write_text("", encoding="utf-8")

        # Visible test passes initially
        (tests_dir / "test_visible.py").write_text("""from src.models import Account
from src.service import process_withdrawal

def test_withdrawal():
    acc = Account(balance=100.0, fee=5.0)
    assert process_withdrawal(acc, 20.0) == 75.0
""", encoding="utf-8")

        # Regression test FAILS initially because default fee is 5.0 instead of 0.0
        (tests_dir / "test_regression.py").write_text("""from src.models import Account

def test_account_default_fee():
    acc = Account(balance=100.0)
    assert acc.fee == 0.0, f"Expected default fee 0.0, got {acc.fee}"
""", encoding="utf-8")

        os.system(f'git -C "{temp_dir}" add .')
        os.system(f'git -C "{temp_dir}" commit -m "Initial commit with regression" -q')

        loop = build_coding_loop()
        state = loop.invoke({
            "workspace_root": str(temp_dir),
            "task_instruction": "Ensure account fee handling and withdrawal logic work correctly. Preserve existing account defaults.",
            "test_target": "tests/test_visible.py",
            "regression_test_target": "tests/test_regression.py",
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
            "git_checkpoint_ref": None,
            "ledger_entries": [],
        })

        print(f"  E2E Final Status: {state.get('status')}")
        print(f"  E2E Final Iteration: {state.get('iteration')}")
        print(f"  E2E Rolled Back: {state.get('rolled_back')}")

        ledger = state.get("ledger_entries", [])
        stages = [e["stage"] for e in ledger]
        print(f"  Stages visited: {stages}")

        summary = summarize_ledger(ledger)
        print(f"  Ledger summary guard events: {summary['guard_events']}")

        # Assertions
        assert summary["guard_events"]["target_swapped"] is True, "target_swapped guard event must have fired"
        assert state.get("status") == "converged_accepted", f"Expected converged_accepted, got {state.get('status')}"
        assert state.get("rolled_back") is False, "Should not be rolled back"

        # Verify that both tests pass now
        from src.coding_agent.tools import run_test_suite
        vis_check = run_test_suite(temp_dir, "tests/test_visible.py")
        reg_check = run_test_suite(temp_dir, "tests/test_regression.py")
        print(f"  Post-run visible test passed: {vis_check.success}")
        print(f"  Post-run regression test passed: {reg_check.success}")

        assert vis_check.success, "Visible test must pass"
        assert reg_check.success, "Regression test must pass"

        print("  E2E Loop Target Swap Repair: PASSED")
        return True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_all_target_swap_tests():
    print("=" * 65)
    print("REMEDIATION TARGET SWAPPING SCIENTIFIC VALIDATION")
    print("=" * 65)
    t1 = test_discrete_target_swapping()
    t2 = test_dual_verification_convergence()
    t3 = test_e2e_remediation_target_swap_repair()

    all_ok = t1 and t2 and t3
    print("\n" + "=" * 65)
    print(f"ALL REMEDIATION TARGET SWAP TESTS: {'PASSED (3/3)' if all_ok else 'FAILED'}")
    print("=" * 65)
    return all_ok


if __name__ == "__main__":
    run_all_target_swap_tests()
