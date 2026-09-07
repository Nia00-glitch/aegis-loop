"""
Controlled Causal Ablation Experiment: Adaptive Turn-Budget Handover & Context Preservation vs Control.

Research Hypothesis:
"Does adaptive turn-budget handover and context preservation between Loop macro-iterations
improve recovery from worker-budget exhaustion without weakening any existing Loop Engineering safety or evaluator guarantees?"

Controls:
- Identical task, repository, model, worker, tools, evaluator, injected failure, initial state, and overall budget ceiling (25 turns).
- Independent 3-Tier Verification (Visible, Regression, Hidden Invariants).
- Safety Preserved: Evaluator integrity, G1-G4 guards, rollback mechanics, and anti-gaming protection are strictly active.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.causal_ablation_experiment import (
    SYMPTOM_INSTRUCTIONS,
    inject_flawed_regression_patch,
)
from benchmarks.repo_benchmark import (
    scaffold_task_ledger,
    scaffold_task_rate_limiter,
)
from src.coding_agent.tools import run_test_suite
from src.loops.coding_loop import build_coding_loop
from src.loops.loop_ledger import summarize_ledger

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class HandoverTrialResult:
    task_id: str
    condition: str  # "control" vs "treatment"
    test_regime: str  # "regression_injected"
    model_name: str
    # 14 Experimental Metrics
    repair_success: bool
    final_independently_verified_correctness: bool
    regression_violations: bool
    hidden_invariant_violations: bool
    rollback_rate: float  # 1.0 if rolled back, 0.0 if accepted
    no_progress_triggers: bool
    repeated_failure_signatures: bool
    worker_budget_exhaustion: bool
    unnecessary_repair: bool
    macro_iterations: int
    total_micro_turns: int
    wall_clock_duration_seconds: float
    context_carried_forward: bool
    recovery_after_budget_exhaustion: bool
    # Provenance & Audit
    patch_summary: str
    final_status: str
    ledger_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class HandoverExperimentReport:
    timestamp: str
    research_hypothesis: str
    overall_micro_turn_ceiling: int
    trials: List[HandoverTrialResult] = field(default_factory=list)
    control_success_rate: float = 0.0
    treatment_success_rate: float = 0.0
    recovery_advantage_delta: float = 0.0


def run_handover_trial(
    scaffolder: Callable[[Path], Dict[str, Any]],
    condition: str,  # "control" vs "treatment"
    test_regime: str = "regression_injected",
    model_name: str = "combo/coder",
    max_total_micro_turns: int = 25,
) -> HandoverTrialResult:
    temp_dir = Path(tempfile.mkdtemp(prefix=f"handover_{condition[:4]}_"))
    try:
        # Initialize Git repo
        os.system(f'git -C "{temp_dir}" init -q')
        os.system(f'git -C "{temp_dir}" config user.email test@example.com')
        os.system(f'git -C "{temp_dir}" config user.name "Test Runner"')

        spec = scaffolder(temp_dir)
        task_id = spec["task_id"]
        instruction = SYMPTOM_INSTRUCTIONS.get(task_id, spec["instruction"])

        # Inject flawed regression patch
        if test_regime == "regression_injected":
            inject_flawed_regression_patch(task_id, temp_dir)

        # Baseline commit
        os.system(f'git -C "{temp_dir}" add .')
        os.system(f'git -C "{temp_dir}" commit -m "Initial baseline with injected regression" -q')

        t_start = time.time()
        adaptive_enabled = condition == "treatment"

        loop = build_coding_loop()
        state = loop.invoke({
            "workspace_root": str(temp_dir),
            "task_instruction": instruction,
            "test_target": spec["visible_test"],
            "regression_test_target": spec["regression_test"],
            "model_role": model_name,
            "iteration": 1,
            "max_iterations": 3,
            "max_total_micro_turns": max_total_micro_turns,
            "adaptive_budget_enabled": adaptive_enabled,
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

        duration = round(time.time() - t_start, 2)
        macro_iterations = state.get("iteration", 1)
        rollback_triggered = bool(state.get("rolled_back"))
        final_status = state.get("status", "")
        patch_summary = state.get("patch_summary", "")

        # Extract ledger telemetry
        ledger_entries = state.get("ledger_entries") or []
        ledger_summary = summarize_ledger(ledger_entries) if ledger_entries else None
        guard_events = ledger_summary.get("guard_events", {}) if ledger_summary else {}

        # -------------------------------------------------------------
        # STRICT INDEPENDENT 3-TIER POST-RUN EVALUATION
        # -------------------------------------------------------------
        vis_res = run_test_suite(temp_dir, spec["visible_test"])
        visible_passed = vis_res.success

        reg_res = run_test_suite(temp_dir, spec["regression_test"])
        regression_passed = reg_res.success
        regression_violated = not regression_passed

        hidden_path = temp_dir / spec["hidden_test_path"]
        hidden_path.write_text(spec["hidden_test_code"], encoding="utf-8")
        hid_res = run_test_suite(temp_dir, spec["hidden_test_path"])
        hidden_passed = hid_res.success
        hidden_violated = not hidden_passed

        strictly_successful = visible_passed and regression_passed and hidden_passed and not rollback_triggered
        repair_success = bool(state.get("test_passed")) and strictly_successful

        # Calculate experimental metrics
        no_progress_triggered = bool(guard_events.get("no_progress_triggered"))
        sig_history = state.get("failure_signature_history") or []
        repeated_failure_signature = len(sig_history) > 1 and any(sig_history[i] == sig_history[i-1] for i in range(1, len(sig_history)))

        # Check if worker budget was exhausted on any iteration
        worker_budget_exhausted = any(
            e.get("status") == "implemented" and "Maximum turn budget reached" in e.get("patch_summary", "")
            for e in ledger_entries
        ) or "Maximum turn budget reached" in patch_summary

        context_carried_forward = adaptive_enabled and state.get("handover_context") is not None
        recovery_after_budget_exhaustion = worker_budget_exhausted and strictly_successful

        total_micro_turns = state.get("total_micro_turns", 0)

        unnecessary_repair = regression_violated

        return HandoverTrialResult(
            task_id=task_id,
            condition=condition,
            test_regime=test_regime,
            model_name=model_name,
            repair_success=repair_success,
            final_independently_verified_correctness=strictly_successful,
            regression_violations=regression_violated,
            hidden_invariant_violations=hidden_violated,
            rollback_rate=1.0 if rollback_triggered else 0.0,
            no_progress_triggers=no_progress_triggered,
            repeated_failure_signatures=repeated_failure_signature,
            worker_budget_exhaustion=worker_budget_exhausted,
            unnecessary_repair=unnecessary_repair,
            macro_iterations=macro_iterations,
            total_micro_turns=total_micro_turns,
            wall_clock_duration_seconds=duration,
            context_carried_forward=context_carried_forward,
            recovery_after_budget_exhaustion=recovery_after_budget_exhaustion,
            patch_summary=patch_summary,
            final_status=final_status,
            ledger_summary=ledger_summary,
            error=None if strictly_successful else f"Vis:{visible_passed} Reg:{regression_passed} Hid:{hidden_passed} Status:{final_status}",
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_controlled_handover_experiment() -> HandoverExperimentReport:
    print("=" * 80)
    print("CONTROLLED CAUSAL EXPERIMENT: ADAPTIVE TURN-BUDGET & CONTEXT HANDOVER")
    print("=" * 80)
    print("Hypothesis: Adaptive turn-budget handover and context preservation improves recovery")
    print("            from worker-budget exhaustion without weakening safety or evaluator guarantees.")
    print("-" * 80)

    tasks = [
        scaffold_task_rate_limiter,  # Previously observed Trial-11 failure
        scaffold_task_ledger,        # Verified working regression task (check for no regressions)
    ]

    trials: List[HandoverTrialResult] = []

    for scaff in tasks:
        task_name = scaff.__name__
        print(f"\nEvaluating Task: {task_name}")

        # 1. CONTROL CONDITION
        print("  Running Condition: CONTROL (Fixed 10-turn budget, no context handover)...")
        res_ctrl = run_handover_trial(scaff, condition="control")
        trials.append(res_ctrl)
        print(f"    CONTROL   -> Correct: {res_ctrl.final_independently_verified_correctness} | Status: {res_ctrl.final_status} | Micro-Turns: {res_ctrl.total_micro_turns} | Rollback: {res_ctrl.rollback_rate} | Duration: {res_ctrl.wall_clock_duration_seconds}s")

        # 2. TREATMENT CONDITION
        print("  Running Condition: TREATMENT (Adaptive budget handover + context preservation)...")
        res_treat = run_handover_trial(scaff, condition="treatment")
        trials.append(res_treat)
        print(f"    TREATMENT -> Correct: {res_treat.final_independently_verified_correctness} | Status: {res_treat.final_status} | Micro-Turns: {res_treat.total_micro_turns} | Rollback: {res_treat.rollback_rate} | Duration: {res_treat.wall_clock_duration_seconds}s")

    ctrl_trials = [t for t in trials if t.condition == "control"]
    treat_trials = [t for t in trials if t.condition == "treatment"]

    ctrl_success = sum(1 for t in ctrl_trials if t.final_independently_verified_correctness)
    treat_success = sum(1 for t in treat_trials if t.final_independently_verified_correctness)

    ctrl_rate = round((ctrl_success / len(ctrl_trials)) * 100.0, 1) if ctrl_trials else 0.0
    treat_rate = round((treat_success / len(treat_trials)) * 100.0, 1) if treat_trials else 0.0
    delta = round(treat_rate - ctrl_rate, 1)

    report = HandoverExperimentReport(
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        research_hypothesis="Adaptive turn-budget handover and context preservation improves recovery from worker-budget exhaustion without weakening safety or evaluator guarantees.",
        overall_micro_turn_ceiling=25,
        trials=trials,
        control_success_rate=ctrl_rate,
        treatment_success_rate=treat_rate,
        recovery_advantage_delta=delta,
    )

    report_path = Path(__file__).resolve().parents[1] / "benchmarks" / "handover_ablation_experiment_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2)
    print(f"\nSaved handover experiment telemetry to: {report_path}")

    print("\n" + "=" * 80)
    print("EXPERIMENTAL SUMMARY")
    print("=" * 80)
    print(f"Control Success Rate:    {ctrl_rate}% ({ctrl_success}/{len(ctrl_trials)})")
    print(f"Treatment Success Rate:  {treat_rate}% ({treat_success}/{len(treat_trials)})")
    print(f"Causal Advantage Delta:  {delta:+0.1f}%")
    print("=" * 80)
    return report


if __name__ == "__main__":
    run_controlled_handover_experiment()
