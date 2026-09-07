# Comprehensive Survey Report: Benchmark Harness, Task Suite & Causal Experimentation

**Explorer**: Survey Explorer 3 (Benchmark Harness & Causal Experimentation)  
**Date**: 2026-09-07  
**Working Directory**: C:\Users\Arsh\market-intelligence-os\.agents\teamwork_preview_explorer_survey_3  
**Repository**: C:\Users\Arsh\market-intelligence-os  

---

## Executive Summary

This investigation surveys the autonomous coding test runners, benchmark harnesses, task datasets, model configurations, 25-turn budget enforcement, causal control vs. treatment conditions, and reliability metric extractors in market-intelligence-os.

Key empirical determinations include:
1. **Harnesses & Evaluators**: The codebase contains four primary benchmark harnesses (enchmarks/repo_benchmark.py, enchmarks/causal_ablation_experiment.py, enchmarks/handover_ablation_experiment.py, and enchmarks/coding_benchmark.py). All four evaluators were validated empirically using alidate_evaluator_correctness() and confirmed **100% sound** (failing on defective code, passing regression tests on baseline, and failing hidden invariant tests).
2. **Task Battery**: Four canonical multi-file repository tasks are available (ledger_reconciliation, 
ate_limiter_invariants, 	iered_lru_cache, stream_watermark_aggregator), each equipped with a 3-tier test structure (Tier 1: Visible, Tier 2: Untouched Regression, Tier 3: Quarantine Hidden Invariant) across two experimental regimes (symptom_diagnostic and 
egression_injected).
3. **Control vs. Treatment Isolation**: An exact matched pair holding model (combo/coder routing to kiro/qwen3-coder-next), task distribution, tool bindings, and budget ceiling (25 turns) strictly constant requires contrasting a bare unguided CodeActCodingAgent(max_turns=25) against the 8-stage uild_coding_loop(max_total_micro_turns=25) with G1-G5 active.
4. **Reliability Metrics**: 14+ core reliability metrics are formalized across capability, stability, regression resilience, rollback safety, and efficiency. However, previous trial telemetry was collected across single-shot runs (N=1), leaving repeated-run consistency (pass^k) unaggregated across repeated seeds.
5. **Critical Gaps & Remedies**: Identified a model routing key mismatch (combo/coder causing 401 fallback to primary vs. coder), unequal micro-turn ceilings in prior causal ablation scripts (15 turns in control vs. 30 in treatment), absence of multi-run pass^k statistical looping, and missing test suite integration in 	ests/.

---

## 1. Test & Benchmark Harnesses Inventory

| Harness File | Invocation Command | Target Objective | Output Telemetry File |
|---|---|---|---|
| enchmarks/repo_benchmark.py | .venv\Scripts\python.exe -m benchmarks.repo_benchmark | Scientific 4-phase benchmark: Evaluator validation, Loop vs. Baseline Control, Model comparison, Ablation | enchmarks/evaluation_experiment_report.json |
| enchmarks/causal_ablation_experiment.py | .venv\Scripts\python.exe -m benchmarks.causal_ablation_experiment | Controlled Causal Ablation: Full-Loop vs. No-Loop Control under Symptom and Regression regimes | enchmarks/causal_ablation_experiment_report.json |
| enchmarks/handover_ablation_experiment.py | .venv\Scripts\python.exe -m benchmarks.handover_ablation_experiment | Causal ablation of Adaptive Turn-Budget Handover & Context Preservation (G5.2) vs. Static Control | enchmarks/handover_ablation_experiment_report.json |
| enchmarks/coding_benchmark.py | .venv\Scripts\python.exe -m benchmarks.coding_benchmark | Extended battery testing multi-file ledger and rate limiter self-repair | enchmarks/latest_benchmark_report.json |
| scripts/test_loop_engineering_enhancements.py | .venv\Scripts\python.exe -m scripts.test_loop_engineering_enhancements | Discrete verification of G1 (Ledger), G2 (Regression Gate), G3 (Anti-Gaming Hash), G4 (Repairability Gate) | Console stdout (Pass 4/4) |
| scripts/test_remediation_target_swap.py | .venv\Scripts\python.exe -m scripts.test_remediation_target_swap | Discrete & E2E verification of G5.1 Remediation Target Swapping | Console stdout (Pass 3/3) |
| scripts/openhands_spike_evaluation.py | .venv\Scripts\python.exe -m scripts.openhands_spike_evaluation | Spike comparison of OpenHands runtime vs. Custom CodeAct worker | enchmarks/openhands_spike_report.json |

