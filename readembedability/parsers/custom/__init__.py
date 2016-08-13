import re
from operator import itemgetter

from readembedability.io import get_page
from readembedability.parsers.base import BaseParser
from readembedability.parsers.html import SmartHTMLDocument


class CustomParser(BaseParser):
    PARSERS = []

    @classmethod
    def register(klass, regex, fclass):
        regex = re.compile(regex, re.IGNORECASE)
        klass.PARSERS.append((regex, fclass))

    async def enrich(self, result):
        for regex, fclass in CustomParser.PARSERS:
            if regex.match(self.response.url) is not None:
                return await fclass(self.response).enrich(result)
        return result


class FortuneParser(CustomParser):
    def _enrich(self, page, postid, result):
        body = page.toJSON()
        article = filter(lambda article: article['id'] == postid, body['articles'])[0]
        result.set('embed', False, 4)
        result.set('title', article['short_title'], 3)
        result.set('content', article['content'], 3)
        if 'featured_image' in article:
            result.set('primary_image', article['featured_image']['src'], 3)
        result.set('summary', SmartHTMLDocument(article['excerpt']).getText(), 3)
        authors = [i['name'] for i in article['authors']]
        result.set('authors', authors, 3)
        result.set('keywords', map(itemgetter('name'), article['tags'].values()), 3)
        # should be able to parse this
        result.set('published_at', self.parse_date(article['time']['published']), 3)
        return result

    async def enrich(self, result):
        if self.bs is None:
            return result
        classes = [s for s in self.bs.body.attrs.get('class', []) if s.startswith('postid-')]
        if len(classes) == 0:
            return result
        postid = classes[0].split('-')[1]
        page = await get_page("http://fortune.com/data/articles/%s/1/" % postid)
        return self._enrich(page, int(postid), result)


CustomParser.register("https?://fortune\.com/", FortuneParser)
