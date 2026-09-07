from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from src.coding_agent.agent import CodeActCodingAgent
from src.coding_agent.tools import git_checkpoint, git_rollback, run_test_suite
from src.core.model_router import router
from src.loops.loop_ledger import (
    StageTimer,
    append_ledger_entry,
    create_ledger_entry,
    summarize_ledger,
)

logger = logging.getLogger(__name__)


class CodingState(TypedDict):
    workspace_root: str
    task_instruction: str
    test_target: str
    iteration: int
    max_iterations: int
    status: str
    history: List[str]
    invariants: List[str]
    plan: str
    patch_summary: str
    test_passed: bool
    test_output: str
    failure_attribution: str
    remediation_plan: str
    git_checkpoint_ref: Optional[str]
    baseline_passed: Optional[bool]
    baseline_output: Optional[str]
    failure_classification: Optional[str]
    failure_signature_history: Optional[List[str]]
    no_progress_detected: Optional[bool]
    state_improved: Optional[bool]
    rolled_back: Optional[bool]
    worker_runtime: Optional[str]
    # G1: Evidence & Provenance Ledger
    ledger_entries: Optional[List[Dict[str, Any]]]
    # G2: Regression & Invariant Protection
    regression_test_target: Optional[str]
    regression_detected: Optional[bool]
    # G3: Anti-Gaming / Test Integrity Guard
    test_file_hash: Optional[str]
    test_integrity_violation: Optional[bool]
    # G4: Repairability Gate
    failure_classification_history: Optional[List[str]]
    unrepairable: Optional[bool]


def compute_failure_signature(output: str) -> str:
    """Computes a normalized fingerprint of the failure trace to detect repeating cycles."""
    if not output:
        return "empty_output"
    normalized = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", output)
    normalized = re.sub(r":\d+:", ":LINE:", normalized)
    normalized = re.sub(r"in \d+\.\d+s", "in TIME", normalized)
    normalized = re.sub(r"line \d+", "line LINE", normalized)
    return hashlib.sha256(normalized.strip().encode("utf-8")).hexdigest()[:16]


def classify_failure(output: str) -> str:
    """Classifies failure into canonical taxonomy."""
    out_lower = output.lower()
    if "syntaxerror" in out_lower or "indentationerror" in out_lower:
        return "SYNTAX_ERROR"
    if "importerror" in out_lower or "modulenotfounderror" in out_lower:
        return "IMPORT_ERROR"
    if "assert" in out_lower or "assertionerror" in out_lower or "failed" in out_lower:
        return "ASSERTION_ERROR"
    if "timeout" in out_lower or "timed out" in out_lower:
        return "TIMEOUT"
    return "LOGIC_OR_RUNTIME_ERROR"


def compute_test_file_hash(workspace_root: Path, test_target: str) -> Optional[str]:
    """G3: Compute SHA-256 hash of test file content to detect agent tampering."""
    test_path = (workspace_root / test_target).resolve()
    try:
        if test_path.is_file():
            content = test_path.read_bytes()
            return hashlib.sha256(content).hexdigest()
    except Exception:
        pass
    return None


