# Comprehensive Survey Report: Repository Architecture, Safety Gates, & Empirical Benchmark Inventory

**Author**: Survey Explorer 1 (Repository Architecture & Safety Gates)  
**Date**: 2026-09-07  
**Workspace**: `C:\Users\Arsh\market-intelligence-os`  
**Target Directives**: R1 Capability Classification & Repository State Reconstruction

---

## 1. Executive Summary

This investigation conducted a complete, forensic inspection of the repository at `C:\Users\Arsh\market-intelligence-os`. The repository exhibits a dual architectural nature:
1. **Application Layer (Market & Product Intelligence OS)**: Outlined in `ARCHITECTURE.md` as an "Evidence-First Market & Product Intelligence OS" with a 29-stage locked pipeline. Most domain modules in `src/` (`src/analysis`, `src/competitive`, `src/critics`, `src/decision`, `src/entities`, `src/evaluation`, `src/evidence`, `src/extraction`, `src/gap`, `src/memory`, `src/opportunity`, `src/product`, `src/reasoning`, `src/reporting`, `src/synthesis`, `src/verification`) exist primarily as architectural stubs (`__init__.py`), with active implementation concentrated in `src/application/research/` (adaptive search, claim extraction, document chunking, evidence assessment) and `src/core/gatekeeper.py`.
2. **Loop Engineering Autonomous Coding Agent Subsystem**: Outlined in `AGENTS.md` and implemented in `src/loops/coding_loop.py`, `src/loops/loop_ledger.py`, `src/coding_agent/*`, `benchmarks/*`, and `scripts/*`. This is an advanced, production-grade, closed-loop governor implementing an 8-stage state machine (`DEFINE` -> `PLAN` -> `IMPLEMENT` -> `TEST` -> `VERIFY` -> `FAILURE` -> `REFINE` -> `RE-EVALUATE`) with Git rollback checkpoints, multi-tier independent evaluators, model routing via OmniRoute (`http://localhost:20128/v1`), and formal safety gates G1 through G5.2.

All safety gates G1 through G5.2 possess complete, working code implementations in `src/` and dedicated deterministic verification suites in `scripts/`. G6 ("Multi-File Patch Isolation") is currently **speculative/unimplemented**. Multiple causal ablation batteries and benchmark reports exist in `benchmarks/` recording trials across controlled treatments.

---

## 2. Repository Architecture & Design Documentation

### 2.1 ARCHITECTURE.md
- **Declared Baseline**: "Locked Baseline" for Evidence-First Market & Product Intelligence OS.
- **Core Principles**: Evidence before conclusions (Rule 1-2); Loop Engineering controls research iteration (Rule 3); Module and model replaceability (Rules 4, 7); Zero silent bypass of verification (Rule 8); Support for critique and repair loops (Rule 9).
- **Pipeline Flow**: 29 sequential processing nodes spanning Research Gatekeeper -> Master Loop Engineering -> Research Planning -> Task Graph -> Adaptive Search -> Source Discovery -> Extraction -> Evidence Engine/Graph -> Entity Resolution -> Fact Verification -> Research Memory -> Market Analysis -> Competitive Matrix -> Product Understanding -> Gap Engine -> Customer Pain -> Opportunity Engine -> Prioritization -> Product Decision -> Reasoning -> Decision Critic -> Synthesis -> Product Roadmap -> Research Critic -> Quality & Benchmark Engine -> Final Intelligence.
- **9 Required Loop Types**: Master Loop, Discovery Loop, Evidence Loop, Reasoning Loop, Completeness Loop, Product Gap Loop, Decision Loop, Quality Loop, Benchmark Loop.

### 2.2 AGENTS.md
- **Loop Engineering Contract**: Enforces an 8-stage state machine for autonomous code modifications:
  $$\text{DEFINE} \to \text{PLAN} \to \text{IMPLEMENT} \to \text{TEST} \to \text{VERIFY} \to \text{FAILURE} \to \text{REFINE} \to \text{RE-EVALUATE}$$
- **Model Gateway (OmniRoute)**: Base URL `http://localhost:20128/v1` with task-specific model combo roles:
  - `combo/planner`: Reasoning & boundary conditions
  - `combo/coder`: Patch synthesis
  - `combo/debugger`: Failure diagnosis & root-cause attribution
  - `combo/reviewer`: Diff review & regression gate
  - `combo/fast`: Token triage & quick edits
