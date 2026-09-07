# Plan: Autonomous Reliability Research & Causal Benchmarking

## Phase 0: Survey & Scoping (Top-Level Orchestrator)
- [ ] Dispatch 3 parallel Explorers:
  - Explorer 1: Codebase Architecture & Safety Gates (ARCHITECTURE.md, G1-G6 capabilities, ledgers, prior ablations)
  - Explorer 2: External Peer-Reviewed Literature & Metric Grounding (pass@k vs pass^k, repeated-run reliability, evaluator integrity, contamination, causal agent evaluation)
  - Explorer 3: Test Infrastructure, Benchmark Harness & Model/Task Configuration (evaluators, tasks, budget ceilings, tool bindings)
- [ ] Synthesize Explorer reports into `PROJECT.md` (Architecture, Feature Inventory, Milestones, Interface Contracts, Code Layout)

## Phase 1: Dual Track Execution
### Track A: Implementation & Research Track
- [ ] Milestone M1: State Reconstruction, Literature Synthesis & Evidence Matrix (Classify G1-G6 into 6 evidence tiers)
- [ ] Milestone M2: Scientific Hypothesis Formulation (Evaluate system-level reliability vs guard accumulation, formulate precise falsifiable hypothesis)
- [ ] Milestone M3: Controlled Causal Experimentation & Multi-Metric Verification (Pairwise Control vs Treatment holding model, tasks, tools, 25-turn budget constant; measure all 14+ reliability metrics; preserve G1-G5 safety guarantees)
- [ ] Milestone M4: 14-Section Definitive Research Deliverable Compilation (Sections A-N, exactly ONE highest-value next research uncertainty designated)

### Track B: E2E Testing & Verification Track
- [ ] Dispatch E2E Testing Track to create `TEST_INFRA.md` and opaque-box test suite (Tiers 1-4)
- [ ] Publish `TEST_READY.md`

## Phase 2: Final Verification & Gate
- [ ] Full E2E & Multi-Metric Verification Pass
- [ ] Independent Forensic Audit Verification (CLEAN verdict required)
- [ ] Victory Audit handoff preparation & notification to Sentinel
