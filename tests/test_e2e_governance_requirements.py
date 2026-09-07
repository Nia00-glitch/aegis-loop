"""
E2E Requirement-Driven Governance Verification Test Suite.
Validates Loop Engineering Safety Guarantees G1–G5 across Tiers 1–4.
Opaque-box verification grounded in PROJECT.md and AGENTS.md specifications.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from src.coding_agent.agent import AgentTurn, CodeActCodingAgent, CodingSessionResult
from src.coding_agent.tools import (
    ToolResult,
    git_checkpoint,
    git_rollback,
    run_test_suite,
)
from src.core.model_router import router
from src.infrastructure.models.omniroute_client import OmniRouteResponse
from src.loops.coding_loop import (
    CodingState,
    build_coding_loop,
    check_reevaluate_decision,
    check_verification_decision,
    classify_failure,
    compute_failure_signature,
    compute_test_file_hash,
    define_stage,
    failure_stage,
    implement_stage,
    reevaluate_stage,
    rollback_and_stop_stage,
    verify_stage,
)
from src.loops.loop_ledger import (
    StageTimer,
    append_ledger_entry,
    create_ledger_entry,
    summarize_ledger,
)


@pytest.fixture(autouse=True)
def fast_router_mock(monkeypatch):
    """
    Ensures tests execute deterministically and rapidly by stubbing out
    remote LLM network latency while preserving all governance state logic.
    """
    def _mock_execute(role: str, messages: List[Dict[str, str]], **kwargs):
        if role == "planner":
            return OmniRouteResponse(content="1. Preserve invariants\n2. Zero regressions\n3. Minimal diff", model="fast-mock")
        if role == "debugger":
            return OmniRouteResponse(content="Diagnosed failure: assertion mismatch in patched function", model="fast-mock")
        return OmniRouteResponse(content="Generic mock model response", model="fast-mock")

    monkeypatch.setattr(router, "execute_with_fallback", _mock_execute)


@pytest.fixture
def temp_workspace():
    """Provides an isolated clean workspace directory and tears down afterwards."""
    td = Path(tempfile.mkdtemp(prefix="test_gov_ws_"))
    yield td
    shutil.rmtree(td, ignore_errors=True)


@pytest.fixture
def temp_git_workspace(temp_workspace):
    """Initializes a local Git repository in the temporary workspace."""
    subprocess.run(["git", "init", "-q"], cwd=str(temp_workspace), check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(temp_workspace), check=True)
    subprocess.run(["git", "config", "user.name", "Governance Test Runner"], cwd=str(temp_workspace), check=True)
    return temp_workspace


# ==============================================================================
# TIER 1: FEATURE COVERAGE (G1 - G5.2)
# ==============================================================================


class TestTier1FeatureCoverage:
    """Tier 1: Comprehensive verification of individual Loop Engineering safety gates."""

    def test_g1_ledger_schema_and_timestamps(self):
        """G1: Verify ledger entries capture required schema, UTC ISO timestamps, and durations."""
        entry = create_ledger_entry(
            stage="TEST",
            iteration=1,
            status="tested",
            test_passed=True,
            duration_seconds=0.125,
            extra={"test_data": {"count": 1}},
        )
        assert "timestamp" in entry
        assert entry["stage"] == "TEST"
        assert entry["iteration"] == 1
        assert entry["status"] == "tested"
        assert entry["test_passed"] is True
        assert entry["duration_seconds"] == 0.125
        assert "T" in entry["timestamp"]  # ISO-8601 UTC format check
        assert entry.get("rolled_back") is None

    def test_g1_ledger_append_only_immutability(self):
        """G1: Verify ledger entries list is append-only and preserves historical order."""
        ledger = None
        entry1 = create_ledger_entry(stage="DEFINE", iteration=1, status="defined", duration_seconds=0.05)
        ledger = append_ledger_entry(ledger, entry1)
        assert len(ledger) == 1

        entry2 = create_ledger_entry(stage="PLAN", iteration=1, status="planned", duration_seconds=0.04)
        ledger = append_ledger_entry(ledger, entry2)
        assert len(ledger) == 2
        assert ledger[0]["stage"] == "DEFINE"
        assert ledger[1]["stage"] == "PLAN"

    def test_g1_ledger_summary_aggregation(self):
        """G1: Verify summarize_ledger computes aggregate metrics and guard flags correctly."""
        entries = [
            create_ledger_entry(stage="DEFINE", iteration=1, status="defined", duration_seconds=0.1),
            create_ledger_entry(stage="IMPLEMENT", iteration=1, status="implemented", duration_seconds=0.5),
            create_ledger_entry(stage="RE-EVALUATE", iteration=1, status="regression_detected", regression_detected=True, duration_seconds=0.2),
            create_ledger_entry(stage="ROLLBACK_AND_STOP", iteration=1, status="regression_rolled_back", rolled_back=True, duration_seconds=0.3),
        ]
        summary = summarize_ledger(entries)
        assert summary["total_entries"] == 4
        assert summary["stages_visited"] == ["DEFINE", "IMPLEMENT", "RE-EVALUATE", "ROLLBACK_AND_STOP"]
        assert summary["final_status"] == "regression_rolled_back"
        assert summary["guard_events"]["regression_detected"] is True
        assert summary["guard_events"]["rollback_triggered"] is True
        assert round(summary["total_duration_seconds"], 2) == 1.1

    def test_g2_regression_detection_and_status(self, temp_workspace):
        """G2: Verify reevaluate_stage runs regression suite and flags regression_detected."""
        visible_test = temp_workspace / "test_vis.py"
        visible_test.write_text("def test_v(): assert True\n", encoding="utf-8")
        reg_test = temp_workspace / "test_reg.py"
        reg_test.write_text("def test_r(): assert False, 'Regression broke baseline!'\n", encoding="utf-8")

        state: CodingState = {
            "workspace_root": str(temp_workspace),
            "task_instruction": "Test task",
            "test_target": "test_vis.py",
            "original_test_target": "test_vis.py",
            "regression_test_target": "test_reg.py",
            "iteration": 1,
            "max_iterations": 3,
            "status": "tested",
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

        res = reevaluate_stage(state)
        assert res["regression_detected"] is True
        assert res["status"] == "regression_detected"
        assert "REGRESSION TEST FAILURE" in res["test_output"]
        assert res["test_passed"] is False

    def test_g2_regression_exhaustion_rollback(self):
        """G2: Verify check_reevaluate_decision routes to fail when iteration >= max_iterations."""
        state: CodingState = {
            "regression_detected": True,
            "iteration": 3,
            "max_iterations": 3,
        }
        decision = check_reevaluate_decision(state)
        assert decision == "fail"

    def test_g2_regression_retry_routing(self):
        """G2: Verify check_reevaluate_decision routes to retry when iteration < max_iterations."""
        state: CodingState = {
            "regression_detected": True,
            "iteration": 1,
            "max_iterations": 3,
        }
        decision = check_reevaluate_decision(state)
        assert decision == "retry"

    def test_g3_sha256_hash_computation(self, temp_workspace):
        """G3: Verify compute_test_file_hash computes accurate SHA-256 for a test file."""
        test_file = temp_workspace / "test_calc.py"
        content = b"def test_math(): assert 1 + 1 == 2\n"
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_test_file_hash(temp_workspace, "test_calc.py")
        assert actual_hash == expected_hash

    def test_g3_tampering_detection_and_abort(self, temp_workspace):
        """G3: Verify verify_stage catches assertion tampering and sets test_integrity_violation."""
        test_file = temp_workspace / "test_target.py"
        original_code = b"def test_auth(): assert authenticate() is True\n"
        test_file.write_bytes(original_code)
        init_hash = hashlib.sha256(original_code).hexdigest()

        # Adversarial tampering: agent strips assertion to make test pass
        test_file.write_bytes(b"def test_auth(): pass  # Tampered!\n")

        state: CodingState = {
            "workspace_root": str(temp_workspace),
            "test_target": "test_target.py",
            "test_file_hash": init_hash,
            "test_passed": True,
            "iteration": 1,
            "status": "tested",
            "history": [],
            "ledger_entries": [],
        }

        res = verify_stage(state)
        assert res["test_integrity_violation"] is True
        assert res["status"] == "test_integrity_violation"
        assert res["state_improved"] is False

    def test_g3_tampering_no_retry_enforcement(self):
        """G3: Verify check_verification_decision immediately fails without retries on tampering."""
        state: CodingState = {
            "test_integrity_violation": True,
            "iteration": 1,
            "max_iterations": 5,  # Plentiful iterations must NOT allow retry
            "test_passed": True,
        }
        decision = check_verification_decision(state)
        assert decision == "fail"

    def test_g4_failure_taxonomy_classification(self):
        """G4: Verify classify_failure categorizes output into canonical error classes."""
        assert classify_failure("SyntaxError: invalid syntax") == "SYNTAX_ERROR"
        assert classify_failure("IndentationError: unexpected indent") == "SYNTAX_ERROR"
        assert classify_failure("ModuleNotFoundError: No module named 'foo'") == "IMPORT_ERROR"
        assert classify_failure("ImportError: cannot import name 'bar'") == "IMPORT_ERROR"
        assert classify_failure("AssertionError: 1 != 2") == "ASSERTION_ERROR"
        assert classify_failure("FAILED tests/test_v.py - assert False") == "ASSERTION_ERROR"
        assert classify_failure("Timed out after 30 seconds") == "TIMEOUT"
        assert classify_failure("ZeroDivisionError: division by zero") == "LOGIC_OR_RUNTIME_ERROR"

    def test_g4_repeated_import_error_unrepairable(self, temp_workspace):
        """G4: Verify repeated IMPORT_ERROR trips the unrepairable flag."""
        state: CodingState = {
            "workspace_root": str(temp_workspace),
            "task_instruction": "Fix import",
            "test_target": "test.py",
            "iteration": 2,
            "test_output": "ModuleNotFoundError: No module named 'missing_lib'",
            "failure_classification_history": ["IMPORT_ERROR"],
            "ledger_entries": [],
            "history": [],
        }
        res = failure_stage(state)
        assert res["unrepairable"] is True
        assert res["failure_classification"] == "IMPORT_ERROR"
        assert res["failure_classification_history"] == ["IMPORT_ERROR", "IMPORT_ERROR"]

    def test_g4_repeated_syntax_error_unrepairable(self, temp_workspace):
        """G4: Verify repeated SYNTAX_ERROR trips the unrepairable flag."""
        state: CodingState = {
            "workspace_root": str(temp_workspace),
            "task_instruction": "Fix syntax",
            "test_target": "test.py",
            "iteration": 2,
            "test_output": "SyntaxError: unmatched ')'",
            "failure_classification_history": ["SYNTAX_ERROR"],
            "ledger_entries": [],
            "history": [],
        }
        res = failure_stage(state)
        assert res["unrepairable"] is True
        assert res["failure_classification"] == "SYNTAX_ERROR"

    def test_g4_fingerprint_normalization(self):
        """G4: Verify compute_failure_signature normalizes line numbers, addresses, and timing."""
        trace1 = "Error at 0x7f8b2c14 line 42 in 0.05s: test failed"
        trace2 = "Error at 0xDEADBEEF line 108 in 2.14s: test failed"
        sig1 = compute_failure_signature(trace1)
        sig2 = compute_failure_signature(trace2)
        assert sig1 == sig2

    def test_g5_1_target_swapping_mechanics(self, temp_workspace):
        """G5.1: Verify active test_target swaps to regression target on regression failure."""
        (temp_workspace / "test_vis.py").write_text("def test_v(): assert True\n", encoding="utf-8")
        reg_file = temp_workspace / "test_reg.py"
        reg_file.write_text("def test_r(): assert False\n", encoding="utf-8")

        state: CodingState = {
            "workspace_root": str(temp_workspace),
            "test_target": "test_vis.py",
            "original_test_target": "test_vis.py",
            "regression_test_target": "test_reg.py",
            "iteration": 1,
            "status": "tested",
            "history": [],
            "ledger_entries": [],
        }

        res = reevaluate_stage(state)
        assert res["target_swapped"] is True
        assert res["test_target"] == "test_reg.py"
        assert res["original_test_target"] == "test_vis.py"
        assert res["test_file_hash"] == compute_test_file_hash(temp_workspace, "test_reg.py")

    def test_g5_1_dual_verification_convergence(self, temp_workspace):
        """G5.1: Verify reevaluate_stage verifies both suites and converges only when both pass."""
        (temp_workspace / "test_vis.py").write_text("def test_v(): assert True\n", encoding="utf-8")
        (temp_workspace / "test_reg.py").write_text("def test_r(): assert True\n", encoding="utf-8")

        state: CodingState = {
            "workspace_root": str(temp_workspace),
            "test_target": "test_reg.py",  # Currently swapped
            "original_test_target": "test_vis.py",
            "regression_test_target": "test_reg.py",
            "iteration": 2,
            "status": "tested",
            "history": [],
            "ledger_entries": [],
        }

        res = reevaluate_stage(state)
        assert res["status"] == "converged_accepted"
        assert res["regression_detected"] is False
        assert res["test_target"] == "test_vis.py"  # Restored to original

    def test_g5_1_collateral_regression_swap_back(self, temp_workspace):
        """G5.1: Verify swap back to visible test if regression repair broke visible test."""
        # Regression suite passes now
        (temp_workspace / "test_reg.py").write_text("def test_r(): assert True\n", encoding="utf-8")
        # But visible suite broke during the regression repair!
        (temp_workspace / "test_vis.py").write_text("def test_v(): assert False, 'Collateral damage'\n", encoding="utf-8")

        state: CodingState = {
            "workspace_root": str(temp_workspace),
            "test_target": "test_reg.py",
            "original_test_target": "test_vis.py",
            "regression_test_target": "test_reg.py",
            "iteration": 2,
            "status": "tested",
            "history": [],
            "ledger_entries": [],
        }

        res = reevaluate_stage(state)
        assert res["regression_detected"] is True
        assert res["target_swapped"] is True
        assert res["test_target"] == "test_vis.py"  # Swapped back to visible

    def test_g5_2_budget_ceiling_enforcement(self, temp_workspace):
        """G5.2: Verify micro-turn budget ceiling tracking and accumulation in implement_stage."""
        dummy_test = temp_workspace / "test_d.py"
        dummy_test.write_text("def test_d(): assert True\n", encoding="utf-8")

        state: CodingState = {
            "workspace_root": str(temp_workspace),
            "task_instruction": "Task",
            "test_target": "test_d.py",
            "plan": "Plan",
            "iteration": 1,
            "total_micro_turns": 8,
            "max_total_micro_turns": 25,
            "adaptive_budget_enabled": True,
            "history": [],
            "ledger_entries": [],
        }

        mock_res = CodingSessionResult(
            success=True,
            iterations=5,
            patch_summary="Applied minimal patch",
            tests_passed=True,
        )

        with patch.object(CodeActCodingAgent, "run_task", return_value=mock_res):
            res = implement_stage(state)
            assert res["total_micro_turns"] == 13  # 8 + 5
            ledger = res["ledger_entries"]
            assert ledger[-1]["extra"]["cumulative_turns"] == 13
            assert ledger[-1]["extra"]["stage_budget"] == 10  # min(10, 25-8=17)

    def test_g5_2_adaptive_stage_budget_allocation(self, temp_workspace):
        """G5.2: Verify dynamic allocation grants up to 15 turns upon BudgetExhausted recovery."""
        state: CodingState = {
            "workspace_root": str(temp_workspace),
            "task_instruction": "Task",
            "test_target": "test_d.py",
            "plan": "Plan",
            "iteration": 2,
            "total_micro_turns": 10,
            "max_total_micro_turns": 25,
            "adaptive_budget_enabled": True,
            "handover_context": {"outcome": "BudgetExhausted", "micro_turns_used": 10},
            "history": [],
            "ledger_entries": [],
        }

        mock_res = CodingSessionResult(
            success=True,
            iterations=7,
            patch_summary="Finished patch after recovery",
            tests_passed=True,
        )

        with patch.object(CodeActCodingAgent, "run_task", return_value=mock_res):
            res = implement_stage(state)
            assert res["total_micro_turns"] == 17  # 10 + 7
            ledger = res["ledger_entries"]
            assert ledger[-1]["extra"]["stage_budget"] == 15  # min(15, 25-10=15)

    def test_g5_2_handover_summary_structure(self):
        """G5.2: Verify CodingSessionResult extracts structured context without state bloat."""
        turns = [
            AgentTurn(1, "Read models", {"action": "read_file", "path": "src/models.py"}, ToolResult(True, "content")),
            AgentTurn(2, "Patch models", {"action": "write_file", "path": "src/models.py"}, ToolResult(True, "written")),
            AgentTurn(3, "Run test suite", {"action": "run_tests", "test_target": "tests/test_v.py"}, ToolResult(True, "Passed")),
        ]
        result = CodingSessionResult(
            success=True,
            iterations=3,
            patch_summary="Updated fee",
            turns=turns,
        )
        handover = result.get_handover_summary()
        assert handover["micro_turns_used"] == 3
        assert handover["outcome"] == "Completed"
        assert handover["files_inspected"] == ["src/models.py"]
        assert handover["files_modified"] == ["src/models.py"]
        assert "tests/test_v.py: Passed" in handover["tests_run"]


# ==============================================================================
# TIER 2: BOUNDARY & CORNER CASES
# ==============================================================================


class TestTier2BoundaryCases:
    """Tier 2: Verification of edge boundaries, zero limits, empty files, and malformed inputs."""

    def test_tier2_empty_test_file(self, temp_workspace):
        """Boundary: Verify empty test file computes empty hash and run_test_suite handles it."""
        empty_file = temp_workspace / "test_empty.py"
        empty_file.write_bytes(b"")

        empty_sha256 = hashlib.sha256(b"").hexdigest()
        assert compute_test_file_hash(temp_workspace, "test_empty.py") == empty_sha256

        # run_test_suite on empty test file: pytest collects 0 items
        result = run_test_suite(temp_workspace, "test_empty.py")
        # In pytest, no tests collected returns exit code 5 (success False)
        assert isinstance(result, ToolResult)
        assert result.success is False or "no tests ran" in result.output.lower()

    def test_tier2_missing_test_target(self, temp_workspace):
        """Boundary: Verify non-existent test file returns None without raising unhandled error."""
        assert compute_test_file_hash(temp_workspace, "non_existent.py") is None

        res = run_test_suite(temp_workspace, "non_existent.py")
        assert res.success is False

    def test_tier2_zero_turn_budget_ceiling(self, temp_workspace):
        """Boundary: Verify max_total_micro_turns=0 or used >= max gracefully defaults to 1."""
        state: CodingState = {
            "workspace_root": str(temp_workspace),
            "task_instruction": "Task",
            "test_target": "test_d.py",
            "plan": "Plan",
            "iteration": 1,
            "total_micro_turns": 25,
            "max_total_micro_turns": 25,  # 0 remaining
            "adaptive_budget_enabled": True,
            "history": [],
            "ledger_entries": [],
        }

        mock_res = CodingSessionResult(
            success=False,
            iterations=1,
            patch_summary="No turns remaining",
            tests_passed=False,
        )

        with patch.object(CodeActCodingAgent, "run_task", return_value=mock_res):
            res = implement_stage(state)
            assert res["total_micro_turns"] == 26
            ledger = res["ledger_entries"]
            assert ledger[-1]["extra"]["stage_budget"] == 1  # max(1, 25-25=0) -> 1

    def test_tier2_corrupt_ledger_handling(self):
        """Boundary: Verify append_ledger_entry and summarize_ledger handle None or empty ledgers."""
        entry = create_ledger_entry(stage="DEFINE", iteration=1, status="defined", duration_seconds=0.01)
        res = append_ledger_entry(None, entry)
        assert isinstance(res, list)
        assert len(res) == 1

        summary = summarize_ledger([])
        assert summary["total_entries"] == 0
        assert summary["stages_visited"] == []
        assert summary["outcome"] == "unknown"

    def test_tier2_identical_stacktrace_no_progress(self, temp_workspace):
        """Boundary: Verify identical failure stack trace triggers no_progress circuit breaker."""
        err_trace = "AssertionError: Expected status 200 at 0x7ffd12 line 10 in 0.03s"
        sig = compute_failure_signature(err_trace)

        state: CodingState = {
            "workspace_root": str(temp_workspace),
            "test_target": "test_t.py",
            "test_passed": False,
            "test_output": err_trace,
            "failure_signature_history": [sig],  # Previous iteration had identical normalized sig
            "iteration": 2,
            "history": [],
            "ledger_entries": [],
        }

        res = verify_stage(state)
        assert res["no_progress_detected"] is True
        assert res["state_improved"] is False

        # Verify decision fails immediately on no progress
        merged = {**state, **res}
        assert check_verification_decision(merged) == "fail"

    def test_tier2_empty_stacktrace_signature(self):
        """Boundary: Verify compute_failure_signature on empty output returns 'empty_output'."""
        assert compute_failure_signature("") == "empty_output"
        assert compute_failure_signature(None) == "empty_output"


# ==============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS
# ==============================================================================


class TestTier3CrossFeatureCombinations:
    """Tier 3: Multi-gate cross-feature combinations and rollback coordination."""

    def test_tier3_g2_g5_1_g1_combined_flow(self, temp_workspace):
        """Cross-Feature: G2 regression triggers G5.1 target swap and writes audit telemetry to G1 ledger."""
        (temp_workspace / "test_vis.py").write_text("def test_v(): assert True\n", encoding="utf-8")
        reg_file = temp_workspace / "test_reg.py"
        reg_file.write_text("def test_r(): assert False, 'Injected baseline regression'\n", encoding="utf-8")

        state: CodingState = {
            "workspace_root": str(temp_workspace),
            "test_target": "test_vis.py",
            "original_test_target": "test_vis.py",
            "regression_test_target": "test_reg.py",
            "iteration": 1,
            "max_iterations": 3,
            "status": "tested",
            "history": [],
            "ledger_entries": [],
        }

        res = reevaluate_stage(state)
        assert res["regression_detected"] is True
        assert res["target_swapped"] is True
        assert res["test_target"] == "test_reg.py"

        # Verify G1 ledger recorded both guard events simultaneously
        ledger = res["ledger_entries"]
        assert len(ledger) == 1
        last = ledger[-1]
        assert last["stage"] == "RE-EVALUATE"
        assert last["regression_detected"] is True
        assert last["target_swapped"] is True
        assert last["extra"]["active_target"] == "test_reg.py"

    def test_tier3_g3_tamper_immediate_rollback(self, temp_git_workspace):
        """Cross-Feature: G3 tampering trips immediate terminal Git rollback without retry."""
        test_file = temp_git_workspace / "test_tamper.py"
        original_bytes = b"def test_important(): assert True\n"
        test_file.write_bytes(original_bytes)

        subprocess.run(["git", "add", "."], cwd=str(temp_git_workspace), check=True)
        subprocess.run(["git", "commit", "-m", "Baseline commit", "-q"], cwd=str(temp_git_workspace), check=True)

        # Baseline checkpoint
        cp = git_checkpoint(temp_git_workspace, label="iter_1")
        cp_ref = cp.data["checkpoint_id"]

        init_hash = hashlib.sha256(original_bytes).hexdigest()

        # Malicious modification by worker
        test_file.write_bytes(b"def test_tampered(): pass\n")

        state: CodingState = {
            "workspace_root": str(temp_git_workspace),
            "test_target": "test_tamper.py",
            "test_file_hash": init_hash,
            "test_passed": True,
            "iteration": 1,
            "max_iterations": 3,
            "git_checkpoint_ref": cp_ref,
            "history": [],
            "ledger_entries": [],
        }

        # 1. Verify stage detects tampering
        ver_res = verify_stage(state)
        assert ver_res["test_integrity_violation"] is True

        # 2. Decision engine intercepts
        merged_state = {**state, **ver_res}
        decision = check_verification_decision(merged_state)
        assert decision == "fail"

        # 3. Rollback stage executes hard Git rollback
        rb_res = rollback_and_stop_stage(merged_state)
        assert rb_res["status"] == "test_tampering_rolled_back"
        assert rb_res["rolled_back"] is True

        # 4. Assert workspace Git state was restored (normalizing Windows CRLF/LF)
        assert test_file.read_bytes().replace(b"\r\n", b"\n") == original_bytes.replace(b"\r\n", b"\n")

    def test_tier3_g4_unrepairable_rollback_telemetry(self, temp_git_workspace):
        """Cross-Feature: G4 repeated syntax error triggers rollback and records reason in G1 ledger."""
        (temp_git_workspace / "main.py").write_text("x = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(temp_git_workspace), check=True)
        subprocess.run(["git", "commit", "-m", "Base", "-q"], cwd=str(temp_git_workspace), check=True)

        cp = git_checkpoint(temp_git_workspace, label="base_cp")
        cp_ref = cp.data["checkpoint_id"]

        state: CodingState = {
            "workspace_root": str(temp_git_workspace),
            "task_instruction": "Fix syntax",
            "test_target": "main.py",
            "iteration": 2,
            "test_output": "SyntaxError: invalid token",
            "failure_classification_history": ["SYNTAX_ERROR"],
            "git_checkpoint_ref": cp_ref,
            "history": [],
            "ledger_entries": [],
        }

        # Failure stage identifies unrepairable
        fail_res = failure_stage(state)
        assert fail_res["unrepairable"] is True

        merged_state = {**state, **fail_res}
        decision = check_verification_decision(merged_state)
        assert decision == "fail"

        # Rollback and stop stage
        rb_res = rollback_and_stop_stage(merged_state)
        assert rb_res["status"] == "unrepairable_rolled_back"

        ledger = rb_res["ledger_entries"]
        summary = summarize_ledger(ledger)
        assert summary["final_status"] == "unrepairable_rolled_back"
        assert summary["guard_events"]["unrepairable_detected"] is True
        assert summary["guard_events"]["rollback_triggered"] is True


# ==============================================================================
# TIER 4: REAL-WORLD WORKLOAD SCENARIOS
# ==============================================================================


class TestTier4RealWorldScenarios:
    """Tier 4: End-to-end multi-stage execution with simulated defects and dynamic recovery."""

    def test_tier4_scenario_defect_injection_and_dynamic_recovery(self, temp_git_workspace):
        """
        Scenario 1: Full multi-stage lifecycle with defect injection and dynamic remediation.
        - Step 1: Baseline with passing visible test but failing regression test.
        - Step 2: Iteration 1 runs, G2 intercepts regression, G5.1 swaps target.
        - Step 3: Iteration 2 receives alert, repairs regression, passes dual verification.
        - Step 4: Final status converges to converged_accepted with restored target.
        """
        src_dir = temp_git_workspace / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "__init__.py").write_text("", encoding="utf-8")

        # Injected defect in models.py (default fee 5.0 instead of 0.0)
        models_code = """class Account:
    def __init__(self, balance: float, fee: float = 5.0):
        self.balance = balance
        self.fee = fee
