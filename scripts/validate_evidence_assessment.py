from src.application.research.evidence_assessor import (
    EvidenceAssessor,
)
from src.application.research.evidence_models import (
    EvidenceCandidate,
    EvidenceStatus,
)


def main():
    print("EVIDENCE ASSESSMENT REGRESSION CHECK")
    print("=" * 60)

    assessor = EvidenceAssessor()

    valid_candidate = EvidenceCandidate(
        evidence_id="evidence-valid",
        claim="The company launched a new product.",
        chunk_id="source#chunk-0",
        source_url="https://example.com",
        supporting_text=(
            "The company announced the launch "
            "of a new product."
        ),
    )

    valid_assessment = assessor.assess(valid_candidate)

    if valid_assessment.status != EvidenceStatus.CANDIDATE:
        raise RuntimeError(
            "Valid structural evidence should remain "
            "CANDIDATE before semantic validation"
        )

    if valid_assessment.confidence != 0.0:
        raise RuntimeError(
            "Confidence must remain 0.0 before "
            "semantic validation"
        )

    empty_claim = EvidenceCandidate(
        evidence_id="evidence-empty-claim",
        claim="",
        chunk_id="source#chunk-1",
        source_url="https://example.com",
        supporting_text="Some supporting text.",
    )

    empty_claim_assessment = assessor.assess(
        empty_claim
    )

    if (
        empty_claim_assessment.status
        != EvidenceStatus.INSUFFICIENT
    ):
        raise RuntimeError(
            "Empty claim was not marked INSUFFICIENT"
        )

    empty_support = EvidenceCandidate(
        evidence_id="evidence-empty-support",
        claim="A test claim.",
        chunk_id="source#chunk-2",
        source_url="https://example.com",
        supporting_text="",
    )

    empty_support_assessment = assessor.assess(
        empty_support
    )

    if (
        empty_support_assessment.status
        != EvidenceStatus.INSUFFICIENT
    ):
        raise RuntimeError(
            "Empty support was not marked INSUFFICIENT"
        )

    print("\nVALID CANDIDATE")
    print(f"Status: {valid_assessment.status.value}")
    print(f"Confidence: {valid_assessment.confidence}")
    print(f"Reasoning: {valid_assessment.reasoning}")

    print("\nEMPTY CLAIM")
    print(
        f"Status: "
        f"{empty_claim_assessment.status.value}"
    )

    print("\nEMPTY SUPPORT")
    print(
        f"Status: "
        f"{empty_support_assessment.status.value}"
    )

    print("\n" + "=" * 60)
    print("EVIDENCE ASSESSMENT REGRESSION: PASSED")


if __name__ == "__main__":
    main()
