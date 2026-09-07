from src.infrastructure.search.searxng_adapter import SearXNGSearchAdapter


def main():
    adapter = SearXNGSearchAdapter()

    print("SEARXNG SEARCH ADAPTER CHECK")
    print("=" * 50)

    response = adapter.search(
        query="AI market research software",
        limit=5,
    )

    print(f"Query: {response.query}")
    print(f"Total results: {response.number_of_results}")
    print(f"Returned results: {len(response.results)}")

    print("=" * 50)

    for index, result in enumerate(response.results, start=1):
        print(f"\nRESULT {index}")
        print(f"Title: {result.title}")
        print(f"URL: {result.url}")
        print(f"Engine: {result.engine}")
        print(f"Content: {result.content[:200]}")

    print("\n" + "=" * 50)
    print("SEARXNG SEARCH ADAPTER: PASSED")


if __name__ == "__main__":
    main()
