"""
End-to-End Test for Loop Engineering Coding Loop Stack
Runs a complete multi-file repair cycle through:
Antigravity -> Loop Engineering -> Coding Agent -> OmniRoute -> Model -> Pytest -> Verification
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from src.loops.coding_loop import build_coding_loop


def setup_test_workspace(workspace: Path) -> str:
    """Sets up an isolated test project with an intentional bug and unit test."""
    src_dir = workspace / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    tests_dir = workspace / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Calculation logic with an intentional bug (adds instead of multiplies tax)
    (src_dir / "calculator.py").write_text("""def compute_subtotal(items):
    return sum(item["price"] * item["quantity"] for item in items)

def apply_tax(subtotal: float, tax_rate: float) -> float:
    # BUG: using + instead of *
    return round(subtotal + (subtotal * tax_rate), 2)

def calculate_order_total(items, tax_rate: float) -> float:
    sub = compute_subtotal(items)
    return apply_tax(sub, tax_rate)
""", encoding="utf-8")

    # Pytest verifying the calculation
    (tests_dir / "test_calculator.py").write_text("""from src.calculator import compute_subtotal, apply_tax, calculate_order_total

def test_subtotal():
    items = [{"price": 10.0, "quantity": 2}, {"price": 5.0, "quantity": 1}]
    assert compute_subtotal(items) == 25.0

def test_apply_tax():
    # $100 with 10% tax should be $110.00
    assert apply_tax(100.0, 0.10) == 110.0

def test_order_total():
    items = [{"price": 50.0, "quantity": 2}]
    # $100 + 8% tax = $108.00
    assert calculate_order_total(items, 0.08) == 108.0
""", encoding="utf-8")

    return "tests/test_calculator.py"


def main():
    print("=" * 60)
    print("LOOP ENGINEERING END-TO-END CODING AGENT TEST")
    print("=" * 60)

    temp_dir = Path(tempfile.mkdtemp(prefix="e2e_coding_test_"))
    try:
        test_target = setup_test_workspace(temp_dir)
        print(f"Isolated test workspace: {temp_dir}")
        print(f"Test target: {test_target}")

        loop = build_coding_loop()

        instruction = (
            "Diagnose and fix any issues in src/calculator.py so all tests in tests/test_calculator.py pass. "
            "Inspect the test assertions first to understand the expected behavior."
        )

        state = loop.invoke({
            "workspace_root": str(temp_dir),
            "task_instruction": instruction,
            "test_target": test_target,
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
        })

        print("\n" + "=" * 60)
        print("EXECUTION RESULT")
        print("=" * 60)
        print(f"Final Status: {state.get('status')}")
        print(f"Tests Passed: {state.get('test_passed')}")
        print(f"Total Iterations: {state.get('iteration')}")
        print(f"Stage History: {' -> '.join(state.get('history', []))}")
        print(f"Patch Summary: {state.get('patch_summary')}")
        print("=" * 60)

        assert state.get("test_passed") is True, f"Tests did not pass: {state.get('test_output')}"
        print("END-TO-END TEST: PASSED")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
