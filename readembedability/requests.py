from twisted.internet import defer

from readembedability.io import getPage
from readembedability.base import ParseResult
from readembedability.assets import ImageTypeParser, ImagesParser, PDFTypeParser, LastDitchMedia
from readembedability.oembed import OEmbedParser
from readembedability.sanitizers import ReadableLxmlParser
from readembedability.sanitizers import GooseParser
from readembedability.sanitizers import StandardsParser
from readembedability.sanitizers import SummarizingParser
from readembedability.sanitizers import LastDitchParser
from readembedability.sanitizers import FinalContentPass
from readembedability.custom import CustomParser
from readembedability.meta import AuthorParser
from readembedability.meta import DatePublishedParser


class ReadabedPage:
    """
    Readability + oembed = awesome.
    """
    parsers = [CustomParser, PDFTypeParser, ImageTypeParser, ImagesParser, OEmbedParser, StandardsParser,
               ReadableLxmlParser, GooseParser, LastDitchParser, LastDitchMedia, FinalContentPass, SummarizingParser,
               AuthorParser, DatePublishedParser]

    def __init__(self, url):
        self.url = url

    def empty(self):
        empty = ParseResult()
        empty.set('embed', False)
        empty.set('primary_image', None)
        empty.set('secondary_images', [])
        empty.set('content', None)
        empty.set('summary', None)
        empty.set('title', None)
        empty.set('author', None)
        empty.set('published_at', None)
        empty.set('keywords', [])
        empty.set('url', self.url, True)
        empty.set('canonical_url', None)
        return empty

    def fetch(self):
        return getPage(self.url).addCallbacks(self._fetch, lambda _: self.empty().jsonReady())

    def _fetch(self, page):
        result = self.empty()
        result.set('canonical_url', page.url)

        if page.status != 200:
            return result.jsonReady()

        parsers = [ K(page) for K in self.parsers ]
        d = self._tryParser(result, parsers[0], parsers[1:])
        return d.addCallback(self.logResult)

    def logResult(self, result):
        """
        Optionally - log result here.
        """
        return result.jsonReady()

    def _tryParser(self, result, parser, remaining):
        d = defer.maybeDeferred(parser.enrich, result)
        if len(remaining) > 0:
            d.addCallback(self._tryParser, remaining[0], remaining[1:])
        return d


def getReadembedable(url):
    return ReadabedPage(url).fetch()
