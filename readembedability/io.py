import cgi
import json
import logging
import aiohttp
import asyncio

from readembedability.utils import URL
from readembedability import __version__

log = logging.getLogger(__name__)


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
        self.status = response.status
        self.url = response.url        
        self.headers = {}
        for key, value in response.raw_headers:
            self.headers[key.decode().lower()] = value.decode()
        self.content_type = None
        content_types = self.headers.get('content-type', None)
        if content_types is not None:
            self.content_type, _ = cgi.parse_header(content_types)

    async def process(self):
        body = bytes()
        chunk = await self.response.content.read(1024)
        while chunk and len(body) < self.maxsize:
            body += chunk
            chunk = await self.response.content.read(1024)

        if not self.response.content.at_eof():
            raise ResponseTooLargeError

        self.response._content = body
        # use aiohttp to decode
        self.body = await self.response.text()
        

    def isHTML(self):
        return self.content_type == "text/html"

    def isFeed(self):
        feeds = [ "text/rss", "text/atom", "application/rss", "application/rss+xml", "text/xml", "application/xml" ]
        return self.content_type in feeds

    def isImage(self):
        ctypes = [ "image/gif", "image/jpeg", "image/png", "image/svg+xml" ]
        return self.content_type in ctypes

    def isText(self):
        ctypes = ["text/plain"]
        return self.content_type in ctypes

    def toJSON(self):
        return json.loads(self.body)

    def __str__(self):
        return self.body


async def get_page(url, headers=None, timeout=10):
    headers = headers or {}
    headers['User-Agent'] = "readembedability/%s" % __version__
    #headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'

    if not isinstance(url, URL):
        url = URL(url)
    surl = str(url)

    log.info("Attempting to download %s" % url)
    try:
        with aiohttp.Timeout(timeout):
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(surl) as resp:
                    result = HTTPResponse(resp)
                    await result.process()
    except aiohttp.errors.ClientOSError as e:
        log.error("Error fetching %s: %s" % (url, e))
        result = None
    except asyncio.TimeoutError:
        log.error("Timeout reached for %s" % url)
        result = None
    return result
