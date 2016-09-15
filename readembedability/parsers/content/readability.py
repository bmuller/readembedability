from readability.readability import Document

from readembedability.parsers.html import sanitize_html
from readembedability.parsers.base import BaseParser


class ReadableLxmlParser(BaseParser):
    async def enrich(self, result):
        doc = Document(self.content, url=self.url)
        content = doc.summary(html_partial=True)
        result.set('content', sanitize_html(content), 2, 'textquality')
        result.set('title', doc.short_title(), 1, 'textlength')
        return result
