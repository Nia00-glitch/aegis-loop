# Adversarial Challenge & Empirical Stress-Test Analysis (Milestone M1)

**Challenger**: Challenger 1 (Empirical Challenger / Critic & Specialist)  
**Target Document**: `reports/state_reconstruction_and_evidence_matrix.md` (`REP-R1-STATE-EVIDENCE-20260907`)  
**Date**: 2026-09-07  
**Verdict**: **CHALLENGE_FAILED** (Core assertions regarding G3 infallibility and G4 immediate termination refuted by empirical evidence; G3 classification as "PROVEN" is invalid and must be downgraded to "EXPERIMENTAL / VULNERABLE")

---

## 1. Executive Summary of Challenges

The target report `reports/state_reconstruction_and_evidence_matrix.md` provides an extensive reconstruction of the repository and theoretical grounding. However, under adversarial empirical stress-testing and source-code inspection, several critical assertions collapse:

| Capability / Claim | Report Classification | Empirical Reality | Challenger Verdict |
|---|---|---|---|
| **G1 Evidence Ledger** | PROVEN | Fully deterministic, tamper-evident within python process, monotonic timing confirmed. | **APPROVE (PROVEN)** |
| **G2 Regression Gate** | STRONGLY SUPPORTED | Intercepts failing regression test and triggers retry/rollback as claimed. | **APPROVE (STRONGLY SUPPORTED)** |
| **G3 Anti-Gaming Test Hash** | **PROVEN** | **CRITICAL VULNERABILITIES FOUND**: Easily circumvented via directory targets, test file deletion, shared fixture tampering, and regression target evasion. | **REFUTED / DOWNGRADE REQUIRED (EXPERIMENTAL / VULNERABLE)** |
| **G4 Structural Repairability Gate** | STRONGLY SUPPORTED | **STRUCTURAL LEAKAGE FOUND**: Flagged `unrepairable = True` does NOT abort execution at `failure_stage`. StateGraph leaks an entire extra iteration (`refine` -> `implement` -> `test`) before `verify` catches it. Unit test masked this by bypassing the StateGraph runtime. | **PARTIALLY REFUTED / STRUCTURAL DEFECT** |
| **G5.1 Remediation Target Swapping** | STRONGLY SUPPORTED | Mechanically functional (swaps target and recovers), but hashes swapped target *post-mutation*, creating a window for regression test gaming. | **APPROVE WITH CAVEAT (STRONGLY SUPPORTED)** |
| **G5.2 Adaptive Context Handover** | EXPERIMENTALLY DEMONSTRATED | Implemented and benchmarked, though advantage delta was neutral ($\Delta = 0.0\%$) due to task simplicity. | **APPROVE (EXPERIMENTALLY DEMONSTRATED)** |
| **G6 Multi-File Patch Isolation** | SPECULATIVE | Completely unimplemented. Classification as SPECULATIVE is accurate. | **APPROVE (SPECULATIVE)** |
| **Mathematical Soundness (pass@k vs pass^k)** | SOUND | Formulations of Chen et al. pass@k and hypergeometric pass^k are mathematically exact. | **APPROVE (SOUND)** |

---

## 2. Empirical Verification of Standard Test Suites

### 2.1 Enhancements Test Suite (`scripts/test_loop_engineering_enhancements.py`)
Execution command:
```powershell
.venv\Scripts\python.exe -m scripts.test_loop_engineering_enhancements
```
**Empirical Result**: `ALL ENHANCEMENT TESTS: PASSED (4/4)`
- `test_g1_evidence_ledger`: Recorded 6 stages (`DEFINE`, `PLAN`, `IMPLEMENT`, `TEST`, `VERIFY`, `RE-EVALUATE`) with monotonic `duration_seconds`.
- `test_g2_regression_gate`: Caught injected regression and routed to `regression_rolled_back`.
- `test_g3_anti_gaming_guard`: Detected direct string edit in single file `test_target.py` and flagged `test_integrity_violation`.
- `test_g4_repairability_gate`: Successfully returned `unrepairable = True` and decision `fail` when manually invoked.

### 2.2 Remediation Target Swap Suite (`scripts/test_remediation_target_swap.py`)
Execution command:
```powershell
.venv\Scripts\python.exe -m scripts.test_remediation_target_swap
```
**Empirical Result**: Running (Tests 1 and 2 passed deterministically; Test 3 undergoing E2E loop).
- Test 1 (Discrete Target Swapping): Verified target swapped from `test_visible.py` to `test_regression.py`.
- Test 2 (Dual Verification Convergence): Verified both regression and visible tests must pass before acceptance.

