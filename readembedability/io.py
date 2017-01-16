import cgi
import json
import logging
import asyncio

import aiohttp

from readembedability.utils import URL
from readembedability import __version__

LOG = logging.getLogger(__name__)

FEED_CONTENT_TYPES = [
    "text/rss",
    "text/atom",
    "application/rss",
    "application/rss+xml",
    "text/xml",
    "application/xml"
]

IMAGE_CONTENT_TYPES = [
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/svg+xml"
]


class ResponseTooLargeError(Exception):
    """Response from HTTP request was too large."""
    pass


class HTTPResponse:
    def __init__(self, response, maxsize=5000000):
        """
        Param maxsize has a 3mb cutoff by default.
        """
        self.response = response
        self.maxsize = maxsize
        self.status = response.status
        self.url = response.url
        self.headers = {}
        self.body = None
        for key, value in response.raw_headers:
            self.headers[key.decode().lower()] = value.decode()

        self.content_type = None
        content_types = self.headers.get('content-type', None)
        if content_types:
            self.content_type, _ = cgi.parse_header(content_types)

    async def process(self):
        body = bytes()
        chunk = await self.response.content.read(1024)
        while chunk and len(body) < self.maxsize:
            body += chunk
            chunk = await self.response.content.read(1024)

        if not self.response.content.at_eof():
            raise ResponseTooLargeError

        # pylint: disable=protected-access
        self.response._content = body

        if self.is_binary():
            self.body = body
        else:
            # Until https://github.com/KeepSafe/aiohttp/pull/1542 is accepted
            # and released...
            encoding = self.response._get_encoding()
            self.body = self.response._content.decode(encoding, 'ignore')

    def is_binary(self):
        """
        Return true if this is a non-text response (image, pdf, etc)
        """
        nonbins = [
            self.is_html(),
            self.is_feed(),
            self.is_text(),
            self.is_json(),
            self.is_javascript()
        ]
        return not any(nonbins)

    def is_html(self):
        return self.content_type == "text/html"

    def is_feed(self):
        return self.content_type in FEED_CONTENT_TYPES

    def is_image(self):
        return self.content_type in IMAGE_CONTENT_TYPES

    def is_text(self):
        return self.content_type == "text/plain"

    def is_pdf(self):
        return self.content_type == "application/pdf"

    def is_json(self):
        return self.content_type == "application/json"

    def is_javascript(self):
        # first is obsolete, but these publishers...
        jses = ["text/javascript", "application/javascript"]
        return self.content_type in jses

    def to_json(self):
        return json.loads(self.body)

    def __str__(self):
        return self.body

    def empty_body(self):
        return (not self.body) or self.body.strip() == ""


async def get_page(url, headers=None, timeout=10, mobile=False):
    headers = headers or {}
    if 'User-Agent' not in headers:
        usera = "readembedability/%s" % __version__
        if mobile:
            usera += " (Mobile)"
        headers['User-Agent'] = usera

    if not isinstance(url, URL):
        url = URL(url)
    surl = str(url)

    LOG.info("Attempting to download %s", url)
    try:
        kwargs = {
            'connector': aiohttp.TCPConnector(verify_ssl=False),
            'headers': headers
        }
        async with aiohttp.ClientSession(**kwargs) as session:
            async with session.get(surl, timeout=timeout) as resp:
                result = HTTPResponse(resp)
                await result.process()
    except asyncio.CancelledError as error:
        LOG.error("Client error fetching %s: %s", url, error)
        result = None
    except aiohttp.errors.ClientOSError as error:
        LOG.error("Error fetching %s: %s", url, error)
        result = None
    except asyncio.TimeoutError:
        LOG.error("Timeout reached for %s", url)
        result = None
    return result
