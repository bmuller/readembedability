import codecs
import re
import cgi
import json

from twisted.web.http import PotentialDataLoss

import treq

from utils import URL

PROXY_DOMAINS = [ re.compile(regex, re.IGNORECASE) for regex in [ "https?://news\.ycombinator\.com" ] ]

RE_META_TAG = re.compile("""<meta(?!\s*(?:name|value)\s*=)[^>]*?charset\s*=[\s"']*([^\s"'/>]*)""")


class HTTPResponse(object):
    def __init__(self, maxsize=3000000):
        """
        3mb cutoff
        """
        self.body = ""
        self._maxsize = maxsize

    def process(self, response, forceUrl=None):
        self.status = response.code
        self.response_headers = response.headers
        self.url = forceUrl or response.request.absoluteURI
        d = treq.collect(response, self._collect)
        return d.addCallback(lambda _: self._decode())

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

    def _decode(self):
        encoding = self._get_encoding()
        if encoding is None:
            self.body = unicode(self.body, 'utf-8', errors='replace')
            return self
        try:
            codecs.lookup(encoding)
            self.body = unicode(self.body, encoding)
        except LookupError:
            self.body = unicode(self.body, 'utf-8', errors='replace')
        return self

    def _get_encoding(self):
        encoding = None
        self.content_type = None
        content_types = self.response_headers.getRawHeaders('content-type')
        if content_types is not None:
            self.content_type, params = cgi.parse_header(content_types[-1])
            if 'charset' in params:
                encoding = params.get('charset').strip("'\"")
        if encoding is None:
            m = RE_META_TAG.search(self.body)
            if m is not None:
                encoding = m.group(1)

        # sometimes, the encoding is just the iso number, but codecs can't resolve
        # it unless it starts w/ iso
        if encoding is not None and len(encoding) > 0 and encoding[0].isdigit():
            encoding = "iso-" + encoding

        # this space char is a sure sign of 8859
        if encoding is None and '\xa0' in self.body:
            encoding = 'iso-8859-1'

        return encoding

    def _collect(self, data):
        self.body += data
        if len(self.body) > self._maxsize:
            raise PotentialDataLoss

_global_pool = [None]


def set_global_pool(pool):
    _global_pool[0] = pool


def getPage(url, headers=None):
    headers = headers or {}
    # headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 "
    # headers['User-Agent'] += "(KHTML, like Gecko) Chrome/30.0.1599.17 Safari/537.36"
    headers['User-Agent'] = "durch.io/0.1"
    pool = _global_pool[0]

    c = HTTPResponse()
    for regex in PROXY_DOMAINS:
        if regex.match(url) is not None:
            purl = URL("http://www.gmodules.com/ig/proxy?").setParam('url', url)
            return treq.get(str(purl), headers=headers, timeout=10, pool=pool).addCallback(c.process, url)

    url = URL(url)
    if url.startswith("http://www.google.com/url?") and url.getParam('url') is not None:
        url = URL(url.getParam('url'))

    return treq.get(str(url), headers=headers, timeout=10, pool=pool).addCallback(c.process)