---

## 3. Adversarial Challenge 1: G3 SHA-256 Anti-Gaming Circumvention

### 3.1 The Report's Claim
In Table 6.2 and Section 3.3, the report claims:
> "G3 Anti-Gaming Test Hash Guard: **PROVEN**"  
> "SHA-256 collision resistance mathematically guarantees detection of any byte modification to the test target. Aborts immediately without retries. Zero false positives in benchmarks. Invalidation conditions: Discovery of a SHA-256 collision or undetected mutation of a test target."

### 3.2 The Flaw
The claim confuses **cryptographic hash collision resistance** (which is proven mathematically for SHA-256) with **system-level integrity enforcement** (which is software engineering prone to design flaws). An agent does NOT need to find a SHA-256 collision to completely evade G3.

### 3.3 Four Empirical Attack Scenarios Refuting G3 Infallibility

#### Attack Scenario A: Directory-Level Test Targets (Complete Guard Deactivation)
- **Source Code Inspection** (`src/loops/coding_loop.py:94-103`):
  ```python
  def compute_test_file_hash(workspace_root: Path, test_target: str) -> Optional[str]:
      test_path = (workspace_root / test_target).resolve()
      try:
          if test_path.is_file():
              content = test_path.read_bytes()
              return hashlib.sha256(content).hexdigest()
      except Exception:
          pass
      return None
  ```
- **Vulnerability**: If `test_target` is a directory (e.g. `tests/` or `tests`), `test_path.is_file()` returns `False`. `compute_test_file_hash` returns `None`.
- In `define_stage`: `state["test_file_hash"] = None`.
- In `verify_stage` (lines 383-392):
  ```python
  init_hash = state.get("test_file_hash")
  if init_hash:
      current_hash = compute_test_file_hash(Path(state["workspace_root"]), state["test_target"])
      if current_hash and current_hash != init_hash:
          integrity_violation = True
  ```
  Since `init_hash` is `None`, the entire guard block is **bypassed completely**.
