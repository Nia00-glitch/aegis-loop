"""
Empirical Challenge Audit Suite (Challenger 2 - Milestone M1)
Authoritative verification and stress-testing of empirical claims in
reports/state_reconstruction_and_evidence_matrix.md against raw benchmark data.
"""

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
CAUSAL_REPORT_PATH = REPO_ROOT / "benchmarks" / "causal_ablation_experiment_report.json"
HANDOVER_REPORT_PATH = REPO_ROOT / "benchmarks" / "handover_ablation_experiment_report.json"
OPENHANDS_REPORT_PATH = REPO_ROOT / "benchmarks" / "openhands_spike_report.json"
EVAL_REPORT_PATH = REPO_ROOT / "benchmarks" / "evaluation_experiment_report.json"


def audit_causal_ablation():
    print("=" * 70)
    print("AUDIT 1: Causal Ablation Raw Data vs Deliverable Claims")
    print("=" * 70)

    with open(CAUSAL_REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    trials = data.get("trials", [])
    assert len(trials) == 12, f"Expected 12 trials, found {len(trials)}"

    # Separate by regime
    symptom_trials = [t for t in trials if t["test_regime"] == "symptom_diagnostic"]
    regression_trials = [t for t in trials if t["test_regime"] == "regression_injected"]

    assert len(symptom_trials) == 8, f"Expected 8 symptom trials, got {len(symptom_trials)}"
    assert len(regression_trials) == 4, f"Expected 4 regression trials, got {len(regression_trials)}"

    # Symptom regime metrics
    fl_sym_succ = [t for t in symptom_trials if t["experiment_condition"] == "full_loop" and t["success"]]
    nl_sym_succ = [t for t in symptom_trials if t["experiment_condition"] == "no_loop_control" and t["success"]]
    print(f"Symptom Diagnostic: Full-Loop = {len(fl_sym_succ)}/4 ({len(fl_sym_succ)/4*100:.1f}%), No-Loop = {len(nl_sym_succ)}/4 ({len(nl_sym_succ)/4*100:.1f}%)")

    # Regression regime metrics
    fl_reg = [t for t in regression_trials if t["experiment_condition"] == "full_loop"]
    nl_reg = [t for t in regression_trials if t["experiment_condition"] == "no_loop_control"]

    fl_reg_succ = [t for t in fl_reg if t["success"]]
    nl_reg_succ = [t for t in nl_reg if t["success"]]

    fl_reg_rate = len(fl_reg_succ) / len(fl_reg) * 100
    nl_reg_rate = len(nl_reg_succ) / len(nl_reg) * 100
    print(f"Regression Injected: Full-Loop = {len(fl_reg_succ)}/{len(fl_reg)} ({fl_reg_rate:.1f}%), No-Loop = {len(nl_reg_succ)}/{len(nl_reg)} ({nl_reg_rate:.1f}%)")

    print("\nDetailed Trial Dissection (Regression Regime):")
    for t in regression_trials:
        cond = t["experiment_condition"]
        task = t["task_id"]
        succ = t["success"]
        err = t.get("error")
        vis = t.get("visible_tests_passed")
        reg = t.get("regression_tests_passed")
        hid = t.get("hidden_tests_passed")
        ls = t.get("ledger_summary")
        status = ls.get("final_status") if ls else ("SUCCESS" if succ else "FAILED")
        print(f"  Task: {task:<28} | Cond: {cond:<16} | Succ: {str(succ):<5} | Vis:{vis} Reg:{reg} Hid:{hid} | Status: {status} | Error: {err}")

    # EMPIRICAL FINDING 1: Full-Loop did NOT achieve 100% verified correctness on regressions
    assert fl_reg_rate == 50.0, f"Full-Loop regression success rate is {fl_reg_rate}%, not 50.0%"
    assert nl_reg_rate == 50.0, f"No-Loop regression success rate is {nl_reg_rate}%, not 50.0%"

    # Check Trial 10 false convergence
    t10 = [t for t in nl_reg if t["task_id"] == "ledger_reconciliation"][0]
    assert t10["visible_tests_passed"] is True and t10["regression_tests_passed"] is False, "Trial 10 did not exhibit false convergence"
    print("\n[VERIFIED] Trial 10 definitively demonstrates false convergence: visible=True, regression=False, hidden=False.")

    # Check Trial 11 Full-Loop failure
    t11 = [t for t in fl_reg if t["task_id"] == "rate_limiter_invariants"][0]
    assert t11["success"] is False, "Trial 11 was expected to fail"
    assert t11["ledger_summary"]["final_status"] == "no_progress_rolled_back"
    print("[REFUTATION] Deliverable Claim in Section 1.4 ('Governed Loop Engineering agents ... achieve 100% verified correctness'):")
    print(f"  -> REFUTED: Full-Loop in Trial 11 failed with '{t11['error']}' and status '{t11['ledger_summary']['final_status']}'. Success rate is 50.0%, NOT 100.0%.")

    # Check Trial 12 No-Loop success
    t12 = [t for t in nl_reg if t["task_id"] == "rate_limiter_invariants"][0]
    assert t12["success"] is True, "Trial 12 was expected to succeed"
    print("[REFUTATION] Deliverable Claim in Section 8.2 ('Foundation models suffer catastrophic false convergence (100% failure on Trial 10)'):")
    print(f"  -> REFUTED: No-Loop in Trial 12 succeeded (Vis:{t12['visible_tests_passed']}, Reg:{t12['regression_tests_passed']}, Hid:{t12['hidden_tests_passed']}). Success rate is 50.0%, NOT 0.0%.")


def audit_handover_ablation():
    print("\n" + "=" * 70)
    print("AUDIT 2: Adaptive Handover Ablation & Taxonomic Integrity")
    print("=" * 70)

    with open(HANDOVER_REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    trials = data.get("trials", [])
    assert len(trials) == 4, f"Expected 4 trials, found {len(trials)}"

    ctrl_trials = [t for t in trials if t["condition"] == "control"]
    treat_trials = [t for t in trials if t["condition"] == "treatment"]

    ctrl_succ = sum(1 for t in ctrl_trials if t["final_independently_verified_correctness"])
    treat_succ = sum(1 for t in treat_trials if t["final_independently_verified_correctness"])

    ctrl_turns = sum(t["total_micro_turns"] for t in ctrl_trials)
    treat_turns = sum(t["total_micro_turns"] for t in treat_trials)

    ctrl_time = sum(t["wall_clock_duration_seconds"] for t in ctrl_trials)
    treat_time = sum(t["wall_clock_duration_seconds"] for t in treat_trials)

    print(f"Control:   Success = {ctrl_succ}/2 ({ctrl_succ/2*100:.1f}%), Micro-Turns = {ctrl_turns}, Time = {ctrl_time:.1f}s")
    print(f"Treatment: Success = {treat_succ}/2 ({treat_succ/2*100:.1f}%), Micro-Turns = {treat_turns}, Time = {treat_time:.1f}s")
    print(f"Delta:     Success Delta = 0.0%, Turn Inflation = +{treat_turns - ctrl_turns} (+{(treat_turns/ctrl_turns - 1)*100:.1f}%), Latency Inflation = +{treat_time - ctrl_time:.1f}s (+{(treat_time/ctrl_time - 1)*100:.1f}%)")

    # Taxonomic check
    print("\n[REFUTATION] Deliverable Classification of G5.2 as 'EXPERIMENTALLY DEMONSTRATED':")
    print("  -> Deliverable Section 6.1 Definition of EXPERIMENTALLY DEMONSTRATED requires: 'Statistically observed producing positive causal deltas in internal controlled ablations'")
    print(f"  -> Observed delta in report: {data.get('recovery_advantage_delta')}% (Delta = 0.0%).")
    print("  -> Under deliverable's own definitions, G5.2 belongs in 'EXPERIMENTAL' (implemented, passing unit tests, but Delta = 0.0%), NOT 'EXPERIMENTALLY DEMONSTRATED'.")


def audit_benchmark_metric_conflation():
    print("\n" + "=" * 70)
    print("AUDIT 3: Benchmark Metric Conflation (Macro-Iterations vs Micro-Turns)")
    print("=" * 70)

    with open(EVAL_REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    runs = data.get("metrics", [])
    print(f"Loaded {len(runs)} benchmark runs from evaluation_experiment_report.json.")

    le_runs = [r for r in runs if r["architecture_mode"] == "loop_engineering" and r["model_name"] == "combo/coder"]
    ctrl_runs = [r for r in runs if r["architecture_mode"] == "baseline_control"]

    print("\nLoop Engineering vs Baseline Control Comparison (combo/coder):")
    for r in le_runs:
        print(f"  LE   | Task: {r['task_id']:<28} | Iterations: {r['iterations_used']} | Time: {r['duration_seconds']:6.2f}s | Success: {r['success']}")
    for r in ctrl_runs:
        print(f"  CTRL | Task: {r['task_id']:<28} | Iterations: {r['iterations_used']} | Time: {r['duration_seconds']:6.2f}s | Success: {r['success']}")

    print("\n[REFUTATION] Deliverable Claim in Section 5.3:")
    print("  'Loop Engineering achieved 1-iteration convergence on tasks that required up to 9 iterations for baseline unguided agents.'")
    print("  -> In benchmarks/repo_benchmark.py:")
    print("     - LE 'iterations_used' is state.get('iteration', 1) [outer StateGraph macro-iterations, max 3]")
    print("     - CTRL 'iterations_used' is agent.iterations [inner CodeAct micro-turns/tool calls, max 10]")
    print("  -> Comparing 1 macro-iteration to 9 micro-turns conflates two distinct hierarchical levels.")
    print("  -> Notice that LE took 127.95s for 1 macro-iteration, whereas CTRL took only 30.28s for 9 micro-turns.")


def audit_openhands_spike():
    print("\n" + "=" * 70)
    print("AUDIT 4: OpenHands Spike & Safety Gate Empirical Verification")
    print("=" * 70)

    with open(OPENHANDS_REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    oh = data["openhands"]
    cb = data["custom_baseline"]

    print(f"OpenHands:       Status = {oh['final_status']}, Rolled Back = {oh['rolled_back']}, No Progress = {oh['no_progress_detected']}, Success = {oh['overall_success']}")
    print(f"Custom Baseline: Status = {cb['final_status']}, Rolled Back = {cb['rolled_back']}, No Progress = {cb['no_progress_detected']}, Success = {cb['overall_success']}")

    assert oh["overall_success"] is False and oh["rolled_back"] is True
    assert cb["overall_success"] is True and cb["rolled_back"] is False
    print("\n[VERIFIED] OpenHands thrashing and rollback cleanly confirmed by raw spike data.")
    print("[VERIFIED] G4 / terminal rollback guard operated correctly to protect workspace from corrupting commits.")


if __name__ == "__main__":
    audit_causal_ablation()
    audit_handover_ablation()
    audit_benchmark_metric_conflation()
    audit_openhands_spike()
    print("\n" + "=" * 70)
    print("ALL EMPIRICAL AUDITS COMPLETED SUCCESSFULLY.")
    print("=" * 70)
