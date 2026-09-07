from src.infrastructure.extraction.crawler import Crawl4AIAdapter


def main():
    url = "https://www.anthropic.com/news"

    print("CRAWLER ADAPTER LIVE CHECK")
    print("=" * 60)
    print(f"URL: {url}")

    adapter = Crawl4AIAdapter()
    document = adapter.extract(url)

    print(f"\nSuccess: {document.success}")
    print(f"Extracted at: {document.extracted_at}")

    if not document.success:
        print(f"Error: {document.error}")
        raise RuntimeError("Crawler adapter failed")

    print(
        f"Extracted characters: "
        f"{len(document.markdown)}"
    )

    print("\nCONTENT PREVIEW")
    print("-" * 60)
    print(document.markdown[:1000])

    print("\n" + "=" * 60)
    print("CRAWLER ADAPTER LIVE TEST: PASSED")


if __name__ == "__main__":
    main()
