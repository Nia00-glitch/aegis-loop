from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from src.core.config import settings


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    engine: str | None = None
    category: str | None = None
    score: float | None = None


@dataclass
class SearchResponse:
    query: str
    number_of_results: int
    results: list[SearchResult]


class SearXNGSearchAdapter:
    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.base_url = (
            base_url
            or settings.searxng_base_url
        ).rstrip("/")

        self.timeout_seconds = timeout_seconds

    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> SearchResponse:

        params = {
            "q": query,
            "format": "json",
        }

        response = httpx.get(
            f"{self.base_url}/search",
            params=params,
            timeout=self.timeout_seconds,
        )

        response.raise_for_status()

        data: dict[str, Any] = response.json()

        raw_results = data.get("results", [])[:limit]

        results = [
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("content", ""),
                engine=item.get("engine"),
                category=item.get("category"),
                score=item.get("score"),
            )
            for item in raw_results
        ]

        return SearchResponse(
            query=data.get("query", query),
            number_of_results=data.get(
                "number_of_results",
                len(results),
            ),
            results=results,
        )
