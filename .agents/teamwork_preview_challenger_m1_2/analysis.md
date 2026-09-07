# Adversarial Empirical Challenge & Forensic Audit: Milestone M1

**Author**: Challenger 2 (`teamwork_preview_challenger_m1_2`)  
**Role**: Empirical Challenger (critic, specialist)  
**Parent**: `orchestrator_1` (`50bad958-86ec-4534-a7f1-16433dcdb5ac`)  
**Target Deliverable**: `reports/state_reconstruction_and_evidence_matrix.md` (`REP-R1-STATE-EVIDENCE-20260907`)  
**Audit Artifacts**:
- `benchmarks/causal_ablation_experiment_report.json` ($N=12$)
- `benchmarks/handover_ablation_experiment_report.json` ($N=4$)
- `benchmarks/openhands_spike_report.json` ($N=2$)
- `benchmarks/evaluation_experiment_report.json` ($N=13$)
- `benchmarks/repo_benchmark.py`, `benchmarks/causal_ablation_experiment.py`, `benchmarks/handover_ablation_experiment.py`
- `scripts/test_empirical_ablation_audit.py` (Reproducible Challenger Audit Harness)  
**Date**: 2026-09-07  
**Adversarial Verdict**: **CHALLENGE_FAILED** (The target deliverable fails the empirical challenge due to critical empirical overstatements, taxonomic inconsistency, metric conflation, and selective reporting).

---

## 1. Executive Summary & Core Challenge Findings

An empirical challenge must not rely on passive reading of text summaries. As Challenger 2, I developed and executed a deterministic empirical verification harness (`scripts/test_empirical_ablation_audit.py`) to interrogate every raw JSON trial record, state transition trace, timing ledger, and patch summary.

While `reports/state_reconstruction_and_evidence_matrix.md` contains excellent theoretical grounding and accurately captures many repository realities (such as the structural dichotomy between application stubs and the operational loop engine, and the mechanics of Trial 9 and 10), **it suffers from four critical empirical flaws that compromise its scientific objectivity**:

1. **Factual Overstatement of Full-Loop Regression Recovery**:
   In Section 1.4 (line 22), the deliverable asserts:
   > *"Governed Loop Engineering agents reliably intercept the regression via G2, swap targets via G5.1, repair the regression, and achieve 100% verified correctness."*
   **Refutation from Raw Data**: In Trial 11 (`rate_limiter_invariants`, full_loop, regression_injected), Governed Loop Engineering **FAILED** (`Vis:False Reg:False Hid:False`), ran out of turns, and triggered `no_progress_rolled_back` on iteration 2. G2 was not triggered (`regression_detected: false`), G5.1 was not triggered (`target_swapped: false`), and correctness was 0.0%. The actual success rate of Full-Loop under regression stress is **50.0% (1/2)**, NOT 100.0%.

2. **Asymmetric Narrative & Cherry-Picking of Baseline Control Failures**:
   In Section 1.4 (line 22) and Section 8.2 (line 567), the deliverable claims that under regression stress, unguided baseline agents suffer catastrophic false convergence, citing *"100% failure on Trial 10"*.
   **Refutation from Raw Data**: In Trial 12 (`rate_limiter_invariants`, no_loop_control, regression_injected), the unguided baseline agent **SUCCEEDED** (`Vis:True Reg:True Hid:True`), diagnosing both the limiter defect and the injected bucket regression in 8 micro-turns without loops. The author dismissed Trial 12 as having *"passed by luck in 8 turns"* (line 431) while omitting it from the Executive Summary and Section 8.2. Across the regression regime, No-Loop Control had a **50.0% (1/2)** success rate—identically matched with Full-Loop (50.0%).