def define_stage(state: CodingState) -> Dict[str, Any]:
    """01 / DEFINE: Formalize boundary conditions, capture baseline, and establish checkpoint."""
    logger.info("LOOP STAGE: DEFINE")
    with StageTimer() as timer:
        # 1. Establish initial Git checkpoint
        cp = git_checkpoint(Path(state["workspace_root"]), label=f"coding_loop_iter_{state['iteration']}")
        cp_id = cp.data.get("checkpoint_id") if cp.data else None

        # 2. Establish baseline test state before mutations
        baseline_res = run_test_suite(
            workspace_root=Path(state["workspace_root"]),
            test_target=state["test_target"],
        )

        # 3. G3: Capture initial test file hash for anti-gaming guard
        init_test_hash = compute_test_file_hash(Path(state["workspace_root"]), state["test_target"])

        # 4. Deconstruct boundary requirements and invariants using planner role
        prompt = [
            {
                "role": "system",
                "content": "Define formal invariants and boundary conditions for this coding task. List 3 key invariants that must not be violated.",
            },
            {
                "role": "user",
                "content": f"Task: {state['task_instruction']}\nWorkspace: {state['workspace_root']}\nTest Target: {state['test_target']}\nBaseline Tests Passed: {baseline_res.success}",
            },
        ]
        try:
            res = router.execute_with_fallback(role="planner", messages=prompt, temperature=0.0)
            invariants = [res.content.strip()]
        except Exception:
            invariants = ["Preserve existing public API signatures", "Zero test regressions", "Minimal justified diff"]

    ledger_entry = create_ledger_entry(
        stage="DEFINE",
        iteration=state["iteration"],
        status="defined",
        duration_seconds=timer.elapsed,
        extra={
            "checkpoint_ref": cp_id,
            "baseline_passed": baseline_res.success,
            "test_file_hash": init_test_hash[:12] if init_test_hash else None,
            "invariants_count": len(invariants),
        },
    )
    ledger_entries = append_ledger_entry(state.get("ledger_entries"), ledger_entry)

    return {
        "status": "defined",
        "invariants": invariants,
        "git_checkpoint_ref": cp_id,
        "baseline_passed": baseline_res.success,
        "baseline_output": baseline_res.output,
        "failure_signature_history": [],
        "no_progress_detected": False,
        "state_improved": False,
        "rolled_back": False,
        "ledger_entries": ledger_entries,
        "regression_test_target": state.get("regression_test_target"),
        "regression_detected": False,
        "test_file_hash": init_test_hash,
        "test_integrity_violation": False,
        "failure_classification_history": [],
        "unrepairable": False,
        "history": state.get("history", []) + ["DEFINE"],
    }


def plan_stage(state: CodingState) -> Dict[str, Any]:
    """02 / PLAN: Design minimal justified code contract before mutation."""
    logger.info("LOOP STAGE: PLAN")
    with StageTimer() as timer:
        prompt = [
            {
                "role": "system",
                "content": "Create a minimal execution plan. Name the exact files and methods to modify to solve the task without speculative additions.",
            },
            {
                "role": "user",
                "content": f"Task: {state['task_instruction']}\nInvariants: {state['invariants']}\nBaseline Status: {'Passed' if state.get('baseline_passed') else 'Failing (Expected)'}",
            },
        ]
        try:
            res = router.execute_with_fallback(role="planner", messages=prompt, temperature=0.0)
            plan_text = res.content.strip()
        except Exception:
            plan_text = "Inspect target files, locate defective logic, and apply minimal patch."

    ledger_entry = create_ledger_entry(
        stage="PLAN",
        iteration=state["iteration"],
        status="planned",
        duration_seconds=timer.elapsed,
        extra={"plan_preview": plan_text[:200]},
    )
    ledger_entries = append_ledger_entry(state.get("ledger_entries"), ledger_entry)

    return {
        "status": "planned",
        "plan": plan_text,
        "ledger_entries": ledger_entries,
        "history": state["history"] + ["PLAN"],
    }



def implement_stage(state: CodingState) -> Dict[str, Any]:
    """03 / IMPLEMENT: Dispatch to selected coding worker runtime (Custom CodeAct or OpenHands)."""
    logger.info("LOOP STAGE: IMPLEMENT (Iteration %d)", state["iteration"])
    with StageTimer() as timer:
        worker_choice = state.get("worker_runtime", "custom")
        task_desc = f"{state['task_instruction']}\nPLAN:\n{state['plan']}"
        if state.get("remediation_plan"):
            task_desc += f"\nPREVIOUS FAILURE REMEDIATION:\n{state['remediation_plan']}"

        patch_summary = ""
        if worker_choice == "openhands":
            logger.info("Dispatching implementation to OpenHandsAdapter...")
            try:
                from src.coding_agent.openhands_adapter import OpenHandsAdapter
                adapter = OpenHandsAdapter(model_name="combo/coder", max_turns=10)
                worker_res = adapter.run_task(
                    workspace_root=Path(state["workspace_root"]),
                    task_instruction=task_desc,
                    test_target=state.get("test_target"),
                )
                patch_summary = worker_res.patch_summary
                if not worker_res.success and worker_res.error:
                    patch_summary += f" (Worker error: {worker_res.error})"
            except Exception as exc:
                logger.error("OpenHands execution exception: %s. Falling back to Custom CodeAct.", exc)
                agent = CodeActCodingAgent(
                    workspace_root=Path(state["workspace_root"]),
                    max_turns=10,
                    model_role="coder",
                )
                result = agent.run_task(task_instruction=task_desc, test_target=state["test_target"])
                patch_summary = f"[Fallback Custom] {result.patch_summary}"
        else:
            agent = CodeActCodingAgent(
                workspace_root=Path(state["workspace_root"]),
                max_turns=10,
                model_role="coder",
            )
            result = agent.run_task(task_instruction=task_desc, test_target=state["test_target"])
            patch_summary = result.patch_summary

    ledger_entry = create_ledger_entry(
        stage="IMPLEMENT",
        iteration=state["iteration"],
        status="implemented",
        patch_summary=patch_summary,
        duration_seconds=timer.elapsed,
        extra={"worker_runtime": worker_choice},
    )
    ledger_entries = append_ledger_entry(state.get("ledger_entries"), ledger_entry)

    return {
        "status": "implemented",
        "patch_summary": patch_summary,
        "ledger_entries": ledger_entries,
        "history": state["history"] + ["IMPLEMENT"],
    }