"""
        (src_dir / "models.py").write_text(models_code, encoding="utf-8")

        service_code = """from src.models import Account

def withdraw(acc: Account, amount: float) -> float:
    return acc.balance - amount - acc.fee
"""
        (src_dir / "service.py").write_text(service_code, encoding="utf-8")

        tests_dir = temp_git_workspace / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / "__init__.py").write_text("", encoding="utf-8")

        # Visible test passes
        (tests_dir / "test_visible.py").write_text("""from src.models import Account
from src.service import withdraw

def test_withdraw_visible():
    acc = Account(balance=100.0, fee=5.0)
    assert withdraw(acc, 20.0) == 75.0
""", encoding="utf-8")

        # Regression test FAILS initially because default fee is 5.0 instead of 0.0
        (tests_dir / "test_regression.py").write_text("""from src.models import Account

def test_account_default_fee():
    acc = Account(balance=100.0)
    assert acc.fee == 0.0, f"Expected 0.0, got {acc.fee}"
""", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=str(temp_git_workspace), check=True)
        subprocess.run(["git", "commit", "-m", "Initial defect injection", "-q"], cwd=str(temp_git_workspace), check=True)

        loop = build_coding_loop()

        def _simulated_worker(self, task_instruction, test_target):
            """Simulates agent self-repair behavior based on incoming prompt alerts."""
            if "REGRESSION REMEDIATION ALERT" in task_instruction:
                # Agent receives remediation swap alert and fixes models.py default fee to 0.0
                fixed_models = """class Account:
    def __init__(self, balance: float, fee: float = 0.0):
        self.balance = balance
        self.fee = fee
