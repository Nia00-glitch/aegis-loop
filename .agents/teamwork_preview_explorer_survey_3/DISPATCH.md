# DISPATCH: Survey Explorer 3 (Benchmark Harness, Task Suite & Causal Experimentation)

## Target Objective
Investigate existing benchmark runner, test execution harnesses, evaluation scripts, task datasets, tools, model configurations (combo/coder / kiro/qwen3-coder-next), 25-turn budget ceiling enforcement, control vs treatment execution setup, and metric extraction scripts in the repository `C:\Users\Arsh\market-intelligence-os`.
Determine exactly:
- How tests and benchmarks are structured and executed
- What tasks are available in the benchmark suite
- How Control vs Treatment conditions can be causally isolated and executed
- What metrics are currently measured vs needed to measure all 14+ core reliability metrics
- What dependencies or commands are needed to run them

## Mandatory Reading
Read `C:\Users\Arsh\market-intelligence-os\.agents\ORIGINAL_REQUEST.md` before starting work.

## Scope Boundaries
- Read-only exploration and inspection.
- Do NOT modify source files or create implementation code.
- Write your findings, benchmark inventory, and execution specifications to `analysis.md` and `handoff.md` in your working directory `C:\Users\Arsh\market-intelligence-os\.agents\teamwork_preview_explorer_survey_3`.

## 2026-09-07T09:53:57Z
You are Survey Explorer 3 (Benchmark Harness & Causal Experimentation).
Your working directory is C:\Users\Arsh\market-intelligence-os\.agents\teamwork_preview_explorer_survey_3.
Your parent is orchestrator_1 (conversation ID: 50bad958-86ec-4534-a7f1-16433dcdb5ac).

MANDATORY FIRST STEP:
Read C:\Users\Arsh\market-intelligence-os\.agents\ORIGINAL_REQUEST.md and C:\Users\Arsh\market-intelligence-os\.agents\teamwork_preview_explorer_survey_3\DISPATCH.md.

YOUR MISSION:
Investigate existing benchmark runners, test harnesses, evaluation scripts, task datasets, tools, model configurations (combo/coder / kiro/qwen3-coder-next), 25-turn budget ceiling enforcement, control vs treatment execution setup, and metric extraction scripts in C:\Users\Arsh\market-intelligence-os.
Specifically determine:
1. What test/benchmark harnesses exist and how they are invoked.
2. What task distributions/datasets are available for benchmarking.
3. How a matched Control (baseline tools/turns without target governance) vs Treatment (governed closed-loop controls) experiment can be executed holding model, tasks, tools, and budget ceiling (25 turns) strictly constant.
4. How all 14+ core reliability metrics (verified correctness, repeated-run reliability, regression rate, rollback rate, hidden invariant violations, repeated failures, efficiency overhead, etc.) are extracted and tracked.
5. Identify any gaps in the harness or runner that need to be implemented or extended.

OUTPUT DELIVERABLE:
Write a comprehensive report to C:\Users\Arsh\market-intelligence-os\.agents\teamwork_preview_explorer_survey_3\analysis.md and your handoff to C:\Users\Arsh\market-intelligence-os\.agents\teamwork_preview_explorer_survey_3\handoff.md.
When done, notify parent via send_message.


## 2026-09-07T10:10:18Z
**Context**: Phase 0 Survey - Benchmark Harness & Causal Setup
**Content**: Checking in on your progress. What is the current status of your benchmark harness investigation and report drafting?
**Action**: Please provide a quick status update or complete your handoff if ready.
