from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from src.application.research.result_normalizer import (
    NormalizedSource,
)


@dataclass
class ScoredSource:
    source: NormalizedSource
    score: float
    authority_score: float
    source_type: str
    reasons: list[str]


class SourceQualityScorer:
    OFFICIAL_DOMAINS = (
        ".gov",
        ".gov.in",
        ".edu",
        ".ac.in",
    )

    RESEARCH_DOMAINS = (
        "arxiv.org",
        "papers.ssrn.com",
        "nature.com",
        "science.org",
        "ieee.org",
        "acm.org",
        "springer.com",
        "sciencedirect.com",
        "frontiersin.org",
        "plos.org",
    )

    REPUTABLE_DOMAINS = (
        "reuters.com",
        "bloomberg.com",
        "ft.com",
        "wsj.com",
        "economist.com",
        "mckinsey.com",
        "bcg.com",
        "bain.com",
        "gartner.com",
        "forrester.com",
        "statista.com",
    )

    COMMUNITY_DOMAINS = (
        "reddit.com",
        "quora.com",
        "news.ycombinator.com",
        "stackoverflow.com",
        "github.com",
    )

    def classify_source(
        self,
        domain: str,
    ) -> tuple[str, float, str]:

        domain = domain.lower()

        if domain.endswith(self.OFFICIAL_DOMAINS):
            return (
                "official_or_institutional",
                0.95,
                "Official or institutional domain",
            )

        if any(
            research_domain in domain
            for research_domain in self.RESEARCH_DOMAINS
        ):
            return (
                "academic_or_research",
                0.90,
                "Recognized academic or research publisher",
            )

        if any(
            reputable_domain in domain
            for reputable_domain in self.REPUTABLE_DOMAINS
        ):
            return (
                "reputable_publisher",
                0.85,
                "Established research, business, or news publisher",
            )

        if any(
            community_domain in domain
            for community_domain in self.COMMUNITY_DOMAINS
        ):
            return (
                "community_or_discussion",
                0.55,
                "Community or discussion source",
            )

        return (
            "general_web",
            0.50,
            "General web source",
        )

    def score_source(
        self,
        source: NormalizedSource,
    ) -> ScoredSource:

        source_type, authority_score, reason = (
            self.classify_source(source.domain)
        )

        score = authority_score

        reasons = [reason]

        strategy_count = len(source.strategies)

        if strategy_count >= 3:
            score += 0.05
            reasons.append(
                "Discovered across multiple search strategies"
            )
        elif strategy_count == 2:
            score += 0.02
            reasons.append(
                "Discovered by two search strategies"
            )

        score = min(score, 1.0)

        return ScoredSource(
            source=source,
            score=round(score, 3),
            authority_score=authority_score,
            source_type=source_type,
            reasons=reasons,
        )

    def score_sources(
        self,
        sources: list[NormalizedSource],
    ) -> list[ScoredSource]:

        scored_sources = [
            self.score_source(source)
            for source in sources
        ]

        return sorted(
            scored_sources,
            key=lambda item: item.score,
            reverse=True,
        )