"""
                (self.workspace_root / "src" / "models.py").write_text(fixed_models, encoding="utf-8")
                return CodingSessionResult(
                    success=True,
                    iterations=2,
                    patch_summary="Fixed Account default fee in models.py",
                    tests_passed=True,
                    turns=[AgentTurn(1, "Fixed models.py", {"action": "write_file", "path": "src/models.py"}, ToolResult(True, "Saved"))],
                )
            else:
                # Iteration 1: Worker considers task complete without modifying models.py
                return CodingSessionResult(
                    success=True,
                    iterations=1,
                    patch_summary="Preserved withdrawal logic",
                    tests_passed=True,
                )

        with patch.object(CodeActCodingAgent, "run_task", _simulated_worker):
            final_state = loop.invoke({
                "workspace_root": str(temp_git_workspace),
                "task_instruction": "Ensure withdrawal and account models work without breaking defaults.",
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

            assert final_state["status"] == "converged_accepted"
            assert final_state["rolled_back"] is False
            assert final_state["test_target"] == "tests/test_visible.py"  # Restored

            # Verify G1 ledger recorded target_swapped guard event
            summary = summarize_ledger(final_state["ledger_entries"])
            assert summary["guard_events"]["target_swapped"] is True
            assert summary["guard_events"]["regression_detected"] is True

            # Independent post-flight verification: both tests pass
            vis_check = run_test_suite(temp_git_workspace, "tests/test_visible.py")
            reg_check = run_test_suite(temp_git_workspace, "tests/test_regression.py")
            assert vis_check.success is True
            assert reg_check.success is True

    def test_tier4_scenario_anti_gaming_tamper_defense(self, temp_git_workspace):
        """
        Scenario 2: Tampering attack defense in end-to-end execution.
        - Worker attempts to pass test by modifying test file assertions.
        - Loop detects hash tampering, bypasses retries, executes git rollback.
        - Workspace baseline is preserved.
        """
        tests_dir = temp_git_workspace / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        original_test_content = """def test_core_invariant():
    assert 1 == 1
    assert 2 == 2