- **Objective Verification Gate**: Prohibits self-certification by model output; enforces 100% passing tests and zero regressions.
- **Security & Workspace Isolation**: Mandatory Git checkpoints per modification cycle for instant rollback; path confinement strictly within workspace; protection of `.env`, secrets, and SQLite files.

### 2.3 Configuration & Model Routing
- **File**: `config/model_registry.yaml` and `src/core/model_router.py`.
- **Gateway**: `http://127.0.0.1:20128/v1`, API key `sk-96ac38503125b798-733820-5d37878f`.
- **Adaptive Fallback**: `ModelRouter.execute_with_fallback(role, messages)` dispatches requests to primary models (`kiro/claude-sonnet-4.5`, `kiro/qwen3-coder-next`, `kiro/claude-haiku-4.5`) with automated fallback to local Ollama weights (`ollama/qwen3:4b-instruct-2507-q4_K_M`).

---

## 3. Deep-Dive Inspection of Safety Gates (G1 - G6)

The safety gates and loop engineering components are located primarily in `src/loops/coding_loop.py` and `src/loops/loop_ledger.py`. Below is the complete structural and operational breakdown.

### G1: Evidence & Provenance Ledger
- **Source Files**: `src/loops/loop_ledger.py` (lines 1–134), `src/loops/coding_loop.py` (lines 50–51, 140–152, 201–209, 318–332, 353–361, 413–423, 468–477, 510–517, 596–605, 650–658).
- **Test File**: `scripts/test_loop_engineering_enhancements.py::test_g1_evidence_ledger` (lines 20–65).
- **Mechanism**:
  - `CodingState['ledger_entries']` stores an append-only, immutable audit trail of every stage transition.
  - Telemetry per entry includes: UTC ISO 8601 timestamp (`datetime.now(timezone.utc).isoformat()`), `stage`, `iteration`, `status`, execution duration via monotonic timer (`StageTimer`), test pass/fail flags, failure classifications, failure signatures, guard triggers (`no_progress`, `rolled_back`, `test_integrity_violation`, `regression_detected`, `target_swapped`, `unrepairable`), truncated patch summaries, and attribution text.
  - `summarize_ledger(entries)` generates a compact report summarizing `total_entries`, `stages_visited`, `total_duration_seconds`, `final_status`, and a `guard_events` map.
- **Operational Status**: Fully operational in code, 100% test pass rate, embedded in all benchmark reports.

### G2: Regression & Invariant Protection Gate
- **Source Files**: `src/loops/coding_loop.py` (`reevaluate_stage`, lines 52–54, 528–622; `check_reevaluate_decision`, lines 687–697; `rollback_and_stop_stage`, lines 624–665).
- **Test File**: `scripts/test_loop_engineering_enhancements.py::test_g2_regression_gate` (lines 67–108).
- **Mechanism**:
  - In `reevaluate_stage` (Stage 08), after visible tests pass in `verify_stage`, the loop executes `run_test_suite` on the untouched `regression_test_target`.
  - If regression fails: flags `regression_detected = True`, logs failure output, and updates status to `"regression_detected"`.
  - Decision Logic (`check_reevaluate_decision`):
    - If `regression_detected` and `iteration < max_iterations`: routes to `failure` -> `refine` -> `implement` for self-repair.
    - If `regression_detected` and `iteration >= max_iterations`: routes to `rollback_and_stop` with final status `"regression_rolled_back"`, triggering `git_rollback` to initial checkpoint.
  - Dual Verification: If regression target passes, also re-evaluates `original_test_target` to ensure fixing the regression didn't introduce collateral damage to visible specifications.
- **Operational Status**: Fully working in code, proven in deterministic unit tests, validated in causal ablation experiments.

