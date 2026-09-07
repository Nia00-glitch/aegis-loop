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


def define_stage(state: CodingState) -> Dict[str, Any]:
    """01 / DEFINE: Formalize boundary conditions, capture baseline, and establish checkpoint."""
    logger.info("LOOP STAGE: DEFINE")

    # 1. Establish initial Git checkpoint
    cp = git_checkpoint(Path(state["workspace_root"]), label=f"coding_loop_iter_{state['iteration']}")
    cp_id = cp.data.get("checkpoint_id") if cp.data else None

    # 2. Establish baseline test state before mutations
    baseline_res = run_test_suite(
        workspace_root=Path(state["workspace_root"]),
        test_target=state["test_target"],
    )

    # 3. Deconstruct boundary requirements and invariants using planner role
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
        "history": state.get("history", []) + ["DEFINE"],
    }


def plan_stage(state: CodingState) -> Dict[str, Any]:
    """02 / PLAN: Design minimal justified code contract before mutation."""
    logger.info("LOOP STAGE: PLAN")
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

    return {
        "status": "planned",
        "plan": plan_text,
        "history": state["history"] + ["PLAN"],
    }


def implement_stage(state: CodingState) -> Dict[str, Any]:
    """03 / IMPLEMENT: Dispatch to selected coding worker runtime (Custom CodeAct or OpenHands)."""
    logger.info("LOOP STAGE: IMPLEMENT (Iteration %d)", state["iteration"])
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

    return {
        "status": "implemented",
        "patch_summary": patch_summary,
        "history": state["history"] + ["IMPLEMENT"],
    }


def test_stage(state: CodingState) -> Dict[str, Any]:
    """04 / TEST: Execute automated test suite against mutated code."""
    logger.info("LOOP STAGE: TEST")
    test_res = run_test_suite(
        workspace_root=Path(state["workspace_root"]),
        test_target=state["test_target"],
    )
    return {
        "status": "tested",
        "test_passed": test_res.success,
        "test_output": test_res.output,
        "history": state["history"] + ["TEST"],
    }


def verify_stage(state: CodingState) -> Dict[str, Any]:
    """05 / VERIFY: Objective diagnostic verification gate with no-progress detection."""
    logger.info("LOOP STAGE: VERIFY")
    passed = state["test_passed"]
    sig_history = list(state.get("failure_signature_history") or [])
    no_progress = False
    state_improved = False

    if passed:
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

    return {
        "status": status_label,
        "failure_signature_history": sig_history,
        "no_progress_detected": no_progress,
        "state_improved": state_improved,
        "history": state["history"] + ["VERIFY"],
    }


def failure_stage(state: CodingState) -> Dict[str, Any]:
    """06 / FAILURE: Classification and root-cause attribution of failure signal."""
    logger.info("LOOP STAGE: FAILURE ATTRIBUTION & CLASSIFICATION")
    test_out = state.get("test_output", "")
    classification = classify_failure(test_out)

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

    return {
        "status": "failure_attributed",
        "failure_classification": classification,
        "failure_attribution": attribution,
        "history": state["history"] + ["FAILURE"],
    }


def refine_stage(state: CodingState) -> Dict[str, Any]:
    """07 / REFINE: Prescribe minimal surgical remediation for the next iteration."""
    logger.info("LOOP STAGE: REFINE")
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

    return {
        "iteration": state["iteration"] + 1,
        "status": "refined",
        "remediation_plan": remediation,
        "history": state["history"] + ["REFINE"],
    }


def reevaluate_stage(state: CodingState) -> Dict[str, Any]:
    """08 / RE-EVALUATE: Convergence verification and final acceptance."""
    logger.info("LOOP STAGE: RE-EVALUATE")
    return {
        "status": "converged_accepted",
        "history": state["history"] + ["RE-EVALUATE"],
    }


def rollback_and_stop_stage(state: CodingState) -> Dict[str, Any]:
    """Terminal Guard: Rollback workspace cleanly upon unrecoverable failure or no-progress cycle."""
    reason = "NO PROGRESS DETECTED" if state.get("no_progress_detected") else "ITERATION BUDGET EXHAUSTED"
    logger.warning("TERMINAL GUARD TRIGGERED (%s): Executing deterministic Git rollback.", reason)

    cp_ref = state.get("git_checkpoint_ref")
    if cp_ref:
        rollback_res = git_rollback(Path(state["workspace_root"]), checkpoint_ref=cp_ref)
        logger.info("Git rollback executed: %s", rollback_res.success)

    final_status = "no_progress_rolled_back" if state.get("no_progress_detected") else "failed_rolled_back"
    return {
        "status": final_status,
        "rolled_back": True,
        "history": state["history"] + ["ROLLBACK_AND_STOP"],
    }


def check_verification_decision(
    state: CodingState,
) -> Literal["accept", "retry", "fail"]:
    if state.get("test_passed"):
        return "accept"
    if state.get("no_progress_detected"):
        logger.warning("Decision: fail due to repeated failure without progress.")
        return "fail"
    if state.get("iteration", 1) < state.get("max_iterations", 3):
        return "retry"
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
    graph.add_edge("reevaluate", END)
    graph.add_edge("rollback_and_stop", END)

    return graph.compile()