### Detailed Harness Architecture

#### A. enchmarks/repo_benchmark.py
- **Lines 551-590 (alidate_evaluator_correctness)**:
  Performs pre-flight soundness checks across all tasks in TASK_REGISTRY. Verifies that untouched code fails visible tests, passes baseline regression tests, and fails hidden tests.
- **Lines 620-771 (execute_benchmark_task)**:
  Unified runner supporting modes 'loop_engineering', 'baseline_control', and 'ablation_*'.
  Initializes an isolated Git repository in a temporary directory, commits the baseline, runs the agent/loop, and then executes strict 3-tier post-run evaluation.
- **Lines 773-868 (
un_full_evaluation_experiment)**:
  Orchestrates Phase 2 (Evaluator Validation), Phase 3 & 5 (Loop vs. Baseline), Phase 4 (Model comparison), and Phase 6 (Ablations).

#### B. enchmarks/causal_ablation_experiment.py
- **Lines 146-320 (
un_single_trial)**:
  Direct pairwise comparison of ull_loop (via uild_coding_loop()) vs. 
o_loop_control (via CodeActCodingAgent).
- Evaluates across two distinct regimes:
  - symptom_diagnostic (Tasks 1 to 4): Instructions state symptoms without leaking solution or file paths.
  - 
egression_injected (Tasks 1 & 2): Seeds a realistic flaw into an untouched file prior to the agent run.
- Telemetry records visible, regression, and hidden test outcomes, macro-iterations, agent micro-turns, rollbacks, and ledger summaries.

#### C. enchmarks/handover_ablation_experiment.py
- **Lines 83-208 (
un_handover_trial)**:
  Isolates G5.2 Adaptive Micro-Turn Budget Handover & Context Preservation.
  Enforces an overall micro-turn ceiling of 25 turns (max_total_micro_turns=25).
  Evaluates recovery from worker budget exhaustion across iterations.

---

## 2. Task Battery & Dataset Distribution

The repository implements four canonical multi-file tasks in TASK_REGISTRY (enchmarks/repo_benchmark.py lines 70-545). None of the tasks are trivial single-file toy problems; each requires reasoning across interdependent modules.

### Task Catalog

