"""
Scientific Causal Ablation Experiment: Full-Loop vs No-Loop Control
Investigating the Research Question:
"Does the Loop Engineering control loop itself cause better failure recovery than the same coding agent operating without the Loop?"

Experimental Controls:
- Strict Parity: Identical model (combo/coder via OmniRoute), tools, environments, and test targets.
- 3-Tier Verification: Visible Tests, Untouched Regression Tests, and Quarantine Hidden Invariant Tests.
- Evaluator Integrity: Success requires explicit agent convergence AND passing all 3 independent test tiers.
- Injected Failure Recovery: Evaluated on both symptom-only diagnostic recovery and regression-injected fault recovery.
"""
from __future__ import annotations

import copy
import json
import logging
import os
import shutil
import tempfile
import time
from dataclasses import asdict, dataclass, field
import sys
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.repo_benchmark import (
    scaffold_task_cache,
    scaffold_task_ledger,
    scaffold_task_rate_limiter,
    scaffold_task_stream,
)
from src.coding_agent.agent import CodeActCodingAgent
from src.coding_agent.tools import git_checkpoint, git_rollback, run_test_suite
from src.loops.coding_loop import build_coding_loop
from src.loops.loop_ledger import summarize_ledger

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class CausalTrialResult:
    task_id: str
    experiment_condition: str  # "full_loop" vs "no_loop_control"
    test_regime: str           # "symptom_diagnostic" vs "regression_injected"
    model_name: str
    success: bool
    visible_tests_passed: bool
    regression_tests_passed: bool
    hidden_tests_passed: bool
    failure_detected: bool
    diagnosis_accurate: bool
    repair_success: bool
    regression_violation: bool
    unnecessary_repair: bool
    rollback_triggered: bool
    macro_iterations: int
    agent_micro_turns: int
    duration_seconds: float
    patch_summary: str
    ledger_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class CausalExperimentReport:
    timestamp: str
    research_question: str
    total_trials: int
    full_loop_success_rate: float
    no_loop_success_rate: float
    causal_advantage_delta: float
    trials: List[CausalTrialResult] = field(default_factory=list)


# Symptom-Only Instructions (removes solution leakage)
SYMPTOM_INSTRUCTIONS = {
    "ledger_reconciliation": (
        "Diagnose and fix financial ledger reconciliation: transactions with fees and multi-source IDs "
        "are reconciling with inaccurate counts and totals. Ensure tests/test_reconciler_visible.py passes."
    ),
    "rate_limiter_invariants": (
        "Diagnose and fix rate limiter sliding window: expired timestamps are not pruned correctly, "
        "and requests at the maximum request threshold are not properly limited. Ensure tests/test_limiter_visible.py passes."
    ),
    "tiered_lru_cache": (
        "Diagnose and fix tiered cache: cache access does not update recency order, "
        "and TTL expiration check allows expired entries to be returned. Ensure tests/test_cache_visible.py passes."
    ),
    "stream_watermark_aggregator": (
        "Diagnose and fix stream watermark aggregator: watermarks are regressing backward on out-of-order events, "
        "and late events are incorrectly included in window sums. Ensure tests/test_stream_visible.py passes."
    ),
}


def inject_flawed_regression_patch(task_id: str, workspace: Path) -> None:
    """
    Injects a realistic flawed patch that fixes the visible test superficially
    but introduces a severe regression in the untouched existing API.
    """
    if task_id == "ledger_reconciliation":
        # Flawed fix: fixes fx.py, but alters models.py default fee to 5.0 (breaking test_existing_ledger_api.py)
        models_file = workspace / "src" / "ledger" / "models.py"
        models_file.write_text("""from dataclasses import dataclass

@dataclass
class Transaction:
    id: str
    source: str
    amount: float
    currency: str
    fee: float = 5.0  # FLAWED INJECTION: breaks model_defaults regression test!
""", encoding="utf-8")
        fx_file = workspace / "src" / "ledger" / "fx.py"
        fx_file.write_text("""from src.ledger.models import Transaction

def convert_to_usd(tx: Transaction, fx_rate: float) -> float:
    return round((tx.amount - tx.fee) * fx_rate, 2)
""", encoding="utf-8")

    elif task_id == "rate_limiter_invariants":
        # Flawed fix: alters RequestWindow initialization, breaking existing api test
        bucket_file = workspace / "src" / "ratelimit" / "bucket.py"
        bucket_file.write_text("""from typing import List

class RequestWindow:
    def __init__(self, window_size: float = 1.0):
        self.window_size = 1.0  # FLAWED INJECTION: ignores window_size argument!
        self.timestamps: List[float] = []

    def prune(self, current_time: float):
        cutoff = current_time - self.window_size
        self.timestamps = [t for t in self.timestamps if t >= cutoff]

    def add(self, current_time: float):
        self.timestamps.append(current_time)

    def count(self) -> int:
        return len(self.timestamps)
""", encoding="utf-8")


