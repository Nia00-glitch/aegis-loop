from src.infrastructure.extraction.crawler import (
    Crawl4AIAdapter,
)
from src.application.research.document_preparer import (
    DocumentPreparer,
)
from src.application.research.document_chunker import (
    DocumentChunker,
)


def main():
    url = "https://www.anthropic.com/news"

    print("BOUNDARY-AWARE CHUNKING REGRESSION CHECK")
    print("=" * 60)
    print(f"URL: {url}")

    crawler = Crawl4AIAdapter()
    preparer = DocumentPreparer()

    chunker = DocumentChunker(
        chunk_size=1000,
        overlap=100,
    )

    extracted = crawler.extract(url)

    if not extracted.success:
        raise RuntimeError(
            f"Extraction failed: {extracted.error}"
        )

    prepared = preparer.prepare(extracted)
    chunks = chunker.chunk(prepared)

    if not chunks:
        raise RuntimeError(
            "No chunks were created"
        )

    chunk_ids = [
        chunk.chunk_id
        for chunk in chunks
    ]

    if len(chunk_ids) != len(set(chunk_ids)):
        raise RuntimeError(
            "Chunk IDs are not unique"
        )

    if any(
        chunk.document_url != url
        for chunk in chunks
    ):
        raise RuntimeError(
            "Document URL traceability failed"
        )

    if any(
        not chunk.content.strip()
        for chunk in chunks
    ):
        raise RuntimeError(
            "Empty chunk detected"
        )

    max_chunk_size = max(
        chunk.character_count
        for chunk in chunks
    )

    print(f"\nPrepared characters: {prepared.character_count}")
    print(f"Total chunks: {len(chunks)}")
    print(f"Configured chunk size: {chunker.chunk_size}")
    print(f"Largest chunk: {max_chunk_size}")

    print("\nCHUNK SUMMARY")
    print("-" * 60)

    for chunk in chunks[:5]:
        print(
            f"Chunk {chunk.chunk_index}: "
            f"{chunk.character_count} chars"
        )

    print("\n" + "=" * 60)
    print("BOUNDARY-AWARE CHUNKING REGRESSION: PASSED")


if __name__ == "__main__":
    main()
