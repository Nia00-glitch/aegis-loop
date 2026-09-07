"""
Loops Package: Master Research Loop & Coding Loop
"""

from src.loops.master_loop import build_master_loop, ResearchState
from src.loops.coding_loop import build_coding_loop, CodingState

__all__ = [
    "build_master_loop",
    "ResearchState",
    "build_coding_loop",
    "CodingState",
]
