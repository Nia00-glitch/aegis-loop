from __future__ import annotations

import re
from dataclasses import dataclass

from src.infrastructure.extraction.crawler import ExtractedDocument


@dataclass
class PreparedDocument:
    url: str
    content: str
    character_count: int
    word_count: int


class DocumentPreparer:
    def clean_markdown(
        self,
        markdown: str,
    ) -> str:
        content = markdown

        # Remove excessive blank lines
        content = re.sub(
            r"\n{3,}",
            "\n\n",
            content,
        )

        # Remove repeated spaces/tabs
        content = re.sub(
            r"[ \t]+",
            " ",
            content,
        )

        # Remove empty markdown links/images
        content = re.sub(
            r"!\[\]\([^)]+\)",
            "",
            content,
        )

        content = re.sub(
            r"\[\]\([^)]+\)",
            "",
            content,
        )

        return content.strip()

    def prepare(
        self,
        document: ExtractedDocument,
    ) -> PreparedDocument:

        if not document.success:
            raise ValueError(
                "Cannot prepare an unsuccessful extraction"
            )

        content = self.clean_markdown(
            document.markdown
        )

        return PreparedDocument(
            url=document.url,
            content=content,
            character_count=len(content),
            word_count=len(content.split()),
        )
