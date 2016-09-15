from robostrippy.utils import absolute_url

from readembedability.parsers.html import SmartHTMLDocument


class BaseParser:
    def __init__(self, response):
        self.response = response
        self.url = response.url
        self.content = response.body
        self.soup = None

        if response.is_text():
            tbody = '<html><body><pre>%s</pre></body></html>'
            self.content = tbody % response.body

        if not response.is_binary():
            if self.content and "html>" in self.content:
                self.soup = SmartHTMLDocument(self.content)

    def absoluteify(self, path):
        return absolute_url(self.url, path)

    async def enrich(self, result):
        """
        Should enrich given ParseResult
        """
        raise NotImplementedError
