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

    print("TRACEABLE CHUNKING PIPELINE CHECK")
    print("=" * 60)

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
        raise RuntimeError("No chunks were created")

    print(f"Prepared characters: {prepared.character_count}")
    print(f"Total chunks: {len(chunks)}")

    chunk_ids = [chunk.chunk_id for chunk in chunks]

    if len(chunk_ids) != len(set(chunk_ids)):
        raise RuntimeError("Chunk IDs are not unique")

    if any(chunk.document_url != url for chunk in chunks):
        raise RuntimeError("Source URL traceability failed")

    print("\nFIRST CHUNK")
    print("-" * 60)

    first = chunks[0]

    print(f"Chunk ID: {first.chunk_id}")
    print(f"Index: {first.chunk_index}")
    print(f"Characters: {first.character_count}")
    print(f"URL: {first.document_url}")
    print("\nContent preview:")
    print(first.content[:500])

    print("\n" + "=" * 60)
    print("TRACEABLE CHUNKING PIPELINE: PASSED")


if __name__ == "__main__":
    main()