### G3: Anti-Gaming / Test Integrity Guard
- **Source Files**: `src/loops/coding_loop.py` (`compute_test_file_hash`, lines 94–103; `define_stage`, lines 120–122; `verify_stage`, lines 382–393; `reevaluate_stage`, lines 584–589; `check_verification_decision`, lines 671–673).
- **Test File**: `scripts/test_loop_engineering_enhancements.py::test_g3_anti_gaming_guard` (lines 110–159).
- **Mechanism**:
  - In `define_stage`, computes SHA-256 hash of the test file: `compute_test_file_hash(workspace_root, test_target)`.
  - In `verify_stage`, re-hashes the test file and checks: `current_hash != init_hash`.
  - If a discrepancy is detected (i.e. the agent modified test assertions or deleted tests to pass):
    - Logs critical alert: `"SECURITY GUARD: TEST INTEGRITY VIOLATION DETECTED! Test file ... was modified by agent."`
    - Sets `test_integrity_violation = True` and status `"test_integrity_violation"`.
    - `check_verification_decision` intercepts the violation and routes immediately to `rollback_and_stop` (`"test_tampering_rolled_back"`), preventing any further retries or reward gaming.
  - Dynamically updates the protected baseline hash when remediation targets are swapped (G5.1).
- **Operational Status**: Fully operational in code, proven in deterministic unit tests with 0% false positives in benchmark trials.

### G4: Repairability / Unrepairable Failure Gate
- **Source Files**: `src/loops/coding_loop.py` (`classify_failure`, lines 80–92; `failure_stage`, lines 444–451; `compute_failure_signature`, lines 69–77; `verify_stage`, lines 401–411; `check_verification_decision`, lines 677–679).
- **Test File**: `scripts/test_loop_engineering_enhancements.py::test_g4_repairability_gate` (lines 161–205).
- **Mechanism**:
  - Classifies test failure outputs into a standard taxonomy: `SYNTAX_ERROR`, `IMPORT_ERROR`, `ASSERTION_ERROR`, `TIMEOUT`, `LOGIC_OR_RUNTIME_ERROR`.
  - Maintains `failure_classification_history`. If identical structural blockers occur consecutively (`len(history) >= 2 and history[-1] == history[-2]` for `IMPORT_ERROR` or `SYNTAX_ERROR`):
    - Flags `unrepairable = True`.
    - Logs warning: `"UNREPAIRABLE FAILURE PATTERN DETECTED: Repeated ... indicates structural blocker."`
    - `check_verification_decision` routes directly to `rollback_and_stop` (`"unrepairable_rolled_back"`).
  - Complemented by `compute_failure_signature`: Normalizes stack traces (stripping line numbers, memory hex addresses, timings) to compute SHA-256 fingerprint; detects consecutive repeating failures as `no_progress_detected = True` and aborts loop thrashing.
- **Operational Status**: Fully operational in code, proven in unit tests and observed aborting openhands thrashing in benchmark reports.

### G5.1: Remediation Target Swapping
- **Source Files**: `src/loops/coding_loop.py` (`reevaluate_stage`, lines 553–563, 564–581; `implement_stage`, lines 227–232).
- **Test File**: `scripts/test_remediation_target_swap.py` (lines 1–274, 3 discrete test functions).
- **Mechanism**:
  - In `reevaluate_stage`, if `regression_test_target` fails, the loop dynamically switches `test_target` to `regression_test_target` (`target_swapped = True`, preserving `original_test_target`).
  - In `implement_stage`, injects a high-priority directive:
    `"REGRESSION REMEDIATION ALERT: A regression was detected. Active test target has been dynamically swapped to '{test_target}'. Fix the regression while preserving original requirements."`
  - Dual Verification Convergence: Once the agent repairs the regression target, `reevaluate_stage` verifies BOTH the regression suite and the original visible test suite. Only when both pass does it restore `test_target = original_test_target` and exit to `converged_accepted`. If repairing the regression broke the original visible test, it swaps back to the visible test target.
- **Operational Status**: Fully operational in code, supported by 3 dedicated deterministic unit & integration tests, demonstrated in multi-iteration ablation runs (`causal_ablation_experiment_report.json`).

