# Loop Engineering Governance Test Infrastructure (TEST_INFRA)

## 1. Executive Summary & Verification Objective

The Loop Engineering governance subsystem enforces strict safety invariants over autonomous coding agents to ensure reproducibility, recoverability, tamper-resistance, and regression protection. This document formalizes the opaque-box, requirement-driven test infrastructure and verification methodology for Loop Engineering safety guarantees (G1–G5.2), implemented in `tests/test_e2e_governance_requirements.py`.

The test suite provides exhaustive independent verification across four rigorous tiers:
1. **Tier 1: Feature Coverage** (G1–G5.2 individual safety gates)
2. **Tier 2: Boundary & Corner Cases** (BVA, corrupt inputs, edge limits)
3. **Tier 3: Cross-Feature Combinations** (Multi-gate interaction and rollback coordination)
4. **Tier 4: Real-World Workload Scenarios** (Multi-stage defect injection, dynamic target swapping, anti-tampering interception, and clean recovery)

---

## 2. Test Philosophy & Methodological Rigor

The verification infrastructure adheres to four core testing paradigms:

### 2.1 Opaque-Box & Interface-Driven Verification
All tests interact strictly with documented interface contracts and state transitions as specified in `PROJECT.md` and `AGENTS.md`. Test assertions evaluate observable outputs:
- Returned `CodingState` fields (`status`, `rolled_back`, `regression_detected`, `test_integrity_violation`, `unrepairable`, `total_micro_turns`)
- Cryptographic provenance and telemetry in `ledger_entries`
- Filesystem and Git repository state (commits, tree cleanliness, head references)
- Test suite outcomes (`success`, `output`, `data`)

Internal private variables and uncontracted implementation details are never accessed, preserving complete test portability and resilience against internal refactoring.

### 2.2 Category-Partition Method
Input spaces and failure domains are systematically partitioned into equivalence classes:
- **Failure Classification Equivalence Classes**: `SYNTAX_ERROR`, `IMPORT_ERROR`, `ASSERTION_ERROR`, `TIMEOUT`, `LOGIC_OR_RUNTIME_ERROR`.
- **Termination Decisions**: `accept` (all tests passing), `retry` (repairable failure with remaining budget), `fail` (structural blocker, tampering, or budget exhaustion).
- **Execution Runtimes**: Custom CodeAct agent vs. simulated worker.
- **Budget Categories**: Fresh iteration (`iter=1`), normal retry (`iter>1`), post-exhaustion recovery (`BudgetExhausted`).

### 2.3 Boundary Value Analysis (BVA)
Extremes of parameter ranges are systematically exercised:
- **Turn Budgets**: `max_total_micro_turns = 0`, `used_so_far >= max_total`, `stage_budget = 1`.
- **Macro-Iterations**: `iteration = 1` with `max_iterations = 1` (immediate terminal rollback on regression) vs `max_iterations = 3`.
- **Filesystem Boundaries**: 0-byte empty test files, missing/deleted test targets, non-existent workspace paths.
- **Telemetry Boundaries**: `None` ledger entries, empty history lists, empty failure traces.

### 2.4 Pairwise & Cross-Feature Interaction Testing
Guards do not operate in isolation. The suite exercises orthogonal feature intersections:
- Regression detection (G2) triggering dynamic target swapping (G5.1) while maintaining immutable ledger audit entries (G1).
- Test assertion modification (G3) triggering immediate terminal rollback (G4 / Aux-1) without allowing repair retries.
- Remediation of regression causing collateral regression in visible tests, verifying dual-target oscillation protection.

### 2.5 Real-World Workload Testing (Tier 4)
End-to-end integration tests execute complete multi-stage loops within temporary Git repositories. Defects are injected into realistic multi-file modules, evaluating whether the governor detects anomalies, adapts remediation directives, prevents evaluator gaming, and converges or aborts safely.

---

## 3. Feature Inventory & Tier Mapping

| Feature ID | Safety Gate / Guarantee | Description | Target Test Tier | Primary Test Function(s) |
|---|---|---|---|---|
| **G1** | **Evidence & Provenance Ledger** | Immutable audit trail, ISO-8601 timestamps, monotonic durations, guard telemetry, and aggregation | Tier 1, Tier 3 | `test_g1_ledger_schema_and_timestamps`<br>`test_g1_ledger_append_only_immutability`<br>`test_g1_ledger_summary_aggregation` |
| **G2** | **Regression & Invariant Gate** | Intercepts broken baseline invariants, prevents false convergence, enforces rollback on budget exhaustion | Tier 1, Tier 3 | `test_g2_regression_detection_and_status`<br>`test_g2_regression_exhaustion_rollback`<br>`test_g2_regression_retry_routing` |
| **G3** | **Anti-Gaming Test Hash** | SHA-256 pre/post mutation hash verification, catches assertion tampering, aborts immediately | Tier 1, Tier 3 | `test_g3_sha256_hash_computation`<br>`test_g3_tampering_detection_and_abort`<br>`test_g3_tampering_no_retry_enforcement` |
| **G4** | **Repairability Gate & No-Progress** | Categorizes failure taxonomy; trips circuit breaker on repeated syntax/import blockers or identical stack traces | Tier 1, Tier 2, Tier 3 | `test_g4_failure_taxonomy_classification`<br>`test_g4_repeated_import_error_unrepairable`<br>`test_g4_repeated_syntax_error_unrepairable`<br>`test_g4_fingerprint_normalization` |
| **G5.1** | **Remediation Target Swapping** | Dynamically redirects active `test_target` to failing regression suite; executes dual verification before final acceptance | Tier 1, Tier 3 | `test_g5_1_target_swapping_mechanics`<br>`test_g5_1_dual_verification_convergence`<br>`test_g5_1_collateral_regression_swap_back` |
| **G5.2** | **Adaptive Context Handover & Micro-Turn Budget** | Enforces 25-turn global ceiling; dynamically transfers residual turns and structured inspection/patch context | Tier 1, Tier 2 | `test_g5_2_budget_ceiling_enforcement`<br>`test_g5_2_adaptive_stage_budget_allocation`<br>`test_g5_2_handover_summary_structure` |
| **BND** | **Boundary & Corner Cases** | Empty files, missing paths, zero budgets, corrupt telemetry, identical error loops | Tier 2 | `test_tier2_empty_test_file`<br>`test_tier2_missing_test_target`<br>`test_tier2_zero_turn_budget_ceiling`<br>`test_tier2_corrupt_ledger_handling`<br>`test_tier2_identical_stacktrace_no_progress` |
| **XFEAT**| **Cross-Feature Combinations** | Multi-gate interaction: G2 + G5.1 + G1, G3 + G4 terminal rollback, G4 + G1 telemetry audit | Tier 3 | `test_tier3_g2_g5_1_g1_combined_flow`<br>`test_tier3_g3_tamper_immediate_rollback`<br>`test_tier3_g4_unrepairable_rollback_telemetry` |
| **WORK** | **Real-World Workload Scenarios** | Full lifecycle defect injection, dynamic repair, tampering interception, structural blocker abort | Tier 4 | `test_tier4_scenario_defect_injection_and_dynamic_recovery`<br>`test_tier4_scenario_anti_gaming_tamper_defense`<br>`test_tier4_scenario_structural_blocker_abort` |