3. **Taxonomic Inconsistency (Self-Contradiction) on G5.2 Classification**:
   The deliverable defines `EXPERIMENTALLY DEMONSTRATED` (Section 6.1) as requiring:
   > *"Statistically observed producing positive causal deltas in internal controlled ablations holding model, tools, and budget constant."*
   Yet, for G5.2 (Table 6.2), the deliverable records:
   > *"Recovery Advantage Delta: 0.0%"* (Section 5.2) and *"empirical delta over static control is currently Δ = 0.0%"* (Table 6.2).
   Despite an observed advantage delta of **0.0%**, the deliverable promoted G5.2 to **EXPERIMENTALLY DEMONSTRATED**. Under its own rubric, G5.2 is strictly **EXPERIMENTAL** (Category 4).

4. **Hierarchical Metric Conflation (Macro-Iterations vs Micro-Turns)**:
   In Section 5.3 (line 446), the deliverable asserts:
   > *"Loop Engineering achieved 1-iteration convergence on tasks that required up to 9 iterations for baseline unguided agents."*
   **Refutation from Code & Data**: In `benchmarks/repo_benchmark.py`, `iterations_used` for Loop Engineering logs **macro-iterations** of the outer StateGraph (1 to 3), whereas for Baseline Control it logs **micro-turns** (tool calls, 1 to 10) of the inner CodeAct agent. In reality, 1 macro-iteration of Loop Engineering took **127.95s**, while the 9 micro-turns of Baseline Control took only **30.28s**. Comparing macro-iterations to micro-turns is an invalid apples-to-oranges conflation.

---

## 2. Empirical Audit: Causal Ablation Report (`benchmarks/causal_ablation_experiment_report.json`)

The causal ablation battery evaluated $N=12$ trials across 4 core tasks in two experimental regimes.

### 2.1 Complete Raw Data Matrix

| Trial # | Task ID | Condition | Regime | Success | Turns | Macro Iters | Wall Time (s) | Final Status | Evaluator Output |
|:---:|:---|:---|:---|:---:|:---:|:---:|:---:|:---|:---|
| 1 | `ledger_reconciliation` | `full_loop` | `symptom_diagnostic` | **True** | 3 | 1 | 51.76 | `converged_accepted` | `Vis:T Reg:T Hid:T` |
| 2 | `ledger_reconciliation` | `no_loop_control` | `symptom_diagnostic` | **True** | 11 | 1 | 51.26 | `SUCCESS` | `Vis:T Reg:T Hid:T` |
| 3 | `rate_limiter_invariants` | `full_loop` | `symptom_diagnostic` | **True** | 3 | 1 | 56.81 | `converged_accepted` | `Vis:T Reg:T Hid:T` |
| 4 | `rate_limiter_invariants` | `no_loop_control` | `symptom_diagnostic` | **True** | 14 | 1 | 39.72 | `SUCCESS` | `Vis:T Reg:T Hid:T` |
| 5 | `tiered_lru_cache` | `full_loop` | `symptom_diagnostic` | **True** | 3 | 1 | 60.44 | `converged_accepted` | `Vis:T Reg:T Hid:T` |
| 6 | `tiered_lru_cache` | `no_loop_control` | `symptom_diagnostic` | **True** | 10 | 1 | 26.53 | `SUCCESS` | `Vis:T Reg:T Hid:T` |
| 7 | `stream_watermark_aggregator` | `full_loop` | `symptom_diagnostic` | **True** | 3 | 1 | 58.35 | `converged_accepted` | `Vis:T Reg:T Hid:T` |
| 8 | `stream_watermark_aggregator` | `no_loop_control` | `symptom_diagnostic` | **True** | 9 | 1 | 23.59 | `SUCCESS` | `Vis:T Reg:T Hid:T` |
| 9 | `ledger_reconciliation` | `full_loop` | `regression_injected` | **True** | 6 | 2 | 132.84 | `converged_accepted` | `Vis:T Reg:T Hid:T` |
| 10 | `ledger_reconciliation` | `no_loop_control` | `regression_injected` | **False** | 10 | 1 | 32.65 | `FAILED` | `Vis:T Reg:F Hid:F` |
| 11 | `rate_limiter_invariants` | `full_loop` | `regression_injected` | **False** | 6 | 2 | 154.42 | `no_progress_rolled_back` | `Vis:F Reg:F Hid:F` |
| 12 | `rate_limiter_invariants` | `no_loop_control` | `regression_injected` | **True** | 8 | 1 | 25.98 | `SUCCESS` | `Vis:T Reg:T Hid:T` |

