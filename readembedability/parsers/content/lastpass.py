from readability.readability import Document

from readembedability.parsers.html import sanitize_html, SmartHTMLDocument
from readembedability.parsers.base import BaseParser
from readembedability.parsers.html import SmartElem


class LastDitchParser(BaseParser):
    """
    If we've gotten nothing so far, try something that may be stupid.
    """
    async def enrich(self, result):
        if not self.soup:
            return result

        result.set('title', self.soup.title.string, 0, 'textlength')

        if result.has('content'):
            return result

        parts = []
        for txt in self.soup.find_all("noscript"):
            if txt.string is not None:
                parts.append(txt.string)
        html = " ".join(parts).strip()
        if not html:
            html = self.soup.all_text()

        try:
            doc = Document(html, url=self.url)
            content = doc.summary(html_partial=True)
            result.set('content', sanitize_html(content))
        # pylint: disable=bare-except
        except:
            pass

        return result


class FinalContentPass(BaseParser):
    def __init__(self, result):
        super().__init__(result)
        self.cbs = None

    async def enrich(self, result):
        """
        1) remove title from content if it's the first item
        2) remove all links that just contain social crap
        """
        if not result.has('content'):
            return result

        self.cbs = SmartHTMLDocument(result.get('content'))
        result = self.remove_title(result)
        result = self.remove_social_links(result)
        return result

    # pylint: disable=no-self-use
    def remove_social_links(self, result):
        """
        Don't do anything here.  We should actually be checking the href
        on the a's to make sure they're share links.
        """
        return result
        # verboten = ['twitter', 'facebook', 'google', 'google+', 'pinterest']
        # for a in self.cbs.find_all('a'):
        #     txt = self.cbs.getText(a).strip().lower().replace(' ', '')
        #     if txt in verboten:
        #         a.extract()
        # result.set('content', str(self.cbs), 3)
        # return result

    def remove_title(self, result):
        title = result.get('title')
        if title is not None and result.get('content') is not None:
            title = title.lower().strip()
            tnodes = self.cbs.get_text_nodes()
            # if first text node is title, remove it
            if tnodes and tnodes[0].lower().strip() == title:
                node = tnodes[0]
                content = SmartElem(node.parent).all_text().lower()
                while node.parent is not None and content == title:
                    node = node.parent
                    content = SmartElem(node.parent).all_text().lower()
                node.extract()
                result.set('content', str(self.cbs), 3)
        return result
