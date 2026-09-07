from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.research.claim_models import (
    ClaimExtractionResult,
)
from src.application.research.document_chunker import (
    DocumentChunk,
)


class SemanticClaimExtractor(ABC):
    @abstractmethod
    def extract(
        self,
        chunk: DocumentChunk,
    ) -> ClaimExtractionResult:
        raise NotImplementedError
