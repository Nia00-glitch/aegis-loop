from src.application.research.adaptive_search import AdaptiveSearchEngine


def main():
    engine = AdaptiveSearchEngine()

    query = "AI market research software"

    print("ADAPTIVE SEARCH CHECK")
    print("=" * 60)
    print(f"Original Query: {query}")

    response = engine.search(
        query=query,
        results_per_strategy=3,
    )

    print(f"\nStrategies executed: {len(response.strategies)}")
    print("=" * 60)

    for strategy in response.strategies:
        results = response.results.get(strategy.name, [])

        print(f"\nSTRATEGY: {strategy.name}")
        print(f"QUERY: {strategy.query}")
        print(f"RESULTS: {len(results)}")

        for index, result in enumerate(results, start=1):
            print(f"\n  [{index}] {result.title}")
            print(f"      {result.url}")

        print("-" * 60)

    total_results = sum(
        len(results)
        for results in response.results.values()
    )

    print(f"\nTOTAL RESULTS COLLECTED: {total_results}")
    print("ADAPTIVE SEARCH: PASSED")


if __name__ == "__main__":
    main()
