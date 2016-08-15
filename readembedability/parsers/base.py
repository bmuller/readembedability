from collections import defaultdict

from robostrippy.utils import absolute_url

from readembedability.parsers.html import SmartHTMLDocument


class ParseResult:
    def __init__(self, url):
        self.props = {}

        # this is used for logging
        self.current_parser = None
        self.log = defaultdict(list)

        self.set('url', str(url), 4)
        self.set('embed', False)
        self.set('primary_image', None)
        self.set('secondary_images', [])
        self.set('content', None)
        self.set('summary', None)
        self.set('title', None)
        self.set('subtitle', None)
        self.set('authors', [])
        self.set('published_at', None)
        self.set('keywords', [])
        self.set('canonical_url', None)

    def set_parser_name(self, name):
        self.current_parser = name

    def set(self, prop, value, confidence=0):
        """
        Confidences:
          0 A guess
          1 Fairly sure
          2 Mostly sure
          3 Sure
          4 Max.  Bet your life.
        """
        confidence = min(confidence, 4)
        # log this for later debugging
        if self.current_parser:
            self.log[prop].append((self.current_parser, value, confidence))
        if prop in self.props and confidence < self.props[prop][1]:
            return
        self.props[prop] = (value, confidence)
        return self

    def has(self, prop):
        value = self.get(prop)
        return value is not None and len(value) > 0

    def add(self, prop, items, confidence=None, unique=True):
        """
        If confidence is None, then the current value will be used if items
        already exist (and the default for the set method if not)
        """
        if prop not in self:
            values = list(set(items)) if unique else items
            if confidence is None:
                return self.set(prop, values)
            return self.set(prop, values, confidence)

        value, exconf = self.props[prop]
        value += items
        value = list(set(value)) if unique else value
        nconf = exconf if confidence is None else confidence
        return self.set(prop, value, nconf)

    def set_if_longer(self, prop, value, confidence=0):
        if value is not None:
            if self.get(prop) is None or len(value) > len(self.get(prop, "")):
                return self.set(prop, value, confidence)
        return self

    def get(self, prop, default=None):
        if prop in self:
            return self.props[prop][0]
        return default

    def to_dict(self):
        return {k: v for k, v in self.props.items() if not k.startswith('_')}

    def __str__(self):
        """
        For debugging.
        """
        parts = []
        for k, vconf in self.props.items():
            value, confidence = vconf
            parts += ["(%i) %s = %s" % (confidence, k, value)]
        return "\n\n".join(parts)

    def __contains__(self, prop):
        return prop in self.props


class BaseParser:
    def __init__(self, response):
        self.response = response
        self.url = response.url
        self.content = response.body

        if response.is_text():
            tbody = '<html><body><pre>%s</pre></body></html>'
            self.content = tbody % response.body

        if self.content is not None and "html>" in self.content:
            self.soup = SmartHTMLDocument(self.content)
        else:
            self.soup = None

    def absoluteify(self, path):
        return absolute_url(self.url, path)

    async def enrich(self, result):
        """
        Should enrich given ParseResult
        """
        raise NotImplementedError
