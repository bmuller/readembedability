from operator import methodcaller

from twisted.internet import defer
from twisted.python import log

from readembedability.io import getPage
from readembedability.parsers.base import ParseResult
from readembedability.parsers.assets import ImageTypeParser, ImagesParser, PDFTypeParser, LastDitchMedia
from readembedability.parsers.oembed import OEmbedParser
from readembedability.parsers.sanitizers import ReadableLxmlParser, GooseParser, StandardsParser, SummarizingParser
from readembedability.parsers.sanitizers import LastDitchParser, FinalContentPass
from readembedability.parsers.custom import CustomParser
from readembedability.parsers.meta import AuthorParser, DatePublishedParser


class ReadabedPage:
    """
    Readability + oembed = awesome.
    """
    parsers = [CustomParser, PDFTypeParser, ImageTypeParser, ImagesParser, OEmbedParser, StandardsParser,
               ReadableLxmlParser, GooseParser, LastDitchParser, LastDitchMedia, FinalContentPass, SummarizingParser,
               AuthorParser, DatePublishedParser]

    def __init__(self, url, debug=False):
        self.url = url
        self.debug = debug

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
        return getPage(self.url).addCallbacks(self._fetch, self.error)

    def error(self, error):
        log.err("Issue fetching %s" % self.url)
        log.err(error)
        empty = self.empty()
        empty.set('success', False)
        return empty.jsonReady()

    def _fetch(self, page):
        result = self.empty()
        result.set('canonical_url', page.url)

        if page.status != 200:
            log.err("Download of %s returned HTTP respond of %i" % (self.url, page.status))
            result.set('success', False)
            return result.jsonReady()

        result.set('success', True)
        parsers = [ K(page) for K in self.parsers ]
        d = self._tryParser(result, parsers[0], parsers[1:])
        return d.addCallback(methodcaller('jsonReady'))

    def debugResult(self, result, parser):
        log.msg("Result of %s:\n%s" % (parser.__class__.__name__, result))
        return defer.succeed(result)

    def _tryParser(self, result, parser, remaining):
        d = defer.maybeDeferred(parser.enrich, result)
        if self.debug:
            d = d.addCallback(self.debugResult, parser)
        if len(remaining) > 0:
            d.addCallback(self._tryParser, remaining[0], remaining[1:])
        return d


def getReadembedable(url, debug=False):
    return ReadabedPage(url, debug).fetch()