| Task ID | Domain | Interdependent Source Files | Defect Description | Invariant & Regression Targets |
|---|---|---|---|---|
| ledger_reconciliation | Financial Ledger Engine | src/ledger/models.py<br>src/ledger/fx.py<br>src/ledger/reconciler.py | 1. convert_to_usd in x.py ignores 	x.fee.<br>2. 
econcile in 
econciler.py deduplicates on 	x.id instead of (tx.source, tx.id). | **Visible**: 	est_reconciler_visible.py<br>**Regression**: 	est_existing_ledger_api.py (Transaction default fee=0.0)<br>**Hidden**: 	est_reconciler_hidden.py (zero-amount fee, cross-source true duplicate) |
| 
ate_limiter_invariants | High-Throughput Token Bucket & Limiter | src/ratelimit/bucket.py<br>src/ratelimit/limiter.py | 1. prune() in ucket.py uses < cutoff (inverts pruning, keeping expired timestamps).<br>2. llow() in limiter.py checks count > max_requests instead of >=. | **Visible**: 	est_limiter_visible.py<br>**Regression**: 	est_existing_ratelimit_api.py (window initialization)<br>**Hidden**: 	est_limiter_hidden.py (multi-tenant client isolation, exact boundary) |
| 	iered_lru_cache | Tiered Cache with Temporal Invariants | src/cache/lru.py<br>src/cache/tiered_cache.py | 1. get() in lru.py fails to call move_to_end on access.<br>2. get() in 	iered_cache.py checks current < ttls[key] (inverted TTL expiration). | **Visible**: 	est_cache_visible.py<br>**Regression**: 	est_existing_cache_api.py (cache miss)<br>**Hidden**: 	est_cache_hidden.py (TTL overwrite updates expiry, capacity 1 eviction) |
| stream_watermark_aggregator | Streaming Window Aggregator | src/stream/watermark.py<br>src/stream/window.py | 1. update() in watermark.py allows non-monotonic watermark regression.<br>2. dd_event() in window.py does not check or reject late events. | **Visible**: 	est_stream_visible.py<br>**Regression**: 	est_existing_stream_api.py (window indexing arithmetic)<br>**Hidden**: 	est_stream_hidden.py (late events dropped from sum) |

### 3-Tier Independent Evaluator Structure
For each task:
1. **Tier 1 (Visible Test)**: Available in the repository workspace during agent execution. The agent can run pytest <visible_test>.
2. **Tier 2 (Untouched Regression Test)**: Existing tests covering baseline contracts (e.g. default constructor parameters, miss behaviors). Must remain passing post-mutation.
3. **Tier 3 (Quarantine Hidden Invariant Test)**: Stored in memory as a string in 
epo_benchmark.py. Written into the workspace **strictly after the agent run concludes**. Proves that the fix is general, not overfitted or gamed.

### Evaluator Soundness Verification Results
Execution of alidate_evaluator_correctness() confirmed:
- ll_evaluators_sound: **True** (4/4 tasks sound)
- For every task:
  - Initial visible test fails: **True**
  - Baseline regression test passes: **True**
  - Initial hidden test fails: **True**

---

## 3. Matched Control vs. Treatment Causal Experiment Design

To rigorously measure the causal effect of Loop Engineering closed-loop controls, all confounders must be held strictly constant.

### Experimental Controls

| Dimension | Control Condition (Baseline Agent) | Treatment Condition (Loop Engineering Agent) | Isolation Rigor |
|---|---|---|---|
| **Model** | combo/coder (kiro/qwen3-coder-next) | combo/coder (kiro/qwen3-coder-next) | Strictly identical weights, gateway URL, temperature (0.0), and fallback list |
| **Tool Set** | 
ead_file, write_file, patch_file, 
un_command, 
un_tests, inish | Identical tools exposed to worker | Strictly identical tool definitions and execution sandbox |
| **Task Set** | All 4 canonical tasks | All 4 canonical tasks | Identical initial Git repository commits |
| **Prompt Regime** | Symptom-Only and Injected-Regression | Symptom-Only and Injected-Regression | Identical initial prompt text |
| **Budget Ceiling** | Exactly 25 micro-turns total | Exactly 25 micro-turns total (cumulative across macro iterations) | Constant total action-observation budget |
| **Governance Architecture** | **Unguided Bare CodeAct**: Direct conversation loop with model. No macro-stages, no ledger, no regression gate, no anti-gaming hash, no automated rollback. | **8-Stage Closed-Loop StateGraph**: DEFINE -> PLAN -> IMPLEMENT -> TEST -> VERIFY -> FAILURE -> REFINE -> RE-EVALUATE. Guards G1-G5 active. | **Pure causal treatment variable: Closed-Loop Governance** |

### Budget Ceiling Enforcement Mechanism

