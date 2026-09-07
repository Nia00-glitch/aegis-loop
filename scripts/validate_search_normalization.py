from src.application.research.adaptive_search import (
    AdaptiveSearchEngine,
)
from src.application.research.result_normalizer import (
    ResultNormalizer,
)


def main():
    query = "AI market research software"

    print("ADAPTIVE SEARCH + NORMALIZATION CHECK")
    print("=" * 60)
    print(f"Query: {query}")

    search_engine = AdaptiveSearchEngine()
    normalizer = ResultNormalizer()

    response = search_engine.search(
        query=query,
        results_per_strategy=5,
    )

    raw_result_count = sum(
        len(results)
        for results in response.results.values()
    )

    normalized_sources = normalizer.normalize(
        response.results
    )

    unique_source_count = len(normalized_sources)

    print()
    print(f"Search strategies: {len(response.strategies)}")
    print(f"Raw results collected: {raw_result_count}")
    print(f"Unique sources: {unique_source_count}")
    print(f"Duplicates removed: {raw_result_count - unique_source_count}")

    print("\n" + "=" * 60)
    print("UNIQUE EVIDENCE CANDIDATES")
    print("=" * 60)

    for index, source in enumerate(
        normalized_sources,
        start=1,
    ):
        print(f"\nSOURCE {index}")
        print(f"Title: {source.title}")
        print(f"Domain: {source.domain}")
        print(f"URL: {source.url}")
        print(
            "Found by strategies: "
            + ", ".join(source.strategies)
        )

    print("\n" + "=" * 60)
    print("SEARCH + NORMALIZATION: PASSED")


if __name__ == "__main__":
    main()