def test_stage(state: CodingState) -> Dict[str, Any]:
    """04 / TEST: Execute automated test suite against mutated code."""
    logger.info("LOOP STAGE: TEST")
    with StageTimer() as timer:
        test_res = run_test_suite(
            workspace_root=Path(state["workspace_root"]),
            test_target=state["test_target"],
        )

    ledger_entry = create_ledger_entry(
        stage="TEST",
        iteration=state["iteration"],
        status="tested",
        test_passed=test_res.success,
        duration_seconds=timer.elapsed,
        extra={"test_data": test_res.data},
    )
    ledger_entries = append_ledger_entry(state.get("ledger_entries"), ledger_entry)

    return {
        "status": "tested",
        "test_passed": test_res.success,
        "test_output": test_res.output,
        "ledger_entries": ledger_entries,
        "history": state["history"] + ["TEST"],
    }


def verify_stage(state: CodingState) -> Dict[str, Any]:
    """05 / VERIFY: Objective diagnostic verification gate with no-progress & test integrity detection."""
    logger.info("LOOP STAGE: VERIFY")
    with StageTimer() as timer:
        passed = state["test_passed"]
        sig_history = list(state.get("failure_signature_history") or [])
        no_progress = False
        state_improved = False
        integrity_violation = False

        # G3: Anti-Gaming / Test Integrity Check
        init_hash = state.get("test_file_hash")
        if init_hash:
            current_hash = compute_test_file_hash(Path(state["workspace_root"]), state["test_target"])
            if current_hash and current_hash != init_hash:
                logger.critical(
                    "SECURITY GUARD: TEST INTEGRITY VIOLATION DETECTED! Test file '%s' was modified by agent.",
                    state["test_target"],
                )
                integrity_violation = True

        if integrity_violation:
            status_label = "test_integrity_violation"
            state_improved = False
        elif passed:
            status_label = "verified_passed"
            state_improved = True
        else:
            status_label = "verified_failed"
            current_sig = compute_failure_signature(state.get("test_output", ""))

            # Check research guard: Did same failure repeat consecutively?
            if sig_history and sig_history[-1] == current_sig:
                logger.warning("NO PROGRESS DETECTED: Consecutive iterations produced identical failure fingerprint %s", current_sig)
                no_progress = True
                state_improved = False
            else:
                state_improved = True  # State changed or first failure

            sig_history.append(current_sig)

    ledger_entry = create_ledger_entry(
        stage="VERIFY",
        iteration=state["iteration"],
        status=status_label,
        test_passed=passed,
        no_progress=no_progress,
        test_integrity_violation=integrity_violation,
        duration_seconds=timer.elapsed,
        extra={"signature": sig_history[-1] if sig_history else None},
    )
    ledger_entries = append_ledger_entry(state.get("ledger_entries"), ledger_entry)

    return {
        "status": status_label,
        "failure_signature_history": sig_history,
        "no_progress_detected": no_progress,
        "state_improved": state_improved,
        "test_integrity_violation": integrity_violation,
        "ledger_entries": ledger_entries,
        "history": state["history"] + ["VERIFY"],
    }



