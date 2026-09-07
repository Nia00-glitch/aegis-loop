from src.infrastructure.extraction.crawler import (
    Crawl4AIAdapter,
)
from src.application.research.document_preparer import (
    DocumentPreparer,
)


def main():
    url = "https://www.anthropic.com/news"

    print("DOCUMENT PREPARATION PIPELINE CHECK")
    print("=" * 60)
    print(f"URL: {url}")

    crawler = Crawl4AIAdapter()
    preparer = DocumentPreparer()

    extracted_document = crawler.extract(url)

    if not extracted_document.success:
        print(f"Extraction error: {extracted_document.error}")
        raise RuntimeError("Extraction failed")

    prepared_document = preparer.prepare(
        extracted_document
    )

    print("\nEXTRACTION")
    print(f"Raw characters: {len(extracted_document.markdown)}")

    print("\nPREPARATION")
    print(
        f"Prepared characters: "
        f"{prepared_document.character_count}"
    )
    print(
        f"Word count: "
        f"{prepared_document.word_count}"
    )

    print("\nCONTENT PREVIEW")
    print("-" * 60)
    print(prepared_document.content[:1000])

    print("\n" + "=" * 60)
    print("DOCUMENT PREPARATION PIPELINE: PASSED")


if __name__ == "__main__":
    main()
