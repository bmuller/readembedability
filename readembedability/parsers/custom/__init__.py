import re
from operator import itemgetter

from readembedability.io import getPage
from readembedability.parsers.base import BaseParser
from readembedability.parsers.html import SmartHTMLDocument


class CustomParser(BaseParser):
    PARSERS = []

    @classmethod
    def register(klass, regex, fclass):
        regex = re.compile(regex, re.IGNORECASE)
        klass.PARSERS.append((regex, fclass))

    def enrich(self, result):
        for regex, fclass in CustomParser.PARSERS:
            if regex.match(self.response.url) is not None:
                return fclass(self.response).enrich(result)
        return result


class FortuneParser(CustomParser):
    def _enrich(self, page, postid, result):
        body = page.toJSON()
        article = filter(lambda article: article['id'] == postid, body['articles'])[0]
        result.set('embed', False, lock=True)
        result.set('title', article['short_title'], lock=True)
        result.set('content', article['content'], lock=True)
        if 'featured_image' in article:
            result.set('primary_image', article['featured_image']['src'], lock=True)
        result.set('summary', SmartHTMLDocument(article['excerpt']).getText(), lock=True)
        authors = " and ".join(map(itemgetter('name'), article['authors']))
        result.set('author', authors, lock=True)
        result.set('keywords', map(itemgetter('name'), article['tags'].values()), lock=True)
        # should be able to parse this
        result.set('published_at', self.parse_date(article['time']['published']), lock=True)
        return result

    def enrich(self, result):
        if self.bs is None:
            return result
        classes = filter(lambda s: s.startswith('postid-'), self.bs.body.attrs.get('class', []))
        if len(classes) == 0:
            return result
        postid = classes[0].split('-')[1]
        d = getPage("http://fortune.com/data/articles/%s/1/" % postid)
        return d.addCallback(self._enrich, int(postid), result).addBlindErrback(result)


CustomParser.register("https?://fortune\.com/", FortuneParser)
