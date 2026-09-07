from __future__ import annotations

import re
from dataclasses import dataclass

from src.application.research.document_preparer import (
    PreparedDocument,
)


@dataclass
class DocumentChunk:
    chunk_id: str
    document_url: str
    chunk_index: int
    content: str
    character_count: int


class DocumentChunker:
    def __init__(
        self,
        chunk_size: int = 2000,
        overlap: int = 200,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than 0"
            )

        if overlap < 0:
            raise ValueError(
                "overlap cannot be negative"
            )

        if overlap >= chunk_size:
            raise ValueError(
                "overlap must be smaller than chunk_size"
            )

        self.chunk_size = chunk_size
        self.overlap = overlap

    def _split_large_block(
        self,
        block: str,
    ) -> list[str]:
        parts: list[str] = []

        start = 0

        while start < len(block):
            end = min(
                start + self.chunk_size,
                len(block),
            )

            if end < len(block):
                boundary = block.rfind(
                    " ",
                    start,
                    end,
                )

                if boundary > start:
                    end = boundary

            part = block[start:end].strip()

            if part:
                parts.append(part)

            if end >= len(block):
                break

            start = end

        return parts

    def _get_overlap_text(
        self,
        content: str,
    ) -> str:
        if self.overlap == 0:
            return ""

        if len(content) <= self.overlap:
            return content

        overlap_text = content[-self.overlap:]

        boundary = overlap_text.find(" ")

        if boundary != -1:
            overlap_text = overlap_text[
                boundary + 1:
            ]

        return overlap_text.strip()

    def chunk(
        self,
        document: PreparedDocument,
    ) -> list[DocumentChunk]:

        content = document.content.strip()

        if not content:
            return []

        blocks = [
            block.strip()
            for block in re.split(
                r"\n\s*\n",
                content,
            )
            if block.strip()
        ]

        normalized_blocks: list[str] = []

        for block in blocks:
            if len(block) <= self.chunk_size:
                normalized_blocks.append(block)
            else:
                normalized_blocks.extend(
                    self._split_large_block(block)
                )

        chunk_texts: list[str] = []
        current = ""

        for block in normalized_blocks:
            if not current:
                current = block
                continue

            candidate = (
                f"{current}\n\n{block}"
            )

            if len(candidate) <= self.chunk_size:
                current = candidate
                continue

            chunk_texts.append(current)

            overlap_text = self._get_overlap_text(
                current
            )

            current = (
                f"{overlap_text}\n\n{block}".strip()
                if overlap_text
                else block
            )

        if current:
            chunk_texts.append(current)

        return [
            DocumentChunk(
                chunk_id=(
                    f"{document.url}"
                    f"#chunk-{index}"
                ),
                document_url=document.url,
                chunk_index=index,
                content=chunk_text,
                character_count=len(chunk_text),
            )
            for index, chunk_text
            in enumerate(chunk_texts)
        ]