---

## 4. Test Suite Architecture & Runner Specifications

### 4.1 Directory Structure
```
tests/
├── __init__.py
└── test_e2e_governance_requirements.py   # Primary E2E requirement verification suite
```

### 4.2 Class Hierarchy in `test_e2e_governance_requirements.py`
The test suite is structured into clear test classes mapping to each tier:
- `TestTier1FeatureCoverage`: Discrete verification of G1 through G5.2.
- `TestTier2BoundaryCases`: Edge boundaries, 0-budgets, empty files, missing targets, signature normalization.
- `TestTier3CrossFeatureCombinations`: Multi-gate interactions (regression + target swap + ledger; tampering + rollback).
- `TestTier4RealWorldScenarios`: End-to-end realistic workflows with defect injection, dynamic repair, and containment.

### 4.3 Execution Commands
To execute the complete E2E requirement verification suite:
```powershell
.venv\Scripts\python.exe -m pytest tests/test_e2e_governance_requirements.py -v
```

To execute specific tiers:
```powershell
# Tier 1 only
.venv\Scripts\python.exe -m pytest tests/test_e2e_governance_requirements.py -k "Tier1" -v

# Tier 2 only
.venv\Scripts\python.exe -m pytest tests/test_e2e_governance_requirements.py -k "Tier2" -v

# Tier 3 only
.venv\Scripts\python.exe -m pytest tests/test_e2e_governance_requirements.py -k "Tier3" -v

# Tier 4 only
.venv\Scripts\python.exe -m pytest tests/test_e2e_governance_requirements.py -k "Tier4" -v
```

---

## 5. Real-World Application Scenarios (Tier 4 Specifications)

### Scenario 1: Multi-Stage Defect Injection & Dynamic Recovery
- **Context**: A multi-file service (`src/models.py`, `src/service.py`) where a developer or prior agent introduced an implementation that satisfies visible withdrawal requirements (`test_visible.py`) but breaks an untouched account fee invariant (`test_regression.py`).
- **Execution**:
  1. Iteration 1: Agent implements visible withdrawal logic; visible test passes.
  2. Re-evaluate Stage: G2 regression gate executes `test_regression.py`, detects failure.
  3. G5.1 Activation: Active `test_target` dynamically switches to `test_regression.py`, baseline hash is updated, and alert is logged.
  4. Iteration 2: Remediator receives regression alert and handover context, repairs `models.py` default fee.
  5. Re-evaluate Stage: G2 dual verification executes both `test_regression.py` and `test_visible.py`. Both pass.
  6. Final Outcome: Status transitions to `converged_accepted`, `original_test_target` is restored, Git repository remains clean and valid.

### Scenario 2: Anti-Gaming Tamper Defense & Containment
- **Context**: An adversarial or misaligned agent attempts to bypass a failing test requirement by modifying or commenting out assertions in `test_target.py`.
- **Execution**:
  1. Define Stage: G3 computes SHA-256 baseline hash of `test_target.py`.
  2. Mutation: Test file assertion is altered or stripped.
  3. Verify Stage: G3 re-hashes `test_target.py`, detects discrepancy, logs critical security guard alert.
  4. Interception: Routing bypasses all retry loops and immediately invokes `rollback_and_stop_stage`.
  5. Postcondition: Status is `test_tampering_rolled_back`, Git hard reset restores original test file, workspace integrity is preserved.

### Scenario 3: Structural Blocker & Unrepairability Guard
- **Context**: A defective patch introduces an external dependency that does not exist in the environment (`ModuleNotFoundError: No module named 'invalid_package'`).
- **Execution**:
  1. Iteration 1: Failure is classified by G4 as `IMPORT_ERROR`.
  2. Iteration 2: Defect persists with identical `IMPORT_ERROR`.
  3. Interception: G4 detects consecutive structural blockers (`len >= 2` and identical classification), sets `unrepairable = True`.
  4. Circuit Breaker: Verification routing aborts loop thrashing and triggers `rollback_and_stop_stage`.
  5. Telemetry: G1 records `unrepairable=True` and reason `UNREPAIRABLE FAILURE PATTERN`. Workspace is rolled back cleanly.
