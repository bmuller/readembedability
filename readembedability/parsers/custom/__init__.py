import re
from operator import itemgetter

from readembedability.io import get_page
from readembedability.utils import parse_date
from readembedability.parsers.base import BaseParser
from readembedability.parsers.html import SmartHTMLDocument


class CustomParser(BaseParser):
    PARSERS = []

    @classmethod
    def register(cls, regex, fclass):
        regex = re.compile(regex, re.IGNORECASE)
        cls.PARSERS.append((regex, fclass))

    async def enrich(self, result):
        for regex, fclass in CustomParser.PARSERS:
            if regex.match(self.response.url) is not None:
                return await fclass(self.response).enrich(result)
        return result


class FortuneParser(CustomParser):
    async def enrich(self, result):
        if not self.soup:
            return result
        caddrs = self.soup.body.attrs.get('class', [])
        classes = [s for s in caddrs if s.startswith('postid-')]
        if len(classes) == 0:
            return result
        postid = int(classes[0].split('-')[1])
        url = "http://fortune.com/data/articles/%i/1/" % postid
        page = await get_page(url)
        body = page.toJSON()
        article = [a for a in body['articles'] if a['id'] == postid][0]
        result.set('embed', False, 4)
        result.set('title', article['short_title'], 3)
        result.set('content', article['content'], 3)
        if 'featured_image' in article:
            result.set('primary_image', article['featured_image']['src'], 3)
        excerpt = SmartHTMLDocument(article['excerpt']).all_text()
        result.set('summary', excerpt, 3)
        authors = [i['name'] for i in article['authors']]
        result.set('authors', authors, 3)
        kwords = [v['name'] for v in article['tags'].values()]
        result.set('keywords', kwords, 3)
        # should be able to parse this
        result.set('published_at', parse_date(article['time']['published']), 3)
        return result


# pylint: disable=anomalous-backslash-in-string
CustomParser.register("https?://fortune\.com/", FortuneParser)
