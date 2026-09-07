# Antigravity Workspace Guidelines: Loop Engineering & OmniRoute

This workspace utilizes the **Loop Engineering** iterative development framework and **OmniRoute** model gateway.

## Core Rules

1. **Loop Engineering Contract**:
   All autonomous code modifications must pass through the 8 Loop Engineering stages:
   `DEFINE` $\to$ `PLAN` $\to$ `IMPLEMENT` $\to$ `TEST` $\to$ `VERIFY` $\to$ `FAILURE` $\to$ `REFINE` $\to$ `RE-EVALUATE`.

2. **Model Gateway**:
   External and local model calls are routed via OmniRoute on `http://localhost:20128/v1`.
   Task-specific combos:
   - `combo/planner`: Reasoning & boundary conditions
   - `combo/coder`: Patch synthesis
   - `combo/debugger`: Failure diagnosis
   - `combo/reviewer`: Diff review & regression gate
   - `combo/fast`: Quick edits & token triage

3. **Objective Verification Gate**:
   Never declare success based solely on model output. Success requires 100% passing tests and zero regressions.

4. **Security & Workspace Isolation**:
   - Operations are confined strictly within the project workspace.
   - Every modification cycle must have a Git checkpoint for instant rollback.
   - Protected files (`.env`, secrets, SQLite databases) must never be committed or printed.