def failure_stage(state: CodingState) -> Dict[str, Any]:
    """06 / FAILURE: Classification, root-cause attribution, and repairability check."""
    logger.info("LOOP STAGE: FAILURE ATTRIBUTION & CLASSIFICATION")
    with StageTimer() as timer:
        test_out = state.get("test_output", "")
        classification = classify_failure(test_out)

        # G4: Repairability Gate — detect unrecoverable repeating failure patterns
        class_history = list(state.get("failure_classification_history") or [])
        class_history.append(classification)
        unrepairable = False
        if len(class_history) >= 2 and class_history[-1] == class_history[-2] and classification in ("IMPORT_ERROR", "SYNTAX_ERROR"):
            logger.warning("UNREPAIRABLE FAILURE PATTERN DETECTED: Repeated %s indicates structural blocker.", classification)
            unrepairable = True

        prompt = [
            {
                "role": "system",
                "content": f"Diagnose the test failure classified as {classification}. Isolate the root cause and explain precisely why the assertion failed.",
            },
            {
                "role": "user",
                "content": f"Task: {state['task_instruction']}\nCategory: {classification}\nTest Output:\n{test_out}",
            },
        ]
        try:
            res = router.execute_with_fallback(role="debugger", messages=prompt, temperature=0.0)
            attribution = f"[{classification}] {res.content.strip()}"
        except Exception:
            attribution = f"[{classification}] Test assertion failed. Stack trace indicates logic error in patched function."

    ledger_entry = create_ledger_entry(
        stage="FAILURE",
        iteration=state["iteration"],
        status="failure_attributed",
        failure_classification=classification,
        failure_attribution=attribution,
        unrepairable=unrepairable,
        duration_seconds=timer.elapsed,
    )
    ledger_entries = append_ledger_entry(state.get("ledger_entries"), ledger_entry)

    return {
        "status": "failure_attributed",
        "failure_classification": classification,
        "failure_attribution": attribution,
        "failure_classification_history": class_history,
        "unrepairable": unrepairable,
        "ledger_entries": ledger_entries,
        "history": state["history"] + ["FAILURE"],
    }


def refine_stage(state: CodingState) -> Dict[str, Any]:
    """07 / REFINE: Prescribe minimal surgical remediation for the next iteration."""
    logger.info("LOOP STAGE: REFINE")
    with StageTimer() as timer:
        prompt = [
            {
                "role": "system",
                "content": "Formulate a surgical remediation plan to fix the attributed root cause without collateral changes.",
            },
            {
                "role": "user",
                "content": f"Attribution:\n{state['failure_attribution']}\nInvariants:\n{state['invariants']}",
            },
        ]
        try:
            res = router.execute_with_fallback(role="debugger", messages=prompt, temperature=0.0)
            remediation = res.content.strip()
        except Exception:
            remediation = "Fix logic flaw in target function while preserving input/output signatures."

    ledger_entry = create_ledger_entry(
        stage="REFINE",
        iteration=state["iteration"],
        status="refined",
        duration_seconds=timer.elapsed,
        extra={"remediation_plan": remediation[:300]},
    )
    ledger_entries = append_ledger_entry(state.get("ledger_entries"), ledger_entry)

    return {
        "iteration": state["iteration"] + 1,
        "status": "refined",
        "remediation_plan": remediation,
        "ledger_entries": ledger_entries,
        "history": state["history"] + ["REFINE"],
    }


def reevaluate_stage(state: CodingState) -> Dict[str, Any]:
    """08 / RE-EVALUATE: Convergence verification, regression protection gate, and final acceptance."""
    logger.info("LOOP STAGE: RE-EVALUATE")
    with StageTimer() as timer:
        regression_target = state.get("regression_test_target")
        regression_detected = False
        regression_output = ""

        if regression_target:
            logger.info("Running regression test gate against: %s", regression_target)
            reg_res = run_test_suite(
                workspace_root=Path(state["workspace_root"]),
                test_target=regression_target,
            )
            if not reg_res.success:
                logger.warning("REGRESSION DETECTED: Regression test suite failed post-mutation!")
                regression_detected = True
                regression_output = reg_res.output

        status_label = "regression_detected" if regression_detected else "converged_accepted"

    ledger_entry = create_ledger_entry(
        stage="RE-EVALUATE",
        iteration=state["iteration"],
        status=status_label,
        regression_detected=regression_detected,
        duration_seconds=timer.elapsed,
        extra={"regression_target": regression_target},
    )
    ledger_entries = append_ledger_entry(state.get("ledger_entries"), ledger_entry)

    result: Dict[str, Any] = {
        "status": status_label,
        "regression_detected": regression_detected,
        "ledger_entries": ledger_entries,
        "history": state["history"] + ["RE-EVALUATE"],
    }
    if regression_detected:
        result["test_output"] = f"REGRESSION TEST FAILURE:\n{regression_output}"
        result["test_passed"] = False

    return result