### G5.2: Adaptive Context Handover & Micro-Turn Budgeting
- **Source Files**: `src/coding_agent/agent.py` (`get_handover_summary`, lines 44–72); `src/loops/coding_loop.py` (`implement_stage`, lines 234–268).
- **Benchmark / Validation**: `benchmarks/handover_ablation_experiment.py`, `benchmarks/handover_ablation_experiment_report.json`.
- **Mechanism**:
  - `CodeActCodingAgent.get_handover_summary()` distills the agent's turn history into a compact, non-bloated JSON payload: `micro_turns_used`, `outcome`, `files_inspected`, `files_modified`, `tests_run`, `last_thought`.
  - Dynamic Turn Budgeting: Maintains a global ceiling (e.g. 25 micro-turns across macro-iterations). In normal iterations, grants `min(10, remaining)`. If the previous iteration terminated with `BudgetExhausted`, grants `min(15, remaining)` to give the agent sufficient headroom to finish patching.
  - Context Injection: Formats a structured `PREVIOUS ITERATION CONTEXT HANDOVER` section into the prompt, explicitly informing the worker which files have already been inspected and modified, eliminating exploratory turn waste.
  - Control vs Treatment: Under control (`adaptive_budget_enabled = False`), the agent gets a static 10-turn limit with zero context handover across iterations.
- **Operational Status**: Implemented and benchmarked in code. In N=4 ablation trials, both control and treatment achieved 100% success; causal advantage delta is currently 0.0% due to task simplicity.

### G6: Multi-File Patch Isolation
- **Source Files**: None.
- **Status**: **SPECULATIVE / UNIMPLEMENTED**. Mentioned as a conceptual candidate in `ORIGINAL_REQUEST.md`. No isolation staging or file-level patching sandbox exists in the codebase.

---

## 4. Prior Ablation Reports, Run Logs, & Benchmark Inventory

The repository contains extensive JSON reports of prior benchmark and ablation runs conducted on the codebase.

| Report File | Timestamp | Trials | Tasks Evaluated | Key Findings |
|---|---|---|---|---|
| `benchmarks/causal_ablation_experiment_report.json` | 2026-09-07 14:12:59 | 12 | 4 tasks (`ledger_reconciliation`, `rate_limiter_invariants`, `tiered_lru_cache`, `stream_watermark_aggregator`) across 2 regimes (`symptom_diagnostic`, `regression_injected`) | **Full Loop: 83.3% vs No-Loop: 83.3%** (Causal Delta: 0.0%). In `symptom_diagnostic`, both conditions solved all tasks in iteration 1. In `regression_injected`, on `ledger_reconciliation`, No-Loop falsely declared success (passed visible tests, broke regression & hidden: `Vis:True Reg:False Hid:False`), whereas Full Loop detected regression, swapped target, repaired it in iteration 2, and converged cleanly! On `rate_limiter_invariants`, Full Loop triggered `no_progress_rolled_back` on iteration 2 (preventing bad commit), while No-Loop passed by luck in single turn. |
| `benchmarks/handover_ablation_experiment_report.json` | 2026-09-07 14:53:49 | 4 | `rate_limiter_invariants`, `ledger_reconciliation` (regression-injected) | **Control: 100.0% vs Treatment: 100.0%** (Advantage Delta: 0.0%). Ceiling: 25 turns. Both control and treatment resolved both tasks. Treatment utilized adaptive budget (up to 25 micro-turns) and carried forward context without regressing invariants. |
| `benchmarks/evaluation_experiment_report.json` | 2026-09-05 18:40:32 | 13 | 4 repository benchmark tasks | **Overall Success Rate: 100.0%** across 13 runs. Evaluator validity verified sound across all 4 tasks (initial visible fails, baseline regression passes, initial hidden fails). Loop Engineering achieved 1-iteration convergence; baseline control required up to 9 iterations. |
| `benchmarks/openhands_spike_report.json` | 2026-09-05 22:32:57 | 2 | `ledger_reconciliation` | **OpenHands failed (0%) vs Custom CodeAct passed (100%)**. OpenHands worker modified unnecessary files (`tests/test_existing_ledger_api.py`, `tests/test_reconciler_visible.py`), triggered `no_progress_detected` in iteration 2, and was cleanly rolled back by G4/terminal guard. Custom CodeAct resolved task in 1 iteration (114s). |
| `benchmarks/latest_benchmark_report.json` | 2026-09-05 18:01:30 | 2 | `task1_reconciliation`, `task2_rate_limiter` | **100% pass rate** (2/2 tasks). Average duration: 61.82s. Both completed in 1 iteration. |

---

## 5. Comprehensive Capability Classification Matrix (R1)