"""
        (tests_dir / "test_core.py").write_text(original_test_content, encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(temp_git_workspace), check=True)
        subprocess.run(["git", "commit", "-m", "Base commit", "-q"], cwd=str(temp_git_workspace), check=True)

        loop = build_coding_loop()

        def _tampering_worker(self, task_instruction, test_target):
            # Adversarial worker modifies the test file!
            (self.workspace_root / test_target).write_text("def test_core_invariant(): pass\n", encoding="utf-8")
            return CodingSessionResult(
                success=True,
                iterations=1,
                patch_summary="Bypassed assertion",
                tests_passed=True,
            )

        with patch.object(CodeActCodingAgent, "run_task", _tampering_worker):
            final_state = loop.invoke({
                "workspace_root": str(temp_git_workspace),
                "task_instruction": "Satisfy core invariant",
                "test_target": "tests/test_core.py",
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

            assert final_state["status"] == "test_tampering_rolled_back"
            assert final_state["rolled_back"] is True
            assert final_state["test_integrity_violation"] is True

            # Verify Git rollback restored the exact original test file (normalizing line endings)
            current_content = (tests_dir / "test_core.py").read_text(encoding="utf-8").strip()
            assert current_content == original_test_content.strip()

    def test_tier4_scenario_structural_blocker_abort(self, temp_git_workspace):
        """
        Scenario 3: Unrepairable structural blocker abort.
        - Worker repeatedly fails with IMPORT_ERROR on missing package.
        - G4 identifies unrepairability or no progress, halts execution, and triggers rollback.
        """
        src_dir = temp_git_workspace / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "__init__.py").write_text("", encoding="utf-8")
        (src_dir / "app.py").write_text("def run(): return True\n", encoding="utf-8")

        tests_dir = temp_git_workspace / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / "test_app.py").write_text("""from src.app import run
