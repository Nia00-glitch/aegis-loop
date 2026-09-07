import asyncio

from crawl4ai import AsyncWebCrawler


async def main():
    url = "https://www.anthropic.com/news"

    print("CRAWL4AI LIVE EXTRACTION CHECK")
    print("=" * 60)
    print(f"URL: {url}")

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

    print(f"\nSuccess: {result.success}")

    if not result.success:
        print(f"Error: {result.error_message}")
        raise RuntimeError("Crawl failed")

    content = result.markdown

    print(f"Extracted characters: {len(content)}")
    print("\nCONTENT PREVIEW")
    print("-" * 60)
    print(content[:1000])

    print("\n" + "=" * 60)
    print("CRAWL4AI LIVE EXTRACTION: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