Based on code inspection, unit test verification, and empirical benchmark evidence, existing Loop Engineering capabilities are classified as follows:

| Capability ID | Capability Name | Classification | Code Location | Unit / Test Location | Empirical Evidence & Grounding |
|---|---|---|---|---|---|
| **G1** | **Evidence & Provenance Ledger** | **PROVEN** | `src/loops/loop_ledger.py:1-134`, `src/loops/coding_loop.py:50,140,318,596` | `scripts/test_loop_engineering_enhancements.py:20` (`test_g1_evidence_ledger`) | Deterministic unit tests pass. 100% capture rate across 30+ recorded benchmark trials in JSON reports. Zero failures or schema corruptions. |
| **G2** | **Regression Gate** | **STRONGLY SUPPORTED** | `src/loops/coding_loop.py:52,542,687` | `scripts/test_loop_engineering_enhancements.py:67` (`test_g2_regression_gate`) | Deterministic unit test verifies interception and rollback. In `causal_ablation_experiment_report.json`, intercepted silent regression that fooled no-loop control. |
| **G3** | **Anti-Gaming Test Hash** | **STRONGLY SUPPORTED** | `src/loops/coding_loop.py:55,94,382,584` | `scripts/test_loop_engineering_enhancements.py:110` (`test_g3_anti_gaming_guard`) | Deterministic unit test verifies tampering detection and immediate non-retry rollback. Active in all benchmarks with 0.0% false positive rate. |
| **G4** | **Repairability Gate & No-Progress Detection** | **STRONGLY SUPPORTED** | `src/loops/coding_loop.py:58,69,444,677` | `scripts/test_loop_engineering_enhancements.py:161` (`test_g4_repairability_gate`) | Deterministic unit test verifies consecutive `IMPORT_ERROR` trip and rollback. Prevented infinite thrashing in OpenHands spike evaluation and rate limiter ablation. |
| **G5.1** | **Remediation Target Swapping** | **STRONGLY SUPPORTED** | `src/loops/coding_loop.py:28,227,553,564` | `scripts/test_remediation_target_swap.py:1-274` (3 deterministic tests) | Validated across 3 unit/integration tests (discrete, dual verification, end-to-end Git repair). Demonstrated in multi-iteration causal ablation trial. |
| **G5.2** | **Adaptive Context Handover & Micro-Turn Budget** | **EXPERIMENTALLY DEMONSTRATED** | `src/coding_agent/agent.py:44`, `src/loops/coding_loop.py:62,234` | `benchmarks/handover_ablation_experiment.py` | Implemented in code and benchmarked in N=4 trial battery. However, causal advantage delta over static control is currently 0.0% due to task simplicity. |
| **G6** | **Multi-File Patch Isolation** | **SPECULATIVE** | None (unimplemented) | None | Conceptual candidate mentioned in research directives. No code or tests exist. |
| **Aux-1** | **Git Checkpoint & Rollback Engine** | **PROVEN** | `src/coding_agent/tools.py:229-305` | Tested in G1-G4 test suites and all benchmark harnesses | Atomic, isolated commit tagging and hard reset cleanups operating reliably across all trials. |
| **Aux-2** | **Multi-Role OmniRoute Model Router** | **PROVEN** | `src/core/model_router.py:1-112`, `config/model_registry.yaml` | `scripts/openhands_spike_evaluation.py`, `benchmarks/repo_benchmark.py` | Full multi-role dispatch (`planner`, `coder`, `debugger`, `reviewer`) with automated fallback to Ollama local weights. |
| **Aux-3** | **OpenHands Worker Adapter** | **NOT SUFFICIENTLY VERIFIED** | `src/coding_agent/openhands_adapter.py:1-115` | `scripts/openhands_spike_evaluation.py` | Failed in empirical spike (0% vs 100% Custom CodeAct); modified wrong test files and required rollback. |
| **Aux-4** | **Master Research Loop StateGraph** | **EXPERIMENTAL** | `src/loops/master_loop.py:1-100` | `scripts/test_master_loop.py` | Mock StateGraph skeleton printing emojis; no real research tools or LLM calls wired up. |

---

## 6. Critical Observations & Key Insights for Downstream Research