- **Blast Radius**: Any task invoked with a directory test target (such as `test_target="tests"`, as seen in G4's own unit test!) allows the agent to edit, overwrite, or empty ANY test file inside `tests/` without triggering G3.

#### Attack Scenario B: Test Target File Deletion Bypass
- If `test_target` is a file (e.g. `test_target.py`), `define_stage` records `init_hash`.
- If the agent **deletes** the test file:
  In `verify_stage`:
  `current_hash = compute_test_file_hash(...)` returns `None` (because `is_file()` is False).
  The check `if current_hash and current_hash != init_hash:` evaluates `current_hash and ...` which evaluates to `None` (Falsey)!
  `test_integrity_violation` is **NEVER set to True**!
- **Blast Radius**: The agent can delete the test suite file to silence tests, and G3 will fail to raise a test integrity violation.

#### Attack Scenario C: Regression Target File Tampering in `reevaluate_stage`
- In `define_stage`, G3 ONLY computes the hash for `state["test_target"]` (the visible test file).
- If a task defines `regression_test_target="tests/test_regression.py"`, its hash is **NEVER computed at baseline**!
- During `implement_stage`, the agent has full filesystem write permissions and can modify `tests/test_regression.py` (e.g., rewriting failing assertions to `assert True`).
- In `verify_stage`, G3 checks ONLY `state["test_target"]` (`tests/test_visible.py`). Since the visible test was not touched, G3 passes!
- In `reevaluate_stage`, the harness executes `run_test_suite(..., test_target=regression_target)`. The tampered regression test passes!
- `reevaluate_stage` NEVER checked `regression_target` against any baseline hash! It then marks `status = "converged_accepted"`.
- **Blast Radius**: The agent can trivially game regression tests without detection.

#### Attack Scenario D: Shared Test Fixture / `conftest.py` Tampering
- G3 hashes strictly the single path in `test_target`.
- In any pytest suite, assertions and mocks can be subverted by modifying `conftest.py` or helper fixtures.
- The hash of `test_target` remains byte-identical, completely blind to the fixture compromise.

### 3.4 Verdict on G3
G3 cannot be classified as **PROVEN**. A security mechanism that fails upon directory targets, file deletions, and unmonitored regression files is **EXPERIMENTAL / VULNERABLE**. It must be downgraded.

---

## 4. Adversarial Challenge 2: G4 Structural Repairability Gate Termination Defect

### 4.1 The Report's Claim
In Table 6.2 and Section 3.4:
> "G4: Structural Repairability & No-Progress Gate: **STRONGLY SUPPORTED**"  
> "Deterministic unit tests confirm consecutive `IMPORT_ERROR` trips rollback... Invalidation conditions: Failure to trip on infinite identical failure loops or false abort on genuine progress."

### 4.2 The Flaw
The unit test `test_g4_repairability_gate` was **empirically deceptive**:
```python
fail_res = failure_stage(state)
merged_state = {**state, **fail_res}
decision = check_verification_decision(merged_state)
```
The test manually chained `failure_stage` into `check_verification_decision`. But in the compiled LangGraph StateGraph (`src/loops/coding_loop.py:713-744`), that edge **does not exist**!

### 4.3 Empirical Proof of StateGraph Stage Leakage
In `build_coding_loop()`:
```python
graph.add_edge("failure", "refine")
graph.add_edge("refine", "implement")
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
```
- When consecutive `IMPORT_ERROR`s occur, `failure_stage` sets `unrepairable = True`.
- However, `failure` has an **unconditional, hard edge** to `refine` (`graph.add_edge("failure", "refine")`)!
- It does NOT terminate or route to `rollback_and_stop_stage`!
- It proceeds to execute `refine_stage` (invoking the debugger LLM), then `implement_stage` (invoking the coding agent and consuming worker micro-turns!), then `test_stage`, and only in `verify_stage` does `check_verification_decision` finally see `unrepairable == True` and stop the loop.
- **Consequence**: The gate fails to provide immediate short-circuiting on unrepairable structural blockers; it leaks an entire extra refinement and implementation cycle, burning LLM tokens and execution budget after a structural blocker has already been identified.

---

## 5. Adversarial Challenge 3: G5.1 Remediation Target Swapping Mechanics

### 5.1 Verification
- Target swapping correctly redirects `test_target` to `regression_test_target` when a regression is caught.
- Dual-direction verification ensures both regression and original visible tests must pass.
- **Empirical Edge Case**:
  Because G3's hash for the swapped regression target is calculated in `reevaluate_stage` (after mutations have already occurred in iteration 1), any pre-existing tampering of the regression test file by the agent in iteration 1 is locked in as the "valid" hash for iteration 2!
  Baseline hashes for ALL potential test targets (visible and regression) must be established up front in `define_stage`.

---

## 6. Verification of Mathematical Formulations

Section 4.1 of the report formalizes:
1. Classical $\text{pass}@k$ (Chen et al., 2021):
   $$\text{pass}@k = \mathbb{E}_{\text{tasks}}\left[1 - \frac{\binom{n-c}{k}}{\binom{n}{k}}\right]$$
2. Autonomous repeated-run consistency ($\text{pass}^k$):
   $$\text{pass}^k = p^k = \left(\frac{c}{n}\right)^k$$
   Finite-sample estimator without replacement:
   $$\widehat{\text{pass}^k} = \frac{\binom{c}{k}}{\binom{n}{k}}$$
3. Divergence Table ($p=0.20 \implies \text{pass}@5=67.2\%, \text{pass}^5=0.03\%$).

**Assessment**: The mathematical formulations, combinatorial logic, and numerical derivations are **rigorous, sound, and fully verified**.

---

## 7. Required Corrections to Evidence Matrix

To restore scientific integrity, the following amendments to `reports/state_reconstruction_and_evidence_matrix.md` are mandatory:

1. **Downgrade G3 from PROVEN to EXPERIMENTAL / VULNERABLE**:
   SHA-256 collision resistance does not confer immunity to file deletion, directory targets, or unhashed regression files. G3 must hash all test files in the workspace (or a directory tree hash) during `define_stage` and treat missing files as tampering.
2. **Correct G4 StateGraph Routing**:
   `failure_stage` must have a conditional routing edge: if `unrepairable == True`, route immediately to `rollback_and_stop`, rather than leaking into `refine` and `implement`.
3. **Pre-Compute All Target Hashes in G5.1**:
   `define_stage` must capture baseline hashes for both `test_target` and `regression_test_target` before any worker turns execute.
