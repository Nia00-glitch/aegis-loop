# Project: Loop Engineering Causal Reliability & Governance Benchmarking

## Architecture
- **Loop Engineering Subsystem**:
  - `src/loops/coding_loop.py`: 8-stage state machine (`DEFINE` -> `PLAN` -> `IMPLEMENT` -> `TEST` -> `VERIFY` -> `FAILURE` -> `REFINE` -> `RE-EVALUATE`), atomic Git rollbacks, micro-turn budget management.
  - `src/loops/loop_ledger.py`: G1 immutable structured telemetry, SHA-256 state hash chaining, stage timing, outcome metrics.
  - `src/coding_agent/agent.py`: Custom CodeAct coding agent with bash execution, file read/write, context handover summaries (G5.2).
  - `src/core/model_router.py`: OmniRoute gateway client on `http://127.0.0.1:20128/v1` supporting fallback routing and role mappings (`coder` -> `kiro/qwen3-coder-next`).
- **Benchmark & Verification Harness**:
  - `benchmarks/repo_benchmark.py`: Benchmark framework, task definitions, and evaluator correctness validator (`validate_evaluator_correctness`).
  - `benchmarks/causal_ablation_experiment.py`: Pairwise causal ablation runner comparing baseline unguided control against governed treatment under matched constraints.
  - `benchmarks/handover_ablation_experiment.py`: Adaptive context handover and turn-budget transfer benchmark.
  - 3-Tier Independent Evaluator:
    - Tier 1: Visible unit tests (exercised by agent during implementation).
    - Tier 2: Regression tests (untouched baseline invariants).
    - Tier 3: Quarantine Hidden Invariant tests (run strictly post-run by evaluator, zero agent visibility).
- **Active Safety Gates**:
  - G1: Evidence Ledger (cryptographic hash chaining, immutable event log)
  - G2: Regression Gate (untouched regression test execution and detection)
  - G3: Anti-Gaming Test Hash (SHA-256 pre/post mutation verification of test files)
  - G4: Repairability Gate & No-Progress Guard (syntax/import classification and stack-trace hash detection)
  - G5.1: Remediation Target Swapping (dynamic target redirection to failing regression target)
  - G5.2: Adaptive Context Handover & Micro-Turn Budget Transfer (structured inter-iteration handover under global 25-turn budget)

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | Repository State Reconstruction | Comprehensive inspection of ARCHITECTURE.md, safety gates G1-G6, prior ablations | M1 | Survey E1 |
| F2 | External Literature Grounding | Formal synthesis of pass@k vs pass^k, evaluator gaming, causal agent evaluation, trajectory attribution | M1 | Survey E2 |
| F3 | Epistemological Evidence Matrix | Classify G1-G6 into 6 evidence categories (PROVEN to NOT SUFFICIENTLY VERIFIED) | M1 | Survey E1, E2 |
| F4 | Scientific Hypothesis Formulation | Formulate falsifiable hypothesis evaluating system-level reliability over guard accumulation | M2 | Survey E2, User R2 |
| F5 | Pairwise Causal Isolation | Matched Control (unguided CodeAct) vs Treatment (closed-loop governance) with fixed 25-turn budget, model, tasks | M3 | Survey E3, User R3 |
| F6 | Multi-Metric Reliability Verification | Measurement of all 14+ core reliability metrics (pass@1, pass^k, regression rate, rollback rate, hidden invariant violations, etc.) | M3 | Survey E2, E3, User R4 |
| F7 | Safety Guarantee Preservation | Empirical verification of active preservation of G1, G2, G3, G4, G5.1, G5.2 | M3 | Survey E1, E3 |
| F8 | 14-Section Research Deliverable | Formal publication-grade research report adhering strictly to sections A through N | M4 | User Deliverable |
| F9 | Single Uncertainty Designation | Formal empirical designation of exactly ONE highest-value next research uncertainty | M4 | User Deliverable |
| F10 | Opaque-Box E2E Test Suite | 4-tier requirement-driven verification test suite covering loop engineering safety guarantees | M_TEST | User R4, E2E Track |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | State Reconstruction & Literature Grounding | Complete repository inspection, literature synthesis, and G1-G6 evidence classification matrix | none | IN_PROGRESS |
| M2 | Scientific Hypothesis Formulation | Formulate and justify falsifiable hypothesis regarding closed-loop governance vs unguided agent | M1 | PLANNED |
| M3 | Controlled Causal Experimentation & Multi-Metric Verification | Run pairwise Control vs Treatment across 4 multi-file benchmark tasks with repeated runs (k>=3), 25-turn budget, model kiro/qwen3-coder-next, extract all 14+ reliability metrics | M2 | PLANNED |
| M4 | 14-Section Definitive Research Deliverable Compilation | Author 14-section formal report (Sections A-N), synthesize findings, failure analysis, causal interpretation, and designate single uncertainty | M3 | PLANNED |
| M_TEST | E2E Testing & Independent Verification Track | Build requirement-driven opaque-box test suite for loop engineering governance, publish TEST_READY.md | none | IN_PROGRESS |

## Interface Contracts
### Loop State ↔ Evaluator
- `LoopState` must contain:
  - `workspace_root`: str / Path
  - `test_target`: str (relative path to active test)
  - `regression_test_target`: str (relative path to baseline invariant test)
  - `hidden_test_target`: str (relative path to hidden test)
  - `total_micro_turns`: int (strictly <= 25)
  - `ledger_entries`: list of LedgerEntry
  - `status`: str ('success', 'regression_rolled_back', 'no_progress_rolled_back', 'unrepairable_rolled_back', 'test_integrity_violation', 'budget_exhausted')
- Evaluator outputs:
  - `visible_passed`: bool
  - `regression_passed`: bool
  - `hidden_passed`: bool
  - `evaluator_sound`: bool
  - `verified_correctness`: bool (`visible_passed and regression_passed and hidden_passed and not integrity_violation`)

## Code Layout
- `src/loops/`: Core loop implementation (`coding_loop.py`, `loop_ledger.py`)
- `src/coding_agent/`: Agent implementation (`agent.py`, `base.py`)
- `src/core/`: Foundation infrastructure (`model_router.py`)
- `benchmarks/`: Benchmark definitions, runners, and experiment reports
- `scripts/`: Verification scripts and runner tools
- `tests/`: Unit and integration test suites
- `reports/`: Formal research reports and empirical evidence artifacts
