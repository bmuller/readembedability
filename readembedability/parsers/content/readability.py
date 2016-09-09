from readability.readability import Document

from readembedability.parsers.html import sanitize_html
from readembedability.parsers.base import BaseParser


class ReadableLxmlParser(BaseParser):
    async def enrich(self, result):
        doc = Document(self.content, url=self.url)
        content = doc.summary(html_partial=True)
        result.set_if_longer('content', sanitize_html(content))
        result.set_if_longer('title', doc.short_title())
        return result