### 2.2 Deep Dive: False Convergence in Trial 10 (Substantiated)
In Trial 10 (`ledger_reconciliation`, `no_loop_control`, `regression_injected`):
- The baseline agent ran 10 micro-turns.
- Patch Summary: *"Fixed the reconcile function in src/ledger/reconciler.py. The defect was using only tx.id as the deduplication key... Changed key to (tx.id, tx.source)... Tests now pass."*
- Behavior: The agent ran `tests/test_reconciler_visible.py`, observed 2/2 tests passing, and halted. It was blind to the broken default fee in `src/ledger/models.py`.
- Evaluator Output: `visible_tests_passed: True`, `regression_tests_passed: False`, `hidden_tests_passed: False`.
- **Verdict**: The claim of **false convergence** is **100% substantiated for Trial 10**.

### 2.3 Deep Dive: Full-Loop Recovery in Trial 9 (Substantiated)
In Trial 9 (`ledger_reconciliation`, `full_loop`, `regression_injected`):
- Iteration 1: Agent fixed `reconciler.py`.
- Stage `RE-EVALUATE`: G2 Regression Gate intercepted the failure in `test_existing_ledger_api.py`.
- G5.1 swapped the target to `test_existing_ledger_api.py` and alerted the model.
- Iteration 2: Agent fixed the default fee in `models.py` from `5.0` to `0.0`.
- Stage `RE-EVALUATE`: Dual verification confirmed both visible and regression suites passed.
- **Verdict**: Full-Loop recovery via G2 and G5.1 is **100% substantiated for Trial 9**.

### 2.4 Deep Dive: Trial 11 vs Trial 12 (The Omitted Counter-Evidence)
In Trial 11 (`rate_limiter_invariants`, `full_loop`, `regression_injected`):
- The Full-Loop agent failed to repair the rate limiter defects within its turn allotment in iteration 1.
- In iteration 2, it made no further progress, tripping `no_progress_triggered: true`.
- Final status: `no_progress_rolled_back`. All tests failed (`Vis:False Reg:False Hid:False`).
- **G2 and G5.1 never activated** (`regression_detected: false`, `target_swapped: false`).

In Trial 12 (`rate_limiter_invariants`, `no_loop_control`, `regression_injected`):
- The unguided agent ran 8 micro-turns.
- Patch Summary verbatim:
  > *"Fixed two bugs in the rate limiter:\n1. In `src/ratelimit/bucket.py`: Changed line 5 to use the passed `window_size` parameter instead of hardcoding it to `1.0`\n2. In `src/ratelimit/limiter.py`: Changed the comparison from `>` to `>=` on line 16 so requests are blocked when count reaches max_requests (not just when exceeding it)\nBoth tests now pass: `test_rate_limit_blocking` and `test_rate_limit_expiry`"*
- Evaluator Output: `visible_tests_passed: True`, `regression_tests_passed: True`, `hidden_tests_passed: True`. Success: `True`.
- **Verdict**: Calling Trial 12 "passed by luck" is an unscientific dismissal. The model inspected the code, detected the hardcoded `1.0` bug injected in `bucket.py`, corrected it, fixed the limiter threshold, and achieved verified correctness.

### 2.5 Summary of Causal Ablation Regime 2
- Full-Loop Success Rate: **1/2 (50.0%)**
- No-Loop Control Success Rate: **1/2 (50.0%)**
- Causal Advantage Delta: **0.0%**
- **Conclusion**: Closed-loop governance did NOT achieve a positive causal advantage delta over baseline control on regression-injected tasks in this dataset. It prevented bad commits when failing (clean rollback), but did not increase verified resolution rate.

