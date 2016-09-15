import logging

from readembedability.io import get_page
from readembedability.utils import URL
from readembedability.parsers.result import ParseResult
from readembedability.parsers import assets
from readembedability.parsers import oembed
from readembedability.parsers import content
from readembedability.parsers import meta
from readembedability.parsers import custom
from readembedability.parsers import text

LOG = logging.getLogger(__name__)

PARSERS = [
    custom.CustomParser,
    content.AMPParser,
    assets.PDFTypeParser,
    assets.ImageTypeParser,
    meta.SocialParser,
    content.NewspaperParser,
    assets.ImagesParser,
    oembed.OEmbedParser,
    meta.StandardsParser,
    meta.LDJSONParser,
    content.ReadableLxmlParser,
    content.LastDitchParser,
    assets.LastDitchMedia,
    content.FinalContentPass,
    text.SummarizingParser,
    meta.AuthorParser,
    meta.DatePublishedParser
]


async def get_readembedable_result(url, **kwargs):
    if not isinstance(url, URL):
        url = URL(url)

    result = ParseResult(url)
    page = await get_page(url, **kwargs)

    # this happens if we can't even fetch
    if page is None:
        LOG.error("Could not contact server for %s", url)
        return (None, result)

    result.set('canonical_url', page.url)
    # this happens if we can contact server but not a 200
    if page.status != 200:
        LOG.error("%s fetch returned HTTP code %i", url, page.status)
        return (None, result)

    result.set('success', True)
    for parser_class in PARSERS:
        parser = parser_class(page)
        result.set_parser_name(parser_class.__name__)
        result = await parser.enrich(result)
        # allow short circuiting
        if not result.get('success'):
            return (page, result)
    return (page, result)


async def get_readembedable(url, **kwargs):
    _, result = await get_readembedable_result(url, **kwargs)
    return result.to_dict()
