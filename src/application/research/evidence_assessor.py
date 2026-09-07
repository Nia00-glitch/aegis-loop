from __future__ import annotations

from src.application.research.evidence_models import (
    EvidenceAssessment,
    EvidenceCandidate,
    EvidenceStatus,
)


class EvidenceAssessor:
    def assess(
        self,
        candidate: EvidenceCandidate,
    ) -> EvidenceAssessment:
        if not candidate.claim.strip():
            return EvidenceAssessment(
                evidence_id=candidate.evidence_id,
                confidence=0.0,
                status=EvidenceStatus.INSUFFICIENT,
                reasoning="Evidence candidate has no claim text.",
            )

        if not candidate.supporting_text.strip():
            return EvidenceAssessment(
                evidence_id=candidate.evidence_id,
                confidence=0.0,
                status=EvidenceStatus.INSUFFICIENT,
                reasoning="Evidence candidate has no supporting text.",
            )

        if candidate.source_url != candidate.source_url.strip():
            return EvidenceAssessment(
                evidence_id=candidate.evidence_id,
                confidence=0.0,
                status=EvidenceStatus.INSUFFICIENT,
                reasoning="Evidence candidate has an invalid source URL.",
            )

        return EvidenceAssessment(
            evidence_id=candidate.evidence_id,
            confidence=0.0,
            status=EvidenceStatus.CANDIDATE,
            reasoning=(
                "Structural validation passed. "
                "Semantic claim validation is required "
                "before assigning supported status."
            ),
        )

    def assess_many(
        self,
        candidates: list[EvidenceCandidate],
    ) -> list[EvidenceAssessment]:
        return [
            self.assess(candidate)
            for candidate in candidates
        ]
