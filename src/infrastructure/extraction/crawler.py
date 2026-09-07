from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from crawl4ai import AsyncWebCrawler


@dataclass
class ExtractedDocument:
    url: str
    markdown: str
    success: bool
    error: str | None
    extracted_at: datetime


class Crawl4AIAdapter:
    async def extract_async(
        self,
        url: str,
    ) -> ExtractedDocument:

        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)

            if not result.success:
                return ExtractedDocument(
                    url=url,
                    markdown="",
                    success=False,
                    error=result.error_message,
                    extracted_at=datetime.now(
                        timezone.utc
                    ),
                )

            return ExtractedDocument(
                url=url,
                markdown=result.markdown or "",
                success=True,
                error=None,
                extracted_at=datetime.now(
                    timezone.utc
                ),
            )

        except Exception as exc:
            return ExtractedDocument(
                url=url,
                markdown="",
                success=False,
                error=str(exc),
                extracted_at=datetime.now(
                    timezone.utc
                ),
            )

    def extract(
        self,
        url: str,
    ) -> ExtractedDocument:

        return asyncio.run(
            self.extract_async(url)
        )
