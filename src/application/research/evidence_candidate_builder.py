from __future__ import annotations

import hashlib

from src.application.research.document_chunker import (
    DocumentChunk,
)
from src.application.research.evidence_models import (
    EvidenceCandidate,
    EvidenceStatus,
)


class EvidenceCandidateBuilder:
    def _build_evidence_id(
        self,
        chunk: DocumentChunk,
    ) -> str:
        raw_value = (
            f"{chunk.chunk_id}:"
            f"{chunk.content}"
        )

        digest = hashlib.sha256(
            raw_value.encode("utf-8")
        ).hexdigest()[:16]

        return f"evidence-{digest}"

    def build(
        self,
        chunk: DocumentChunk,
    ) -> EvidenceCandidate:
        return EvidenceCandidate(
            evidence_id=self._build_evidence_id(chunk),
            claim=chunk.content,
            chunk_id=chunk.chunk_id,
            source_url=chunk.document_url,
            supporting_text=chunk.content,
            status=EvidenceStatus.CANDIDATE,
        )

    def build_many(
        self,
        chunks: list[DocumentChunk],
    ) -> list[EvidenceCandidate]:
        return [
            self.build(chunk)
            for chunk in chunks
        ]