def rollback_and_stop_stage(state: CodingState) -> Dict[str, Any]:
    """Terminal Guard: Rollback workspace cleanly upon unrecoverable failure, tampering, or no-progress cycle."""
    with StageTimer() as timer:
        if state.get("test_integrity_violation"):
            reason = "TEST INTEGRITY VIOLATION"
            final_status = "test_tampering_rolled_back"
        elif state.get("unrepairable"):
            reason = "UNREPAIRABLE FAILURE PATTERN"
            final_status = "unrepairable_rolled_back"
        elif state.get("no_progress_detected"):
            reason = "NO PROGRESS DETECTED"
            final_status = "no_progress_rolled_back"
        elif state.get("regression_detected"):
            reason = "UNRESOLVED REGRESSION AT BUDGET EXHAUSTION"
            final_status = "regression_rolled_back"
        else:
            reason = "ITERATION BUDGET EXHAUSTED"
            final_status = "failed_rolled_back"

        logger.warning("TERMINAL GUARD TRIGGERED (%s): Executing deterministic Git rollback.", reason)

        cp_ref = state.get("git_checkpoint_ref")
        if cp_ref:
            rollback_res = git_rollback(Path(state["workspace_root"]), checkpoint_ref=cp_ref)
            logger.info("Git rollback executed: %s", rollback_res.success)

    ledger_entry = create_ledger_entry(
        stage="ROLLBACK_AND_STOP",
        iteration=state["iteration"],
        status=final_status,
        rolled_back=True,
        decision=reason,
        duration_seconds=timer.elapsed,
    )
    ledger_entries = append_ledger_entry(state.get("ledger_entries"), ledger_entry)

    return {
        "status": final_status,
        "rolled_back": True,
        "ledger_entries": ledger_entries,
        "history": state["history"] + ["ROLLBACK_AND_STOP"],
    }


def check_verification_decision(
    state: CodingState,
) -> Literal["accept", "retry", "fail"]:
    if state.get("test_integrity_violation"):
        logger.critical("Decision: fail immediately due to test integrity violation.")
        return "fail"
    if state.get("no_progress_detected"):
        logger.warning("Decision: fail due to repeated failure without progress.")
        return "fail"
    if state.get("unrepairable"):
        logger.warning("Decision: fail due to structurally unrepairable failure pattern.")
        return "fail"
    if state.get("test_passed"):
        return "accept"
    if state.get("iteration", 1) < state.get("max_iterations", 3):
        return "retry"
    return "fail"


def check_reevaluate_decision(
    state: CodingState,
) -> Literal["accept", "retry", "fail"]:
    if not state.get("regression_detected"):
        return "accept"
    if state.get("iteration", 1) < state.get("max_iterations", 3):
        logger.warning("Decision: retry to repair regression detected in re-evaluation.")
        return "retry"
    logger.warning("Decision: fail and rollback due to unresolvable regression at budget exhaustion.")
    return "fail"


def build_coding_loop():
    """Compiles the 8-stage Loop Engineering StateGraph for coding tasks with rollback guards."""
    graph = StateGraph(CodingState)

    graph.add_node("define", define_stage)
    graph.add_node("plan", plan_stage)
    graph.add_node("implement", implement_stage)
    graph.add_node("test", test_stage)
    graph.add_node("verify", verify_stage)
    graph.add_node("failure", failure_stage)
    graph.add_node("refine", refine_stage)
    graph.add_node("reevaluate", reevaluate_stage)
    graph.add_node("rollback_and_stop", rollback_and_stop_stage)

    graph.add_edge(START, "define")
    graph.add_edge("define", "plan")
    graph.add_edge("plan", "implement")
    graph.add_edge("implement", "test")
    graph.add_edge("test", "verify")

    graph.add_conditional_edges(
        "verify",
        check_verification_decision,
        {
            "accept": "reevaluate",
            "retry": "failure",
            "fail": "rollback_and_stop",
        },
    )

    graph.add_edge("failure", "refine")
    graph.add_edge("refine", "implement")

    graph.add_conditional_edges(
        "reevaluate",
        check_reevaluate_decision,
        {
            "accept": END,
            "retry": "failure",
            "fail": "rollback_and_stop",
        },
    )

    graph.add_edge("rollback_and_stop", END)

    return graph.compile()

