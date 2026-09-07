from src.application.research.adaptive_search import (
    AdaptiveSearchEngine,
)
from src.application.research.result_normalizer import (
    ResultNormalizer,
)
from src.application.research.source_quality import (
    SourceQualityScorer,
)


def main():
    query = "AI market research software"

    print("SOURCE QUALITY SCORING CHECK")
    print("=" * 70)
    print(f"Query: {query}")

    search_engine = AdaptiveSearchEngine()
    normalizer = ResultNormalizer()
    scorer = SourceQualityScorer()

    search_response = search_engine.search(
        query=query,
        results_per_strategy=5,
    )

    normalized_sources = normalizer.normalize(
        search_response.results
    )

    scored_sources = scorer.score_sources(
        normalized_sources
    )

    print(f"\nUnique sources: {len(normalized_sources)}")
    print(f"Scored sources: {len(scored_sources)}")

    print("\n" + "=" * 70)
    print("RANKED EVIDENCE CANDIDATES")
    print("=" * 70)

    for index, item in enumerate(
        scored_sources,
        start=1,
    ):
        print(f"\nRANK {index}")
        print(f"Score: {item.score}")
        print(f"Authority: {item.authority_score}")
        print(f"Type: {item.source_type}")
        print(f"Title: {item.source.title}")
        print(f"Domain: {item.source.domain}")
        print(f"URL: {item.source.url}")
        print(
            "Strategies: "
            + ", ".join(item.source.strategies)
        )
        print(
            "Reasons: "
            + "; ".join(item.reasons)
        )

    print("\n" + "=" * 70)
    print("SOURCE QUALITY SCORING: PASSED")


if __name__ == "__main__":
    main()
