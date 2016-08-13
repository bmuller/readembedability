from operator import methodcaller
import logging

from readembedability.io import get_page
from readembedability.utils import URL
from readembedability.parsers.base import ParseResult
from readembedability.parsers.assets import ImageTypeParser, ImagesParser, PDFTypeParser, LastDitchMedia
from readembedability.parsers.oembed import OEmbedParser
from readembedability.parsers.sanitizers import ReadableLxmlParser, StandardsParser, SummarizingParser
from readembedability.parsers.sanitizers import LastDitchParser, FinalContentPass
from readembedability.parsers.custom import CustomParser
from readembedability.parsers.meta import AuthorParser, DatePublishedParser
from readembedability.parsers.newspaper import NewspaperParser

log = logging.getLogger(__name__)

PARSERS = [CustomParser, PDFTypeParser, ImageTypeParser, NewspaperParser, ImagesParser, OEmbedParser,
           StandardsParser, ReadableLxmlParser, LastDitchParser, LastDitchMedia, FinalContentPass,
           SummarizingParser, AuthorParser, DatePublishedParser]


async def getReadembedable(url):
    if not isinstance(url, URL):
        url = URL(url)

    result = ParseResult(url)
    page = await get_page(url)
    # this happens if we can't even fetch
    if page is None:
        log.error("Could not contact server for %s" % url)
        result.set('success', False)
        return result.to_dict()

    result.set('canonical_url', page.url)
    # this happens if we can contact server but not a 200
    if page.status != 200:
        log.err("Download of %s returned HTTP respond of %i" % (url, page.status))
        result.set('success', False)
        return result.to_dict()

    result.set('success', True, 4)
    for parser_class in PARSERS:
        parser = parser_class(page)
        result.set_parser_name(parser_class.__name__)
        result = await parser.enrich(result)
    return result
