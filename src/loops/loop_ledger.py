"""
Loop Engineering Evidence & Provenance Ledger.

Records every stage transition in the coding loop with structured telemetry:
- ISO 8601 timestamps
- Stage name and iteration
- Key state deltas (status, test results, classifications, guard triggers)
- Stage execution duration
- Decision rationale

The ledger is stored as a list of dicts in CodingState['ledger_entries'].
Callers can serialize to JSON for post-hoc analysis and audit.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def create_ledger_entry(
    stage: str,
    iteration: int,
    *,
    status: str = "",
    test_passed: Optional[bool] = None,
    failure_classification: Optional[str] = None,
    failure_signature: Optional[str] = None,
    no_progress: Optional[bool] = None,
    rolled_back: Optional[bool] = None,
    test_integrity_violation: Optional[bool] = None,
    regression_detected: Optional[bool] = None,
    target_swapped: Optional[bool] = None,
    unrepairable: Optional[bool] = None,
    patch_summary: Optional[str] = None,
    failure_attribution: Optional[str] = None,
    decision: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Creates a single structured ledger entry for a loop stage transition."""
    entry: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "iteration": iteration,
        "status": status,
    }

    # Conditional fields — only include when set (keeps ledger compact)
    if test_passed is not None:
        entry["test_passed"] = test_passed
    if failure_classification is not None:
        entry["failure_classification"] = failure_classification
    if failure_signature is not None:
        entry["failure_signature"] = failure_signature
    if no_progress is not None:
        entry["no_progress"] = no_progress
    if rolled_back is not None:
        entry["rolled_back"] = rolled_back
    if test_integrity_violation is not None:
        entry["test_integrity_violation"] = test_integrity_violation
    if regression_detected is not None:
        entry["regression_detected"] = regression_detected
    if target_swapped is not None:
        entry["target_swapped"] = target_swapped
    if unrepairable is not None:
        entry["unrepairable"] = unrepairable
    if patch_summary is not None:
        entry["patch_summary"] = patch_summary[:500]  # Truncate for ledger compactness
    if failure_attribution is not None:
        entry["failure_attribution"] = failure_attribution[:500]
    if decision is not None:
        entry["decision"] = decision
    if duration_seconds is not None:
        entry["duration_seconds"] = round(duration_seconds, 3)
    if extra:
        entry["extra"] = extra

    return entry


class StageTimer:
    """Context manager to measure stage execution duration."""

    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.elapsed: float = 0.0

    def __enter__(self) -> "StageTimer":
        self.start_time = time.monotonic()
        return self

    def __exit__(self, *args: Any) -> None:
        self.elapsed = time.monotonic() - self.start_time


def append_ledger_entry(
    existing_entries: Optional[List[Dict[str, Any]]],
    entry: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Immutably appends a ledger entry to the existing list."""
    entries = list(existing_entries or [])
    entries.append(entry)
    return entries


def summarize_ledger(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Produces a compact summary of the full ledger for final reporting."""
    if not entries:
        return {"total_entries": 0, "stages_visited": [], "outcome": "unknown"}

    stages = [e["stage"] for e in entries]
    total_duration = sum(e.get("duration_seconds", 0.0) for e in entries)
    final_status = entries[-1].get("status", "unknown")
    iterations = max(e.get("iteration", 1) for e in entries)

    guard_events = {
        "no_progress_triggered": any(e.get("no_progress") for e in entries),
        "rollback_triggered": any(e.get("rolled_back") for e in entries),
        "test_integrity_violation": any(e.get("test_integrity_violation") for e in entries),
        "regression_detected": any(e.get("regression_detected") for e in entries),
        "target_swapped": any(e.get("target_swapped") for e in entries),
        "unrepairable_detected": any(e.get("unrepairable") for e in entries),
    }

    return {
        "total_entries": len(entries),
        "stages_visited": stages,
        "total_iterations": iterations,
        "total_duration_seconds": round(total_duration, 3),
        "final_status": final_status,
        "guard_events": guard_events,
    }
