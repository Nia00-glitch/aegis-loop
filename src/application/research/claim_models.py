from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ClaimType(str, Enum):
    FACT = "fact"
    METRIC = "metric"
    FEATURE = "feature"
    MARKET = "market"
    COMPETITIVE = "competitive"
    OTHER = "other"


@dataclass
class AtomicClaim:
    claim_id: str
    text: str
    claim_type: ClaimType
    source_chunk_id: str
    source_url: str
    supporting_text: str


@dataclass
class ClaimExtractionResult:
    source_chunk_id: str
    claims: list[AtomicClaim]
