from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EvidenceStatus(str, Enum):
    CANDIDATE = "candidate"
    SUPPORTED = "supported"
    INSUFFICIENT = "insufficient"
    CONFLICTING = "conflicting"


@dataclass
class EvidenceCandidate:
    evidence_id: str
    claim: str
    chunk_id: str
    source_url: str
    supporting_text: str
    status: EvidenceStatus = EvidenceStatus.CANDIDATE


@dataclass
class EvidenceAssessment:
    evidence_id: str
    confidence: float
    status: EvidenceStatus
    reasoning: str


@dataclass
class VerifiedEvidence:
    evidence_id: str
    claim: str
    source_url: str
    supporting_text: str
    confidence: float
    status: EvidenceStatus
