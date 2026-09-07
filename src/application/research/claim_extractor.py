from __future__ import annotations

import hashlib
import re

from src.application.research.claim_models import (
    AtomicClaim,
    ClaimExtractionResult,
    ClaimType,
)
from src.application.research.document_chunker import (
    DocumentChunk,
)


class ClaimExtractor:
    MIN_CLAIM_LENGTH = 10

    def _split_sentences(
        self,
        text: str,
    ) -> list[str]:
        parts = re.split(
            r"(?<=[.!?])\s+",
            text.strip(),
        )

        return [
            part.strip()
            for part in parts
            if len(part.strip()) >= self.MIN_CLAIM_LENGTH
        ]

    def _build_claim_id(
        self,
        chunk: DocumentChunk,
        claim_text: str,
    ) -> str:
        raw_value = (
            f"{chunk.chunk_id}:"
            f"{claim_text}"
        )

        digest = hashlib.sha256(
            raw_value.encode("utf-8")
        ).hexdigest()[:16]

        return f"claim-{digest}"

    def _classify_claim(
        self,
        text: str,
    ) -> ClaimType:
        lowered = text.lower()

        if any(
            marker in lowered
            for marker in [
                "$",
                "%",
                "million",
                "billion",
                "thousand",
                "revenue",
                "growth",
            ]
        ):
            return ClaimType.METRIC

        if any(
            marker in lowered
            for marker in [
                "feature",
                "launched",
                "launch",
                "product",
                "platform",
            ]
        ):
            return ClaimType.FEATURE

        if any(
            marker in lowered
            for marker in [
                "market",
                "industry",
                "customers",
                "users",
                "demand",
            ]
        ):
            return ClaimType.MARKET

        if any(
            marker in lowered
            for marker in [
                "competitor",
                "compared",
                "alternative",
                "versus",
                "vs.",
            ]
        ):
            return ClaimType.COMPETITIVE

        return ClaimType.FACT

    def extract(
        self,
        chunk: DocumentChunk,
    ) -> ClaimExtractionResult:
        sentences = self._split_sentences(
            chunk.content
        )

        claims = [
            AtomicClaim(
                claim_id=self._build_claim_id(
                    chunk,
                    sentence,
                ),
                text=sentence,
                claim_type=self._classify_claim(
                    sentence
                ),
                source_chunk_id=chunk.chunk_id,
                source_url=chunk.document_url,
                supporting_text=sentence,
            )
            for sentence in sentences
        ]

        return ClaimExtractionResult(
            source_chunk_id=chunk.chunk_id,
            claims=claims,
        )

    def extract_many(
        self,
        chunks: list[DocumentChunk],
    ) -> list[ClaimExtractionResult]:
        return [
            self.extract(chunk)
            for chunk in chunks
        ]