1. **Why Causal Advantage Delta is Currently 0.0% in Benchmark Reports**:
   - In `causal_ablation_experiment_report.json`, both Full-Loop and No-Loop achieved 83.3% overall success.
   - On simple symptom-diagnostic tasks, `combo/coder` (`qwen3-coder-next`) is capable of solving the bug in a single shot (1 iteration, 3-10 micro-turns). When an agent succeeds on the first attempt without triggering regressions, governance controls (G2, G4, G5) remain passive, resulting in identical success rates.
   - In `handover_ablation_experiment_report.json`, both control and treatment achieved 100% success on N=4 trials. The tasks did not sufficiently stress the 10-turn worker budget to cause failure in the control condition.
2. **Where Governance Demonstrated Crucial Value**:
   - On `ledger_reconciliation` with injected regression, the un-governed control agent exhibited classic **false-convergence / evaluator gaming**: it patched visible tests, ignored the broken regression test, and falsely declared success (`Vis:True Reg:False Hid:False`). The governed Loop Engineering agent intercepted the regression via G2, swapped target via G5.1, diagnosed the root cause, repaired it in iteration 2, and passed all 3 tiers independently!
   - On `openhands`, the un-governed agent began thrashing and modifying tests; G3/G4 cleanly aborted and reverted the workspace, preventing repository corruption.
3. **The Highest-Value Next Uncertainty**:
   - Rather than accumulating speculative guards like G6 (Multi-File Patch Isolation), the highest-value scientific uncertainty is **multi-iteration convergence stability under hard budget ceilings and high-entropy multi-step regression injection** (testing whether closed-loop governance prevents false convergence and improves recovery when single-turn solution priors are eliminated).

---

## 7. Inventory of Key Files & Lines

- `src/loops/coding_loop.py`:
  - Lines 24–67: `CodingState` definition with all G1–G5 fields.
  - Lines 69–77: `compute_failure_signature` (fingerprinting).
  - Lines 80–92: `classify_failure` (taxonomy).
  - Lines 94–103: `compute_test_file_hash` (G3 hash calculation).
  - Lines 106–178: `define_stage` (G1 baseline, G3 initial hash).
  - Lines 181–215: `plan_stage` (invariant formulation).
  - Lines 219–341: `implement_stage` (G5.1 swap alert, G5.2 adaptive turn budget & handover).
  - Lines 344–369: `test_stage` (automated test execution).
  - Lines 372–434: `verify_stage` (G3 integrity check, no-progress detection).
  - Lines 437–487: `failure_stage` (G4 failure classification, unrepairable detection).
  - Lines 490–525: `refine_stage` (surgical remediation planning).
  - Lines 528–621: `reevaluate_stage` (G2 regression gate, G5.1 target swapping, dual verification).
  - Lines 624–665: `rollback_and_stop_stage` (terminal rollback guard).
  - Lines 668–697: Routing decisions (`check_verification_decision`, `check_reevaluate_decision`).
  - Lines 699–745: `build_coding_loop` (StateGraph wiring).
- `src/loops/loop_ledger.py`:
  - Lines 21–79: `create_ledger_entry` (telemetry schema).
  - Lines 82–95: `StageTimer` (monotonic timer).
  - Lines 97–104: `append_ledger_entry` (immutable accumulation).
  - Lines 107–134: `summarize_ledger` (aggregate metrics).
- `src/coding_agent/agent.py`:
  - Lines 44–72: `get_handover_summary` (decision-relevant state extraction).
  - Lines 75–282: `CodeActCodingAgent` implementation.
- `src/coding_agent/tools.py`:
  - Lines 11–30: Blocked commands and sensitive file patterns.
  - Lines 46–69: `resolve_safe_path` (workspace confinement).
  - Lines 229–275: `git_checkpoint`.
  - Lines 277–305: `git_rollback`.
  - Lines 307–384: `run_test_suite`.
- `scripts/test_loop_engineering_enhancements.py`:
  - Lines 20–65: Test G1.
  - Lines 67–108: Test G2.
  - Lines 110–159: Test G3.
  - Lines 161–205: Test G4.
- `scripts/test_remediation_target_swap.py`:
  - Lines 26–95: Test G5.1 discrete swap.
  - Lines 97–148: Test G5.1 dual verification.
  - Lines 150–255: Test G5.1 end-to-end loop integration.
