from __future__ import annotations

from dataclasses import dataclass

from src.infrastructure.search.searxng_adapter import (
    SearchResult,
    SearXNGSearchAdapter,
)


@dataclass
class SearchStrategy:
    name: str
    query: str


@dataclass
class AdaptiveSearchResponse:
    original_query: str
    strategies: list[SearchStrategy]
    results: dict[str, list[SearchResult]]


class AdaptiveSearchEngine:
    def __init__(
        self,
        search_adapter: SearXNGSearchAdapter | None = None,
    ) -> None:
        self.search_adapter = (
            search_adapter
            or SearXNGSearchAdapter()
        )

    def build_strategies(
        self,
        query: str,
    ) -> list[SearchStrategy]:

        return [
            SearchStrategy(
                name="core",
                query=query,
            ),
            SearchStrategy(
                name="market_landscape",
                query=f"{query} competitors alternatives market",
            ),
            SearchStrategy(
                name="customer_pain",
                query=f"{query} problems complaints challenges",
            ),
            SearchStrategy(
                name="feature_discovery",
                query=f"{query} features capabilities",
            ),
            SearchStrategy(
                name="gaps_opportunities",
                query=f"{query} gaps unmet needs opportunities",
            ),
        ]

    def search(
        self,
        query: str,
        results_per_strategy: int = 5,
    ) -> AdaptiveSearchResponse:

        strategies = self.build_strategies(query)

        collected_results: dict[
            str,
            list[SearchResult],
        ] = {}

        for strategy in strategies:
            response = self.search_adapter.search(
                query=strategy.query,
                limit=results_per_strategy,
            )

            collected_results[
                strategy.name
            ] = response.results

        return AdaptiveSearchResponse(
            original_query=query,
            strategies=strategies,
            results=collected_results,
        )
