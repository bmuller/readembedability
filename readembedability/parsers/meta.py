import json
from datetime import datetime
import logging

from readembedability.parsers.text import parse_authors
from readembedability.parsers.html import sanitize_html, SmartHTMLDocument
from readembedability.utils import unique, longest, parse_date, URL, flatten
from readembedability.parsers.base import BaseParser

LOG = logging.getLogger(__name__)


class AuthorParser(BaseParser):
    # pylint: disable=no-self-use
    def has_byline_prefix(self, prefix):
        prefix = prefix.lower()
        for allowed in ['by']:
            hasp = prefix.startswith(allowed)
            if hasp and len(prefix) == len(allowed):
                return True
            if hasp and not prefix[len(allowed)].isalpha():
                return True
        return False

    def get_standards(self):
        attempts = [
            ('meta', 'content', {'name': 'sailthru.author'}),
            ('meta', 'content', {'property': 'author'}),
            ('meta', 'content', {'name': 'author'}),
            (None, None, {'itemprop': 'author'}),
            ('a', None, {'rel': 'author'})
        ]
        return self.soup.coalesce_elem_value(attempts)

    async def enrich(self, result):
        if self.soup is None:
            return result

        # try standards based approach
        author = self.get_standards()
        if author is not None:
            result.set_if('authors', parse_authors(author), confidence=3)
            return result

        for txt in self.soup.text_chunks():
            parts = [s for s in txt.split(' ') if s != ""]
            if len(parts) == 0:
                return result
            # overlen is the max length + 1 for an author string
            overlen = 8 + (txt.lower().count(' and ') * 8)
            overlen += (txt.count(',') * 8)
            isbyline = self.has_byline_prefix(parts[0])
            if len(parts) in range(2, overlen) and isbyline:
                name = " ".join(parts[1:])
                if author is None or len(name) < len(author):
                    author = name

        if author:
            result.set_if('authors', parse_authors(author))
        return result


class DatePublishedParser(BaseParser):
    def get_standards(self):
        attempts = [
            (None, None, {'itemprop': 'datePublished'}),
            ('meta', 'content', {'itemprop': 'datePublished'}),
            ('meta', 'content', {'property': 'article:published_time'}),
            ('meta', 'content', {'name': 'PublishDate'}),
            ('meta', 'content', {'name': 'CreationDate'}),
            ('meta', 'content', {'name': 'date'}),
            ('time'),
            ('meta', 'content', {'name': 'eomportal-lastUpdate'}),
            ('meta', 'content', {'property': 'article:published_time'}),
            ('meta', 'content', {'property': 'article:modified_time'}),
            ('meta', 'content', {'property': 'og:updated_time'})
        ]
        return self.soup.coalesce_elem_value(attempts)

    async def enrich(self, result):
        if self.soup is None:
            return result

        pat = self.get_standards()
        if pat is not None:
            pat = parse_date(pat)

        # last ditch, check url
        if pat is None:
            pat = URL(self.url).url_date

        # Don't set any published_at to be in the future
        if pat is not None and pat < datetime.now().replace(tzinfo=pat.tzinfo):
            result.set('published_at', pat, 2, 'timespecificity')
        return result


class StandardsParser(BaseParser):
    async def enrich(self, result):
        if self.soup is None:
            return result

        atypes = ["http://schema.org/Article", "http://schema.org/BlogPosting"]
        articles = self.soup.find_all(itemtype=atypes)
        content = longest(map(str, articles))
        if content is not None:
            content = sanitize_html(content)

        parts = self.soup.find_all_loose(itemprop='articleBody')
        if parts:
            content = sanitize_html("".join(map(str, parts)))

        if content is not None and len(content.strip()) > 5:
            result.set('content', content, 3)
            result.set('_text', SmartHTMLDocument(content).all_text(), 3)

        keywords = result.get('keywords')
        for genre in self.soup.find_all_loose(itemprop="genre", content=True):
            keywords.append(genre['content'].strip())

        tags = self.soup.find_all('meta', name='sailthru.tags', content=True)
        for tag in tags:
            keywords += [t.strip() for t in tag['content'].split(',')]

        tags = self.soup.find_all('meta', property='article:tag', content=True)
        for tag in tags:
            keywords.append(tag['content'].strip())
        result.set('keywords', unique(keywords))

        return result


class SocialParser(BaseParser):
    async def enrich(self, result):
        if not self.soup:
            return result

        ogtitle = self.soup.find_all("meta", property="og:title", content=True)
        if ogtitle:
            result.set('title', ogtitle[0]['content'], 2)

        attrs = {'property': 'og:description', 'content': True}
        ogdesc = self.soup.find_all("meta", **attrs)
        if ogdesc:
            result.set('summary', ogdesc[0]['content'], 0, 'textlength')
        return result


class LDJSONParser(BaseParser):
    async def enrich(self, result):
        if not self.soup:
            return result

        for elem in self.soup.find_all('script', type="application/ld+json"):
            datas = []
            try:
                datas = json.loads(elem.get_text().strip())
                # datas can be a list - if it's not, make it one
                if not isinstance(datas, list):
                    datas = [datas]
            except json.decoder.JSONDecodeError as err:
                LOG.error(err)
            for obj in datas:
                if obj.get('@type') == 'NewsArticle':
                    result = self.eat_news_article(obj, result)
        return result

    # pylint: disable=no-self-use
    def eat_news_article(self, obj, result):
        if 'creator' in obj:
            # based on observation, this could be either
            # a single str, a list, or a list of lists
            creator = list(flatten(obj['creator']))
            result.set('authors', creator, 3)
        if 'dateCreated' in obj:
            result.set('published_at', parse_date(obj['dateCreated']), 3)
        if 'headline' in obj:
            result.set('title', obj['headline'], 3)
        return result