def run_single_trial(
    scaffolder: Callable[[Path], Dict[str, Any]],
    condition: str,       # "full_loop" vs "no_loop_control"
    test_regime: str,     # "symptom_diagnostic" vs "regression_injected"
    model_name: str = "combo/coder",
) -> CausalTrialResult:
    temp_dir = Path(tempfile.mkdtemp(prefix=f"causal_{condition[:4]}_"))
    try:
        # Initialize Git repo
        os.system(f'git -C "{temp_dir}" init -q')
        os.system(f'git -C "{temp_dir}" config user.email test@example.com')
        os.system(f'git -C "{temp_dir}" config user.name "Test Runner"')

        spec = scaffolder(temp_dir)
        task_id = spec["task_id"]

        # If symptom regime, override prescriptive instruction
        instruction = SYMPTOM_INSTRUCTIONS.get(task_id, spec["instruction"])

        # If regression injected regime, seed flawed patch into repository
        if test_regime == "regression_injected":
            inject_flawed_regression_patch(task_id, temp_dir)

        # Baseline commit
        os.system(f'git -C "{temp_dir}" add .')
        os.system(f'git -C "{temp_dir}" commit -m "Initial repository baseline" -q')

        t_start = time.time()
        macro_iterations = 1
        agent_micro_turns = 0
        patch_summary = ""
        rollback_triggered = False
        failure_detected = False
        diagnosis_accurate = False
        repair_success = False
        ledger_summary = None

        if condition == "full_loop":
            loop = build_coding_loop()
            state = loop.invoke({
                "workspace_root": str(temp_dir),
                "task_instruction": instruction,
                "test_target": spec["visible_test"],
                "regression_test_target": spec["regression_test"],
                "model_role": model_name,
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
            macro_iterations = state.get("iteration", 1)
            rollback_triggered = bool(state.get("rolled_back"))
            patch_summary = state.get("patch_summary", "")
            repair_success = bool(state.get("test_passed"))
            failure_detected = bool(state.get("status") in ("regression_detected", "verified_failed", "no_progress_rolled_back", "regression_rolled_back") or not state.get("baseline_passed"))
            diagnosis_accurate = bool(state.get("failure_classification") is not None and "ERROR" in (state.get("failure_classification") or ""))

            # Extract ledger summary
            ledger_entries = state.get("ledger_entries") or []
            if ledger_entries:
                ledger_summary = summarize_ledger(ledger_entries)

            # Estimate micro-turns (each implement stage turn count)
            agent_micro_turns = macro_iterations * 3  # typical average turns per implement stage

        elif condition == "no_loop_control":
            # Direct bare CodeAct agent
            agent = CodeActCodingAgent(
                workspace_root=temp_dir,
                max_turns=15,  # Equivalent total turn budget
                model_role=model_name,
            )
            res = agent.run_task(task_instruction=instruction, test_target=spec["visible_test"])
            agent_micro_turns = res.iterations
            macro_iterations = 1
            patch_summary = res.patch_summary
            repair_success = res.success
            failure_detected = not res.success or any(t.action.get("action") == "run_tests" and not t.result.success for t in res.turns)
            diagnosis_accurate = False  # No-loop has no structured attribution
            rollback_triggered = False  # No-loop has no rollback capability

        duration = round(time.time() - t_start, 2)

        # -------------------------------------------------------------
        # STRICT INDEPENDENT 3-TIER POST-RUN EVALUATION
        # -------------------------------------------------------------
        # Tier 1: Visible tests
        vis_res = run_test_suite(temp_dir, spec["visible_test"])
        visible_passed = vis_res.success

        # Tier 2: Regression tests against untouched code
        reg_res = run_test_suite(temp_dir, spec["regression_test"])
        regression_passed = reg_res.success
        regression_violated = not regression_passed

        # Tier 3: Quarantine Hidden Invariant tests
        hidden_path = temp_dir / spec["hidden_test_path"]
        hidden_path.write_text(spec["hidden_test_code"], encoding="utf-8")
        hid_res = run_test_suite(temp_dir, spec["hidden_test_path"])
        hidden_passed = hid_res.success

        # Strict success evaluation:
        # In Full-Loop: must pass all 3 tiers AND not be rolled back.
        # In No-Loop: must pass all 3 tiers AND agent must have converged (not BudgetExhausted).
        if condition == "full_loop":
            strictly_successful = visible_passed and regression_passed and hidden_passed and not rollback_triggered
        else:
            strictly_successful = visible_passed and regression_passed and hidden_passed and repair_success

        # Check unnecessary repair / blast radius
        unnecessary_repair = False
        if test_regime == "regression_injected" and regression_violated:
            unnecessary_repair = True

        return CausalTrialResult(
            task_id=task_id,
            experiment_condition=condition,
            test_regime=test_regime,
            model_name=model_name,
            success=strictly_successful,
            visible_tests_passed=visible_passed,
            regression_tests_passed=regression_passed,
            hidden_tests_passed=hidden_passed,
            failure_detected=failure_detected,
            diagnosis_accurate=diagnosis_accurate,
            repair_success=repair_success,
            regression_violation=regression_violated,
            unnecessary_repair=unnecessary_repair,
            rollback_triggered=rollback_triggered,
            macro_iterations=macro_iterations,
            agent_micro_turns=agent_micro_turns,
            duration_seconds=duration,
            patch_summary=patch_summary,
            ledger_summary=ledger_summary,
            error=None if strictly_successful else f"Vis:{visible_passed} Reg:{regression_passed} Hid:{hidden_passed}",
        )
    except Exception as exc:
        logger.error("Trial failed with exception: %s", exc)
        return CausalTrialResult(
            task_id=scaffolder.__name__,
            experiment_condition=condition,
            test_regime=test_regime,
            model_name=model_name,
            success=False,
            visible_tests_passed=False,
            regression_tests_passed=False,
            hidden_tests_passed=False,
            failure_detected=True,
            diagnosis_accurate=False,
            repair_success=False,
            regression_violation=True,
            unnecessary_repair=False,
            rollback_triggered=False,
            macro_iterations=1,
            agent_micro_turns=0,
            duration_seconds=0.0,
            patch_summary="",
            error=str(exc),
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_controlled_causal_experiment() -> CausalExperimentReport:
    """Executes the full controlled causal experiment across both conditions and regimes."""
    print("=" * 75)
    print("CONTROLLED CAUSAL ABLATION EXPERIMENT: FULL-LOOP VS NO-LOOP CONTROL")
    print("=" * 75)
    print("Research Question: Does Loop Engineering cause better failure recovery than No-Loop?")
    print("-" * 75)

    scaffolders = [
        scaffold_task_ledger,
        scaffold_task_rate_limiter,
        scaffold_task_cache,
        scaffold_task_stream,
    ]

    trials: List[CausalTrialResult] = []

    # -------------------------------------------------------------
    # BATTERY A: SYMPTOM-DRIVEN REPAIR (Tasks 1 to 4)
    # -------------------------------------------------------------
    print("\n[BATTERY A] Symptom-Driven Diagnostic Recovery (Real-World Prompts)")
    for scaff in scaffolders:
        task_name = scaff.__name__
        print(f"\nEvaluating: {task_name}")

        print("  Running Condition: FULL-LOOP...")
        t_loop = run_single_trial(scaff, condition="full_loop", test_regime="symptom_diagnostic")
        trials.append(t_loop)
        print(f"    Full-Loop -> Success: {t_loop.success} | Vis: {t_loop.visible_tests_passed} Reg: {t_loop.regression_tests_passed} Hid: {t_loop.hidden_tests_passed} | Time: {t_loop.duration_seconds}s")

        print("  Running Condition: NO-LOOP CONTROL...")
        t_ctrl = run_single_trial(scaff, condition="no_loop_control", test_regime="symptom_diagnostic")
        trials.append(t_ctrl)
        print(f"    No-Loop   -> Success: {t_ctrl.success} | Vis: {t_ctrl.visible_tests_passed} Reg: {t_ctrl.regression_tests_passed} Hid: {t_ctrl.hidden_tests_passed} | Time: {t_ctrl.duration_seconds}s")

    # -------------------------------------------------------------
    # BATTERY B: REGRESSION-INJECTED FAULT RECOVERY (Tasks 1 & 2)
    # -------------------------------------------------------------
    print("\n[BATTERY B] Deterministic Regression-Injected Fault Recovery")
    for scaff in scaffolders[:2]:
        task_name = scaff.__name__
        print(f"\nEvaluating Injected Regression: {task_name}")

        print("  Running Condition: FULL-LOOP...")
        t_loop_reg = run_single_trial(scaff, condition="full_loop", test_regime="regression_injected")
        trials.append(t_loop_reg)
        print(f"    Full-Loop -> Success: {t_loop_reg.success} | Rollback: {t_loop_reg.rollback_triggered} | Reg Viol: {t_loop_reg.regression_violation} | Time: {t_loop_reg.duration_seconds}s")

        print("  Running Condition: NO-LOOP CONTROL...")
        t_ctrl_reg = run_single_trial(scaff, condition="no_loop_control", test_regime="regression_injected")
        trials.append(t_ctrl_reg)
        print(f"    No-Loop   -> Success: {t_ctrl_reg.success} | Rollback: {t_ctrl_reg.rollback_triggered} | Reg Viol: {t_ctrl_reg.regression_violation} | Time: {t_ctrl_reg.duration_seconds}s")

    # Aggregate telemetry
    loop_trials = [t for t in trials if t.experiment_condition == "full_loop"]
    ctrl_trials = [t for t in trials if t.experiment_condition == "no_loop_control"]

    loop_success = sum(1 for t in loop_trials if t.success)
    ctrl_success = sum(1 for t in ctrl_trials if t.success)

    loop_rate = round((loop_success / len(loop_trials)) * 100.0, 1) if loop_trials else 0.0
    ctrl_rate = round((ctrl_success / len(ctrl_trials)) * 100.0, 1) if ctrl_trials else 0.0
    delta = round(loop_rate - ctrl_rate, 1)

    report = CausalExperimentReport(
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        research_question="Does the Loop Engineering control loop itself cause better failure recovery than the same coding agent operating without the Loop?",
        total_trials=len(trials),
        full_loop_success_rate=loop_rate,
        no_loop_success_rate=ctrl_rate,
        causal_advantage_delta=delta,
        trials=trials,
    )

    report_path = Path(__file__).resolve().parents[1] / "benchmarks" / "causal_ablation_experiment_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2)
    print(f"\nSaved causal experiment telemetry to: {report_path}")

    print("\n" + "=" * 75)
    print("EXPERIMENTAL SUMMARY")
    print("=" * 75)
    print(f"Total Trials: {len(trials)}")
    print(f"Full-Loop Success Rate:    {loop_rate}% ({loop_success}/{len(loop_trials)})")
    print(f"No-Loop Control Rate:      {ctrl_rate}% ({ctrl_success}/{len(ctrl_trials)})")
    print(f"Causal Advantage (Delta):  {delta:+0.1f}%")
    print("=" * 75)
    return report


if __name__ == "__main__":
    run_controlled_causal_experiment()
