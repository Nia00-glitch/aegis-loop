from src.application.research.claim_extractor import (
    ClaimExtractor,
)
from src.application.research.claim_models import (
    ClaimType,
)
from src.application.research.document_chunker import (
    DocumentChunk,
)


def main():
    print("ATOMIC CLAIM EXTRACTION REGRESSION CHECK")
    print("=" * 60)

    content = (
        "The company launched a new analytics platform. "
        "The platform costs $20 per month. "
        "The global market is growing rapidly. "
        "The company has 10 million users."
    )

    chunk = DocumentChunk(
        chunk_id="test-source#chunk-0",
        chunk_index=0,
        document_url="https://example.com/research",
        content=content,
        character_count=len(content),
    )

    extractor = ClaimExtractor()

    first_result = extractor.extract(chunk)
    second_result = extractor.extract(chunk)

    first_claims = first_result.claims
    second_claims = second_result.claims

    if len(first_claims) < 2:
        raise RuntimeError(
            "Multiple atomic claims were not extracted"
        )

    if len(first_claims) != len(second_claims):
        raise RuntimeError(
            "Extraction is not deterministic"
        )

    first_ids = [
        claim.claim_id
        for claim in first_claims
    ]

    second_ids = [
        claim.claim_id
        for claim in second_claims
    ]

    if first_ids != second_ids:
        raise RuntimeError(
            "Claim IDs are not deterministic"
        )

    if len(first_ids) != len(set(first_ids)):
        raise RuntimeError(
            "Duplicate claim IDs detected"
        )

    valid_types = set(ClaimType)

    for claim in first_claims:
        if not claim.text.strip():
            raise RuntimeError(
                "Empty claim detected"
            )

        if claim.source_chunk_id != chunk.chunk_id:
            raise RuntimeError(
                "Source chunk traceability failed"
            )

        if claim.source_url != chunk.document_url:
            raise RuntimeError(
                "Source URL traceability failed"
            )

        if claim.claim_type not in valid_types:
            raise RuntimeError(
                "Invalid claim type detected"
            )

    print(f"\nTotal claims: {len(first_claims)}")

    for index, claim in enumerate(
        first_claims,
        start=1,
    ):
        print(f"\nCLAIM {index}")
        print(f"ID: {claim.claim_id}")
        print(f"Type: {claim.claim_type.value}")
        print(f"Text: {claim.text}")
        print(
            f"Source chunk: "
            f"{claim.source_chunk_id}"
        )

    print("\n" + "=" * 60)
    print("ATOMIC CLAIM EXTRACTION: PASSED")


if __name__ == "__main__":
    main()
