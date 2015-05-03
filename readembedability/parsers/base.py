from dateutil.parser import parse as dateutil_parse

from robostrippy.utils import absoluteURL

from readembedability.parsers.html import SmartHTMLDocument


class ParseResult:
    def __init__(self):
        self.props = {}
        self.locks = set([])

    def set(self, prop, value, lock=False, overwrite=False):
        if prop in self.locks and not overwrite:
            return
        self.props[prop] = value
        if lock:
            self.locks.add(prop)

    def setIfLonger(self, prop, value):
        if value is not None and (self.get(prop) is None or len(value) > len(self.get(prop))):
            self.set(prop, value)

    def get(self, prop):
        return self.props[prop]

    def jsonReady(self):
        r = {}
        for k in [ k for k in self.props.keys() if not k.startswith('_') ]:
            r[k] = self.props[k]
        return r

    def __contains__(self, prop):
        return prop in self.props


class BaseParser:
    def __init__(self, response):
        self.response = response
        self.url = response.url
        self.content = response.body

        if response.isText():
            self.content = '<html><body><pre>%s</pre></body></html>' % response.body

        if self.content is not None and "html>" in self.content:
            self.bs = SmartHTMLDocument(self.content)
        else:
            self.bs = None


    def parse_date(self, datestring):
        try:
            return dateutil_parse(datestring, fuzzy=True)
        except:
            return None


    def absoluteify(self, path):
        return absoluteURL(self.url, path)


    def enrich(self, result):
        """
        Should enrich given ParseResult
        """
        raise NotImplementedError