---

## 3. Empirical Audit: Adaptive Context Handover (`benchmarks/handover_ablation_experiment_report.json`)

The handover ablation battery evaluated $N=4$ trials testing whether dynamic micro-turn budget reallocation and file context preservation improved recovery.

### 3.1 Raw Performance & Resource Consumption

| Condition | Task ID | Success | Iterations | Micro-Turns | Wall Time (s) | Final Status |
|:---|:---|:---:|:---:|:---:|:---:|:---|
| **Control** | `rate_limiter_invariants` | True | 1 | 10 | 110.39 | `converged_accepted` |
| **Treatment** | `rate_limiter_invariants` | True | 2 | 25 | 229.00 | `converged_accepted` |
| **Control** | `ledger_reconciliation` | True | 2 | 15 | 182.99 | `converged_accepted` |
| **Treatment** | `ledger_reconciliation` | True | 2 | 17 | 178.87 | `converged_accepted` |

### 3.2 Aggregate Metrics & Efficiency Penalties
- Control Success Rate: **100.0% (2/2)**
- Treatment Success Rate: **100.0% (2/2)**
- **Recovery Advantage Delta**: **0.0%**
- **Turn Inflation**: Control consumed 25 total micro-turns; Treatment consumed 42 total micro-turns (**+68.0% overhead**, +17 turns).
- **Wall-Clock Inflation**: Control consumed 293.38s; Treatment consumed 407.87s (**+39.0% overhead**, +114.49s).

### 3.3 Epistemological Classification Violation
In Section 6.1, the deliverable defines:
- **3. EXPERIMENTALLY DEMONSTRATED**: *"Statistically observed producing positive causal deltas in internal controlled ablations holding model, tools, and budget constant."*
- **4. EXPERIMENTAL**: *"Implemented, operational in code, and passing unit tests, but currently lacking statistically significant advantage delta over matched controls (Δ = 0.0%)."*

Because the observed delta in `benchmarks/handover_ablation_experiment_report.json` is **0.0%**, G5.2 strictly meets the definition of **EXPERIMENTAL**, not **EXPERIMENTALLY DEMONSTRATED**. Promoting G5.2 violates the report's own rubric.

---

## 4. Empirical Audit: Repository Benchmark & Metric Conflation (`benchmarks/evaluation_experiment_report.json`)

Section 5.3 of the deliverable claims:
> *"Loop Engineering achieved 1-iteration convergence on tasks that required up to 9 iterations for baseline unguided agents."*

### 4.1 Root Cause in `benchmarks/repo_benchmark.py`
Inspection of `benchmarks/repo_benchmark.py` reveals how metrics were logged:
- **For `loop_engineering`** (line 663):
  `iters_used = state.get("iteration", 1)`  
  This records the **macro-iteration** of the LangGraph StateGraph (which has `max_iterations = 3`). Within each macro-iteration, the `IMPLEMENT` stage runs a CodeAct agent that executes multiple micro-turns.
- **For `baseline_control`** (lines 613, 671):
  `success, iters_used, patch_summary = run_baseline_control_agent(...)`  
  where `res.iterations` from `CodeActCodingAgent` is the count of **micro-turns** (tool calls, up to `max_turns = 10`).

### 4.2 Raw Time and Metric Comparison