#### In Control (CodeActCodingAgent):
- max_turns = 25.
- Turns increment on each model action (	urn_idx in range(1, self.max_turns + 1) in src/coding_agent/agent.py:189).
- If 25 turns are reached without a valid inish action, terminates with BudgetExhausted.

#### In Treatment (uild_coding_loop):
- max_total_micro_turns = 25 in CodingState.
- In implement_stage (src/loops/coding_loop.py:238-252):
  `python
  max_total = state.get('max_total_micro_turns', 25)
  used_so_far = state.get('total_micro_turns', 0)
  remaining_budget = max(1, max_total - used_so_far)
  stage_budget = min(remaining_budget, 10 if current_iter == 1 else 15)
  `
- Cumulative micro-turns are recorded in state['total_micro_turns'] and persisted across iterations.
- If 	otal_micro_turns >= 25, remaining budget collapses to 0, terminating the loop and triggering deterministic rollback if unverified.

---

## 4. Multi-Metric Extraction & Tracking Framework

The 14+ core reliability metrics are structured into five evaluation dimensions:

### Matrix of 14+ Core Reliability Metrics

| # | Metric Name | Mathematical / Operational Definition | Extraction Source |
|---|---|---|---|
| **M1** | **Independently Verified Correctness** | VisiblePassed and RegressionPassed and HiddenPassed and not RolledBack | Post-run independent test execution |
| **M2** | **First-Attempt Success Rate (pass@1)** | Fraction of tasks passing all 3 tiers on macro-iteration 1 without retries | iterations_used == 1 and strictly_successful |
| **M3** | **Repeated-Run Reliability (pass^k)** | Product of successes over k consecutive runs: all k runs pass | Multi-run trial aggregation (k >= 3) |
| **M4** | **Repair Success Rate** | Fraction of failing trials successfully brought to passing state | 
epair_success flag in trial result |
| **M5** | **Regression Rate** | Fraction of trials where agent mutations broke untouched baseline tests | 
ot RegressionPassed |
| **M6** | **Rollback Rate** | Frequency of automated Git rollback triggering to protect workspace baseline | status in rollback_statuses |
| **M7** | **Hidden Invariant Violations** | Rate of superficial patches passing visible tests but failing hidden invariants | VisiblePassed and not HiddenPassed |
| **M8** | **Repeated Failure Signatures** | Consecutive iterations producing identical failure SHA-256 fingerprints | sig_history[i] == sig_history[i-1] |
| **M9** | **No-Progress Circuit Breaker Triggers** | Frequency of G1/G4 tripping to abort unrecoverable loops | guard_events['no_progress_triggered'] |
| **M10**| **Worker Budget Exhaustion** | Rate of reaching the micro-turn ceiling before convergence | worker_budget_exhaustion flag |
| **M11**| **Unnecessary Repair / Blast Radius** | Modifications to files/APIs outside the scope causing collateral breakage | 	est_regime == 'regression' and RegressionViolated |
| **M12**| **Macro-Iteration Overhead** | Number of macro-loop iterations traversed (1 to 3) | macro_iterations from loop state |
| **M13**| **Micro-Turn Consumption** | Total tool invocation turns taken by worker agent (<= 25) | 	otal_micro_turns |
| **M14**| **Wall-Clock Latency & Stage Overhead**| Total elapsed wall-clock duration and per-stage latency | StageTimer in loop_ledger.py |
| **M15**| **Test Anti-Gaming Detection Rate** | Frequency of catching agent test modifications via SHA-256 hash | 	est_integrity_violation |
| **M16**| **Handover Recovery Rate** | Success rate of iterations that began after prior worker budget exhaustion | 
ecovery_after_budget_exhaustion |