def test_app():
    assert run() is True
""", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=str(temp_git_workspace), check=True)
        subprocess.run(["git", "commit", "-m", "Initial clean app", "-q"], cwd=str(temp_git_workspace), check=True)

        loop = build_coding_loop()
        attempt = {"count": 0}

        def _import_error_worker(self, task_instruction, test_target):
            attempt["count"] += 1
            # Worker repeatedly introduces unresolvable import
            pkg_name = f"non_existent_pkg_{attempt['count']}"
            (self.workspace_root / "src" / "app.py").write_text(f"import {pkg_name}\ndef run(): return True\n", encoding="utf-8")
            return CodingSessionResult(
                success=False,
                iterations=1,
                patch_summary=f"Added missing import {pkg_name}",
                tests_passed=False,
            )

        with patch.object(CodeActCodingAgent, "run_task", _import_error_worker):
            final_state = loop.invoke({
                "workspace_root": str(temp_git_workspace),
                "task_instruction": "Improve app",
                "test_target": "tests/test_app.py",
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

            # G4 halts execution via rollback when unrepairable or no-progress cycle is detected
            assert final_state["status"] in ("unrepairable_rolled_back", "no_progress_rolled_back")
            assert final_state["rolled_back"] is True

            # Verify workspace was rolled back to clean initial commit
            current_app = (src_dir / "app.py").read_text(encoding="utf-8")
            assert "non_existent_pkg_" not in current_app
