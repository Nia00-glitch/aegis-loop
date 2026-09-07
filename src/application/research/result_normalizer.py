from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

from src.infrastructure.search.searxng_adapter import SearchResult


@dataclass
class NormalizedSource:
    title: str
    url: str
    content: str
    domain: str
    strategies: list[str]


class ResultNormalizer:
    @staticmethod
    def normalize_url(url: str) -> str:
        parsed = urlparse(url)

        normalized = parsed._replace(
            scheme=parsed.scheme.lower(),
            netloc=parsed.netloc.lower(),
            fragment="",
            query="",
        )

        return urlunparse(normalized).rstrip("/")

    @staticmethod
    def get_domain(url: str) -> str:
        return urlparse(url).netloc.lower()

    def normalize(
        self,
        results: dict[str, list[SearchResult]],
    ) -> list[NormalizedSource]:

        unique_sources: dict[str, NormalizedSource] = {}

        for strategy_name, strategy_results in results.items():

            for result in strategy_results:

                if not result.url:
                    continue

                normalized_url = self.normalize_url(
                    result.url
                )

                if normalized_url in unique_sources:

                    existing = unique_sources[
                        normalized_url
                    ]

                    if strategy_name not in existing.strategies:
                        existing.strategies.append(
                            strategy_name
                        )

                    continue

                unique_sources[normalized_url] = (
                    NormalizedSource(
                        title=result.title,
                        url=normalized_url,
                        content=result.content,
                        domain=self.get_domain(
                            normalized_url
                        ),
                        strategies=[strategy_name],
                    )
                )

        return list(unique_sources.values())