### Telemetry Ledger Implementation (G1)
Every stage transition in coding_loop.py records a structured ledger entry via src/loops/loop_ledger.py:
- 	imestamp: UTC ISO-8601 string
- stage: Current stage (DEFINE, PLAN, IMPLEMENT, TEST, VERIFY, FAILURE, REFINE, RE-EVALUATE, ROLLBACK_AND_STOP)
- iteration: Current macro-iteration count
- status: Machine-readable state delta
- duration_seconds: Measured via StageTimer context manager
- guard_events: Dictionary tracking triggers for rollback, no-progress, test tampering, regression, target swap, and unrepairability.

---

## 5. Prior Empirical Findings & Evidence Base

Analysis of existing benchmark reports in enchmarks/ reveals critical empirical insights:

### 1. causal_ablation_experiment_report.json (12 Trials)
- **Full-Loop Success Rate**: 83.3% (5/6)
- **No-Loop Control Success Rate**: 83.3% (5/6)
- **Causal Advantage Delta**: 0.0%
- **Crucial Diagnostic Finding**:
  - In Trial 10 (ledger_reconciliation with 
egression_injected):
    - **Full-Loop**: PASSED (Visible: True, Regression: True, Hidden: True). G2 detected the regression, G5.1 swapped the active target to 	est_existing_ledger_api.py, and the agent successfully repaired the regression.
    - **No-Loop Control**: FAILED (Visible: True, Regression: False, Hidden: False). The unguided agent fixed the visible test but was oblivious to the broken models.py regression!
  - In Trial 11 (
ate_limiter_invariants with 
egression_injected):
    - **Full-Loop**: FAILED with 
o_progress_rolled_back because the worker exhausted its single-stage 10-turn budget without convergence, and no handover context was carried forward.
    - **No-Loop Control**: PASSED in 8 turns.

### 2. handover_ablation_experiment_report.json (4 Trials)
- Tested adaptive budget handover and context preservation on the failure mode observed in Trial 11.
- Both Control and Treatment achieved 100% verified correctness on the injected tasks because the handover mechanism permitted carrying forward discovered file paths and residual turns, avoiding redundant exploration.

---

## 6. Identified Gaps & Required Extensions

| Gap ID | Area | Current Limitation | Concrete Remediation Specification |
|---|---|---|---|
| **GAP-1** | **Model Routing Key Inconsistency** | config/model_registry.yaml indexes roles by 'coder', but scripts pass model_name='combo/coder'. This causes 
outer.get_role_config('combo/coder') to synthesize combo/combo/coder, fail with HTTP 401 on OmniRoute, and fall back to primary: kiro/qwen3-coder-next. | In agent and benchmark runners, consistently pass model_role='coder' or map 'combo/coder' -> 'coder' in ModelRouter.get_role_config(). |
| **GAP-2** | **Budget Parity Discrepancy in Causal Runner** | In enchmarks/causal_ablation_experiment.py, 
o_loop_control ran with max_turns=15 while ull_loop had up to 3 macro-iterations of 10 turns (potential 30 turns). Furthermore, gent_micro_turns was approximated as macro_iterations * 3 rather than measured. | Standardize max_total_micro_turns=25 across both conditions. Track exact micro-turns from CodeActCodingAgent.iterations in both conditions. |
| **GAP-3** | **Absence of Repeated-Run (pass^k) Evaluation** | All existing runners execute N=1 trial per task/condition. LLM generation variance and pass consistency across repeated seeds are not measured. | Add a --repeats 3 loop in the runner to compute pass@k and pass^k = product of successes over k runs per task condition. |
| **GAP-4** | **Empty 	ests/ Directory** | The repository root has an empty 	ests/ directory; test suites currently reside only in scripts/ or embedded in enchmarks/repo_benchmark.py. | Standardize opaque-box unit and integration tests into 	ests/ so pytest tests/ can be run natively by standard CI/auditing tools. |
| **GAP-5** | **Unified Execution Entry Point** | Running causal experiments requires invoking individual scripts with manual parameters. | Construct a unified causal experiment runner script (
un_causal_experiment.py) with CLI flags (--regime, --ceiling 25, --repeats 3, --model coder). |