| Architecture Mode | Task ID | "Iterations" Logged | Actual Meaning | Wall Time (s) | Success |
|:---|:---|:---:|:---|:---:|:---:|
| `loop_engineering` | `ledger_reconciliation` | 1 | 1 Macro-Iteration | 62.23 | True |
| `baseline_control` | `ledger_reconciliation` | 9 | 9 Micro-Turns | 29.05 | True |
| `loop_engineering` | `rate_limiter_invariants` | 1 | 1 Macro-Iteration | 74.25 | True |
| `baseline_control` | `rate_limiter_invariants` | 10 | 10 Micro-Turns | 28.93 | True |
| `loop_engineering` | `tiered_lru_cache` | 1 | 1 Macro-Iteration | 66.17 | True |
| `baseline_control` | `tiered_lru_cache` | 10 | 10 Micro-Turns | 27.94 | True |
| `loop_engineering` | `stream_watermark_aggregator` | 1 | 1 Macro-Iteration | 127.95 | True |
| `baseline_control` | `stream_watermark_aggregator` | 9 | 9 Micro-Turns | 30.28 | True |

Notice that 1 macro-iteration of `loop_engineering` took **62s to 128s**, while 9-10 micro-turns of `baseline_control` took only **28s to 30s**. Conflating 1 macro-iteration with 9 micro-turns creates a misleading impression of order-of-magnitude efficiency gains where none exist.

---

## 5. Empirical Audit: OpenHands Spike & Safety Gate Integrity (`benchmarks/openhands_spike_report.json`)

### 5.1 Verification Results
- **OpenHands Worker**: Failed (`overall_success: false`, `final_status: no_progress_rolled_back`, `rolled_back: true`). Modified files included test files (`tests/test_existing_ledger_api.py`, `tests/test_reconciler_visible.py`).
- **Custom Baseline Worker**: Succeeded (`overall_success: true`, `final_status: converged_accepted`, `iterations: 1`, duration: 114.52s).
- **Safety Gate Verification**: G4 stack trace fingerprinting and terminal rollback operated cleanly as claimed.

### 5.2 Internal Inconsistency Regarding G3
- Section 1.5 (line 23): Lists G3 as **STRONGLY SUPPORTED**.
- Section 6.2 (line 496): Lists G3 as **PROVEN**.
- **Assessment**: In addition to Challenger 1's empirical proof that G3 can be bypassed by directory test targets, test file deletion, and unhashed regression targets, the deliverable contradicts itself internally on G3's classification.

---

## 6. Challenge Verdict & Required Remediations

### Adversarial Verdict: **CHALLENGE_FAILED**
The deliverable cannot be approved in its present form because:
1. It claims 100% verified correctness for Full-Loop under regression stress when raw data shows 50.0% (Trial 11 failed).
2. It claims catastrophic false convergence for baseline unguided agents while concealing Trial 12 (where baseline unguided succeeded on both defects).
3. It violates its own epistemological taxonomy by classifying G5.2 as EXPERIMENTALLY DEMONSTRATED despite an observed advantage delta of Δ = 0.0%.
4. It compares macro-iterations to micro-turns in Section 5.3, exaggerating convergence differences.

### Required Revisions for Authoritative Deliverable:
1. **Correct Section 1.4**: Accurately report that under regression stress, Full-Loop achieved 50.0% (1/2) and No-Loop achieved 50.0% (1/2). Note that Full-Loop demonstrated clean safety rollback on failure (Trial 11) and recovered via G2/G5.1 on Trial 9, whereas No-Loop exhibited false convergence on Trial 10 and successful multi-defect resolution on Trial 12.
2. **Reclassify G5.2**: Change G5.2 from **EXPERIMENTALLY DEMONSTRATED** to **EXPERIMENTAL** in Table 6.2 and Section 1, explicitly citing the Δ = 0.0% delta and efficiency overhead.
3. **Harmonize G3 Classification**: Resolve the contradiction between Section 1 (STRONGLY SUPPORTED) and Section 6.2 (PROVEN). Given the vulnerabilities proven by Challenger 1, G3 should be classified as **EXPERIMENTAL / VULNERABLE**.
4. **Clarify Iteration Metrics in Section 5.3**: Explicitly distinguish macro-iterations (StateGraph cycles) from micro-turns (tool calls), and report wall-clock latencies alongside turn counts.
