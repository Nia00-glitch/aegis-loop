from src.infrastructure.extraction.crawler import (
    Crawl4AIAdapter,
)
from src.application.research.document_preparer import (
    DocumentPreparer,
)
from src.application.research.document_chunker import (
    DocumentChunker,
)
from src.application.research.evidence_candidate_builder import (
    EvidenceCandidateBuilder,
)


def main():
    url = "https://www.anthropic.com/news"

    print("EVIDENCE CANDIDATE PIPELINE CHECK")
    print("=" * 60)
    print(f"URL: {url}")

    crawler = Crawl4AIAdapter()
    preparer = DocumentPreparer()
    chunker = DocumentChunker(
        chunk_size=1000,
        overlap=100,
    )
    builder = EvidenceCandidateBuilder()

    extracted = crawler.extract(url)

    if not extracted.success:
        raise RuntimeError(
            f"Extraction failed: {extracted.error}"
        )

    prepared = preparer.prepare(extracted)
    chunks = chunker.chunk(prepared)
    candidates = builder.build_many(chunks)

    if not candidates:
        raise RuntimeError(
            "No evidence candidates created"
        )

    evidence_ids = [
        candidate.evidence_id
        for candidate in candidates
    ]

    if len(evidence_ids) != len(set(evidence_ids)):
        raise RuntimeError(
            "Evidence IDs are not unique"
        )

    first_again = builder.build(chunks[0])

    if first_again.evidence_id != candidates[0].evidence_id:
        raise RuntimeError(
            "Evidence ID is not deterministic"
        )

    for chunk, candidate in zip(chunks, candidates):
        if candidate.chunk_id != chunk.chunk_id:
            raise RuntimeError(
                "Chunk ID traceability failed"
            )

        if candidate.source_url != chunk.document_url:
            raise RuntimeError(
                "Source URL traceability failed"
            )

        if not candidate.supporting_text.strip():
            raise RuntimeError(
                "Empty supporting text detected"
            )

    print(f"\nPrepared characters: {prepared.character_count}")
    print(f"Total chunks: {len(chunks)}")
    print(f"Evidence candidates: {len(candidates)}")

    first = candidates[0]

    print("\nFIRST EVIDENCE CANDIDATE")
    print("-" * 60)
    print(f"Evidence ID: {first.evidence_id}")
    print(f"Chunk ID: {first.chunk_id}")
    print(f"Source URL: {first.source_url}")
    print(f"Status: {first.status.value}")
    print(
        f"Supporting characters: "
        f"{len(first.supporting_text)}"
    )

    print("\n" + "=" * 60)
    print("EVIDENCE CANDIDATE PIPELINE: PASSED")


if __name__ == "__main__":
    main()
