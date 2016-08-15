from readability.readability import Document

from readembedability.parsers.html import sanitize_html
from readembedability.parsers.base import BaseParser


class ReadableLxmlParser(BaseParser):
    async def enrich(self, result):
        try:
            doc = Document(self.content, url=self.url)
            content = doc.summary(html_partial=True)
            sanitized = sanitize_html(content)
            result.setIfLonger('content', sanitized)
            result.setIfLonger('title', doc.short_title())
        # pylint: disable=bare-except
        except:
            pass
        return result
