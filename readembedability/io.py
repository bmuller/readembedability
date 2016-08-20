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
    def __init__(self, response, maxsize=3000000):
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
        # use aiohttp to decode
        self.body = await self.response.text()

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

    def to_json(self):
        return json.loads(self.body)

    def __str__(self):
        return self.body


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
        with aiohttp.Timeout(timeout):
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(surl) as resp:
                    result = HTTPResponse(resp)
                    await result.process()
    except aiohttp.errors.ClientOSError as error:
        LOG.error("Error fetching %s: %s", url, error)
        result = None
    except asyncio.TimeoutError:
        LOG.error("Timeout reached for %s", url)
        result = None
    return result
